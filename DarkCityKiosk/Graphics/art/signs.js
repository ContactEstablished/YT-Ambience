// Signs atlas: lit sign faces (emissive in Unreal) and the painted-steel skin of the retrofitted sign
// housings (2 px/mm). Lit faces stay cleaner and brighter than paper: only dust and dead insects
// collect along the bottom inside the diffuser, and the tubes behind show as soft bands.
(function () {
  const A = window.ART;
  const F = A.F;
  const items = (A.items = A.items || []);
  const add = (it) => items.push(Object.assign({ atlas: 'Signs', margin: 0 }, it));
  const lit = (seed, extra = {}) => Object.assign({ seed, kind: 'lit', paper: [0.99, 0.86, 0.46], rough: 0.25, absorb: 0.15, emissive: 1,
    yellow: 0, fade: 0, dirt: 0.04, edgeDirt: 0.35, grain: 0.008, wrinkle: 0, bugs: true, normalStrength: 0.3 }, extra);

  // 24-hour sign: narrow retrofitted lightbox on the front-right pole (after the reference's "24 時間 営業")
  add({ name: 'sign24_face', w: 168, h: 448, age: lit(201, { tubes: [0.5] }),
    draw(g) {
      const W = 168, H = 448;
      g.strokeStyle = '#141414';
      g.lineWidth = 4;
      g.strokeRect(9, 9, W - 18, H - 18);
      A.fitText(g, '24', W / 2, 96, 128, 118, { font: F.latin, weight: 700, color: '#121212' });
      A.fitText(g, '時間', W / 2, 228, 134, 66, { font: F.jp, weight: 900, color: '#121212', ls: 0.05 });
      A.fitText(g, '営業', W / 2, 330, 134, 66, { font: F.jp, weight: 900, color: '#121212', ls: 0.05 });
      A.rect(g, 26, 384, W - 52, 2, '#121212');
      A.fitText(g, 'OPEN 24 HOURS', W / 2, 408, 120, 13, { font: F.cond, weight: 700, color: '#121212', ls: 0.12 });
    } });
  // Corner sign face: cream acrylic, red border, vertical コーヒー and a steaming cup
  add({ name: 'corner_face', w: 220, h: 890, age: lit(202, { paper: [1.0, 0.82, 0.42], tubes: [0.3, 0.7], dirt: 0.06 }),
    draw(g) {
      const W = 220, H = 890;
      A.rect(g, 0, 0, W, H, '#ffd472');
      g.strokeStyle = '#c8141c';
      g.lineWidth = 14;
      g.strokeRect(10, 10, W - 20, H - 20);
      A.rect(g, 24, 24, W - 48, 64, '#c8141c');
      A.fitText(g, '珈琲', W / 2, 56, 130, 46, { font: F.jpMincho, weight: 700, color: '#ffd472' });
      A.vtext(g, 'コーヒー', W / 2, 112, 138, { font: F.jp, weight: 900, color: '#c8141c', step: 1.0 });
      // cup + steam
      const cy = 740;
      g.fillStyle = '#c8141c';
      g.beginPath();
      g.moveTo(54, cy - 30);
      g.lineTo(166, cy - 30);
      g.lineTo(156, cy + 40);
      g.quadraticCurveTo(110, cy + 62, 64, cy + 40);
      g.closePath();
      g.fill();
      g.lineWidth = 9;
      g.strokeStyle = '#c8141c';
      g.beginPath();
      g.arc(170, cy, 18, -1.2, 1.3);
      g.stroke();
      A.rect(g, 40, cy + 58, 140, 8, '#c8141c');
      g.lineWidth = 6;
      g.lineCap = 'round';
      for (const dx of [-28, 0, 28]) {
        g.beginPath();
        for (let t = 0; t <= 1; t += 0.05) {
          const y = cy - 46 - t * 70, x = W / 2 + dx + Math.sin(t * 6.5) * 7;
          t ? g.lineTo(x, y) : g.moveTo(x, y);
        }
        g.stroke();
      }
      A.fitText(g, 'COFFEE', W / 2, 852, 150, 30, { font: F.latin, weight: 700, color: '#c8141c', ls: 0.15 });
    } });
  // Under-counter sign: smoked acrylic with warm LED-dot lettering (after the reference)
  add({ name: 'counter_face', w: 600, h: 450, age: lit(203, { paper: [0.06, 0.045, 0.035], bugs: false, dirt: 0.12, edgeDirt: 0.6, tubes: null, rough: 0.18 }),
    draw(g) {
      const W = 600, H = 450;
      // lettering into a mask canvas, then sampled onto an LED dot grid
      const mc = document.createElement('canvas');
      const res = 2;
      mc.width = W * res;
      mc.height = H * res;
      const m = mc.getContext('2d');
      m.scale(res, res);
      const lines = [['HOT RAMEN', 108, 104], ['COLD BREW', 108, 232], ['BETTER HUMANS', 86, 352]];
      for (const [t, sz, y] of lines) A.fitText(m, t, W / 2, y, 520, sz, { font: F.latin, weight: 700, color: '#fff', ls: 0.06 });
      const md = m.getImageData(0, 0, mc.width, mc.height).data;
      const pitch = 5.0;
      const rnd = A.rng(77);
      for (let y = pitch / 2; y < H; y += pitch) {
        for (let x = pitch / 2; x < W; x += pitch) {
          const v = md[(Math.floor(y * res) * mc.width + Math.floor(x * res)) * 4] / 255;
          const dead = rnd() < 0.012;
          if (v > 0.4 && !dead) {
            const warm = rnd() * 0.08;
            A.circle(g, x, y, pitch * 0.36, `rgb(255,${Math.round(178 + 30 * warm)},${Math.round(64 + 40 * warm)})`);
          } else {
            A.circle(g, x, y, pitch * 0.3, 'rgba(60,40,22,0.55)');
          }
        }
      }
      // a dark frame line
      g.strokeStyle = 'rgba(0,0,0,0.9)';
      g.lineWidth = 8;
      g.strokeRect(4, 4, W - 8, H - 8);
    },
    emisAt: (x, y, e, da) => e,
  });
  // Painted steel skin for the sign housings and brackets (charcoal paint, chipped, rusty edges)
  add({ name: 'frame_steel', w: 256, h: 256, age: { seed: 204, kind: 'metal', paper: [0.075, 0.075, 0.08], rough: 0.5, metal: 0.0, absorb: 0.5,
    yellow: 0, fade: 0, dirt: 0.3, edgeDirt: 0.0, scratches: 0.35, rust: 0.35, grain: 0.02, normalStrength: 0.6, streaks: 0.4 },
    draw(g) {
      // chips to grey primer / bare steel
      const r = A.rng(5);
      for (let k = 0; k < 28; k++) {
        const x = r() * 256, y = r() * 256, s = 0.5 + r() * 3;
        g.fillStyle = r() < 0.5 ? 'rgba(70,68,64,0.9)' : 'rgba(70,45,30,0.9)';
        g.beginPath();
        g.ellipse(x, y, s * (1 + r()), s, r() * 3, 0, Math.PI * 2);
        g.fill();
      }
    } });
})();
