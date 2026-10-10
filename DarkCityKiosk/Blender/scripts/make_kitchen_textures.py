"""Kitchen pass (2026-10-09): the wear textures for M_Kitchen (pure numpy; Blender's python runs it):

    "C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe" make_kitchen_textures.py

Unreal/RawContent/kitchen/T_CounterWear.png (4096 x 512, the customer counter's top sheet through its
UV1; row 0 = the wall side, the last row = the customer's edge, columns = x along the counter):
    R polish    where hands, trays and bowls slide every shift: brighter, lower roughness
    G scratches fine lines, mostly along the counter (things slid along it), a few across
    B stains    faint rings from cups and bowls, dried drips and soy spots near the condiments
    A seams     dark grime in the sheet seams, round the jambs and the terminal, along the wall
Old but hygienic: wiped every night, so stains are faint and only the seams hold dirt.
Unreal/RawContent/kitchen/T_KitchenDetail.png (1024^2, tiles every KITCHEN_LOOK DetailTile metres):
    R brushed grain  G smudges + fingerprints  B water spots  A grime noise
"""
import json
import math
import os
import struct
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kiosk_config as C  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Unreal", "RawContent", "kitchen")
RNG = np.random.default_rng(7)


def png(path, img):
    """img: HxWx4 float 0..1 -> 8-bit RGBA PNG."""
    a = (np.clip(img, 0, 1) * 255 + 0.5).astype(np.uint8)
    h, w = a.shape[:2]
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    open(path, "wb").write(data)


def value_noise(h, w, cell, seed, tile=False):
    """Smooth value noise with `cell` px features (tileable if tile)."""
    rng = np.random.default_rng(seed)
    gh, gw = int(math.ceil(h / cell)) + 1, int(math.ceil(w / cell)) + 1
    g = rng.random((gh, gw))
    if tile:
        g[-1, :], g[:, -1] = g[0, :], g[:, 0]
    y = np.arange(h) / cell
    x = np.arange(w) / cell
    y0, x0 = np.floor(y).astype(int), np.floor(x).astype(int)
    fy, fx = y - y0, x - x0
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0]
    b = g[y0][:, x0 + 1]
    c = g[y0 + 1][:, x0]
    d = g[y0 + 1][:, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy)[:, None] + (c * (1 - fx) + d * fx) * fy[:, None]


def fbm(h, w, cell, octaves, seed, tile=False):
    out, amp, tot = np.zeros((h, w)), 1.0, 0.0
    for o in range(octaves):
        out += amp * value_noise(h, w, max(cell / 2 ** o, 2), seed + o * 13, tile)
        tot += amp
        amp *= 0.5
    return out / tot


def blur(a, r):
    """Separable box blur x3 (~gaussian), radius r px."""
    if r < 1:
        return a
    k = np.ones(2 * r + 1) / (2 * r + 1)
    for _ in range(3):
        a = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 0, a)
        a = np.apply_along_axis(lambda v: np.convolve(v, k, mode="same"), 1, a)
    return a


def lines(h, w, n, length, angle_fn, width, strength_fn, seed, tile=False):
    """Anti-aliased line segments splatted into an h x w field (scratches)."""
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w))
    for _ in range(n):
        x0, y0 = rng.random() * w, rng.random() * h
        L = length * (0.3 + rng.random() * 1.2)
        a = angle_fn(rng)
        s = strength_fn(x0, y0, rng)
        if s <= 0:
            continue
        steps = int(L * 2) + 2
        t = np.linspace(0, 1, steps)
        bend = (rng.random() - 0.5) * 0.15
        xs = x0 + np.cos(a + bend * t) * L * t
        ys = y0 + np.sin(a + bend * t) * L * t
        fade = np.sin(np.pi * t) ** 0.5 * s * (0.6 + 0.4 * rng.random(steps))
        for dx, dy, wt in ((0, 0, 1.0), (0, 1, 0.5 * width), (0, -1, 0.5 * width)):
            xi, yi = (xs + dx).astype(int), (ys + dy).astype(int)
            if tile:
                xi, yi = xi % w, yi % h
                ok = np.ones_like(xi, bool)
            else:
                ok = (xi >= 0) & (xi < w) & (yi >= 0) & (yi < h)
            np.add.at(acc, (yi[ok], xi[ok]), fade[ok] * wt)
    return np.clip(acc, 0, 1)


def counter_wear():
    data = json.load(open(os.path.join(OUT, "kitchen.json"), encoding="utf-8"))
    r = data["counter_uv"]
    W, H = 4096, 512
    x = r["x0"] + (np.arange(W) + 0.5) / W * (r["x1"] - r["x0"])  # metres along the counter
    y = r["y1"] - (np.arange(H) + 0.5) / H * (r["y1"] - r["y0"])  # row 0 = wall side
    X, Y = np.meshgrid(x, y)
    front = r["y0"] + 0.01  # the customer's edge
    d_front = Y - front  # 0 at the edge, 0.4 at the wall
    sw, pos = C.SERVICE_WINDOW, C.POS
    n1 = fbm(H, W, 90, 4, 11)
    n2 = fbm(H, W, 22, 3, 12)
    # polish: forearm band along the edge, the pickup spot by the opening, in front of the terminal
    edge_band = np.exp(-(d_front / 0.09) ** 2)
    opening = np.exp(-(((X - (sw["x0"] + sw["x1"]) / 2) / 0.9) ** 4))
    pickup = np.exp(-(((X + 0.52) / 0.28) ** 2 + ((d_front - 0.17) / 0.14) ** 2))
    terminal = np.exp(-(((X - (pos["x0"] + pos["x1"]) / 2) / 0.22) ** 2)) * np.exp(-((d_front - 0.05) / 0.09) ** 2)
    nose = np.exp(-(d_front / 0.012) ** 2)
    polish = np.clip((edge_band * (0.35 + 0.45 * opening) + pickup * 0.55 + terminal * 0.6 + nose * 0.5) * (0.65 + 0.7 * n1), 0, 1)
    # scratches: along x mostly (slid trays and bowls), where things are actually slid (prompt 10: they were laid
    # evenly at 35% or more everywhere, plus 900 random ones at 50%, and read as a bright, even haze): strength follows
    # the polish map's use zones (pickup spot, forearm band, terminal), faint elsewhere; few strays; patchy, not uniform
    pol_at = lambda x0, y0, rng: 0.06 + 0.94 * polish[int(y0), int(x0)] ** 1.6  # noqa: E731
    sc = lines(H, W, 4200, 40, lambda rng: (rng.normal(0, 0.18) + (math.pi if rng.random() < 0.5 else 0)), 0.6, pol_at, 21)
    sc += lines(H, W, 300, 18, lambda rng: rng.random() * math.pi, 0.5, lambda a, b, rng: 0.2, 22)
    sc = np.clip(sc * (0.25 + 0.95 * np.clip((n2 - 0.35) * 2.2, 0, 1)) * 0.8, 0, 1)
    # stains: rings (cups, bowls), a few drips, soy specks round the condiment caddy
    st = np.zeros((H, W))
    rng = np.random.default_rng(31)
    px_m = W / (r["x1"] - r["x0"])
    for _ in range(26):
        cx = rng.uniform(r["x0"] + 0.3, r["x1"] - 0.1)
        cy = rng.uniform(front + 0.06, r["y1"] - 0.05)
        rad = rng.choice([0.032, 0.036, 0.045, 0.06, 0.095])
        dist = np.hypot(X - cx, Y - cy)
        ring = np.exp(-((dist - rad) / 0.0016) ** 2)
        arc = (np.cos(np.arctan2(Y - cy, X - cx) - rng.uniform(0, 6.3)) > rng.uniform(-0.6, 0.3)).astype(float)
        st += ring * arc * rng.uniform(0.25, 0.6) * (dist < rad + 0.01)
    for _ in range(40):  # drips and spots
        cx, cy = rng.uniform(r["x0"], r["x1"]), rng.uniform(front + 0.03, r["y1"] - 0.03)
        if rng.random() < 0.5:
            cx = rng.normal(-1.12, 0.12)  # round the condiment caddy
        rad = rng.uniform(0.002, 0.009)
        dist = np.hypot(X - cx, Y - cy)
        st += np.clip(1 - dist / rad, 0, 1) ** 0.5 * rng.uniform(0.2, 0.5)
    st = np.clip(st * (0.7 + 0.5 * n2), 0, 1)
    # seams and edge grime: distance to the nearest sheet edge (pieces from the kitchen build)
    dmin = np.full((H, W), 1.0)
    for a, b, c, d in data["counter_pieces"]:
        inside = (X >= a) & (X <= b) & (Y >= c) & (Y <= d)
        de = np.minimum.reduce([X - a, b - X, Y - c, d - Y])
        dmin = np.where(inside, np.minimum(dmin, de), dmin)
    seam = np.exp(-(dmin / 0.004) ** 2)
    seam = np.where(d_front < 0.02, seam * 0.25, seam)  # the customer edge is the cleanest (wiped, rubbed)
    seam = np.clip(seam * (0.55 + 0.6 * n2) + np.exp(-((r["y1"] - Y) / 0.012) ** 2) * 0.5 * n1, 0, 1)
    png(os.path.join(OUT, "T_CounterWear.png"), np.dstack([polish, sc, st, seam]))
    print(f"T_CounterWear: polish mean {polish.mean():.2f}, scratches {sc.mean():.3f}, stains {st.mean():.3f}, seams {seam.mean():.3f}, "
          f"{px_m:.0f} px/m")


def kitchen_detail():
    N = 1024
    grain = fbm(N, N, 3, 2, 41, tile=True)
    streak = blur(np.random.default_rng(42).random((N, N)), 0)
    streak = np.apply_along_axis(lambda v: np.convolve(np.concatenate([v[-40:], v, v[:40]]), np.ones(81) / 81, mode="same")[40:-40], 1, streak)
    brushed = np.clip((streak - streak.mean()) * 6 + 0.5, 0, 1) * 0.8 + grain * 0.2
    sm = fbm(N, N, 140, 4, 43, tile=True)
    smudge = np.clip((sm - 0.52) * 3.2, 0, 1)
    rng = np.random.default_rng(44)
    Y, X = np.mgrid[0:N, 0:N]
    for _ in range(40):  # fingerprints: small ovals of whorls
        cx, cy, a = rng.uniform(0, N), rng.uniform(0, N), rng.uniform(0, math.pi)
        dx = (X - cx + N / 2) % N - N / 2
        dy = (Y - cy + N / 2) % N - N / 2
        u = dx * math.cos(a) + dy * math.sin(a)
        v = -dx * math.sin(a) + dy * math.cos(a)
        rr = np.hypot(u / 9, v / 13)
        smudge += np.clip(1 - rr, 0, 1) ** 0.7 * (0.5 + 0.5 * np.sin(rr * 26)) * rng.uniform(0.3, 0.7)
    smudge = np.clip(smudge, 0, 1)
    spots = np.zeros((N, N))
    for _ in range(260):
        cx, cy, rad = rng.uniform(0, N), rng.uniform(0, N), rng.uniform(1.5, 7)
        dx = (X - cx + N / 2) % N - N / 2
        dy = (Y - cy + N / 2) % N - N / 2
        d = np.hypot(dx, dy)
        spots += (np.exp(-((d - rad) / 0.9) ** 2) * 0.8 + np.clip(1 - d / rad, 0, 1) * 0.25) * rng.uniform(0.3, 1.0)
    spots = np.clip(spots, 0, 1)
    grime = fbm(N, N, 60, 4, 45, tile=True)
    png(os.path.join(OUT, "T_KitchenDetail.png"), np.dstack([brushed, smudge, spots, grime]))
    print(f"T_KitchenDetail: brushed {brushed.mean():.2f}, smudge {smudge.mean():.2f}, spots {spots.mean():.3f}, grime {grime.mean():.2f}")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    counter_wear()
    kitchen_detail()
