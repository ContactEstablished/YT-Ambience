// Claude's sole editor entry point. Keeps a durable lease through asynchronous MRQ.
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { root, read, immutable, lock, renderProcesses, sleep, now, hash, decodeImages } from './lib.mjs';

const [jobId, mode, ...args] = process.argv.slice(2);
const w = path.join(root, 'Workflow');
async function main() {
  const s = read(path.join(w, 'status.json'));
  if (s.active?.job_id !== jobId || s.active.kind !== 'build' || s.active.phase !== 'running') throw Error('No matching active Claude build lease');
  if (!['editor', 'render'].includes(mode)) throw Error('Usage: node Workflow/ue-guard.mjs JOB_ID editor|render Scripts/file.py [args]');
  if (mode === 'render' && args[0] !== 'Scripts/render.py') throw Error('Render mode requires existing render.py');
  if (mode === 'editor' && args.some(a => /render|capture/i.test(a))) throw Error('Render/capture must use render mode');
  if (s.active.round_id === 'TRAIN-00') {
    if (mode !== 'render') throw Error('Baseline permits only existing MRQ capture, no editor scripts');
    const expected = [
      ['Scripts/render.py', '--tag', 'TRAIN-00-mid', '--frames', '180-181', '--temporal', '4'],
      ['Scripts/render.py', '--tag', 'TRAIN-00-train', '--frames', '432-433', '--temporal', '4']
    ];
    if (!expected.some(e => JSON.stringify(e) === JSON.stringify(args))) throw Error('Baseline capture arguments differ from approved prompt');
  }
  if (renderProcesses().length) throw Error('Existing render: no editor operations permitted');
  const tag = args[args.indexOf('--tag') + 1];
  if (mode === 'render' && (!/^[A-Z0-9][A-Za-z0-9-]*$/.test(tag) || fs.existsSync(path.join(root, 'Renders', 'frames', tag)))) throw Error('Render tag must be new and confined to Renders/frames');
  const release = lock(path.join(w, 'render.lock'), { job_id: jobId, mode, args });
  let clean = false;
  try {
    const logDir = path.join(w, 'logs', jobId);
    const id = 'ue-' + Date.now();
    const log = fs.openSync(path.join(logDir, id + '.log'), 'wx');
    const child = spawn(process.execPath, [path.join(root, 'Unreal', 'Scripts', 'ue.mjs'), ...args], {
      cwd: path.join(root, 'Unreal'), windowsHide: true, shell: false, stdio: ['ignore', log, log]
    });
    let exit = null; let failure = null;
    child.on('error', e => { failure = e; }); child.on('exit', code => { exit = code; });
    let seen = false; let absent = 0;
    const deadline = Date.now() + read(path.join(w, 'config.json')).job_timeout_seconds * 1000;
    try {
      while (Date.now() < deadline) {
        if (failure) throw failure;
        if (exit !== null && exit !== 0) throw Error('Editor bridge failed; reconcile render lease');
        const active = renderProcesses();
        if (active.length) { seen = true; absent = 0; }
        else absent++;
        if (mode === 'editor' && exit === 0 && !active.length) { clean = true; break; }
        if (mode === 'render' && seen && absent >= 3 && exit === 0) { clean = true; break; }
        await sleep(1000);
      }
      if (!clean) throw Error('Render lifecycle uncertain/timeout. Lease retained; do not retry.');
      let output_sha256 = null;
      if (mode === 'render') {
        const outputDir = path.join(root, 'Renders', 'frames', tag);
        const images = fs.readdirSync(outputDir).filter(n => n.endsWith('.png')).map(n => path.join(outputDir, n));
        if (!images.length) throw Error('Render produced no PNGs');
        await decodeImages(images);
        if (images.length === 1) output_sha256 = hash(images[0]);
      }
      immutable(path.join(logDir, id + '.json'), { job_id: jobId, args, mode, tag, output_sha256, process_seen: seen, finished_at: now(), render_processes_remaining: [] });
    } finally { fs.closeSync(log); }
  } finally { if (clean) release(); }
}
main().catch(e => { console.error(e.message); process.exitCode = 1; });
