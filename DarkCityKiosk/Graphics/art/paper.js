// Paper atlas: posters, notices, menus, owner-made notes (2 px/mm). Sizes in mm; draw(g) works in mm
// with the paper's top-left at (0, 0). See lib.js for the aging parameters.
(function () {
  const A = window.ART;
  const F = A.F;
  const items = (A.items = A.items || []);
  const add = (it) => items.push(Object.assign({ atlas: 'Paper', margin: 0 }, it));

  // The street brand of the city (KAZE screens on the towers): small poster, cool blue/cyan + red,
  // the newest paper in the door-wall cluster (relatively intact).
  add({
    name: 'kaze_poster', w: 280, h: 400, margin: 10,
    age: { seed: 1, paper: [0.93, 0.94, 0.95], rough: 0.5, absorb: 0.75, yellow: 0.03, fade: 0.12, dirt: 0.06, edgeDirt: 0.25,
      stains: 0.12, stainBias: 'bottom', stainScale: 30, crease: [['h', 0.5, 1.4, 0.25], ['v', 0.5, 1.0, 0.15]], wrinkle: 0.12,
      tape: [{ x: 0.02, y: 0.01, w: 34, h: 13, rot: -0.7, clear: true }, { x: 0.985, y: 0.012, w: 34, h: 13, rot: 0.75, clear: true },
        { x: 0.02, y: 0.985, w: 30, h: 12, rot: 0.6, color: [0.82, 0.76, 0.6] }] },
    draw(g) {
      const W = 280, H = 400;
      const grd = g.createLinearGradient(0, 0, 0, H);
      grd.addColorStop(0, '#071630');
      grd.addColorStop(0.55, '#0d4f86');
      grd.addColorStop(1, '#1db7d8');
      g.fillStyle = grd;
      g.fillRect(0, 0, W, H);
      // wind ribbons
      g.save();
      for (let k = 0; k < 14; k++) {
        g.strokeStyle = `rgba(190,240,255,${0.08 + 0.05 * (k % 3)})`;
        g.lineWidth = 0.6 + (k % 4) * 0.5;
        g.beginPath();
        for (let t = 0; t <= 1.0001; t += 0.02) {
          const x = -20 + t * (W + 40);
          const y = 70 + k * 21 + Math.sin(t * 5 + k * 0.7) * 18 + t * 60;
          t ? g.lineTo(x, y) : g.moveTo(x, y);
        }
        g.stroke();
      }
      g.restore();
      A.text(g, 'KAZE INDUSTRIES  ·  風  ·  NEO-TOKYO 2089', 14, 20, 7.5, { font: F.cond, weight: 600, color: '#cfeefa', ls: 1.2 });
      A.rect(g, 14, 25, W - 28, 0.8, 'rgba(207,238,250,0.7)');
      A.kazeMark(g, W / 2, 128, 72, '#f4fbff');
      A.fitText(g, 'KAZE', W / 2, 252, 200, 62, { font: F.latin, weight: 700, color: '#f4fbff', ls: 0.12 });
      A.fitText(g, 'カゼ', W / 2, 296, 60, 24, { font: F.jp, weight: 700, color: '#f4fbff', ls: 0.2 });
      // red accent band
      A.rect(g, 0, 318, W, 20, '#e3232c');
      A.fitText(g, 'NEW  K-7  NEURAL  WEAR', W / 2 - 18, 328, 190, 11, { font: F.cond, weight: 700, color: '#fff', ls: 0.15 });
      A.circle(g, W - 22, 328, 6.5, '#fff');
      A.circle(g, W - 22, 328, 3.5, '#e3232c');
      A.fitText(g, '風を、まとう。', W / 2, 360, 170, 19, { font: F.jp, weight: 700, color: '#ffffff' });
      A.fitText(g, 'A BRIGHTER HUMAN TOMORROW', W / 2, 378, 160, 6.5, { font: F.latin, weight: 600, color: '#e6f8ff', ls: 0.2 });
      // QR + small print
      A.rect(g, 236, 352, 32, 38, '#f4fbff');
      A.qr(g, 238.5, 354.5, 27, 4471, '#0b1d3a');
      A.text(g, 'kaze.co/k7', 238, 388.5, 4.2, { font: F.mono, weight: 400, color: '#0b1d3a' });
      for (let k = 0; k < 3; k++) A.rect(g, 14, 386 + k * 3.2, 120 - k * 25, 1.0, 'rgba(220,245,255,0.55)');
      A.text(g, '© KAZE 2089', 14, 397, 4, { font: F.latin, weight: 400, color: 'rgba(220,245,255,0.8)' });
    },
  });

  // Faded food advertisement (the oldest print in the cluster): sun-bleached, drifting cyan, water stained
  add({
    name: 'ramen_ad', w: 297, h: 420, margin: 0,
    age: { seed: 2, paper: [0.93, 0.92, 0.88], rough: 0.65, yellow: 0.22, fade: 0.82, fadeTop: true, dirt: 0.22, edgeDirt: 0.45,
      stains: 0.55, stainBias: 'bottom', stainScale: 45, streaks: 0.35, crease: [['h', 0.33, 1.5, 0.3]], wrinkle: 0.3,
      tears: [{ a: [0.78, 1.02], b: [1.02, 0.83], jag: 5, keep: 1, seed: 3 }], holes: [[0.06, 0.04, 2.0], [0.94, 0.05, 1.6]] },
    draw(g) {
      const W = 297, H = 420;
      A.rect(g, 0, 0, W, 210, '#c8102e');
      A.rect(g, 0, 210, W, 210, '#f6efe0');
      // burst
      g.save();
      g.translate(62, 52);
      g.fillStyle = '#ffd400';
      g.beginPath();
      for (let k = 0; k < 32; k++) {
        const r = k % 2 ? 30 : 42, a = (k / 32) * Math.PI * 2;
        k ? g.lineTo(Math.cos(a) * r, Math.sin(a) * r) : g.moveTo(Math.cos(a) * r, Math.sin(a) * r);
      }
      g.fill();
      g.restore();
      A.fitText(g, '濃厚', 62, 52, 50, 30, { font: F.jp, weight: 900, color: '#c8102e' });
      A.fitText(g, 'とんこつ', 190, 58, 180, 46, { font: F.jp, weight: 900, color: '#fff', stroke: '#5a0010', strokeW: 3 });
      A.fitText(g, 'ラーメン', 190, 110, 180, 40, { font: F.jp, weight: 900, color: '#fff', stroke: '#5a0010', strokeW: 3 });
      // bowl illustration
      const cx = W / 2, cy = 205;
      g.save();
      g.beginPath();
      g.ellipse(cx, cy + 18, 118, 66, 0, 0, Math.PI);
      g.closePath();
      const bg = g.createLinearGradient(0, cy, 0, cy + 90);
      bg.addColorStop(0, '#1b1b1b');
      bg.addColorStop(1, '#3a2c22');
      g.fillStyle = bg;
      g.fill();
      g.beginPath();
      g.ellipse(cx, cy + 18, 118, 30, 0, 0, Math.PI * 2);
      const br = g.createRadialGradient(cx - 20, cy + 10, 10, cx, cy + 18, 120);
      br.addColorStop(0, '#f3d79a');
      br.addColorStop(1, '#c58a3a');
      g.fillStyle = br;
      g.fill();
      // noodles
      g.strokeStyle = '#f8e7b0';
      g.lineWidth = 1.6;
      for (let k = 0; k < 26; k++) {
        g.beginPath();
        const y = cy + 6 + (k % 7) * 4;
        for (let t = 0; t <= 1; t += 0.05) {
          const x = cx - 90 + t * 180;
          const yy = y + Math.sin(t * 12 + k) * 3;
          t ? g.lineTo(x, yy) : g.moveTo(x, yy);
        }
        g.stroke();
      }
      // chashu, egg, nori, negi
      for (const [x, y] of [[cx - 55, cy + 8], [cx - 25, cy + 2]]) {
        A.circle(g, x, y, 18, '#b9724b');
        A.circle(g, x, y, 13, '#d9a07a');
        A.circle(g, x + 3, y - 2, 6, '#efc9a8');
      }
      for (const x of [cx + 30, cx + 52]) {
        g.beginPath();
        g.ellipse(x, cy + 12, 14, 10, 0.3, 0, Math.PI * 2);
        g.fillStyle = '#fbf6ea';
        g.fill();
        A.circle(g, x, cy + 12, 6, '#f29b1d');
      }
      g.fillStyle = '#1d2a1a';
      g.save();
      g.translate(cx + 78, cy - 22);
      g.rotate(0.25);
      g.fillRect(-12, -26, 24, 42);
      g.restore();
      for (let k = 0; k < 30; k++) A.circle(g, cx - 10 + ((k * 37) % 70), cy + 18 + ((k * 13) % 14) - 7, 2.2, k % 2 ? '#5aa33a' : '#8fd062');
      g.restore();
      A.fitText(g, '¥680', W / 2 + 40, 318, 150, 64, { font: F.latin, weight: 700, color: '#c8102e' });
      A.text(g, '税込', 34, 320, 13, { font: F.jp, weight: 700, color: '#c8102e' });
      A.rect(g, 20, 350, 150, 26, '#111');
      A.fitText(g, '替玉 1回無料', 95, 363, 136, 17, { font: F.jp, weight: 900, color: '#ffd400' });
      // stamp-like shop mark
      A.rect(g, 222, 344, 54, 54, '#c8102e');
      A.fitText(g, '風月', 249, 364, 44, 22, { font: F.jpMincho, weight: 700, color: '#fff' });
      A.fitText(g, '麺屋', 249, 386, 30, 12, { font: F.jpMincho, weight: 700, color: '#fff' });
      A.text(g, '※写真はイメージです', 20, 398, 7, { font: F.jp, weight: 400, color: '#333' });
      A.text(g, '麺屋 風月  三番街店  営業 11:00〜翌3:00', 20, 410, 7.5, { font: F.jp, weight: 700, color: '#333' });
    },
  });

  // Torn flyer for a local night market: most of the upper-left torn away
  add({
    name: 'market_flyer', w: 210, h: 297, margin: 6,
    age: { seed: 3, paper: [0.95, 0.94, 0.9], rough: 0.8, yellow: 0.18, fade: 0.38, dirt: 0.16, edgeDirt: 0.35, stains: 0.38,
      stainBias: 'bottom', stainScale: 28, crease: [['h', 0.5, 1.2, 0.3]], wrinkle: 0.35,
      tears: [{ a: [-0.05, 0.62], b: [0.74, -0.05], jag: 9, scale: 11, seed: 5 }],
      holes: [[0.9, 0.93, 1.4]],
      tape: [{ x: 0.97, y: 0.0, w: 26, h: 11, rot: 0.6, color: [0.8, 0.74, 0.58] }, { x: 0.03, y: 0.99, w: 26, h: 11, rot: -0.5, color: [0.8, 0.74, 0.58] }] },
    draw(g) {
      const W = 210, H = 297;
      A.rect(g, 0, 0, W, H, '#1b1f4a');
      // lantern string
      g.strokeStyle = '#2b2b2b';
      g.lineWidth = 0.8;
      g.beginPath();
      g.moveTo(0, 30);
      g.quadraticCurveTo(W / 2, 62, W, 30);
      g.stroke();
      for (let k = 0; k < 7; k++) {
        const t = (k + 0.5) / 7, x = t * W, y = 30 + 4 * 32 * t * (1 - t) + 14;
        g.save();
        g.beginPath();
        g.ellipse(x, y, 11, 14, 0, 0, Math.PI * 2);
        g.fillStyle = k % 2 ? '#ff8a1f' : '#ffb84d';
        g.fill();
        g.strokeStyle = 'rgba(80,30,0,0.6)';
        for (let r = -10; r <= 10; r += 4) {
          g.beginPath();
          g.moveTo(x - 11 * Math.sqrt(1 - (r / 14) ** 2), y + r);
          g.lineTo(x + 11 * Math.sqrt(1 - (r / 14) ** 2), y + r);
          g.stroke();
        }
        g.restore();
      }
      A.fitText(g, '第38回', W / 2, 92, 70, 16, { font: F.jp, weight: 700, color: '#ffd28a' });
      A.fitText(g, '下町夜市', W / 2, 128, 180, 44, { font: F.jp, weight: 900, color: '#ffffff', stroke: '#ff8a1f', strokeW: 1.5 });
      A.fitText(g, 'NIGHT  MARKET', W / 2, 160, 150, 14, { font: F.cond, weight: 700, color: '#ffb84d', ls: 0.2 });
      A.rect(g, 18, 176, W - 36, 0.8, '#ffb84d');
      A.fitText(g, '10.12 SAT  18:00 – 24:00', W / 2, 196, 170, 15, { font: F.latin, weight: 700, color: '#fff' });
      A.fitText(g, '東区三番街  高架下', W / 2, 220, 150, 14, { font: F.jp, weight: 700, color: '#fff' });
      A.fitText(g, '屋台 ・ 古道具 ・ 修理 ・ 音楽', W / 2, 244, 170, 11, { font: F.jp, weight: 700, color: '#ffd28a' });
      // stall silhouettes
      g.fillStyle = '#0e1030';
      for (let k = 0; k < 5; k++) {
        const x = 12 + k * 40;
        g.fillRect(x, 262, 32, 22);
        g.beginPath();
        g.moveTo(x - 3, 262);
        g.lineTo(x + 16, 252);
        g.lineTo(x + 35, 262);
        g.fill();
      }
      A.text(g, '主催 三番街商店会  協賛 KAZE', 14, 292, 6.5, { font: F.jp, weight: 700, color: '#c9c9e6' });
    },
  });

  // Electrical inspection notice from the utility (tri-folded letter, stained edges, taped)
  add({
    name: 'inspection_notice', w: 210, h: 297, margin: 8,
    age: { seed: 4, paper: [0.95, 0.95, 0.93], rough: 0.85, yellow: 0.38, fade: 0.15, dirt: 0.22, edgeDirt: 0.7, stains: 0.75,
      stainBias: 'edges', stainScale: 26, crease: [['h', 0.333, 1.3, 0.4], ['h', 0.666, 1.3, 0.4]], wrinkle: 0.3,
      tape: [{ x: 0.0, y: 0.0, w: 30, h: 12, rot: -0.78, color: [0.86, 0.79, 0.55] }, { x: 1.0, y: 0.0, w: 30, h: 12, rot: 0.78, color: [0.86, 0.79, 0.55] },
        { x: 0.0, y: 1.0, w: 30, h: 12, rot: 0.78, color: [0.86, 0.79, 0.55] }, { x: 1.0, y: 1.0, w: 30, h: 12, rot: -0.78, color: [0.86, 0.79, 0.55] }] },
    draw(g) {
      const W = 210;
      A.text(g, '2089年 8月 25日', W - 16, 18, 6.5, { font: F.jp, weight: 400, align: 'right' });
      A.rrect(g, 16, 26, W - 32, 30, 1, null, '#111', 1.2);
      A.fitText(g, 'お知らせ', W / 2, 41, 70, 18, { font: F.jp, weight: 900 });
      A.fitText(g, '電気設備 定期点検 実施のお知らせ', W / 2, 74, 172, 12, { font: F.jp, weight: 700 });
      A.text(g, 'NOTICE OF SCHEDULED ELECTRICAL INSPECTION', W / 2, 84, 5.2, { font: F.latin, weight: 400, align: 'center' });
      const lines = ['日頃より電力の安定供給にご協力いただき、誠にありがとうございます。', '下記の日程にて、受変電設備の定期点検を実施いたします。',
        '点検中は一時的に停電いたします。ご不便をおかけしますが、', 'ご理解とご協力をお願い申し上げます。'];
      lines.forEach((l, i) => A.text(g, l, 18, 100 + i * 9, 6.2, { font: F.jp, weight: 400, maxW: 176 }));
      A.fitText(g, '記', W / 2, 146, 10, 8, { font: F.jp, weight: 700 });
      const rows = [['実施日', '2089年 9月 14日 (水)'], ['時　間', '午前 2:00 〜 5:00'], ['停　電', '約 30分 (2回)'], ['対　象', '東区三番街 第三街区 屋台 K-01〜K-12']];
      rows.forEach(([k, v], i) => {
        const y = 156 + i * 14;
        g.strokeStyle = '#111';
        g.lineWidth = 0.5;
        g.strokeRect(22, y, 40, 14);
        g.strokeRect(62, y, 126, 14);
        A.text(g, k, 42, y + 9.6, 6.8, { font: F.jp, weight: 700, align: 'center' });
        A.text(g, v, 66, y + 9.6, 6.8, { font: F.jp, weight: 400, maxW: 118 });
      });
      A.text(g, '※雨天の場合も実施いたします。', 22, 226, 6, { font: F.jp, weight: 400 });
      A.text(g, '東都電設株式会社  保安課', W - 18, 250, 7.5, { font: F.jp, weight: 700, align: 'right' });
      A.text(g, 'TEL 03-5512-0471 (24時間受付)', W - 18, 261, 6.2, { font: F.jp, weight: 400, align: 'right' });
      // red hanko + handwritten tick
      g.save();
      g.translate(44, 262);
      g.rotate(-0.15);
      A.circle(g, 0, 0, 13, null, 'rgba(200,20,30,0.85)', 1.6);
      A.fitText(g, '点検', 0, -3.5, 14, 7, { font: F.jpMincho, weight: 700, color: 'rgba(200,20,30,0.85)' });
      A.fitText(g, '済', 0, 6, 8, 7, { font: F.jpMincho, weight: 700, color: 'rgba(200,20,30,0.85)' });
      g.restore();
      A.hand(g, '9/14 済  森', 66, 276, 11, { font: F.jp, color: '#1f3a8a', seed: 11, weight: 400, thick: 0.03 });
    },
  });

  // Laminated menu card by the service window, with the owner's price corrections
  add({
    name: 'menu_card', w: 148, h: 210, margin: 7,
    age: { seed: 5, paper: [0.97, 0.95, 0.9], rough: 0.24, absorb: 0.35, yellow: 0.1, fade: 0.25, dirt: 0.1, edgeDirt: 0.3, stains: 0.12,
      stainScale: 20, wrinkle: 0.05, grain: 0.015,
      tape: [{ x: 0.12, y: -0.01, w: 30, h: 12, rot: -0.12, clear: true }, { x: 0.88, y: -0.01, w: 30, h: 12, rot: 0.1, clear: true }] },
    draw(g) {
      const W = 148, H = 210;
      A.rect(g, 0, 0, W, H, '#f4ead4');
      A.rect(g, 6, 6, W - 12, H - 12, '#fbf5e6');
      A.rect(g, 6, 6, W - 12, 30, '#222');
      A.fitText(g, 'お品書き', W / 2 - 14, 21, 70, 16, { font: F.jpMincho, weight: 700, color: '#fbf5e6' });
      A.text(g, 'MENU', W - 14, 25, 8, { font: F.latin, weight: 700, color: '#e3a33a', align: 'right' });
      const rows = [['醤油ラーメン', '680'], ['味噌ラーメン', '720'], ['塩ラーメン', '680'], ['替え玉', '150'], ['味付玉子', '100'],
        ['珈琲  HOT / ICE', '400'], ['水出し珈琲', '480']];
      rows.forEach(([k, v], i) => {
        const y = 52 + i * 17;
        A.text(g, k, 14, y, 9, { font: F.jp, weight: 700, color: '#222', maxW: 84 });
        g.strokeStyle = 'rgba(0,0,0,0.35)';
        g.setLineDash([0.8, 1.6]);
        g.lineWidth = 0.5;
        g.beginPath();
        g.moveTo(14, y + 3);
        g.lineTo(W - 14, y + 3);
        g.stroke();
        g.setLineDash([]);
        A.text(g, v, W - 14, y, 10, { font: F.latin, weight: 700, color: '#b3121f', align: 'right' });
      });
      A.rect(g, 12, 172, W - 24, 24, '#b3121f');
      A.fitText(g, '義体 調整・修理  要相談', W / 2, 180, W - 34, 9, { font: F.jp, weight: 700, color: '#fff' });
      A.fitText(g, 'IMPLANT TUNING & REPAIR — ASK', W / 2, 190, W - 40, 5, { font: F.latin, weight: 600, color: '#ffd9d9' });
      // the owner's corrections: shoyu 680 struck through -> 720 in marker; coffee 400 under a small sticker "450"
      g.strokeStyle = 'rgba(200,20,20,0.9)';
      g.lineWidth = 1.4;
      g.beginPath();
      g.moveTo(W - 34, 49);
      g.lineTo(W - 12, 47);
      g.stroke();
      A.hand(g, '720', W - 52, 45, 9, { font: F.latin, color: 'rgba(200,20,20,0.95)', seed: 4, weight: 700, rot: -0.1 });
      A.rect(g, W - 36, 136, 26, 13, '#fffdf6');
      A.hand(g, '450', W - 33, 146.5, 10, { font: F.latin, color: '#111', seed: 9, weight: 700 });
    },
  });

  // Owner-made: "today: miso sold out, sorry" on a page torn from a notebook
  add({
    name: 'soldout_note', w: 128, h: 92, margin: 6,
    age: { seed: 6, paper: [0.97, 0.97, 0.95], rough: 0.85, yellow: 0.06, fade: 0.05, dirt: 0.1, edgeDirt: 0.2, wrinkle: 0.4,
      crease: [['v', 0.62, 1.0, 0.2]], tears: [{ a: [0.03, -0.1], b: [0.03, 1.1], jag: 1.2, scale: 2.5, keep: -1, seed: 12 }],
      tape: [{ x: 0.5, y: 0.0, w: 50, h: 13, rot: 0.04, color: [0.86, 0.82, 0.66] }] },
    draw(g) {
      const W = 128, H = 92;
      for (let y = 14; y < H; y += 7) A.rect(g, 0, y, W, 0.35, 'rgba(70,120,200,0.55)');
      A.rect(g, 16, 0, 0.5, H, 'rgba(220,60,70,0.6)');
      for (let y = 4; y < H; y += 6) A.circle(g, 5, y, 1.1, 'rgba(0,0,0,0.25)');
      A.hand(g, '本日', 22, 25, 11, { seed: 21, thick: 0.07 });
      A.hand(g, '味噌 売切れ!!', 22, 47, 15, { seed: 22, thick: 0.08 });
      g.strokeStyle = 'rgba(210,25,25,0.9)';
      g.lineWidth = 1.6;
      g.beginPath();
      g.moveTo(22, 52);
      g.bezierCurveTo(50, 55, 80, 50, 118, 53);
      g.stroke();
      A.hand(g, 'すみません  店主', 46, 72, 9, { seed: 23, thick: 0.06 });
    },
  });

  // Owner-made: coffee price rise on a scrap of kraft card
  add({
    name: 'price_note', w: 92, h: 58, margin: 5,
    age: { seed: 7, paper: [0.62, 0.48, 0.33], rough: 0.9, yellow: 0.0, fade: 0.05, dirt: 0.15, edgeDirt: 0.3, wrinkle: 0.15, grain: 0.06,
      tears: [{ a: [1.05, 0.7], b: [0.82, 1.05], jag: 2.5, keep: 1, seed: 13 }],
      tape: [{ x: 0.5, y: 0.0, w: 34, h: 11, rot: -0.05, clear: true }] },
    draw(g) {
      A.hand(g, '珈琲', 8, 19, 12, { seed: 31, thick: 0.07 });
      A.hand(g, '450円に', 8, 36, 12, { seed: 32, thick: 0.07, font: F.jp });
      A.hand(g, '値上げしました', 8, 51, 9.5, { seed: 33, thick: 0.06 });
    },
  });

  // Small vertical food sign (tanzaku): gyoza
  add({
    name: 'gyoza_strip', w: 72, h: 290, margin: 6,
    age: { seed: 8, paper: [0.96, 0.95, 0.9], rough: 0.8, yellow: 0.18, fade: 0.45, dirt: 0.15, edgeDirt: 0.35, stains: 0.3,
      stainBias: 'bottom', stainScale: 22, wrinkle: 0.3,
      tape: [{ x: 0.5, y: 0.0, w: 34, h: 12, rot: 0.03, color: [0.84, 0.78, 0.6] }, { x: 0.5, y: 1.0, w: 34, h: 12, rot: -0.04, color: [0.84, 0.78, 0.6] }] },
    draw(g) {
      const W = 72, H = 290;
      g.strokeStyle = '#c4161c';
      g.lineWidth = 3;
      g.strokeRect(5, 5, W - 10, H - 10);
      A.vtext(g, '餃子', W / 2, 18, 46, { font: F.jpMincho, weight: 700, color: '#c4161c' });
      A.vtext(g, 'あります', W / 2, 120, 26, { font: F.jp, weight: 900, color: '#1a1a1a' });
      A.fitText(g, '6個 380円', W / 2, 268, 56, 10, { font: F.jp, weight: 700, color: '#c4161c' });
    },
  });

  // Old "cash only" card, crossed out by hand when the stall went cashless
  add({
    name: 'cash_card', w: 91, h: 55, margin: 5,
    age: { seed: 9, paper: [0.95, 0.94, 0.9], rough: 0.8, yellow: 0.32, fade: 0.65, dirt: 0.28, edgeDirt: 0.5, stains: 0.35, stainScale: 15,
      wrinkle: 0.15, tape: [{ x: 0.0, y: 0.5, w: 12, h: 26, rot: 0.1, clear: true, dirt: 0.6 }] },
    draw(g) {
      A.rect(g, 4, 4, 83, 47, '#fff');
      A.rect(g, 4, 4, 83, 13, '#c4161c');
      A.fitText(g, 'お支払い', 45.5, 10.5, 50, 8, { font: F.jp, weight: 700, color: '#fff' });
      A.fitText(g, '現金のみ', 45.5, 28, 70, 15, { font: F.jp, weight: 900, color: '#111' });
      A.fitText(g, 'CASH ONLY', 45.5, 42, 50, 8, { font: F.latin, weight: 700, color: '#111' });
      g.strokeStyle = 'rgba(15,15,15,0.92)';
      g.lineWidth = 2.4;
      g.lineCap = 'round';
      g.beginPath();
      g.moveTo(8, 10);
      g.lineTo(82, 47);
      g.moveTo(80, 9);
      g.lineTo(10, 46);
      g.stroke();
      A.hand(g, '電子決済OK→', 30, 54, 7.5, { color: '#1f3fae', seed: 41, thick: 0.05 });
    },
  });

  // Implant-clinic poster on the strip between the service window and the window bay
  add({
    name: 'clinic_poster', w: 250, h: 353, margin: 8,
    age: { seed: 10, paper: [0.95, 0.95, 0.94], rough: 0.6, absorb: 0.85, yellow: 0.12, fade: 0.4, dirt: 0.14, edgeDirt: 0.35, stains: 0.3,
      stainBias: 'bottom', stainScale: 35, streaks: 0.25, crease: [['v', 0.5, 1.2, 0.25]], wrinkle: 0.2,
      tape: [{ x: 0.0, y: 0.0, w: 28, h: 11, rot: -0.75, clear: true }, { x: 1.0, y: 0.0, w: 28, h: 11, rot: 0.75, clear: true },
        { x: 1.0, y: 1.0, w: 28, h: 11, rot: -0.75, clear: true }] },
    draw(g) {
      const W = 250, H = 353;
      A.rect(g, 0, 0, W, H, '#f3f3f1');
      A.rect(g, 0, 0, W, 64, '#d0101f');
      A.fitText(g, '義体メンテナンス', W / 2, 30, 220, 34, { font: F.jp, weight: 900, color: '#fff' });
      A.fitText(g, 'PROSTHETIC  MAINTENANCE', W / 2, 54, 180, 9, { font: F.cond, weight: 700, color: '#ffd5d8', ls: 0.15 });
      // schematic arm
      g.save();
      g.translate(70, 92);
      g.strokeStyle = '#1a1a1a';
      g.lineWidth = 1.6;
      g.fillStyle = '#e5e7ea';
      const seg = (x, y, w, h, a) => {
        g.save();
        g.translate(x, y);
        g.rotate(a);
        g.beginPath();
        g.roundRect(-w / 2, 0, w, h, w / 2);
        g.fill();
        g.stroke();
        g.restore();
      };
      seg(0, 0, 34, 92, -0.2);
      A.circle(g, 18, 92, 13, '#d0101f', '#1a1a1a', 1.6);
      seg(18, 92, 26, 88, -0.65);
      A.circle(g, 72, 160, 9, '#e5e7ea', '#1a1a1a', 1.6);
      for (let k = 0; k < 4; k++) seg(72 + k * 6 - 8, 160, 5, 26 - k * 3, -0.9 + k * 0.25);
      g.strokeStyle = '#1d6fb8';
      g.lineWidth = 0.8;
      for (let k = 0; k < 3; k++) {
        g.beginPath();
        g.moveTo(-4 + k * 4, 10);
        g.bezierCurveTo(10 + k * 4, 60, 0 + k * 4, 80, 18 + k * 3, 92);
        g.stroke();
      }
      g.restore();
      const callout = (y, t1, t2) => {
        A.rect(g, 150, y, 86, 0.6, '#1a1a1a');
        A.text(g, t1, 150, y + 11, 10, { font: F.jp, weight: 700 });
        A.text(g, t2, 150, y + 20, 5.5, { font: F.latin, weight: 400, color: '#555' });
      };
      callout(96, '関節・駆動系', 'JOINT / ACTUATOR');
      callout(134, '神経接続', 'NEURAL LINK');
      callout(172, '人工皮膚 交換', 'SKIN REPLACEMENT');
      callout(210, '定期点検', 'ROUTINE CHECK');
      A.rect(g, 0, 268, W, 40, '#1a1a1a');
      A.fitText(g, '24H  予約不要', W / 2, 288, 200, 22, { font: F.jp, weight: 900, color: '#ffd400' });
      A.fitText(g, 'タクミ義体工房  第三街区 2F', W / 2, 324, 220, 14, { font: F.jp, weight: 700, color: '#1a1a1a' });
      A.fitText(g, 'CYBER CLINIC TAKUMI   TEL 03-5512-8840', W / 2, 342, 220, 7, { font: F.latin, weight: 600, color: '#d0101f' });
    },
  });

  // The top strip of a poster someone tore down: still taped, ragged lower edge
  add({
    name: 'torn_remnant', w: 230, h: 62, margin: 7,
    age: { seed: 11, paper: [0.94, 0.93, 0.88], rough: 0.7, yellow: 0.3, fade: 0.65, dirt: 0.25, edgeDirt: 0.45, stains: 0.3, stainBias: 'top',
      wrinkle: 0.35, tears: [{ a: [1.05, 0.42], b: [-0.05, 0.7], jag: 10, scale: 12, keep: -1, seed: 17 }],
      tape: [{ x: 0.02, y: 0.06, w: 30, h: 12, rot: -0.65, color: [0.82, 0.74, 0.55], dirt: 0.6 }, { x: 0.97, y: 0.08, w: 30, h: 12, rot: 0.55, color: [0.82, 0.74, 0.55], dirt: 0.6 }] },
    draw(g) {
      A.rect(g, 0, 0, 230, 62, '#1f6e3a');
      A.rect(g, 0, 0, 230, 8, '#ffd400');
      A.fitText(g, '大感謝セール  全品', 115, 42, 200, 30, { font: F.jp, weight: 900, color: '#fff' });
    },
  });

  // Owner-made note on the door: please knock
  add({
    name: 'knock_note', w: 108, h: 74, margin: 6,
    age: { seed: 12, paper: [0.96, 0.96, 0.93], rough: 0.85, yellow: 0.12, fade: 0.08, dirt: 0.12, edgeDirt: 0.3, wrinkle: 0.2,
      stains: 0.2, stainScale: 18, tape: [{ x: 0.5, y: 0.0, w: 40, h: 12, rot: -0.06, clear: true, dirt: 0.5 }] },
    draw(g) {
      A.hand(g, '御用の方は', 10, 22, 11, { seed: 51, thick: 0.06 });
      A.hand(g, 'ノックして', 10, 42, 15, { seed: 52, thick: 0.07 });
      A.hand(g, 'ください →', 34, 62, 11, { seed: 53, thick: 0.06 });
    },
  });

  // Scraps of tape still holding torn paper corners (where notices were ripped off)
  for (const [i, rot] of [[0, -0.5], [1, 0.4], [2, -0.1]]) {
    add({
      name: `tape_scrap_${i}`, w: 26, h: 20, margin: 8,
      age: { seed: 20 + i, paper: [0.93, 0.92, 0.87], rough: 0.8, yellow: 0.35, fade: 0.5, dirt: 0.3, edgeDirt: 0.5, wrinkle: 0.4,
        tears: [{ a: [1.1, 0.25 + i * 0.1], b: [0.15 + i * 0.1, 1.1], jag: 4, scale: 4, keep: 1, seed: 30 + i }],
        tape: [{ x: 0.3, y: 0.3, w: 32, h: 11, rot, color: [0.8, 0.73, 0.55], dirt: 0.7 }] },
      draw(g) {
        A.rect(g, 0, 0, 26, 20, ['#d4d0c2', '#b3121f', '#1b1f4a'][i]);
      },
    });
  }
})();
