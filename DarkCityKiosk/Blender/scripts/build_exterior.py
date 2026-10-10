"""Exterior pass (2026-10-09, prompt 8): builds the ground props round the kiosk's footprint and exports them
on their own, so the kiosk export and its weathering bake stay untouched.

    blender -b --factory-startup -P build_exterior.py [-- --render [--cams Mid,A,B,...] [--tag x1] [--res 1600x900]]

Needs: Unreal/RawContent/kiosk_detail.glb and kiosk_kitchen.glb (context for the checks; the old ground props
are trimmed out of SM_Kiosk_Props here with the same rules Unreal uses, the kitchen's old interior with the
kitchen's), and Unreal/RawContent/graphics/graphics_manifest.json with the Exterior atlas
(node Graphics/make_kiosk_graphics.mjs Exterior).
Writes:
  Unreal/RawContent/kiosk_exterior.glb         SM_Kiosk_Exterior, SM_Kiosk_ExteriorCards and the prototypes SM_XP_*
  Unreal/RawContent/exterior/exterior.json     prototype placements (Unreal instances them), the trim rules,
                                               materials, the canopy footprint (rain exposure)
  Blender/kiosk_exterior.blend                 kiosk + kitchen + exterior for checks; Blender/renders/<tag>_<cam>.png
Then in Unreal: node Scripts/ue.mjs Scripts/kiosk_exterior.py
"""
import json
import math
import os
import sys
import time

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kiosk_config as C  # noqa: E402
import build_kiosk_blockout as B  # noqa: E402
import build_kitchen as BK  # noqa: E402
from kiosk import exterior, kitchen, masks, review  # noqa: E402

BLENDER_DIR = os.path.dirname(HERE)
RAW = os.path.join(os.path.dirname(BLENDER_DIR), "Unreal", "RawContent")
GFX = os.path.join(RAW, "graphics")
OUT = os.path.join(RAW, "kiosk_exterior.glb")
OUT_JSON = os.path.join(RAW, "exterior", "exterior.json")
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

# The old step-3 ground props that Unreal trims out of a copy of SM_Kiosk_Props (kiosk_exterior.py reads these
# from exterior.json). Boxes are kiosk-frame metres; a triangle goes only if all three corners are inside.
# Material filters keep the railing, the stools, the 24h pole, the lantern's pole and the electrical cluster.
X0, X1, Y0, Y1 = C.X0, C.X1, C.Y0, C.Y1
TRIM = {
    "SM_Kiosk_Props": {
        "boxes": [
            ((-3.24, 1.24, 0.11), (-2.81, 1.66, 1.03)),  # the lantern's box pedestal (its pole stands on the new riser)
            ((3.06, -2.40, 0.11), (3.59, -1.90, 0.66)),  # the grey bin (and its handles)
        ],
        "materials_in_box": [
            ("Wood_Crate", ((-3.48, 1.89, 0.11), (-2.86, 2.41, 0.88))),  # the slatted crate stack
            ("Cabinet_Green", ((-3.74, 1.53, 0.11), (-3.21, 2.07, 1.13))),  # the green equipment cabinet...
            ("Screen_Multi", ((-3.74, 1.53, 0.11), (-3.21, 2.07, 1.13))),  # ...its lit square
            ("Steel_Dark", ((-3.736, 1.59, 0.21), (-3.715, 2.01, 0.63))),  # ...and its panel
            ("Plastic_Red", ((-3.09, 1.04, 0.11), (-2.66, 1.36, 0.43))),  # the red bottle crate
            ("Steel_Grey", ((2.54, -2.115, 0.11), (3.01, -1.69, 0.98))),  # the utility cabinet...
            ("Steel_Dark", ((2.57, -2.135, 0.16), (2.98, -2.095, 0.93))),
            ("Rubber_Black", ((2.62, -2.115, 0.78), (2.93, -2.10, 0.95))),
            ("Stock_Yellow", ((2.64, -2.115, 0.36), (2.78, -2.10, 0.46))),
            ("Bin_Green", ((-3.20, -1.71, 0.11), (-2.68, -1.18, 0.80))),  # the green bin...
            ("Rubber_Black", ((-3.21, -1.51, 0.63), (-3.165, -1.39, 0.69))),  # ...its handles
            ("Rubber_Black", ((-2.725, -1.51, 0.63), (-2.68, -1.39, 0.69))),
            ("Rubber_Black", ((-3.00, -1.47, 0.11), (-2.66, -1.13, 0.93))),  # the junction box's floor cable
            ("Cardboard", ((-3.49, 2.33, 0.11), (-2.99, 2.67, 0.44))),  # the flattened cartons
        ],
    },
}


def opt(name, default):
    return ARGV[ARGV.index(name) + 1] if name in ARGV else default


def card_material():
    m = bpy.data.materials.new("KG_Exterior")
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    img = nt.nodes.new("ShaderNodeTexImage")
    path = os.path.join(GFX, "T_KG_Exterior_C.png")
    if os.path.exists(path):
        img.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(img.outputs["Alpha"], bsdf.inputs["Alpha"])
    return m


def import_glb(name, coll):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(RAW, name))
    objs = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    for o in [o for o in bpy.data.objects if o not in before and o.type != "MESH"]:
        bpy.data.objects.remove(o, do_unlink=True)
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        coll.objects.link(o)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return objs


def trim(objs, rules):
    """Deletes faces by the Unreal trim rules (all corners inside a box, optionally of one material)."""
    import bmesh
    counts = {}
    for o in objs:
        name = o.name.split(".")[0]
        rule = rules.get(name)
        if not rule:
            continue
        mats = [s.material.name.split(".")[0] if s.material else "" for s in o.material_slots]
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.faces.ensure_lookup_table()
        inside = lambda f, lo, hi: all(lo[i] <= v.co[i] <= hi[i] for v in f.verts for i in range(3))  # noqa: E731
        kill = []
        for f in bm.faces:
            mn = mats[f.material_index] if f.material_index < len(mats) else ""
            if mn in rule.get("materials", []) or any(inside(f, lo, hi) for lo, hi in rule.get("boxes", [])) or \
                    any(mn == mm and inside(f, lo, hi) for mm, (lo, hi) in rule.get("materials_in_box", [])):
                kill.append(f)
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(o.data)
        bm.free()
        counts[name] = len(kill)
        print(f"  trimmed {name}: {len(kill)} faces")
        # residue check: faces of the old props' own materials still standing in any trim region
        left = {}
        for f in o.data.polygons:
            mn = mats[f.material_index]
            if mn in RESIDUE:
                left[mn] = left.get(mn, 0) + 1
        print(f"  residue {name}: {left or 'none'}")
    return counts


# materials only the old ground props used: none of them should survive the trim
RESIDUE = ("Wood_Crate", "Rust_Red", "Cabinet_Green", "Screen_Multi", "Plastic_Red", "Bin_Green", "Cardboard", "Stock_Yellow")


def import_context():
    """The kiosk and kitchen as Unreal shows them: the old interior and the old ground props trimmed."""
    kiosk = B.collection("Kiosk")
    objs = import_glb("kiosk_detail.glb", kiosk)
    trim(objs, BK.TRIM)
    counts = trim(objs, TRIM)
    kcoll = B.collection("KitchenContext")
    kobjs = import_glb("kiosk_kitchen.glb", kcoll)
    for o in list(kobjs):
        if o.name.startswith("SM_KP_"):  # the kitchen's prototypes sit at the origin; the review doesn't need them
            bpy.data.objects.remove(o, do_unlink=True)
            kobjs.remove(o)
    return objs + kobjs, counts


def bake_with_context(objs):
    """Edge / occlusion / cavity masks (kiosk/masks.py) with the kiosk and the slab visible, so the props'
    feet and wall sides pick up the occlusion that grime follows."""
    masks.bake_masks(objs)


def main():
    t0 = time.time()
    B.reset_scene()
    B.init_shared()
    materials = exterior.ensure_materials(B)
    kitchen.ensure_materials(B)
    card_material()
    man = json.load(open(os.path.join(GFX, "graphics_manifest.json"), encoding="utf-8"))
    if not any(it["atlas"] == "Exterior" for it in man["items"].values()):
        raise RuntimeError("no Exterior atlas in graphics_manifest.json: run node Graphics/make_kiosk_graphics.mjs Exterior")
    context, counts = import_context()

    ecoll = B.collection("Exterior")
    pcoll = B.collection("ExteriorProto")
    icoll = B.collection("ExteriorInstances")
    objs, protos, placements = exterior.build(B, ecoll, man)
    proto_objs = {name: pm.build(pcoll, materials) for name, pm in protos.items()}

    # masks: the one-off parts in place, the kiosk + slab occluding; then the prototypes spread on a grid
    # (each on its own patch of ground, the in-place parts hidden)
    bake_with_context([objs["exterior"]])
    names = sorted(proto_objs)
    for k, n in enumerate(names):
        proto_objs[n].location = (30 + (k % 4) * 1.5, 30 + (k // 4) * 1.5, 0)
    hidden = [o for o in context + [objs["exterior"], objs["cards"]] if not o.hide_render]
    for o in hidden:
        o.hide_render = True
    me = bpy.data.meshes.new("BakeGround")
    s = 4.0
    me.from_pydata([(28 - s, 28 - s, 0), (36 + s, 28 - s, 0), (36 + s, 36 + s, 0), (28 - s, 36 + s, 0)], [], [(0, 1, 2, 3)])
    ground = bpy.data.objects.new("BakeGround", me)
    pcoll.objects.link(ground)
    masks.bake_masks([proto_objs[n] for n in names])
    bpy.data.objects.remove(ground, do_unlink=True)
    for o in hidden:
        o.hide_render = False
    for n in names:
        proto_objs[n].location = (0, 0, 0)

    # preview instances (not exported)
    for n, pos, yaw, sc in placements:
        o = bpy.data.objects.new(f"I_{n}", proto_objs[n].data)
        o.location = pos
        o.rotation_euler = (0, 0, math.radians(yaw))
        o.scale = (sc, sc, sc)
        icoll.objects.link(o)

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    data = {"props": [{"name": n, "pos": list(p), "yaw": y, "scale": sc} for n, p, y, sc in placements],
            "trim": TRIM, "trim_counts_blender": counts,
            "materials": {k: [list(v[0]), v[1], v[2], v[3]] for k, v in exterior.MATERIALS.items()},
            "canopy": list(C.EXTERIOR["canopy"]), "platform_h": C.PLATFORM_H}
    json.dump(data, open(OUT_JSON, "w", encoding="utf-8"), indent=1)

    bpy.ops.object.select_all(action="DESELECT")
    for o in list(objs.values()) + list(proto_objs.values()):
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs["exterior"]
    gltf = dict(filepath=OUT, export_format="GLB", use_selection=True, export_apply=True, export_yup=True,
                export_cameras=False, export_lights=False, export_image_format="NONE")
    try:
        bpy.ops.export_scene.gltf(**gltf, export_vertex_color="ACTIVE")
    except TypeError:
        bpy.ops.export_scene.gltf(**gltf, export_colors=True)
    tris = {k: len(o.data.polygons) for k, o in objs.items()}
    ptris = {k: len(o.data.polygons) for k, o in proto_objs.items()}
    print(f"build_exterior: {tris}, prototypes {ptris}, {len(placements)} instances -> {OUT} ({time.time() - t0:.1f}s)")

    scene = bpy.context.scene
    rcoll = B.collection("Review")
    review.setup_scene(scene, rcoll, materials)
    path = os.path.join(BLENDER_DIR, "kiosk_exterior.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, check_existing=False)

    if "--render" in ARGV:
        cams = review.cameras(rcoll)
        for name, (loc, tgt, lens) in list(C.EXTERIOR_REVIEW_CAMS.items()) + [("UnderCounter", C.KITCHEN_REVIEW_CAMS["UnderCounter"]),
                                                                              ("LeftSign", C.GRAPHICS_REVIEW_CAMS["LeftSign"])]:
            cams[name] = review.look_camera(rcoll, f"CAM_{name}", loc, tgt, lens)
        tag = opt("--tag", "exterior")
        res = tuple(int(v) for v in opt("--res", "1600x900").split("x"))
        os.makedirs(os.path.join(BLENDER_DIR, "renders"), exist_ok=True)
        for key in opt("--cams", "Mid,A,B,ExtDoorSide,ExtDoorCorner,ExtService,ExtFrontLow").split(","):
            review.render(scene, cams[key], os.path.join(BLENDER_DIR, "renders", f"{tag}_{key}.png"), res)


if __name__ == "__main__":
    main()
