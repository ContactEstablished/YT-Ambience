// Kiosk graphics art (signage pass, 2026-10-05): draws every poster, notice, label, sticker, sign face
// and paint decal in headless Chromium (system fonts: Yu Gothic, Bahnschrift, Caveat...), ages them,
// packs them into four atlases and writes, per atlas, three maps plus one manifest:
//
//   Unreal/RawContent/graphics/T_KG_<Atlas>_C.png   albedo (sRGB) + opacity
//   Unreal/RawContent/graphics/T_KG_<Atlas>_N.png   normal (DirectX convention, like Unreal)
//   Unreal/RawContent/graphics/T_KG_<Atlas>_S.png   R roughness, G metallic, B emissive mask, A weather response
//   Unreal/RawContent/graphics/graphics_manifest.json   per item: atlas, pixel rect, UV rect, size in metres
//   Graphics/preview/<Atlas>.png                    albedo over grey, for checking
//
// Atlases: Paper (posters, notices, owner notes; 2 px/mm), Labels (maintenance labels, stickers,
// plates; 5 px/mm), Signs (lit faces + housing skin; 2 px/mm), Decals (marks in the paint, projected
// by Unreal deferred decals; 2 px/mm). The art is in Graphics/art/*.js.
//
//   node Graphics/make_kiosk_graphics.mjs [Paper,Labels,...] [--only name,name]
// Blender (build_graphics.py) reads the manifest to size and UV the cards; Unreal (kiosk_graphics.py)
// imports the maps.
import fs from 'node:fs';
import path from 'node:path';
import zlib from 'node:zlib';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, '..', 'Unreal', 'RawContent', 'graphics');
const PREVIEW = path.join(HERE, 'preview');
const ATLASES = {
  Paper: { size: 2048, s: 2, gutter: 12, fill: [200, 196, 186, 0] },
  Labels: { size: 2048, s: 5, gutter: 12, fill: [200, 200, 200, 0] },
  Signs: { size: 2048, s: 2, gutter: 12, fill: [250, 220, 120, 0] },
  Decals: { size: 2048, s: 2, gutter: 12, fill: [200, 160, 60, 0] },
  Kitchen: { size: 2048, s: 4, gutter: 12, fill: [120, 120, 120, 0] },  // kitchen pass (10/9): terminal, tickets, tape labels, packaging
  Exterior: { size: 2048, s: 4, gutter: 12, fill: [110, 110, 105, 0] },  // exterior pass (10/9): crates, bins, cylinders, cabinet, cartons
};
const SCRIPTS = ['lib.js', 'paper.js', 'labels.js', 'signs.js', 'decals.js', 'kitchen.js', 'exterior.js', 'build.js'];

const argv = process.argv.slice(2);
const onlyIdx = argv.indexOf('--only');
const only = onlyIdx >= 0 ? argv[onlyIdx + 1].split(',') : null;
const names = argv.filter((a, i) => !a.startsWith('--') && (onlyIdx < 0 || i !== onlyIdx + 1))
  .flatMap((a) => a.split(',')).filter((a) => ATLASES[a]);
const todo = names.length ? names : Object.keys(ATLASES);

// ---- PNG (RGBA 8-bit, unpremultiplied) -----------------------------------------------------------
const CRC = new Int32Array(256).map((_, n) => {
  let c = n;
  for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
  return c;
});
function crc32(buf) {
  let c = -1;
  for (let i = 0; i < buf.length; i++) c = CRC[(c ^ buf[i]) & 255] ^ (c >>> 8);
  return (c ^ -1) >>> 0;
}
function chunk(type, data) {
  const len = Buffer.alloc(4);
  len.writeUInt32BE(data.length);
  const td = Buffer.concat([Buffer.from(type, 'ascii'), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(td));
  return Buffer.concat([len, td, crc]);
}
function png(w, h, rgba, channels = 4) {
  const stride = w * channels;
  const raw = Buffer.alloc((stride + 1) * h);
  for (let y = 0; y < h; y++) {
    raw[y * (stride + 1)] = 0;
    if (channels === 4) rgba.copy(raw, y * (stride + 1) + 1, y * w * 4, (y + 1) * w * 4);
    else for (let x = 0; x < w; x++) for (let c = 0; c < channels; c++) raw[y * (stride + 1) + 1 + x * channels + c] = rgba[(y * w + x) * 4 + c];
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0);
  ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8;
  ihdr[9] = channels === 4 ? 6 : 2;
  return Buffer.concat([Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]), chunk('IHDR', ihdr),
    chunk('IDAT', zlib.deflateSync(raw, { level: 6 })), chunk('IEND', Buffer.alloc(0))]);
}

// ---- run -------------------------------------------------------------------------------------------
fs.mkdirSync(OUT, { recursive: true });
fs.mkdirSync(PREVIEW, { recursive: true });
const browser = await chromium.launch({ args: ['--use-angle=d3d11'] });
const page = await browser.newPage();
page.on('console', (m) => console.log('[page]', m.text()));
page.on('pageerror', (e) => console.error('[page error]', e.message));
await page.setContent('<!doctype html><html><head><meta charset="utf-8"></head><body></body></html>');
for (const f of SCRIPTS) await page.addScriptTag({ path: path.join(HERE, 'art', f) });

const manifestPath = path.join(OUT, 'graphics_manifest.json');
const manifest = fs.existsSync(manifestPath) ? JSON.parse(fs.readFileSync(manifestPath, 'utf8')) : { atlases: {}, items: {} };
for (const name of todo) {
  const cfg = ATLASES[name];
  const res = await page.evaluate(([n, c, o]) => window.ART.buildAtlas(n, c, o), [name, cfg, only]);
  const N = res.size;
  for (const map of ['C', 'N', 'S']) {
    const buf = Buffer.from(res[map], 'base64');
    fs.writeFileSync(path.join(OUT, `T_KG_${name}_${map}.png`), png(N, N, buf, map === 'N' ? 3 : 4));
    if (map === 'C') {
      // preview: albedo over mid grey
      const pv = Buffer.alloc(N * N * 4);
      for (let i = 0; i < N * N; i++) {
        const a = buf[i * 4 + 3] / 255;
        for (let c = 0; c < 3; c++) pv[i * 4 + c] = Math.round(buf[i * 4 + c] * a + 70 * (1 - a));
        pv[i * 4 + 3] = 255;
      }
      fs.writeFileSync(path.join(PREVIEW, `${name}.png`), png(N, N, pv, 3));
    }
  }
  manifest.atlases[name] = { size: N, px_per_mm: cfg.s };
  if (!only) for (const k of Object.keys(manifest.items)) if (manifest.items[k].atlas === name) delete manifest.items[k];
  Object.assign(manifest.items, res.manifest);
  console.log(`${name}: ${Object.keys(res.manifest).length} items, ${res.used}/${N} px rows used, ${res.ms} ms`);
}
fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, 1));
await browser.close();
console.log(`wrote ${OUT}`);
