"""Quick editor screenshots through CAM_Sweep at orbit angles (no Movie Render Queue).
    node Scripts/ue.mjs Scripts/capture_stills.py [--res 1920x1080] [--tag test] [theta ...]
Default angles: -45 (A), 0 (Mid), 45 (B). Writes DarkCityKiosk/Renders/stills/<tag>_<name>.png.
Runs on the editor tick, so it returns immediately; 'capture_stills: done' goes to the log.
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402

dck = importlib.reload(dck)
import scene_config as S  # noqa: E402

S = importlib.reload(S)
import unreal  # noqa: E402

args = sys.argv[1:]


def opt(name, default):
    if name in args:
        i = args.index(name)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return default


res = tuple(int(v) for v in opt("--res", "1920x1080").split("x"))
tag = opt("--tag", "still")
settle = int(opt("--settle", "60"))
# Optional overrides for lens tests (defaults come from kiosk_config / scene_config)
lens = float(opt("--lens", "0")) or None
VC = dck.K.VIDEO_CAM
dist = float(opt("--dist", "0")) or VC["distance_scale"]
pitch = float(opt("--pitch", "-99"))
pitch = None if pitch == -99 else pitch
pitch = VC["pitch_deg"] if pitch is None else pitch
angles = [float(a) for a in args] or [-VC["arc_deg"], 0.0, VC["arc_deg"]]
names = {-VC["arc_deg"]: "A", 0.0: "Mid", VC["arc_deg"]: "B"}
out_dir = os.path.join(dck.ROOT_DIR, "Renders", "stills")
os.makedirs(out_dir, exist_ok=True)

dck.ensure_map()
unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
dck.LEVELS.editor_set_viewport_realtime(True)
cam = dck.find_actor("CAM_Preview") or dck.get_or_spawn(unreal.CineCameraActor, "CAM_Preview", folder="Cameras")
cc = dck.setup_cine_camera(cam)
if lens:
    cc.set_editor_property("current_focal_length", lens)
state = {"i": 0, "tick": 0}


def on_tick(_dt):
    i = state["i"]
    if i >= len(angles):
        unreal.unregister_slate_post_tick_callback(state["handle"])
        unreal.log("capture_stills: done")
        return
    theta = angles[i]
    if state["tick"] == 0:
        loc, rot = dck.orbit_pose(theta, VC["height_m"], dist, pitch)
        cam.set_actor_location_and_rotation(loc, rot, False, True)
        # Rain spawns around the active view: park the editor viewport on the shot while it settles.
        unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).set_level_viewport_camera_info(loc, rot)
    elif state["tick"] == settle:
        name = names.get(theta, f"{theta:+.0f}")
        unreal.AutomationLibrary.take_high_res_screenshot(res[0], res[1], os.path.join(out_dir, f"{tag}_{name}.png"), cam)
    elif state["tick"] >= settle + 20:
        state["i"] += 1
        state["tick"] = -1
    state["tick"] += 1


state["handle"] = unreal.register_slate_post_tick_callback(on_tick)
print(f"capturing {len(angles)} stills -> {out_dir}")
