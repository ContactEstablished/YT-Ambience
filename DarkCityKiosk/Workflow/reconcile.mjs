// Explicit operator recovery only. Never redispatches an interrupted job.
import fs from 'node:fs';
import path from 'node:path';
import { Coordinator } from './coordinator.mjs';
import { read, write, immutable, live, now, renderProcesses, lock } from './lib.mjs';

export async function reconcile(c, action, notes, inspect = renderProcesses, isLive = live) {
  if (!['accept', 'abandon', 'unlock'].includes(action) || !notes.trim()) throw Error('Explicit reconciliation action and notes required');
  c.pause('Operator reconciliation in progress');
  const s = c.state();
  if (inspect().length || (s.active?.pid && isLive(s.active.pid))) throw Error('Job/render process still live. No takeover permitted.');
  const coordinatorLock = path.join(c.w, 'coordinator.lock');
  if (fs.existsSync(coordinatorLock)) {
    const old = read(coordinatorLock);
    if (isLive(old.pid)) throw Error('Coordinator still live. Stop it and wait before recovery.');
    immutable(path.join(c.w, 'logs', `recovered-lock-${Date.now()}.json`), old);
    fs.unlinkSync(coordinatorLock); // explicit audited recovery, never automatic
  }
  const release = lock(coordinatorLock, { command: 'reconcile' });
  try {
    const renderLock = path.join(c.w, 'render.lock');
    if (fs.existsSync(renderLock)) {
      const old = read(renderLock);
      if (isLive(old.pid)) throw Error('Render guard still live');
      immutable(path.join(c.w, 'logs', `recovered-render-${Date.now()}.json`), old);
      fs.unlinkSync(renderLock);
    }
    c.event('reconciliation', { action, notes, active: s.active });
    if (s.active) {
      if (action === 'unlock') throw Error('Active job requires accept or abandon');
      if (action === 'accept') {
        const result = read(path.join(c.w, 'logs', s.active.job_id, 'exit.json'));
        if (result.code !== 0) throw Error('Cannot accept failed/missing exit receipt');
        await c.finish(s.active, result, s);
        s.completed_jobs.push(s.active.job_id);
      } else {
        s.rounds[s.active.round_id].status = 'abandoned_after_reconciliation';
        s.queue = s.queue.filter(j => j.round_id !== s.active.round_id);
      }
      s.active = null; c.save(s);
    }
    write(path.join(c.w, 'PAUSE'), { at: now(), reason: 'Reconciled; explicit resume required' });
    console.log('Reconciled and paused. Original job/round is never retried.');
  } finally { release(); }
}
async function main() {
  const [action, flag, ...words] = process.argv.slice(2);
  if (flag !== '--confirmed-idle' || !words.join(' ').trim()) throw Error('Usage: node Workflow/reconcile.mjs accept|abandon|unlock --confirmed-idle "operator investigation notes"');
  await reconcile(new Coordinator(), action, words.join(' '));
}
if (process.argv[1] && path.resolve(process.argv[1]) === import.meta.filename) main().catch(e => { console.error(e.message); process.exitCode = 1; });
