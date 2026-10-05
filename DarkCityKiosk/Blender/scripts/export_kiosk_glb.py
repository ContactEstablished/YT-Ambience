"""Exports the kiosk blockout for Unreal: one mesh per section (Body, Canopy, Roof, ...),
with booleans applied and sign text converted to geometry.

    blender -b ../kiosk_blockout.blend --factory-startup -P export_kiosk_glb.py
    blender -b ../kiosk_detail.blend --factory-startup -P export_kiosk_glb.py [-- --no-weather]

The detailed kiosk also gets its surfacing data: vertex-colour masks (kiosk/masks.py) and the
weathering bake (kiosk/weather.py: WeatherUV + Unreal/RawContent/weather/T_KioskWear_*.png).

Writes Unreal/RawContent/<blend name>.glb. The .blend on disk is not modified.
All meshes keep the kiosk frame (origin = footprint centre at ground level), so every
section is placed at the same actor origin in Unreal.
"""

import os

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(os.path.dirname(HERE))
# Named after the .blend: kiosk_blockout.blend -> kiosk_blockout.glb, kiosk_detail.blend -> kiosk_detail.glb
OUT = os.path.join(PROJECT_DIR, "Unreal", "RawContent", os.path.splitext(os.path.basename(bpy.data.filepath))[0] + ".glb")


def select_only(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]


# Bake modifiers (the window cut-outs) into the body mesh, then drop helpers.
for ob in list(bpy.data.objects):
    if ob.type == "MESH" and ob.modifiers:
        select_only([ob])
        for mod in list(ob.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)
for ob in list(bpy.data.objects):
    if ob.type == "CAMERA" or ob.name.startswith("Cutter_") or ob.name == "Ground":
        bpy.data.objects.remove(ob, do_unlink=True)

# Text -> mesh
fonts = [o for o in bpy.data.objects if o.type == "FONT"]
if fonts:
    select_only(fonts)
    bpy.ops.object.convert(target="MESH")

# One object per section collection
kiosk = bpy.data.collections["Kiosk"]
for coll in kiosk.children:
    objs = [o for o in coll.objects if o.type == "MESH"]
    if not objs:
        continue
    select_only(objs)
    if len(objs) > 1:
        bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = f"SM_Kiosk_{coll.name}"
    joined.data.name = joined.name
    print(f"{joined.name}: {len(joined.data.polygons)} faces, {len(joined.material_slots)} materials")

# Step 5 texture prep: surfacing masks in vertex colours (detailed kiosk only)
if "kiosk_detail" in OUT:
    import sys
    sys.path.insert(0, HERE)
    from kiosk import masks
    masks.bake_masks([o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("SM_Kiosk_")])
    # Surfacing pass (2026-10-04): weathering masks + the WeatherUV channel (kiosk/weather.py).
    # --no-weather skips it (the glTF then has no TEXCOORD_1 and Unreal's weathered materials go flat).
    if "--no-weather" not in sys.argv:
        import kiosk_config as C
        from kiosk import weather
        weather.build([bpy.data.objects[f"SM_Kiosk_{s}"] for s in C.WEATHER["sections"] if f"SM_Kiosk_{s}" in bpy.data.objects])

os.makedirs(os.path.dirname(OUT), exist_ok=True)
gltf_args = dict(filepath=OUT, export_format="GLB", use_selection=False, export_apply=True, export_yup=True,
                 export_cameras=False, export_lights=False)
try:
    bpy.ops.export_scene.gltf(**gltf_args, export_vertex_color="ACTIVE")
except TypeError:  # older exporters
    bpy.ops.export_scene.gltf(**gltf_args, export_colors=True)
print(f"exported {OUT}")
