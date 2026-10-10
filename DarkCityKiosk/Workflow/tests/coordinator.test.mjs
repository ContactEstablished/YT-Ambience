import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { Coordinator } from '../coordinator.mjs';
import { reconcile } from '../reconcile.mjs';
import { root, read, write, hash, lock, validatePackage } from '../lib.mjs';

// Each test owns a retained fixture workspace. No production state, CLIs or Unreal calls.
const run = path.join(root, 'Workflow', 'logs', 'tests', new Date().toISOString().replaceAll(':', '-'));
fs.mkdirSync(run, { recursive: true });
const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aD1sAAAAASUVORK5CYII=', 'base64');
let serial = 0;
function setup(mode = 'normal') {
  const base = path.join(run, `${++serial}-${mode}`); const w = path.join(base, 'Workflow');
  fs.mkdirSync(path.join(w, 'rounds'), { recursive: true });
  fs.mkdirSync(path.join(w, 'prompt')); fs.mkdirSync(path.join(w, 'reviews'));
  for (const f of ['config.json', 'status.json']) fs.copyFileSync(path.join(root, 'Workflow', f), path.join(w, f));
  const state = read(path.join(w, 'status.json'));
  Object.assign(state, { jobs_started: 0, queue: [], active: null, rounds: {}, completed_jobs: [], accepted: [], drafts: [], run_limit: 3 });
  write(path.join(w, 'status.json'), state);
  fs.writeFileSync(path.join(w, 'PLAN.md'), '# Fixture plan\n');
  fs.writeFileSync(path.join(w, 'prompt', 'TRAIN-00.md'), 'Fixture baseline');
  write(path.join(w, 'rounds', 'TRAIN-00.json'), { feature: 'train-baseline', required_images: ['fixture.png'] });
  fs.mkdirSync(path.join(base, '_reference')); fs.writeFileSync(path.join(base, '_reference', 'PrimaryReference.png'), png);
  let calls = 0;
  const adapter = { renders: async () => mode === 'active-render' ? [{ pid: 123 }] : [], run: async (job, c) => {
    calls++;
    if (mode === 'failed') return { code: 1 };
    if (job.kind === 'build') {
      const dir = path.join(base, 'Renders', 'stills', job.round_id);
      fs.writeFileSync(path.join(dir, 'fixture.png'), mode === 'corrupt' ? 'not an image' : png);
      const m = { schema_version: 1, round_id: job.round_id, job_id: mode === 'wrong-job' ? 'other' : job.job_id,
        prompt_path: job.prompt_path, prompt_sha256: job.prompt_sha256, status: 'complete', render_active: false,
        outputs: [{ path: `Renders/stills/${job.round_id}/fixture.png`, kind: 'image', sha256: hash(path.join(dir, 'fixture.png')), description: 'fixture', source: 'synthetic fixture' }],
        changes: [], validation: [{ check: 'fixture', result: 'PASS', details: 'mock only' }], known_issues: [], unverified_requirements: ['motion', 'seamless_loop'] };
      write(path.join(dir, 'manifest.json'), m);
      fs.writeFileSync(path.join(dir, 'COMPLETE ROUND.md'), [job.round_id, job.job_id, job.prompt_path, job.prompt_sha256].join('\n'));
      if (mode === 'incomplete') fs.unlinkSync(path.join(dir, 'fixture.png')); // fixture only
      if (mode === 'pause') c.pause('mock pause during running job');
      return { code: 0 };
    }
    if (job.kind === 'review') return { code: 0, value: { round_id: job.round_id, build_job_id: job.build_job_id,
      prompt_sha256: job.prompt_sha256, manifest_sha256: job.package.manifest_sha256, verdict: mode === 'needs-input' ? 'NEEDS INPUT' : 'PASS',
      summary: 'Mock visual review, no real assessment', inspected_images: [`Renders/stills/${job.round_id}/fixture.png`, '_reference/PrimaryReference.png'],
      reference_comparison: 'Fixture comparison', previous_evidence_comparison: 'Fixture previous image', findings: [],
      unverified_requirements: ['motion', 'seamless_loop'], motion_verified: false, loop_verified: false } };
    return { code: 0, value: { round_id: 'TRAIN-01', queued: false, prompt: 'Fixture draft only' } };
  } };
  const c = new Coordinator(base, adapter); const s = c.state(); c.enqueue(s, 'TRAIN-00'); c.save(s);
  return { c, adapter, base, calls: () => calls };
}

test('normal handoff, independent review, unqueued draft and automatic pause', async () => {
  const { c, calls } = setup();
  assert.equal(await c.cycle(), true); assert.equal(c.state().queue[0].kind, 'review');
  assert.equal(await c.cycle(), true); assert.equal(c.state().accepted.length, 1);
  assert.equal(await c.cycle(), true); assert.equal(c.blocked(), true);
  assert.equal(c.state().queue.length, 0); assert.equal(c.state().rounds['TRAIN-01'], undefined);
  assert.equal(calls(), 3); assert.equal(await c.cycle(), false); assert.equal(calls(), 3);
});
for (const mode of ['incomplete', 'corrupt', 'wrong-job', 'failed']) test(`${mode} package/job pauses without retry`, async () => {
  const { c, calls } = setup(mode); assert.equal(await c.cycle(), false);
  assert.ok(c.state().active); assert.equal(c.blocked(), true);
  assert.equal(await c.cycle(), false); assert.equal(calls(), 1);
});
test('duplicate marker does not redispatch a completed build', async () => {
  const { c, calls } = setup(); await c.cycle();
  assert.throws(() => c.enqueue(c.state(), 'TRAIN-00'), /already registered/);
  await c.cycle(); await c.cycle(); await c.cycle(); assert.equal(calls(), 3);
});
test('pre-existing round folder is not adopted as fresh evidence', async () => {
  const { c, base, calls } = setup();
  fs.mkdirSync(path.join(base, 'Renders/stills/TRAIN-00'), { recursive: true });
  assert.equal(await c.cycle(), false); assert.equal(calls(), 0); assert.ok(c.state().active);
});
test('pause before dispatch and pause during running job prevent next dispatch', async () => {
  const pre = setup(); pre.c.pause('before'); await pre.c.cycle(); assert.equal(pre.calls(), 0);
  const mid = setup('pause'); await mid.c.cycle(); await mid.c.cycle();
  assert.equal(mid.calls(), 1); assert.equal(mid.c.state().queue[0].kind, 'review');
});
test('restart resumes completed handoff but refuses interrupted active job', async () => {
  const { c, adapter, base, calls } = setup(); await c.cycle();
  const restarted = new Coordinator(base, adapter); await restarted.cycle(); assert.equal(calls(), 2);
  const s = restarted.state(); s.active = { ...s.queue[0], phase: 'dispatching' }; restarted.save(s);
  const again = new Coordinator(base, adapter); await again.cycle();
  assert.equal(calls(), 2); assert.equal(again.blocked(), true);
});
test('live/ambiguous ownership lock cannot be silently stolen', () => {
  const { c } = setup(); const p = path.join(c.w, 'test.lock'); const release = lock(p, {});
  assert.throws(() => lock(p, {}), /never steal/); release();
});
test('active render, run limit and missing authority prevent model calls', async () => {
  const a = setup('active-render'); await a.c.cycle(); assert.equal(a.calls(), 0);
  const b = setup(); const s = b.c.state(); s.jobs_started = s.run_limit; b.c.save(s); await b.c.cycle(); assert.equal(b.calls(), 0);
  const d = setup(); const cfg = read(path.join(d.c.w, 'config.json')); cfg.features['train-baseline'].authorized_rounds = []; write(path.join(d.c.w, 'config.json'), cfg);
  await d.c.cycle(); assert.equal(d.calls(), 0);
});
test('no model requests on empty idle cycle', async () => {
  const { c, calls } = setup(); const s = c.state(); s.queue = []; c.save(s);
  await c.cycle(); await c.cycle(); assert.equal(calls(), 0);
});
test('immutable prompt changes pause before dispatch', async () => {
  const { c, calls } = setup(); fs.appendFileSync(path.join(c.w, 'prompt/TRAIN-00.md'), 'changed');
  await c.cycle(); assert.equal(calls(), 0); assert.equal(c.blocked(), true);
});
test('NEEDS INPUT pauses without drafting', async () => {
  const { c, calls } = setup('needs-input'); await c.cycle(); await c.cycle(); await c.cycle();
  assert.equal(calls(), 2); assert.equal(c.state().drafts.length, 0); assert.equal(c.blocked(), true);
});
test('R3 and unauthorized redesign are rejected', () => {
  const { c } = setup(); assert.throws(() => c.enqueue(c.state(), 'TRAIN-01-R3'), /maximum R2/);
  write(path.join(c.w, 'rounds/TRAIN-01.json'), { feature: 'train-baseline', required_images: ['fixture.png'] });
  assert.throws(() => c.enqueue(c.state(), 'TRAIN-01'), /not user-authorized/);
});

test('restart recovery accepts a recorded successful package exactly once without rerunning builder', async () => {
  const { c, adapter, base, calls } = setup();
  c.finish = async () => { throw Error('Simulated interruption after exit journal, before handoff'); };
  await c.cycle(); assert.equal(calls(), 1); assert.ok(c.state().active);
  const restarted = new Coordinator(base, adapter);
  await reconcile(restarted, 'accept', 'Fixture: inspected successful exit and outputs; all processes idle', () => [], () => false);
  assert.equal(restarted.state().active, null); assert.equal(restarted.state().queue.length, 1);
  assert.equal(restarted.state().queue[0].kind, 'review'); assert.equal(calls(), 1);
  await reconcile(restarted, 'accept', 'Fixture: repeated operator command is not a replay', () => [], () => false);
  assert.equal(restarted.state().queue.length, 1); assert.equal(calls(), 1);
});
test('failed job can only be abandoned; active PID cannot be stolen', async () => {
  const { c, calls } = setup('failed'); await c.cycle();
  await assert.rejects(reconcile(c, 'accept', 'Fixture', () => [], () => false), /Cannot accept/);
  const s = c.state(); s.active.pid = 42; c.save(s);
  await assert.rejects(reconcile(c, 'abandon', 'Fixture', () => [], () => true), /still live/);
  await reconcile(c, 'abandon', 'Fixture: inspected interrupted state; no retry', () => [], () => false);
  assert.equal(c.state().active, null); assert.equal(calls(), 1);
  assert.throws(() => c.enqueue(c.state(), 'TRAIN-00'), /already registered/);
});
test('missing capture receipt prevents a package from being accepted', async () => {
  const { c } = setup(); const s = c.state();
  s.queue[0].required_captures = [{ tag: 'TRAIN-00-mid', image: 'fixture.png' }]; c.save(s);
  assert.equal(await c.cycle(), false); assert.match(c.state().active.error, /Missing guarded capture receipt/);
});
test('evidence changed between handoff and review pauses without reviewing', async () => {
  const { c, base, calls } = setup(); await c.cycle();
  fs.appendFileSync(path.join(base, 'Renders/stills/TRAIN-00/fixture.png'), 'changed');
  await c.cycle(); assert.equal(calls(), 1); assert.equal(c.blocked(), true);
});
test('feature allows at most two corrective rounds total, across stems', () => {
  const { c } = setup(); const cfg = read(path.join(c.w, 'config.json'));
  cfg.features['train-baseline'] = { authorized_rounds: ['TRAIN-00', 'TRAIN-00-R1', 'TRAIN-00-R2', 'TRAIN-01', 'TRAIN-01-R1'], max_rounds: 9, max_corrective_rounds: 9 };
  write(path.join(c.w, 'config.json'), cfg);
  for (const id of ['TRAIN-00-R1', 'TRAIN-00-R2', 'TRAIN-01', 'TRAIN-01-R1']) {
    write(path.join(c.w, `rounds/${id}.json`), { feature: 'train-baseline', required_images: ['fixture.png'] });
    fs.writeFileSync(path.join(c.w, `prompt/${id}.md`), 'fixture');
  }
  const s = c.state(); c.enqueue(s, 'TRAIN-00-R1'); c.enqueue(s, 'TRAIN-00-R2'); c.enqueue(s, 'TRAIN-01');
  assert.throws(() => c.enqueue(s, 'TRAIN-01-R1'), /corrective budget exhausted/);
});

console.log('Retained fixture evidence:', run);
