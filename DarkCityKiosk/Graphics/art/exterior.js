// Exterior atlas (exterior pass, 2026-10-09, prompt 8): the marks on the ground props round the kiosk:
// supplier stamps on the delivery crates, the bottle crate's moulded logo, a delivery note and tape on
// the tote, the bins' signs, the gas cylinders' labels and inspection tag, the cage's no-fire plate, the
// utility cabinet's warning and record card, stencils on the locker and the steel case, the noodle
// cartons' print, tape remnants (4 px/mm; the cartons 2). Kept small and quiet: subordinate to the
// kiosk's signage.
(function () {
  const A = window.ART;
  const F = A.F;
  const items = (A.items = A.items || []);
  const add = (it) => items.push(Object.assign({ atlas: 'Exterior', margin: 0 }, it));
  const vinyl = (seed, extra = {}) => Object.assign({ seed, kind: 'vinyl', rough: 0.45, absorb: 0.35, yellow: 0.04, fade: 0.3, dirt: 0.18,
    edgeDirt: 0.5, scratches: 0.35, wrinkle: 0.02, grain: 0.01, normalStrength: 0.6 }, extra);
  // ink printed straight onto moulded plastic: the plastic shows through between the strokes
  const ink = (seed, extra = {}) => Object.assign({ seed, kind: 'vinyl', rough: 0.55, absorb: 0.2, yellow: 0.0, fade: 0.45, dirt: 0.2,
    edgeDirt: 0.0, scratches: 0.6, wrinkle: 0.0, grain: 0.02, normalStrength: 0.3 }, extra);
  const paper = (seed, extra = {}) => Object.assign({ seed, kind: 'paper', paper: [0.93, 0.92, 0.88], rough: 0.8, absorb: 0.6, yellow: 0.1,
    fade: 0.15, dirt: 0.25, edgeDirt: 0.5, wrinkle: 0.2, grain: 0.03, normalStrength: 0.8 }, extra);
  const tape = (seed, extra = {}) => Object.assign({ seed, kind: 'paper', paper: [0.86, 0.80, 0.62], rough: 0.75, absorb: 0.3,
    yellow: 0.08, fade: 0.05, dirt: 0.3, edgeDirt: 0.55, wrinkle: 0.12, grain: 0.03, normalStrength: 0.7 }, extra);
  const kraft = (seed, extra = {}) => Object.assign({ seed, kind: 'paper', paper: [0.55, 0.40, 0.25], rough: 0.85, absorb: 0.7, yellow: 0.0,
    fade: 0.1, dirt: 0.15, edgeDirt: 0.45, wrinkle: 0.05, grain: 0.05, normalStrength: 0.7 }, extra);

  // ---- delivery crates -------------------------------------------------------------------------
  // hot-stamped supplier marks on the crates' label panels (white ink, half worn off)
  add({ name: 'x_crate_marusan', w: 150, h: 46, design_alpha: true, age: ink(801),
    draw(g) {
      A.fitText(g, '丸三青果', 52, 19, 96, 22, { font: F.jp, weight: 900, color: '#e9e6dc' });
      A.fitText(g, 'MARUSAN PRODUCE', 52, 38, 96, 8, { font: F.latin, weight: 700, color: '#e9e6dc', ls: 0.1 });
      A.circle(g, 126, 23, 18, null, '#e9e6dc', 2.2);
      A.fitText(g, '返却', 126, 21, 24, 11, { font: F.jp, weight: 900, color: '#e9e6dc' });
      A.fitText(g, 'RETURN', 126, 31, 22, 4.4, { font: F.latin, weight: 700, color: '#e9e6dc' });
    } });
  add({ name: 'x_crate_kaze', w: 140, h: 40, design_alpha: true, age: ink(802, { fade: 0.55 }),
    draw(g) {
      A.kazeMark(g, 20, 20, 15, '#e9e6dc');
      A.fitText(g, 'KAZE 物流', 85, 17, 100, 17, { font: F.jp, weight: 900, color: '#e9e6dc' });
      A.fitText(g, '持出禁止  NOT FOR SALE', 85, 33, 100, 6.5, { font: F.jp, weight: 700, color: '#e9e6dc' });
    } });
  // delivery slip in the crate's card slot (thermal, a bit damp)
  add({ name: 'x_crate_slip', w: 86, h: 58, age: paper(803, { paper: [0.95, 0.94, 0.91], stains: 0.4, stainBias: 'bottom', dirt: 0.3 }),
    draw(g) {
      A.text(g, '納品書  DELIVERY', 4, 9, 6.5, { font: F.jp, weight: 900 });
      A.rect(g, 4, 11.5, 78, 0.5, '#222');
      A.text(g, '屋台 K-07 様', 4, 20, 6, { font: F.jp, weight: 700 });
      A.text(g, 'キャベツ  ×6', 4, 29, 5.2, { font: F.jp, weight: 700 });
      A.text(g, '長ネギ  ×2束', 4, 36, 5.2, { font: F.jp, weight: 700 });
      A.text(g, '2089.10.09  05:40', 4, 44, 4.6, { font: F.mono, weight: 700 });
      A.barcode(g, 4, 47, 50, 7, 813, '#222');
      A.hand(g, '済', 66, 50, 12, { seed: 7, color: '#b3261e' });
    } });

  // ---- the lidded tote: masking-tape label and a delivery note taped to the lid -------------------
  add({ name: 'x_tote_tape', w: 120, h: 26, age: tape(811, { tears: [{ a: [0.97, -0.1], b: [0.99, 1.1], jag: 1.2, scale: 2.5, seed: 3 }] }),
    draw(g) { A.hand(g, '紙コップ 8oz ×1000', 6, 18, 12, { seed: 811, color: '#151515', font: F.hand2 }); } });
  add({ name: 'x_tote_note', w: 74, h: 52, age: paper(812, { wrinkle: 0.35, stains: 0.3, stainBias: 'edges',
    tape: [{ x: 0.5, y: 0.04, w: 40, h: 9, rot: 0.03, clear: true }] }),
    draw(g) {
      A.hand(g, 'ムラタさんへ', 5, 15, 8, { seed: 21, color: '#1d3f8a', font: F.hand2 });
      A.hand(g, 'フタ・ストロー', 5, 27, 7.5, { seed: 22, color: '#1d3f8a', font: F.hand2 });
      A.hand(g, '月曜に追加', 5, 38, 7.5, { seed: 23, color: '#1d3f8a', font: F.hand2 });
      A.hand(g, '— 佐伯', 40, 48, 6, { seed: 24, color: '#1d3f8a', font: F.hand2 });
    } });

  // ---- bottle crate: the moulded logo panel's print, a return tag ---------------------------------
  add({ name: 'x_bottle_logo', w: 150, h: 54, design_alpha: true, age: ink(821, { fade: 0.35 }),
    draw(g) {
      A.fitText(g, 'MIRAI', 52, 26, 92, 26, { font: F.impact, weight: 400, color: '#f3efe6', ls: 0.04 });
      A.fitText(g, 'ラムネ・ソーダ', 52, 44, 92, 10, { font: F.jp, weight: 900, color: '#f3efe6' });
      A.rrect(g, 106, 8, 38, 38, 4, null, '#f3efe6', 2);
      A.fitText(g, '瓶', 125, 26, 26, 20, { font: F.jp, weight: 900, color: '#f3efe6' });
      A.fitText(g, '20本', 125, 41, 24, 7, { font: F.jp, weight: 900, color: '#f3efe6' });
    } });
  add({ name: 'x_bottle_tag', w: 40, h: 60, age: paper(822, { paper: [0.95, 0.83, 0.25], stains: 0.5, stainBias: 'bottom', holes: [[0.5, 0.1, 2.2]] }),
    draw(g) {
      A.fitText(g, '空瓶', 20, 20, 30, 11, { font: F.jp, weight: 900 });
      A.fitText(g, 'EMPTIES', 20, 30, 30, 5.5, { font: F.latin, weight: 700 });
      A.hand(g, '14', 9, 50, 14, { seed: 41, color: '#151515', font: F.hand2 });
    } });

  // ---- bins ------------------------------------------------------------------------------------------
  add({ name: 'x_bin_burnable', w: 150, h: 96, shape: 'rounded', radius: 5, age: vinyl(831, { fade: 0.4, dirt: 0.28, scratches: 0.5 }),
    draw(g) {
      A.rect(g, 0, 0, 150, 96, '#f4f1e8');
      A.rect(g, 0, 0, 150, 30, '#c4161c');
      A.fitText(g, '燃えるゴミ', 75, 16, 132, 21, { font: F.jp, weight: 900, color: '#fff' });
      A.fitText(g, 'BURNABLE', 75, 50, 120, 17, { font: F.latin, weight: 700, color: '#1b1b1b', ls: 0.06 });
      A.fitText(g, '紙コップ・割り箸・紙ナプキン', 75, 70, 132, 9, { font: F.jp, weight: 700, color: '#333' });
      A.fitText(g, 'CUPS · CHOPSTICKS · NAPKINS', 75, 84, 120, 6, { font: F.latin, weight: 700, color: '#555' });
    } });
  add({ name: 'x_bin_cans', w: 120, h: 84, shape: 'rounded', radius: 5, age: vinyl(832, { fade: 0.35, dirt: 0.3, scratches: 0.55 }),
    draw(g) {
      A.rect(g, 0, 0, 120, 84, '#f4f1e8');
      A.rect(g, 0, 0, 120, 30, '#1f5aa6');
      A.fitText(g, 'カン・ビン', 60, 16, 106, 20, { font: F.jp, weight: 900, color: '#fff' });
      A.fitText(g, 'CANS · BOTTLES', 60, 50, 106, 13, { font: F.latin, weight: 700, color: '#1b1b1b' });
      A.fitText(g, '中身を空にしてください', 60, 70, 106, 8.5, { font: F.jp, weight: 700, color: '#333' });
    } });
  // an older sticker scraped half off the burnable bin's side
  add({ name: 'x_bin_scraped', w: 70, h: 50, shape: 'rounded', radius: 3, age: vinyl(833, { fade: 0.7, dirt: 0.4, scratches: 0.8,
    tears: [{ a: [0.62, -0.1], b: [0.30, 1.1], jag: 4, scale: 6, seed: 9 }, { a: [-0.1, 0.25], b: [0.4, -0.1], jag: 2, scale: 4, seed: 13 }] }),
    draw(g) {
      A.rect(g, 0, 0, 70, 50, '#e8e2d0');
      A.rect(g, 0, 0, 70, 14, '#2a7a3b');
      A.fitText(g, '分別にご協力を', 35, 8, 64, 9, { font: F.jp, weight: 900, color: '#fff' });
      A.fitText(g, '回収 月・木', 35, 30, 60, 10, { font: F.jp, weight: 900, color: '#1b1b1b' });
      A.fitText(g, 'PICKUP MON · THU', 35, 43, 60, 6, { font: F.latin, weight: 700, color: '#444' });
    } });

  // ---- gas cylinders and their cage -------------------------------------------------------------------
  add({ name: 'x_lpg_label', w: 110, h: 70, shape: 'rounded', radius: 3, age: vinyl(841, { fade: 0.45, dirt: 0.35, scratches: 0.6 }),
    draw(g) {
      A.rect(g, 0, 0, 110, 70, '#f2c200');
      A.fitText(g, 'LPガス', 55, 20, 96, 20, { font: F.jp, weight: 900, color: '#151515' });
      A.fitText(g, '液化石油ガス  10kg', 55, 38, 96, 9, { font: F.jp, weight: 900, color: '#151515' });
      A.rect(g, 6, 45, 98, 0.8, '#151515');
      A.fitText(g, 'KAZE ENERGY  容器 No. 47-3318', 55, 55, 98, 6, { font: F.latin, weight: 700, color: '#151515' });
      A.fitText(g, '火気厳禁', 55, 65, 60, 6.5, { font: F.jp, weight: 900, color: '#c4161c' });
    } });
  add({ name: 'x_lpg_tag', w: 46, h: 72, age: paper(842, { paper: [0.94, 0.94, 0.90], stains: 0.45, stainBias: 'bottom', holes: [[0.5, 0.07, 2.4]],
    wrinkle: 0.3 }),
    draw(g) {
      A.rect(g, 0, 10, 46, 12, '#1f5aa6');
      A.fitText(g, '充填済', 23, 16.5, 40, 8.5, { font: F.jp, weight: 900, color: '#fff' });
      A.fitText(g, 'FILLED', 23, 30, 36, 6.5, { font: F.latin, weight: 700 });
      A.text(g, '2089.10.02', 4, 42, 5.5, { font: F.mono, weight: 700 });
      A.text(g, '検査 2091.03', 4, 51, 5.5, { font: F.jp, weight: 700 });
      A.hand(g, 'ヤマダ', 6, 66, 9, { seed: 51, color: '#151515', font: F.hand2 });
    } });
  add({ name: 'x_no_fire', w: 150, h: 64, shape: 'rounded', radius: 3, age: Object.assign(vinyl(843, { fade: 0.3, dirt: 0.3 }), { kind: 'metal',
    paper: [0.85, 0.85, 0.83], rough: 0.4, metal: 0.4, rust: 0.3, scratches: 0.6 }),
    draw(g) {
      A.rect(g, 0, 0, 150, 64, '#f4f1e8');
      A.rect(g, 3, 3, 144, 38, '#c4161c');
      A.fitText(g, '火気厳禁', 75, 22, 130, 28, { font: F.jp, weight: 900, color: '#fff', ls: 0.08 });
      A.fitText(g, 'NO OPEN FLAMES  ·  LP GAS', 75, 53, 130, 9, { font: F.latin, weight: 700, color: '#151515' });
    } });

  // ---- utility cabinet: shock warning, the circuit card in a sleeve, the owner's label -----------------
  add({ name: 'x_cab_warn', w: 70, h: 92, shape: 'rounded', radius: 3, age: vinyl(851, { fade: 0.35, dirt: 0.3 }),
    draw(g) {
      A.rect(g, 0, 0, 70, 92, '#f7f5ef');
      A.rect(g, 0, 0, 70, 58, '#f2c200');
      A.hazard(g, 35, 33, 52, 'bolt');
      A.fitText(g, '高電圧', 35, 72, 60, 13, { font: F.jp, weight: 900 });
      A.fitText(g, 'HIGH VOLTAGE', 35, 86, 58, 6.5, { font: F.latin, weight: 700, color: '#c4161c' });
    } });
  add({ name: 'x_cab_card', w: 64, h: 90, age: paper(852, { paper: [0.92, 0.92, 0.88], stains: 0.35, stainBias: 'bottom',
    tape: [{ x: 0.5, y: 0.02, w: 44, h: 8, rot: -0.04, clear: true }, { x: 0.5, y: 0.98, w: 40, h: 8, rot: 0.05, clear: true }] }),
    draw(g) {
      A.text(g, '点検記録', 4, 11, 7.5, { font: F.jp, weight: 900 });
      A.text(g, 'INSPECTION', 40, 11, 4.2, { font: F.latin, weight: 700, maxW: 21 });
      for (let i = 0; i < 7; i++) {
        const y = 20 + i * 9.5;
        A.rect(g, 4, y, 56, 0.4, '#444');
        if (i < 5) {
          A.text(g, `2089.0${3 + i}.1${i}`, 5, y + 7, 4.4, { font: F.mono, weight: 700 });
          A.hand(g, i === 3 ? '漏電なし' : 'OK', 38, y + 7.4, 5.5, { seed: 60 + i, color: '#1d3f8a', font: F.hand2 });
        }
      }
    } });
  add({ name: 'x_cab_owner', w: 64, h: 22, shape: 'rounded', radius: 1.5, age: Object.assign(vinyl(853), { kind: 'metal', paper: [0.66, 0.67, 0.67],
    rough: 0.32, metal: 1, scratches: 0.8, rust: 0.2 }),
    draw(g) {
      A.rect(g, 0, 0, 64, 22, '#a9abab');
      A.text(g, '屋台 K-07  電源盤', 3, 9, 6, { font: F.jp, weight: 900, color: '#222' });
      A.text(g, 'SUPPLY 100V 30A', 3, 17.5, 5, { font: F.latin, weight: 700, color: '#222' });
    } });

  // ---- locker and steel case: stencils (paint, transparent between the strokes) -----------------------
  add({ name: 'x_locker_stencil', w: 220, h: 70, design_alpha: true, age: ink(861, { fade: 0.3, scratches: 0.8, dirt: 0.3 }),
    draw(g) {
      A.fitText(g, 'K-07', 62, 30, 110, 44, { font: F.impact, weight: 400, color: '#d9d4c4', ls: 0.06 });
      A.fitText(g, '在庫  STOCK', 170, 26, 90, 16, { font: F.jp, weight: 900, color: '#d9d4c4' });
      A.fitText(g, '施錠厳守', 170, 50, 80, 12, { font: F.jp, weight: 900, color: '#d9d4c4' });
      // stencil bridges: thin gaps through the letters
      g.globalCompositeOperation = 'destination-out';
      for (let x = 14; x < 220; x += 23) A.rect(g, x, 0, 2, 70, '#000');
      g.globalCompositeOperation = 'source-over';
    } });
  add({ name: 'x_case_stencil', w: 120, h: 40, design_alpha: true, age: ink(862, { fade: 0.5, scratches: 0.9, dirt: 0.35 }),
    draw(g) {
      A.fitText(g, '工具  TOOLS', 60, 17, 112, 18, { font: F.jp, weight: 900, color: '#e3dcc6' });
      A.fitText(g, 'No.3', 60, 34, 40, 10, { font: F.latin, weight: 700, color: '#e3dcc6' });
    } });
  add({ name: 'x_crate_wood', w: 170, h: 60, design_alpha: true, age: ink(863, { fade: 0.6, scratches: 0.5, dirt: 0.4 }),
    draw(g) {
      A.fitText(g, '天地無用', 60, 28, 100, 26, { font: F.jp, weight: 900, color: '#1b1612' });
      A.fitText(g, 'THIS SIDE UP', 60, 50, 100, 11, { font: F.latin, weight: 700, color: '#1b1612' });
      g.fillStyle = '#1b1612';
      for (const x of [140, 158]) {
        g.beginPath();
        g.moveTo(x, 8); g.lineTo(x + 8, 22); g.lineTo(x + 3, 22); g.lineTo(x + 3, 50); g.lineTo(x - 3, 50); g.lineTo(x - 3, 22); g.lineTo(x - 8, 22);
        g.closePath();
        g.fill();
      }
    } });

  // ---- noodle cartons (2 px/mm): the long side's print -----------------------------------------------
  add({ name: 'x_carton_noodle', w: 290, h: 140, s: 2, age: kraft(871, { dirt: 0.2, edgeDirt: 0.6 }),
    draw(g) {
      A.rect(g, 0, 0, 290, 140, '#8c6a43');
      A.rect(g, 0, 18, 290, 4, '#7a2018');
      A.fitText(g, '生中華麺', 110, 66, 190, 52, { font: F.jp, weight: 900, color: '#7a2018' });
      A.fitText(g, '朝日製麺所  ASAHI NOODLE WORKS', 110, 98, 190, 13, { font: F.jp, weight: 700, color: '#2a1d12' });
      A.fitText(g, '20食入  要冷蔵 10°C以下', 110, 122, 190, 12, { font: F.jp, weight: 700, color: '#2a1d12' });
      A.circle(g, 250, 70, 32, null, '#7a2018', 3);
      A.fitText(g, '麺', 250, 72, 40, 38, { font: F.jp, weight: 900, color: '#7a2018' });
    } });
  add({ name: 'x_carton_cups', w: 260, h: 120, s: 2, age: kraft(872, { dirt: 0.25, edgeDirt: 0.6, paper: [0.62, 0.48, 0.32] }),
    draw(g) {
      A.rect(g, 0, 0, 260, 120, '#9a7a53');
      A.fitText(g, 'PAPER CUP 8oz', 120, 50, 200, 30, { font: F.latin, weight: 700, color: '#1d3557' });
      A.fitText(g, '1000個入  KAZE PACK', 120, 86, 200, 16, { font: F.jp, weight: 700, color: '#1d3557' });
      A.barcode(g, 210, 92, 40, 18, 872, '#1d3557');
    } });
  // packing tape remnant, clear-ish tan
  add({ name: 'x_tape_strip', w: 120, h: 48, age: tape(881, { paper: [0.72, 0.58, 0.36], rough: 0.35, absorb: 0.1, dirt: 0.2,
    tears: [{ a: [0.02, -0.1], b: [0.05, 1.1], jag: 1.5, scale: 2.5, seed: 31 }, { a: [0.95, -0.1], b: [0.99, 1.1], jag: 1.5, scale: 2.5, seed: 33 }] }),
    draw(g) { A.rect(g, 0, 0, 120, 48, '#b48f5a'); } });
})();
