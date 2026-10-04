"""Imports the scripted city (RawContent/city.glb + city_manifest.json) into L_DarkCity:
places the meshes, swaps facade materials for the procedural window shader (M_Windows),
sets emissive strengths, and adds glow lights for the screens and shopfronts.

    node Scripts/ue.mjs Scripts/setup_city.py
Re-runnable: re-imports in place, finds actors by label.
"""
import importlib
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402
import matkit as mk  # noqa: E402
import scene_config as S  # noqa: E402

dck, mk, S = importlib.reload(dck), importlib.reload(mk), importlib.reload(S)
import unreal  # noqa: E402

CITY = f"{dck.GAME}/City"
GEOM = f"{CITY}/Geometry"
MATS = f"{CITY}/Materials"
CS = S.CITY

# Procedural windows on metre-scale UVs (u along the facade, v = height; glTF flips V).
# Returns rgb = window emission, a = 1 inside a window pane, 0 on the wall between panes.
WINDOW_HLSL = r"""
float2 p = float2(UV.x, -UV.y);
float2 g = p / float2(BayW, FloorH);
float2 cell = floor(g);
float2 f = frac(g);
float win = step(abs(f.x - 0.5), WinW * 0.5) * step(abs(f.y - 0.5), WinH * 0.5);
float h1 = frac(sin(dot(cell, float2(12.9898, 78.233))) * 43758.5453);
float h2 = frac(sin(dot(cell, float2(39.3468, 11.1350))) * 24634.6345);
float h3 = frac(sin(dot(cell, float2(73.1560, 52.2350))) * 13579.2468);
float floorBias = frac(sin(cell.y * 17.13 + floor(p.x / 40.0) * 3.7) * 9631.5);
float lit = step(h1, LitFraction * (0.4 + 1.2 * floorBias));
float3 warm = float3(1.0, 0.70, 0.42);
float3 cool = float3(0.72, 0.88, 1.0);
float3 teal = float3(0.35, 1.0, 0.85);
float3 col = h2 < WarmFraction ? warm : (h2 < 0.94 ? cool : teal);
float interior = lerp(0.55, 1.2, saturate(f.y * 1.3 - 0.15)) * (h3 < 0.25 ? 0.45 : 1.0);
float3 e = col * lit * interior * Intensity * (0.6 + 0.8 * h3);
return float4(e * win, win);
"""


def build_window_material():
    m = mk.material(MATS, "M_Windows")
    tc = mk.expr(m, unreal.MaterialExpressionTextureCoordinate, -1400, 0)
    params = {k: mk.scalar(m, k, v, -1400, 120 + i * 90) for i, (k, v) in enumerate(
        (("FloorH", 3.6), ("BayW", 1.6), ("WinW", 0.9), ("WinH", 0.78), ("LitFraction", 0.22),
         ("WarmFraction", 0.55), ("Intensity", 4.0)))}
    c = mk.custom(m, WINDOW_HLSL, ["UV"] + list(params), unreal.CustomMaterialOutputType.CMOT_FLOAT4, -1000, 0, "Windows")
    mk.link(tc, "", c, "UV")
    for k, e in params.items():
        mk.link(e, "", c, k)
    rgb = mk.expr(m, unreal.MaterialExpressionComponentMask, -700, 0, r=True, g=True, b=True, a=False)
    mk.link(c, "", rgb, "")
    a = mk.expr(m, unreal.MaterialExpressionComponentMask, -700, 150, r=False, g=False, b=False, a=True)
    mk.link(c, "", a, "")
    glass = mk.vector(m, "GlassColor", (0.02, 0.025, 0.03), -700, 300)
    wall = mk.vector(m, "WallColor", (0.06, 0.06, 0.065), -700, 420)
    base = mk.expr(m, unreal.MaterialExpressionLinearInterpolate, -400, 300)
    mk.link(wall, "", base, "A")
    mk.link(glass, "", base, "B")
    mk.link(a, "", base, "Alpha")
    gr, wr = mk.scalar(m, "GlassRough", 0.08, -700, 560), mk.scalar(m, "WallRough", 0.6, -700, 650)
    rough = mk.expr(m, unreal.MaterialExpressionLinearInterpolate, -400, 560)
    mk.link(wr, "", rough, "A")
    mk.link(gr, "", rough, "B")
    mk.link(a, "", rough, "Alpha")
    mk.out(m, rgb, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mk.out(m, base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mk.out(m, rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mk.finish(m)
    return {style: mk.instance(MATS, f"MI_Windows_{style.title()}", m, CS[style]) for style in ("glass", "slab", "shop")}


def import_city():
    task = mk.setp(unreal.AssetImportTask(), filename=os.path.join(dck.RAW, "city.glb"), destination_path=GEOM,
                   automated=True, replace_existing=True, save=True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    return [unreal.load_asset(str(a.package_name)) for a in reg.get_assets_by_path(f"{GEOM}/city/StaticMeshes", recursive=True)
            if str(a.asset_class_path.asset_name) == "StaticMesh"]


def tune_emissive():
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    for a in reg.get_assets_by_path(f"{GEOM}/city/Materials", recursive=True):
        name = str(a.asset_name)
        for prefix, strength in CS["emissive"].items():
            if name.startswith(prefix):
                mi = unreal.load_asset(str(a.package_name))
                mk.MEL.set_material_instance_scalar_parameter_value(mi, "EmissiveStrength", strength)
                mk.MEL.update_material_instance(mi)
                mk.EAL.save_loaded_asset(mi)


def place(meshes, window_mis):
    swap = {"City_Window_Glass": window_mis["glass"], "City_Window_Slab": window_mis["slab"], "City_Shop": window_mis["shop"]}
    for sm in meshes:
        a = dck.get_or_spawn(unreal.StaticMeshActor, sm.get_name(), folder="City")
        comp = a.static_mesh_component
        comp.modify()
        comp.set_static_mesh(sm)
        for i, slot in enumerate(comp.get_material_slot_names()):
            if str(slot) in swap:
                comp.set_material(i, swap[str(slot)])


def rect(label, pos_m, normal, w_m, h_m, color, cd, radius_m, vol, folder):
    n = unreal.Vector(normal[0], -normal[1], 0.0)  # Blender -> Unreal (Y flipped)
    side = unreal.Vector(-n.y, n.x, 0.0)
    rot = unreal.MathLibrary.make_rot_from_xy(n, side)
    a = dck.get_or_spawn(unreal.RectLight, label, dck.to_ue(*pos_m), rot, folder)
    c = a.get_component_by_class(unreal.RectLightComponent)
    c.modify()
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    mk.setp(c, intensity_units=unreal.LightUnits.CANDELAS, source_width=w_m * 100, source_height=h_m * 100,
            attenuation_radius=radius_m * 100, cast_shadows=False, volumetric_scattering_intensity=vol, barn_door_angle=88.0)
    c.set_intensity(cd)
    c.set_light_color(unreal.LinearColor(*color, 1.0))


def point(label, pos_m, color, cd, radius_m, vol, folder):
    a = dck.get_or_spawn(unreal.PointLight, label, dck.to_ue(*pos_m), unreal.Rotator(0, 0, 0), folder)
    c = a.get_component_by_class(unreal.PointLightComponent)
    c.modify()
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    mk.setp(c, intensity_units=unreal.LightUnits.CANDELAS, attenuation_radius=radius_m * 100, cast_shadows=False,
            volumetric_scattering_intensity=vol, source_radius=200.0)
    c.set_intensity(cd)
    c.set_light_color(unreal.LinearColor(*color, 1.0))


def lights(manifest):
    for actor in dck.ACTORS.get_all_level_actors():  # rebuild city lights from the manifest each run
        if actor.get_actor_label().startswith(("L_Screen_", "L_Shop_")):
            actor.destroy_actor()
    sl, nits = CS["screen_light"], CS["emissive"]["City_Screen_"]
    for s in manifest["screens"]:
        c, n = s["center"], s["normal"]
        pos = (c[0] + n[0] * 0.8, c[1] + n[1] * 0.8, c[2])
        rect(f"L_Screen_{s['name']}", pos, n, s["width"], s["height"], s["colour"],
             nits * sl["nits_scale"] * s["width"] * s["height"], sl["radius_m"],
             sl.get("volumetric_per_screen", {}).get(s["name"], sl["volumetric_scattering"]), "Lights/City")
    for actor in dck.ACTORS.get_all_level_actors():
        if actor.get_actor_label().startswith("L_ViaductLamp_"):
            actor.destroy_actor()
    vl = S.VIADUCT_LAMP
    for k, p in enumerate(manifest.get("viaduct_lamps", [])[::vl["every"]]):
        a = dck.get_or_spawn(unreal.SpotLight, f"L_ViaductLamp_{k:02d}", dck.to_ue(*p), unreal.Rotator(roll=0, pitch=-90, yaw=0), "Lights/City")
        c = a.get_component_by_class(unreal.SpotLightComponent)
        c.modify()
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        mk.setp(c, intensity_units=unreal.LightUnits.CANDELAS, attenuation_radius=vl["radius_m"] * 100, outer_cone_angle=vl["cone_deg"] / 2,
                inner_cone_angle=vl["cone_deg"] / 4, cast_shadows=True, volumetric_scattering_intensity=vl["volumetric_scattering"], source_radius=15.0)
        c.set_intensity(vl["intensity_cd"])
        c.set_light_color(unreal.LinearColor(1.0, 0.82, 0.6, 1.0))
    sh = CS["shop_light"]
    for k, s in enumerate(manifest["shops"]):
        if math.hypot(s["pos"][0], s["pos"][1]) <= sh["max_distance_m"]:
            point(f"L_Shop_{s['tower']}", s["pos"], s["colour"], sh["intensity_cd"], sh["radius_m"], sh["volumetric_scattering"], "Lights/City")


dck.ensure_map()
with open(os.path.join(dck.RAW, "city_manifest.json"), encoding="utf-8") as f:
    manifest = json.load(f)
window_mis = build_window_material()
meshes = import_city()
tune_emissive()
place(meshes, window_mis)
lights(manifest)
dck.LEVELS.save_current_level()
print(f"setup_city: {len(meshes)} city meshes, {len(manifest['screens'])} screen lights, "
      f"{sum(1 for s in manifest['shops'] if math.hypot(*s['pos'][:2]) <= CS['shop_light']['max_distance_m'])} shop lights")
