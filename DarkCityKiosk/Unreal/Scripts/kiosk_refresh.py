"""Brings a re-exported kiosk into L_DarkCity without rebuilding the scene (setup_scene.py does
everything from scratch; this touches only the kiosk):

1. imports RawContent/<dck.KIOSK_GLB>.glb in place (as import_kiosk.py does),
2. places an SM_Kiosk_* actor for every kiosk mesh at the kiosk origin (new sections, such as
   SM_Kiosk_Structure from the 2026-10-04 massing pass, appear here),
3. re-applies the kiosk material tuning from scene_config (EMISSIVE, EMISSIVE_COLOR,
   KIOSK_ROUGHNESS), since the import rewrites the material instances,
4. re-applies the weathered materials (kiosk_weather.py, surfacing pass) to the re-imported slots,
5. moves the kiosk lights that follow the kiosk geometry (soffit tubes, canopy spill, corner
   sign, the ramen lantern, window lightbox, and the interior light from scene_config.INTERIOR) to the
   positions in kiosk_config. Intensities and colours stay as they are.
6. re-applies the signage pass (kiosk_graphics.apply(): overrides, decals, the 24h sign light).
7. re-applies the kitchen pass (kiosk_kitchen.apply(full=True)): re-trims the old interior out of copies of the
   re-imported ServiceSide / Body and puts them back on those actors, the kitchen actors, instances and lights.
8. re-applies the exterior pass (kiosk_exterior.apply(full=True)): re-trims the old ground props out of a copy of
   the re-imported Props and puts it back on that actor, the exterior actors and instances.

    node Scripts/ue.mjs Scripts/kiosk_refresh.py [--no-import]
"""
import importlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402
import scene_config as S  # noqa: E402

dck, S = importlib.reload(dck), importlib.reload(S)
import unreal  # noqa: E402

K = dck.K = importlib.reload(dck.K)
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
args = sys.argv[1:]

dck.ensure_map()

# 1. Import in place: placed actors keep their mesh references
if "--no-import" not in args:
    src = os.path.join(dck.RAW, f"{dck.KIOSK_GLB}.glb")
    task = dck.setp(unreal.AssetImportTask(), filename=src, destination_path=dck.KIOSK_MESHES,
                    automated=True, replace_existing=True, save=True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    print("imported:", len(task.get_editor_property("imported_object_paths")), "objects")

# 2. One actor per kiosk mesh, all at the kiosk origin, like the existing sections
reg = unreal.AssetRegistryHelpers.get_asset_registry()
meshes = [a for a in reg.get_assets_by_path(f"{dck.KIOSK_MESHES}/{dck.KIOSK_GLB}/StaticMeshes", recursive=True)
          if str(a.asset_class_path.asset_name) == "StaticMesh"]
for a in sorted(meshes, key=lambda a: str(a.asset_name)):
    label = str(a.asset_name)
    mesh = unreal.load_asset(str(a.package_name))
    new = dck.find_actor(label) is None
    actor = dck.get_or_spawn(unreal.StaticMeshActor, label, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0), "Kiosk")
    comp = actor.static_mesh_component
    comp.modify()
    if comp.static_mesh != mesh:
        comp.set_static_mesh(mesh)
    b = mesh.get_bounding_box()
    nanite = mesh.get_editor_property("nanite_settings").enabled
    print(f"{label:24} {'NEW ' if new else ''}tris={mesh.get_num_triangles(0)} nanite={nanite} cast_shadow={comp.cast_shadow} "
          f"bounds ({b.min.x:.0f},{b.min.y:.0f},{b.min.z:.0f})..({b.max.x:.0f},{b.max.y:.0f},{b.max.z:.0f})")

# 3. Material tuning (same values setup_scene.tune_kiosk_materials applies)
folder = f"{dck.KIOSK_MESHES}/{dck.KIOSK_GLB}/Materials"
tuned = 0
for table, kind in ((S.EMISSIVE, "EmissiveStrength"), (S.KIOSK_ROUGHNESS, "RoughnessFactor"), (S.EMISSIVE_COLOR, "color")):
    for name, value in table.items():
        path = f"{folder}/{name}"
        if not EAL.does_asset_exist(path):
            continue
        mi = unreal.load_asset(path)
        if kind == "color":
            for param in ("EmissiveFactor", "BaseColorFactor"):
                MEL.set_material_instance_vector_parameter_value(mi, param, unreal.LinearColor(*value, 1.0))
        else:
            MEL.set_material_instance_scalar_parameter_value(mi, kind, value)
        MEL.update_material_instance(mi)
        EAL.save_loaded_asset(mi)
        tuned += 1
print(f"material tuning re-applied: {tuned} values")


# 4. Weathered materials (surfacing pass): the import rewrote the glTF instances, so refresh the
# weathered ones from them and put them back on the slots (slot order can change on import)
if dck.EAL.does_asset_exist("/Game/DarkCity/Kiosk/Weather/M_KioskWeathered"):
    import kiosk_weather  # noqa: E402
    kiosk_weather = importlib.reload(kiosk_weather)
    kiosk_weather.build_instances()
    kiosk_weather.assign()


# 5. Lights that follow the canopy geometry (positions/sizes only)
def move(label, pos, x_dir=None, y_dir=None, width_cm=None):
    a = dck.find_actor(label)
    if a is None:
        print(f"  (no {label}; setup_scene.py creates it)")
        return
    a.modify()
    rot = unreal.MathLibrary.make_rot_from_xy(unreal.Vector(*x_dir), unreal.Vector(*y_dir)) if x_dir else a.get_actor_rotation()
    a.set_actor_location_and_rotation(dck.to_ue(*pos), rot, False, False)
    if width_cm:
        c = a.get_component_by_class(unreal.RectLightComponent)
        c.modify()
        c.set_editor_property("source_width", width_cm)


tilt = math.radians(S.SOFFIT["tilt_to_wall_deg"])
for i, (axis, fixed, a0, a1) in enumerate(K.SOFFIT_TUBES):
    z = K.SOFFIT_TUBE_Z - 0.04  # just under the hanging tube
    if axis == "X":
        move(f"L_Soffit_{i}", ((a0 + a1) / 2, fixed, z), (0, -math.sin(tilt), -math.cos(tilt)), (1, 0, 0), (a1 - a0) * 100)
    else:
        move(f"L_Soffit_{i}", (fixed, (a0 + a1) / 2, z), (math.sin(tilt), 0, -math.cos(tilt)), (0, 1, 0), (a1 - a0) * 100)
d = math.radians(S.CANOPY_SPILL["down_deg"])
mid_z = (K.FACE_Z0 + K.FACE_Z1) / 2  # centre of the lit yellow face
move("L_CanopySpill_Front", ((K.CANOPY_X0 + K.CANOPY_X1) / 2, K.CANOPY_Y0 - 0.06, mid_z), (0, math.cos(d), -math.sin(d)), (1, 0, 0),
     (K.CANOPY_X1 - K.CANOPY_X0 - 0.2) * 100)
move("L_CanopySpill_Left", (K.CANOPY_X0 - 0.06, (K.CANOPY_Y0 + K.CANOPY_Y1) / 2, mid_z), (-math.cos(d), 0, -math.sin(d)), (0, 1, 0),
     (K.CANOPY_Y1 - K.CANOPY_Y0 - 0.2) * 100)
cs = K.CORNER_SIGN
move("L_CornerSign", (cs["x"], cs["y"] - 0.25, (cs["z0"] + cs["z1"]) / 2))
# lights at parts placed from the walls (they move when the body is resized)
ll, lr, w = K.LANTERN_L, K.LANTERN_R, K.WINDOW_LIGHTBOX
move("L_Lantern_L", (ll["x"], ll["y"], ll["z"]))
# L_Lantern_R lights the 24h lightbox since the signage pass; kiosk_graphics.apply() below places it
move("L_Interior", S.INTERIOR["pos"])
move("L_WindowLightbox", ((w["x0"] + w["x1"]) / 2, K.Y0 - w["depth"] - 0.05, (w["z0"] + w["z1"]) / 2), (0, 1, 0), (1, 0, 0),
     (w["x1"] - w["x0"]) * 100)
lb = dck.find_actor("L_WindowLightbox")
if lb:
    c = lb.get_component_by_class(unreal.RectLightComponent)
    c.set_editor_property("source_height", (w["z1"] - w["z0"]) * 100)

# 6. Signage pass (2026-10-05): the graphics overrides (the canopy lettering's slot; slot order can change
# on import), the decals and the 24h sign's light. The cards themselves come from kiosk_graphics.glb.
if dck.EAL.does_asset_exist(f"{dck.GAME}/Kiosk/Graphics/M_KioskGraphic"):
    import kiosk_graphics  # noqa: E402
    kiosk_graphics = importlib.reload(kiosk_graphics)
    kiosk_graphics.apply()

# 7. Kitchen pass (2026-10-09): step 2 put the untrimmed ServiceSide / Body back on their actors
if dck.EAL.does_asset_exist(f"{dck.GAME}/Kiosk/Kitchen/M_Kitchen"):
    import kiosk_kitchen  # noqa: E402
    kiosk_kitchen = importlib.reload(kiosk_kitchen)
    kiosk_kitchen.apply(full=True)

# 8. Exterior pass (2026-10-09): step 2 put the untrimmed Props (with the old ground props) back on its actor
if dck.EAL.does_asset_exist(f"{dck.GAME}/Kiosk/Exterior/M_Exterior"):
    import kiosk_exterior  # noqa: E402
    kiosk_exterior = importlib.reload(kiosk_exterior)
    kiosk_exterior.apply(full=True)

dck.LEVELS.save_current_level()
print("kiosk_refresh: done")
