#!/usr/bin/env node
// Runs Python inside the live Unreal Editor over the PythonScriptPlugin
// remote-execution protocol (the same one Epic's remote_execution.py speaks).
// This machine has no standalone Python, so this Node client is the bridge.
//
//   node Scripts/ue.mjs path/to/script.py [args...]   run a file (sys.argv gets args)
//   node Scripts/ue.mjs -c "print(unreal.SystemLibrary.get_engine_version())"
//   node Scripts/ue.mjs -e "unreal.EditorLevelLibrary.get_editor_world().get_name()"
//
// Requires Project Settings > Python > Enable Remote Execution (localhost only:
// bind 127.0.0.1, multicast TTL 0). Picks the editor whose project is
// UE_PROJECT (default DarkCityKiosk) so other open editors are ignored.

import dgram from 'node:dgram';
import net from 'node:net';
import path from 'node:path';
import crypto from 'node:crypto';

const GROUP = '239.0.0.1';
const GROUP_PORT = 6766;
const BIND = '127.0.0.1';
const PROJECT = process.env.UE_PROJECT || 'DarkCityKiosk';
const TIMEOUT_MS = Number(process.env.UE_TIMEOUT_MS || 60 * 60 * 1000);

const nodeId = crypto.randomUUID();
const message = (type, dest, data) =>
  Buffer.from(JSON.stringify({ version: 1, magic: 'ue_py', type, source: nodeId, ...(dest && { dest }), ...(data && { data }) }), 'utf8');

function parseArgs(argv) {
  if (argv[0] === '-c') return { command: argv.slice(1).join(' '), mode: 'ExecuteFile' };
  if (argv[0] === '-e') return { command: argv.slice(1).join(' '), mode: 'EvaluateStatement' };
  if (!argv[0]) {
    console.error('usage: node Scripts/ue.mjs <script.py> [args...] | -c "<python>" | -e "<expression>"');
    process.exit(2);
  }
  // Run the file in a fresh namespace (runpy) rather than the editor's shared
  // __main__: leftover globals from earlier runs would otherwise keep assets
  // (e.g. a sequence the script wants to delete and rebuild) alive.
  const file = path.resolve(argv[0]).replaceAll('\\', '/');
  const argvList = JSON.stringify([file, ...argv.slice(1)]);
  const command = [
    'import gc, runpy, sys',
    `sys.argv = ${argvList}`,
    'try:',
    `    runpy.run_path(${JSON.stringify(file)}, run_name="__main__")`,
    'finally:',
    '    gc.collect()',
  ].join('\n');
  return { command, mode: 'ExecuteFile' };
}

function discover(udp) {
  return new Promise((resolve, reject) => {
    const seen = new Map();
    const ping = () => udp.send(message('ping'), GROUP_PORT, GROUP);
    const onMsg = (buf) => {
      let m;
      try { m = JSON.parse(buf.toString('utf8')); } catch { return; }
      if (m.magic !== 'ue_py' || m.type !== 'pong' || m.source === nodeId) return;
      seen.set(m.source, m.data?.project_name);
      if (m.data?.project_name === PROJECT) { cleanup(); resolve(m.source); }
    };
    const timer = setInterval(ping, 1000);
    const deadline = setTimeout(() => {
      cleanup();
      const found = [...seen.values()].join(', ') || 'none';
      reject(new Error(`No Unreal Editor for project "${PROJECT}" answered (editors seen: ${found}). Is Remote Execution enabled?`));
    }, 8000);
    const cleanup = () => { clearInterval(timer); clearTimeout(deadline); udp.off('message', onMsg); };
    udp.on('message', onMsg);
    ping();
  });
}

function openCommandChannel(udp, remote) {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.listen(0, BIND, () => {
      const { port } = server.address();
      const ask = () => udp.send(message('open_connection', remote, { command_ip: BIND, command_port: port }), GROUP_PORT, GROUP);
      const timer = setInterval(ask, 1000);
      const deadline = setTimeout(() => { clearInterval(timer); server.close(); reject(new Error('Editor never opened the command connection.')); }, 8000);
      server.once('connection', (sock) => { clearInterval(timer); clearTimeout(deadline); server.close(); resolve(sock); });
      ask();
    });
  });
}

function runCommand(sock, remote, command, mode) {
  return new Promise((resolve, reject) => {
    let buf = Buffer.alloc(0);
    const deadline = setTimeout(() => reject(new Error(`Command timed out after ${TIMEOUT_MS} ms`)), TIMEOUT_MS);
    sock.on('data', (chunk) => {
      buf = Buffer.concat([buf, chunk]);
      let m;
      try { m = JSON.parse(buf.toString('utf8')); } catch { return; } // wait for the rest of the message
      if (m.type !== 'command_result' || m.source === nodeId) return;
      clearTimeout(deadline);
      resolve(m.data);
    });
    sock.on('error', reject);
    sock.on('close', () => reject(new Error('Editor closed the command connection.')));
    sock.write(message('command', remote, { command, unattended: true, exec_mode: mode }));
  });
}

async function main() {
  const { command, mode } = parseArgs(process.argv.slice(2));
  const udp = dgram.createSocket({ type: 'udp4', reuseAddr: true });
  await new Promise((r) => udp.bind(GROUP_PORT, BIND, r));
  udp.setMulticastInterface(BIND);
  udp.setMulticastLoopback(true);
  udp.setMulticastTTL(0);
  udp.addMembership(GROUP, BIND);

  let sock;
  let remote;
  try {
    remote = await discover(udp);
    sock = await openCommandChannel(udp, remote);
    const result = await runCommand(sock, remote, command, mode);
    for (const o of result.output || []) {
      const line = String(o.output).replace(/\s+$/, '');
      if (o.type === 'Error' || o.type === 'Warning') console.error(line); else console.log(line);
    }
    if (mode === 'EvaluateStatement' && result.result !== undefined && result.result !== 'None') console.log(result.result);
    if (!result.success) {
      if (mode !== 'EvaluateStatement' && result.result && result.result !== 'None') console.error(result.result);
      process.exitCode = 1;
    }
  } finally {
    if (remote) udp.send(message('close_connection', remote), GROUP_PORT, GROUP, () => udp.close());
    else udp.close();
    sock?.destroy();
  }
}

main().catch((err) => { console.error(err.message); process.exit(1); });
