#!/usr/bin/env node
// Projects kiosk-frame boxes through the solved reference camera, and fits
// roof items so their projected footprint matches where they appear in
// PrimaryReference.png. Prints suggested (cx, cy) for kiosk_config.py.
//
//   node fit_to_reference.mjs

const PX = 836, PY = 470.5, F = 1496.92;
const CAM = { pos: [-9.94, -8.76, 0.05], heading: 35.8, pitch: 12.8 };
const DECK = 2.95;

const rad = (d) => (d * Math.PI) / 180;
const h = rad(CAM.heading), p = rad(CAM.pitch);
const Fw = [Math.cos(p) * Math.cos(h), Math.cos(p) * Math.sin(h), Math.sin(p)];
const R = [Math.sin(h), -Math.cos(h), 0];
const U = [-Math.sin(p) * Math.cos(h), -Math.sin(p) * Math.sin(h), Math.cos(p)];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

export function project(P) {
  const d = [P[0] - CAM.pos[0], P[1] - CAM.pos[1], P[2] - CAM.pos[2]];
  const z = dot(d, Fw);
  return [PX + (F * dot(d, R)) / z, PY - (F * dot(d, U)) / z];
}

// Image-space bbox of a box sitting on the deck.
function boxBBox(cx, cy, w, d, ht, z0 = DECK) {
  const xs = [], ys = [];
  for (const dx of [-w / 2, w / 2]) for (const dy of [-d / 2, d / 2]) for (const z of [z0, z0 + ht]) {
    const [x, y] = project([cx + dx, cy + dy, z]);
    xs.push(x); ys.push(y);
  }
  return { x0: Math.min(...xs), x1: Math.max(...xs), top: Math.min(...ys) };
}

// Targets read off the reference (p_roof crop): image x-range and top y.
// size = [w, d, h] from kiosk_config.py; start = current (cx, cy).
const items = [
  { name: 'SmallUnit', size: [0.60, 0.50, 0.45], start: [-2.50, 0.55], x: [432, 487], top: 360 },
  { name: 'ACCondenser', size: [0.70, 1.00, 0.75], start: [-2.10, -0.25], x: [487, 565], top: 320 },
  { name: 'TallCabinet', size: [0.80, 0.70, 1.00], start: [-1.35, -0.60], x: [560, 670], top: 302 },
  { name: 'TankCluster', size: [1.10, 0.55, 0.90], start: [-0.60, -1.05], x: [680, 770], top: 322 },
  { name: 'StickerCabinet', size: [0.60, 0.50, 0.80], start: [-0.40, -1.80], x: [760, 820], top: 335 },
  { name: 'CableReel', size: [0.90, 0.40, 0.90], start: [1.30, -0.70], x: [805, 875], top: 390 },
  { name: 'WhiteBox', size: [0.55, 0.45, 0.40], start: [0.42, -1.93], x: [870, 925], top: 405 },
  { name: 'Mast', size: [0.15, 0.15, 1.65], start: [1.32, -1.28], x: [882, 902], top: 315 },
];

function fit(it) {
  const [w, d, ht] = it.size;
  const tx = (it.x[0] + it.x[1]) / 2;
  let best = null;
  // Grid search over the roof deck, keeping the item on the canopy footprint.
  for (let cx = -2.85 + w / 2; cx <= 2.55 - w / 2; cx += 0.025) {
    for (let cy = -2.25 + d / 2; cy <= 1.95 - d / 2; cy += 0.025) {
      const b = boxBBox(cx, cy, w, d, ht);
      const err = ((b.x0 + b.x1) / 2 - tx) ** 2 + 0.5 * (b.top - it.top) ** 2;
      if (!best || err < best.err) best = { cx, cy, err, b };
    }
  }
  return best;
}

const r2 = (v) => Math.round(v * 100) / 100;
for (const it of items) {
  const cur = boxBBox(...it.start, ...it.size);
  const best = fit(it);
  console.log(
    `${it.name.padEnd(15)} target x ${it.x.join('-')} top ${it.top} | current x ${cur.x0.toFixed(0)}-${cur.x1.toFixed(0)} top ${cur.top.toFixed(0)}` +
      ` | fit (${r2(best.cx)}, ${r2(best.cy)}) -> x ${best.b.x0.toFixed(0)}-${best.b.x1.toFixed(0)} top ${best.b.top.toFixed(0)}`,
  );
}

// Text centring on the canopy bands: where along each band does the reference text sit?
const bandFront = (X) => project([X, -2.27, 2.70]);
const bandLeft = (Y) => project([-2.87, Y, 2.70]);
const solveX = (target, fn, lo, hi) => {
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (fn(mid)[0] < target) lo = mid; else hi = mid;
  }
  return (lo + hi) / 2;
};
console.log('front band: "coffee, ramen, implant" spans X',
  r2(solveX(735, bandFront, -2.85, 2.55)), 'to', r2(solveX(925, bandFront, -2.85, 2.55)), '; circle mark at X', r2(solveX(935, bandFront, -2.85, 2.55)));
// Left band runs right-to-left as Y increases, so invert the search.
const solveY = (target) => {
  let lo = -2.25, hi = 1.95;
  for (let i = 0; i < 60; i++) {
    const mid = (lo + hi) / 2;
    if (bandLeft(mid)[0] > target) lo = mid; else hi = mid;
  }
  return (lo + hi) / 2;
};
console.log('left band: 珈琲 starts at Y', r2(solveY(355)), '; 義体 ends at Y', r2(solveY(515)), '; bowl icon centre at Y', r2(solveY(565)));
console.log('ticket machine (ref x 668-725, y 595-690) -> front wall X', r2(solveX(668, (X) => project([X, -1.80, 1.3]), -2.2, 2.2)), 'to', r2(solveX(725, (X) => project([X, -1.80, 1.3]), -2.2, 2.2)));
