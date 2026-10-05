"""Signage pass (2026-10-05, brief 6): builds the kiosk's graphics onto the exported kiosk and exports
them on their own, so iterating on signage never touches the kiosk export or its weathering bake.

    blender -b --factory-startup -P build_graphics.py [-- --glb <kiosk glb>]

Needs: Unreal/RawContent/kiosk_detail.glb (export_kiosk_glb.py; the kiosk as Unreal sees it, with
WeatherUV) and Unreal/RawContent/graphics/graphics_manifest.json (Graphics/make_kiosk_graphics.mjs).
Writes:
  Unreal/RawContent/kiosk_graphics.glb           SM_Kiosk_Graphics (every card) + SM_Kiosk_Signs (the 24h
                                                 lightbox, its clamps and wiring, the lantern lettering)
  Unreal/RawContent/graphics/kiosk_decals.json   paint decals (Unreal deferred decals) + the WeatherUV map
                                                 of the lit fascia, for the lettering's ageing material
  Blender/kiosk_graphics.blend                   the kiosk + graphics, textured, for Workbench checks
Then in Unreal: node Scripts/ue.mjs Scripts/kiosk_graphics.py
Placements: kiosk_config.GRAPHICS_CARDS / GRAPHICS_DECALS / SIGN_24H / LANTERN_LETTERING.
"""
import json
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kiosk_config as C  # noqa: E402
import build_kiosk_blockout as B  # noqa: E402
from kiosk import geo, graphics  # noqa: E402

BLENDER_DIR = os.path.dirname(HERE)
RAW = os.path.join(os.path.dirname(BLENDER_DIR), "Unreal", "RawContent")
GFX = os.path.join(RAW, "graphics")
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
GLB = ARGV[ARGV.index("--glb") + 1] if "--glb" in ARGV else os.path.join(RAW, "kiosk_detail.glb")
OUT = os.path.join(RAW, "kiosk_graphics.glb")


def card_materials():
    """Graphics materials; textured (albedo + alpha) for Workbench checks. The glb is exported without
    images: Unreal builds its own materials (kiosk_graphics.py)."""
    mats = {}
    for name, tex in (("KG_Paper", "Paper"), ("KG_Labels", "Labels"), ("KG_Signs", "Signs"), ("KG_SignFrame", "Signs")):
        m = bpy.data.materials.new(name)
        nt = m.node_tree
        bsdf = nt.nodes.get("Principled BSDF")
        img = nt.nodes.new("ShaderNodeTexImage")
        path = os.path.join(GFX, f"T_KG_{tex}_C.png")
        if os.path.exists(path):
            img.image = bpy.data.images.load(path, check_existing=True)
        nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(img.outputs["Alpha"], bsdf.inputs["Alpha"])
        m.blend_method = "CLIP" if hasattr(m, "blend_method") else None
        mats[name] = m
    ink = B.mat("KG_LanternInk", (0.03, 0.02, 0.015))
    mats["KG_LanternInk"] = ink
    for name in ("Steel_Dark", "Steel_Grey", "Steel_Galv_Dull", "Rubber_Black", "Cable_Black"):
        mats[name] = bpy.data.materials.get(name) or B.mat(name, (0.1, 0.1, 0.1))
    return mats


def main():
    t0 = time.time()
    B.reset_scene()
    B.init_shared()
    mats = card_materials()
    man = json.load(open(os.path.join(GFX, "graphics_manifest.json"), encoding="utf-8"))

    kiosk = B.collection("Kiosk")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=GLB)
    imported = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    for o in imported:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        kiosk.objects.link(o)
    target = graphics.Target([o for o in imported if o.name.startswith("SM_Kiosk_")])
    print(f"build_graphics: {len(target.objs)} kiosk meshes from {GLB}")

    gcoll = B.collection("Graphics")
    cards = graphics.CardMesh("SM_Kiosk_Graphics")
    report = []
    for k, (item, wall, u, z, rot, layer, opt) in enumerate(C.GRAPHICS_CARDS):
        if item not in man["items"]:
            print(f"  ! {item}: not in the manifest (run Graphics/make_kiosk_graphics.mjs)")
            continue
        misses, weathered, tris = graphics.lay_card(cards, target, man, item, wall, u, z, rot, layer, opt, f"{item}{k}")
        report.append((item, misses, weathered, tris))
        if misses:
            print(f"  ! {item}: {misses} grid points found no surface (laid on the wall plane)")
    cards.build(gcoll, mats)

    signs = graphics.CardMesh("SM_Kiosk_Signs")
    hw = geo.Mesh("Signs_Hardware")
    centre, normal = graphics.sign_24h(signs, hw, man)
    graphics.lantern_lettering(hw, B, gcoll)
    sob = signs.build(gcoll, mats)
    hob = hw.build(gcoll, mats)
    bpy.ops.object.select_all(action="DESELECT")
    sob.select_set(True)
    hob.select_set(True)
    bpy.context.view_layer.objects.active = sob
    bpy.ops.object.join()

    decals = [graphics.place_decal(target, man, item, wall, u, z, rot, w, h, opt)
              for item, wall, u, z, rot, w, h, opt in C.GRAPHICS_DECALS if item in man["items"]]
    fascia = graphics.fascia_uv1(target)
    for side, f in fascia.items():
        print(f"  fascia {side}: WeatherUV fit over {f['loops']} loops of 1/{f['islands']} islands (u {f['u_range'][0]:.2f}..{f['u_range'][1]:.2f}), "
              f"max error {f['max_err']:.2e}, covers the lettering: {f['covers_lettering']}")
    s24 = C.SIGN_24H
    json.dump({"decals": decals, "fascia_uv1": fascia,
               "sign_24h": {"centre": list(centre), "normal": list(normal), "w": s24["w"], "h": s24["h"]}},
              open(os.path.join(GFX, "kiosk_decals.json"), "w", encoding="utf-8"), indent=1)

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLENDER_DIR, "kiosk_graphics.blend"), check_existing=False)
    bpy.ops.object.select_all(action="DESELECT")
    for o in gcoll.objects:
        o.select_set(True)
    gltf = dict(filepath=OUT, export_format="GLB", use_selection=True, export_apply=True, export_yup=True,
                export_cameras=False, export_lights=False, export_image_format="NONE")
    try:
        bpy.ops.export_scene.gltf(**gltf, export_vertex_color="ACTIVE")
    except TypeError:
        bpy.ops.export_scene.gltf(**gltf, export_colors=True)
    ntri = sum(r[3] for r in report)
    nw = sum(r[2] for r in report)
    print(f"build_graphics: {len(report)} cards ({ntri} tris, {nw} on weathered surfaces), {len(decals)} decals -> {OUT} "
          f"({time.time() - t0:.1f}s)")


if __name__ == "__main__":
    main()
