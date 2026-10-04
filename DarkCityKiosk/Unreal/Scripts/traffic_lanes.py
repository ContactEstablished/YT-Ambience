"""Flight-lane search for the flying traffic. Pure Python (no unreal), so it also runs in
Blender's bundled python for quick experiments:

    "C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe" Scripts/traffic_lanes.py

A route is two straight legs joined by one smooth turn at a pass point the camera can see
(a straight lane is a turn of 0). Each leg runs out to a point the camera never sees: behind
a tower (occluded from every camera position along the orbit), off the edge of every frame,
or out in the haze. The whole route must clear every tower, the landmark and the viaduct.
Routes are ranked by how many metres are on screen and unoccluded, so the cars fly where
they will be seen (not behind the kiosk, which hides the far end of the street).
Positions are in the Blender kiosk frame (metres).
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


# ---- Boxes: (cx, cy, angle, half_u, half_v, z0, z1) in a frame rotated by angle ---------------
def tower_box(t, pad):
    a = math.radians(t["azimuth"])
    return (t["distance"] * math.cos(a), t["distance"] * math.sin(a), a, t["depth"] / 2 + pad, t["width"] / 2 + pad, -1.0, t["height"] + pad)


def axis_box(x0, x1, y0, y1, z0, z1):
    return ((x0 + x1) / 2, (y0 + y1) / 2, 0.0, (x1 - x0) / 2, (y1 - y0) / 2, z0, z1)


def inside(p, b):
    cx, cy, a, hu, hv, z0, z1 = b
    if not z0 < p[2] < z1:
        return False
    dx, dy = p[0] - cx, p[1] - cy
    ca, sa = math.cos(a), math.sin(a)
    return abs(dx * ca + dy * sa) < hu and abs(-dx * sa + dy * ca) < hv


def segment_hits(p, q, b):
    """Slab test of segment p->q against an oriented box."""
    cx, cy, a, hu, hv, z0, z1 = b
    ca, sa = math.cos(a), math.sin(a)
    pu, pv = (p[0] - cx) * ca + (p[1] - cy) * sa, -(p[0] - cx) * sa + (p[1] - cy) * ca
    qu, qv = (q[0] - cx) * ca + (q[1] - cy) * sa, -(q[0] - cx) * sa + (q[1] - cy) * ca
    t0, t1 = 0.0, 1.0
    for s, e, lo, hi in ((pu, qu, -hu, hu), (pv, qv, -hv, hv), (p[2], q[2], z0, z1)):
        d = e - s
        if abs(d) < 1e-9:
            if not lo < s < hi:
                return False
            continue
        ta, tb = (lo - s) / d, (hi - s) / d
        if ta > tb:
            ta, tb = tb, ta
        t0, t1 = max(t0, ta), min(t1, tb)
        if t0 > t1:
            return False
    return True


class City:
    def __init__(self, manifest, cfg):
        self.cfg = cfg
        pad = cfg["collision_pad_m"]
        r, v, lm = manifest["railway"], manifest["viaduct"], manifest["landmark"]
        # collision: padded towers, the landmark (as a box around its bulb), the railway
        self.solid, self.solid_tight = ([tower_box(t, pd) for t in manifest["towers"]] for pd in (pad, cfg["car_clearance_m"]))
        for solids, pd in ((self.solid, pad), (self.solid_tight, cfg["car_clearance_m"])):
            lr = lm["radius"] * 1.6 + pd
            solids.append(axis_box(lm["center"][0] - lr, lm["center"][0] + lr, lm["center"][1] - lr, lm["center"][1] + lr, -1.0, lm["height"] + 60))
            solids.append(axis_box(r["x0"] - pd, r["x1"] + pd, v["y0"] - pd, v["y1"] + pd, -1.0, r["rail_top"] + 6))
        # occluders: towers shrunk a little (a near miss must not count as hidden), the kiosk, the deck
        self.occ = [tower_box(t, -1.0) for t in manifest["towers"]]
        self.occ.append(axis_box(lm["center"][0] - lm["radius"], lm["center"][0] + lm["radius"], lm["center"][1] - lm["radius"],
                                 lm["center"][1] + lm["radius"], -1.0, lm["height"]))
        self.occ.append(axis_box(K.CANOPY_X0, K.CANOPY_X1, K.CANOPY_Y0, K.CANOPY_Y1, 0.0, K.CANOPY_TOP + 0.6))
        self.occ.append(axis_box(r["x0"], r["x1"], v["y0"] + 0.3, v["y1"] - 0.3, v["deck_z"] - 1.6, v["deck_z"] + 1.0))
        # the instanced city background (load_city): tier, roof and skybridge boxes
        ex = manifest.get("extra_boxes")
        if ex:
            for solids, pd in ((self.solid, pad), (self.solid_tight, cfg["car_clearance_m"])):
                solids.extend((b[0], b[1], b[2], b[3] + pd, b[4] + pd, b[5], b[6] + pd) for b in ex["solid"])
            self.occ.extend(tuple(b) for b in ex["occ"])
        self.occ_r = [math.hypot(b[3], b[4]) for b in self.occ]
        self.cams = [camera(th) for th in cfg["camera_samples_deg"]]

    def blocked(self, p, tight=False):
        return any(inside(p, b) for b in (self.solid_tight if tight else self.solid))

    def occluded(self, cam, p):
        # cheap circle reject first: the segment must pass within a box's bounding radius
        cx0, cy0 = cam["pos"][0], cam["pos"][1]
        dx, dy = p[0] - cx0, p[1] - cy0
        L2 = dx * dx + dy * dy or 1e-9
        for b, rr in zip(self.occ, self.occ_r):
            t = max(0.0, min(1.0, ((b[0] - cx0) * dx + (b[1] - cy0) * dy) / L2))
            ex, ey = cx0 + dx * t - b[0], cy0 + dy * t - b[1]
            if ex * ex + ey * ey > rr * rr:
                continue
            if segment_hits(cam["pos"], p, b):
                return True
        return False

    def seen_by(self, cam, p):
        """Visible from this camera pose: in frame, within fog range and unoccluded."""
        if math.dist(cam["pos"], p) > self.cfg["fog_hide_m"]:
            return False
        if not in_frame(cam, p, self.cfg["frame_margin"]):
            return False
        return not self.occluded(cam, p)

    def hidden(self, p):
        return not any(self.seen_by(c, p) for c in self.cams)

    def visibility(self, p):
        """Fraction of camera poses that see p, weighted down with distance (small, fogged)."""
        n = sum(1 for c in self.cams if self.seen_by(c, p))
        if not n:
            return 0.0
        d = math.dist(self.cams[len(self.cams) // 2]["pos"], p)
        near, far = self.cfg["full_weight_within_m"], self.cfg["fog_hide_m"]
        return n / len(self.cams) * max(0.15, min(1.0, 1.0 - (d - near) / (far - near)))

    def walk(self, p, d):
        """From p along unit vector d until the car has been hidden for hide_margin_m.
        Returns the end point, or None if the run hits something while it can still be seen."""
        step, need, reach = 3.0, self.cfg["hide_margin_m"], self.cfg["max_reach_m"]
        hid, s = 0.0, 0.0
        while s < reach:
            s += step
            q = (p[0] + d[0] * s, p[1] + d[1] * s, p[2] + d[2] * s)
            if q[2] < self.cfg["min_altitude_m"]:
                return None
            if self.blocked(q):
                return None
            if self.hidden(q):
                hid += step
                if hid >= need:
                    return q
            else:
                hid = 0.0
        return None

    def path_clear(self, pts, tight=False):
        """Every point clears the city and both ends are hidden (pts are STEP_M apart). Routes are
        searched with the full pad; a car's offset copy only needs car_clearance_m."""
        return not any(self.blocked(q, tight) for q in pts) and self.hidden(pts[0]) and self.hidden(pts[-1])

    def score(self, pts):
        """Metres of the path on screen (weighted by how many camera poses see it, and distance)."""
        return sum(self.visibility(q) for q in pts[::2]) * 2 * STEP_M


# ---- Camera (mirrors dck.orbit_pose; Blender frame) -----------------------------------------
def camera(theta_deg):
    hc, vc = K.HERO_CAM, K.VIDEO_CAM
    px, py = K.ORBIT_PIVOT
    t = math.radians(theta_deg)
    dx, dy = (hc["pos_xy"][0] - px) * vc["distance_scale"], (hc["pos_xy"][1] - py) * vc["distance_scale"]
    pos = (px + dx * math.cos(t) - dy * math.sin(t), py + dx * math.sin(t) + dy * math.cos(t), vc["height_m"])
    h, pt = math.radians(hc["heading_deg"] + theta_deg), math.radians(vc["pitch_deg"])
    fwd = (math.cos(h) * math.cos(pt), math.sin(h) * math.cos(pt), math.sin(pt))
    right = (math.sin(h), -math.cos(h), 0.0)
    up = (right[1] * fwd[2] - right[2] * fwd[1], right[2] * fwd[0] - right[0] * fwd[2], right[0] * fwd[1] - right[1] * fwd[0])
    return {"pos": pos, "fwd": fwd, "right": right, "up": up, "f": vc["lens_mm"] / vc["sensor_w_mm"]}


def project(cam, p):
    """Normalised screen coords: x in [-0.5, 0.5] across the frame, y in [-0.28, 0.28] (16:9)."""
    v = [p[i] - cam["pos"][i] for i in range(3)]
    z = sum(v[i] * cam["fwd"][i] for i in range(3))
    if z <= 0.5:
        return None
    return (cam["f"] * sum(v[i] * cam["right"][i] for i in range(3)) / z, cam["f"] * sum(v[i] * cam["up"][i] for i in range(3)) / z)


def in_frame(cam, p, margin):
    s = project(cam, p)
    return s is not None and abs(s[0]) < 0.5 + margin and abs(s[1]) < 0.5 * 9 / 16 + margin


STEP_M = 2.0  # path sample spacing


def unit(h, climb):
    return (math.cos(h) * math.cos(climb), math.sin(h) * math.cos(climb), math.sin(climb))


def resample(pts, step=STEP_M):
    """Evenly spaced points along a polyline."""
    out, carry = [pts[0]], 0.0
    for p, q in zip(pts, pts[1:]):
        L = math.dist(p, q)
        if L < 1e-9:
            continue
        s = step - carry
        while s <= L:
            out.append(tuple(p[i] + (q[i] - p[i]) * s / L for i in range(3)))
            s += step
        carry = L - (s - step)
    if math.dist(out[-1], pts[-1]) > 0.2 * step:
        out.append(pts[-1])
    return out


def route_path(a, p, b, radius):
    """a -> p -> b with the corner at p rounded off by a quadratic Bezier, every STEP_M."""
    la, lb = math.dist(a, p), math.dist(p, b)
    r = min(radius, 0.45 * la, 0.45 * lb)
    p1 = tuple(p[i] + (a[i] - p[i]) * r / la for i in range(3))
    p2 = tuple(p[i] + (b[i] - p[i]) * r / lb for i in range(3))
    curve = [tuple((1 - t) ** 2 * p1[i] + 2 * (1 - t) * t * p[i] + t * t * p2[i] for i in range(3)) for t in (k / 24 for k in range(25))]
    return resample([a] + curve + [b])


def offset_path(pts, side, up):
    """Shift a path sideways (left of travel, metres) and up, along its local horizontal normal."""
    out = []
    for i, p in enumerate(pts):
        q0, q1 = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        tx, ty = q1[0] - q0[0], q1[1] - q0[1]
        n = math.hypot(tx, ty) or 1.0
        out.append((p[0] - ty / n * side, p[1] + tx / n * side, p[2] + up))
    return out


def path_dist(p, q):
    return min(math.dist(a, b) for a in p[::3] for b in q[::3])


def load_city(ignore_groups=()):
    """The city the cars fly through: city_manifest.json, or, once setup_city_bg.py has built the
    instanced background (RawContent/city_bg.json), the kept hero towers plus its boxes and landmark.
    ignore_groups: leave out those background groups (corridor planning ignores the near bands, which
    are then laid out round the corridors)."""
    with open(os.path.join(RAW, "city_manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    bg = os.path.join(RAW, "city_bg.json")
    if os.path.exists(bg):
        import scene_config as S
        with open(bg, encoding="utf-8") as f:
            layout = json.load(f)
        heroes = S.CITY_BG["heroes"]
        bx = layout["boxes"]
        if ignore_groups and "groups" in bx:
            keep = [i for i, g in enumerate(bx["groups"]) if g not in ignore_groups]
            bx = {"solid": [bx["solid"][i] for i in keep], "occ": [bx["occ"][i] for i in keep]}
        manifest = dict(manifest, towers=[t for t in manifest["towers"] if t["name"] in heroes], landmark=layout["landmark"],
                        extra_boxes=bx)
    return manifest


def make_routes(manifest, cfg, log=print):
    city = City(manifest, cfg)
    rng = random.Random(cfg["seed"])
    cands = []
    for _ in range(cfg["tries"]):
        d = rng.uniform(*cfg["pass_distance_m"])
        az = math.radians(rng.uniform(*cfg["pass_azimuth_deg"]))
        elev = math.radians(rng.uniform(*cfg["pass_elevation_deg"]))
        p = (d * math.cos(az), d * math.sin(az), max(cfg["min_altitude_m"], d * math.tan(elev)))
        if city.blocked(p) or not city.visibility(p):
            continue
        h1 = rng.uniform(0.0, 2 * math.pi)
        c1, c2 = (rng.uniform(-1, 1) * math.radians(cfg["max_climb_deg"]) for _ in range(2))
        u1 = unit(h1, c1)
        a = city.walk(p, (-u1[0], -u1[1], -u1[2]))
        if not a:
            continue
        best = None
        for turn in cfg["turns_deg"]:
            b = city.walk(p, unit(h1 + math.radians(turn), c2))
            if not b:
                continue
            pts = route_path(a, p, b, cfg["turn_radius_m"])
            if not city.path_clear(pts):
                continue
            sc = city.score(pts)
            if not best or sc > best["score"]:
                best = {"points": pts, "pass": p, "score": sc, "heading": math.degrees(h1) % 360, "turn": turn}
        if best and best["score"] >= cfg["min_visible_m"]:
            cands.append(best)
    cands.sort(key=lambda r: -r["score"])
    routes = []
    for c in cands:
        if all(path_dist(c["points"], r["points"]) > cfg["route_separation_m"] for r in routes):
            routes.append(c)
            if len(routes) == cfg["routes"]:
                break
    log(f"traffic_lanes: {len(cands)} candidate routes from {cfg['tries']} tries, kept {len(routes)}")
    return city, routes


def describe(route):
    p = route["pass"]
    return (f"passes d={math.hypot(p[0], p[1]):.0f} m az={math.degrees(math.atan2(p[1], p[0])):.0f} z={p[2]:.0f} m, heading {route['heading']:.0f}, "
            f"turn {route['turn']:+d}, length {len(route['points']) * STEP_M:.0f} m, on screen ~{route['score']:.0f} m")


if __name__ == "__main__":
    import scene_config as S
    _, routes = make_routes(load_city(), S.TRAFFIC["routes"])
    for i, r in enumerate(routes):
        print(f"  route {i}: {describe(r)}")
