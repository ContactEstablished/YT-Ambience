"""Creates CAM_Sweep and LS_Sweep: a ping-pong orbit (A -> B -> A) around the kiosk.
Arc, length and height come from scene_config.SWEEP; the reference angle is the middle.

The loop is frames [0, seconds * FPS) (the playback range). Every track also runs on for SWEEP["tail_s"] past the
loop end, keyed as the loop's own first moments (prompt 10), so a render of [0, loop + tail) can be crossfaded into
the loop's start (encode_loop.mjs) and the rain, which never repeats, flows across the seam.

    node Scripts/ue.mjs Scripts/make_sweep.py
"""
import importlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402

dck = importlib.reload(dck)
import scene_config as S  # noqa: E402

S = importlib.reload(S)
import unreal  # noqa: E402

sw = dict(S.SWEEP, **dck.K.VIDEO_CAM)
dck.ensure_map()
unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()

loc, rot = dck.orbit_pose(-sw["arc_deg"], sw["height_m"], sw["distance_scale"], sw["pitch_deg"])
cam = dck.get_or_spawn(unreal.CineCameraActor, "CAM_Sweep", loc, rot, folder="Cameras")
dck.setup_cine_camera(cam)

folder, name = dck.SEQUENCE.rsplit("/", 1)
if unreal.EditorAssetLibrary.does_asset_exist(dck.SEQUENCE):
    unreal.EditorAssetLibrary.delete_asset(dck.SEQUENCE)
dck.ensure_dir(folder)
seq = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
frames = int(sw["seconds"] * dck.FPS)
tail = int(round(sw.get("tail_s", 0.0) * dck.FPS))  # frames past the loop end, keyed as the loop's first moments
frames_all, T_all = frames + tail, sw["seconds"] + tail / dck.FPS
seq.set_display_rate(unreal.FrameRate(dck.FPS, 1))
seq.set_playback_start(0)
seq.set_playback_end(frames)

binding = seq.add_possessable(cam)
track = binding.add_track(unreal.MovieScene3DTransformTrack)
section = track.add_section()
section.set_range(0, frames_all)
ch = section.get_all_channels()  # loc xyz, rot xyz (roll, pitch, yaw), scale xyz
step = sw["key_every_s"]
n = int(round(sw["seconds"] / step))
n_all = int(math.ceil(T_all / step - 1e-9))  # keys on into the tail (sweep_theta is periodic)
for k in range(n_all + 1):
    t = k * step
    f = unreal.FrameNumber(int(round(t * dck.FPS)))
    theta = dck.sweep_theta(t, sw["seconds"], sw["arc_deg"])
    loc, rot = dck.orbit_pose(theta, sw["height_m"], sw["distance_scale"], sw["pitch_deg"])
    ch[0].add_key(f, loc.x)
    ch[1].add_key(f, loc.y)
    ch[2].add_key(f, loc.z)
    ch[4].add_key(f, rot.pitch)
    ch[5].add_key(f, rot.yaw)
ch[3].add_key(unreal.FrameNumber(0), 0.0)
for c in ch[6:9]:
    c.add_key(unreal.FrameNumber(0), 1.0)

# Mist waves: fog density + volumetric extinction rise and fall a whole number of times per loop.
mw = S.MIST_WAVES
fog = dck.find_actor("HeightFog")
fog_binding = seq.add_possessable(fog.get_component_by_class(unreal.ExponentialHeightFogComponent))
for prop, (lo, hi) in (("FogDensity", mw["fog_density"]), ("VolumetricFogExtinctionScale", mw["volumetric_extinction"])):
    tr = fog_binding.add_track(unreal.MovieSceneFloatTrack)
    tr.set_property_name_and_path(prop, prop)
    sec = tr.add_section()
    sec.set_range(0, frames_all)
    c = sec.get_all_channels()[0]
    for k in range(n_all + 1):
        t = k * step
        w = (0.5 - 0.5 * math.cos(2.0 * math.pi * mw["cycles"] * t / sw["seconds"])) ** mw["power"]
        c.add_key(unreal.FrameNumber(int(round(t * dck.FPS))), lo + (hi - lo) * w)
tr = fog_binding.add_track(unreal.MovieSceneColorTrack)
tr.set_property_name_and_path("VolumetricFogEmissive", "VolumetricFogEmissive")
sec = tr.add_section()
sec.set_range(0, frames_all)
rgba = sec.get_all_channels()
lo, hi = mw["volumetric_emissive"]
for k in range(n_all + 1):
    t = k * step
    w = (0.5 - 0.5 * math.cos(2.0 * math.pi * mw["cycles"] * t / sw["seconds"])) ** mw["power"]
    f = unreal.FrameNumber(int(round(t * dck.FPS)))
    for i in range(3):
        rgba[i].add_key(f, lo[i] + (hi[i] - lo[i]) * w)
    rgba[3].add_key(f, 1.0)

# The train: one run per loop along the railway into tower RightA (linear between keys).
train = dck.find_actor("Train")
if train:
    import json
    with open(os.path.join(dck.RAW, "city_manifest.json"), encoding="utf-8") as f:
        rail = json.load(f)["railway"]
    tb = seq.add_possessable(train)
    tt = tb.add_track(unreal.MovieScene3DTransformTrack)
    tsec = tt.add_section()
    tsec.set_range(0, frames_all)
    tch = tsec.get_all_channels()
    lin = unreal.MovieSceneKeyInterpolation.LINEAR
    # VARIANT["train"] False: the train stays parked off screen (left of the frame) all loop
    train_keys = S.TRAIN["keys"] if S.VARIANT.get("train", True) else [(0.0, S.TRAIN["keys"][0][1]), (sw["seconds"], S.TRAIN["keys"][0][1])]

    def train_x(t):
        for (ta, xa), (tb, xb) in zip(train_keys, train_keys[1:]):
            if ta <= t <= tb:
                return xa + (xb - xa) * (t - ta) / max(tb - ta, 1e-9)
        return train_keys[-1][1]
    # (frame, sub-frame, x): the loop's keys, then the tail: the train is back at its start (hidden: parked off screen)
    # from the loop end on. The jump sits in the last tick before the end, after any temporal sample of the last frame.
    tkeys = [(int(round(t * dck.FPS)), 0.0, x) for t, x in train_keys if t < sw["seconds"]]
    if tail:
        tkeys.append((frames - 1, 0.999, train_x(sw["seconds"])))
        tkeys += [(frames + int(round(t * dck.FPS)), 0.0, x) for t, x in train_keys if t * dck.FPS < tail]
        tkeys.append((frames_all, 0.0, train_x(T_all - sw["seconds"])))
    else:
        tkeys.append((frames, 0.0, train_x(sw["seconds"])))
    for f, sub, x in tkeys:
        loc = dck.to_ue(x, rail["y"], rail["rail_top"])
        for c, val in zip(tch[0:3], (loc.x, loc.y, loc.z)):
            c.add_key(unreal.FrameNumber(f), val, sub_frame=sub, interpolation=lin)
    for c in tch[3:6]:
        c.add_key(unreal.FrameNumber(0), 0.0)
    for c in tch[6:9]:
        c.add_key(unreal.FrameNumber(0), 1.0)

# Flying traffic (traffic.json from traffic_plan.py via setup_traffic.py): every run is baked,
# keys every few frames (position, rotation, scale ramp, light intensity, a cargo container's sway).
# Between runs a vehicle waits far below the city at zero scale with its lights off. No run crosses
# the seam, and frame 0 == frame end (parked at the first run's start), so every loop variant splices.
traffic_path = os.path.join(dck.RAW, "traffic.json")
if os.path.exists(traffic_path):
    import json
    with open(traffic_path, encoding="utf-8") as f:
        plan = json.load(f)
    T_loop, eps = sw["seconds"], 1.0 / dck.FPS
    if abs(plan.get("loop_s", T_loop) - T_loop) > 1e-6:
        print(f"  !! traffic.json was planned for a {plan['loop_s']} s loop; this sequence is {T_loop} s (re-run setup_traffic.py)")
    lin = unreal.MovieSceneKeyInterpolation.LINEAR
    scale0 = S.TRAFFIC["scale"]

    def fr(t):
        return unreal.FrameNumber(int(round(t * dck.FPS)))

    for a in plan.get("actors", []):
        actor = dck.find_actor(a["label"])
        if not actor or not a["runs"]:
            continue
        rows = []  # (t, x, y, z, roll, pitch, yaw, ramp, light_scale)

        def parked(k, t):
            return (t, k[1], k[2], -400.0, k[4], k[5], k[6], 0.0, 0.0)
        first = a["runs"][0]["keys"][0]
        rows.append(parked(first, 0.0))
        for run in a["runs"]:
            ks = run["keys"]
            rows.append(parked(ks[0], ks[0][0] - eps))
            rows += [tuple(k) + (run["light_scale"],) for k in ks]
            rows.append(parked(ks[-1], ks[-1][0] + eps))
        rows.append(parked(first, T_loop))
        for run in a["runs"]:  # the tail: runs that start in the loop's first tail_s start again past the end
            ks = run["keys"]
            if ks[0][0] < T_all - T_loop:
                rows.append(parked(ks[0], T_loop + ks[0][0] - eps))
                rows += [(k[0] + T_loop,) + tuple(k[1:]) + (run["light_scale"],) for k in ks]
                rows.append(parked(ks[-1], T_loop + ks[-1][0] + eps))
        if not any(run["keys"][0][0] < T_all - T_loop < run["keys"][-1][0] for run in a["runs"]):
            rows.append(parked(first, T_all))
        rows.sort(key=lambda r: r[0])
        seen, uniq = set(), []
        for r in rows:  # one key per frame (one past the tail's end is kept, so a run in progress there interpolates)
            f = int(round(r[0] * dck.FPS))
            if f not in seen and 0 <= f <= frames_all + dck.FPS:
                seen.add(f)
                uniq.append(r)
        b = seq.add_possessable(actor)
        tr = b.add_track(unreal.MovieScene3DTransformTrack)
        sec = tr.add_section()
        sec.set_range(0, frames_all)
        ch = sec.get_all_channels()
        for r in uniq:
            loc = dck.to_ue(r[1], r[2], r[3])
            scl = scale0 * a.get("scale", 1.0) * max(0.02, r[7])
            for c, val in zip(ch, (loc.x, loc.y, loc.z, r[4], r[5], r[6], scl, scl, scl)):
                c.add_key(fr(r[0]), val, interpolation=lin)
        for L in a.get("lights", []):  # light intensity follows the ramp
            la = dck.find_actor(L["label"])
            if not la:
                continue
            lb = seq.add_possessable(la.get_component_by_class(getattr(unreal, L["class"])))
            lt = lb.add_track(unreal.MovieSceneFloatTrack)
            lt.set_property_name_and_path("Intensity", "Intensity")
            ls = lt.add_section()
            ls.set_range(0, frames_all)
            lc = ls.get_all_channels()[0]
            for r in uniq:
                lc.add_key(fr(r[0]), L["cd"] * r[8] * r[7], interpolation=lin)
        if a.get("container"):  # the hanging container: its sway relative to the lifter
            ca = dck.find_actor(a["container"])
            if ca:
                cb = seq.add_possessable(ca)
                ct = cb.add_track(unreal.MovieScene3DTransformTrack)
                cs = ct.add_section()
                cs.set_range(0, frames_all)
                cch = cs.get_all_channels()
                rel = a.get("container_offset_cm", [0.0, 0.0, -125.0])
                sway = [(0.0, 0.0, 0.0), (T_loop, 0.0, 0.0), (T_all, 0.0, 0.0)]
                for run in a["runs"]:
                    c = run.get("container") or []
                    for shift in (0.0, T_loop):  # and again in the tail when the run starts in the loop's first tail_s
                        if c and (shift == 0.0 or c[0][0] < T_all - T_loop):
                            sway += [(c[0][0] + shift - eps, 0.0, 0.0)] + [(x[0] + shift,) + tuple(x[1:]) for x in c] + [(c[-1][0] + shift + eps, 0.0, 0.0)]
                done = set()
                for t, p, rl in sorted(sway):
                    f = int(round(t * dck.FPS))
                    if f in done or not 0 <= f <= frames_all + dck.FPS:
                        continue
                    done.add(f)
                    for c, val in zip(cch, (rel[0], rel[1], rel[2], rl, p, 0.0, 1.0, 1.0, 1.0)):
                        c.add_key(fr(t), val, interpolation=lin)

# Umbrella crowd (crowd.json from setup_crowd.py): walkers follow their paths once per loop,
# appearing and disappearing where the camera can't see them, waiting far below the city in
# between; the walk clip restarts each run at the walker's play rate. Standing people idle all
# loop at a rate that fits a whole number of cycles. A run that crosses the loop seam is split
# in two with the clip offset carried over, so frame 0 == frame end.
crowd_path = os.path.join(dck.RAW, "crowd.json")
if os.path.exists(crowd_path):
    import json
    with open(crowd_path, encoding="utf-8") as f:
        crowd = json.load(f)
    T_loop, eps, KEY_DT = sw["seconds"], 1.0 / dck.FPS, 0.5
    tick = seq.get_tick_resolution()
    tps = tick.numerator / tick.denominator
    lin = unreal.MovieSceneKeyInterpolation.LINEAR

    def fr(t):
        return unreal.FrameNumber(int(round(t * dck.FPS)))

    def clip(track, anim, t0, t1, anim_start_s, rate):
        sec = track.add_section()
        prm = sec.get_editor_property("params")
        prm.set_editor_property("animation", anim)
        pr = unreal.MovieSceneTimeWarpVariant()  # 5.8: play rate is a time-warp variant
        pr.set_fixed_play_rate(rate)
        prm.set_editor_property("play_rate", pr)
        prm.set_editor_property("first_loop_start_frame_offset", unreal.FrameNumber(int(round((anim_start_s % anim.get_play_length()) * tps))))
        sec.set_editor_property("params", prm)
        sec.set_range(int(round(t0 * dck.FPS)), int(round(t1 * dck.FPS)))  # after params: setting the clip resizes the section

    for p in crowd["people"]:
        actor = dck.find_actor(p["label"])
        if not actor:
            continue
        anim = unreal.load_asset(p["anim"])
        b = seq.add_possessable(actor)
        at = b.add_track(unreal.MovieSceneSkeletalAnimationTrack)
        if p["kind"] == "standing":
            cycles = max(1, round(T_loop / anim.get_play_length()))
            clip(at, anim, 0.0, T_all, p["anim_offset_s"], cycles * anim.get_play_length() / T_loop)  # whole cycles: wraps into the tail
            continue
        pts, v, sp = p["path"], p["speed"], p["spacing_m"]
        s0, T = round(p["start_s"] * dck.FPS) / dck.FPS, p["travel_s"]
        heads = []
        for i in range(len(pts)):
            q0, q1 = pts[max(0, i - 2)], pts[min(len(pts) - 1, i + 2)]
            heads.append(math.atan2(q1[1] - q0[1], q1[0] - q0[0]))
        for i in range(1, len(heads)):  # unwrap
            heads[i] += round((heads[i - 1] - heads[i]) / (2 * math.pi)) * 2 * math.pi

        def state(t):
            u = (t - s0) % T_loop
            if u > T + 0.5 * eps:  # between runs: far below the city, turned for the next start
                back = u > 0.5 * (T + T_loop)
                i = 0 if back else len(pts) - 1
                return [pts[i][0], pts[i][1], -400.0], heads[i]
            x = min(len(pts) - 1.0, u * v / sp)
            i = min(len(pts) - 2, int(x))
            f = x - i
            return [pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f, 0.0], heads[i] + (heads[i + 1] - heads[i]) * f

        times = {0.0, T_loop, T_all}
        for s in (s0 - T_loop, s0, s0 + T_loop):  # the run before, this loop's, and its repeat in the tail
            for t in [s - eps, s, s + T, s + T + eps] + [s + j * KEY_DT for j in range(1, int(T / KEY_DT) + 1)]:
                if 0.0 < t < T_all:
                    times.add(round(t * dck.FPS) / dck.FPS)
            if s + T > 0 and s < T_all:  # the walk clip for this run, clipped to the loop + tail
                t0, t1 = max(0.0, s), min(T_all, s + T)
                clip(at, anim, t0, t1, p["anim_offset_s"] + (t0 - s) * p["rate"], p["rate"])
        tt = b.add_track(unreal.MovieScene3DTransformTrack)
        ts = tt.add_section()
        ts.set_range(0, frames_all)
        ch = ts.get_all_channels()
        for t in sorted(times):
            pos, h = state(t)
            loc = dck.to_ue(*pos)
            yaw = dck.heading_to_ue_yaw(math.degrees(h)) - 90.0  # the mannequin faces +Y
            for c, val in zip(ch, (loc.x, loc.y, loc.z, 0.0, 0.0, yaw, p["scale"], p["scale"], p["scale"])):
                c.add_key(fr(t), val, interpolation=lin)

# Rain contact pass (prompt 9): the loop clock for every animated water / steam effect (wet_fx.py, ground.py). LoopTime
# runs linearly from 0 to the loop length; each effect completes whole cycles per loop, so frame end == frame 0.
mpc_path = f"{dck.GAME}/WetFX/MPC_WetFX"
if unreal.EditorAssetLibrary.does_asset_exist(mpc_path):
    import wetfx_hlsl
    wetfx_hlsl.set_mpc_default("LoopLength", sw["seconds"])
    ct = seq.add_track(unreal.MovieSceneMaterialParameterCollectionTrack)
    ct.set_editor_property("mpc", unreal.load_asset(mpc_path))
    cs = ct.add_section()
    cs.set_range(0, frames_all)
    cs.add_scalar_parameter_key("LoopTime", unreal.FrameNumber(0), 0.0)  # creates the channel (this call takes ticks)
    lc = cs.get_all_channels()[0]
    # on past the loop end into the tail: every effect is periodic in LoopTime (wetfx_hlsl.loop_time wraps the city's)
    lc.add_key(unreal.FrameNumber(frames_all), float(T_all), interpolation=unreal.MovieSceneKeyInterpolation.LINEAR)  # display frames
    for key in lc.get_keys():
        key.set_interpolation_mode(unreal.RichCurveInterpMode.RCIM_LINEAR)

cut_track = seq.add_track(unreal.MovieSceneCameraCutTrack)
cut = cut_track.add_section()
cut.set_range(0, frames_all)
cut.set_camera_binding_id(seq.get_portable_binding_id(seq, binding))
unreal.EditorAssetLibrary.save_loaded_asset(seq)
dck.LEVELS.save_current_level()
print(f"make_sweep: {dck.SEQUENCE} {frames} frames + {tail} tail, {n + 1} keys, arc +-{sw['arc_deg']} deg at {sw['height_m']} m")
