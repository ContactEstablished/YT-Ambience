// Permission preflight runner. Launches Claude exactly as coordinator.mjs run() launches a build job
// (same executable, flags, cwd and stdin delivery) but outside the production queue: it never touches
// status.json, the queue, locks, round folders or the authorization ledger.
//   node Workflow/permission-check/run-preflight.mjs <run-name> <prompt-file>
// Writes Workflow/permission-check/<run-name>/{command.json,stdout.log,stderr.log,exit.json,tools.json}.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { root, read, now } from '../lib.mjs';

const [name, promptFile] = process.argv.slice(2);
if (!/^[a-z0-9-]+$/.test(name || '') || !promptFile) throw Error('usage: run-preflight.mjs <run-name> <prompt-file>');
const here = path.join(root, 'Workflow', 'permission-check');
const dir = path.join(here, name);
fs.mkdirSync(dir); // throws if the run name exists: evidence is never overwritten
const cfg = read(path.join(root, 'Workflow', 'config.json'));
const prompt = fs.readFileSync(path.resolve(here, promptFile), 'utf8');
// Identical to coordinator.mjs: job.kind === 'build' args, cfg.claude.executable, cwd = project root.
const executable = cfg.claude.executable;
const args = ['-p', '--output-format', 'json', '--permission-mode', 'manual', '--permission-prompts', 'none'];
fs.writeFileSync(path.join(dir, 'command.json'), JSON.stringify({ executable, args, cwd: root, prompt_file: promptFile, started_at: now() }, null, 2) + '\n');
const stdout = fs.openSync(path.join(dir, 'stdout.log'), 'wx');
const stderr = fs.openSync(path.join(dir, 'stderr.log'), 'wx');
const child = spawn(executable, args, { cwd: root, stdio: ['pipe', stdout, stderr], windowsHide: true, shell: false });
const timer = setTimeout(() => child.kill(), 20 * 60_000);
child.stdin.on('error', () => {}); child.stdin.end(prompt);
const code = await new Promise((resolve, reject) => { child.on('error', reject); child.on('exit', resolve); });
clearTimeout(timer); fs.closeSync(stdout); fs.closeSync(stderr);

// The coordinator's own acceptance test for a build envelope.
let envelope = null; let parse_error = null;
try { envelope = read(path.join(dir, 'stdout.log')); } catch (e) { parse_error = e.message; }
const coordinator_accepts = code === 0 && !!envelope && !envelope.is_error && !envelope.permission_denials?.length;

// Tool calls the session actually made, from its transcript (~/.claude/projects/<key>/<session_id>.jsonl).
const tools = [];
let transcript = null;
if (envelope?.session_id) {
  const base = path.join(os.homedir(), '.claude', 'projects');
  for (const d of fs.readdirSync(base)) {
    const p = path.join(base, d, envelope.session_id + '.jsonl');
    if (fs.existsSync(p)) { transcript = p; break; }
  }
  if (transcript) {
    const results = new Map(); const uses = [];
    for (const line of fs.readFileSync(transcript, 'utf8').split('\n')) {
      if (!line.trim()) continue;
      let m; try { m = JSON.parse(line); } catch { continue; }
      for (const c of Array.isArray(m.message?.content) ? m.message.content : []) {
        if (c.type === 'tool_use') uses.push(c);
        if (c.type === 'tool_result') {
          const text = typeof c.content === 'string' ? c.content : (c.content || []).map(x => x.text || '').join('');
          results.set(c.tool_use_id, { is_error: !!c.is_error, text: text.slice(0, 400) });
        }
      }
    }
    for (const u of uses) tools.push({ tool: u.name, input: u.input?.command ?? u.input?.file_path ?? u.input, result: results.get(u.id) ?? null });
  }
}
fs.writeFileSync(path.join(dir, 'tools.json'), JSON.stringify(tools, null, 2) + '\n');
const summary = { name, code, parse_error, coordinator_accepts, is_error: envelope?.is_error, subtype: envelope?.subtype,
  permission_denials: envelope?.permission_denials, session_id: envelope?.session_id, transcript, num_turns: envelope?.num_turns,
  envelope_keys: envelope ? Object.keys(envelope) : null, ended_at: now() };
fs.writeFileSync(path.join(dir, 'exit.json'), JSON.stringify(summary, null, 2) + '\n');
console.log(JSON.stringify(summary, null, 2));
