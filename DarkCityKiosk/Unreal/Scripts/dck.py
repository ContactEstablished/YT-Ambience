"""Shared paths and helpers for the Dark City Kiosk editor scripts (run through ue.mjs)."""
import importlib
import math
import os
import sys

import unreal

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPTS_DIR)  # .../DarkCityKiosk/Unreal
ROOT_DIR = os.path.dirname(PROJECT_DIR)  # .../DarkCityKiosk
RAW = os.path.join(PROJECT_DIR, "RawContent")
BLENDER_SCRIPTS = os.path.join(ROOT_DIR, "Blender", "scripts")

GAME = "/Game/DarkCity"
MAP = f"{GAME}/Maps/L_DarkCity"
SEQUENCE = f"{GAME}/Sequences/LS_Sweep"
# The kiosk in use: RawContent/<KIOSK_GLB>.glb imports to <KIOSK_MESHES>/<KIOSK_GLB>/{StaticMeshes,Materials}
KIOSK_GLB = "kiosk_detail"  # was "kiosk_blockout" (grey box, /Game/DarkCity/Kiosk/Blockout)
KIOSK_MESHES = f"{GAME}/Kiosk/Detail"

FPS = 24

# The Blender build config is the single source of kiosk dimensions and cameras.
if BLENDER_SCRIPTS not in sys.path:
    sys.path.insert(0, BLENDER_SCRIPTS)
import kiosk_config as K  # noqa: E402

K = importlib.reload(K)

EAL = unreal.EditorAssetLibrary
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def world():
    return unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()


# ---- Blender kiosk frame (metres, right-handed) -> Unreal (cm, left-handed) ----
# Set by verify_axes after the first import: glTF via Interchange keeps X and flips Y.
def to_ue(x, y, z):
    return unreal.Vector(x * 100.0, -y * 100.0, z * 100.0)


def heading_to_ue_yaw(heading_deg):
    """Blender heading (from +X toward +Y) -> Unreal yaw (from +X toward +Y, Y flipped)."""
    return -heading_deg


def find_actor(label):
    for a in ACTORS.get_all_level_actors():
        if a.get_actor_label() == label:
            return a
    return None


def get_or_spawn(cls, label, location=unreal.Vector(0, 0, 0), rotation=unreal.Rotator(0, 0, 0), folder=None):
    a = find_actor(label)
    if a is None:
        a = ACTORS.spawn_actor_from_class(cls, location, rotation)
        a.set_actor_label(label)
    else:
        a.modify()
        a.set_actor_location_and_rotation(location, rotation, False, False)
    if folder:
        a.set_folder_path(folder)
    return a


def setp(obj, **props):
    for k, v in props.items():
        obj.set_editor_property(k, v)
    return obj


def ensure_dir(path):
    if not EAL.does_directory_exist(path):
        EAL.make_directory(path)


def ensure_map():
    """Open L_DarkCity, creating it (non-partitioned, empty) on first use."""
    if world() and world().get_path_name().startswith(MAP):
        return world()
    if EAL.does_asset_exist(MAP):
        LEVELS.load_level(MAP)
    else:
        ensure_dir(f"{GAME}/Maps")
        LEVELS.new_level(MAP)
    return world()


# ---- Camera sweep -------------------------------------------------------------------
def sweep_theta(t, seconds, arc_deg):
    """Ping-pong orbit angle at time t: -arc at 0 (A), +arc at half time (B), back to -arc.
    A cosine ease, so the camera slows to a stop at each end and the loop is seamless."""
    return -arc_deg * math.cos(2.0 * math.pi * t / seconds)


def orbit_pose(theta_deg, height_m, distance_scale=1.0, pitch_deg=None):
    """Camera location (Unreal cm) and rotation for an orbit angle around the kiosk.
    distance_scale moves the camera out along its line to the kiosk centre (1.0 = reference)."""
    hc = K.HERO_CAM
    px, py = K.ORBIT_PIVOT
    t = math.radians(theta_deg)
    dx, dy = (hc["pos_xy"][0] - px) * distance_scale, (hc["pos_xy"][1] - py) * distance_scale
    x = px + dx * math.cos(t) - dy * math.sin(t)
    y = py + dx * math.sin(t) + dy * math.cos(t)
    pitch = hc["pitch_up_deg"] if pitch_deg is None else pitch_deg
    rot = unreal.Rotator(roll=0.0, pitch=pitch, yaw=heading_to_ue_yaw(hc["heading_deg"] + theta_deg))
    return to_ue(x, y, height_m), rot


def setup_cine_camera(cam):
    cc = cam.get_cine_camera_component()
    cc.modify()
    fb = cc.get_editor_property("filmback")
    fb.set_editor_property("sensor_width", K.HERO_CAM["sensor_w_mm"])
    fb.set_editor_property("sensor_height", K.HERO_CAM["sensor_w_mm"] * 9.0 / 16.0)
    cc.set_editor_property("filmback", fb)
    cc.set_editor_property("current_focal_length", K.VIDEO_CAM["lens_mm"])
    focus = cc.get_editor_property("focus_settings")
    focus.set_editor_property("focus_method", unreal.CameraFocusMethod.DISABLE)
    cc.set_editor_property("focus_settings", focus)
    return cc
