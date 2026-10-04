"""Builds the detailed kiosk (scripted) into Blender/kiosk_detail.blend.

    blender -b --factory-startup -P build_kiosk.py -- [--render] [--cams A,Mid,B,Corner,Soffit]

Detailed so far: platform, body shell, canopy (step 1), service side + door side (step 2),
wall clutter + lanterns + posters/stickers + ground props (step 3), roof machinery (step 4).
Earlier versions reused grey-box parts (build_kiosk_blockout.py) and
are replaced step by step. Everything is rebuilt from kiosk_config.py on each run.
"""
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kiosk_config as C  # noqa: E402,F401
import build_kiosk_blockout as B  # noqa: E402
from kiosk import canopy, clutter, openings, review, roof, shell  # noqa: E402

BLENDER_DIR = os.path.dirname(HERE)
RENDERS = os.path.join(BLENDER_DIR, "renders")
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default):
    return ARGV[ARGV.index(name) + 1] if name in ARGV else default


def main():
    B.reset_scene()
    B.init_shared()
    B.mat("Kiosk_Core", (0.02, 0.02, 0.022))
    for name, rough, metal in (("Kiosk_YellowPaint", 0.35, 0.0), ("Kiosk_YellowPaint_Dark", 0.4, 0.0),
                               ("Steel_Dark", 0.35, 0.6), ("Steel_Grey", 0.4, 0.5), ("Steel_Galvanised", 0.3, 0.8),
                               ("Platform_Concrete", 0.6, 0.0)):
        bsdf = bpy.data.materials[name].node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    openings.ensure_materials(B)
    clutter.ensure_materials(B)
    materials = roof.ensure_materials(B)

    scene = bpy.context.scene
    kiosk = B.collection("Kiosk")
    cols = {n: B.collection(n, kiosk) for n in ("Ground", "Body", "ServiceSide", "DoorSide", "Canopy", "Roof", "Props")}
    cutters = B.collection("Cutters", kiosk)
    cutters.hide_render = True
    review_coll = B.collection("Review")

    shell.build_platform(cols["Ground"], materials)
    shell.build_body(cols["Body"], cutters, materials)
    openings.build_service_side(cols["ServiceSide"], materials, B)
    openings.build_door_side(cols["DoorSide"], materials, B)
    canopy.build(cols["Canopy"], materials, B)
    roof.build(cols["Roof"], materials)
    clutter.build(cols["Props"], materials, B)

    review.setup_scene(scene, review_coll, materials)
    cams = review.cameras(review_coll)
    scene.camera = cams["Mid"]

    path = os.path.join(BLENDER_DIR, "kiosk_detail.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, check_existing=False)
    tris = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == "MESH")
    print(f"saved {path}: {len(bpy.data.objects)} objects, {tris} faces")

    if "--render" in ARGV:
        os.makedirs(RENDERS, exist_ok=True)
        tag = opt("--tag", "detail")
        for key in opt("--cams", "Mid,Roof,Corner").split(","):
            review.render(scene, cams[key], os.path.join(RENDERS, f"{tag}_{key}.png"))


if __name__ == "__main__":
    main()
