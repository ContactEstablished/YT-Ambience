"""Layout for the instanced city background (setup_city_bg.py builds it in Unreal).

Pure Python (no unreal), so it also runs in Blender's bundled python for quick checks:

    "C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe" Scripts/city_bg_layout.py

That writes RawContent/city_bg.json (every part, the re-hosted screens, shop lights and the
collision/occlusion boxes for the traffic check) and prints per-band stats.

Every tower is a stack of primitive parts (unit cube / cylinder instances) in the Blender kiosk
frame (metres, +X along the kiosk front, +Y toward its back; yaw from +X toward +Y):
  facade  window tiers (the window shader reads each part's size from per-instance data)
  podium  shop floors at street level (same shader, shop settings)
  plain   roof plant, masts, ledges, skybridge decks, screen bezels (dark, no windows)
  light   beacons, neon strips, landmark rings, skybridge glazing (emissive, blinking/pulsing)
Bands, heights and the hero-view vista are set in scene_config.CITY_BG.
"""
import json
import math
import os
import random
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(os.path.dirname(SCRIPTS_DIR), "RawContent")
BLENDER_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(SCRIPTS_DIR)), "Blender", "scripts")
for p in (SCRIPTS_DIR, BLENDER_SCRIPTS):
    if p not in sys.path:
        sys.path.insert(0, p)
import kiosk_config as K  # noqa: E402
import scene_config as S  # noqa: E402

FACADE_FLOATS = 10  # sx, sy, sz, lit, warm, bright, seed, shape (0 box, 1 cylinder), floor_h, bay_w
LIGHT_FLOATS = 7  # r, g, b, intensity, blink (0..1), phase (0..1), pulse (0..1)


def mid_camera():
    """Mid-pose camera position (kiosk frame): the orbit at theta 0."""
    hc, vc = K.HERO_CAM, K.VIDEO_CAM
    px, py = K.ORBIT_PIVOT
    return (px + (hc["pos_xy"][0] - px) * vc["distance_scale"], py + (hc["pos_xy"][1] - py) * vc["distance_scale"])


CAM = mid_camera()


def cam_polar(x, y):
    """(distance, azimuth deg) of a point seen from the Mid camera."""
    dx, dy = x - CAM[0], y - CAM[1]
    return math.hypot(dx, dy), math.degrees(math.atan2(dy, dx))


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def light(rgb, intensity, blink=0.0, phase=0.0, pulse=0.0):
    return [rgb[0], rgb[1], rgb[2], intensity, blink, phase, pulse]


def part(kind, shape, x, y, z0, z1, sx, sy, yaw, data=None, group=None):
    return {"kind": kind, "shape": shape, "c": [round(x, 3), round(y, 3), round((z0 + z1) / 2, 3)],
            "size": [round(sx, 3), round(sy, 3), round(z1 - z0, 3)], "yaw": round(yaw, 3), "data": data, "group": group}


# ---- 2D footprints ---------------------------------------------------------------------------
def quad(cx, cy, yaw, sx, sy, pad=0.0):
    a = math.radians(yaw)
    ux, uy = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
    hx, hy = sx / 2 + pad, sy / 2 + pad
    return [(cx + ux[0] * i * hx + uy[0] * j * hy, cy + ux[1] * i * hx + uy[1] * j * hy) for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def overlap(a, b):
    """Separating-axis test for two convex quads."""
    for poly in (a, b):
        for i in range(4):
            ex, ey = poly[(i + 1) % 4][0] - poly[i][0], poly[(i + 1) % 4][1] - poly[i][1]
            nx, ny = -ey, ex
            pa = [nx * p[0] + ny * p[1] for p in a]
            pb = [nx * p[0] + ny * p[1] for p in b]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return False
    return True


def in_quad(q, x, y):
    s = None
    for i in range(4):
        (x0, y0), (x1, y1) = q[i], q[(i + 1) % 4]
        c = (x1 - x0) * (y - y0) - (y1 - y0) * (x - x0)
        if s is None:
            s = c > 0
        elif (c > 0) != s:
            return False
    return True


class Occupancy:
    """Placed footprints with a bounding-circle reject in front of the SAT test."""

    def __init__(self):
        self.items = []

    def add(self, q):
        cx, cy = sum(p[0] for p in q) / 4, sum(p[1] for p in q) / 4
        self.items.append((cx, cy, max(math.hypot(p[0] - cx, p[1] - cy) for p in q), q))

    def hits(self, q):
        cx, cy = sum(p[0] for p in q) / 4, sum(p[1] for p in q) / 4
        r = max(math.hypot(p[0] - cx, p[1] - cy) for p in q)
        return any((cx - ox) ** 2 + (cy - oy) ** 2 < (r + orr) ** 2 and overlap(q, oq) for ox, oy, orr, oq in self.items)


class CarPaths:
    """Flying-traffic corridor centrelines (RawContent/traffic_routes.json from traffic_plan.py, or an
    older traffic.json with per-car paths), bucketed on a 20 m grid."""

    def __init__(self, path):
        self.cells = {}
        lines = []
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            if "layers" in data:
                lines = [r["points"] for recs in data["layers"].values() for r in recs] + ([data["hero"]["points"]] if data.get("hero") else [])
            else:
                lines = [c["path"] for c in data.get("cars", [])]
        for line in lines:
            for p in line:
                self.cells.setdefault((int(p[0] // 20), int(p[1] // 20)), []).append(p)

    def near(self, x0, x1, y0, y1):
        for i in range(int(x0 // 20), int(x1 // 20) + 1):
            for j in range(int(y0 // 20), int(y1 // 20) + 1):
                yield from self.cells.get((i, j), ())

    def conflict(self, q, top, pad):
        xs, ys = [p[0] for p in q], [p[1] for p in q]
        return any(p[2] < top + pad and in_quad(q, p[0], p[1]) for p in self.near(min(xs), max(xs), min(ys), max(ys)))

    def conflict_boxes(self, boxes):
        """Any path point inside one of these (cx, cy, angle, half_u, half_v, z0, z1) boxes."""
        for cx, cy, a, hu, hv, z0, z1 in boxes:
            r = math.hypot(hu, hv)
            ca, sa = math.cos(a), math.sin(a)
            for p in self.near(cx - r, cx + r, cy - r, cy + r):
                dx, dy = p[0] - cx, p[1] - cy
                if z0 < p[2] < z1 and abs(dx * ca + dy * sa) < hu and abs(-dx * sa + dy * ca) < hv:
                    return True
        return False

    def near_segment(self, a, b, clear):
        """Any path point within `clear` of the 3D segment a-b."""
        x0, x1 = min(a[0], b[0]) - clear, max(a[0], b[0]) + clear
        y0, y1 = min(a[1], b[1]) - clear, max(a[1], b[1]) + clear
        d = [b[i] - a[i] for i in range(3)]
        L2 = sum(v * v for v in d) or 1e-9
        for p in self.near(x0, x1, y0, y1):
            t = max(0.0, min(1.0, sum((p[i] - a[i]) * d[i] for i in range(3)) / L2))
            if math.dist(p, [a[i] + d[i] * t for i in range(3)]) < clear:
                return True
        return False


# ---- Towers ------------------------------------------------------------------------------------
class Tower:
    """Parts in the tower's frame: origin at its footprint centre on the ground, rotated by yaw."""

    def __init__(self, name, group, cx, cy, yaw, data):
        self.name, self.group, self.cx, self.cy, self.yaw = name, group, cx, cy, yaw
        a = math.radians(yaw)
        self.ca, self.sa = math.cos(a), math.sin(a)
        self.dist_cam, self.az_cam = cam_polar(cx, cy)
        self.data = data
        self.parts, self.tiers, self.signs = [], [], []
        self.height = 0.0

    def w(self, lx, ly):
        return self.cx + self.ca * lx - self.sa * ly, self.cy + self.sa * lx + self.ca * ly

    def add(self, kind, shape, lx, ly, z0, z1, sx, sy, data=None, yaw_off=0.0):
        x, y = self.w(lx, ly)
        self.parts.append(part(kind, shape, x, y, z0, z1, sx, sy, self.yaw + yaw_off, data, self.group))

    def tier(self, shape, lx, ly, z0, z1, dd, ww, kind="facade"):
        d = self.data
        if kind == "podium":
            fd = [dd, ww, z1 - z0, S.CITY_BG["shop_lit"], 0.7, d["bright"], d["seed"] + 3.0, 0.0, 0.0, 0.0]
        else:
            fd = [dd, ww, z1 - z0, d["lit"], d["warm"], d["bright"], d["seed"], 1.0 if shape == "cyl" else 0.0, d["floor_h"], d["bay"]]
            self.tiers.append((lx, ly, z0, z1, dd, ww, shape))
            self.height = max(self.height, z1)
        self.add(kind, shape, lx, ly, z0, z1, dd, ww, [round(v, 4) for v in fd])

    def front_face(self, ox, oy, dd, ww):
        """The face of a box tier that looks most toward the Mid camera."""
        best = None
        for nx, ny in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            wx, wy = self.ca * nx - self.sa * ny, self.sa * nx + self.ca * ny
            fx, fy = self.w(ox + nx * dd / 2, oy + ny * ww / 2)
            tx, ty = CAM[0] - fx, CAM[1] - fy
            s = (wx * tx + wy * ty) / (math.hypot(tx, ty) or 1.0)
            if best is None or s > best[0]:
                best = (s, nx, ny)
        _, nx, ny = best
        return {"n": (nx, ny), "t": (-ny, nx), "c": (ox + nx * dd / 2, oy + ny * ww / 2), "width": ww if nx else dd}

    def face_box(self, f, off, out, z0, z1, width, thick, kind, data):
        lx = f["c"][0] + f["t"][0] * off + f["n"][0] * (out + thick / 2)
        ly = f["c"][1] + f["t"][1] * off + f["n"][1] * (out + thick / 2)
        sx, sy = (thick, width) if f["n"][0] else (width, thick)
        self.add(kind, "box", lx, ly, z0, z1, sx, sy, data)

    def top_all(self):
        """Highest point of any part (masts, beacons, roof plant)."""
        return max((p["c"][2] + p["size"][2] / 2 for p in self.parts), default=self.height)

    def boxes(self, pad):
        """(cx, cy, angle, half_u, half_v, z0, z1) per tier, for traffic_lanes. pad >= 0: collision boxes,
        each reaching up to the tallest mast; pad < 0: occluders, shrunk (cylinders by their inscribed box)."""
        out = []
        top = self.top_all()
        for lx, ly, z0, z1, dd, ww, shape in self.tiers:
            x, y = self.w(lx, ly)
            k = 0.85 if (shape == "cyl" and pad < 0) else 1.0
            zt = max(z1, top) + pad if pad >= 0 else z1
            out.append([x, y, math.radians(self.yaw), dd / 2 * k + pad, ww / 2 * k + pad, -1.0, zt])
        return out


def beacon(t, rng, lx, ly, z, phase=None, blink=None):
    bc = S.CITY_BG["beacon"]
    bs = max(bc["min_size_m"], t.dist_cam * bc["size_per_m"])
    blink = (rng.random() < bc["blink_share"]) if blink is None else blink
    t.add("light", "box", lx, ly, z, z + bs, bs, bs, light(bc["color"], bc["intensity"], 1.0 if blink else 0.0,
                                                           rng.random() if phase is None else phase))


def roof(t, rng, b, ox, oy, dd, ww, top, force_mast=False):
    C = S.CITY_BG
    sc = min(2.5, max(0.6, min(dd, ww) / 25.0))
    for _ in range(rng.randint(0 if b["name"] == "Band4" else 1, 3)):
        px, py = dd * rng.uniform(0.18, 0.42), ww * rng.uniform(0.18, 0.42)
        t.add("plain", "box", ox + rng.uniform(-0.8, 0.8) * (dd - px) / 2, oy + rng.uniform(-0.8, 0.8) * (ww - py) / 2,
              top - 0.5, top + rng.uniform(2.5, 8.0) * sc, px, py)
    if force_mast or rng.random() < b["antenna_chance"]:
        for _ in range(rng.choice((1, 1, 2, 3))):
            mw = max(0.6, t.dist_cam * C["mast_width_per_m"])
            mh = min(70.0, max(8.0, rng.uniform(0.05, 0.15) * t.height))
            mx, my = ox + rng.uniform(-0.3, 0.3) * dd, oy + rng.uniform(-0.3, 0.3) * ww
            t.add("plain", "box", mx, my, top - 0.5, top + mh, mw, mw)
            beacon(t, rng, mx, my, top + mh)
    if rng.random() < b["beacon_chance"]:
        corner_beacons(t, rng, ox, oy, dd, ww, top)


def corner_beacons(t, rng, ox, oy, dd, ww, z):
    f = t.front_face(ox, oy, dd, ww)
    ph, bl = rng.random(), rng.random() < S.CITY_BG["beacon"]["blink_share"]
    inset = max(0.8, t.dist_cam / 500.0)
    for s in (-1, 1):
        lx = f["c"][0] + f["t"][0] * s * (f["width"] / 2 - inset) - f["n"][0] * inset
        ly = f["c"][1] + f["t"][1] * s * (f["width"] / 2 - inset) - f["n"][1] * inset
        beacon(t, rng, lx, ly, z, ph, bl)


def tier_fractions(rng, n, decay=0.78):
    w = [rng.uniform(0.8, 1.2) * decay ** i for i in range(n)]
    s = sum(w)
    return [v / s for v in w]


def build_body(t, rng, b, arche, w, d, h, z):
    """Window tiers + roof for one archetype, from height z (above any podium) to h."""
    near = b["name"] in ("Band1", "Band2", "Anchors")
    if arche == "round":
        r = min(w, d) / 2
        n = rng.randint(2, 3)
        rings = rng.random() < 0.4
        ring_col = rng.choice(((0.72, 0.84, 1.0), (1.0, 0.75, 0.42), (0.3, 0.95, 1.0)))
        for i, fr in enumerate(tier_fractions(rng, n)):
            z1 = z + (h - z) * fr if i < n - 1 else h
            t.tier("cyl", 0, 0, z, z1, 2 * r, 2 * r)
            if rings:
                zr = z + rng.uniform(6, 14)
                while zr < z1 - 4:
                    t.add("light", "cyl", 0, 0, zr, zr + 0.9, 2 * r + 0.7, 2 * r + 0.7, light(ring_col, 6.0))
                    zr += rng.uniform(18, 30)
            z = z1
            if i < n - 1:
                r *= rng.uniform(0.7, 0.88)
        roof(t, rng, b, 0, 0, 2 * r * 0.7, 2 * r * 0.7, h)
    elif arche == "twin":
        base = z + (h - z) * rng.uniform(0.18, 0.32)
        t.tier("box", 0, 0, z, base, d, w)
        ws = w * rng.uniform(0.38, 0.46)
        for side, hh in ((-1, h), (1, base + (h - base) * rng.uniform(0.6, 0.88))):
            oy, dd = side * (w / 2 - ws / 2), d * rng.uniform(0.8, 1.0)
            t.tier("box", 0, oy, base, hh, dd, ws)
            roof(t, rng, b, 0, oy, dd, ws, hh)
    elif arche == "crown":
        shaft = z + (h - z) * rng.uniform(0.74, 0.86)
        t.tier("box", 0, 0, z, shaft, d, w)
        c1 = shaft + (h - shaft) * 0.6
        if near:
            t.add("plain", "box", 0, 0, shaft - 0.6, shaft, d + 0.8, w + 0.8)
        t.tier("box", 0, 0, shaft, c1, d * 0.72, w * 0.72)
        t.tier("box", 0, 0, c1, h, d * 0.46, w * 0.46)
        if rng.random() < 0.5:
            corner_beacons(t, rng, 0, 0, d, w, shaft)
        roof(t, rng, b, 0, 0, d * 0.46, w * 0.46, h, force_mast=True)
    elif arche == "slab":
        t.tier("box", 0, 0, z, h, d, w)
        roof(t, rng, b, 0, 0, d, w, h)
    else:  # stepped
        n = rng.randint(*b["tiers"])
        ox = oy = 0.0
        dd, ww = d, w
        for i, fr in enumerate(tier_fractions(rng, n)):
            z1 = z + (h - z) * fr if i < n - 1 else h
            t.tier("box", ox, oy, z, z1, dd, ww)
            z = z1
            if i < n - 1 and rng.random() < b["setback_chance"]:
                if near:
                    t.add("plain", "box", ox, oy, z - 0.6, z, dd + 0.8, ww + 0.8)
                if rng.random() < 0.3:
                    corner_beacons(t, rng, ox, oy, dd, ww, z)
                nd, nw = dd * rng.uniform(0.6, 0.88), ww * rng.uniform(0.6, 0.88)
                ox += rng.uniform(-0.7, 0.7) * (dd - nd) / 2
                oy += rng.uniform(-0.7, 0.7) * (ww - nw) / 2
                dd, ww = nd, nw
        roof(t, rng, b, ox, oy, dd, ww, h)


def podium(t, rng, w, d, ph, signs=True):
    C = S.CITY_BG
    pd, pw = d + 2.4, w + 2.4
    t.tier("box", 0, 0, -1.0, ph, pd, pw, kind="podium")
    t.add("plain", "box", 0, 0, ph, ph + 0.5, pd + 2.0, pw + 2.0)  # canopy slab
    col = rng.choice(C["neon"]["colors"])
    if signs:
        f = t.front_face(0, 0, pd, pw)
        t.face_box(f, 0.0, 0.05, ph - 1.6, ph - 0.4, f["width"] * 0.7, 0.2, "light", light(col, C["neon"]["band_sign_intensity"]))
    return col, pd, pw


def neon(t, rng, b):
    C = S.CITY_BG
    for lx, ly, z0, z1, dd, ww, shape in t.tiers:
        if shape != "box" or z1 - z0 < 20:
            continue
        f = t.front_face(lx, ly, dd, ww)
        sw = min(rng.uniform(*C["neon"]["width_m"]), f["width"] * 0.3)
        sh = min(rng.uniform(*C["neon"]["height_m"]), (z1 - z0) * 0.6)
        zlo = max(z0 + 4, t.dist_cam * math.tan(math.radians(C["neon"]["min_elev_deg"])))
        if zlo > z1 - sh - 4:
            continue
        zb = rng.uniform(zlo, z1 - sh - 4)
        off = rng.uniform(-0.35, 0.35) * f["width"]
        t.face_box(f, off, 0.25, zb, zb + sh, sw, 0.4, "light",
                   light(rng.choice(C["neon"]["colors"]), C["neon"]["intensity"], 0.0, rng.random(), rng.uniform(*C["neon"]["pulse"])))
        return


def tower_data(rng, b, lit=None):
    C = S.CITY_BG
    return {"lit": max(0.02, min(0.95, (b["lit"] if lit is None else lit) + rng.uniform(-1, 1) * b["lit_spread"])),
            "warm": max(0.0, min(0.95, b["warm_share"] + rng.uniform(-0.12, 0.12))),
            "bright": rng.uniform(*C["brightness"]), "seed": rng.uniform(0, 97),
            "floor_h": rng.uniform(*b.get("floor_h_m", C["floor_h_m"])), "bay": rng.uniform(*b.get("bay_w_m", C["bay_w_m"]))}


# ---- Heights -----------------------------------------------------------------------------------
def vista_weight(az_cam):
    v = S.CITY_BG["vista"]
    return 1.0 - smoothstep(v["core_deg"], v["halfwidth_deg"], abs(wrap(az_cam - v["axis_deg"])))


def shape_height(rng, b, cx, cy, h_run, sight):
    """Run-off height outside the vista; inside it the top drops into the band's elevation range."""
    dc, az = cam_polar(cx, cy)
    if rng.random() < b["visible_top_share"]:
        h_out = dc * math.tan(math.radians(rng.uniform(*b["top_elev_deg"])))
    else:
        h_out = h_run
    hv = dc * math.tan(math.radians(rng.uniform(*b["vista_elev_deg"])))
    w = vista_weight(az)
    h = h_out + (min(h_out, hv) - h_out) * w
    h = max(h, dc * math.tan(math.radians(b["min_top_elev_deg"])), 30.0)
    cap = sight(cx, cy, dc, az)
    if cap is not None:
        h = min(h, dc * math.tan(math.radians(cap)))
    return h


# ---- Landmark ----------------------------------------------------------------------------------
def build_landmark(rng):
    L = S.CITY_BG["landmark"]
    a = math.radians(L["azimuth_deg"])
    cx, cy = L["distance_m"] * math.cos(a), L["distance_m"] * math.sin(a)
    t = Tower("Landmark", "Landmark", cx, cy, 0.0, {"lit": L["lit"], "warm": 0.6, "bright": 1.1, "seed": 51.0,
                                                    "floor_h": 3.8, "bay": 1.8})
    r, h = L["radius_m"], L["height_m"]
    t.tier("cyl", 0, 0, -1.0, 14.0, 3 * r, 3 * r)
    prof = [(14.0, 0.72 * h, r), (0.72 * h, 0.9 * h, 0.85 * r), (0.9 * h, h, 0.6 * r)]
    for z0, z1, rr in prof:
        t.tier("cyl", 0, 0, z0, z1, 2 * rr, 2 * rr)
    t.add("plain", "cyl", 0, 0, h, h + 6.0, 0.5 * r, 0.5 * r)
    t.add("plain", "box", 0, 0, h + 6.0, h + L["spire_m"], 1.2, 1.2)
    beacon(t, rng, 0, 0, h + L["spire_m"], blink=True)
    ring = light(L["ring_color"], L["ring_intensity"])
    sg = L["sign"]
    rs_sign = next(p[2] for p in prof if p[0] <= sg["z"] * h < p[1])
    sign_half = sg["width_r"] * rs_sign * sg["aspect"] / 2 + 2.0
    z = 30.0
    while z < 0.9 * h:
        rr = next(p[2] for p in prof if p[0] <= z < p[1])
        if abs(z + 0.75 - sg["z"] * h) < sign_half:  # no ring across the sign
            z += L["ring_every_m"]
            continue
        t.add("light", "cyl", 0, 0, z, z + 1.5, 2 * (rr + L["ring_out_m"]), 2 * (rr + L["ring_out_m"]), ring)
        z += L["ring_every_m"]
    # floating halos, each on four spokes
    n = L["halo_segments"]
    for frac, rmul in L["halos"]:
        hz, R = frac * h, rmul * r
        r0 = 0.8 * next(p[2] for p in prof if p[0] <= hz < p[1] + 1e-6)
        for i in range(n):
            phi = 2 * math.pi * i / n
            t.add("light", "box", R * math.cos(phi), R * math.sin(phi), hz, hz + 1.6, 2 * math.pi * R / n * 1.04, 1.6,
                  ring, yaw_off=math.degrees(phi) + 90.0)
        for k in range(4):
            phi = math.pi / 4 + k * math.pi / 2
            t.add("plain", "box", (r0 + R) / 2 * math.cos(phi), (r0 + R) / 2 * math.sin(phi), hz + 0.2, hz + 1.2, R - r0, 1.0,
                  yaw_off=math.degrees(phi))
    # vertical light strip on the side facing the Mid camera
    phi = math.atan2(CAM[1] - cy, CAM[0] - cx)
    t.add("light", "box", (r + 0.3) * math.cos(phi), (r + 0.3) * math.sin(phi), 0.3 * h, 0.68 * h, 0.6, 1.6,
          light(L["strip_color"], L["strip_intensity"], 0.0, 0.0, 0.15), yaw_off=math.degrees(phi))
    sg = L["sign"]  # a separate actor (setup_city_bg.build_signs): an additive plane facing the Mid camera
    zc = sg["z"] * h
    rs = next(p[2] for p in prof if p[0] <= zc < p[1])
    w = sg["width_r"] * rs
    nx, ny = math.cos(phi), math.sin(phi)
    t.signs = [{"name": sg["name"], "texture": sg["texture"], "intensity": sg["intensity"], "width": w, "height": w * sg["aspect"],
                "center": [cx + (rs + 0.8) * nx, cy + (rs + 0.8) * ny, zc], "normal": [nx, ny]}]
    return t


# ---- Layout ------------------------------------------------------------------------------------
def build_layout(log=print):
    C = S.CITY_BG
    rng = random.Random(C["seed"])
    with open(os.path.join(RAW, "city_manifest.json"), encoding="utf-8") as f:
        man = json.load(f)
    specs = {t["name"]: t for t in man["towers"]}
    # The city no longer bends round the traffic: traffic_plan.py plans its corridors around the city
    # (city first, then corridors). keepout.avoid_traffic True restores the old behaviour.
    routes_json = os.path.join(RAW, "traffic_routes.json")
    cars = CarPaths(routes_json if C["keepout"].get("avoid_traffic") else "")  # bands 1-2 and bridges keep clear of the air corridors
    ko = C["keepout"]
    occ = Occupancy()
    for name in C["heroes"]:
        t = specs[name]
        a = math.radians(t["azimuth"])
        occ.add(quad(t["distance"] * math.cos(a), t["distance"] * math.sin(a), t["azimuth"], t["depth"] + 3, t["width"] + 3, ko["hero_pad_m"]))
    v = man["viaduct"]
    vp = ko["viaduct_pad_m"]
    occ.add([(v["x0"] - vp, v["y0"] - vp), (v["x1"] + 200, v["y0"] - vp), (v["x1"] + 200, v["y1"] + vp), (v["x0"] - vp, v["y1"] + vp)])

    towers = []
    lm = build_landmark(rng)
    towers.append(lm)
    L = C["landmark"]
    lr = max(h[1] for h in L["halos"]) * L["radius_m"] + 4
    occ.add(quad(lm.cx, lm.cy, 0, 2 * lr, 2 * lr))
    lm_half = math.degrees(math.atan2(lr, lm.dist_cam)) + ko["sightline_margin_deg"]

    def sight(cx, cy, dc, az):
        """Elevation cap for towers in front of the landmark (low) and right behind it (just above the rail)."""
        da = abs(wrap(az - lm.az_cam))
        if dc < lm.dist_cam and da < lm_half:
            return ko["sightline_max_elev_deg"]
        if dc > lm.dist_cam and da < lm_half * ko["behind_width"]:
            return ko["behind_max_elev_deg"]
        return None

    # The ad towers in the vista: rebuilt on their old footprints, screens re-hosted unchanged
    b1 = dict(C["bands"]["Band1"], name="Anchors")
    screens, shop_lights = [], []
    for name in C["anchors"]:
        sp = specs[name]
        a = math.radians(sp["azimuth"])
        cx, cy = sp["distance"] * math.cos(a), sp["distance"] * math.sin(a)
        scr = [s for s in man["screens"] if s["name"].startswith(name + "_")]
        top_scr = max((s["center"][2] + s["height"] / 2 for s in scr), default=0.0)
        dc, az = cam_polar(cx, cy)
        vmid = sum(b1["vista_elev_deg"]) / 2
        h = sp["height"] + (min(sp["height"], dc * math.tan(math.radians(vmid))) - sp["height"]) * vista_weight(az)
        h = max(h, top_scr + C["anchor_clearance_m"])
        t = Tower(name, "Anchors", cx, cy, sp["azimuth"], tower_data(rng, b1))
        t.height = h
        ph = C["podium_h_m"]
        podium(t, rng, sp["width"], sp["depth"], ph, signs=False)
        zb = max(top_scr + 6.0, ph + 0.5 + (h - ph) * 0.45)
        t.tier("box", 0, 0, ph + 0.5, zb, sp["depth"], sp["width"])
        t.add("plain", "box", 0, 0, zb - 0.6, zb, sp["depth"] + 0.8, sp["width"] + 0.8)
        build_body(t, rng, dict(b1, tiers=(1, 3)), rng.choice(("stepped", "crown")), sp["width"] * 0.78, sp["depth"] * 0.8, h, zb)
        for s in scr:  # bezel behind the screen (the screen itself is a separate actor)
            n = s["normal"]
            fx, fy = s["center"][0] - n[0] * 0.45, s["center"][1] - n[1] * 0.45
            yaw = math.degrees(math.atan2(n[1], n[0]))
            lx, ly = fx + n[0] * 0.175, fy + n[1] * 0.175
            t.parts.append(part("plain", "box", lx, ly, s["center"][2] - s["height"] / 2 - 0.4, s["center"][2] + s["height"] / 2 + 0.4,
                                0.35, s["width"] + 0.8, yaw, None, "Anchors"))
            screens.append({"name": s["name"], "center": s["center"], "normal": n, "width": s["width"], "height": s["height"]})
        occ.add(quad(cx, cy, sp["azimuth"], sp["depth"] + 3, sp["width"] + 3, b1["pad_m"]))
        towers.append(t)

    # Bands
    arche_names, arche_w = zip(*C["archetypes"].items())
    stats = {}
    for bname, bcfg in C["bands"].items():
        b = dict(bcfg, name=bname)
        made = tries = 0
        target = b["count"] + b.get("vista_extra", 0)
        vs = C["vista"]
        while made < target and tries < target * 120:
            tries += 1
            dist = math.sqrt(rng.uniform(b["dist_m"][0] ** 2, b["dist_m"][1] ** 2))
            if made < b["count"]:
                az = rng.uniform(*C["azimuth_deg"])
                cx, cy = dist * math.cos(math.radians(az)), dist * math.sin(math.radians(az))
            else:  # inside the vista
                ac = math.radians(vs["axis_deg"] + rng.uniform(-0.8, 0.8) * vs["halfwidth_deg"])
                cx, cy = CAM[0] + dist * math.cos(ac), CAM[1] + dist * math.sin(ac)
                az = math.degrees(math.atan2(cy, cx))
            w = rng.uniform(*b["width_m"])
            d = rng.uniform(*b["width_m"]) * rng.uniform(0.75, 1.0)
            j = C["yaw_jitter_deg"]
            yaw = rng.uniform(-j, j) if rng.random() < C["grid_share"] else az + rng.uniform(-j, j)
            foot = (d + 2.4, w + 2.4) if b["podium"] else (d, w)
            q = quad(cx, cy, yaw, foot[0], foot[1], b["pad_m"])
            if occ.hits(q):
                continue
            h = shape_height(rng, b, cx, cy, rng.uniform(*b["height_m"]), sight)
            arche = rng.choices(arche_names, arche_w)[0]
            t = Tower(f"{bname}_{made:03d}", bname, cx, cy, yaw, tower_data(rng, b))
            t.height = h
            z = 0.0
            col = None
            if b["podium"]:
                col, _, _ = podium(t, rng, w, d, C["podium_h_m"])
                z = C["podium_h_m"] + 0.5
            build_body(t, rng, b, arche, w, d, h, z)
            if b["neon_chance"] and rng.random() < b["neon_chance"]:
                neon(t, rng, b)
            if cars.conflict_boxes(t.boxes(ko["car_clear_m"])):
                continue  # a flying-car lane passes too close (same boxes traffic_lanes plans around)
            if b.get("shop_lights") and col is not None:
                f = t.front_face(0, 0, foot[0], foot[1])
                lx, ly = f["c"][0] + f["n"][0] * 4.0, f["c"][1] + f["n"][1] * 4.0
                x, y = t.w(lx, ly)
                if math.hypot(x, y) <= C["shop_light"]["max_distance_m"]:
                    shop_lights.append({"name": t.name, "pos": [x, y, 3.0], "colour": list(col)})
            occ.add(q)
            towers.append(t)
            made += 1
        stats[bname] = {"made": made, "tries": tries}

    bridges, bridge_boxes = skybridges(rng, towers, cars)
    parts = [p for t in towers for p in t.parts] + bridges
    solid = [bx for t in towers for bx in t.boxes(0.0)] + bridge_boxes
    occl = [bx for t in towers for bx in t.boxes(-1.0)] + bridge_boxes
    groups = [t.group for t in towers for _ in t.tiers] + ["Details"] * len(bridge_boxes)  # per box, for traffic planning
    counts = {}
    for p in parts:
        k = (p["group"], p["kind"], p["shape"])
        counts[k] = counts.get(k, 0) + 1
    for bname, s in stats.items():
        hs = [t.height for t in towers if t.group == bname]
        log(f"  {bname}: {s['made']} towers ({s['tries']} tries), heights {min(hs):.0f}-{max(hs):.0f} m" if hs else f"  {bname}: none")
    log(f"  {len(towers)} towers incl. landmark + {len(C['anchors'])} anchors, {len(bridges) // 4} skybridges, {len(parts)} parts, "
        f"{len(screens)} screens, {len(shop_lights)} shop lights")
    return {"towers": [{"name": t.name, "group": t.group, "c": [t.cx, t.cy], "yaw": t.yaw, "height": t.height,
                        "dist_cam": t.dist_cam, "az_cam": t.az_cam} for t in towers],
            "parts": parts, "screens": screens, "signs": lm.signs, "shop_lights": shop_lights,
            "boxes": {"solid": solid, "occ": occl, "groups": groups},
            "landmark": {"center": [lm.cx, lm.cy], "radius": C["landmark"]["radius_m"], "height": C["landmark"]["height_m"]},
            "counts": {"|".join(k): v for k, v in sorted(counts.items())}}


def skybridges(rng, towers, cars):
    """Walkways between neighbouring band-1/2 towers, where the Mid camera sees them and no car flies."""
    C = S.CITY_BG
    sb = C["skybridges"]
    cand = [t for t in towers if t.group in ("Band1", "Band2", "Anchors") and t.tiers]
    pairs = []
    for i, a in enumerate(cand):
        for b in cand[i + 1:]:
            d = math.hypot(a.cx - b.cx, a.cy - b.cy)
            if not sb["pair_dist_m"][0] < d < sb["pair_dist_m"][1]:
                continue
            mx, my = (a.cx + b.cx) / 2, (a.cy + b.cy) / 2
            dc, az = cam_polar(mx, my)
            if abs(wrap(az - 35.8)) > sb["frame_deg"] or abs(a.dist_cam - b.dist_cam) > 0.8 * d:
                continue  # in the Mid frame, and spanning across the view rather than along it
            pairs.append((rng.random(), a, b, d, dc))
    pairs.sort(key=lambda p: p[0])
    out, used, boxes = [], {}, []
    others = [(t, t.boxes(0.5)) for t in towers]
    for _, a, b, d, dc in pairs:
        if len(out) // 4 >= sb["count"]:
            break
        if used.get(a.name, 0) >= 2 or used.get(b.name, 0) >= 2:
            continue
        zmax = min(a.tiers[0][3], b.tiers[0][3]) - 8.0
        zmin = max(20.0, dc * math.tan(math.radians(sb["min_elev_deg"])))
        if zmax <= zmin:
            continue
        z = rng.uniform(zmin, zmax)
        p0, p1 = (a.cx, a.cy, z + sb["height_m"] / 2), (b.cx, b.cy, z + sb["height_m"] / 2)
        yaw_r = math.atan2(b.cy - a.cy, b.cx - a.cx)
        box = [(a.cx + b.cx) / 2, (a.cy + b.cy) / 2, yaw_r, d / 2, sb["width_m"] / 2, z, z + sb["height_m"]]
        cc = C["keepout"]["car_clear_m"]
        if cars.conflict_boxes([[box[0], box[1], yaw_r, box[3] + cc, box[4] + cc, z - cc, z + sb["height_m"] + cc]]):
            continue
        blocked = False
        for t, bxs in others:
            if t is a or t is b:
                continue
            for k in range(1, 20):
                x, y = a.cx + (b.cx - a.cx) * k / 20, a.cy + (b.cy - a.cy) * k / 20
                for cx, cy, ang, hu, hv, z0, z1 in bxs:
                    ca, sa = math.cos(ang), math.sin(ang)
                    du, dv = (x - cx) * ca + (y - cy) * sa, -(x - cx) * sa + (y - cy) * ca
                    if abs(du) < hu + 3 and abs(dv) < hv + 3 and z0 < z + sb["height_m"] and z < z1:
                        blocked = True
                        break
                if blocked:
                    break
            if blocked:
                break
        if blocked:
            continue
        yaw = math.degrees(math.atan2(b.cy - a.cy, b.cx - a.cx))
        mx, my = (a.cx + b.cx) / 2, (a.cy + b.cy) / 2
        wv, hh = sb["width_m"], sb["height_m"]
        nx, ny = -math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
        out.append(part("plain", "box", mx, my, z, z + hh, d, wv, yaw, None, "Details"))
        glaze = light(sb["glaze_color"], sb["glaze_intensity"])
        for s in (-1, 1):
            out.append(part("light", "box", mx + nx * s * (wv / 2 + 0.06), my + ny * s * (wv / 2 + 0.06), z + 1.2, z + 2.6, d * 0.98, 0.12,
                            yaw, glaze, "Details"))
        out.append(part("light", "box", mx, my, z - 0.25, z, d * 0.98, 0.5, yaw, light(sb["strip_color"], sb["strip_intensity"]), "Details"))
        used[a.name] = used.get(a.name, 0) + 1
        used[b.name] = used.get(b.name, 0) + 1
        boxes.append(box)
    return out, boxes


if __name__ == "__main__":
    layout = build_layout()
    with open(os.path.join(RAW, "city_bg.json"), "w", encoding="utf-8") as f:
        json.dump(layout, f)
    for k, v in layout["counts"].items():
        print(f"    {k}: {v}")
    print("wrote", os.path.join(RAW, "city_bg.json"))
