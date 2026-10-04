"""Walker paths for the umbrella crowd. Pure Python + numpy, run offline with Blender's python:

    "C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe" Scripts/crowd_paths.py

Writes RawContent/crowd_plan.json for setup_crowd.py / make_sweep.py.

A walker follows a path (two straight legs and a rounded turn) at its walk speed, once per loop.
A dark figure against the glowing mist stays visible far away, so the haze can't hide anyone
appearing: every walker must appear and disappear where the camera can't see them AT THAT
MOMENT of the sweep (behind the kiosk, a viaduct pier or a tower corner, or off frame). The
camera pose is known at every time, so the search picks each walker's path, direction and
start time together. Walkers keep >= min_gap_m apart while both are out.
Positions are in the Blender kiosk frame (metres).
"""
import json
import math
import os
import random
import sys

import numpy as np

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(os.path.dirname(SCRIPTS_DIR), "RawContent")
BLENDER_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(SCRIPTS_DIR)), "Blender", "scripts")
for p in (SCRIPTS_DIR, BLENDER_SCRIPTS):
    if p not in sys.path:
        sys.path.insert(0, p)
import kiosk_config as K  # noqa: E402
import scene_config as S  # noqa: E402
import traffic_lanes as TL  # noqa: E402

C = S.CROWD
LOOP = S.SWEEP["seconds"]
DT = 0.5  # visibility time step (s)
SPACING = 0.5  # path sample spacing (m)
NB = int(round(LOOP / DT))


# ---- World ------------------------------------------------------------------------------------
def boxes(manifest):
    """(solid 2D rects for walking, occluder 3D boxes for hiding), as (cx, cy, angle, hu, hv, z0, z1)."""
    pad = C["tower_pad_m"]
    solid = [TL.tower_box(t, pad) for t in manifest["towers"]]
    occ = [TL.tower_box(t, -0.3) for t in manifest["towers"]]
    kx0, kx1, ky0, ky1 = C["kiosk_zone"]
    solid.append(TL.axis_box(kx0, kx1, ky0, ky1, -1, 10))
    occ.append(TL.axis_box(-K.BODY_W / 2, K.BODY_W / 2, -K.BODY_D / 2, K.BODY_D / 2, 0.0, K.BODY_TOP))  # body
    occ.append(TL.axis_box(K.CANOPY_X0, K.CANOPY_X1, K.CANOPY_Y0, K.CANOPY_Y1, K.BODY_TOP, K.CANOPY_TOP + 0.6))  # canopy + roof kit
    for x, y, half, h in manifest.get("viaduct_piers", []):
        solid.append(TL.axis_box(x - half - C["pier_pad_m"], x + half + C["pier_pad_m"], y - half - C["pier_pad_m"], y + half + C["pier_pad_m"], -1, h))
        occ.append(TL.axis_box(x - 0.7, x + 0.7, y - 0.7, y + 0.7, 0.0, h))
        occ.append(TL.axis_box(x - 1.2, x + 1.2, y - 1.2, y + 1.2, 0.0, 0.35))  # footing
    for st in C["standing"]:
        sx, sy = st["pos"]
        solid.append(TL.axis_box(sx - 0.7, sx + 0.7, sy - 0.7, sy + 0.7, -1, 3))
    return solid, np.array(occ, dtype=np.float64)


def cams():
    """Camera pose at every DT bucket of the loop (mirrors dck.sweep_theta)."""
    a = K.VIDEO_CAM["arc_deg"]
    return [TL.camera(-a * math.cos(2 * math.pi * k * DT / LOOP)) for k in range(NB)]


def arc_points():
    return [TL.camera(th)["pos"][:2] for th in np.linspace(-K.VIDEO_CAM["arc_deg"], K.VIDEO_CAM["arc_deg"], 46)]


def seen(cam, pts, occ):
    """pts (M,3) -> bool (M,): in frame and not occluded, for one camera pose."""
    c = np.array(cam["pos"])
    v = pts - c
    z = v @ np.array(cam["fwd"])
    x = cam["f"] * (v @ np.array(cam["right"])) / np.maximum(z, 1e-3)
    y = cam["f"] * (v @ np.array(cam["up"])) / np.maximum(z, 1e-3)
    m = C["frame_margin"]
    inf = (z > 0.3) & (np.abs(x) < 0.5 + m) & (np.abs(y) < 0.28125 + m)
    if not inf.any():
        return inf
    # slab test of every segment cam->pt against every occluder (M, B)
    cx, cy, ang, hu, hv, z0, z1 = (occ[:, i][None, :] for i in range(7))
    ca, sa = np.cos(ang), np.sin(ang)
    px, py, pz = c[0], c[1], c[2]
    qx, qy, qz = pts[:, 0:1], pts[:, 1:2], pts[:, 2:3]
    pu, pv = (px - cx) * ca + (py - cy) * sa, -(px - cx) * sa + (py - cy) * ca
    qu, qv = (qx - cx) * ca + (qy - cy) * sa, -(qx - cx) * sa + (qy - cy) * ca
    t0 = np.zeros(qu.shape)
    t1 = np.ones(qu.shape) * 0.999  # stop short of the point itself
    for s, e, lo, hi in ((pu, qu, -hu, hu), (pv, qv, -hv, hv), (pz + 0 * qz, qz, z0, z1)):
        d = e - s
        dd = np.where(np.abs(d) < 1e-9, 1e-9, d)
        ta, tb = (lo - s) / dd, (hi - s) / dd
        lo_t, hi_t = np.minimum(ta, tb), np.maximum(ta, tb)
        flat = np.abs(d) < 1e-9
        inside = (s > lo) & (s < hi)
        lo_t = np.where(flat, np.where(inside, -np.inf, np.inf), lo_t)
        hi_t = np.where(flat, np.where(inside, np.inf, -np.inf), hi_t)
        t0, t1 = np.maximum(t0, lo_t), np.minimum(t1, hi_t)
    blocked = (t0 <= t1).any(axis=1)
    return inf & ~blocked


def visibility(path, poses, occ):
    """hidden (N, NB) bool and seen-weight (N, NB) for a person at each path point and time."""
    P = np.array(path)
    N = len(P)
    hs = C["heights_m"]
    pts = np.concatenate([np.column_stack([P, np.full(N, h)]) for h in hs])
    vis = np.zeros((N, NB), dtype=bool)
    for k, cam in enumerate(poses):
        vis[:, k] = seen(cam, pts, occ).reshape(len(hs), N).any(axis=0)
    d = np.array([[math.dist(cam["pos"][:2], p) for cam in poses] for p in P])
    near, far = C["weight_band_m"]
    w = np.clip(np.minimum(d / near, 1.0) * np.clip(1.0 - (d - far) / far, 0.3, 1.0), 0.3, 1.0)
    return ~vis, vis * w


# ---- Paths ------------------------------------------------------------------------------------
def blocked(p, solid, arc):
    if math.hypot(*p) > C["max_radius_m"]:
        return True
    if any(TL.inside((p[0], p[1], 0.0), b) for b in solid):
        return True
    return min(math.dist(p, a) for a in arc) < C["camera_keepout_m"]


def leg(p, h, solid, arc):
    out = []
    for k in range(1, int(C["leg_max_m"] / SPACING) + 1):
        q = (p[0] + math.cos(h) * k * SPACING, p[1] + math.sin(h) * k * SPACING)
        if blocked(q, solid, arc):
            break
        out.append(q)
    return out


def make_path(p, h1, turn, solid, arc):
    back = leg(p, h1 + math.pi, solid, arc)
    fwd = leg(p, h1 + math.radians(turn), solid, arc)
    if len(back) < 4 or len(fwd) < 4:
        return None
    a, b = back[-1], fwd[-1]
    pts = TL.route_path((a[0], a[1], 0.0), (p[0], p[1], 0.0), (b[0], b[1], 0.0), C["corner_radius_m"])
    pts = [q[:2] for q in TL.resample(pts, SPACING)]
    if any(blocked(q, solid, arc) for q in pts[::2]):
        return None
    return pts


def best_timing(hidden, weight, v):
    """Best (score, i0, s, i1, nb) for a walker at v m/s along the path: appears hidden at point i0
    at bucket s, disappears hidden at i1 after nb buckets."""
    N = hidden.shape[0]
    step = v * DT / SPACING  # path points per bucket
    min_b, max_b = int(C["min_visible_s"] / DT), int(C["max_run_s"] / DT)
    hid3 = hidden & np.roll(hidden, 1, axis=1) & np.roll(hidden, -1, axis=1)  # hidden for +-1 bucket
    best = None
    for i0 in range(0, N - 8, 2):
        for s in np.nonzero(hid3[i0])[0]:
            score = 0.0
            for b in range(1, max_b + 1):
                idx = int(round(i0 + b * step))
                if idx >= N:
                    break
                k = (s + b) % NB
                score += weight[idx, k] * DT
                if b >= min_b and hid3[idx, k] and score > C["min_visible_s"] * 0.5:
                    if not best or score > best[0]:
                        best = (score, i0, int(s), idx, b)
    return best


def positions(w, poses_t):
    """Walker position at each DT bucket of the loop (None when not out)."""
    out = [None] * NB
    step = w["speed"] * DT / SPACING
    for b in range(w["buckets"] + 1):
        k = (w["start_bucket"] + b) % NB
        out[k] = w["path"][min(len(w["path"]) - 1, int(round(b * step)))]
    return out


def plan(manifest, log=print):
    rng = random.Random(C["seed"])
    solid, occ = boxes(manifest)
    poses = cams()
    arc = arc_points()
    cands = []
    for _ in range(C["tries"]):
        d = rng.uniform(*C["pass_distance_m"])
        az = math.radians(rng.uniform(*C["pass_azimuth_deg"]))
        p = (d * math.cos(az), d * math.sin(az))
        if blocked(p, solid, arc):
            continue
        h1 = rng.uniform(0, 2 * math.pi)
        path = make_path(p, h1, rng.choice(C["turns_deg"]), solid, arc)
        if not path:
            continue
        rate = rng.uniform(*C["rate_range"])
        v = C["walk_speed"] * rate
        for pth in (path, path[::-1]):
            hidden, weight = visibility(pth, poses, occ)
            t = best_timing(hidden, weight, v)
            if t:
                score, i0, s, i1, nb = t
                cands.append({"path": [list(map(lambda x: round(x, 3), q)) for q in pth[i0:i1 + 1]], "speed": v, "rate": rate,
                              "start_bucket": s, "buckets": nb, "score": score})
    cands.sort(key=lambda c: -c["score"])
    chosen = []
    for c in cands:
        pc = positions(c, poses)
        ok = True
        for o in chosen:
            po = o["_pos"]
            for k in range(NB):
                if pc[k] is not None and po[k] is not None and math.dist(pc[k], po[k]) < C["min_gap_m"]:
                    ok = False
                    break
            if not ok:
                break
            # no conga lines: a second walker on nearly the same path must be well apart in time
            if math.dist(c["path"][0], o["path"][0]) < 3 and math.dist(c["path"][-1], o["path"][-1]) < 3:
                ok = False
                break
        if ok:
            c["_pos"] = pc
            chosen.append(c)
            if len(chosen) == C["walkers"]:
                break
    log(f"crowd_paths: {len(cands)} candidate walks, chose {len(chosen)}")
    for c in chosen:
        c.pop("_pos")
        c["start_s"] = c["start_bucket"] * DT
        c["travel_s"] = c["buckets"] * DT
    return chosen


if __name__ == "__main__":
    with open(os.path.join(RAW, "city_manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    walkers = plan(manifest)
    for i, w in enumerate(walkers):
        a, b = w["path"][0], w["path"][-1]
        print(f"  walker {i:2d}: {len(w['path']) * SPACING:5.1f} m from ({a[0]:6.1f},{a[1]:6.1f}) to ({b[0]:6.1f},{b[1]:6.1f}), "
              f"out at {w['start_s']:4.1f} s for {w['travel_s']:4.1f} s, {w['speed']:.2f} m/s, on screen ~{w['score']:.1f} s")
    with open(os.path.join(RAW, "crowd_plan.json"), "w", encoding="utf-8") as f:
        json.dump({"loop_s": LOOP, "spacing_m": SPACING, "walkers": walkers, "standing": C["standing"]}, f, indent=1)
