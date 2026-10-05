// Labels atlas: small maintenance and industrial labels, inspection stickers, nameplates, street
// stickers, the payment decal and the permit plate (4 px/mm). Reusable: one cell can go on many parts.
(function () {
  const A = window.ART;
  const F = A.F;
  const items = (A.items = A.items || []);
  const add = (it) => items.push(Object.assign({ atlas: 'Labels', margin: 0 }, it));
  const vinyl = (seed, extra = {}) => Object.assign({ seed, kind: 'vinyl', rough: 0.42, absorb: 0.4, yellow: 0.04, fade: 0.2, dirt: 0.1,
    edgeDirt: 0.45, scratches: 0.25, wrinkle: 0.02, grain: 0.01, normalStrength: 0.6 }, extra);
  const metal = (seed, extra = {}) => Object.assign({ seed, kind: 'metal', paper: [0.62, 0.63, 0.63], rough: 0.32, metal: 1, absorb: 0.3,
    yellow: 0, fade: 0, dirt: 0.18, edgeDirt: 0.6, scratches: 0.7, wrinkle: 0, grain: 0.0, rust: 0.25, normalStrength: 1.2 }, extra);
  const plate = (seed, extra = {}) => Object.assign({ seed, kind: 'plastic', rough: 0.3, absorb: 0.35, yellow: 0.05, fade: 0.15, dirt: 0.12,
    edgeDirt: 0.5, scratches: 0.4, wrinkle: 0, grain: 0.005, normalStrength: 0.8 }, extra);

  // hazard: electric shock triangle (die-cut)
  add({ name: 'haz_bolt', w: 56, h: 50, design_alpha: true, age: vinyl(101, { fade: 0.3 }),
    draw: (g) => A.hazard(g, 28, 28.5, 54, 'bolt') });
  add({ name: 'haz_bolt_small', w: 34, h: 30, design_alpha: true, age: vinyl(102, { fade: 0.45, dirt: 0.2 }),
    draw: (g) => A.hazard(g, 17, 17.2, 32.5, 'bolt') });
  // hazard with text panel
  add({ name: 'haz_shock_jp', w: 56, h: 78, shape: 'rounded', radius: 3, age: vinyl(103, { fade: 0.25 }),
    draw(g) {
      A.rect(g, 0, 0, 56, 78, '#f7f5ef');
      A.rect(g, 0, 0, 56, 50, '#f2c200');
      A.hazard(g, 28, 27, 42, 'bolt');
      A.fitText(g, '感電注意', 28, 60, 48, 11, { font: F.jp, weight: 900 });
      A.fitText(g, 'DANGER  HIGH VOLTAGE', 28, 72, 46, 4.6, { font: F.latin, weight: 700, color: '#c4161c' });
    } });
  add({ name: 'haz_hot', w: 50, h: 70, shape: 'rounded', radius: 3, age: vinyl(104, { fade: 0.35, dirt: 0.25 }),
    draw(g) {
      A.rect(g, 0, 0, 50, 70, '#f7f5ef');
      A.hazard(g, 25, 24, 40, 'hot');
      A.fitText(g, '高温注意', 25, 54, 42, 10, { font: F.jp, weight: 900 });
      A.fitText(g, 'CAUTION HOT SURFACE', 25, 65, 42, 4.2, { font: F.latin, weight: 700 });
    } });
  add({ name: 'no_open', w: 62, h: 26, shape: 'rounded', radius: 2, age: vinyl(105, { fade: 0.3 }),
    draw(g) {
      A.rect(g, 0, 0, 62, 26, '#c4161c');
      A.fitText(g, '通電中 開放厳禁', 31, 11, 56, 10, { font: F.jp, weight: 900, color: '#fff' });
      A.fitText(g, 'LIVE — DO NOT OPEN', 31, 21.5, 50, 5, { font: F.latin, weight: 700, color: '#fff' });
    } });
  // voltage labels
  add({ name: 'volt_200', w: 40, h: 17, shape: 'rounded', radius: 1.5, age: vinyl(106),
    draw(g) { A.rect(g, 0, 0, 40, 17, '#c4161c'); A.fitText(g, '200V', 20, 8.8, 34, 12, { font: F.latin, weight: 700, color: '#fff' }); } });
  add({ name: 'volt_100', w: 46, h: 17, shape: 'rounded', radius: 1.5, age: vinyl(107, { fade: 0.4 }),
    draw(g) {
      A.rect(g, 0, 0, 46, 17, '#fff'); g.strokeStyle = '#c4161c'; g.lineWidth = 1.6; g.strokeRect(1.2, 1.2, 43.6, 14.6);
      A.fitText(g, 'AC100V', 23, 8.8, 38, 10, { font: F.latin, weight: 700, color: '#c4161c' });
    } });
  add({ name: 'volt_3ph', w: 52, h: 17, shape: 'rounded', radius: 1.5, age: vinyl(108),
    draw(g) { A.rect(g, 0, 0, 52, 17, '#1d4fa3'); A.fitText(g, '3φ 200V 60A', 26, 8.8, 46, 9.5, { font: F.latin, weight: 700, color: '#fff' }); } });
  // engraved equipment ID plates (lamacoid: the letters cut through to the white core)
  const engraved = (name, txt, bg, fg, w, h, seed) => add({ name, w, h, shape: 'rounded', radius: 1.2, age: plate(seed),
    relief: (x, y) => 0, draw(g) {
      A.rect(g, 0, 0, w, h, bg);
      A.fitText(g, txt, w / 2, h / 2 + 0.3, w - 7, h * 0.58, { font: F.latin, weight: 700, color: fg, ls: 0.06 });
      for (const x of [2.6, w - 2.6]) A.circle(g, x, h / 2, 1.1, 'rgba(0,0,0,0.55)');
    } });
  engraved('id_db02', 'DB-02', '#151515', '#f2f2f2', 46, 15, 109);
  engraved('id_k07', 'K-07  主幹', '#f2c200', '#151515', 56, 16, 110);
  engraved('id_ml3', 'ML-3', '#b3121f', '#fff', 36, 13, 111);
  engraved('id_hv1', 'HV-1  空調', '#1e4d33', '#f0f0f0', 54, 16, 112);
  engraved('id_sg4', 'SG-4  看板', '#151515', '#f2f2f2', 52, 15, 113);
  engraved('id_wt', 'WT-1  給湯', '#1d4fa3', '#fff', 50, 15, 114);
  // round inspection stickers with punched months (the holes go through: opacity)
  const roundInsp = (name, col, year, txt, seed, fade, punched) => add({ name, w: 36, h: 36, shape: 'round', age: vinyl(seed, { fade, holes: [] }),
    draw(g) {
      A.circle(g, 18, 18, 18, col);
      A.circle(g, 18, 18, 11, '#fff');
      A.fitText(g, txt, 18, 16.5, 16, 6.5, { font: F.jp, weight: 900, color: col });
      A.fitText(g, year, 18, 23.5, 14, 4.2, { font: F.latin, weight: 700, color: '#111' });
      for (let mth = 1; mth <= 12; mth++) {
        const a = -Math.PI / 2 + ((mth - 0.5) / 12) * Math.PI * 2;
        A.fitText(g, String(mth), 18 + Math.cos(a) * 14.5, 18 + Math.sin(a) * 14.5, 4.5, 3.6, { font: F.latin, weight: 700, color: '#fff' });
      }
    },
    holesAt: punched });
  roundInsp('insp_green', '#1f8a3c', '2089', '点検済', 115, 0.12, [4]);
  roundInsp('insp_yellow', '#e0a400', '2086', '検査済', 116, 0.6, [10]);
  roundInsp('insp_blue', '#1d4fa3', '2088', '点検済', 117, 0.35, [7]);
  // punched-month holes (applied in the runner via it.age.holes from holesAt)
  for (const it of items) if (it.holesAt) it.age.holes = it.holesAt.map((mth) => {
    const a = -Math.PI / 2 + ((mth - 0.5) / 12) * Math.PI * 2;
    return [(18 + Math.cos(a) * 14.5) / 36, (18 + Math.sin(a) * 14.5) / 36, 1.6];
  });
  add({ name: 'insp_rect', w: 56, h: 32, shape: 'rounded', radius: 1.5, age: vinyl(118, { fade: 0.25, rough: 0.6, absorb: 0.7 }),
    draw(g) {
      A.rect(g, 0, 0, 56, 32, '#fbfbf7');
      A.rect(g, 0, 0, 56, 9, '#1d4fa3');
      A.fitText(g, '検査済証  INSPECTED', 28, 4.8, 50, 5.5, { font: F.jp, weight: 700, color: '#fff' });
      A.text(g, 'No. 8841', 3, 15, 4.2, { font: F.mono, weight: 400 });
      A.text(g, '2089.04.09', 3, 21, 4.2, { font: F.mono, weight: 400 });
      A.text(g, '東都電設', 3, 28.5, 4.6, { font: F.jp, weight: 700 });
      g.strokeStyle = '#111'; g.lineWidth = 0.35; g.strokeRect(34, 12, 19, 17);
      A.text(g, '検査員', 35, 15.5, 2.6, { font: F.jp, weight: 400 });
      A.hand(g, '森', 39, 26.5, 9, { seed: 61, color: '#1f3a8a', thick: 0.04, weight: 400 });
    } });
  add({ name: 'next_insp', w: 46, h: 24, shape: 'rounded', radius: 1.5, age: vinyl(119, { fade: 0.35, rough: 0.6, absorb: 0.7 }),
    draw(g) {
      A.rect(g, 0, 0, 46, 24, '#f39200');
      A.fitText(g, '次回点検', 23, 6, 30, 6.5, { font: F.jp, weight: 900, color: '#111' });
      A.rect(g, 3, 10, 40, 11, '#fff');
      A.hand(g, '2090. 3', 7, 19.2, 8, { font: F.latin, seed: 62, color: '#111', thick: 0.04 });
    } });
  // metal nameplates: stamped/etched, four rivet holes
  const nameplate = (name, w, h, lines, seed) => add({ name, w, h, shape: 'rounded', radius: 2, age: metal(seed),
    relief(x, y) {
      let r = 0;
      for (const [cx, cy] of [[3.5, 3.5], [w - 3.5, 3.5], [3.5, h - 3.5], [w - 3.5, h - 3.5]]) r -= Math.max(0, 1 - Math.hypot(x - cx, y - cy) / 1.6) * 0.6;
      return r;
    },
    metalAt: (x, y, m0, da) => m0 * (1 - da * 0.9),
    roughAt: (x, y, r0, R, G, B, da) => (da > 0.5 ? 0.55 : r0),
    draw(g) {
      g.strokeStyle = '#1a1a1a'; g.lineWidth = 0.4; g.strokeRect(6, 6, w - 12, h - 12);
      lines.forEach(([t, sz, font, bold], i, arr) => {
        const y = 10 + (i + 0.8) * ((h - 16) / arr.length);
        A.text(g, t, 9, y, sz, { font, weight: bold ? 700 : 400, color: '#161616', maxW: w - 18 });
      });
      for (const [cx, cy] of [[3.5, 3.5], [w - 3.5, 3.5], [3.5, h - 3.5], [w - 3.5, h - 3.5]]) A.circle(g, cx, cy, 1.6, '#2a2a2a');
    } });
  nameplate('plate_cabinet', 80, 46, [['TOHTO DENKI CO., LTD.', 5.4, F.latin, 1], ['TYPE  KX-220   分電盤', 4.4, F.jp, 0], ['SER. No.  0047731', 4.4, F.mono, 0],
    ['200V 3φ 50/60Hz 60A', 4.4, F.mono, 0], ['MFD. 2061.03   NEO-TOKYO', 4.0, F.latin, 0]], 120);
  nameplate('plate_hvac', 92, 54, [['業務用エアコン  PACKAGED A/C', 5.0, F.jp, 1], ['MODEL  HX-4000R', 4.6, F.mono, 0], ['REFRIGERANT  R-32  1.8 kg', 4.4, F.mono, 0],
    ['冷房 4.0kW  暖房 4.5kW', 4.4, F.jp, 0], ['SER. 22K09931   2074', 4.4, F.mono, 0]], 121);
  nameplate('plate_tank', 70, 40, [['第二種圧力容器', 5.0, F.jp, 1], ['MAX 0.98 MPa  120L', 4.4, F.mono, 0], ['No. P-55120', 4.4, F.mono, 0], ['検定 2069', 4.2, F.jp, 0]], 122);
  // the stall's official number plate (enamel)
  add({ name: 'plate_k07', w: 104, h: 40, shape: 'rounded', radius: 3, age: plate(123, { rough: 0.22, fade: 0.25, rust: 0.15 }),
    draw(g) {
      A.rrect(g, 0, 0, 104, 40, 3, '#16408a');
      A.rrect(g, 2.5, 2.5, 99, 35, 2, null, '#f2f2f2', 0.8);
      A.fitText(g, '東区 第三街区', 52, 12, 70, 8, { font: F.jp, weight: 700, color: '#f2f2f2' });
      A.fitText(g, '屋台  K-07', 52, 27, 84, 15, { font: F.jp, weight: 900, color: '#f2f2f2' });
      for (const x of [6, 98]) A.circle(g, x, 20, 1.8, '#0c0c0c');
    } });
  // service company stickers
  add({ name: 'svc_nagase', w: 72, h: 36, shape: 'rounded', radius: 2.5, age: vinyl(124, { fade: 0.25 }),
    draw(g) {
      const gr = g.createLinearGradient(0, 0, 72, 36); gr.addColorStop(0, '#0f5bb8'); gr.addColorStop(1, '#0a3e80');
      g.fillStyle = gr; g.fillRect(0, 0, 72, 36);
      A.fitText(g, 'ナガセ設備', 40, 10, 50, 10, { font: F.jp, weight: 900, color: '#fff' });
      A.fitText(g, '24h 修理受付', 40, 20, 48, 6.5, { font: F.jp, weight: 700, color: '#ffe066' });
      A.fitText(g, '0120-37-4410', 40, 29.5, 50, 7, { font: F.latin, weight: 700, color: '#fff' });
      // wrench
      g.save(); g.translate(11, 18); g.rotate(-0.7); g.fillStyle = '#fff';
      g.fillRect(-1.6, -9, 3.2, 16); A.circle(g, 0, -10, 4.2, '#fff'); A.rect(g, -1.3, -15, 2.6, 5, '#0f5bb8'); g.restore();
    } });
  add({ name: 'svc_minato', w: 60, h: 30, shape: 'rounded', radius: 2, age: vinyl(125, { fade: 0.7, dirt: 0.25, scratches: 0.5 }),
    draw(g) {
      A.rect(g, 0, 0, 60, 30, '#fff'); A.rect(g, 0, 0, 60, 10, '#c4161c');
      A.fitText(g, 'ミナト電機サービス', 30, 5.4, 54, 6, { font: F.jp, weight: 700, color: '#fff' });
      A.fitText(g, '冷凍・空調', 30, 17, 40, 7, { font: F.jp, weight: 900, color: '#c4161c' });
      A.fitText(g, '☎ 03-5512-2209', 30, 25.5, 44, 5, { font: F.latin, weight: 700, color: '#111' });
    } });
  // asset barcodes and a QR service log
  add({ name: 'asset_a', w: 50, h: 22, shape: 'rounded', radius: 1, age: vinyl(126, { rough: 0.5, fade: 0.2 }),
    draw(g) {
      A.rect(g, 0, 0, 50, 22, '#f4f4f0'); A.barcode(g, 4, 3, 42, 11, 51); A.text(g, 'ASSET 00-4471', 25, 19, 4.2, { font: F.mono, weight: 700, align: 'center' });
    } });
  add({ name: 'asset_b', w: 40, h: 20, shape: 'rounded', radius: 1, age: vinyl(127, { rough: 0.5, fade: 0.45, dirt: 0.25 }),
    draw(g) {
      A.rect(g, 0, 0, 40, 20, '#e9eef2'); A.barcode(g, 3, 3, 34, 9, 52); A.text(g, 'KS-0718  東都', 20, 17, 3.8, { font: F.jp, weight: 700, align: 'center' });
    } });
  add({ name: 'qr_log', w: 34, h: 42, shape: 'rounded', radius: 1.5, age: vinyl(128, { fade: 0.15 }),
    draw(g) {
      A.rect(g, 0, 0, 34, 42, '#fff'); A.rect(g, 0, 0, 34, 8, '#111');
      A.fitText(g, 'SERVICE LOG', 17, 4.2, 30, 4.5, { font: F.cond, weight: 700, color: '#fff' });
      A.qr(g, 3.5, 10.5, 27, 88); A.text(g, '点検記録', 17, 40.5, 3.6, { font: F.jp, weight: 700, align: 'center' });
    } });
  // pipe identification (flow labels)
  const flow = (name, txt, bg, fg, w, seed) => add({ name, w, h: 14, shape: 'rounded', radius: 1, age: vinyl(seed, { fade: 0.3 }),
    draw(g) {
      A.rect(g, 0, 0, w, 14, bg); A.fitText(g, txt, w / 2 - 6, 7.4, w - 20, 8, { font: F.jp, weight: 900, color: fg });
      g.fillStyle = fg; g.beginPath(); g.moveTo(w - 10, 3); g.lineTo(w - 3, 7); g.lineTo(w - 10, 11); g.fill();
    } });
  flow('flow_water', '給水 WATER', '#1d6fb8', '#fff', 64, 129);
  flow('flow_drain', '排水 DRAIN', '#6b6b6b', '#fff', 64, 130);
  flow('flow_gas', 'ガス GAS', '#f2c200', '#111', 56, 131);
  add({ name: 'refrig', w: 36, h: 18, shape: 'rounded', radius: 1.5, age: vinyl(132, { fade: 0.3 }),
    draw(g) { A.rect(g, 0, 0, 36, 18, '#fff'); A.rect(g, 0, 0, 12, 18, '#1d6fb8'); A.fitText(g, 'R-32', 24, 9.2, 20, 9, { font: F.latin, weight: 700, color: '#1d6fb8' }); } });
  add({ name: 'earth', w: 22, h: 22, shape: 'round', age: vinyl(133, { fade: 0.25 }),
    draw(g) {
      A.circle(g, 11, 11, 11, '#1f8a3c'); A.circle(g, 11, 11, 8.6, '#f2c200');
      g.fillStyle = '#111'; g.fillRect(10.3, 4, 1.4, 7); g.fillRect(5, 11, 12, 1.4); g.fillRect(6.8, 13.6, 8.4, 1.3); g.fillRect(8.6, 16.1, 4.8, 1.2);
    } });
  // "please buy a meal ticket" strip over the ticket machine
  add({ name: 'ticket_strip', w: 180, h: 30, shape: 'rounded', radius: 2, age: vinyl(134, { fade: 0.35 }),
    draw(g) {
      A.rect(g, 0, 0, 180, 30, '#c4161c');
      A.fitText(g, '食券をお買い求めください', 72, 13, 128, 13, { font: F.jp, weight: 900, color: '#fff' });
      A.fitText(g, 'PLEASE BUY A TICKET FIRST', 72, 25, 110, 5.5, { font: F.latin, weight: 700, color: '#ffd9d9' });
      g.fillStyle = '#fff'; g.beginPath(); g.moveTo(152, 8); g.lineTo(172, 8); g.lineTo(162, 23); g.fill();
    } });
  // breaker map in a plastic sleeve on the fuse box door
  add({ name: 'breaker_map', w: 66, h: 46, age: { seed: 135, kind: 'paper', paper: [0.96, 0.96, 0.92], rough: 0.25, absorb: 0.5, yellow: 0.3,
    fade: 0.2, dirt: 0.2, edgeDirt: 0.6, stains: 0.3, stainScale: 10, wrinkle: 0.05 },
    draw(g) {
      A.text(g, '分電盤  回路表', 33, 7, 5.2, { font: F.jp, weight: 700, align: 'center' });
      const rows = ['① 照明', '② 冷蔵庫', '③ 給湯器', '④ 看板', '⑤ 空調', '⑥ 予備'];
      rows.forEach((t, i) => {
        const y = 10 + i * 5.6;
        g.strokeStyle = '#333'; g.lineWidth = 0.25; g.strokeRect(4, y, 58, 5.6);
        A.text(g, t, 6, y + 4.2, 3.8, { font: F.jp, weight: 400 });
      });
      A.hand(g, '× 空調(屋上)', 32, 37.6, 4.0, { seed: 63, color: '#1f3a8a', thick: 0.04, weight: 400 });
      A.hand(g, '冷蔵庫 20A', 32, 21.4, 3.8, { seed: 64, color: '#c4161c', thick: 0.04, weight: 400 });
    } });
  // street stickers ("slaps"), different ages
  add({ name: 'st_cat', w: 48, h: 48, shape: 'round', age: vinyl(140, { fade: 0.5, dirt: 0.2 }),
    draw(g) {
      A.circle(g, 24, 24, 24, '#111'); A.circle(g, 24, 26, 15, '#f4f4f4');
      g.fillStyle = '#f4f4f4'; g.beginPath(); g.moveTo(10, 18); g.lineTo(14, 4); g.lineTo(21, 13); g.fill(); g.beginPath(); g.moveTo(38, 18); g.lineTo(34, 4); g.lineTo(27, 13); g.fill();
      A.circle(g, 18.5, 24, 3.4, '#19d3e0'); A.circle(g, 29.5, 24, 3.4, '#19d3e0'); A.circle(g, 18.5, 24, 1.3, '#111'); A.circle(g, 29.5, 24, 1.3, '#111');
      A.fitText(g, 'NEKO DRIVE', 24, 41.5, 28, 5, { font: F.cond, weight: 700, color: '#f4f4f4' });
    } });
  add({ name: 'st_band', w: 70, h: 44, shape: 'rounded', radius: 4, age: vinyl(141, { fade: 0.3, scratches: 0.5,
    tears: [{ a: [0.62, 1.1], b: [1.1, 0.42], jag: 4, scale: 5, keep: 1, seed: 141 }] }),
    draw(g) {
      A.rect(g, 0, 0, 70, 44, '#ff2f8e'); A.rect(g, 4, 4, 62, 36, '#111');
      A.fitText(g, 'NEON', 35, 17, 50, 14, { font: F.impact, weight: 400, color: '#ff2f8e' });
      A.fitText(g, 'TIGERS', 35, 32, 54, 12, { font: F.impact, weight: 400, color: '#f4f4f4' });
    } });
  add({ name: 'st_kaze', w: 40, h: 40, shape: 'round', age: vinyl(142, { fade: 0.15 }),
    draw(g) { A.circle(g, 20, 20, 20, '#0d4f86'); A.kazeMark(g, 20, 20, 15, '#e8f8ff'); } });
  add({ name: 'st_eye', w: 50, h: 50, shape: 'round', age: vinyl(143, { fade: 0.7, dirt: 0.3, scratches: 0.4 }),
    draw(g) {
      A.circle(g, 25, 25, 25, '#d71920'); A.circle(g, 25, 25, 21, '#fff');
      g.fillStyle = '#d71920'; g.beginPath(); g.ellipse(25, 22, 15, 8, 0, 0, Math.PI * 2); g.fill();
      A.circle(g, 25, 22, 5.5, '#fff'); A.circle(g, 25, 22, 2.5, '#111');
      A.fitText(g, 'SEE YOU', 25, 38, 28, 6.5, { font: F.cond, weight: 700, color: '#d71920' });
    } });
  add({ name: 'st_ramenclub', w: 60, h: 40, shape: 'rounded', radius: 5, age: vinyl(144, { fade: 0.4 }),
    draw(g) {
      A.rect(g, 0, 0, 60, 40, '#ffd400'); A.circle(g, 16, 22, 11, '#c4161c');
      g.strokeStyle = '#ffd400'; g.lineWidth = 1.1; for (const dx of [-3, 0, 3]) { g.beginPath(); g.moveTo(16 + dx, 9); g.lineTo(16 + dx, 18); g.stroke(); }
      A.fitText(g, 'RAMEN', 42, 17, 30, 10, { font: F.impact, weight: 400, color: '#c4161c' });
      A.fitText(g, 'CLUB 23', 42, 30, 30, 8, { font: F.impact, weight: 400, color: '#111' });
    } });
  add({ name: 'st_circle_red', w: 34, h: 34, shape: 'round', age: vinyl(145, { fade: 0.55, dirt: 0.2 }),
    draw(g) { A.circle(g, 17, 17, 17, '#e02a2a'); A.circle(g, 17, 17, 12, '#fff'); A.fitText(g, '風', 17, 17, 16, 15, { font: F.jpMincho, weight: 700, color: '#e02a2a' }); } });
  add({ name: 'st_glitch', w: 62, h: 22, shape: 'rounded', radius: 1.5, age: vinyl(146, { fade: 0.25 }),
    draw(g) {
      A.rect(g, 0, 0, 62, 22, '#101820');
      for (let k = 0; k < 9; k++) A.rect(g, 2 + k * 6.6, 3 + ((k * 7) % 5), 4, 2, k % 2 ? '#00e5ff' : '#ff2f8e');
      A.fitText(g, 'GHOST//NET', 31, 15, 54, 8, { font: F.mono, weight: 700, color: '#e8fdff' });
    } });
  // payment / service decal on the service window post (glossy vinyl)
  add({ name: 'pay_decal', w: 96, h: 120, shape: 'rounded', radius: 5, age: vinyl(150, { fade: 0.18, rough: 0.3, dirt: 0.08, scratches: 0.3 }),
    draw(g) {
      const W = 96, H = 120;
      const gr = g.createLinearGradient(0, 0, 0, H); gr.addColorStop(0, '#0d1b33'); gr.addColorStop(1, '#14335c');
      g.fillStyle = gr; g.fillRect(0, 0, W, H);
      A.fitText(g, 'CASHLESS', W / 2, 13, 80, 11, { font: F.latin, weight: 700, color: '#fff', ls: 0.08 });
      A.fitText(g, 'キャッシュレス決済 OK', W / 2, 24, 80, 6.5, { font: F.jp, weight: 700, color: '#7fe7ff' });
      const tile = (x, y, label, icon) => {
        A.rrect(g, x, y, 40, 34, 3, '#f4f8fb');
        icon(x + 20, y + 13);
        A.fitText(g, label, x + 20, y + 29, 36, 5.2, { font: F.jp, weight: 700, color: '#0d1b33' });
      };
      tile(6, 32, 'タッチ決済', (cx, cy) => { g.strokeStyle = '#0d1b33'; g.lineWidth = 1.6; for (const r of [4, 7.5, 11]) { g.beginPath(); g.arc(cx - 6, cy, r, -0.8, 0.8); g.stroke(); } });
      tile(50, 32, 'QR コード', (cx, cy) => A.qr(g, cx - 8, cy - 8, 16, 9, '#0d1b33'));
      tile(6, 72, '生体認証', (cx, cy) => {
        g.strokeStyle = '#0d1b33'; g.lineWidth = 1.1;
        for (let r = 2; r <= 10; r += 2.2) { g.beginPath(); g.ellipse(cx, cy, r * 0.8, r, 0, Math.PI * 1.05, Math.PI * 2.95); g.stroke(); }
      });
      tile(50, 72, '電子マネー', (cx, cy) => { A.rrect(g, cx - 11, cy - 7, 22, 14, 2, '#1d6fb8'); A.rect(g, cx - 11, cy - 3, 22, 3, '#0d1b33'); });
      A.fitText(g, 'KAZE WALLET · NEOPAY · TRNS-IC', W / 2, 114, 86, 4.6, { font: F.cond, weight: 700, color: '#9fb6d6' });
    } });
  // food-business permit (plastic sleeve over a printed certificate)
  add({ name: 'permit', w: 112, h: 78, age: { seed: 151, kind: 'paper', paper: [0.97, 0.96, 0.92], rough: 0.2, absorb: 0.45, yellow: 0.25,
    fade: 0.25, dirt: 0.15, edgeDirt: 0.5, stains: 0.2, stainScale: 15, wrinkle: 0.04, scratches: 0.25 },
    draw(g) {
      const W = 112;
      g.strokeStyle = '#7a5a12'; g.lineWidth = 1.4; g.strokeRect(4, 4, W - 8, 70); g.lineWidth = 0.4; g.strokeRect(6.5, 6.5, W - 13, 65);
      A.fitText(g, '飲食店営業許可証', W / 2, 16, 76, 10, { font: F.jpMincho, weight: 700 });
      const rows = [['許可番号', '東区 第 2084-0731 号'], ['営業所', '東区三番街 第三街区 K-07'], ['屋号', '森屋 (珈琲・拉麺・義体)'], ['営業者', '森  健司'],
        ['有効期限', '2090年 5月 31日']];
      rows.forEach(([k, v], i) => {
        A.text(g, k, 12, 30 + i * 8.2, 4.6, { font: F.jp, weight: 700 });
        A.text(g, v, 36, 30 + i * 8.2, 4.6, { font: F.jp, weight: 400, maxW: 68 });
      });
      A.circle(g, W - 18, 62, 7, null, 'rgba(200,20,30,0.8)', 1);
      A.fitText(g, '東区長', W - 18, 62, 9, 3.6, { font: F.jpMincho, weight: 700, color: 'rgba(200,20,30,0.8)' });
    } });
  // staff-only plate on the door
  add({ name: 'staff_only', w: 150, h: 48, shape: 'rounded', radius: 2, age: plate(152, { fade: 0.2, scratches: 0.5, dirt: 0.15 }),
    draw(g) {
      A.rect(g, 0, 0, 150, 48, '#f4f4f2'); A.rect(g, 0, 0, 150, 24, '#c4161c');
      A.fitText(g, '関係者以外立入禁止', 75, 12.5, 132, 15, { font: F.jp, weight: 900, color: '#fff' });
      A.fitText(g, 'STAFF ONLY', 75, 37, 90, 13, { font: F.latin, weight: 700, color: '#111', ls: 0.12 });
      for (const x of [5, 145]) A.circle(g, x, 24, 1.8, '#333');
    } });
  // a hand-labelled date tag
  add({ name: 'date_tag', w: 40, h: 20, shape: 'rounded', radius: 1, age: vinyl(153, { rough: 0.7, absorb: 0.8, fade: 0.1, dirt: 0.25 }),
    draw(g) {
      A.rect(g, 0, 0, 40, 20, '#fbfbf5');
      A.hand(g, '89.6 点検', 3, 9, 6, { seed: 71, thick: 0.05 });
      A.hand(g, '森 OK', 6, 17, 5.5, { seed: 72, thick: 0.05, color: '#1f3a8a' });
    } });
  // phase colour bands for cables/conduits
  for (const [i, col] of [[0, '#c4161c'], [1, '#f4f4f4'], [2, '#1d4fa3'], [3, '#f2c200']]) {
    add({ name: `band_${i}`, w: 40, h: 10, age: vinyl(160 + i, { fade: 0.2, dirt: 0.2, scratches: 0.3 }),
      draw: (g) => A.rect(g, 0, 0, 40, 10, col) });
  }
})();
