"""Creates LS_Review: the kiosk close-up review cameras (kiosk_config.REVIEW_CAMS) plus the solved
reference camera and the signage-pass shots (GRAPHICS_REVIEW_CAMS), one camera cut each, for before/after comparisons of surfacing passes.

LS_Review is a copy of LS_Sweep (so rain, crowd and traffic behave as in the video) with its own
camera cuts and the mist waves switched off (the fog holds its clear phase). Each shot lasts
SHOT_FRAMES so Lumen and TSR settle after the cut; use the LAST frame of each shot.

    node Scripts/ue.mjs Scripts/make_review.py
    node Scripts/ue.mjs Scripts/render.py --sequence LS_Review --tag <tag> --frames 0-128 --res 2560x1440

Shot k covers frames [k * SHOT_FRAMES, (k + 1) * SHOT_FRAMES); the order is REVIEW_ORDER.

Final polish (prompt 10):
    node Scripts/ue.mjs Scripts/make_review.py --polish   # LS_Polish: POLISH_ORDER (Cinematic, OrbitA, OrbitB, the
                                                          # POLISH_REVIEW_CAMS tele views, POLISH_DETAIL_SHOTS)
    node Scripts/ue.mjs Scripts/make_review.py --motion   # LS_CineMotion: LS_Sweep from a fixed camera at the Cinematic pose
"""
import importlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402

dck = importlib.reload(dck)
import unreal  # noqa: E402

K = dck.K
SHOT_FRAMES = 16
REVIEW = f"{dck.GAME}/Sequences/LS_Review"
FOG_WAVE_PROPS = ("FogDensity", "VolumetricFogExtinctionScale", "VolumetricFogEmissive")


def review_cameras():
    """name -> (UE location, UE rotation, lens mm): REVIEW_CAMS, Reference, GRAPHICS_REVIEW_CAMS,
    KITCHEN_REVIEW_CAMS, Cinematic (the sweep camera at Mid), EXTERIOR_REVIEW_CAMS, then OrbitA / OrbitB
    (the sweep camera at its two stops)."""
    cams = {}
    for name, (loc, tgt, lens) in (list(K.REVIEW_CAMS.items()) + list(K.GRAPHICS_REVIEW_CAMS.items())
                                   + list(K.KITCHEN_REVIEW_CAMS.items()) + list(K.EXTERIOR_REVIEW_CAMS.items())
                                   + list(getattr(K, "WET_REVIEW_CAMS", {}).items())):
        a, b = dck.to_ue(*loc), dck.to_ue(*tgt)
        d = b - a
        rot = unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(d.z, math.hypot(d.x, d.y))),
                             yaw=math.degrees(math.atan2(d.y, d.x)))
        cams[name] = (a, rot, lens)
    hc = K.HERO_CAM
    cams["Reference"] = (dck.to_ue(hc["pos_xy"][0], hc["pos_xy"][1], hc["height_overlay"]),
                         unreal.Rotator(roll=0.0, pitch=hc["pitch_up_deg"], yaw=dck.heading_to_ue_yaw(hc["heading_deg"])),
                         hc["lens_mm"])
    vc = K.VIDEO_CAM  # the video camera at the middle of its arc (LS_Sweep frame 180 / 540)
    loc, rot = dck.orbit_pose(0.0, vc["height_m"], vc["distance_scale"], vc["pitch_deg"])
    cams["Cinematic"] = (loc, rot, vc["lens_mm"])
    for name, theta in (("OrbitA", -vc["arc_deg"]), ("OrbitB", vc["arc_deg"])):  # LS_Sweep frames 0 and 360
        loc, rot = dck.orbit_pose(theta, vc["height_m"], vc["distance_scale"], vc["pitch_deg"])
        cams[name] = (loc, rot, vc["lens_mm"])
    for name, (theta, tgt, lens) in getattr(K, "POLISH_REVIEW_CAMS", {}).items():  # prompt 10: tele from the video camera
        loc, _ = dck.orbit_pose(theta, vc["height_m"], vc["distance_scale"], vc["pitch_deg"])
        d = dck.to_ue(*tgt) - loc
        cams[name] = (loc, unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(d.z, math.hypot(d.x, d.y))),
                                          yaw=math.degrees(math.atan2(d.y, d.x))), lens)
    return cams


# the signage pass (2026-10-05) shots come after Reference, then the kitchen pass (2026-10-09) shots, then the
# exterior pass (2026-10-09, prompt 8) shots and the orbit stops, so the older shots keep their frame numbers
REVIEW_ORDER = (list(K.REVIEW_CAMS) + ["Reference"] + list(K.GRAPHICS_REVIEW_CAMS) + list(K.KITCHEN_REVIEW_CAMS) + ["Cinematic"]
                + list(K.EXTERIOR_REVIEW_CAMS) + ["OrbitA", "OrbitB"] + list(getattr(K, "WET_REVIEW_CAMS", {})))

WETFX = f"{dck.GAME}/Sequences/LS_WetFX"
POLISH = f"{dck.GAME}/Sequences/LS_Polish"
POLISH_ORDER = ["Cinematic", "OrbitA", "OrbitB"] + list(getattr(K, "POLISH_REVIEW_CAMS", {})) + list(getattr(K, "POLISH_DETAIL_SHOTS", []))
CINE_MOTION = f"{dck.GAME}/Sequences/LS_CineMotion"


def wetfx_sequence():
    """LS_WetFX (rain contact pass, prompt 9): LS_Sweep (rain, crowd, traffic, the loop clock) seen from one fixed
    camera, K.WET_MOTION_CAM, for the water + steam motion preview. Mist waves off, as in LS_Review."""
    if dck.EAL.does_asset_exist(WETFX):
        dck.EAL.delete_asset(WETFX)
    seq = dck.EAL.duplicate_asset(dck.SEQUENCE, WETFX)
    for tr in list(seq.get_tracks()):
        if isinstance(tr, unreal.MovieSceneCameraCutTrack):
            seq.remove_track(tr)
    for b in seq.get_bindings():
        for tr in b.get_tracks():
            if isinstance(tr, unreal.MovieScenePropertyTrack) and str(tr.get_property_name()) in FOG_WAVE_PROPS:
                for s in tr.get_sections():
                    s.set_is_active(False)
    loc, tgt, lens = K.WET_MOTION_CAM
    a, b = dck.to_ue(*loc), dck.to_ue(*tgt)
    d = b - a
    rot = unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(d.z, math.hypot(d.x, d.y))), yaw=math.degrees(math.atan2(d.y, d.x)))
    cam = dck.get_or_spawn(unreal.CineCameraActor, "CAM_WetFX", a, rot, folder="Cameras/Review")
    cc = dck.setup_cine_camera(cam)
    cc.set_editor_property("current_focal_length", float(lens))
    binding = seq.add_possessable(cam)
    cut = seq.add_track(unreal.MovieSceneCameraCutTrack).add_section()
    cut.set_range(0, seq.get_playback_end())
    cut.set_camera_binding_id(seq.get_portable_binding_id(seq, binding))
    dck.EAL.save_loaded_asset(seq)
    print(f"make_review: {WETFX} from CAM_WetFX ({lens} mm), {seq.get_playback_end()} frames")


def shot_sequence(path, order):
    """A copy of LS_Sweep (rain, crowd, traffic, the loop clock) with one SHOT_FRAMES camera cut per name in order and
    the mist waves off (the fog holds its clear phase)."""
    if dck.EAL.does_asset_exist(path):
        dck.EAL.delete_asset(path)
    seq = dck.EAL.duplicate_asset(dck.SEQUENCE, path)
    for tr in list(seq.get_tracks()):
        if isinstance(tr, unreal.MovieSceneCameraCutTrack):
            seq.remove_track(tr)
    off = 0
    for b in seq.get_bindings():
        for tr in b.get_tracks():
            if isinstance(tr, unreal.MovieScenePropertyTrack) and str(tr.get_property_name()) in FOG_WAVE_PROPS:
                for s in tr.get_sections():
                    s.set_is_active(False)
                    off += 1
    cut_track = seq.add_track(unreal.MovieSceneCameraCutTrack)
    cams = review_cameras()
    for k, name in enumerate(order):
        loc, rot, lens = cams[name]
        cam = dck.get_or_spawn(unreal.CineCameraActor, f"CAM_Rev_{name}", loc, rot, folder="Cameras/Review")
        cam.modify()
        cam.set_actor_location_and_rotation(loc, rot, False, False)
        cc = dck.setup_cine_camera(cam)
        cc.set_editor_property("current_focal_length", float(lens))
        binding = seq.add_possessable(cam)
        cut = cut_track.add_section()
        cut.set_range(k * SHOT_FRAMES, (k + 1) * SHOT_FRAMES)
        cut.set_camera_binding_id(seq.get_portable_binding_id(seq, binding))
    seq.set_playback_end(len(order) * SHOT_FRAMES)
    dck.EAL.save_loaded_asset(seq)
    last = [(k + 1) * SHOT_FRAMES - 1 for k in range(len(order))]
    print(f"make_review: {path} {len(order)} shots x {SHOT_FRAMES} frames, fog waves off ({off} sections); "
          f"use frames {dict(zip(order, last))}")


def cine_motion_sequence():
    """LS_CineMotion (prompt 10): LS_Sweep (rain, crowd, traffic, the loop clock, the mist waves) seen from a camera
    held at the Cinematic pose, for the water + steam motion sample at the video's own framing."""
    if dck.EAL.does_asset_exist(CINE_MOTION):
        dck.EAL.delete_asset(CINE_MOTION)
    seq = dck.EAL.duplicate_asset(dck.SEQUENCE, CINE_MOTION)
    for tr in list(seq.get_tracks()):
        if isinstance(tr, unreal.MovieSceneCameraCutTrack):
            seq.remove_track(tr)
    loc, rot, lens = review_cameras()["Cinematic"]
    cam = dck.get_or_spawn(unreal.CineCameraActor, "CAM_CineMotion", loc, rot, folder="Cameras/Review")
    cam.set_actor_location_and_rotation(loc, rot, False, False)
    cc = dck.setup_cine_camera(cam)
    cc.set_editor_property("current_focal_length", float(lens))
    binding = seq.add_possessable(cam)
    cut = seq.add_track(unreal.MovieSceneCameraCutTrack).add_section()
    cut.set_range(0, seq.get_playback_end())
    cut.set_camera_binding_id(seq.get_portable_binding_id(seq, binding))
    dck.EAL.save_loaded_asset(seq)
    print(f"make_review: {CINE_MOTION} from CAM_CineMotion ({lens} mm), {seq.get_playback_end()} frames")


if __name__ == "__main__" and "--polish" in sys.argv:
    dck.ensure_map()
    unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
    shot_sequence(POLISH, POLISH_ORDER)
    dck.LEVELS.save_current_level()
elif __name__ == "__main__" and "--motion" in sys.argv:
    dck.ensure_map()
    unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
    cine_motion_sequence()
    dck.LEVELS.save_current_level()
elif __name__ == "__main__" and "--wetfx" in sys.argv:
    dck.ensure_map()
    unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
    wetfx_sequence()
    dck.LEVELS.save_current_level()
elif __name__ == "__main__":
    dck.ensure_map()
    unreal.LevelSequenceEditorBlueprintLibrary.close_level_sequence()
    if dck.EAL.does_asset_exist(REVIEW):
        dck.EAL.delete_asset(REVIEW)
    seq = dck.EAL.duplicate_asset(dck.SEQUENCE, REVIEW)

    # the sweep's own camera cut goes; the mist waves are switched off (clear fog throughout)
    for tr in list(seq.get_tracks()):
        if isinstance(tr, unreal.MovieSceneCameraCutTrack):
            seq.remove_track(tr)
    off = 0
    for b in seq.get_bindings():
        for tr in b.get_tracks():
            if isinstance(tr, unreal.MovieScenePropertyTrack) and str(tr.get_property_name()) in FOG_WAVE_PROPS:
                for s in tr.get_sections():
                    s.set_is_active(False)
                    off += 1

    cut_track = seq.add_track(unreal.MovieSceneCameraCutTrack)
    cams = review_cameras()
    for k, name in enumerate(REVIEW_ORDER):
        loc, rot, lens = cams[name]
        cam = dck.get_or_spawn(unreal.CineCameraActor, f"CAM_Rev_{name}", loc, rot, folder="Cameras/Review")
        cam.modify()
        cam.set_actor_location_and_rotation(loc, rot, False, False)
        cc = dck.setup_cine_camera(cam)
        cc.set_editor_property("current_focal_length", float(lens))
        binding = seq.add_possessable(cam)
        cut = cut_track.add_section()
        cut.set_range(k * SHOT_FRAMES, (k + 1) * SHOT_FRAMES)
        cut.set_camera_binding_id(seq.get_portable_binding_id(seq, binding))
    seq.set_playback_end(len(REVIEW_ORDER) * SHOT_FRAMES)
    dck.EAL.save_loaded_asset(seq)
    dck.LEVELS.save_current_level()
    last = [(k + 1) * SHOT_FRAMES - 1 for k in range(len(REVIEW_ORDER))]
    print(f"make_review: {REVIEW} {len(REVIEW_ORDER)} shots x {SHOT_FRAMES} frames, fog waves off ({off} sections); "
          f"use frames {dict(zip(REVIEW_ORDER, last))}")
