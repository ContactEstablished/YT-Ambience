// Kitchen atlas (kitchen pass, 2026-10-09): the order terminal's screen, displays, key legends and
// stickers; the order tickets on the pass rail; masking-tape labels on tubs and bottles; packaging
// prints for the shelves; the paperwork on the kitchen's right wall (4 px/mm). Displays are 'lit'
// (emissive in Unreal, kept dim: a screen in a warm kitchen, not a sign).
(function () {
  const A = window.ART;
  const F = A.F;
  const items = (A.items = A.items || []);
  const add = (it) => items.push(Object.assign({ atlas: 'Kitchen', margin: 0 }, it));
  const lit = (seed, extra = {}) => Object.assign({ seed, kind: 'lit', paper: [0.02, 0.03, 0.05], rough: 0.08, absorb: 0.0, emissive: 1,
    yellow: 0, fade: 0, dirt: 0.06, edgeDirt: 0.3, grain: 0.004, wrinkle: 0, normalStrength: 0.15 }, extra);
  const vinyl = (seed, extra = {}) => Object.assign({ seed, kind: 'vinyl', rough: 0.42, absorb: 0.3, yellow: 0.04, fade: 0.15, dirt: 0.12,
    edgeDirt: 0.5, scratches: 0.3, wrinkle: 0.02, grain: 0.01, normalStrength: 0.6 }, extra);
  const thermal = (seed, extra = {}) => Object.assign({ seed, kind: 'paper', paper: [0.95, 0.94, 0.91], rough: 0.7, absorb: 0.2,
    yellow: 0.03, fade: 0.05, dirt: 0.05, edgeDirt: 0.12, wrinkle: 0.25, grain: 0.02, normalStrength: 0.8 }, extra);
  const tape = (seed, extra = {}) => Object.assign({ seed, kind: 'paper', paper: [0.86, 0.80, 0.62], rough: 0.75, absorb: 0.3,
    yellow: 0.08, fade: 0.05, dirt: 0.2, edgeDirt: 0.45, wrinkle: 0.12, grain: 0.03, normalStrength: 0.7 }, extra);
  const print = (seed, paper, extra = {}) => Object.assign({ seed, kind: 'paper', paper, rough: 0.8, absorb: 0.3, yellow: 0.06,
    fade: 0.2, dirt: 0.25, edgeDirt: 0.5, wrinkle: 0.1, grain: 0.03, normalStrength: 0.6 }, extra);

  // ---- the order terminal ----------------------------------------------------------------------
  // Screen: a plain order summary in the city's UI style, deep blue with muted cyan and amber. Dim.
  add({ name: 'pos_screen', w: 216, h: 156, age: lit(301, { dirt: 0.1 }),
    draw(g) {
      const W = 216, H = 156;
      A.rect(g, 0, 0, W, H, '#07111f');
      A.rect(g, 0, 0, W, 22, '#0d2a44');
      A.text(g, '注文  ORDER', 8, 15, 11, { font: F.jp, weight: 700, color: '#9fd8e8' });
      A.text(g, '#0471', W - 8, 15, 11, { font: F.latin, weight: 700, color: '#f2b544', align: 'right' });
      const rows = [['醤油ラーメン', 'SHOYU RAMEN', '1', '880'], ['替玉', 'EXTRA NOODLES', '1', '150'],
        ['味玉', 'SEASONED EGG', '1', '120'], ['コーヒー (HOT)', 'COFFEE', '1', '300']];
      rows.forEach((r, i) => {
        const y = 40 + i * 22;
        A.text(g, r[0], 10, y, 10.5, { font: F.jp, weight: 700, color: '#d8e6ee' });
        A.text(g, r[1], 10, y + 8.5, 5.5, { font: F.latin, weight: 600, color: '#5f8aa0' });
        A.text(g, '×' + r[2], 150, y, 9.5, { font: F.latin, weight: 600, color: '#9fb6c4', align: 'right' });
        A.text(g, '¥' + r[3], W - 10, y, 10, { font: F.latin, weight: 700, color: '#d8e6ee', align: 'right' });
        A.rect(g, 8, y + 12, W - 16, 0.6, '#16324a');
      });
      A.rect(g, 0, 126, W, 30, '#0b1d30');
      A.text(g, '合計 TOTAL', 10, 145, 10, { font: F.jp, weight: 700, color: '#9fd8e8' });
      A.text(g, '¥1,450', W - 10, 146, 17, { font: F.latin, weight: 700, color: '#f2b544', align: 'right' });
      // contactless prompt, bottom-centre
      g.strokeStyle = '#4fc3d9';
      g.lineWidth = 1.4;
      for (let k = 0; k < 3; k++) {
        g.beginPath();
        g.arc(96, 140, 3 + k * 3.2, -0.8, 0.8);
        g.stroke();
      }
    } });
  // Amber segment display on the keypad deck
  add({ name: 'pos_lcd', w: 56, h: 16, age: lit(302, { paper: [0.06, 0.035, 0.0], dirt: 0.12 }),
    draw(g) {
      A.rect(g, 0, 0, 56, 16, '#140a00');
      A.text(g, '¥ 1450', 52, 12.5, 11, { font: F.mono, weight: 700, color: '#ffae2e', align: 'right' });
    } });
  // Key legends (transparent between the glyphs): 3 x 4 keys at 26 mm pitch
  add({ name: 'pos_keys', w: 78, h: 104, design_alpha: true, age: vinyl(303, { rough: 0.5, fade: 0.3, dirt: 0.25 }),
    draw(g) {
      const keys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'];
      keys.forEach((k, i) => {
        const cx = 13 + (i % 3) * 26, cy = 13 + Math.floor(i / 3) * 26;
        A.fitText(g, k, cx, cy + 0.5, 10, 9, { font: F.latin, weight: 700, color: '#1b1b1b' });
      });
    } });
  add({ name: 'pos_fkeys', w: 26, h: 78, design_alpha: true, age: vinyl(304, { fade: 0.3 }),
    draw(g) {
      [['取消', '#ffffff'], ['訂正', '#1b1b1b'], ['確定', '#ffffff']].forEach(([t, c], i) =>
        A.fitText(g, t, 13, 13 + i * 26, 15, 7, { font: F.jp, weight: 900, color: c }));
    } });
  // Contactless pad: glossy black plate, the waves mark, TAP
  add({ name: 'pos_tap', w: 64, h: 52, shape: 'rounded', radius: 4, age: vinyl(305, { rough: 0.18, dirt: 0.05, scratches: 0.6 }),
    draw(g) {
      A.rect(g, 0, 0, 64, 52, '#0c0c0e');
      g.strokeStyle = '#e8e8e8';
      g.lineWidth = 2.2;
      g.lineCap = 'round';
      for (let k = 0; k < 4; k++) {
        g.beginPath();
        g.arc(9, 24, 3 + k * 3.6, -0.85, 0.85);
        g.stroke();
      }
      A.fitText(g, 'タッチ', 44, 21, 30, 8.5, { font: F.jp, weight: 900, color: '#e8e8e8' });
      A.fitText(g, 'TAP', 44, 33, 22, 7.5, { font: F.latin, weight: 700, color: '#e8e8e8' });
      A.fitText(g, 'IC・QR・ID', 32, 46, 50, 5, { font: F.latin, weight: 700, color: '#8a8a8a' });
    } });
  // The maintenance sticker the brief asks for (side of the screen pod)
  add({ name: 'pos_service', w: 42, h: 27, shape: 'rounded', radius: 2, age: vinyl(306, { fade: 0.35, dirt: 0.3 }),
    draw(g) {
      A.rect(g, 0, 0, 42, 27, '#f2c200');
      A.rect(g, 0, 0, 42, 8, '#151515');
      A.fitText(g, '点検済  SERVICED', 21, 4.4, 38, 5, { font: F.jp, weight: 900, color: '#f2c200' });
      A.text(g, 'NEXA POS-7', 3, 14, 5, { font: F.latin, weight: 700, color: '#151515' });
      A.text(g, '2089.06.14', 3, 20, 4.4, { font: F.mono, weight: 700, color: '#151515' });
      A.hand(g, 'OK  ムラタ', 3, 25.5, 4.4, { seed: 31, color: '#1d3f8a', font: F.hand2 });
      A.circle(g, 35, 18, 5, null, '#151515', 0.6);
      A.fitText(g, '次回', 35, 16.5, 7, 2.6, { font: F.jp, weight: 900, color: '#151515' });
      A.fitText(g, '12月', 35, 20.5, 7, 2.8, { font: F.jp, weight: 900, color: '#c4161c' });
    } });
  add({ name: 'pos_asset', w: 40, h: 14, shape: 'rounded', radius: 1.2, age: Object.assign(vinyl(307), { kind: 'metal', paper: [0.66, 0.67, 0.67],
    rough: 0.32, metal: 1, scratches: 0.8 }),
    draw(g) {
      A.rect(g, 0, 0, 40, 14, '#a9abab');
      A.text(g, 'ASSET K07-114', 2.5, 5.5, 3.6, { font: F.latin, weight: 700, color: '#222' });
      A.barcode(g, 2.5, 7, 35, 5, 77, '#222');
    } });
  add({ name: 'pos_nocash', w: 48, h: 18, shape: 'rounded', radius: 2, age: vinyl(308, { fade: 0.45, dirt: 0.25 }),
    draw(g) {
      A.rect(g, 0, 0, 48, 18, '#c4161c');
      A.fitText(g, '現金不可', 24, 8, 42, 8.5, { font: F.jp, weight: 900, color: '#fff' });
      A.fitText(g, 'CARD / IC ONLY', 24, 15, 36, 4, { font: F.latin, weight: 700, color: '#fff' });
    } });
  add({ name: 'pos_brand', w: 54, h: 9, design_alpha: true, age: vinyl(309, { fade: 0.2 }),
    draw(g) { A.fitText(g, 'NEXA · POS 7', 27, 4.8, 52, 7, { font: F.latin, weight: 700, color: '#c9c4b8', ls: 0.12 }); } });
  // under-counter fridge and coffee-brewer displays
  add({ name: 'fridge_display', w: 40, h: 14, age: lit(310, { paper: [0.0, 0.03, 0.01] }),
    draw(g) {
      A.rect(g, 0, 0, 40, 14, '#010702');
      A.text(g, '3.2°C', 36, 11, 10, { font: F.mono, weight: 700, color: '#46e07a', align: 'right' });
      A.circle(g, 5, 7, 1.4, '#46e07a');
    } });
  add({ name: 'brewer_panel', w: 70, h: 30, age: lit(311, { paper: [0.0, 0.02, 0.01], dirt: 0.15 }),
    draw(g) {
      A.rect(g, 0, 0, 70, 30, '#020604');
      A.text(g, 'BREW', 5, 12, 8, { font: F.latin, weight: 700, color: '#3fcf70' });
      A.text(g, '03:20', 65, 13, 11, { font: F.mono, weight: 700, color: '#3fcf70', align: 'right' });
      A.rect(g, 5, 19, 60, 0.6, '#123d22');
      A.text(g, 'HOLD 92°C', 5, 26.5, 6, { font: F.mono, weight: 700, color: '#2a8f4f' });
    } });

  // ---- order tickets (thermal paper) on the pass rail ------------------------------------------
  // torn off the printer roll along the top edge
  const TEAR_TOP = (i) => [{ a: [-0.05, 0.02], b: [1.05, 0.02], jag: 0.8, scale: 2.2, seed: 11 + i }];
  const ORDERS = [
    ['0468', '22:41', [['醤油', 1], ['味玉', 1]]],
    ['0469', '22:44', [['味噌', 2], ['替玉', 1]]],
    ['0470', '22:47', [['コーヒー', 1]]],
    ['0471', '22:52', [['醤油', 1], ['替玉', 1], ['コーヒー', 1]]],
    ['0466', '22:30', [['塩', 1], ['ネギ多め', 1]]],
    ['0472', '22:58', [['味噌', 1], ['チャーシュー', 1]]],
  ];
  ORDERS.forEach(([no, t, lines], i) => add({ name: `ticket_${i}`, w: 58, h: 84,
    age: thermal(320 + i, { dirt: 0.08 + 0.04 * i, wrinkle: 0.2 + 0.05 * (i % 3), tears: TEAR_TOP(i) }),
    draw(g) {
      A.fitText(g, 'K-07  ラーメン・コーヒー', 29, 8, 50, 4.6, { font: F.jp, weight: 700, color: '#3a3a3a' });
      A.rect(g, 4, 11, 50, 0.4, '#555');
      A.fitText(g, '#' + no, 25, 21, 38, 10, { font: F.latin, weight: 700, color: '#222' });
      A.text(g, t, 54, 31.5, 5, { font: F.mono, weight: 700, color: '#444', align: 'right' });
      lines.forEach(([n, q], k) => {
        A.text(g, n, 6, 42 + k * 9, 7, { font: F.jp, weight: 700, color: '#2a2a2a', maxW: 36 });
        A.text(g, '×' + q, 52, 42 + k * 9, 7, { font: F.latin, weight: 700, color: '#2a2a2a', align: 'right' });
      });
      A.rect(g, 4, 72, 50, 0.4, '#555');
      if (i % 2 === 0) A.hand(g, i === 0 ? '済' : 'カタメ', 34, 81, 8, { seed: 40 + i, color: '#b0151b', font: F.hand2 });
    } }));
  // the backs glow faintly: thin thermal paper with the prep light behind it
  add({ name: 'ticket_back', w: 58, h: 84, age: thermal(330, { dirt: 0.1, tears: TEAR_TOP(0), emissive: 0.1 }),
    draw(g) {
      // the print shows through faintly, mirrored
      g.save();
      g.translate(58, 0);
      g.scale(-1, 1);
      A.fitText(g, '#0471', 29, 22, 46, 12, { font: F.latin, weight: 700, color: 'rgba(60,60,60,0.10)' });
      for (let k = 0; k < 3; k++) A.rect(g, 6, 38 + k * 9, 40, 3, 'rgba(60,60,60,0.06)');
      g.restore();
    } });

  // ---- masking-tape labels ---------------------------------------------------------------------
  [['tape_shoyu', '醤油ダレ'], ['tape_miso', '味噌'], ['tape_negi', 'ネギ'], ['tape_chashu', 'チャーシュー'], ['tape_menma', 'メンマ'],
    ['tape_beans', '豆 深煎'], ['tape_sugar', '砂糖'], ['tape_date', '10/8 PM'], ['tape_shio', '塩ダレ'], ['tape_hot', 'HOT']]
    .forEach(([name, txt], i) => add({ name, w: 46, h: 14, age: tape(340 + i, { tears: [{ a: [0.035, -0.1], b: [0.035, 1.1], jag: 0.9, scale: 1.5, seed: i },
      { a: [0.965, -0.1], b: [0.965, 1.1], jag: 0.9, scale: 1.5, seed: i + 7 }] }),
      draw(g) { A.hand(g, txt, 4, 10.5, txt.length > 4 ? 6.2 : 8, { seed: 50 + i, color: '#141414', font: F.hand2 }); } }));

  // ---- packaging prints (shelf stock) -----------------------------------------------------------
  add({ name: 'box_noodle', s: 1.5, w: 250, h: 170, age: print(350, [0.30, 0.42, 0.56]),
    draw(g) {
      A.rect(g, 0, 0, 250, 170, '#4b6a8c');
      A.rect(g, 0, 118, 250, 52, '#e9e3d2');
      A.fitText(g, '生中華麺', 92, 52, 160, 50, { font: F.jpMincho, weight: 700, color: '#f3efe4' });
      A.fitText(g, '中太ちぢれ', 92, 92, 120, 20, { font: F.jp, weight: 900, color: '#f3efe4' });
      A.circle(g, 205, 62, 30, '#c8141c');
      A.fitText(g, '5kg', 205, 64, 40, 20, { font: F.latin, weight: 700, color: '#fff' });
      A.fitText(g, 'FRESH RAMEN NOODLES  ·  KEEP 0–10°C', 125, 140, 230, 12, { font: F.latin, weight: 700, color: '#30455c' });
      A.fitText(g, '製造  ミナト製麺所  ·  K-07 宛', 125, 158, 210, 9, { font: F.jp, weight: 700, color: '#30455c' });
    } });
  add({ name: 'box_cups', s: 1.5, w: 250, h: 170, age: print(351, [0.58, 0.44, 0.28], { fade: 0.1 }),
    draw(g) {
      A.rect(g, 0, 0, 250, 170, '#9a7650');
      A.fitText(g, 'PAPER CUP', 125, 58, 200, 36, { font: F.latin, weight: 700, color: '#1d1a17' });
      A.fitText(g, '12oz  ×  1000', 125, 96, 160, 22, { font: F.latin, weight: 700, color: '#1d1a17' });
      A.fitText(g, '紙コップ  ホット用', 125, 130, 180, 18, { font: F.jp, weight: 900, color: '#1d1a17' });
      g.strokeStyle = '#1d1a17';
      g.lineWidth = 2;
      g.strokeRect(12, 12, 226, 146);
    } });
  add({ name: 'bag_beans', s: 2.5, w: 96, h: 120, shape: 'rounded', radius: 3, age: print(352, [0.08, 0.08, 0.08], { rough: 0.5, dirt: 0.15 }),
    draw(g) {
      A.rect(g, 0, 0, 96, 120, '#141414');
      A.kazeMark(g, 48, 34, 18, '#d8c69a');
      A.fitText(g, 'KAZE ROAST', 48, 68, 80, 12, { font: F.latin, weight: 700, color: '#d8c69a', ls: 0.08 });
      A.fitText(g, '深煎り ブレンド', 48, 86, 76, 10, { font: F.jp, weight: 900, color: '#d8c69a' });
      A.fitText(g, '1kg  ·  BEANS', 48, 104, 60, 7, { font: F.latin, weight: 700, color: '#8b7f62' });
    } });
  add({ name: 'label_tare', s: 3, w: 60, h: 80, shape: 'rounded', radius: 2, age: print(353, [0.92, 0.88, 0.78], { dirt: 0.35 }),
    draw(g) {
      A.rect(g, 0, 0, 60, 80, '#efe6d2');
      A.rect(g, 0, 0, 60, 18, '#7a1d14');
      A.fitText(g, '業務用', 30, 10, 50, 10, { font: F.jp, weight: 900, color: '#efe6d2' });
      A.vtext(g, '濃口醤油', 30, 24, 11, { font: F.jpMincho, weight: 700, color: '#2a1610' });
    } });

  // ---- paperwork on the kitchen's right wall ---------------------------------------------------
  add({ name: 'calendar', s: 2, w: 170, h: 250, age: print(360, [0.93, 0.91, 0.86], { wrinkle: 0.25, dirt: 0.3, stains: 0.3, stainBias: 'bottom' }),
    draw(g) {
      A.rect(g, 0, 0, 170, 120, '#2c4f6e');
      A.fitText(g, 'ミナト製麺所', 85, 30, 140, 16, { font: F.jp, weight: 900, color: '#f2efe6' });
      A.fitText(g, '2089', 85, 74, 120, 34, { font: F.latin, weight: 700, color: '#f2c200' });
      A.fitText(g, '10  OCTOBER', 85, 108, 120, 14, { font: F.latin, weight: 700, color: '#f2efe6', ls: 0.1 });
      const days = '日月火水木金土';
      for (let c = 0; c < 7; c++) A.fitText(g, days[c], 14 + c * 23.5, 134, 12, 9, { font: F.jp, weight: 900, color: c === 0 ? '#c4161c' : '#333' });
      for (let d = 1; d <= 31; d++) {
        const k = d + 2, c = k % 7, r = Math.floor(k / 7);
        const x = 14 + c * 23.5, y = 156 + r * 19;
        A.fitText(g, String(d), x, y, 14, 10, { font: F.latin, weight: 700, color: c === 0 ? '#c4161c' : '#333' });
        if (d < 9) { g.strokeStyle = 'rgba(30,30,30,0.75)'; g.lineWidth = 1.3; g.beginPath(); g.moveTo(x - 7, y - 6); g.lineTo(x + 7, y + 6); g.stroke(); }
      }
      A.hand(g, '業者', 86, 186, 7, { seed: 61, color: '#b0151b', font: F.hand2 });
    } });
  add({ name: 'temp_log', s: 2, w: 150, h: 210, age: print(361, [0.94, 0.93, 0.89], { wrinkle: 0.3, dirt: 0.35, stains: 0.45, stainBias: 'bottom' }),
    draw(g) {
      A.fitText(g, '温度記録表  TEMP LOG', 75, 14, 130, 10, { font: F.jp, weight: 900, color: '#222' });
      g.strokeStyle = '#555';
      g.lineWidth = 0.6;
      for (let r = 0; r <= 14; r++) { g.beginPath(); g.moveTo(8, 24 + r * 12); g.lineTo(142, 24 + r * 12); g.stroke(); }
      for (const x of [8, 34, 70, 106, 142]) { g.beginPath(); g.moveTo(x, 24); g.lineTo(x, 192); g.stroke(); }
      ['日付', '冷蔵', 'スープ', 'サイン'].forEach((t, c) => A.fitText(g, t, [21, 52, 88, 124][c], 32, 30, 7, { font: F.jp, weight: 900, color: '#333' }));
      for (let r = 1; r < 9; r++) {
        const y = 33 + r * 12;
        A.hand(g, `10/${r}`, 11, y, 7, { seed: 70 + r, color: '#1d3f8a', font: F.hand2 });
        A.hand(g, `${(2.6 + (r % 4) * 0.3).toFixed(1)}`, 40, y, 7, { seed: 80 + r, color: '#1d3f8a', font: F.hand2 });
        A.hand(g, `${86 + (r % 3)}`, 78, y, 7, { seed: 90 + r, color: '#1d3f8a', font: F.hand2 });
        A.hand(g, r % 3 ? 'ム' : 'K', 118, y, 7, { seed: 100 + r, color: '#1d3f8a', font: F.hand2 });
      }
    } });
  add({ name: 'k_menu', s: 2.5, w: 120, h: 160, shape: 'rounded', radius: 4, age: Object.assign(print(362, [0.95, 0.93, 0.88]),
    { kind: 'plastic', rough: 0.2, scratches: 0.4 }),
    draw(g) {
      A.rect(g, 0, 0, 120, 160, '#f4efe2');
      A.rect(g, 0, 0, 120, 26, '#8c1a12');
      A.fitText(g, '本日のおすすめ', 60, 14, 104, 12, { font: F.jp, weight: 900, color: '#f4efe2' });
      [['醤油ラーメン', '880'], ['味噌ラーメン', '950'], ['塩ラーメン', '900'], ['替玉', '150'], ['味玉', '120'], ['コーヒー', '300']]
        .forEach(([n, p], i) => {
          A.text(g, n, 8, 46 + i * 18, 10, { font: F.jp, weight: 700, color: '#2a1d16' });
          A.text(g, p, 112, 46 + i * 18, 10, { font: F.latin, weight: 700, color: '#8c1a12', align: 'right' });
        });
    } });
  add({ name: 'hood_note', s: 3, w: 66, h: 44, shape: 'rounded', radius: 2, age: vinyl(363, { dirt: 0.55, fade: 0.3 }),
    draw(g) {
      A.rect(g, 0, 0, 66, 44, '#f7f5ef');
      A.rect(g, 0, 0, 66, 14, '#1d4fa3');
      A.fitText(g, 'フィルター清掃', 33, 7.5, 60, 9, { font: F.jp, weight: 900, color: '#fff' });
      A.fitText(g, '毎週 月曜', 33, 27, 50, 12, { font: F.jp, weight: 900, color: '#222' });
      A.fitText(g, 'CLEAN FILTERS MONDAYS', 33, 39, 58, 5, { font: F.latin, weight: 700, color: '#1d4fa3' });
    } });
})();
