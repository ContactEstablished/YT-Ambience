// Decals atlas: marks IN the paint, projected by Unreal deferred decals onto the weathered walls
// (2 px/mm). Evidence of removed signage (adhesive ghosts, paint protected under an old sign, screw
// holes with rust, scraped sticker residue, torn tape), marker writing and an overpainted stencil.
// Each item supplies pixel(x, y, mask) -> [r, g, b, opacity, height mm, roughness]; `mask` samples the
// item's drawn canvas (its alpha). Colours are sRGB albedo; opacity is how much of the wall it replaces.
(function () {
  const A = window.ART;
  const F = A.F;
  const { fbm, vnoise, clamp, smooth, mix } = A;
  const items = (A.items = A.items || []);
  const add = (it) => items.push(Object.assign({ atlas: 'Decals', margin: 0 }, it));
  // the kiosk's yellow paint as it was before decades of sun (Kiosk_YellowPaint, slightly deeper)
  const DEEP = [0.79, 0.62, 0.22];
  const GRIME = [0.2, 0.16, 0.1];
  const RUST = [0.42, 0.2, 0.08];
  const ADH = [0.42, 0.33, 0.16];

  const rectDist = (x, y, x0, y0, x1, y1) => Math.min(x - x0, y - y0, x1 - x, y1 - y);
  // paint protected under a long-gone sign: deeper, unfaded; dirt lines where grime piled against its edges
  function ghost(x, y, w, h, m, seed, o) {
    const d = rectDist(x, y, m, m, w - m, h - m) + 2.0 * (fbm(x / 9, y / 9, 3, seed) - 0.5);
    const inside = smooth(-1.5, 2.5, d);
    const mott = fbm(x / 25, y / 25, 4, seed + 1);
    let op = inside * (o.inner || 0.32) * (0.55 + 0.6 * mott);
    let col = DEEP.slice();
    // grime line along the outside of the top and side edges (water and dirt held against the sign)
    const top = Math.abs(y - m) < 6 && x > m - 4 && x < w - m + 4 ? 1 : 0;
    const edge = Math.exp(-Math.pow(Math.max(0, -d) / 2.6, 2)) * smooth(-9, -0.5, d) * (1 - inside);
    const gl = edge * (0.45 + 0.4 * fbm(x / 6, y / 6, 3, seed + 2)) * (top ? 1.3 : 0.9) * (o.grime || 1);
    if (gl > 0.02) {
      col = GRIME.map((c, i) => mix(col[i], c, clamp(gl * 2)));
      op = Math.max(op, gl * 0.85);
    }
    return { col, op, d, inside };
  }
  function screwHole(x, y, cx, cy, r, seed) {
    const dd = Math.hypot(x - cx, y - cy);
    const hole = smooth(r * 0.55, r * 0.35, dd);
    const ring = smooth(r * 2.6, r * 0.8, dd) * (0.6 + 0.5 * vnoise(x / 1.2, y / 1.2, seed));
    // rust run below the hole
    const run = smooth(5, 0, Math.abs(x - cx + 1.5 * (fbm(y / 8, cx, 2, seed + 3) - 0.5) * 4)) * smooth(0, 4, y - cy) *
      Math.exp(-(y - cy) / (28 + 30 * vnoise(cx, cy, seed + 4))) * (0.5 + 0.5 * fbm(x / 3, y / 10, 3, seed + 5));
    return { hole, rust: clamp(ring * 0.9 + run * 0.8) };
  }

  add({ name: 'ghost_poster', w: 330, h: 450, margin: 0,
    pixel(x, y) {
      const G = ghost(x, y, 330, 450, 15, 301, { inner: 0.3 });
      let [r, g, b] = G.col;
      let op = G.op, h = 0, rough = 0.55;
      // dark adhesive squares where tape held the corners (dirt sticks to the old glue)
      for (const [cx, cy, a] of [[18, 18, -0.7], [312, 17, 0.75], [17, 431, 0.7], [313, 432, -0.6]]) {
        const ca = Math.cos(a), sa = Math.sin(a);
        const lx = (x - cx) * ca + (y - cy) * sa, ly = -(x - cx) * sa + (y - cy) * ca;
        const t = smooth(1.2, -0.5, Math.max(Math.abs(lx) - 15, Math.abs(ly) - 6) + 1.2 * (fbm(x / 2, y / 2, 3, 305) - 0.5));
        if (t > 0) {
          const patchy = smooth(0.35, 0.6, fbm(x / 3.5, y / 3.5, 3, 306));
          const k = t * (0.4 + 0.6 * patchy);
          r = mix(r, ADH[0], k); g = mix(g, ADH[1], k); b = mix(b, ADH[2], k);
          op = Math.max(op, k * 0.85);
          rough = mix(rough, 0.3, k);
          h += k * 0.05;
          // white paper fibres left in the glue
          const fib = smooth(0.72, 0.8, vnoise(x / 1.1, y / 1.1, 307)) * k;
          r = mix(r, 0.86, fib); g = mix(g, 0.84, fib); b = mix(b, 0.78, fib);
        }
      }
      return [r, g, b, op, h, rough];
    } });

  // paint rectangle where a bolted metal sign hung for years, its four screw holes and rust runs
  add({ name: 'ghost_bolted', w: 500, h: 330,
    pixel(x, y) {
      const G = ghost(x, y, 500, 330, 12, 311, { inner: 0.42, grime: 1.2 });
      let [r, g, b] = G.col;
      let op = G.op, h = 0, rough = 0.5;
      for (const [cx, cy] of [[26, 24], [474, 22], [27, 306], [473, 305]]) {
        const s = screwHole(x, y, cx, cy, 3.2, 312);
        if (s.rust > 0.01) {
          r = mix(r, RUST[0], s.rust); g = mix(g, RUST[1], s.rust); b = mix(b, RUST[2], s.rust);
          op = Math.max(op, s.rust * 0.9);
          rough = mix(rough, 0.85, s.rust);
        }
        if (s.hole > 0.01) {
          r = mix(r, 0.03, s.hole); g = mix(g, 0.025, s.hole); b = mix(b, 0.02, s.hole);
          op = Math.max(op, s.hole);
          h -= s.hole * 1.2;
          rough = mix(rough, 0.9, s.hole);
        }
      }
      return [r, g, b, op, h, rough];
    } });

  // two screw holes (a removed bracket) with a little paint ghost round them
  add({ name: 'holes_pair', w: 80, h: 130,
    pixel(x, y) {
      let r = DEEP[0], g = DEEP[1], b = DEEP[2], op = 0, h = 0, rough = 0.5;
      const G = ghost(x, y, 80, 46, 8, 321, { inner: 0.35 });
      if (y < 46) { [r, g, b] = G.col; op = G.op; }
      for (const [cx, cy] of [[22, 22], [58, 23]]) {
        const s = screwHole(x, y, cx, cy, 3.0, 322 + cx);
        r = mix(r, RUST[0], s.rust); g = mix(g, RUST[1], s.rust); b = mix(b, RUST[2], s.rust);
        op = Math.max(op, s.rust * 0.9);
        r = mix(r, 0.03, s.hole); g = mix(g, 0.025, s.hole); b = mix(b, 0.02, s.hole);
        op = Math.max(op, s.hole);
        h -= s.hole * 1.2;
      }
      return [r, g, b, op, h, rough];
    } });
  add({ name: 'holes_row', w: 230, h: 60,
    pixel(x, y) {
      let r = 0, g = 0, b = 0, op = 0, h = 0, rough = 0.6;
      for (const cx of [20, 82, 148, 210]) {
        const s = screwHole(x, y, cx, 14, 2.6, 330 + cx);
        r = mix(r, RUST[0], s.rust); g = mix(g, RUST[1], s.rust); b = mix(b, RUST[2], s.rust);
        op = Math.max(op, s.rust * 0.85);
        r = mix(r, 0.03, s.hole); g = mix(g, 0.025, s.hole); b = mix(b, 0.02, s.hole);
        op = Math.max(op, s.hole);
        h -= s.hole;
      }
      return [r, g, b, op, h, rough];
    } });

  // scraped-off sticker: white paper remnants in a film of yellowed glue, scraper scratches
  const residue = (name, w, h, shape, seed) => add({ name, w, h,
    pixel(x, y) {
      const cx = w / 2, cy = h / 2;
      const d = shape === 'round' ? Math.min(w, h) / 2 - 3 - Math.hypot(x - cx, y - cy) : rectDist(x, y, 3, 3, w - 3, h - 3);
      const dj = d + 2.5 * (fbm(x / 5, y / 5, 3, seed) - 0.5);
      const film = smooth(-0.5, 1.5, dj);
      const paper = film * smooth(0.5, 0.62, fbm(x / 6, y / 6, 4, seed + 1) + 0.15 * smooth(6, 0, dj));
      const scr = Math.pow(clamp(1 - Math.abs(vnoise(x / 0.3 + y * 0.35, y / 20, seed + 2) - 0.5) * 22), 3) * film;
      let r = mix(ADH[0], 0.9, paper), g = mix(ADH[1], 0.88, paper), b = mix(ADH[2], 0.82, paper);
      r = mix(r, 0.55, scr * 0.5); g = mix(g, 0.5, scr * 0.5); b = mix(b, 0.42, scr * 0.5);
      const op = clamp(film * 0.45 + paper * 0.5 + scr * 0.3);
      return [r, g, b, op, paper * 0.08 - scr * 0.04, mix(0.35, 0.85, paper)];
    } });
  residue('residue_a', 72, 50, 'rect', 341);
  residue('residue_b', 56, 56, 'round', 342);
  residue('residue_c', 96, 40, 'rect', 343);

  // marker writing on metal (the inspection dates on the utility box door)
  add({ name: 'marker_dates', w: 150, h: 104,
    draw(g) {
      A.hand(g, '点検', 8, 22, 15, { seed: 401, thick: 0.08 });
      A.hand(g, '88. 4.12 ✓森', 8, 46, 12, { seed: 402, thick: 0.07, font: F.jp });
      A.hand(g, '88.10. 3 ✓森', 8, 68, 12, { seed: 403, thick: 0.07, font: F.jp });
      A.hand(g, '89. 4. 9 ✓', 8, 90, 12, { seed: 404, thick: 0.07, font: F.jp });
      g.strokeStyle = '#000'; g.lineWidth = 1.6; g.beginPath(); g.moveTo(8, 27); g.lineTo(58, 26); g.stroke();
    },
    pixel(x, y, mask) {
      const k = mask(x, y);
      const ink = clamp(k * (0.75 + 0.35 * fbm(x / 3, y / 3, 3, 405)));
      return [0.05, 0.05, 0.06, ink * 0.92, ink * 0.02, 0.35];
    } });
  // white paint-marker circuit numbers on the dark fuse box
  add({ name: 'marker_breaker', w: 110, h: 80,
    draw(g) {
      A.hand(g, '1 照明', 6, 18, 12, { seed: 411, thick: 0.08 });
      A.hand(g, '2 冷蔵', 6, 38, 12, { seed: 412, thick: 0.08 });
      A.hand(g, '4 看板', 6, 58, 12, { seed: 413, thick: 0.08 });
      A.hand(g, '!! 5 OFF', 6, 76, 10, { seed: 414, thick: 0.08, font: F.latin });
    },
    pixel(x, y, mask) {
      const k = mask(x, y);
      const ink = clamp(k * (0.7 + 0.4 * fbm(x / 2.5, y / 2.5, 3, 415)));
      return [0.86, 0.86, 0.82, ink * 0.88, ink * 0.03, 0.55];
    } });

  // an old stall number painted out with a brushed patch of newer yellow; the stencil still ghosts through
  add({ name: 'overpaint', w: 400, h: 230,
    draw(g) {
      A.fitText(g, 'K-06', 200, 110, 300, 120, { font: F.impact, weight: 400, color: '#000' });
      A.fitText(g, '東区 三番街', 200, 196, 200, 34, { font: F.jp, weight: 900, color: '#000' });
      // stencil bridges
      g.globalCompositeOperation = 'destination-out';
      for (const x of [86, 132, 200, 262, 312]) g.fillRect(x, 50, 5, 120);
      g.globalCompositeOperation = 'source-over';
    },
    pixel(x, y, mask) {
      const edge = rectDist(x, y, 8, 6, 392, 222);
      // brush strokes: horizontal streaks with ragged ends
      const strokeN = fbm(x / 70, y / 7, 3, 421);
      const d = edge + 8 * (fbm(x / 12, y / 12, 3, 422) - 0.5) + 10 * (strokeN - 0.5);
      let cover = smooth(-2, 4, d);
      // drips from the bottom edge
      const dripX = vnoise(x / 9, 3.3, 423);
      const drip = smooth(0.82, 0.86, dripX) * smooth(-30 * dripX, 0, 222 - y) * (y > 210 ? 1 : 0);
      cover = Math.max(cover, drip);
      const st = mask(x, y);
      // newer, slightly greener yellow; the old black stencil reads through the thin coat as a dark ghost
      let r = 0.83, g = 0.68, b = 0.2;
      const thin = 0.55 + 0.45 * smooth(0.3, 0.7, fbm(x / 30, y / 4, 3, 424));
      r = mix(r, 0.36, st * (1 - thin) * 0.9); g = mix(g, 0.29, st * (1 - thin) * 0.9); b = mix(b, 0.1, st * (1 - thin) * 0.9);
      const ridge = (vnoise(x / 30, y / 0.9, 425) - 0.5) * 0.06;
      return [r, g, b, cover * 0.96, ridge * cover + drip * 0.05, 0.3];
    } });
  // the stall number re-stencilled in light spray paint on the dark service hood (overspray specks, worn)
  add({ name: 'stencil_k07', w: 250, h: 118,
    draw(g) {
      A.fitText(g, 'K-07', 125, 56, 210, 84, { font: F.impact, weight: 400, color: '#000' });
      A.fitText(g, '東区 三番街', 125, 104, 130, 18, { font: F.jp, weight: 900, color: '#000' });
      g.globalCompositeOperation = 'destination-out';
      for (const x of [56, 92, 140, 182]) g.fillRect(x, 14, 3.5, 80);
      g.globalCompositeOperation = 'source-over';
    },
    pixel(x, y, mask) {
      const k = mask(x, y);
      const blur = Math.max(mask(x + 0.8, y), mask(x - 0.8, y), mask(x, y + 0.8), mask(x, y - 0.8));
      const spray = smooth(0.94, 0.97, vnoise(x / 0.5, y / 0.5, 431)) * smooth(30, 0, Math.abs(y - 59)) * 0.5;
      const wear = smooth(0.25, 0.6, fbm(x / 14, y / 14, 4, 432));
      const ink = clamp((k * 0.85 + (blur - k) * 0.35) * mix(0.35, 1, wear) + spray * 0.4);
      return [0.8, 0.78, 0.71, ink * 0.92, 0, 0.6];
    } });

  // a sign once bolted to dark painted steel (the service hood): blacker, cleaner paint where it hung,
  // dust settled along its top edge (dust reads lighter than black paint), four holes with rust runs
  add({ name: 'ghost_dark', w: 520, h: 170,
    pixel(x, y) {
      const d = rectDist(x, y, 10, 10, 510, 160) + 1.8 * (fbm(x / 9, y / 9, 3, 451) - 0.5);
      const inside = smooth(-1.5, 2.5, d);
      let r = 0.03, g = 0.03, b = 0.033;
      let op = inside * 0.5 * (0.6 + 0.5 * fbm(x / 25, y / 25, 4, 452));
      const dust = Math.exp(-Math.pow(Math.max(0, -d) / 2.2, 2)) * smooth(-8, -0.5, d) * (1 - inside) * (y < 14 ? 1.4 : 0.7)
        * (0.5 + 0.5 * fbm(x / 5, y / 5, 3, 453));
      if (dust > 0.02) { r = mix(r, 0.36, clamp(dust * 1.6)); g = mix(g, 0.33, clamp(dust * 1.6)); b = mix(b, 0.28, clamp(dust * 1.6)); op = Math.max(op, dust * 0.7); }
      let h = 0, rough = mix(0.45, 0.85, clamp(dust));
      for (const [cx, cy] of [[24, 22], [496, 21], [25, 149], [495, 148]]) {
        const sh = screwHole(x, y, cx, cy, 3.0, 454);
        r = mix(r, RUST[0], sh.rust); g = mix(g, RUST[1], sh.rust); b = mix(b, RUST[2], sh.rust);
        op = Math.max(op, sh.rust * 0.85);
        r = mix(r, 0.01, sh.hole); g = mix(g, 0.01, sh.hole); b = mix(b, 0.01, sh.hole);
        op = Math.max(op, sh.hole);
        h -= sh.hole * 1.2;
      }
      return [r, g, b, op, h, rough];
    } });

  // where an electrical box was once mounted: cleaner, deeper paint, a dirt outline, holes and a cable hole
  add({ name: 'clean_patch', w: 300, h: 230,
    pixel(x, y) {
      const G = ghost(x, y, 300, 230, 14, 441, { inner: 0.45, grime: 1.4 });
      let [r, g, b] = G.col;
      let op = G.op, h = 0, rough = 0.5;
      for (const [cx, cy] of [[34, 30], [266, 31], [35, 200], [265, 199]]) {
        const s = screwHole(x, y, cx, cy, 2.8, 442);
        r = mix(r, RUST[0], s.rust); g = mix(g, RUST[1], s.rust); b = mix(b, RUST[2], s.rust);
        op = Math.max(op, s.rust * 0.9);
        r = mix(r, 0.03, s.hole); g = mix(g, 0.025, s.hole); b = mix(b, 0.02, s.hole);
        op = Math.max(op, s.hole);
        h -= s.hole * 1.2;
      }
      // the old cable entry, plugged with a dark grommet
      const dd = Math.hypot(x - 150, y - 196);
      const plug = smooth(11, 9.5, dd), rim = smooth(15, 11, dd) * (1 - plug);
      r = mix(r, 0.05, plug); g = mix(g, 0.05, plug); b = mix(b, 0.05, plug);
      r = mix(r, RUST[0], rim * 0.8); g = mix(g, RUST[1], rim * 0.8); b = mix(b, RUST[2], rim * 0.8);
      op = Math.max(op, plug, rim * 0.8);
      h += plug * 0.6 - rim * 0.2;
      return [r, g, b, op, h, rough];
    } });
})();
