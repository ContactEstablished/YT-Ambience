"""Rain contact pass (2026-10-09, prompt 9): where the rain reaches the platform, where runoff collects and
drains, and the exact drip / outlet / steam positions, from the finished kiosk and its props.

    blender -b ../kiosk_exterior.blend --factory-startup -P build_rain_contact.py

Needs Blender/kiosk_exterior.blend (build_exterior.py writes it: the kiosk, the kitchen and the exterior props as
they stand in Unreal). Nothing in the kiosk, its weathering bake or the props is rebuilt.
Writes:
  Unreal/RawContent/rain/T_RainContact.png   top-down wet map of the platform, 2048 px over +-4.096 m (4 mm):
                                             R damp, G standing water, B direct rain exposure, A 1 - contact darkening
  Unreal/RawContent/rain/rain_contact.json   drip sources and landing spots, downpipe mouths, the grate, steam
                                             sources (ray-cast heights), and the map's placement
  Blender/renders/rain_contact_map.png       a false-colour preview of the map (canopy outline, drips, trails)
Then in Unreal: node Scripts/ue.mjs Scripts/wet_fx.py

How the map is made (numbers in kiosk_config.RAIN_CONTACT):
  - exposure: from each 16 mm texel of the slab, 40 rays go up against the rain (falling ~10 deg toward +X+Y with
    gusts); the fraction that escapes is how much rain lands there. The canopy, the walls, the counter and every
    prop shelter it, so the wet/dry line follows the real geometry, not the canopy's rectangle;
  - damp = exposure through a soft threshold broken up by noise, plus spatter a few cm into the shelter, street
    splash and wicking along the slab's outer edge, drip spatter, runoff trails and the grate's wet ring;
  - standing water only where rain or runoff feeds a low spot of a gentle height field, and in a narrow intermittent
    line behind the steel edge angle (front and door side), never in front of the counter;
  - contact: anything standing on the slab (feet, bases, the walls) found by short upward rays, with a soft halo.
"""
import json
import math
import os
import struct
import sys
import time
import zlib

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kiosk_config as C  # noqa: E402

RC = C.RAIN_CONTACT
PH = C.PLATFORM_H
BLENDER_DIR = os.path.dirname(HERE)
RAW = os.path.join(os.path.dirname(BLENDER_DIR), "Unreal", "RawContent")
OUT_DIR = os.path.join(RAW, "rain")
HALF, NPX = RC["map_half_m"], RC["map_px"]
PX = 2.0 * HALF / NPX  # metres per texel
M = C.PLATFORM_MARGIN
PLAT = (C.X0 - M, C.X1 + M, C.Y0 - M, C.Y1 + M)
SKIP = {"ExteriorProto", "Review"}


# ---- geometry --------------------------------------------------------------------------------------------

def scene_bvh():
    """One BVH of every visible mesh in world space; tri_owner maps triangle ranges to object names."""
    deps = bpy.context.evaluated_depsgraph_get()
    cos, tris, owners, base, nt = [], [], [], 0, 0
    for ob in bpy.data.objects:
        if ob.type != "MESH" or ob.hide_render or SKIP & {c.name for c in ob.users_collection}:
            continue
        ev = ob.evaluated_get(deps)
        me = ev.to_mesh()
        n = len(me.vertices)
        co = np.empty(n * 3, np.float64)
        me.vertices.foreach_get("co", co)
        mw = np.array(ob.matrix_world)
        co = co.reshape(-1, 3) @ mw[:3, :3].T + mw[:3, 3]
        me.calc_loop_triangles()
        t = np.empty(len(me.loop_triangles) * 3, np.int64)
        me.loop_triangles.foreach_get("vertices", t)
        cos.append(co)
        tris.append(t.reshape(-1, 3) + base)
        owners.append((nt, ob.name))
        base += n
        nt += len(t) // 3
        ev.to_mesh_clear()
    co = np.concatenate(cos)
    tri = np.concatenate(tris)
    bvh = BVHTree.FromPolygons(co.tolist(), tri.tolist(), all_triangles=True)
    print(f"bvh: {len(tri)} triangles from {len(owners)} objects")
    return bvh, owners


def owner(owners, index):
    name = owners[0][1]
    for start, n in owners:
        if index >= start:
            name = n
    return name


# ---- raster helpers ----------------------------------------------------------------------------------------

def grid(n):
    """Texel-centre coordinates (x across, y down the rows from -HALF) for an n x n map."""
    c = -HALF + (np.arange(n) + 0.5) * (2.0 * HALF / n)
    return np.meshgrid(c, c)  # X[row, col], Y[row, col]


def upsample(a, n):
    """Bilinear resize of a square map to n x n (texel centres aligned)."""
    m = a.shape[0]
    s = (np.arange(n) + 0.5) * m / n - 0.5
    i0 = np.clip(np.floor(s).astype(int), 0, m - 1)
    i1 = np.clip(i0 + 1, 0, m - 1)
    f = np.clip(s - i0, 0.0, 1.0)
    rows = a[i0] * (1 - f)[:, None] + a[i1] * f[:, None]
    return rows[:, i0] * (1 - f)[None, :] + rows[:, i1] * f[None, :]


def noise(scale_m, seed, n=NPX):
    """Smooth value noise in [0, 1], features about scale_m across."""
    rng = np.random.default_rng(seed)
    cells = max(2, int(math.ceil(2.0 * HALF / scale_m)) + 1)
    g = rng.random((cells, cells))
    s = (np.arange(n) + 0.5) / n * (cells - 1)
    i0 = np.clip(np.floor(s).astype(int), 0, cells - 2)
    f = s - i0
    f = f * f * (3 - 2 * f)
    rows = g[i0] * (1 - f)[:, None] + g[i0 + 1] * f[:, None]
    return rows[:, i0] * (1 - f)[None, :] + rows[:, i0 + 1] * f[None, :]


def fbm(scales, seed):
    out, wsum = 0.0, 0.0
    for k, (s, w) in enumerate(scales):
        out = out + noise(s, seed + 17 * k) * w
        wsum += w
    return out / wsum


def blur(a, r):
    """Two passes of a separable box blur of radius r texels (about a tent filter)."""
    r = max(1, int(r))
    for _ in range(2):
        for axis in (0, 1):
            p = np.pad(a, [(r + 1, r) if ax == axis else (0, 0) for ax in (0, 1)], mode="edge")
            c = np.cumsum(p, axis=axis)
            if axis == 0:
                a = (c[2 * r + 1:] - c[:-2 * r - 1]) / (2 * r + 1)
            else:
                a = (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)
    return a


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def seg_dist(X, Y, a, b):
    """Distance from every texel to segment a-b, and the position along it (0..1)."""
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = max(dx * dx + dy * dy, 1e-9)
    t = np.clip(((X - ax) * dx + (Y - ay) * dy) / L2, 0.0, 1.0)
    return np.hypot(X - (ax + t * dx), Y - (ay + t * dy)), t


def platform_inside(X, Y, pad=0.0):
    return (X >= PLAT[0] - pad) & (X <= PLAT[1] + pad) & (Y >= PLAT[2] - pad) & (Y <= PLAT[3] + pad)


def edge_dist(X, Y):
    """Distance inside the slab to its nearest outer edge (negative outside)."""
    return np.minimum.reduce([X - PLAT[0], PLAT[1] - X, Y - PLAT[2], PLAT[3] - Y])


# ---- passes -----------------------------------------------------------------------------------------------

def exposure(bvh):
    n = RC["exposure_px"]
    X, Y = grid(n)
    rng = np.random.default_rng(7)
    k = RC["rays"]
    # stratified gust offsets (golden-angle spiral, gaussian radius) around the mean wind tilt
    i = np.arange(k) + 0.5
    rad = RC["gust"] * np.sqrt(-2.0 * np.log(1.0 - i / k * 0.98)) * 0.7
    ang = i * 2.399963 + rng.random() * 6.28
    tilt = np.stack([RC["wind"][0] + rad * np.cos(ang), RC["wind"][1] + rad * np.sin(ang)], 1)
    dirs = [Vector((-tx, -ty, 1.0)).normalized() for tx, ty in tilt]  # up, against the falling rain
    E = np.zeros((n, n))
    todo = platform_inside(X, Y, 0.04) & ~((X > C.X0 + 0.02) & (X < C.X1 - 0.02) & (Y > C.Y0 + 0.02) & (Y < C.Y1 - 0.02))
    t0 = time.time()
    for r, c in zip(*np.nonzero(todo)):
        o = Vector((X[r, c], Y[r, c], PH + 0.004))
        free = 0
        for d in dirs:
            if bvh.ray_cast(o, d, 40.0)[0] is None:
                free += 1
        E[r, c] = free / k
    print(f"exposure: {int(todo.sum())} texels x {k} rays in {time.time() - t0:.0f} s")
    return E


def contact(bvh):
    """1 where something stands on the slab within 3 cm above its top (8 mm texels)."""
    n = NPX // 2
    X, Y = grid(n)
    A = np.zeros((n, n))
    up = Vector((0.0, 0.0, 1.0))
    for r, c in zip(*np.nonzero(platform_inside(X, Y, 0.02))):
        if bvh.ray_cast(Vector((X[r, c], Y[r, c], PH + 0.0015)), up, 0.03)[0] is not None:
            A[r, c] = 1.0
    return A


def wet_trail(X, Y, pts, w0, w1, seed, fade=True):
    """A narrow meandering wet trail along a polyline: (damp, film) maps."""
    wn = noise(0.09, seed)  # width variation
    mn = (noise(0.14, seed + 3) - 0.5) * 0.035  # meander: shifts the centre line sideways
    total = sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))
    D = np.zeros_like(X)
    F = np.zeros_like(X)
    acc = 0.0
    for i in range(len(pts) - 1):
        d, t = seg_dist(X, Y, pts[i], pts[i + 1])
        L = math.dist(pts[i], pts[i + 1])
        s = (acc + t * L) / total  # 0 at the source, 1 at the end
        d = np.abs(d + mn)
        w = (w0 + (w1 - w0) * s) * (0.65 + 0.7 * wn)
        core = smoothstep(w, w * 0.35, d)
        strength = (1.0 - 0.35 * s) if fade else 1.0
        D = np.maximum(D, core * strength)
        F = np.maximum(F, smoothstep(w * 0.55, w * 0.1, d) * (0.85 - 0.45 * s))
        acc += L
    return D, F


def spatter(X, Y, x, y, r, seed):
    """Drip spatter: a wet core and speckles thinning out to radius r."""
    d = np.hypot(X - x, Y - y)
    fall = smoothstep(r, 0.0, d)
    sp = smoothstep(0.55, 0.75, noise(0.012, seed) * 0.6 + noise(0.03, seed + 1) * 0.4 + fall * 0.35)
    core = smoothstep(0.035, 0.008, d)
    return np.maximum(core, sp * fall), smoothstep(0.03, 0.0, d) * 0.6


def write_png(path, rgba):
    """8-bit RGBA PNG (rows top to bottom = map rows, y from -HALF)."""
    h, w, _ = rgba.shape
    raw = b"".join(b"\x00" + rgba[r].tobytes() for r in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def resolve_points(bvh, owners):
    """Drip sources (the underside above each chosen point) and landing spots, outlet landings, steam bases."""
    up, down = Vector((0, 0, 1)), Vector((0, 0, -1))
    out = {"drips": {}, "outlets": {}, "steam": {}}
    for name, d in RC["drips"].items():
        x, y = d["xy"]
        hit = bvh.ray_cast(Vector((x, y, PH + 0.3)), up, 5.0)
        if hit[0] is None:
            raise RuntimeError(f"drip {name}: nothing above {x, y}")
        src = hit[0]
        land = bvh.ray_cast(src + Vector((0, 0, -0.005)), down, 5.0)
        out["drips"][name] = {"src": [x, y, round(src.z, 4)], "land": [x, y, round(land[0].z, 4)],
                              "src_on": owner(owners, hit[2]), "land_on": owner(owners, land[2]),
                              "fall_m": round(src.z - land[0].z, 4)}
    for name, o in RC["outlets"].items():
        x, y = o["land"]
        land = bvh.ray_cast(Vector((x, y, o["mouth"][2] + 0.02)), down, 1.0)
        out["outlets"][name] = {"mouth": list(o["mouth"]), "land": [x, y, round(land[0].z, 4)], "land_on": owner(owners, land[2])}
    for name, s in RC["steam"].items():
        x, y = s["xy"]
        top = bvh.ray_cast(Vector((x, y, s["z"] + 1.5)), down, 3.0)
        out["steam"][name] = dict(s, xy=[x, y], surface_z=round(top[0].z, 4) if top[0] else None,
                                  surface_on=owner(owners, top[2]) if top[0] else None)
    gx, gy = RC["grate"]["xy"]
    g = bvh.ray_cast(Vector((gx, gy, PH + 0.2)), down, 0.5)
    out["grate"] = {"xy": [gx, gy], "z": round(g[0].z, 4), "on": owner(owners, g[2])}
    return out


def main():
    t0 = time.time()
    os.makedirs(OUT_DIR, exist_ok=True)
    bvh, owners = scene_bvh()
    pts = resolve_points(bvh, owners)
    for name, d in pts["drips"].items():
        print(f"drip {name}: source {d['src'][2]:.3f} m on {d['src_on']}, lands {d['land'][2]:.3f} m on {d['land_on']} (fall {d['fall_m']:.2f} m)")
    for name, o in pts["outlets"].items():
        print(f"outlet {name}: lands {o['land'][2]:.3f} m on {o['land_on']}")
    for name, s in pts["steam"].items():
        print(f"steam {name}: surface {s['surface_z']} on {s['surface_on']}")
    print(f"grate: {pts['grate']}")

    X, Y = grid(NPX)
    inside = platform_inside(X, Y, 0.012)  # a little past the edge, so the slab's vertical faces read the edge values
    E = upsample(blur(exposure(bvh), 1), NPX)  # softened a little: thin legs barely shelter real rain
    Ac = upsample(contact(bvh), NPX)

    # damp from direct rain: soft threshold, the line broken up by noise (no canopy-shaped rectangle)
    wn = fbm([(0.55, 0.35), (0.22, 0.35), (0.07, 0.2), (0.025, 0.1)], 11) - 0.5  # damp tongues 20-60 cm, ragged edges
    rain = smoothstep(RC["wet_lo"], RC["wet_hi"], E + wn * RC["edge_noise"] * smoothstep(0.0, 0.2, E + 0.12))
    # spatter a few cm into the shelter, in specks
    sb = blur(rain, RC["splashback_m"] / PX / 2)
    speck = smoothstep(0.45, 0.7, noise(0.014, 21) * 0.55 + noise(0.045, 22) * 0.45)
    damp = np.maximum(rain, sb * 0.75 * (0.35 + 0.65 * speck))
    # street splash and wicking along the slab's outer edge
    de = edge_dist(X, Y)
    w = RC["edge_wick_m"][0] + (RC["edge_wick_m"][1] - RC["edge_wick_m"][0]) * noise(0.22, 31)
    damp = np.maximum(damp, smoothstep(w, w * 0.25, de) * (0.65 + 0.35 * noise(0.05, 32)))

    film = np.zeros_like(X)
    # drips: spatter round the landing spot and a short trail toward the edge
    for k, (name, d) in enumerate(RC["drips"].items()):
        x, y = d["xy"]
        sd, sf = spatter(X, Y, x, y, RC["splash_r_m"], 40 + k)
        tx, ty = d["trail"]
        td, tf = wet_trail(X, Y, [(x, y), (x + tx * 0.5 + 0.01, y + ty * 0.5), (x + tx, y + ty)], 0.022, 0.03, 50 + k)
        damp = np.maximum.reduce([damp, sd, td * 0.9])
        film = np.maximum.reduce([film, sf, tf * 0.5])
    # downpipe outlets: a wet patch on the splash block and a narrow trail to the slab's edge
    w0, w1 = RC["trail_w_m"]
    for k, (name, o) in enumerate(RC["outlets"].items()):
        lx, ly = o["land"]
        d = np.hypot(X - lx, Y - ly)
        damp = np.maximum(damp, smoothstep(0.10, 0.03, d))
        film = np.maximum(film, smoothstep(0.06, 0.015, d) * 0.8)
        sd, _ = spatter(X, Y, lx, ly, 0.16, 60 + k)
        damp = np.maximum(damp, sd * 0.8)
        td, tf = wet_trail(X, Y, [(lx, ly)] + [tuple(p) for p in o["trail"]], w0, w1, 70 + k)
        damp = np.maximum(damp, td)
        film = np.maximum(film, tf)
        ex, ey = o["trail"][-1]  # the run-off fans out a little where it leaves the slab
        damp = np.maximum(damp, smoothstep(0.12, 0.02, np.hypot(X - ex, Y - ey)) * 0.9)
    # the drain hose's grate under the counter: a damp ring
    gx, gy = RC["grate"]["xy"]
    dg = np.hypot(X - gx, Y - gy)
    damp = np.maximum(damp, smoothstep(RC["grate"]["r_m"] * (0.8 + 0.5 * noise(0.04, 80)), 0.05, dg) * 0.85)
    film = np.maximum(film, smoothstep(0.09, 0.05, dg) * 0.3)

    # standing water: a gentle height field; water stands where rain or runoff feeds a low spot
    H = fbm([(0.7, 0.55), (0.22, 0.3), (0.07, 0.15)], 91)
    supply = np.maximum(smoothstep(0.45, 0.8, E), film * 0.8)
    # behind the steel edge angle (front edge y0 and door-side edge x0, 4 mm proud) water dams in a narrow line
    lip = np.minimum(np.where(np.abs(X - PLAT[0]) < 1, X - PLAT[0], 9.0), np.where(np.abs(Y - PLAT[2]) < 1, Y - PLAT[2], 9.0))
    lipband = smoothstep(0.03, 0.04, lip) * smoothstep(0.04 + RC["lip_pool_m"], 0.04 + RC["lip_pool_m"] * 0.4, lip)
    H = H - lipband * 0.2 * smoothstep(0.55, 0.72, noise(0.3, 92))  # in short stretches, not a continuous strip
    pool = smoothstep(RC["pool_level"] + RC["pool_soft"], RC["pool_level"] - RC["pool_soft"], H) * supply
    for (x0, y0), (x1, y1) in RC["no_pool"]:
        keep = smoothstep(0.0, 0.08, np.maximum.reduce([x0 - X, X - x1, y0 - Y, Y - y1]))
        pool *= keep
    film = np.maximum(film, pool)
    damp = np.maximum(damp, smoothstep(0.0, 0.3, film))

    # contact: a soft halo round anything standing on the slab (feet, bases, the walls)
    halo = np.clip(blur(Ac, RC["contact_halo_m"] / PX) * 1.8, 0.0, 1.0)
    contact_d = np.maximum(halo * (0.6 + 0.4 * noise(0.04, 95)), Ac)

    damp *= inside
    film *= inside
    E *= inside
    contact_d *= inside
    # alpha = 1 - contact, never fully transparent: Unreal's PNG import overwrites the colour of zero-alpha texels
    rgba = np.stack([damp, film, E, np.clip(1.0 - contact_d, 1.0 / 255.0, 1.0)], -1)
    rgba = (np.clip(rgba, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)
    write_png(os.path.join(OUT_DIR, "T_RainContact.png"), rgba)

    # preview: grey concrete, darker where damp, blue where water stands, black contact, red canopy outline
    sel = (slice(int((HALF - 4.0) / PX), int((HALF + 4.0) / PX)),) * 2
    base = np.full(X.shape + (3,), 0.62)
    base *= (1.0 - 0.55 * damp)[..., None]
    base = base * (1 - film[..., None]) + np.array([0.15, 0.35, 0.75]) * film[..., None]
    base *= (1.0 - 0.75 * contact_d)[..., None]
    base[~inside] = np.array([0.08, 0.08, 0.09])
    for xa, xb, ya, yb in ((C.CANOPY_X0, C.CANOPY_X1, C.CANOPY_Y0, C.CANOPY_Y0), (C.CANOPY_X0, C.CANOPY_X1, C.CANOPY_Y1, C.CANOPY_Y1),
                           (C.CANOPY_X0, C.CANOPY_X0, C.CANOPY_Y0, C.CANOPY_Y1), (C.CANOPY_X1, C.CANOPY_X1, C.CANOPY_Y0, C.CANOPY_Y1)):
        d, _ = seg_dist(X, Y, (xa, ya), (xb, yb))
        base[d < 0.006] = (0.9, 0.15, 0.1)
    for d in RC["drips"].values():
        base[np.hypot(X - d["xy"][0], Y - d["xy"][1]) < 0.02] = (1.0, 0.1, 0.9)
    img = (np.clip(base[sel][::-1], 0, 1) * 255 + 0.5).astype(np.uint8)  # +Y (back) at the top, like a plan
    a = np.full(img.shape[:2] + (1,), 255, np.uint8)
    os.makedirs(os.path.join(BLENDER_DIR, "renders"), exist_ok=True)
    write_png(os.path.join(BLENDER_DIR, "renders", "rain_contact_map.png"), np.concatenate([img, a], -1))

    pts["map"] = {"half_m": HALF, "px": NPX, "note": "u = (x + half) / (2 half), v = (y + half) / (2 half) in the kiosk frame; v = 0 is the top row"}
    pts["platform"] = {"rect": list(PLAT), "h": PH}
    with open(os.path.join(OUT_DIR, "rain_contact.json"), "w", encoding="utf-8") as f:
        json.dump(pts, f, indent=1)
    cover = lambda m: 100.0 * float((m * inside).sum() / inside.sum())  # noqa: E731
    print(f"slab: damp {cover(damp > 0.5):.1f}%, standing water {cover(film > 0.5):.1f}%, rain-exposed {cover(E > 0.5):.1f}%")
    print(f"build_rain_contact: done in {time.time() - t0:.0f} s -> {OUT_DIR}")


main()
