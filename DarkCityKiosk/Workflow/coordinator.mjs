import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { root, read, write, immutable, hash, now, inside, lock, live, sleep, renderProcesses, decodeImages, validatePackage } from './lib.mjs';

export class Coordinator {
  constructor(base = root, adapter = null) {
    this.root = base; this.w = path.join(base, 'Workflow'); this.adapter = adapter;
    this.statePath = path.join(this.w, 'status.json');
  }
  state() { return read(this.statePath); }
  save(s) { s.updated_at = now(); write(this.statePath, s); }
  event(type, data = {}) { fs.appendFileSync(path.join(this.w, 'events.jsonl'), JSON.stringify({ at: now(), type, ...data }) + '\n'); }
  pause(reason) {
    write(path.join(this.w, 'PAUSE'), { at: now(), reason });
    this.event('pause', { reason });
  }
  blocked() { return ['PAUSE', 'STOP'].some(n => fs.existsSync(path.join(this.w, n))); }
  async safe() {
    if (fs.existsSync(path.join(this.w, 'render.lock'))) throw Error('Unresolved render lock');
    if ((this.adapter ? await this.adapter.renders() : renderProcesses()).length) throw Error('An Unreal render is active');
  }
  enqueue(s, round) {
    if (!/^[A-Z]+-\d{2}(?:-R[12])?$/.test(round)) throw Error('Invalid immutable round ID (maximum R2)');
    const d = read(path.join(this.w, 'rounds', round + '.json'));
    const policy = read(path.join(this.w, 'config.json'));
    const f = policy.features[d.feature];
    if (!f || !f.authorized_rounds.includes(round)) throw Error('Round is not user-authorized');
    const correction = Number(round.match(/-R([12])$/)?.[1] || 0);
    if (correction > Math.min(2, f.max_corrective_rounds)) throw Error('Corrective limit exhausted');
    if (s.rounds[round]) throw Error('Round already registered; never replay it');
    const used = Object.values(s.rounds).filter(r => r.feature === d.feature).length;
    if (used >= f.max_rounds) throw Error('Feature round budget exhausted');
    const correctionsUsed = Object.entries(s.rounds).filter(([id, r]) => r.feature === d.feature && /-R[12]$/.test(id)).length;
    if (correction && correctionsUsed >= Math.min(2, f.max_corrective_rounds)) throw Error('Feature corrective budget exhausted');
    if (correction && !s.rounds[round.replace(/-R[12]$/, correction === 1 ? '' : '-R1')]) throw Error('Missing preceding round');
    const promptPath = `Workflow/prompt/${round}.md`;
    const job = { job_id: crypto.randomUUID(), kind: 'build', round_id: round, feature: d.feature,
      prompt_path: promptPath, prompt_sha256: hash(inside(this.root, promptPath)), required_images: d.required_images,
      minimum_image_size: d.minimum_image_size, required_captures: d.required_captures };
    if (!Array.isArray(job.required_images) || !job.required_images.length) throw Error('Required images not specified');
    s.rounds[round] = { feature: d.feature, status: 'queued', build_job: job.job_id };
    s.queue.push(job); this.event('queued', job);
  }
  async cycle() {
    const s = this.state();
    if (s.active) { this.pause('Interrupted or ambiguous active job: reconcile before any retry'); return false; }
    if (this.blocked() || !s.queue.length) return false;
    const cfg = read(path.join(this.w, 'config.json'));
    if (s.jobs_started >= s.run_limit) { this.pause('Run limit exhausted'); return false; }
    try { await this.safe(); } catch (e) { this.pause(e.message); return false; }
    const job = s.queue[0];
    const f = cfg.features[job.feature];
    if (!f?.authorized_rounds.includes(job.round_id)) { this.pause('Authorization missing/revoked'); return false; }
    if (job.kind === 'build' && !this.adapter) {
      const readyPath = path.join(this.w, 'operator-ready.json');
      if (!fs.existsSync(readyPath) || Date.now() - Date.parse(read(readyPath).at) > 4 * 3600_000) { this.pause('Operator readiness attestation missing/expired; see README'); return false; }
    }
    if (hash(inside(this.root, job.prompt_path)) !== job.prompt_sha256) { this.pause('Prompt changed after queueing'); return false; }
    const logDir = path.join(this.w, 'logs', job.job_id);
    fs.mkdirSync(logDir, { recursive: true });
    // Journal BEFORE launch. A crash on either side of spawn is ambiguous, never retried.
    s.active = { ...job, phase: 'dispatching', started_at: now() }; s.queue.shift(); s.jobs_started++;
    this.save(s); immutable(path.join(logDir, 'job.json'), s.active); this.event('dispatch', s.active);
    try {
      if (job.kind === 'build') {
        const output = path.join(this.root, 'Renders', 'stills', job.round_id);
        if (fs.existsSync(output)) throw Error('Round output already exists: reconcile duplicate/stale evidence');
        fs.mkdirSync(output, { recursive: true });
      }
      if (job.kind === 'review') {
        job.previous_images = s.accepted.flatMap(a => a.images.map(i => path.relative(this.root, i.path).replaceAll('\\', '/')));
        for (const item of s.accepted.flatMap(a => a.images)) if (hash(item.path) !== item.sha256) throw Error('Previously accepted evidence changed');
        job.reference_sha256 = hash(path.join(this.root, '_reference', 'PrimaryReference.png'));
        s.active = { ...s.active, previous_images: job.previous_images, reference_sha256: job.reference_sha256 }; this.save(s);
        const current = await validatePackage(this.root, { ...job, job_id: job.build_job_id });
        if (current.manifest_sha256 !== job.package.manifest_sha256) throw Error('Evidence changed before review');
      }
      const result = this.adapter ? await this.adapter.run(job, this) : await this.run(job, logDir);
      immutable(path.join(logDir, 'exit.json'), { ...result, ended_at: now() });
      if (result.code !== 0) throw Error(`Job failed (exit ${result.code}); inspect logs and permissions/authentication`);
      await this.safe();
      await this.finish(job, result, s);
      s.completed_jobs.push(job.job_id); s.active = null; this.save(s); this.event('completed', { job_id: job.job_id });
      return true;
    } catch (e) {
      s.active = { ...this.state().active, phase: 'needs_reconciliation', error: e.message }; this.save(s);
      this.pause(e.message); return false;
    }
  }
  async finish(job, result, s) {
    if (job.kind === 'build') {
      const pack = await validatePackage(this.root, job);
      immutable(path.join(this.w, 'logs', job.job_id, 'validated-package.json'), pack);
      s.rounds[job.round_id].status = 'awaiting_review';
      s.queue.unshift({ ...job, kind: 'review', job_id: crypto.randomUUID(), build_job_id: job.job_id,
        package: pack });
      // Review identity must continue to name the dispatched BUILDER, not the review process.
    } else if (job.kind === 'review') {
      const r = result.value;
      if (!r || r.round_id !== job.round_id || r.build_job_id !== job.build_job_id || r.prompt_sha256 !== job.prompt_sha256 || r.manifest_sha256 !== job.package.manifest_sha256) throw Error('Review identity mismatch');
      if (!['PASS', 'REVISE', 'NEEDS INPUT'].includes(r.verdict) || !r.summary || !Array.isArray(r.unverified_requirements) || !Array.isArray(r.findings)) throw Error('Invalid review');
      const required = [...job.package.images.map(i => path.relative(this.root, i.path).replaceAll('\\', '/')), '_reference/PrimaryReference.png', ...(job.previous_images || [])];
      if (!Array.isArray(r.inspected_images) || (r.verdict !== 'NEEDS INPUT' && required.some(p => !r.inspected_images.includes(p)))) throw Error('Review did not inspect every required image');
      if (r.motion_verified !== false || r.loop_verified !== false || !r.unverified_requirements.includes('motion') || !r.unverified_requirements.includes('seamless_loop')) throw Error('Still-only review must explicitly leave motion and seamless_loop unverified');
      if (!r.reference_comparison || !r.previous_evidence_comparison) throw Error('Missing visual comparisons');
      const current = await validatePackage(this.root, { ...job, job_id: job.build_job_id });
      if (current.manifest_sha256 !== job.package.manifest_sha256) throw Error('Evidence mutated during review');
      if (hash(path.join(this.root, '_reference', 'PrimaryReference.png')) !== job.reference_sha256) throw Error('Reference changed during review');
      for (const item of s.accepted.flatMap(a => a.images)) if (hash(item.path) !== item.sha256) throw Error('Accepted evidence changed during review');
      immutable(path.join(this.w, 'reviews', job.round_id + '.json'), r);
      immutable(path.join(this.w, 'reviews', job.round_id + '.md'), `# ${job.round_id}: ${r.verdict}\n\n${r.summary}\n\nReference: ${r.reference_comparison}\n\nPrevious evidence: ${r.previous_evidence_comparison}\n\n${r.findings.map(x => '- ' + x).join('\n')}\n\nUnverified: ${r.unverified_requirements.join(', ')}\n`);
      s.rounds[job.round_id].status = r.verdict;
      if (r.verdict === 'PASS') s.accepted.push({ round_id: job.round_id, images: job.package.images });
      if (job.round_id === 'TRAIN-00' && r.verdict !== 'NEEDS INPUT') {
        s.queue.unshift({ ...job, kind: 'draft', job_id: crypto.randomUUID() });
      } else if (r.verdict !== 'PASS') this.pause(`${r.verdict}: direction/revised authorization needed; no blind corrections`);
    } else {
      const d = result.value;
      if (!d || d.round_id !== 'TRAIN-01' || d.queued !== false || !d.prompt) throw Error('Invalid unqueued draft');
      immutable(path.join(this.w, 'prompt', 'TRAIN-01.md'), '# DRAFT — UNAUTHORIZED — UNQUEUED\n\n' + d.prompt + '\n');
      s.drafts.push('TRAIN-01'); this.pause('Baseline assessed; TRAIN-01 draft awaits user scope approval');
    }
    fs.appendFileSync(path.join(this.w, 'PLAN.md'), `\n- ${now()}: ${job.round_id} ${job.kind} completed${result.value?.verdict ? ': ' + result.value.verdict : ''}. Job ${job.job_id}.\n`);
  }
  async run(job, dir) {
    const cfg = read(path.join(this.w, 'config.json'));
    const role = job.kind === 'build' ? 'CLAUDE_ROLE.md' : 'CODEX_ROLE.md';
    const identity = { ...job, job_id: job.kind === 'build' ? job.job_id : job.build_job_id };
    const prompt = [fs.readFileSync(path.join(this.w, role), 'utf8'), fs.readFileSync(path.join(this.w, 'PROTOCOL.md'), 'utf8'),
      'DISPATCH (authoritative identity):', JSON.stringify(identity, null, 2),
      fs.readFileSync(inside(this.root, job.prompt_path), 'utf8'),
      job.kind === 'draft' ? 'DRAFT ONLY: Read the completed baseline review. Return JSON {round_id:"TRAIN-01",queued:false,prompt:"..."}. Propose bounded scope for user approval, preserving all locks. No scene work.' : '',
      job.kind === 'review' ? 'REVIEW ONLY: Return only JSON matching Workflow/review.schema.json. Inspect attached pixels. Read manifest and completion; builder claims are not verification.' : ''
    ].join('\n\n');
    immutable(path.join(dir, 'input.md'), prompt);
    const args = job.kind === 'build' ? ['-p', '--output-format', 'json', '--permission-mode', 'manual', '--permission-prompts', 'none'] :
      [...cfg.codex.prefix, 'exec', '--sandbox', 'read-only', '--json', '--output-last-message', path.join(dir, 'response.json')];
    if (job.kind !== 'build') {
      args.push('--output-schema', path.join(this.w, job.kind === 'review' ? 'review.schema.json' : 'draft.schema.json'));
      if (job.kind === 'review') {
        const images = [...job.package.images.map(i => i.path), path.join(this.root, '_reference', 'PrimaryReference.png'), ...job.previous_images.map(p => inside(this.root, p))];
        await decodeImages(images);
        for (const p of images) args.push('--image', p);
      }
      args.push('-');
    }
    const executable = job.kind === 'build' ? cfg.claude.executable : cfg.codex.executable;
    immutable(path.join(dir, 'command.json'), { executable, args, cwd: this.root });
    const stdout = fs.openSync(path.join(dir, 'stdout.log'), 'wx');
    const stderr = fs.openSync(path.join(dir, 'stderr.log'), 'wx');
    let child;
    try {
      child = spawn(executable, args, { cwd: this.root, stdio: ['pipe', stdout, stderr], windowsHide: true, shell: false });
      const s = this.state(); s.active.pid = child.pid; s.active.phase = 'running'; this.save(s);
      const outcome = new Promise((resolve, reject) => { child.on('error', reject); child.on('exit', code => resolve({ code })); });
      child.stdin.on('error', () => {}); child.stdin.end(prompt);
      let timer;
      const timeout = new Promise((_, reject) => { timer = setTimeout(() => reject(Error('Job timeout; process NOT killed. Reconcile all child/render processes.')), cfg.job_timeout_seconds * 1000); });
      let result;
      try { result = await Promise.race([outcome, timeout]); } finally { clearTimeout(timer); }
      if (result.code === 0) {
        if (job.kind === 'build') {
          const envelope = read(path.join(dir, 'stdout.log'));
          if (envelope.is_error || envelope.permission_denials?.length) throw Error('Claude reported error or permission denial');
        } else result.value = read(path.join(dir, 'response.json'));
      }
      return result;
    } finally { fs.closeSync(stdout); fs.closeSync(stderr); }
  }
}

async function main() {
  const c = new Coordinator(); const [command = 'status', ...args] = process.argv.slice(2);
  if (command === 'status') { console.log(JSON.stringify({ ...c.state(), paused: c.blocked(), pause: fs.existsSync(path.join(c.w, 'PAUSE')) ? read(path.join(c.w, 'PAUSE')) : null, coordinator: fs.existsSync(path.join(c.w, 'coordinator.lock')) ? read(path.join(c.w, 'coordinator.lock')) : null }, null, 2)); return; }
  if (command === 'pause' || command === 'stop') { c.pause(`Operator ${command}`); if (command === 'stop') write(path.join(c.w, 'STOP'), { at: now() }); console.log('Dispatch paused; active work drains. No processes killed.'); return; }
  if (command === 'ready') {
    if (!c.blocked() || c.state().active || !args.join(' ').trim()) throw Error('While paused and idle, use ready "notes confirming exclusive editor access and resolved unsaved changes"');
    await c.safe(); write(path.join(c.w, 'operator-ready.json'), { at: now(), notes: args.join(' ') });
    c.event('operator_ready', { notes: args.join(' ') }); console.log('Readiness recorded for four hours; no jobs started.'); return;
  }
  // Control flag changes do not mutate status.json and work while start holds its ownership lock.
  if (command === 'resume') {
    if (c.state().active) throw Error('Active job must drain or be reconciled before resume');
    await c.safe();
    if (c.state().jobs_started >= c.state().run_limit) throw Error('Run limit exhausted; explicitly set a larger limit');
    for (const n of ['PAUSE', 'STOP']) if (fs.existsSync(path.join(c.w, n))) fs.unlinkSync(path.join(c.w, n));
    write(path.join(c.w, 'WAKE'), { at: now() });
    c.event('resumed'); console.log('Resumed; run start or cycle, or existing scheduler wakes.'); return;
  }
  const release = lock(path.join(c.w, 'coordinator.lock'), { command });
  try {
    if (command === 'enqueue') { const s = c.state(); if (s.active) throw Error('Reconcile active job first'); c.enqueue(s, args[0]); c.save(s); }
    else if (command === 'limit') { const n = Number(args[0]); if (!Number.isInteger(n) || n < 1) throw Error('Positive job limit required'); const s = c.state(); s.run_limit = n; c.save(s); c.event('limit', { limit: n }); }
    else if (command === 'cycle' || command === 'start') {
      if (command === 'cycle') { await c.cycle(); console.log('Single job cycle finished.'); return; }
      console.log('Coordinator running. Idle check: 600 s. Pause/stop from another terminal.');
      while (!fs.existsSync(path.join(c.w, 'STOP'))) {
        const completed = await c.cycle();
        if (completed) continue; // completion triggers immediate next scheduling check
        for (let i = 0; i < 600; i++) {
          if (fs.existsSync(path.join(c.w, 'STOP'))) break;
          if (fs.existsSync(path.join(c.w, 'WAKE'))) { fs.unlinkSync(path.join(c.w, 'WAKE')); break; }
          await sleep(1000);
        }
      }
    } else throw Error('Commands: start | pause | resume | stop | status | cycle | enqueue ROUND | limit N | ready NOTES');
  } finally { release(); }
}
if (process.argv[1] && path.resolve(process.argv[1]) === import.meta.filename) main().catch(e => { console.error(e.message); process.exitCode = 1; });
