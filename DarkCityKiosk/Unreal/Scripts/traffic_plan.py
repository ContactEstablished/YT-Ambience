"""Aerial traffic for the looping shot: corridors in altitude layers, then a per-variant schedule of
vehicle runs with their motion baked. Pure Python (no unreal), so it runs in Blender's python too:

    "C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe" Scripts/traffic_plan.py [--replan]

1. Corridors (cached in RawContent/traffic_routes.json; --replan searches again, a few minutes):
   traffic_lanes.make_routes per layer (low / mid / high, scene_config.TRAFFIC["layers"]) plus one
   hero route. Every corridor point records which sweep angles (every 2 deg) can see it.
2. Schedule (RawContent/traffic.json, from scene_config.VARIANT): runs along each corridor in both
   directions with randomised start times, quiet spells, vehicle type, speed, lane offset, altitude
   offset and light level, and quiet spells. A run starts and ends where the camera can't see at that
   moment (behind a tower, off frame, in the haze), so a vehicle can appear from any corridor point
   that is off screen right then, not only at a corridor's ends. No run crosses the loop seam (every
   variant starts and ends with the same empty sky, so variants splice). Runs keep apart in time and
   space.
3. Motion, baked per run: speed profile (cruise, or brake into an overshoot, settle back, hold,
   accelerate away), bank from the turn rate with lag, pitch from climb and acceleration, hover bob,
   yaw drift, a slow turn while a pod waits at its station, and for cargo lifters the container's
   pendulum sway (damped, driven by the lifter's acceleration) with the lifter leaning against it.
4. Runs are packed onto as few actors per type as possible (setup_traffic.py spawns them).
"""
import json
import math
import os
import random
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
import traffic_lanes as TL  # noqa: E402
import scene_config as S  # noqa: E402

K = TL.K
TR = S.TRAFFIC
STEP = TL.STEP_M
G = 9.81
ROUTES_JSON = os.path.join(TL.RAW, "traffic_routes.json")
OUT_JSON = os.path.join(TL.RAW, "traffic.json")
HALF_LEN = {"Courier": 0.8, "Taxi": 2.6, "Pod": 1.5, "Transit": 8.0, "Cargo": 5.5, "Hero": 3.6}
FINE = 1 / 48  # simulation step (s); keys are written every key_dt_s


def search_cfg(over):
    c = dict(TR["routes"])
    c.update(over)
    return c


def theta_at(t, loop_s):
    return -K.VIDEO_CAM["arc_deg"] * math.cos(2 * math.pi * t / loop_s)


GRID = [-46.0 + 2.0 * i for i in range(47)]  # sweep angles (deg) at which corridor visibility is cached
_BITS = {}


def view_bits(t, loop_s, margin_deg=2.0):
    """Grid bits within margin_deg of the camera's sweep angle at time t: a point seen from any of them
    counts as seen (conservative near the frame edges)."""
    key = (round(t, 2), loop_s)
    if key not in _BITS:
        th = theta_at(t, loop_s)
        b = 0
        for i, g in enumerate(GRID):
            if abs(g - th) <= margin_deg + 1e-9:
                b |= 1 << i
        _BITS[key] = b
    return _BITS[key]


# ---- 1. Corridors ------------------------------------------------------------------------------
def record(city, r, layer):
    """A corridor with, for every point, a bitmask of the sweep angles (GRID) that see it."""
    cams = [TL.camera(g) for g in GRID]
    vis = []
    for p in r["points"]:
        m = 0
        for k, c in enumerate(cams):
            if city.seen_by(c, p):
                m |= 1 << k
        vis.append(m)
    return {"layer": layer, "points": [[round(v, 3) for v in p] for p in r["points"]], "vis": vis,
            "score": round(r["score"], 1), "pass": [round(v, 2) for v in r["pass"]], "turn": r["turn"]}


def plan_routes(log=print):
    man = TL.load_city(ignore_groups=TR.get("plan_ignore_groups", ()))  # the near bands are laid out round the corridors later
    sep = TR["routes"]["route_separation_m"]
    kept, out = [], {"layers": {}}
    for name, over in TR["layers"].items():
        cfg = search_cfg(over)
        want = cfg["routes"]
        cfg["routes"] = want * 4  # extra candidates, then keep those clear of the earlier layers
        city, routes = TL.make_routes(man, cfg, log=log)
        keep = []
        for r in routes:
            if all(TL.path_dist(r["points"], k) > sep for k in kept):
                keep.append(record(city, r, name))
                kept.append(r["points"])
                if len(keep) == want:
                    break
        out["layers"][name] = keep
        log(f"traffic_plan: {name}: {len(keep)} corridors " + ", ".join(f"{len(k['points']) * STEP:.0f} m" for k in keep))
    out["hero"] = plan_hero(man, kept, log)
    with open(ROUTES_JSON, "w", encoding="utf-8") as f:
        json.dump(out, f)
    return out


def plan_hero(man, kept, log=print):
    """The hero's route: of the searched candidates, the route and shaft-of-light point with the best
    passes (continuous, central screen time; crossing the shaft near the middle of the frame)."""
    hs = search_cfg(TR["hero"]["search"])
    city, routes = TL.make_routes(man, hs, log=log)
    cam = TL.camera(0.0)["pos"]
    best = None
    for r in routes:  # it may share airspace with a corridor: the schedule keeps every other vehicle clear of it
        rec = record(city, r, "hero")
        cands = sorted(((bin(m).count("1"), i) for i, (p, m) in enumerate(zip(rec["points"], rec["vis"])) if math.dist(p, cam) < 105 and m),
                       reverse=True)
        if not cands:
            log("  hero candidate skipped: never seen within 105 m of the camera")
            continue
        for _, si in cands[:12:2]:  # judged for the final loop length (slow pan)
            opts = hero_options(rec, si, TR["hero"]["plan_loop_s"], random.Random(5), step=2.0)
            score = len(opts) * (1 + max((o[0] for o in opts), default=0.0))
            if opts and (best is None or score > best[0]):
                rec["shaft_index"] = si
                best = (score, dict(rec), len(opts))
    if best:
        log(f"traffic_plan: hero route {len(best[1]['points']) * STEP:.0f} m, shaft at {best[1]['points'][best[1]['shaft_index']]}, "
            f"{best[2]} workable passes")
        return best[1]
    log("traffic_plan: no hero route found")
    return None


def replan_hero(log=print):
    """Search only the hero route, in the city as built (after the corridors were laid out)."""
    with open(ROUTES_JSON, encoding="utf-8") as f:
        routes = json.load(f)
    kept = [r["points"] for recs in routes["layers"].values() for r in recs]
    routes["hero"] = plan_hero(TL.load_city(), kept, log)
    with open(ROUTES_JSON, "w", encoding="utf-8") as f:
        json.dump(routes, f)
    return routes


# ---- 2. Lanes and segments ---------------------------------------------------------------------
class Lane:
    def __init__(self, rec, reverse, name, loop_s):
        self.name, self.layer, self.reverse, self.loop_s = name, rec["layer"], reverse, loop_s
        self.pts = [tuple(p) for p in (rec["points"][::-1] if reverse else rec["points"])]
        self.vis = rec["vis"][::-1] if reverse else rec["vis"]
        self.cum = cumulative(self.pts)
        cam = TL.camera(0.0)["pos"]
        self.near = [1.0 / max(30.0, math.dist(p, cam)) for p in self.pts]  # on-screen size weight

    def seen(self, i, t):
        return bool(self.vis[max(0, min(len(self.vis) - 1, i))] & view_bits(t, self.loop_s))

    def segment(self, v, t, max_dur, rng, min_vis_s=1.5, must=None):
        """(spawn, despawn, seen points): the vehicle starts and ends somewhere the camera can't see at
        those moments (for the first/last part of its fade too) and is on screen in between. must: an
        index the run has to pass while on screen (the hero's shaft of light)."""
        fade, n = TR["fade_s"], len(self.pts)
        k = max(1, int(round(0.6 * fade * v / STEP)))
        need = max(3, int(min_vis_s * v / STEP))
        starts = [i for i in range(0, n - k - need) if not self.seen(i, t) and not self.seen(i + k, t + 0.6 * fade)]
        rng.shuffle(starts)
        found = []  # every workable (spawn, despawn), scored by how large the vehicle is while on screen
        for i0 in starts[:10]:
            seen, size = 0, 0.0
            for i in range(i0 + 1, n):
                ti = t + (self.cum[i] - self.cum[i0]) / v
                if ti - t > max_dur:
                    break
                if self.seen(i, ti):
                    seen += 1
                    size += self.near[i]
                    continue
                if seen >= need and i - k > i0 and not self.seen(i - k, ti - 0.6 * fade):
                    if must is None or (i0 < must < i and self.seen(must, t + (self.cum[must] - self.cum[i0]) / v)):
                        found.append((size * rng.uniform(0.8, 1.2), i0, i, seen))
        if not found:
            return None
        _, i0, i1, seen = max(found)
        return i0, i1, seen


def cumulative(pts):
    cum = [0.0]
    for p, q in zip(pts, pts[1:]):
        cum.append(cum[-1] + math.dist(p, q))
    return cum


def headings(pts):
    h = []
    for i in range(len(pts)):
        p, q = pts[max(0, i - 1)], pts[min(len(pts) - 1, i + 1)]
        h.append(math.atan2(q[1] - p[1], q[0] - p[0]))
    for i in range(1, len(h)):
        h[i] += round((h[i - 1] - h[i]) / (2 * math.pi)) * 2 * math.pi
    return h


class Path:
    """A lane's (offset) polyline with arc length and heading lookup."""

    def __init__(self, pts):
        self.pts, self.cum, self.head = pts, cumulative(pts), headings(pts)

    def at(self, s):
        cum = self.cum
        s = min(max(s, 0.0), cum[-1])
        lo, hi = 0, len(cum) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if cum[mid] <= s:
                lo = mid
            else:
                hi = mid
        f = (s - cum[lo]) / max(1e-9, cum[hi] - cum[lo])
        p = tuple(self.pts[lo][k] + (self.pts[hi][k] - self.pts[lo][k]) * f for k in range(3))
        return p, self.head[lo] + (self.head[hi] - self.head[lo]) * f, lo + f


# ---- 3. Motion ---------------------------------------------------------------------------------
def speed_profile(s0, s1, v, a, stop=None):
    """s(tau) and duration: cruise, or brake into an overshoot past the stop, settle back, hold, go."""
    if not stop:
        return (lambda tau: s0 + v * tau), (s1 - s0) / v, None
    ss, dl, hold = stop["s"], stop["overshoot"], stop["hold"]
    db = v * v / (2 * a)
    sb, td, ta = ss + dl - db, v / a, v / a
    tb = (sb - s0) / v
    w = 6.0 / min(hold, 1.6)
    s_go = ss + db
    dur = tb + td + hold + ta + (s1 - s_go) / v

    def s(tau):
        if tau <= tb:
            return s0 + v * tau
        u = tau - tb
        if u <= td:
            return sb + v * u - 0.5 * a * u * u
        u -= td
        if u <= hold:
            return ss + dl * (1 + w * u) * math.exp(-w * u)
        u -= hold
        if u <= ta:
            return ss + 0.5 * a * u * u
        return s_go + v * (u - ta)
    return s, dur, (tb + td, tb + td + hold)


def hero_profile(s0, s1, v, s_slow, dip):
    """Slow glide with an extra slow-down around the shaft of light."""
    tab, s, t = [(0.0, s0)], s0, 0.0
    while s < s1:
        vv = v * (1 - dip * math.exp(-((s - s_slow) / 40.0) ** 2))
        s += vv * FINE
        t += FINE
        tab.append((t, min(s, s1)))

    def fn(tau):
        i = min(len(tab) - 1, max(0, int(tau / FINE)))
        if i >= len(tab) - 1:
            return tab[-1][1]
        f = (tau - tab[i][0]) / FINE
        return tab[i][1] + (tab[i + 1][1] - tab[i][1]) * f
    return fn, t, None


def lag(prev, target, dt, tau):
    return prev + (target - prev) * (1 - math.exp(-dt / max(tau, 1e-3)))


def simulate(path, s_fn, dur, typ, cfg, rng, t0, key_dt, wait=None):
    """Keys [t, x, y, z, roll, pitch, yaw, ramp] (+ cargo container [t, pitch, roll]) for one run."""
    n = int(dur / FINE) + 1
    taus = [k * FINE for k in range(n)] + [dur]
    ss = [s_fn(t) for t in taus]
    vs = [(ss[min(len(ss) - 1, k + 1)] - ss[max(0, k - 1)]) / ((min(len(ss) - 1, k + 1) - max(0, k - 1)) * FINE) for k in range(len(ss))]
    acc = [(vs[min(len(vs) - 1, k + 1)] - vs[max(0, k - 1)]) / ((min(len(vs) - 1, k + 1) - max(0, k - 1)) * FINE) for k in range(len(vs))]
    look = [path.at(s) for s in ss]
    hd = [h for _, h, _ in look]
    bank_max, bank_tau = cfg["bank"]
    (amp_lo, amp_hi), (per_lo, per_hi) = cfg["hover"]
    amp, per, ph = rng.uniform(amp_lo, amp_hi), rng.uniform(per_lo, per_hi), rng.uniform(0, 2 * math.pi)
    yd, yph, yper = cfg.get("yaw_drift", 0.0), rng.uniform(0, 2 * math.pi), rng.uniform(5, 9)
    fade = TR["fade_s"]
    bank = pitch_acc = 0.0
    cargo = typ == "Cargo"
    if cargo:
        L, c = cfg["cable_m"], cfg["sway_damping"]
        th_p = th_r = om_p = om_r = 0.0
    keys, cont = [], []
    next_key = 0.0
    for k, tau in enumerate(taus):
        dt = FINE if k else 0.0
        (x, y, z), h, _ = look[k]
        kp, kn = max(0, k - 2), min(len(hd) - 1, k + 2)
        omega = (hd[kn] - hd[kp]) / max(1e-6, (kn - kp) * FINE)
        v = vs[k]
        target = -math.degrees(math.atan(v * omega / G))
        target = max(-bank_max, min(bank_max, target))
        bank = lag(bank, target, dt, bank_tau) if k else target
        pa = max(-4.0, min(4.0, -cfg["pitch_per_accel"] * acc[k]))
        pitch_acc = lag(pitch_acc, pa, dt, 0.6) if k else pa
        p2, _, _ = look[kn]
        p1, _, _ = look[kp]
        climb = math.degrees(math.atan2(p2[2] - p1[2], max(1e-6, math.hypot(p2[0] - p1[0], p2[1] - p1[1]))))
        yaw_off = yd * math.sin(2 * math.pi * tau / yper + yph)
        if wait and wait[0] <= tau <= wait[1]:  # a slow look round while waiting at the station
            u = (tau - wait[0]) / max(1e-6, wait[1] - wait[0])
            yaw_off += cfg["stop"].get("wait_yaw_deg", 0.0) * math.sin(math.pi * u) ** 2
        z += amp * math.sin(2 * math.pi * tau / per + ph)
        roll, pitch = bank, climb + pitch_acc
        if cargo and k:
            a_long, a_lat = acc[k], v * omega
            al_p = -(G / L) * th_p - c * om_p - a_long / L
            al_r = -(G / L) * th_r - c * om_r + a_lat / L
            om_p += al_p * dt
            om_r += al_r * dt
            th_p += om_p * dt
            th_r += om_r * dt
            roll -= cfg["compensate"] * math.degrees(th_r)
            pitch -= cfg["compensate"] * math.degrees(th_p)
        ramp = max(0.0, min(1.0, tau / fade, (dur - tau) / fade))
        if tau + 1e-9 >= next_key or k == len(taus) - 1:
            keys.append([round(t0 + tau, 4), round(x, 3), round(y, 3), round(z, 3), round(roll, 3), round(pitch, 3),
                         round(-math.degrees(h) - yaw_off, 3), round(ramp, 4)])
            if cargo:
                cont.append([round(t0 + tau, 4), round(math.degrees(th_p) - pitch, 3), round(math.degrees(th_r) - roll, 3)])
            next_key += key_dt
    return keys, (cont if cargo else None)


# ---- 4. Schedule -------------------------------------------------------------------------------
def nearest_wall(p, boxes):
    best = 1e9
    for cx, cy, a, hu, hv, z0, z1 in boxes:
        if not z0 < p[2] < z1:
            continue
        dx, dy = p[0] - cx, p[1] - cy
        if dx * dx + dy * dy > (hu + hv + 40) ** 2:
            continue
        ca, sa = math.cos(a), math.sin(a)
        u, w = abs(dx * ca + dy * sa) - hu, abs(-dx * sa + dy * ca) - hv
        best = min(best, math.hypot(max(u, 0.0), max(w, 0.0)))
    return best


def train_box(t):
    """The train's body at time t as (x0, x1, y0, y1, z0, z1), from its keys in scene_config.TRAIN
    (nose x, linear between keys; the cars trail along -X) and the railway in city_manifest.json."""
    global _RAIL
    if _RAIL is None:
        import city_config as CC
        with open(os.path.join(TL.RAW, "city_manifest.json"), encoding="utf-8") as f:
            r = json.load(f)["railway"]
        c = CC.TRAIN
        _RAIL = (r["y"], r["rail_top"], c["cars"] * c["car_len"] + (c["cars"] - 1) * c["gap"], c["width"], c["roof_z"])
    y, top, length, width, roof = _RAIL
    keys = S.TRAIN["keys"]
    if t <= keys[0][0]:
        x = keys[0][1]
    elif t >= keys[-1][0]:
        x = keys[-1][1]
    else:
        for (ta, xa), (tb, xb) in zip(keys, keys[1:]):
            if ta <= t <= tb:
                x = xa + (xb - xa) * (t - ta) / max(1e-9, tb - ta)
                break
    return (x - length, x, y - width / 2, y + width / 2, top, top + roof)


_RAIL = None


def train_gap(p, t):
    """Distance from p to the train's body at time t."""
    x0, x1, y0, y1, z0, z1 = train_box(t)
    return math.dist(p, (min(max(p[0], x0), x1), min(max(p[1], y0), y1), min(max(p[2], z0), z1)))


def hero_options(rec, si_fwd, loop_s, rng, step=0.5, strict=None, train=False):
    """Workable hero passes: (score, start, reverse, s(t), duration, path, seconds seen). It starts and
    ends unseen and is on screen when it crosses the shaft of light. strict (default for loops of 2 min
    or more, where the camera pans slowly): mostly central, continuous, crossing the shaft mid-frame.
    Short test loops pan ~9 deg/s at the middle of the sweep, so they only ask for a shorter look."""
    strict = loop_s >= 120 if strict is None else strict
    hc, margin = TR["hero"], TR["schedule"]["loop_margin_s"]
    out = []
    for rev in (False, True):
        lane = Lane(rec, rev, "hero", loop_s)
        si = si_fwd if not rev else len(rec["points"]) - 1 - si_fwd
        path = Path(lane.pts)
        for k in range(int((loop_s - 2 * margin) / step)):
            t0 = margin + step * k
            seg = lane.segment(hc["speed"] * (1 - hc["slow_at_shaft"] / 2), t0, loop_s - margin - t0, rng,
                               hc["min_visible_s"] if strict else 3.0, must=si)
            if not seg:
                continue
            i0, i1, _ = seg
            s_fn, dur, _ = hero_profile(path.cum[i0], path.cum[i1], hc["speed"], path.cum[si], hc["slow_at_shaft"])
            if t0 + dur > loop_s - margin or lane.seen(i1, t0 + dur):
                continue
            # screen time: continuous, and near the middle of the frame (not skimming an edge)
            vis = cont = run = central = 0.0
            shaft_ok, shaft_done, near_train = False, False, False
            s_sh = path.cum[si]
            for j in range(0, int(dur / 0.25)):
                tau = j * 0.25
                p, _, idx = path.at(s_fn(tau))
                if train and train_gap(p, t0 + tau) < TR["hero"]["train_clearance_m"]:
                    near_train = True  # never over or beside the passing train
                    break
                seen = lane.seen(int(round(idx)), t0 + tau)
                q = TL.project(TL.camera(theta_at(t0 + tau, loop_s)), p) if seen else None
                mid = q is not None and abs(q[0]) < 0.36 and abs(q[1]) < 0.24
                vis += 0.25 * seen
                run = run + 0.25 if seen else 0.0
                cont = max(cont, run)
                central += 0.25 * mid
                if not shaft_done and s_fn(tau) >= s_sh:  # the moment it crosses the shaft
                    shaft_done = True
                    shaft_ok = q is not None and (abs(q[0]) < 0.3 or not strict)
            need = (hc["min_visible_s"], 4.0, 3.0) if strict else (3.0, 2.5, 1.0)
            if not near_train and shaft_ok and vis >= need[0] and cont >= need[1] and central >= need[2]:
                out.append((central + 0.5 * cont, t0, rev, s_fn, dur, path, vis))
    return out


def scale_of(typ):
    return TR["hero"].get("scale", 1.0) if typ == "Hero" else TR["types"][typ].get("scale", 1.0)


def poisson(rng, lam):
    lim, k, p = math.exp(-lam), 0, 1.0
    while True:
        p *= rng.random()
        if p <= lim:
            return k
        k += 1


def schedule(routes, variant, loop_s, log=print):
    rng = random.Random(variant["traffic_seed"])
    sc, types = TR["schedule"], TR["types"]
    margin, key_dt, fade = sc["loop_margin_s"], sc["key_dt_s"], TR["fade_s"]
    city = TL.City(TL.load_city(), TR["routes"])  # collision checks for the offset lanes; walls for stations
    lanes = [Lane(rec, rev, f"{layer}{i}{'r' if rev else 'f'}", loop_s)
             for layer, recs in routes["layers"].items() for i, rec in enumerate(recs) for rev in (False, True)]
    # quiet spells: most traffic holds off for a while, so the sky is never continuously busy
    quiet = []
    for _ in range(max(1, round(loop_s / 60))):
        length = min(rng.uniform(*sc["lull_s"]), 0.25 * loop_s)
        s = rng.uniform(margin, loop_s - margin - length)
        quiet.append((s, s + length))
    runs = []

    def samples_of(keys):
        return {round(k[0] * 4) / 4: (k[1], k[2], k[3]) for k in keys}

    def clear(new, typ, lane_name, t0, t1):
        for r in runs:
            if r["t1"] < t0 or r["t0"] > t1:
                continue
            gap = max(types.get(typ, {}).get("min_gap_m", 10), types.get(r["type"], {}).get("min_gap_m", 10)) if r["lane"][:-1] == lane_name[:-1] \
                else HALF_LEN[typ] * scale_of(typ) + HALF_LEN[r["type"]] * scale_of(r["type"]) + sc["pass_clearance_m"]
            for t, p in new.items():
                q = r["samples"].get(t)
                if q and math.dist(p, q) < gap:
                    return False
        return True

    # The hero first, so everything else keeps out of its way
    hero_rec = routes.get("hero")
    if variant.get("hero") and hero_rec:
        hc = TR["hero"]
        opts = hero_options(hero_rec, hero_rec["shaft_index"], loop_s, rng, train=variant.get("train", True))
        opts.sort(key=lambda o: -o[0])
        best = rng.choice(opts[:3]) if opts else None  # one of the best few: variants differ
        if best:
            _, t0, rev, s_fn, dur, path, vis = best
            keys, _ = simulate(path, s_fn, dur, "Hero", dict(hc, yaw_drift=0.0, stop=None), rng, t0, key_dt)
            runs.append({"type": "Hero", "t0": t0, "t1": t0 + dur, "keys": keys, "container": None, "lane": "hero_",
                         "samples": samples_of(keys), "light_scale": 1.0})
            log(f"traffic_plan: hero at {t0:.1f}-{t0 + dur:.1f} s, ~{vis:.1f} s on screen")
        else:
            log("traffic_plan: (no hero pass fits this loop)")

    dens = variant.get("density", 1.0)
    rej = {"segment": 0, "blocked": 0, "spacing": 0, "quiet": 0, "train": 0, "stop_no_spot": 0, "stop_no_exit": 0}
    has_train = variant.get("train", True)
    for lane in lanes:
        want = poisson(rng, sc["rate_per_min"][lane.layer] * dens * loop_s / 60.0)
        mix = [(name, t["layers"][lane.layer]) for name, t in types.items() if lane.layer in t["layers"]]
        made = 0
        for _ in range(want * 8):
            if made >= want:
                break
            t = rng.uniform(margin, loop_s - margin - 2.0)
            if any(a <= t <= b for a, b in quiet) and rng.random() < 0.85:
                rej["quiet"] += 1
                continue
            typ = rng.choices([m[0] for m in mix], [m[1] for m in mix])[0]
            cfg = types[typ]
            v = rng.uniform(*cfg["speed"])
            seg = lane.segment(v, t, loop_s - margin - t, rng)
            if not seg:
                rej["segment"] += 1
                continue
            i0, i1, _ = seg
            side, up = rng.choice(TR["slots"])
            jx, jz = sc["offset_jitter_m"]
            pts = TL.offset_path(lane.pts, side + rng.uniform(-jx, jx), up + rng.uniform(-jz, jz))
            if any(city.blocked(q, tight=True) for q in pts[i0:i1 + 1]):
                rej["blocked"] += 1
                continue
            path = Path(pts)
            s0, s1 = path.cum[i0], path.cum[i1]
            stop = None
            st = cfg.get("stop")
            if st and rng.random() < st["chance"]:
                hold = rng.uniform(*st["hold_s"])
                db = v * v / (2 * cfg["accel"])
                lo, hi = s0 + v * fade + db + 2, s1 - 4  # the exit can move further on (below)
                cand = [i for i in range(i0, i1 + 1) if lo < path.cum[i] < hi
                        and lane.seen(i, t + (path.cum[i] - s0) / v) and lane.seen(i, t + (path.cum[i] - s0) / v + hold / 2)]
                if not cand:
                    rej["stop_no_spot"] += 1
                if cand:
                    if st.get("station"):  # wait beside a building
                        near = [x for x in ((nearest_wall(pts[i], city.occ), i) for i in cand[::3]) if x[0] < 25]
                        idx = min(near)[1] if near else rng.choice(cand)
                    else:
                        idx = rng.choice(cand[len(cand) // 5: max(len(cand) // 5 + 1, 4 * len(cand) // 5)])
                    stop = {"s": path.cum[idx], "overshoot": rng.uniform(*st["overshoot_m"]), "hold": hold}
            k = max(1, int(round(0.6 * fade * v / STEP)))
            if stop:  # the hold delays the exit: find a point further on that is unseen at the later moment
                stop["hold"] = min(stop["hold"], loop_s - margin - t - (s1 - s0) / v - 6.0)
                delta = (speed_profile(s0, s1, v, cfg["accel"], stop)[1] - (s1 - s0) / v) if stop["hold"] >= 1.0 else None
                found = None
                if delta is not None:
                    for j in range(i1, len(path.pts)):
                        tj = t + (path.cum[j] - s0) / v + delta
                        if tj > loop_s - margin:
                            break
                        if path.cum[j] >= stop["s"] + db + v * fade and not lane.seen(j, tj) and not lane.seen(max(i0, j - k), tj - 0.6 * fade):
                            found = j
                            break
                if found is None:
                    rej["stop_no_exit"] += 1
                    stop = None  # no unseen exit in time: fly straight through
                else:
                    i1, s1 = found, path.cum[found]
            s_fn, dur, wait = speed_profile(s0, s1, v, cfg["accel"], stop)
            if t + dur > loop_s - margin:
                continue
            keys, cont = simulate(path, s_fn, dur, typ, cfg, rng, t, key_dt, wait)
            if has_train and any(train_gap(k[1:4], k[0]) < HALF_LEN[typ] * scale_of(typ) + 4.0 for k in keys[::3]):
                rej["train"] += 1  # would skim the passing train
                continue
            smp = samples_of(keys)
            if not clear(smp, typ, lane.name, t, t + dur):
                rej["spacing"] += 1
                continue
            runs.append({"type": typ, "t0": t, "t1": t + dur, "keys": keys, "container": cont, "lane": lane.name,
                         "samples": smp, "light_scale": rng.uniform(0.8, 1.2), "stop": bool(stop)})
            made += 1

    # Pack runs onto actors (a type's actor is free again two fades after its last run)
    runs.sort(key=lambda r: r["t0"])
    actors = []
    for r in runs:
        free = [a for a in actors if a["type"] == r["type"] and a["runs"][-1]["t1"] + 2 * fade < r["t0"]]
        if free:
            a = free[0]
        else:
            n = sum(1 for a in actors if a["type"] == r["type"])
            a = {"label": f"Veh_{r['type']}_{n:02d}", "type": r["type"], "scale": scale_of(r["type"]),
                 "mesh": TR["hero"]["mesh"] if r["type"] == "Hero" else types[r["type"]]["mesh"], "runs": []}
            actors.append(a)
        a["runs"].append({k: r[k] for k in ("t0", "t1", "keys", "container", "lane", "light_scale")})
    counts = {}
    for r in runs:
        counts[r["type"]] = counts.get(r["type"], 0) + 1
    log(f"traffic_plan: variant {variant['name']} (seed {variant['traffic_seed']}): {len(runs)} runs "
        + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())) + f"; {len(actors)} actors; "
        f"{sum(1 for r in runs if r.get('stop'))} with stops; quiet {', '.join(f'{a:.0f}-{b:.0f} s' for a, b in quiet)}; rejected {rej}")
    shaft = None
    if hero_rec:
        p = hero_rec["points"][hero_rec["shaft_index"]]
        shaft = {"target": p, "pos": [p[0] + 8.0, p[1] + 6.0, p[2] + TR["hero"]["shaft"]["height_m"]]}
    return {"variant": variant, "loop_s": loop_s, "actors": actors, "hero_shaft": shaft, "quiet": quiet}


def remask(log=print):
    """Recompute every corridor's visibility (and the hero's shaft of light) against the city as it is now:
    setup_city_bg.py calls this after rebuilding the city round the corridors."""
    if not os.path.exists(ROUTES_JSON):
        return None
    with open(ROUTES_JSON, encoding="utf-8") as f:
        routes = json.load(f)
    man = TL.load_city()
    for name, recs in routes["layers"].items():
        city = TL.City(man, search_cfg(TR["layers"][name]))
        for i, rec in enumerate(recs):
            pts = [tuple(p) for p in rec["points"]]
            recs[i] = dict(rec, vis=record(city, {"points": pts, "score": rec["score"], "pass": rec["pass"], "turn": rec["turn"]}, name)["vis"])
    h = routes.get("hero")
    if h:
        city = TL.City(man, search_cfg(TR["hero"]["search"]))
        h["vis"] = record(city, {"points": [tuple(p) for p in h["points"]], "score": h["score"], "pass": h["pass"], "turn": h["turn"]}, "hero")["vis"]
        cam = TL.camera(0.0)["pos"]
        cands = sorted(((bin(m).count("1"), i) for i, (p, m) in enumerate(zip(h["points"], h["vis"])) if math.dist(p, cam) < 105 and m), reverse=True)
        best = None
        for _, si in cands[:12:2]:
            opts = hero_options(h, si, TR["hero"]["plan_loop_s"], random.Random(5), step=2.0)
            score = len(opts) * (1 + max((o[0] for o in opts), default=0.0))
            if opts and (best is None or score > best[0]):
                best = (score, si, len(opts))
        if best:
            h["shaft_index"] = best[1]
            log(f"traffic_plan: hero shaft at {h['points'][best[1]]} ({best[2]} workable passes)")
        else:
            log("traffic_plan: !! the hero route has no workable pass in this city (re-plan)")
    with open(ROUTES_JSON, "w", encoding="utf-8") as f:
        json.dump(routes, f)
    seen = sum(1 for recs in routes["layers"].values() for r in recs for m in r["vis"] if m)
    total = sum(len(r["vis"]) for recs in routes["layers"].values() for r in recs)
    log(f"traffic_plan: corridor visibility refreshed ({seen}/{total} points seen from some angle)")
    return routes


def main(replan=False, log=print):
    if replan or not os.path.exists(ROUTES_JSON):
        routes = plan_routes(log)
    else:
        with open(ROUTES_JSON, encoding="utf-8") as f:
            routes = json.load(f)
    plan = schedule(routes, S.VARIANT, S.SWEEP["seconds"], log)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(plan, f)
    return plan


if __name__ == "__main__":
    if "--replan-hero" in sys.argv:
        replan_hero()
        main()
    elif "--remask" in sys.argv:
        remask()
    else:
        main("--replan" in sys.argv)
