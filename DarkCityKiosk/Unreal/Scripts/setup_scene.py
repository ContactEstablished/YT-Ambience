"""Builds/refreshes L_DarkCity from kiosk_config.py + scene_config.py: kiosk blockout,
wet ground (EasyRain puddles), fog, sky light, post process, kiosk lights, placeholder
city, and the EasyRain actor. Safe to re-run: actors are found by label and updated.

    node Scripts/ue.mjs Scripts/setup_scene.py
"""
import importlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402

dck = importlib.reload(dck)
import scene_config as S  # noqa: E402

S = importlib.reload(S)
import unreal  # noqa: E402

K = dck.K
MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()
MAT = f"{dck.GAME}/Materials"
to_ue = dck.to_ue


def setp(obj, **props):
    for k, v in props.items():
        try:
            obj.set_editor_property(k, v)
        except Exception as e:  # noqa: BLE001
            print(f"  (skip {type(obj).__name__}.{k}: {str(e).splitlines()[0][:90]})")
    return obj


# ---- Material helpers ---------------------------------------------------------

def material(folder, name):
    path = f"{folder}/{name}"
    if EAL.does_asset_exist(path):
        m = unreal.load_asset(path)
        MEL.delete_all_material_expressions(m)
        for _ in range(3):
            left = list(MEL.get_material_expressions(m))
            if not left:
                break
            for e in left:
                MEL.delete_material_expression(m, e)
        return m
    dck.ensure_dir(folder)
    return TOOLS.create_asset(name, folder, unreal.Material, unreal.MaterialFactoryNew())


def expr(m, cls, x, y, **props):
    return setp(MEL.create_material_expression(m, cls, x, y), **props)


def link(a, a_out, b, b_in):
    if not MEL.connect_material_expressions(a, a_out, b, b_in):
        print(f"  !! link failed: {a.get_name()}.{a_out} -> {b.get_name()}.{b_in}")


def out(m, e, e_out, prop):
    if not MEL.connect_material_property(e, e_out, prop):
        print(f"  !! output failed: {e.get_name()}.{e_out} -> {prop}")


def finish(m):
    MEL.recompile_material(m)
    EAL.save_loaded_asset(m)


def instance(name, parent, scalars=None, vectors=None):
    path = f"{MAT}/{name}"
    mi = unreal.load_asset(path) if EAL.does_asset_exist(path) else TOOLS.create_asset(
        name, MAT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(mi, parent)
    for k, v in (scalars or {}).items():
        MEL.set_material_instance_scalar_parameter_value(mi, k, v)
    for k, v in (vectors or {}).items():
        MEL.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(v[0], v[1], v[2], 1.0))
    MEL.update_material_instance(mi)
    EAL.save_loaded_asset(mi)
    return mi


def build_materials():
    # Wet concrete street with EasyRain puddles in the low spots (ground.py).
    import ground as ground_mod
    ground = importlib.reload(ground_mod).build()

    # Unlit emissive (placeholder billboards / screens)
    m = material(MAT, "M_Emissive")
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    c = expr(m, unreal.MaterialExpressionVectorParameter, -500, 0, parameter_name="Color", default_value=unreal.LinearColor(1, 1, 1, 1))
    i = expr(m, unreal.MaterialExpressionScalarParameter, -500, 200, parameter_name="Intensity", default_value=10.0)
    mul = expr(m, unreal.MaterialExpressionMultiply, -250, 0)
    link(c, "", mul, "A")
    link(i, "", mul, "B")
    out(m, mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    finish(m)
    emissive = m

    # Plain lit surface (placeholder buildings, viaduct)
    m = material(MAT, "M_Plain")
    c = expr(m, unreal.MaterialExpressionVectorParameter, -500, 0, parameter_name="BaseColor", default_value=unreal.LinearColor(0.2, 0.2, 0.2, 1))
    r = expr(m, unreal.MaterialExpressionScalarParameter, -500, 200, parameter_name="Roughness", default_value=0.6)
    out(m, c, "", unreal.MaterialProperty.MP_BASE_COLOR)
    out(m, r, "", unreal.MaterialProperty.MP_ROUGHNESS)
    finish(m)
    building = instance("MI_Building_Dark", m, {"Roughness": 0.55}, {"BaseColor": S.BUILDING_COLOR})
    return ground, emissive, building


def tune_kiosk_materials():
    folder = f"{dck.KIOSK_MESHES}/{dck.KIOSK_GLB}/Materials"
    for name, strength in S.EMISSIVE.items():
        path = f"{folder}/{name}"
        if EAL.does_asset_exist(path):
            mi = unreal.load_asset(path)
            MEL.set_material_instance_scalar_parameter_value(mi, "EmissiveStrength", strength)
            MEL.update_material_instance(mi)
            EAL.save_loaded_asset(mi)
    for name, rgb in S.EMISSIVE_COLOR.items():
        path = f"{folder}/{name}"
        if EAL.does_asset_exist(path):
            mi = unreal.load_asset(path)
            for param in ("EmissiveFactor", "BaseColorFactor"):
                MEL.set_material_instance_vector_parameter_value(mi, param, unreal.LinearColor(*rgb, 1.0))
            MEL.update_material_instance(mi)
            EAL.save_loaded_asset(mi)
    # Wet paint and steel read glossier
    for name, rough in S.KIOSK_ROUGHNESS.items():
        path = f"{folder}/{name}"
        if EAL.does_asset_exist(path):
            mi = unreal.load_asset(path)
            MEL.set_material_instance_scalar_parameter_value(mi, "RoughnessFactor", rough)
            MEL.update_material_instance(mi)
            EAL.save_loaded_asset(mi)


# ---- Actor helpers ---------------------------------------------------------------

CUBE = unreal.load_asset("/Engine/BasicShapes/Cube")
PLANE = unreal.load_asset("/Engine/BasicShapes/Plane")


def mesh_actor(label, mesh, location, rotation, scale, material=None, folder=None):
    a = dck.get_or_spawn(unreal.StaticMeshActor, label, location, rotation, folder)
    comp = a.static_mesh_component
    comp.modify()
    comp.set_static_mesh(mesh)
    a.set_actor_scale3d(scale)
    if material:
        for i in range(comp.get_num_materials()):
            comp.set_material(i, material)
    return a


def rect_light(label, pos, x_dir, y_dir, width_cm, height_cm, intensity, color=None, temperature=None, radius_m=12, folder="Lights/Kiosk"):
    rot = unreal.MathLibrary.make_rot_from_xy(unreal.Vector(*x_dir), unreal.Vector(*y_dir))
    a = dck.get_or_spawn(unreal.RectLight, label, to_ue(*pos), rot, folder)
    c = a.get_component_by_class(unreal.RectLightComponent)
    c.modify()
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    setp(c, intensity_units=unreal.LightUnits.CANDELAS, source_width=width_cm, source_height=height_cm,
         attenuation_radius=radius_m * 100.0, barn_door_angle=60.0, barn_door_length=10.0,
         volumetric_scattering_intensity=S.KIOSK_LIGHT_VOLUMETRIC)
    c.set_intensity(intensity * S.LIGHT_SCALE)
    if temperature:
        setp(c, use_temperature=True, temperature=float(temperature))
        c.set_light_color(unreal.LinearColor(1, 1, 1, 1))
    elif color:
        setp(c, use_temperature=False)
        c.set_light_color(unreal.LinearColor(*color, 1.0))
    return a


def point_light(label, pos, intensity, radius_m, source_radius_cm=5, color=None, temperature=None, folder="Lights/Kiosk"):
    a = dck.get_or_spawn(unreal.PointLight, label, to_ue(*pos), unreal.Rotator(0, 0, 0), folder)
    c = a.get_component_by_class(unreal.PointLightComponent)
    c.modify()
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    setp(c, intensity_units=unreal.LightUnits.CANDELAS, attenuation_radius=radius_m * 100.0, source_radius=float(source_radius_cm),
         volumetric_scattering_intensity=S.KIOSK_LIGHT_VOLUMETRIC)
    c.set_intensity(intensity * S.LIGHT_SCALE)
    if temperature:
        setp(c, use_temperature=True, temperature=float(temperature))
        c.set_light_color(unreal.LinearColor(1, 1, 1, 1))
    elif color:
        setp(c, use_temperature=False)
        c.set_light_color(unreal.LinearColor(*color, 1.0))
    return a


def unit(v):
    n = math.sqrt(sum(x * x for x in v))
    return tuple(x / n for x in v)


# ---- Build -------------------------------------------------------------------------

dck.ensure_map()
ground_mi, emissive_mat, building_mi = build_materials()
tune_kiosk_materials()

# Kiosk blockout meshes (all share the kiosk origin)
reg = unreal.AssetRegistryHelpers.get_asset_registry()
for a in reg.get_assets_by_path(f"{dck.KIOSK_MESHES}/{dck.KIOSK_GLB}/StaticMeshes", recursive=True):
    if str(a.asset_class_path.asset_name) == "StaticMesh":
        mesh_actor(str(a.asset_name), unreal.load_asset(str(a.package_name)), unreal.Vector(0, 0, 0),
                   unreal.Rotator(0, 0, 0), unreal.Vector(1, 1, 1), folder="Kiosk")

# Ground
size = S.GROUND["size_m"]
mesh_actor("Ground", PLANE, unreal.Vector(0, 0, -0.5), unreal.Rotator(0, 0, 0), unreal.Vector(size, size, 1), ground_mi, "Environment")

# Fog and sky light (atmosphere.py: also runnable on its own)
import atmosphere  # noqa: E402

atmosphere = importlib.reload(atmosphere)
atmosphere.apply()

# Post process: locked exposure (auto exposure pumps with flashing signs), Lumen hit-lighting reflections
ppv = dck.get_or_spawn(unreal.PostProcessVolume, "PostProcess", unreal.Vector(0, 0, 0), folder="Atmosphere")
ppv.modify()
ppv.set_editor_property("unbound", True)
pp = ppv.get_editor_property("settings")
for k, v in (("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL),
             ("auto_exposure_apply_physical_camera_exposure", False),
             ("auto_exposure_bias", S.EXPOSURE_BIAS),
             ("bloom_intensity", S.BLOOM),
             ("vignette_intensity", S.VIGNETTE),
             ("lumen_final_gather_quality", 2.0),
             ("lumen_reflection_quality", 2.0),
             ("lumen_max_roughness_to_trace_reflections", 0.6)):
    setp(pp, **{f"override_{k}": True, k: v})
try:
    setp(pp, override_lumen_ray_lighting_mode=True, lumen_ray_lighting_mode=unreal.LumenRayLightingModeOverride.HIT_LIGHTING_FOR_REFLECTIONS)
except AttributeError as e:
    print("  (no hit-lighting enum)", e)
ppv.set_editor_property("settings", pp)

# ---- Kiosk lights
cb = K.CANOPY_BOTTOM
for i, (axis, fixed, a0, a1) in enumerate(K.SOFFIT_TUBES):
    tilt = math.radians(S.SOFFIT["tilt_to_wall_deg"])
    if axis == "X":  # front band: wall is at +Y (Blender) = -Y (Unreal)
        pos, x_dir, y_dir = ((a0 + a1) / 2, fixed, K.SOFFIT_TUBE_Z - 0.04), (0, -math.sin(tilt), -math.cos(tilt)), (1, 0, 0)
    else:  # left band: wall is at +X
        pos, x_dir, y_dir = (fixed, (a0 + a1) / 2, K.SOFFIT_TUBE_Z - 0.04), (math.sin(tilt), 0, -math.cos(tilt)), (0, 1, 0)
    rect_light(f"L_Soffit_{i}", pos, x_dir, y_dir, (a1 - a0) * 100, S.SOFFIT["height_cm"], S.SOFFIT["intensity_cd"],
               temperature=S.SOFFIT["temperature"])

# Glow from the lit canopy faces onto the ground and rain
sp = S.CANOPY_SPILL
d = math.radians(sp["down_deg"])
mid_z = (K.FACE_Z0 + K.FACE_Z1) / 2  # centre of the lit yellow face
rect_light("L_CanopySpill_Front", ((K.CANOPY_X0 + K.CANOPY_X1) / 2, K.CANOPY_Y0 - 0.06, mid_z),
           (0, math.cos(d), -math.sin(d)), (1, 0, 0), (K.CANOPY_X1 - K.CANOPY_X0 - 0.2) * 100, 40,
           sp["intensity_cd"], color=sp["color"], radius_m=18)
rect_light("L_CanopySpill_Left", (K.CANOPY_X0 - 0.06, (K.CANOPY_Y0 + K.CANOPY_Y1) / 2, mid_z),
           (-math.cos(d), 0, -math.sin(d)), (0, 1, 0), (K.CANOPY_Y1 - K.CANOPY_Y0 - 0.2) * 100, 40,
           sp["intensity_cd"], color=sp["color"], radius_m=18)

it = S.INTERIOR
point_light("L_Interior", it["pos"], it["intensity_cd"], it["radius_m"], 15, temperature=it["temperature"])
ll, lr, lt = K.LANTERN_L, K.LANTERN_R, S.LANTERN_LIGHT
point_light("L_Lantern_L", (ll["x"], ll["y"], ll["z"]), lt["intensity_cd"], lt["radius_m"], ll["radius"] * 100, temperature=lt["temperature"])
point_light("L_Lantern_R", (lr["x"], lr["y"], lr["z"]), lt["intensity_cd"], lt["radius_m"], lr["radius"] * 100, temperature=lt["temperature"])
w = K.WINDOW_LIGHTBOX
rect_light("L_WindowLightbox", ((w["x0"] + w["x1"]) / 2, K.Y0 - w["depth"] - 0.05, (w["z0"] + w["z1"]) / 2),
           (0, 1, 0), (1, 0, 0), (w["x1"] - w["x0"]) * 100, (w["z1"] - w["z0"]) * 100,
           S.WINDOW_LIGHTBOX_LIGHT["intensity_cd"], temperature=S.WINDOW_LIGHTBOX_LIGHT["temperature"], radius_m=6)
cs = K.CORNER_SIGN
point_light("L_CornerSign", (cs["x"], cs["y"] - 0.25, (cs["z0"] + cs["z1"]) / 2), S.CORNER_SIGN_LIGHT["intensity_cd"],
            S.CORNER_SIGN_LIGHT["radius_m"], 10, color=S.CORNER_SIGN_LIGHT["color"])

# ---- Placeholder city (replaced by the scripted city: setup_city.py)
if not S.PLACEHOLDER_CITY:
    for actor in dck.ACTORS.get_all_level_actors():
        if actor.get_actor_label().startswith(("City_Tower_", "City_Billboard_", "L_Billboard_")):
            actor.destroy_actor()
towers = []
for i, (hd, dist, tw, td, th) in enumerate(S.TOWERS if S.PLACEHOLDER_CITY else []):
    hr = math.radians(hd)
    cx, cy = dist * math.cos(hr), dist * math.sin(hr)
    yaw = dck.heading_to_ue_yaw(hd)
    mesh_actor(f"City_Tower_{i:02d}", CUBE, to_ue(cx, cy, th / 2), unreal.Rotator(0, 0, yaw),
               unreal.Vector(td, tw, th), building_mi, "City/Placeholder")
    towers.append((hr, dist, tw, td, th, yaw))
for j, (ti, bw, bh, bz, color, nits) in enumerate(S.BILLBOARDS if S.PLACEHOLDER_CITY else []):
    hr, dist, tw, td, th, yaw = towers[ti]
    r = dist - td / 2 - 0.3
    nits *= S.BILLBOARD_SCALE
    mi = instance(f"MI_Billboard_{j:02d}", emissive_mat, {"Intensity": float(nits)}, {"Color": color})
    mesh_actor(f"City_Billboard_{j:02d}", CUBE, to_ue(r * math.cos(hr), r * math.sin(hr), bz + bh / 2),
               unreal.Rotator(0, 0, yaw), unreal.Vector(0.2, bw, bh), mi, "City/Placeholder")
    if S.BILLBOARD_LIGHT["enabled"]:
        rl = r - 0.5
        inward = (-math.cos(hr), math.sin(hr), 0.0)  # toward the kiosk, in Unreal axes (Y flipped)
        a = rect_light(f"L_Billboard_{j:02d}", (rl * math.cos(hr), rl * math.sin(hr), bz + bh / 2), inward, (math.sin(hr), math.cos(hr), 0.0),
                       bw * 100, bh * 100, nits * bw * bh / S.LIGHT_SCALE, color=color, radius_m=S.BILLBOARD_LIGHT["radius_m"], folder="Lights/City")
        c = a.get_component_by_class(unreal.RectLightComponent)
        setp(c, cast_shadows=False, volumetric_scattering_intensity=S.BILLBOARD_LIGHT["volumetric_scattering"], barn_door_angle=88.0)
v = S.VIADUCT
if not S.PLACEHOLDER_VIADUCT:
    for actor in dck.ACTORS.get_all_level_actors():
        if actor.get_actor_label().startswith("City_Viaduct_") and actor.get_actor_label() != "City_Viaduct":
            actor.destroy_actor()
if S.PLACEHOLDER_VIADUCT:
  mesh_actor("City_Viaduct_Deck", CUBE, to_ue((v["x0"] + v["x1"]) / 2, (v["y0"] + v["y1"]) / 2, v["deck_z"] + v["deck_h"] / 2),
           unreal.Rotator(0, 0, 0), unreal.Vector(v["x1"] - v["x0"], v["y1"] - v["y0"], v["deck_h"]), building_mi, "City/Placeholder")
for actor in dck.ACTORS.get_all_level_actors():  # pillar count changes with the viaduct length
    if actor.get_actor_label().startswith("City_Viaduct_Pillar_"):
        actor.destroy_actor()
x = v["x0"] + v["pillar_every_m"] / 2
n = 0
while S.PLACEHOLDER_VIADUCT and x < v["x1"]:
    mesh_actor(f"City_Viaduct_Pillar_{n:02d}", CUBE, to_ue(x, (v["y0"] + v["y1"]) / 2, v["deck_z"] / 2), unreal.Rotator(0, 0, 0),
               unreal.Vector(v["pillar_w"], v["pillar_w"], v["deck_z"]), building_mi, "City/Placeholder")
    x += v["pillar_every_m"]
    n += 1

# ---- Rain
rain_cls = EAL.load_blueprint_class("/Game/EasyRain/Blueprints/BP_EasyRain")
rain = dck.get_or_spawn(rain_cls, "EasyRain", folder="Weather")
for k, val in S.RAIN.items():
    setp(rain, **{k: val})

dck.LEVELS.save_current_level()
print("setup_scene: done;", len(dck.ACTORS.get_all_level_actors()), "actors in", dck.world().get_path_name())
