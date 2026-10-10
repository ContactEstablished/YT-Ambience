import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { chromium } from 'playwright';

export const root = path.resolve(import.meta.dirname, '..');
export const read = p => JSON.parse(fs.readFileSync(p, 'utf8').replace(/^\uFEFF/, ''));
export const hash = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
export const now = () => new Date().toISOString();
export const sleep = ms => new Promise(r => setTimeout(r, ms));
export function write(p, value) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  const tmp = `${p}.${process.pid}.tmp`;
  fs.writeFileSync(tmp, JSON.stringify(value, null, 2) + '\n');
  fs.renameSync(tmp, p);
}
export function immutable(p, value) {
  fs.mkdirSync(path.dirname(p), { recursive: true });
  fs.writeFileSync(p, typeof value === 'string' ? value : JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
}
export function inside(base, relative) {
  if (typeof relative !== 'string' || path.isAbsolute(relative)) throw Error('Expected relative path');
  const p = path.resolve(base, relative);
  if (!p.startsWith(path.resolve(base) + path.sep)) throw Error(`Path escapes root: ${relative}`);
  // Reject links/junctions that could point outside the root, including existing ancestors.
  let ancestor = p;
  while (!fs.existsSync(ancestor)) ancestor = path.dirname(ancestor);
  const real = fs.realpathSync(ancestor);
  const realBase = fs.realpathSync(base);
  if (real !== realBase && !real.startsWith(realBase + path.sep)) throw Error('Linked path escapes root');
  return p;
}
export function lock(p, data) {
  try { immutable(p, { pid: process.pid, created: now(), ...data }); }
  catch { throw Error(`Lock exists: ${p}. Reconcile; never steal it automatically.`); }
  return () => fs.unlinkSync(p);
}
export function live(pid) {
  try { process.kill(pid, 0); return true; } catch (e) { return e.code !== 'ESRCH'; }
}
export function renderProcesses() {
  if (process.platform !== 'win32') throw Error('Real render guard requires Windows');
  const script = "$ErrorActionPreference='Stop'; $p=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -like 'UnrealEditor*' }); if (@($p | Where-Object { -not $_.CommandLine }).Count) { throw 'Cannot inspect Unreal command line' }; @($p | Where-Object { $_.Name -like '*-Cmd*' -or $_.CommandLine -match '(?i)(-game|MoviePipeline|MovieRender| -Render)' } | Select-Object ProcessId,Name) | ConvertTo-Json -Compress";
  const out = execFileSync('powershell.exe', ['-NoProfile', '-Command', script], { encoding: 'utf8', windowsHide: true }).trim();
  return out ? [JSON.parse(out)].flat() : [];
}
export async function decodeImages(paths) {
  const browser = await chromium.launch({ headless: true });
  try {
    const page = await browser.newPage();
    const result = [];
    for (const p of paths) {
      const data = fs.readFileSync(p).toString('base64');
      const size = await page.evaluate(async data => {
        const img = new Image(); img.src = 'data:image/png;base64,' + data;
        await img.decode();
        if (!img.naturalWidth || !img.naturalHeight) throw Error('Empty image');
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth; canvas.height = img.naturalHeight;
        const ctx = canvas.getContext('2d'); ctx.drawImage(img, 0, 0);
        ctx.getImageData(0, 0, canvas.width, canvas.height);
        return [canvas.width, canvas.height];
      }, data);
      result.push({ path: p, sha256: hash(p), size });
    }
    return result;
  } finally { await browser.close(); }
}

export async function validatePackage(base, job) {
  const dir = inside(base, `Renders/stills/${job.round_id}`);
  const manifestPath = path.join(dir, 'manifest.json');
  const m = read(manifestPath);
  const marker = fs.readFileSync(path.join(dir, 'COMPLETE ROUND.md'), 'utf8');
  for (const key of ['round_id', 'job_id', 'prompt_path', 'prompt_sha256']) {
    if (m[key] !== job[key] || !marker.includes(job[key])) throw Error(`Package identity mismatch: ${key}`);
  }
  if (hash(inside(base, job.prompt_path)) !== job.prompt_sha256) throw Error('Dispatched prompt changed');
  if (m.schema_version !== 1 || m.status !== 'complete' || m.render_active !== false) throw Error('Incomplete package');
  if (['changes', 'known_issues', 'unverified_requirements'].some(k => !Array.isArray(m[k]) || m[k].some(v => typeof v !== 'string'))) throw Error('Missing/invalid package records');
  if (!Array.isArray(m.validation) || !m.validation.length || m.validation.some(v => !v.check || v.result !== 'PASS' || !v.details)) throw Error('Unresolved validation failure');
  if (job.round_id === 'TRAIN-00' && m.changes.length) throw Error('Baseline must not change the scene');
  if (!Array.isArray(m.outputs) || new Set(m.outputs.map(o => o.path)).size !== m.outputs.length) throw Error('Duplicate/missing outputs');
  for (const name of job.required_images) {
    if (!m.outputs.some(o => o.path === `Renders/stills/${job.round_id}/${name}` && o.kind === 'image')) throw Error(`Missing required image: ${name}`);
  }
  const images = [];
  for (const o of m.outputs) {
    const p = inside(base, o.path);
    if (!p.startsWith(dir + path.sep)) throw Error('Output must be in its round folder');
    if (!['image', 'video', 'report'].includes(o.kind) || typeof o.description !== 'string' || !o.description || typeof o.source !== 'string' || !o.source || hash(p) !== o.sha256) throw Error(`Invalid output: ${o.path}`);
    if (o.kind === 'image') images.push(p);
  }
  if (!images.length) throw Error('No review images');
  const decoded = await decodeImages(images);
  if (job.minimum_image_size && decoded.some(i => i.size[0] < job.minimum_image_size[0] || i.size[1] < job.minimum_image_size[1])) throw Error('Image resolution is below round requirement');
  for (const capture of job.required_captures || []) {
    const logs = inside(base, `Workflow/logs/${job.kind === 'review' ? job.build_job_id : job.job_id}`);
    const receipts = fs.readdirSync(logs).filter(n => /^ue-.*\.json$/.test(n)).map(n => read(path.join(logs, n)));
    const image = m.outputs.find(o => o.path === `Renders/stills/${job.round_id}/${capture.image}`);
    if (!receipts.some(r => r.job_id === m.job_id && r.mode === 'render' && r.process_seen === true && r.tag === capture.tag && r.output_sha256 === image?.sha256 && r.render_processes_remaining?.length === 0)) throw Error(`Missing guarded capture receipt: ${capture.tag}`);
  }
  return { manifest_sha256: hash(manifestPath), images: decoded, manifest: m };
}
