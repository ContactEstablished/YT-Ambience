// Kiosk graphics art: shared helpers (runs in headless Chromium, loaded by make_kiosk_graphics.mjs).
//
// Every item is drawn as vector art on a canvas at its atlas density (px per mm), then aged per pixel:
// sun fade (yellow and magenta inks go first, so old prints drift cyan), paper yellowing, water stains
// with tide lines, edge dirt, creases and wrinkles, tears with fibrous edges, tape, scratches. The
// result is four maps per atlas cell:
//   C  albedo (sRGB) + opacity (torn edges, die-cut stickers, punched holes)
//   N  tangent-space normal (DirectX convention like Unreal: +V points down the image)
//   S  R roughness, G metallic, B emissive mask, A weather response (how much the wall's rain
//      streaks, grime and wetness show on it in Unreal: paper 1, vinyl ~0.4, metal ~0.3)
// Units: mm in item space; s = px per mm.

const ART = (window.ART = window.ART || {});

// ---- random + noise ---------------------------------------------------------------------------
ART.rng = function (seed) {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
};
function hash2(ix, iy, seed) {
  let h = (ix * 374761393 + iy * 668265263 + seed * 2246822519) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}
ART.hash2 = hash2;
function vnoise(x, y, seed) {
  const ix = Math.floor(x), iy = Math.floor(y);
  const fx = x - ix, fy = y - iy;
  const ux = fx * fx * (3 - 2 * fx), uy = fy * fy * (3 - 2 * fy);
  const a = hash2(ix, iy, seed), b = hash2(ix + 1, iy, seed), c = hash2(ix, iy + 1, seed), d = hash2(ix + 1, iy + 1, seed);
  return a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy;
}
ART.vnoise = vnoise;
ART.fbm = function (x, y, oct, seed) {
  let s = 0, amp = 0.5, f = 1, n = 0;
  for (let o = 0; o < oct; o++) {
    s += amp * vnoise(x * f, y * f, seed + o * 17);
    n += amp;
    amp *= 0.5;
    f *= 2.03;
  }
  return s / n;
};
const fbm = ART.fbm;
const clamp = (v, a = 0, b = 1) => (v < a ? a : v > b ? b : v);
const smooth = (e0, e1, x) => {
  const t = clamp((x - e0) / (e1 - e0));
  return t * t * (3 - 2 * t);
};
const mix = (a, b, t) => a + (b - a) * t;
ART.clamp = clamp;
ART.smooth = smooth;
ART.mix = mix;

// ---- colours ----------------------------------------------------------------------------------
ART.hex = function (h) {
  const n = parseInt(h.replace('#', ''), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => v / 255);
};
ART.css = function (c, a = 1) {
  return `rgba(${Math.round(c[0] * 255)},${Math.round(c[1] * 255)},${Math.round(c[2] * 255)},${a})`;
};

// ---- fonts ------------------------------------------------------------------------------------
ART.F = {
  jp: '"Yu Gothic", "YuGothic", "MS Gothic", sans-serif',
  jpMincho: '"MingLiU", "PMingLiU", "Yu Gothic", serif',
  latin: '"Bahnschrift", "Segoe UI", sans-serif',
  cond: '"Barlow Condensed", "Roboto Condensed", "Arial Narrow", sans-serif',
  round: '"Montserrat", "Segoe UI", sans-serif',
  mono: '"Consolas", "Cascadia Mono", monospace',
  hand: '"Caveat", "Segoe Print", cursive',
  hand2: '"Ink Free", "Segoe Print", cursive',
  impact: 'Impact, "Bahnschrift", sans-serif',
  barcode: '"Code39AzaleaRegular2", monospace',
  serif: '"Georgia", "Times New Roman", serif',
};

// ---- drawing helpers (mm units: call with g scaled by s) ---------------------------------------
ART.text = function (g, str, x, y, size, opt = {}) {
  g.save();
  g.font = `${opt.style || ''} ${opt.weight || 700} ${size}px ${opt.font || ART.F.jp}`;
  g.fillStyle = opt.color || '#111';
  g.textAlign = opt.align || 'left';
  g.textBaseline = opt.baseline || 'alphabetic';
  if (opt.ls) g.letterSpacing = `${opt.ls}px`;
  if (opt.maxW) {
    const w = g.measureText(str).width;
    if (w > opt.maxW) {
      g.translate(x, y);
      g.scale(opt.maxW / w, 1);
      x = 0;
      y = 0;
    }
  }
  if (opt.stroke) {
    g.strokeStyle = opt.stroke;
    g.lineWidth = opt.strokeW || size * 0.08;
    g.lineJoin = 'round';
    g.strokeText(str, x, y);
  }
  g.fillText(str, x, y);
  g.restore();
};
// fit a line of text into a box (w x h) centred at (cx, cy)
ART.fitText = function (g, str, cx, cy, w, h, opt = {}) {
  g.save();
  g.font = `${opt.weight || 700} ${h}px ${opt.font || ART.F.jp}`;
  if (opt.ls) g.letterSpacing = `${opt.ls * h}px`;
  const m = g.measureText(str);
  const asc = m.actualBoundingBoxAscent, desc = m.actualBoundingBoxDescent;
  const tw = m.width;
  const sx = Math.min(w / tw, opt.squeeze === false ? 1e9 : 1e9);
  const k = Math.min(1, w / tw);
  g.translate(cx, cy);
  g.scale(opt.stretch ? w / tw : k, opt.vscale || 1);
  g.fillStyle = opt.color || '#111';
  g.textAlign = 'center';
  g.textBaseline = 'alphabetic';
  const yoff = (asc - desc) / 2;
  if (opt.stroke) {
    g.strokeStyle = opt.stroke;
    g.lineWidth = opt.strokeW || h * 0.1;
    g.lineJoin = 'round';
    g.strokeText(str, 0, yoff);
  }
  g.fillText(str, 0, yoff);
  g.restore();
  return tw * (opt.stretch ? w / tw : k);
};
// vertical Japanese: one glyph per row, centred on x; long-vowel marks rotate to vertical
ART.vtext = function (g, str, x, y0, size, opt = {}) {
  const step = size * (opt.step || 1.02);
  let y = y0;
  for (const ch of str) {
    g.save();
    g.font = `${opt.weight || 700} ${size}px ${opt.font || ART.F.jp}`;
    g.fillStyle = opt.color || '#111';
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.translate(x, y + size / 2);
    if ('ーー〜～-'.includes(ch)) g.rotate(Math.PI / 2);
    if (ch === '、' || ch === '。') g.translate(size * 0.3, -size * 0.3);
    if (opt.stroke) {
      g.strokeStyle = opt.stroke;
      g.lineWidth = opt.strokeW || size * 0.08;
      g.lineJoin = 'round';
      g.strokeText(ch, 0, 0);
    }
    g.fillText(ch, 0, 0);
    g.restore();
    y += ch === ' ' ? step * 0.5 : step;
  }
  return y;
};
// handwriting: per-glyph jitter in size, angle, baseline; marker ink with soft edges
ART.hand = function (g, str, x, y, size, opt = {}) {
  const r = ART.rng(opt.seed || 7);
  g.save();
  g.fillStyle = opt.color || '#141414';
  g.textBaseline = 'alphabetic';
  let cx = x;
  const slant = opt.slant || -0.04;
  for (const ch of str) {
    const sz = size * (0.9 + 0.2 * r());
    g.save();
    g.font = `${opt.weight || 700} ${sz}px ${opt.font || ART.F.jp}`;
    const w = g.measureText(ch).width;
    g.translate(cx + w / 2, y + (r() - 0.5) * size * 0.08 + (cx - x) * slant);
    g.rotate((r() - 0.5) * 0.12 + (opt.rot || 0));
    g.scale(1 + (r() - 0.5) * 0.08, 1);
    if (opt.stroke !== false) {
      g.strokeStyle = g.fillStyle;
      g.lineWidth = sz * (opt.thick || 0.055);
      g.lineJoin = 'round';
      g.textAlign = 'center';
      g.strokeText(ch, 0, 0);
    }
    g.textAlign = 'center';
    g.fillText(ch, 0, 0);
    g.restore();
    cx += w * (opt.track || 0.98) + (r() - 0.5) * size * 0.04;
  }
  g.restore();
  return cx;
};
ART.rect = function (g, x, y, w, h, color) {
  g.fillStyle = color;
  g.fillRect(x, y, w, h);
};
ART.rrect = function (g, x, y, w, h, r, fill, stroke, lw) {
  g.beginPath();
  g.roundRect(x, y, w, h, r);
  if (fill) {
    g.fillStyle = fill;
    g.fill();
  }
  if (stroke) {
    g.strokeStyle = stroke;
    g.lineWidth = lw || 1;
    g.stroke();
  }
};
ART.circle = function (g, x, y, r, fill, stroke, lw) {
  g.beginPath();
  g.arc(x, y, r, 0, Math.PI * 2);
  if (fill) {
    g.fillStyle = fill;
    g.fill();
  }
  if (stroke) {
    g.strokeStyle = stroke;
    g.lineWidth = lw || 1;
    g.stroke();
  }
};
// hazard triangle: rounded yellow triangle, black border, symbol drawn by fn(cx, cy, size)
ART.hazard = function (g, cx, cy, side, symbol) {
  const h = (side * Math.sqrt(3)) / 2;
  const pts = [
    [cx, cy - h * 0.62],
    [cx + side / 2, cy + h * 0.38],
    [cx - side / 2, cy + h * 0.38],
  ];
  const tri = (k) => {
    g.beginPath();
    const c = [cx, cy + h * 0.05];
    pts.forEach((p, i) => {
      const q = [c[0] + (p[0] - c[0]) * k, c[1] + (p[1] - c[1]) * k];
      i ? g.lineTo(q[0], q[1]) : g.moveTo(q[0], q[1]);
    });
    g.closePath();
  };
  g.save();
  g.lineJoin = 'round';
  tri(1);
  g.fillStyle = '#111';
  g.fill();
  g.lineWidth = side * 0.06;
  g.strokeStyle = '#111';
  g.stroke();
  tri(0.78);
  g.fillStyle = '#f2c200';
  g.fill();
  g.restore();
  if (symbol === 'bolt') ART.bolt(g, cx, cy + h * 0.1, side * 0.42);
  else if (symbol === 'hot') ART.heatWaves(g, cx, cy + h * 0.1, side * 0.36);
  else if (symbol === '!') {
    g.fillStyle = '#111';
    g.fillRect(cx - side * 0.04, cy - h * 0.18, side * 0.08, h * 0.38);
    ART.circle(g, cx, cy + h * 0.3, side * 0.05, '#111');
  }
};
ART.bolt = function (g, cx, cy, s) {
  g.fillStyle = '#111';
  g.beginPath();
  const p = [
    [0.12, -0.55], [-0.22, 0.05], [0.02, 0.05], [-0.14, 0.55], [0.24, -0.08], [0.0, -0.08], [0.16, -0.55],
  ];
  p.forEach(([x, y], i) => (i ? g.lineTo(cx + x * s, cy + y * s) : g.moveTo(cx + x * s, cy + y * s)));
  g.closePath();
  g.fill();
};
ART.heatWaves = function (g, cx, cy, s) {
  g.strokeStyle = '#111';
  g.lineWidth = s * 0.09;
  g.lineCap = 'round';
  for (const dx of [-0.28, 0, 0.28]) {
    g.beginPath();
    for (let t = 0; t <= 1; t += 0.05) {
      const y = cy + (t - 0.5) * s * 1.1;
      const x = cx + dx * s + Math.sin(t * Math.PI * 2.2) * s * 0.08;
      t ? g.lineTo(x, y) : g.moveTo(x, y);
    }
    g.stroke();
  }
};
// the KAZE mark (after make_screens.ps1 KazeLogo): ring + an 'A' whose crossbar is a wind wave
ART.kazeMark = function (g, cx, cy, r, color) {
  g.save();
  g.fillStyle = color;
  g.strokeStyle = color;
  g.beginPath();
  g.arc(cx, cy, r, 0, Math.PI * 2);
  g.arc(cx, cy, r * 0.86, 0, Math.PI * 2, true);
  g.fill();
  const w = r * 0.11;
  g.beginPath();
  g.moveTo(cx - w, cy - r * 0.62);
  g.lineTo(cx + w, cy - r * 0.62);
  g.lineTo(cx + r * 0.52, cy + r * 0.55);
  g.lineTo(cx + r * 0.52 - 2 * w, cy + r * 0.55);
  g.lineTo(cx, cy - r * 0.35);
  g.closePath();
  g.fill();
  g.beginPath();
  g.moveTo(cx - w, cy - r * 0.62);
  g.lineTo(cx, cy - r * 0.35);
  g.lineTo(cx - r * 0.52 + 2 * w, cy + r * 0.55);
  g.lineTo(cx - r * 0.52, cy + r * 0.55);
  g.closePath();
  g.fill();
  g.lineWidth = w * 1.4;
  g.lineCap = 'round';
  g.beginPath();
  for (let k = 0; k <= 30; k++) {
    const x = cx - r * 0.55 + (k * r * 1.1) / 30;
    const y = cy + r * 0.12 + Math.sin((k / 30) * 2 * Math.PI) * r * 0.07;
    k ? g.lineTo(x, y) : g.moveTo(x, y);
  }
  g.stroke();
  g.restore();
};
// a barcode from a seeded pattern (bars in mm)
ART.barcode = function (g, x, y, w, h, seed, color = '#111') {
  const r = ART.rng(seed);
  let cx = x;
  g.fillStyle = color;
  while (cx < x + w) {
    const bw = [0.25, 0.5, 0.75][Math.floor(r() * 3)] * (w / 30);
    if (r() < 0.55) g.fillRect(cx, y, bw, h);
    cx += bw;
  }
};
ART.qr = function (g, x, y, size, seed, color = '#111') {
  const n = 21, c = size / n;
  const r = ART.rng(seed);
  g.fillStyle = color;
  const finder = (fx, fy) => {
    g.fillRect(x + fx * c, y + fy * c, 7 * c, 7 * c);
    g.clearRect(x + (fx + 1) * c, y + (fy + 1) * c, 5 * c, 5 * c);
    g.fillStyle = '#fff';
    g.fillRect(x + (fx + 1) * c, y + (fy + 1) * c, 5 * c, 5 * c);
    g.fillStyle = color;
    g.fillRect(x + (fx + 2) * c, y + (fy + 2) * c, 3 * c, 3 * c);
  };
  for (let i = 0; i < n; i++)
    for (let j = 0; j < n; j++) {
      const inF = (i < 8 && j < 8) || (i > 12 && j < 8) || (i < 8 && j > 12);
      if (!inF && r() < 0.5) g.fillRect(x + i * c, y + j * c, c * 1.02, c * 1.02);
    }
  finder(0, 0);
  finder(14, 0);
  finder(0, 14);
};

// ---- aging ------------------------------------------------------------------------------------
// Signed distance (mm) inside the paper rectangle (positive inside), with tear cuts applied.
function paperField(u, v, it, P) {
  const m = it.margin || 0;
  const x = u - m, y = v - m; // paper coords (mm)
  let d = Math.min(x, y, it.w - x, it.h - y);
  if (it.shape === 'round') d = Math.min(it.w, it.h) / 2 - Math.hypot(x - it.w / 2, y - it.h / 2);
  if (it.shape === 'rounded') {
    const rr = it.radius || 3;
    const qx = Math.max(Math.abs(x - it.w / 2) - (it.w / 2 - rr), 0), qy = Math.max(Math.abs(y - it.h / 2) - (it.h / 2 - rr), 0);
    const inner = Math.min(Math.max(Math.abs(x - it.w / 2) - (it.w / 2 - rr), Math.abs(y - it.h / 2) - (it.h / 2 - rr)), 0);
    d = Math.min(d, -(Math.hypot(qx, qy) + inner) + rr);
  }
  // torn-off parts: half-plane cuts (mm, paper coords) with a jagged, fibrous boundary
  for (const t of P.tears || []) {
    const ax = t.a[0] * it.w, ay = t.a[1] * it.h, bx = t.b[0] * it.w, by = t.b[1] * it.h;
    const lx = bx - ax, ly = by - ay, L = Math.hypot(lx, ly);
    const s = ((x - ax) * -ly + (y - ay) * lx) / L; // signed distance to the line
    const along = ((x - ax) * lx + (y - ay) * ly) / L;
    if (along < 0 || along > L) continue; // a tear runs edge to edge between its two end points
    const jag = (t.jag || 6) * (fbm(along / (t.scale || 9), 3.7 + (t.seed || 0), 4, 91) - 0.5) * 2 +
      (t.fine || 0.8) * (vnoise(along / 0.7, 1.3, 92) - 0.5) * 2;
    // keep the side the paper's centre is on
    const keep = ((it.w / 2 - ax) * -ly + (it.h / 2 - ay) * lx) >= 0 ? 1 : -1;
    d = Math.min(d, keep * s + jag);
  }
  for (const h of P.holes || []) {
    const hx = h[0] * it.w, hy = h[1] * it.h, hr = h[2];
    const jag = 0.4 * (vnoise(x / 0.6, y / 0.6, 77) - 0.5);
    d = Math.min(d, Math.hypot(x - hx, y - hy) - hr + jag);
  }
  return d;
}
ART.paperField = paperField;

// Process an item canvas (already drawn) into the four maps. Returns {C, N, S} ImageData-sized arrays.
ART.age = function (it, cv, s) {
  const W = cv.width, H = cv.height;
  const g = cv.getContext('2d');
  const src = g.getImageData(0, 0, W, H).data;
  const P = Object.assign(
    {
      kind: 'paper', paper: [0.94, 0.93, 0.89], yellow: 0.1, fade: 0.1, dirt: 0.15, edgeDirt: 0.25, stains: 0, stainScale: 40,
      stainBias: 'bottom', crease: [], wrinkle: 0.15, rough: 0.85, metal: 0, absorb: 1.0, scratches: 0, emissive: 0,
      bleach: 0, grain: 0.03, seed: 1,
    },
    it.age || {}
  );
  const seed = P.seed * 131 + 7;
  const out = { C: new Uint8ClampedArray(W * H * 4), N: new Uint8ClampedArray(W * H * 4), S: new Uint8ClampedArray(W * H * 4) };
  const Hgt = new Float32Array(W * H);
  const tape = P.tape || [];
  const crease = P.crease;
  const paper = P.paper;
  const m = it.margin || 0;
  const pw = it.w, ph = it.h;
  for (let j = 0; j < H; j++) {
    for (let i = 0; i < W; i++) {
      const k = j * W + i;
      const u = (i + 0.5) / s, v = (j + 0.5) / s; // mm in the card
      const x = u - m, y = v - m; // mm in the paper
      const sd = paperField(u, v, it, P);
      // opacity: the paper (or die-cut design) inside its torn/punched outline, plus tape reaching past it
      const da = src[k * 4 + 3] / 255;
      const pa = it.design_alpha ? da * clamp(0.5 + sd * s * 0.5) : clamp(0.5 + sd * s * 0.5);
      let ta = 0;
      // design colour over the paper / face colour
      let r = mix(paper[0], src[k * 4] / 255, da), gg = mix(paper[1], src[k * 4 + 1] / 255, da), b = mix(paper[2], src[k * 4 + 2] / 255, da);
      const nx = x / pw, ny = y / ph; // 0..1 over the paper
      let h = 0, rough = P.rough, metal = P.metal, absorb = P.absorb, emis = P.emissive;
      // sun fade: yellow and magenta inks fade first (the print drifts cyan), black lasts
      const fadeMap = P.fade * (0.75 + 0.5 * fbm(x / 60, y / 60, 3, seed + 3)) * (P.fadeTop ? mix(1.25, 0.75, ny) : 1);
      if (fadeMap > 0) {
        const dr = paper[0] - r, dg = paper[1] - gg, db = paper[2] - b;
        const dark = Math.min(dr, dg, db); // the neutral (black) part of the ink
        r = paper[0] - (dark + (dr - dark) * (1 - 0.45 * fadeMap) - dark * 0.25 * fadeMap);
        gg = paper[1] - (dark + (dg - dark) * (1 - 0.8 * fadeMap) - dark * 0.25 * fadeMap);
        b = paper[2] - (dark + (db - dark) * (1 - 0.95 * fadeMap) - dark * 0.25 * fadeMap);
      }
      // paper yellowing (stronger at the edges) and bleaching
      const edge = Math.max(0, sd);
      const yel = P.yellow * (0.8 + 0.4 * fbm(x / 30, y / 30, 3, seed + 5)) * (1 + 0.6 * Math.exp(-edge / 8));
      r = mix(r, r * 0.97, yel);
      gg = mix(gg, gg * 0.9, yel);
      b = mix(b, b * 0.68, yel);
      if (P.bleach) {
        const lum = 0.3 * r + 0.59 * gg + 0.11 * b;
        r = mix(r, lum * 1.08 + 0.05, P.bleach);
        gg = mix(gg, lum * 1.06 + 0.05, P.bleach);
        b = mix(b, lum * 1.02 + 0.05, P.bleach);
      }
      // grain / fibres
      const gr = (vnoise(u * 3.1, v * 3.1, seed + 11) - 0.5) * P.grain;
      r += gr; gg += gr; b += gr;
      // water stains: blotches with darker tide lines
      if (P.stains > 0) {
        const bias = P.stainBias === 'bottom' ? smooth(0.35, 1.0, ny) : P.stainBias === 'top' ? smooth(0.65, 0.0, ny) :
          P.stainBias === 'edges' ? Math.exp(-edge / 25) : 0.6;
        const f = fbm(x / P.stainScale, y / P.stainScale, 5, seed + 21) + bias * 0.45 - 0.62 - (1 - P.stains) * 0.4;
        const inS = smooth(0.0, 0.02, f);
        const tide = Math.exp(-Math.pow(f / 0.012, 2)) * smooth(-0.05, 0.0, f) * 1.0;
        const f2 = fbm(x / (P.stainScale * 0.6), y / (P.stainScale * 0.6), 4, seed + 23) + bias * 0.4 - 0.66 - (1 - P.stains) * 0.4;
        const tide2 = Math.exp(-Math.pow(f2 / 0.01, 2)) * 0.6;
        const st = inS * 0.5 + tide * 0.9 + tide2 * 0.5;
        r = mix(r, r * 0.86, st * 0.7);
        gg = mix(gg, gg * 0.80, st * 0.7);
        b = mix(b, b * 0.62, st * 0.7);
        // inks run a little inside the stain: lighter, washed out
        r = mix(r, mix(r, paper[0] * 0.95, 0.25), inS * 0.5);
        gg = mix(gg, mix(gg, paper[1] * 0.9, 0.25), inS * 0.5);
        b = mix(b, mix(b, paper[2] * 0.8, 0.25), inS * 0.5);
        h += inS * 0.08 + tide * 0.05;
        rough = mix(rough, Math.min(1, rough + 0.06), inS);
      }
      // dirt: broad grime + darker along the edges + drips down from the top edge
      const dn = fbm(x / 12, y / 12, 4, seed + 31);
      const edgeD = P.edgeDirt * Math.exp(-edge / 3.5) * (0.6 + 0.8 * dn);
      const broad = P.dirt * smooth(0.35, 0.8, fbm(x / 45, y / 45, 4, seed + 33)) * (0.7 + 0.6 * ny);
      const streak = (P.streaks || 0) * smooth(0.55, 0.85, fbm(x / 4, y / 60, 3, seed + 35)) * mix(1, 0.3, ny);
      const dirt = clamp(edgeD + broad + streak);
      r = mix(r, 0.23, dirt * 0.55);
      gg = mix(gg, 0.2, dirt * 0.55);
      b = mix(b, 0.15, dirt * 0.55);
      // creases (folds): a ridge with a dirty line, lit on one side via the normal map
      for (const c of crease) {
        const cd = c[0] === 'h' ? Math.abs(y - c[1] * ph) : Math.abs(x - c[1] * pw);
        const w = c[2] || 1.2;
        h += 0.35 * Math.exp(-Math.pow(cd / w, 2));
        const line = Math.exp(-Math.pow(cd / 0.35, 2)) * (c[3] || 0.35);
        r *= 1 - line * 0.35; gg *= 1 - line * 0.37; b *= 1 - line * 0.4;
      }
      // wrinkles
      if (P.wrinkle) h += P.wrinkle * (fbm(x / 18, y / 18, 4, seed + 41) - 0.5) * 1.6 + P.wrinkle * 0.3 * (vnoise(x / 2.5, y / 9, seed + 43) - 0.5);
      // torn edges: the print layer peels back to white fibres along the tear
      if ((P.tears || P.holes) && sd > 0 && sd < 1.6) {
        const fib = smooth(1.6, 0.2, sd) * (0.6 + 0.4 * vnoise(u * 2, v * 2, seed + 51));
        r = mix(r, paper[0] * 1.02, fib * 0.8);
        gg = mix(gg, paper[1] * 1.02, fib * 0.8);
        b = mix(b, paper[2] * 0.98, fib * 0.8);
      }
      // scratches (vinyl, metal, plastic): fine bright lines
      if (P.scratches > 0) {
        const sc = Math.pow(clamp(1 - Math.abs(vnoise(u / 0.25 + v * 0.9, v / 40, seed + 61) - 0.5) * 30), 3) * smooth(0.5, 0.8, fbm(x / 20, y / 20, 3, seed + 63));
        const sc2 = Math.pow(clamp(1 - Math.abs(vnoise(v / 0.25 - u * 0.4, u / 30, seed + 65) - 0.5) * 30), 3) * smooth(0.55, 0.85, fbm(x / 15, y / 15, 3, seed + 67));
        const scr = clamp((sc + sc2) * P.scratches);
        r = mix(r, Math.min(1, r * 1.3 + 0.12), scr * 0.6);
        gg = mix(gg, Math.min(1, gg * 1.3 + 0.12), scr * 0.6);
        b = mix(b, Math.min(1, b * 1.3 + 0.12), scr * 0.6);
        rough = mix(rough, P.kind === 'metal' ? 0.25 : 0.6, scr);
        h -= scr * 0.05;
      }
      // rust spots (metal plates, near rivets/edges)
      if (P.rust) {
        const rs = smooth(0.62, 0.75, fbm(x / 6, y / 6, 4, seed + 71) + Math.exp(-edge / 2) * 0.25) * P.rust;
        r = mix(r, 0.36, rs);
        gg = mix(gg, 0.17, rs);
        b = mix(b, 0.08, rs);
        rough = mix(rough, 0.85, rs);
        metal = mix(metal, 0, rs);
      }
      // tape: masking/clear/cloth strips over corners and edges (they can reach past the paper)
      for (const t of tape) {
        const tx = (t.x * pw) + m, ty = (t.y * ph) + m; // centre in card mm
        const ca = Math.cos(t.rot || 0), sa = Math.sin(t.rot || 0);
        const lx = (u - tx) * ca + (v - ty) * sa, ly = -(u - tx) * sa + (v - ty) * ca;
        const tw = t.w / 2, th = t.h / 2;
        const jagE = 0.5 * (vnoise(ly * 1.3, 4, seed + 81) - 0.5);
        if (Math.abs(lx) < tw + jagE && Math.abs(ly) < th) {
          const tc = t.color || [0.84, 0.77, 0.58];
          const op = t.clear ? 0.35 : 0.92;
          if (!t.clear || sd > 0) {
            r = mix(r, tc[0] * (t.clear ? r * 1.05 : 1), op);
            gg = mix(gg, tc[1] * (t.clear ? gg * 1.05 : 1), op);
            b = mix(b, tc[2] * (t.clear ? b * 1.05 : 1), op);
            const td = (t.dirt || 0.3) * smooth(0.4, 0.8, fbm(lx / 3, ly / 3, 3, seed + 83)) + 0.4 * Math.exp(-(tw - Math.abs(lx)) / 0.8);
            r = mix(r, 0.3, td * 0.4); gg = mix(gg, 0.26, td * 0.4); b = mix(b, 0.18, td * 0.4);
            rough = t.clear ? 0.3 : 0.7;
            absorb = Math.min(absorb, 0.5);
            h += 0.08;
            ta = 1;
          }
        }
      }
      // lit faces: tube banding behind the diffuser, a dimmer corner, dead bugs and dust at the bottom
      if (P.kind === 'lit') {
        const band = P.tubes ? P.tubes.reduce((acc, tb) => acc + Math.exp(-Math.pow((x / pw - tb) / 0.18, 2)), 0) : 1;
        emis = clamp(0.72 + 0.28 * band) * (1 - 0.18 * smooth(0.6, 1.0, Math.hypot(nx - (P.dimCorner || [1, 1])[0], ny - (P.dimCorner || [1, 1])[1]) < 0.5 ? 1 : 0));
        const bug = P.bugs ? smooth(0.9, 0.93, vnoise(x / 2.2, y / 2.2, seed + 91)) * smooth(0.6, 1.0, ny) : 0;
        r = mix(r, 0.08, bug); gg = mix(gg, 0.06, bug); b = mix(b, 0.04, bug);
        emis *= 1 - bug * 0.9;
      }
      if (P.kind === 'metal') {
        // brushed metal grain
        const bg = (vnoise(u * 0.3, v * 8, seed + 95) - 0.5) * 0.08;
        r += bg; gg += bg; b += bg;
      }
      // design-provided extras: height (blue channel of a separate "relief" pass is not used; designs
      // can supply it through it.relief(u, v))
      if (it.relief) h += it.relief(x, y);
      if (it.roughAt) rough = it.roughAt(x, y, rough, src[k * 4] / 255, src[k * 4 + 1] / 255, src[k * 4 + 2] / 255, da);
      if (it.metalAt) metal = it.metalAt(x, y, metal, da);
      if (it.emisAt) emis = it.emisAt(x, y, emis, da);
      const a = Math.max(pa, ta);
      Hgt[k] = h;
      out.C[k * 4] = clamp(r) * 255;
      out.C[k * 4 + 1] = clamp(gg) * 255;
      out.C[k * 4 + 2] = clamp(b) * 255;
      out.C[k * 4 + 3] = clamp(a) * 255;
      out.S[k * 4] = clamp(rough) * 255;
      out.S[k * 4 + 1] = clamp(metal) * 255;
      out.S[k * 4 + 2] = clamp(emis) * 255;
      out.S[k * 4 + 3] = clamp(absorb) * 255;
    }
  }
  // normals from the height field (mm); DirectX convention (+V down the image)
  const kN = (P.normalStrength || 1.0) * s;
  for (let j = 0; j < H; j++) {
    for (let i = 0; i < W; i++) {
      const k = j * W + i;
      const hl = Hgt[j * W + Math.max(0, i - 1)], hr = Hgt[j * W + Math.min(W - 1, i + 1)];
      const hu = Hgt[Math.max(0, j - 1) * W + i], hd = Hgt[Math.min(H - 1, j + 1) * W + i];
      let nx = -(hr - hl) * 0.5 * kN, ny = -(hd - hu) * 0.5 * kN, nz = 1;
      const L = Math.hypot(nx, ny, nz);
      out.N[k * 4] = (nx / L * 0.5 + 0.5) * 255;
      out.N[k * 4 + 1] = (ny / L * 0.5 + 0.5) * 255;
      out.N[k * 4 + 2] = (nz / L * 0.5 + 0.5) * 255;
      out.N[k * 4 + 3] = 255;
    }
  }
  return out;
};

// ---- atlas packing ------------------------------------------------------------------------------
// Skyline (bottom-left) packer: items sorted by height, each placed where it sits lowest. Returns
// {rects: {name: [x, y, w, h]} in px, used}. The gutter keeps neighbours apart in the mips.
ART.pack = function (items, size, gutter) {
  const sorted = items.slice().sort((a, b) => b.ph - a.ph || b.pw - a.pw);
  let sky = [{ x: 0, y: 0, w: size }];
  const rects = {};
  let used = 0;
  for (const it of sorted) {
    const w = it.pw + gutter, h = it.ph + gutter;
    let best = null;
    for (let i = 0; i < sky.length; i++) {
      const x = sky[i].x;
      if (x + w > size) break;
      let y = 0, rem = w, j = i;
      while (rem > 0 && j < sky.length) {
        y = Math.max(y, sky[j].y);
        rem -= sky[j].w;
        j++;
      }
      if (rem > 0) continue;
      if (y + h <= size && (!best || y < best.y || (y === best.y && x < best.x))) best = { x, y };
    }
    if (!best) throw new Error('atlas full at ' + it.name);
    rects[it.name] = [best.x + gutter / 2, best.y + gutter / 2, it.pw, it.ph];
    used = Math.max(used, best.y + h);
    // raise the skyline over [x, x + w)
    const nx = best.x, nw = w, ny = best.y + h;
    const out = [];
    for (const sgm of sky) {
      const a0 = sgm.x, a1 = sgm.x + sgm.w;
      if (a1 <= nx || a0 >= nx + nw) out.push(sgm);
      else {
        if (a0 < nx) out.push({ x: a0, y: sgm.y, w: nx - a0 });
        if (a1 > nx + nw) out.push({ x: nx + nw, y: sgm.y, w: a1 - nx - nw });
      }
    }
    out.push({ x: nx, y: ny, w: nw });
    out.sort((p, q) => p.x - q.x);
    sky = [];
    for (const sgm of out) {
      const last = sky[sky.length - 1];
      if (last && last.y === sgm.y && last.x + last.w === sgm.x) last.w += sgm.w;
      else sky.push(Object.assign({}, sgm));
    }
  }
  return { rects, used };
};
