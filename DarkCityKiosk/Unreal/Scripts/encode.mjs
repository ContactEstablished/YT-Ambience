#!/usr/bin/env node
// Encodes Renders/frames/<tag>/LS_Sweep.#####.png into Renders/<tag>.mp4 (H.264, 24 fps).
//   node Scripts/encode.mjs <tag> [--crf 16]
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const tag = process.argv[2];
const crf = process.argv.includes('--crf') ? process.argv[process.argv.indexOf('--crf') + 1] : '16';
if (!tag) { console.error('usage: node Scripts/encode.mjs <tag> [--crf 16]'); process.exit(2); }
const dir = path.join(root, 'Renders', 'frames', tag);
const frames = fs.readdirSync(dir).filter((f) => /^LS_Sweep\.\d+\.png$/.test(f)).sort();
if (!frames.length) { console.error(`no frames in ${dir}`); process.exit(1); }
const first = Number(frames[0].match(/\.(\d+)\.png$/)[1]);
const out = path.join(root, 'Renders', `${tag}.mp4`);
const r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', '24', '-start_number', String(first),
  '-i', path.join(dir, 'LS_Sweep.%05d.png'), '-c:v', 'libx264', '-preset', 'slow', '-crf', crf,
  '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out], { stdio: 'inherit' });
if (r.status !== 0) process.exit(r.status ?? 1);
console.log(`${frames.length} frames -> ${out}`);
