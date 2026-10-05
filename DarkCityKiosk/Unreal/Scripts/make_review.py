"""Creates LS_Review: the kiosk close-up review cameras (kiosk_config.REVIEW_CAMS) plus the solved
reference camera and the signage-pass shots (GRAPHICS_REVIEW_CAMS), one camera cut each, for before/after comparisons of surfacing passes.

LS_Review is a copy of LS_Sweep (so rain, crowd and traffic behave as in the video) with its own
camera cuts and the mist waves switched off (the fog holds its clear phase). Each shot lasts
SHOT_FRAMES so Lumen and TSR settle after the cut; use the LAST frame of each shot.

    node Scripts/ue.mjs Scripts/make_review.py
    node Scripts/ue.mjs Scripts/render.py --sequence LS_Review --tag <tag> --frames 0-128 --res 2560x1440

Shot k covers frames [k * SHOT_FRAMES, (k + 1) * SHOT_FRAMES); the order is REVIEW_ORDER.
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
    """name -> (UE location, UE rotation, lens mm): REVIEW_CAMS, Reference, then GRAPHICS_REVIEW_CAMS."""
    cams = {}
    for name, (loc, tgt, lens) in list(K.REVIEW_CAMS.items()) + list(K.GRAPHICS_REVIEW_CAMS.items()):
        a, b = dck.to_ue(*loc), dck.to_ue(*tgt)
        d = b - a
        rot = unreal.Rotator(roll=0.0, pitch=math.degrees(math.atan2(d.z, math.hypot(d.x, d.y))),
                             yaw=math.degrees(math.atan2(d.y, d.x)))
        cams[name] = (a, rot, lens)
    hc = K.HERO_CAM
    cams["Reference"] = (dck.to_ue(hc["pos_xy"][0], hc["pos_xy"][1], hc["height_overlay"]),
                         unreal.Rotator(roll=0.0, pitch=hc["pitch_up_deg"], yaw=dck.heading_to_ue_yaw(hc["heading_deg"])),
                         hc["lens_mm"])
    return cams


# the signage pass (2026-10-05) shots come after Reference, so the older shots keep their frame numbers
REVIEW_ORDER = list(K.REVIEW_CAMS) + ["Reference"] + list(K.GRAPHICS_REVIEW_CAMS)

if __name__ == "__main__":
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
