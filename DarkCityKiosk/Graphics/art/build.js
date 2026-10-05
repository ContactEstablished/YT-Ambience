// Builds one atlas in the page: draws and ages every item of that atlas, packs them and returns the
// three maps as base64 RGBA (encoded to PNG by the Node runner, which keeps colour under zero alpha).
(function () {
  const A = window.ART;

  function b64(u8) {
    let s = '';
    const CH = 0x8000;
    for (let i = 0; i < u8.length; i += CH) s += String.fromCharCode.apply(null, u8.subarray(i, i + CH));
    return btoa(s);
  }

  A.buildAtlas = function (name, cfg, only) {
    const items = A.items.filter((it) => it.atlas === name && (!only || only.includes(it.name)));
    for (const it of items) {
      it.s = it.s || cfg.s;
      it.pw = Math.round((it.w + 2 * it.margin) * it.s);
      it.ph = Math.round((it.h + 2 * it.margin) * it.s);
    }
    const { rects, used } = A.pack(items, cfg.size, cfg.gutter);
    const N = cfg.size;
    const C = new Uint8ClampedArray(N * N * 4), Nm = new Uint8ClampedArray(N * N * 4), S = new Uint8ClampedArray(N * N * 4);
    const fillC = cfg.fill || [128, 120, 100, 0];
    for (let i = 0; i < N * N; i++) {
      C.set(fillC, i * 4);
      Nm.set([128, 128, 255, 255], i * 4);
      S.set([220, 0, 0, 255], i * 4);
    }
    const manifest = {};
    const t0 = performance.now();
    for (const it of items) {
      const [rx, ry, rw, rh] = rects[it.name];
      const s = it.s;
      const cv = document.createElement('canvas');
      cv.width = rw;
      cv.height = rh;
      const g = cv.getContext('2d', { willReadFrequently: true });
      g.save();
      g.scale(s, s);
      g.translate(it.margin, it.margin);
      if (it.draw) it.draw(g);
      g.restore();
      let maps;
      if (it.pixel) maps = decalMaps(it, cv, s);
      else maps = A.age(it, cv, s);
      for (let j = 0; j < rh; j++) {
        const dst = ((ry + j) * N + rx) * 4;
        C.set(maps.C.subarray(j * rw * 4, (j + 1) * rw * 4), dst);
        Nm.set(maps.N.subarray(j * rw * 4, (j + 1) * rw * 4), dst);
        S.set(maps.S.subarray(j * rw * 4, (j + 1) * rw * 4), dst);
      }
      manifest[it.name] = {
        atlas: name, rect: [rx, ry, rw, rh], uv: [rx / N, ry / N, (rx + rw) / N, (ry + rh) / N],
        size_m: [(it.w + 2 * it.margin) / 1000, (it.h + 2 * it.margin) / 1000], paper_m: [it.w / 1000, it.h / 1000],
        margin_m: it.margin / 1000, kind: (it.age && it.age.kind) || (it.pixel ? 'decal' : 'paper'), px_per_mm: s,
      };
    }
    return {
      manifest, used, size: N, ms: Math.round(performance.now() - t0),
      C: b64(new Uint8Array(C.buffer)), N: b64(new Uint8Array(Nm.buffer)), S: b64(new Uint8Array(S.buffer)),
    };
  };

  // decals: per-pixel functions, with the drawn canvas available as a mask sampler (mm coords)
  function decalMaps(it, cv, s) {
    const W = cv.width, H = cv.height;
    const src = cv.getContext('2d').getImageData(0, 0, W, H).data;
    const mask = (x, y) => {
      const i = Math.min(W - 1, Math.max(0, Math.floor((x + it.margin) * s))), j = Math.min(H - 1, Math.max(0, Math.floor((y + it.margin) * s)));
      return src[(j * W + i) * 4 + 3] / 255;
    };
    const out = { C: new Uint8ClampedArray(W * H * 4), N: new Uint8ClampedArray(W * H * 4), S: new Uint8ClampedArray(W * H * 4) };
    const Hgt = new Float32Array(W * H);
    for (let j = 0; j < H; j++)
      for (let i = 0; i < W; i++) {
        const k = j * W + i;
        const x = (i + 0.5) / s - it.margin, y = (j + 0.5) / s - it.margin;
        const [r, g, b, a, h, rough] = it.pixel(x, y, mask);
        out.C[k * 4] = r * 255;
        out.C[k * 4 + 1] = g * 255;
        out.C[k * 4 + 2] = b * 255;
        out.C[k * 4 + 3] = a * 255;
        out.S[k * 4] = rough * 255;
        out.S[k * 4 + 1] = 0;
        out.S[k * 4 + 2] = 0;
        out.S[k * 4 + 3] = 255;
        Hgt[k] = h;
      }
    for (let j = 0; j < H; j++)
      for (let i = 0; i < W; i++) {
        const k = j * W + i;
        const hl = Hgt[j * W + Math.max(0, i - 1)], hr = Hgt[j * W + Math.min(W - 1, i + 1)];
        const hu = Hgt[Math.max(0, j - 1) * W + i], hd = Hgt[Math.min(H - 1, j + 1) * W + i];
        const nx = -(hr - hl) * 0.5 * s, ny = -(hd - hu) * 0.5 * s, L = Math.hypot(nx, ny, 1);
        out.N[k * 4] = (nx / L * 0.5 + 0.5) * 255;
        out.N[k * 4 + 1] = (ny / L * 0.5 + 0.5) * 255;
        out.N[k * 4 + 2] = (1 / L * 0.5 + 0.5) * 255;
        out.N[k * 4 + 3] = 255;
      }
    return out;
  }
})();
