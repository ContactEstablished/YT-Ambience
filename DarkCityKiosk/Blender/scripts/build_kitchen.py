"""Kitchen pass (2026-10-09, prompt 7): builds the service opening's working kitchen and exports it on
its own, so the kiosk export and its weathering bake stay untouched.

    blender -b --factory-startup -P build_kitchen.py [-- --render [--cams Mid,Shelves,...] [--tag k1]]

Needs: Unreal/RawContent/kiosk_detail.glb (context for the checks; its old interior is trimmed here with
the same rules Unreal uses) and Unreal/RawContent/graphics/graphics_manifest.json with the Kitchen atlas
(node Graphics/make_kiosk_graphics.mjs Kitchen).
Writes:
  Unreal/RawContent/kiosk_kitchen.glb        SM_Kiosk_Kitchen, SM_Kiosk_KitchenCounter, SM_Kiosk_KitchenCards
                                             and the prototypes SM_KP_* (at the origin)
  Unreal/RawContent/kitchen/kitchen.json     prototype placements (Unreal instances them), light rig,
                                             the counter rect for its wear map, the trim rules
  Blender/kiosk_kitchen.blend                kiosk + kitchen for checks; Blender/renders/<tag>_<cam>.png
Then in Unreal: node Scripts/ue.mjs Scripts/kiosk_kitchen.py
"""
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kiosk_config as C  # noqa: E402
import build_kiosk_blockout as B  # noqa: E402
from kiosk import kitchen, masks, review  # noqa: E402

BLENDER_DIR = os.path.dirname(HERE)
RAW = os.path.join(os.path.dirname(BLENDER_DIR), "Unreal", "RawContent")
GFX = os.path.join(RAW, "graphics")
OUT = os.path.join(RAW, "kiosk_kitchen.glb")
OUT_JSON = os.path.join(RAW, "kitchen", "kitchen.json")
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

# The old step-2 interior that Unreal trims out of copies of the kiosk meshes (kiosk_kitchen.py reads these
# from kitchen.json): whole material slots, plus boxes (kiosk frame, m) for parts sharing a kept material.
SW = C.SERVICE_WINDOW
TRIM = {
    "SM_Kiosk_ServiceSide": {
        "materials": ["Interior_Tile", "Interior_Steel", "Stock_Yellow", "Stock_White", "Stock_Green", "Stock_Red", "Stock_Blue",
                      "Paper_White", "Rubber_Black", "Broth", "Wood_Light", "Machine_Body", "Screen_Multi", "Button_Lit_Red",
                      "Button_Lit_Green", "Button_Lit_Yellow"],
        # the old back wall's grout strips and the stock jars' lids on the old shelves; the old coffee
        # machine's spouts (all Steel_Grey, like parts that stay)
        "boxes": [((SW["x0"] - 0.01, C.Y0 + SW["depth"] - 0.20, SW["z0"] + 0.05), (SW["x1"] + 0.01, C.Y0 + SW["depth"] - 0.01, SW["z1"] + 0.06)),
                  ((SW["x0"] + 0.12, C.Y0 + SW["depth"] - 0.40, SW["z0"] + 0.15), (SW["x0"] + 0.32, C.Y0 + SW["depth"] - 0.32, SW["z0"] + 0.26))],
    },
    # the service recess's lining (the glazed window's shallow recess keeps its own)
    "SM_Kiosk_Body": {"materials_in_box": [("Interior_Recess", ((SW["x0"] - 0.01, C.Y0 - 0.12, SW["z0"] - 0.01),
                                                                (SW["x1"] + 0.01, C.Y0 + SW["depth"] + 0.01, SW["z1"] + 0.01)))]},
}


def opt(name, default):
    return ARGV[ARGV.index(name) + 1] if name in ARGV else default


def card_material():
    m = bpy.data.materials.new("KG_Kitchen")
    nt = m.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    img = nt.nodes.new("ShaderNodeTexImage")
    path = os.path.join(GFX, "T_KG_Kitchen_C.png")
    if os.path.exists(path):
        img.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(img.outputs["Alpha"], bsdf.inputs["Alpha"])
    nt.links.new(img.outputs["Color"], bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 0.0
    return m


def import_context():
    """The kiosk as Unreal sees it, with the old interior trimmed by the same rules (also checks them)."""
    kiosk = B.collection("Kiosk")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=os.path.join(RAW, "kiosk_detail.glb"))
    objs = [o for o in bpy.data.objects if o not in before and o.type == "MESH"]
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        kiosk.objects.link(o)
    # apply transforms (some sections import with a node transform)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    import bmesh
    for o in objs:
        name = o.name.split(".")[0]
        rule = TRIM.get(name)
        if not rule:
            continue
        mats = [s.material.name.split(".")[0] if s.material else "" for s in o.material_slots]
        bm = bmesh.new()
        bm.from_mesh(o.data)
        kill = []
        for f in bm.faces:
            mn = mats[f.material_index] if f.material_index < len(mats) else ""
            c = f.calc_center_median()
            if mn in rule.get("materials", []):
                kill.append(f)
                continue
            if any(all(lo[i] <= v.co[i] <= hi[i] for v in f.verts for i in range(3)) for lo, hi in rule.get("boxes", [])):
                kill.append(f)
                continue
            for mname, (lo, hi) in rule.get("materials_in_box", []):
                if mn == mname and all(lo[i] <= c[i] <= hi[i] for i in range(3)):
                    kill.append(f)
                    break
        bmesh.ops.delete(bm, geom=kill, context="FACES")
        bm.to_mesh(o.data)
        bm.free()
        print(f"  trimmed {name}: {len(kill)} faces")
    return objs


def counter_uv1(ob):
    """UV1 = 0..1 over the customer counter (its wear map), image top row at the wall side."""
    import numpy as np
    me = ob.data
    co = C.COUNTER
    x0, x1 = co["x0"], co["x1"]
    y0, y1 = C.Y0 - co["projection"] - 0.01, C.Y0
    uv = []
    for p in me.polygons:
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv.append(((v.x - x0) / (x1 - x0), (v.y - y0) / (y1 - y0)))
    layer = me.uv_layers.new(name="WearUV")
    layer.data.foreach_set("uv", np.array(uv, np.float32).ravel())
    me.uv_layers.active = me.uv_layers[0]
    return {"x0": x0, "x1": x1, "y0": y0, "y1": y1}


def set_masks(ob, rgba):
    attrs = ob.data.color_attributes
    if "Masks" in attrs:
        attrs.remove(attrs["Masks"])
    layer = attrs.new("Masks", "FLOAT_COLOR", "POINT")
    layer.data.foreach_set("color", list(rgba) * len(ob.data.vertices))
    attrs.active_color = layer
    attrs.render_color_index = attrs.active_color_index


def bake_masks(objs, others):
    """Edge / occlusion / cavity masks in vertex colours (kiosk/masks.py), only the kitchen visible."""
    hidden = [o for o in others if not o.hide_render]
    for o in hidden:
        o.hide_render = True
    masks.bake_masks(objs)
    for o in hidden:
        o.hide_render = False


def preview_lights(coll, rig):
    for name, L in rig.items():
        if L["type"] == "rect":
            ld = bpy.data.lights.new(name, "AREA")
            ld.shape, ld.size, ld.size_y = "RECTANGLE", L["w"], L["h"]
            ld.energy = 25 if "Prep" in name else 4
            ob = bpy.data.objects.new(name, ld)
            ob.location = L["pos"]
            d = Vector(L["x_dir"])
            ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
        elif L["type"] == "spot":
            ld = bpy.data.lights.new(name, "SPOT")
            ld.energy, ld.spot_size = 6, math.radians(L["cone"] * 2)
            ob = bpy.data.objects.new(name, ld)
            ob.location = L["pos"]
            ob.rotation_euler = Vector(L["dir"]).to_track_quat("-Z", "Y").to_euler()
        else:
            continue
        ld.color = (1.0, 0.78, 0.55)
        coll.objects.link(ob)


def main():
    t0 = time.time()
    B.reset_scene()
    B.init_shared()
    materials = kitchen.ensure_materials(B)
    card_material()
    man = json.load(open(os.path.join(GFX, "graphics_manifest.json"), encoding="utf-8"))
    if not any(it["atlas"] == "Kitchen" for it in man["items"].values()):
        raise RuntimeError("no Kitchen atlas in graphics_manifest.json: run node Graphics/make_kiosk_graphics.mjs Kitchen")
    context = import_context()

    kcoll = B.collection("Kitchen")
    pcoll = B.collection("KitchenProto")
    icoll = B.collection("KitchenInstances")
    objs, protos, placements, rig, pieces = kitchen.build(B, kcoll, man)
    proto_objs = {name: pm.build(pcoll, materials) for name, pm in protos.items()}

    # masks: the fixed kitchen in place; prototypes spread on a grid so they don't occlude each other
    bake_masks([objs["kitchen"]], context)
    names = sorted(proto_objs)
    for k, n in enumerate(names):
        proto_objs[n].location = (20 + (k % 8) * 1.0, 20 + (k // 8) * 1.0, 0)
    bake_masks([proto_objs[n] for n in names], context + [objs["kitchen"], objs["counter"], objs["cards"]])
    for n in names:
        proto_objs[n].location = (0, 0, 0)
    set_masks(objs["counter"], (0.0, 1.0, 0.0, 1.0))  # the counter sheet has its own wear map
    rect = counter_uv1(objs["counter"])

    # preview instances (not exported)
    for n, pos, yaw, s in placements:
        o = bpy.data.objects.new(f"I_{n}", proto_objs[n].data)
        o.location = pos
        o.rotation_euler = (0, 0, math.radians(yaw))
        o.scale = (s, s, s)
        icoll.objects.link(o)

    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    data = {"props": [{"name": n, "pos": list(p), "yaw": y, "scale": s} for n, p, y, s in placements],
            "lights": rig, "counter_uv": rect, "trim": TRIM, "materials": {k: [list(v[0]), v[1], v[2], v[3]] for k, v in kitchen.MATERIALS.items()},
            "counter_pieces": [list(p) for p in pieces]}
    json.dump(data, open(OUT_JSON, "w", encoding="utf-8"), indent=1)

    bpy.ops.object.select_all(action="DESELECT")
    for o in list(objs.values()) + list(proto_objs.values()):
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs["kitchen"]
    gltf = dict(filepath=OUT, export_format="GLB", use_selection=True, export_apply=True, export_yup=True,
                export_cameras=False, export_lights=False, export_image_format="NONE")
    try:
        bpy.ops.export_scene.gltf(**gltf, export_vertex_color="ACTIVE")
    except TypeError:
        bpy.ops.export_scene.gltf(**gltf, export_colors=True)
    tris = {k: len(o.data.polygons) for k, o in objs.items()}
    ptris = sum(len(o.data.polygons) for o in proto_objs.values())
    print(f"build_kitchen: {tris}, {len(proto_objs)} prototypes ({ptris} faces), {len(placements)} instances, "
          f"{len(rig)} lights -> {OUT} ({time.time() - t0:.1f}s)")

    scene = bpy.context.scene
    rcoll = B.collection("Review")
    review.setup_scene(scene, rcoll, materials)
    for o in list(rcoll.objects):
        if o.name == "L_Interior":
            bpy.data.objects.remove(o, do_unlink=True)
    preview_lights(rcoll, rig)
    path = os.path.join(BLENDER_DIR, "kiosk_kitchen.blend")
    bpy.ops.wm.save_as_mainfile(filepath=path, check_existing=False)

    if "--render" in ARGV:
        cams = review.cameras(rcoll)
        for name, (loc, tgt, lens) in list(C.KITCHEN_REVIEW_CAMS.items()) + [("ServiceWindow", C.REVIEW_CAMS["ServiceWindow"])]:
            cams[name] = review.look_camera(rcoll, f"CAM_{name}", loc, tgt, lens)
        hc = C.HERO_CAM
        tag = opt("--tag", "kitchen")
        os.makedirs(os.path.join(BLENDER_DIR, "renders"), exist_ok=True)
        for key in opt("--cams", "Mid,ServiceWindow,KitchenShelves,KitchenPOS,CounterTop,UnderCounter").split(","):
            review.render(scene, cams[key], os.path.join(BLENDER_DIR, "renders", f"{tag}_{key}.png"), (1600, 900))
        _ = hc


if __name__ == "__main__":
    main()
