#!/usr/bin/env node
// Prompt 10: the loop seam. Encodes Renders/frames/<tag>/LS_Sweep.#####.png, rendered over [0, loop + tail)
// (render.py --frames 0-744; make_sweep.py keys the tail as the loop's own first second), into:
//   Renders/<tag>_loop.mp4   the seamless loop: frames [0, loop), its first `tail` frames crossfaded from the tail
//                            (frame loop + k is the same moment as frame k for everything the sequence drives, and the
//                            rain particles in it carry straight on from frame loop - 1), so playback wraps cleanly
//   Renders/<tag>_seam.mp4   the boundary for review: the loop's last `ctx` frames then its first `ctx`, `repeat` times,
//                            labelled with frame numbers and a mark on the first frame after the wrap; then the same
//                            boundary as a hard cut (no crossfade) for comparison, `repeat` times
//   Renders/<tag>_seam_diff.txt  mean frame-to-frame change (8-bit luma, whole frame and three regions) across the
//                            boundary, both versions: a reset or pop shows as a spike at the wrap
//   node Scripts/encode_loop.mjs <tag> [--loop 720] [--tail 24] [--ctx 48] [--repeat 3] [--crf 16]
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const argv = process.argv.slice(2);
const opt = (k, d) => (argv.includes(k) ? Number(argv[argv.indexOf(k) + 1]) : d);
const tag = argv[0];
if (!tag) { console.error('usage: node Scripts/encode_loop.mjs <tag> [--loop 720] [--tail 24] [--ctx 48] [--repeat 3]'); process.exit(2); }
const L = opt('--loop', 720), N = opt('--tail', 24), C = opt('--ctx', 48), R = opt('--repeat', 3), crf = String(opt('--crf', 16));
const dir = path.join(root, 'Renders', 'frames', tag);
const pat = path.join(dir, 'LS_Sweep.%05d.png');
const have = new Set(fs.readdirSync(dir).filter((f) => /^LS_Sweep\.\d+\.png$/.test(f)).map((f) => Number(f.match(/(\d+)\.png$/)[1])));
const missing = [];
for (let f = 0; f < L + N; f++) if (!have.has(f)) missing.push(f);
if (missing.length) { console.error(`missing ${missing.length} frames (e.g. ${missing.slice(0, 8).join(', ')}): re-render them first`); process.exit(1); }

const ff = (args, label) => {
  const r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', ...args], { encoding: 'utf8', maxBuffer: 1 << 26 });
  if (r.status !== 0) { console.error(`${label} failed:\n${r.stderr}`); process.exit(1); }
  return r;
};
const seq = (start) => ['-framerate', '24', '-start_number', String(start), '-i', pat];
const x264 = ['-c:v', 'libx264', '-preset', 'slow', '-crf', crf, '-pix_fmt', 'yuv420p', '-movflags', '+faststart'];
const NORM = 'settb=AVTB,setpts=N/24/TB,fps=24,format=yuv420p';
const xf = (a, b, out) => `[${a}]${NORM}[xa];[${b}]${NORM}[xb];` +
  `[xa][xb]xfade=transition=fade:duration=${N / 24}:offset=0,format=yuv420p[${out}]`;

// 1. the loop: tail frames [L, L+N) fading into the loop's frames [0, L)
const loopOut = path.join(root, 'Renders', `${tag}_loop.mp4`);
ff([...seq(L, N), ...seq(0, L), '-filter_complex',
  `[0:v]trim=end_frame=${N}[t];[1:v]trim=end_frame=${L}[a];${xf('t', 'a', 'v')}`, '-map', '[v]', '-frames:v', String(L), ...x264, loopOut], 'loop');

// 2. the boundary clip: crossfaded (as delivered), then the raw hard cut, each R times, labelled
const font = 'C\\:/Windows/Fonts/consola.ttf';
const label = (first, name) => `drawtext=fontfile='${font}':fontsize=30:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=8:x=24:y=24:` +
  `text='${name}   frame %{eif\\:if(lt(mod(n\\,${2 * C})\\,${C})\\,${L - C}+mod(n\\,${2 * C})\\,mod(n\\,${2 * C})-${C})\\:d}',` +
  `drawtext=fontfile='${font}':fontsize=30:fontcolor=yellow:box=1:boxcolor=black@0.55:boxborderw=8:x=24:y=78:` +
  `text='LOOP WRAPS HERE':enable='between(mod(n\\,${2 * C})\\,${C}\\,${C + 5})'`;
const seamOut = path.join(root, 'Renders', `${tag}_seam.mp4`);
ff([...seq(L - C, C), ...seq(L, N), ...seq(0, C), ...seq(0, C), '-filter_complex',
  `[0:v]trim=end_frame=${C},${NORM}[end];` +
  `[1:v]trim=end_frame=${N}[t];[2:v]trim=end_frame=${C}[a0];${xf('t', 'a0', 'head')};` +
  `[3:v]trim=end_frame=${C},${NORM}[headraw];[end]split=2[e1][e2];` +
  `[e1][head]concat=n=2:v=1[cf];[cf]loop=${R - 1}:${2 * C}:0,setpts=N/24/TB,${label(L - C, 'loop (crossfaded tail)')}[cfl];` +
  `[e2][headraw]concat=n=2:v=1[hc];[hc]loop=${R - 1}:${2 * C}:0,setpts=N/24/TB,${label(L - C, 'hard cut, no crossfade')}[hcl];` +
  `[cfl][hcl]concat=n=2:v=1[v]`, '-map', '[v]', ...x264, seamOut], 'seam');

// 3. frame-to-frame change across the boundary (whole frame, sky + city, kiosk, wet foreground)
const regions = { frame: null, sky: 'crop=iw:ih*0.35:0:0', kiosk: 'crop=iw*0.5:ih*0.4:iw*0.25:ih*0.35', ground: 'crop=iw:ih*0.25:0:ih*0.75' };
const lines = [];
for (const [variant, head] of [['crossfaded', 'xf'], ['hard cut', 'raw']]) {
  for (const [name, crop] of Object.entries(regions)) {
    const headGraph = head === 'xf' ? `[1:v]trim=end_frame=${N}[t];[2:v]trim=end_frame=${C}[a0];${xf('t', 'a0', 'h')}`
      : `[2:v]trim=end_frame=${C},${NORM}[h]`;
    const r = ff([...seq(L - C, C), ...seq(L, N), ...seq(0, C), '-filter_complex',
      `[0:v]trim=end_frame=${C},${NORM}[e];${headGraph};[e][h]concat=n=2:v=1,${crop ? crop + ',' : ''}` +
      `format=gray,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-`, '-f', 'null', '-'], 'diff');
    const v = [...r.stdout.matchAll(/YAVG=([\d.]+)/g)].map((m) => Number(m[1]));
    // v[i] = change from clip frame i to i+1; the wrap is i = C - 1 (frame L-1 -> frame 0)
    const w = v[C - 1], around = v.slice(C - 13, C - 1).concat(v.slice(C, C + 12));
    const mean = around.reduce((a, b) => a + b, 0) / around.length, mx = Math.max(...around);
    lines.push(`${variant.padEnd(10)} ${name.padEnd(6)} wrap ${w.toFixed(2)}   neighbours mean ${mean.toFixed(2)} max ${mx.toFixed(2)}   ratio ${(w / mean).toFixed(2)}`);
  }
}
// 4. the whole loop, played twice (so the wrap is inside): flag any step whose change jumps above its neighbourhood
const scan = [];
for (const [name, crop] of Object.entries(regions)) {
  const r = ff(['-stream_loop', '1', '-i', loopOut, '-vf',
    `${crop ? crop + ',' : ''}format=gray,tblend=all_mode=difference,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-`,
    '-f', 'null', '-'], 'scan');
  const v = [...r.stdout.matchAll(/YAVG=([\d.]+)/g)].map((m) => Number(m[1]));
  const flags = [];
  for (let i = 0; i < v.length; i++) {  // v[i]: the change from frame i to i + 1 of the doubled loop
    const win = v.slice(Math.max(0, i - 12), i).concat(v.slice(i + 1, i + 13)).sort((p, q) => p - q);
    const med = win[Math.floor(win.length / 2)];
    if (v[i] > Math.max(med * 2.5, med + 1.5)) flags.push(`${i % L}->${(i + 1) % L} (${v[i].toFixed(1)} vs ${med.toFixed(1)})`);
  }
  const m = v.reduce((p, q) => p + q, 0) / v.length;
  scan.push(`${name.padEnd(6)} mean step ${m.toFixed(2)}  spikes: ${flags.length ? [...new Set(flags)].join(', ') : 'none'}`);
}
lines.push('', 'Whole loop played twice (the wrap included), steps more than 2.5x their 24-step neighbourhood median:', ...scan);
const diffOut = path.join(root, 'Renders', `${tag}_seam_diff.txt`);
fs.writeFileSync(diffOut, `Mean frame-to-frame change (8-bit luma) at the wrap (frame ${L - 1} -> 0) vs the 24 steps around it\n${lines.join('\n')}\n`);
console.log(lines.join('\n'));
console.log(`-> ${loopOut}\n-> ${seamOut}\n-> ${diffOut}`);
