"""Flying traffic: imports the six vehicle types (RawContent/flying_vehicles.glb from Blender
build_flying_vehicles.py), plans the traffic (traffic_plan.py: corridors cached in
RawContent/traffic_routes.json, schedule for scene_config.VARIANT), spawns one actor per pooled
vehicle with its lights (and a cargo lifter's hanging container), plus the hero's shaft of light,
and writes RawContent/traffic.json for make_sweep.py to key. Re-runnable; same seeds -> same traffic.

    node Scripts/ue.mjs Scripts/setup_traffic.py            # schedule from the cached corridors
    node Scripts/ue.mjs Scripts/setup_traffic.py --replan   # search the corridors again (several minutes)
Then run make_sweep.py.
"""
import importlib
import json
import math
import os
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402
import matkit as mk  # noqa: E402
import scene_config as S  # noqa: E402
import traffic_lanes as TL  # noqa: E402
import traffic_plan as TP  # noqa: E402
import wetfx_hlsl as W  # noqa: E402

dck, mk, S, TL, TP, W = (importlib.reload(m) for m in (dck, mk, S, TL, TP, W))
import unreal  # noqa: E402

TR = S.TRAFFIC
DIR = f"{dck.GAME}/Traffic"
MATS = f"{DIR}/Materials"
CARGO_ANCHOR_CM = -125.0  # build_flying_vehicles.CARGO_ANCHOR_Z: where the container's cables hang from
LIGHT_Z_CM = {"Courier": -60, "Taxi": -110, "Pod": -150, "Transit": -230, "Cargo": -180, "Hero": -120}
HEAD_X_CM = {"Taxi": 270, "Transit": 820}

MIST_HLSL = r"""
float r = length(UV - 0.5) * 2.0;
float g = saturate(1.0 - r);
return Col * Intensity * g * g * (3.0 - 2.0 * g);
"""
NAV_HLSL = r"""
float t = frac(Time / Period + Phase);
float on = smoothstep(0.0, 0.03, t) * (1.0 - smoothstep(Duty, Duty + 0.05, t));
return Col * Intensity * (0.04 + 0.96 * on);
"""


def build_materials():
    lm = TR["lift_mist"]
    m = mk.material(MATS, "M_Vehicle_LiftMist")
    mk.setp(m, blend_mode=unreal.BlendMode.BLEND_ADDITIVE, shading_model=unreal.MaterialShadingModel.MSM_UNLIT, two_sided=True)
    ins = {"UV": mk.expr(m, unreal.MaterialExpressionTextureCoordinate, -900, 0), "Col": mk.vector(m, "Color", lm["color"], -900, 100),
           "Intensity": mk.scalar(m, "Intensity", lm["intensity"], -900, 250)}
    c = mk.custom(m, MIST_HLSL, list(ins), unreal.CustomMaterialOutputType.CMOT_FLOAT3, -500, 0, "Soft lift glow")
    for k, e in ins.items():
        mk.link(e, "RGB" if k == "Col" else "", c, k)
    mk.out(m, c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mk.finish(m)
    mist = mk.instance(MATS, "MI_Vehicle_LiftMist", m)
    mist_hero = mk.instance(MATS, "MI_Vehicle_LiftMist_Hero", m, {"Intensity": TR["hero"]["lift_mist"]})

    nb = TR["nav_blink"]
    m = mk.material(MATS, "M_Vehicle_NavBlink")
    phase = mk.expr(m, unreal.MaterialExpressionScalarParameter, -900, 300, parameter_name="Phase", default_value=0.0,
                    use_custom_primitive_data=True, primitive_data_index=0)
    ins = {"Time": W.loop_time(m, -900, 0), "Phase": phase,  # the sequence's loop clock (prompt 10)
           "Col": mk.vector(m, "Color", nb["color"], -900, 100),
           "Intensity": mk.scalar(m, "Intensity", nb["intensity"], -900, 400), "Period": mk.scalar(m, "Period", nb["period_s"], -900, 500),
           "Duty": mk.scalar(m, "Duty", nb["duty"], -900, 600)}
    c = mk.custom(m, NAV_HLSL, list(ins), unreal.CustomMaterialOutputType.CMOT_FLOAT3, -500, 0, "Nav blink")
    for k, e in ins.items():
        mk.link(e, "RGB" if k == "Col" else "", c, k)
    mk.out(m, c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mk.out(m, mk.expr(m, unreal.MaterialExpressionConstant3Vector, -500, 200, constant=unreal.LinearColor(0.05, 0.0, 0.0, 1.0)), "",
           unreal.MaterialProperty.MP_BASE_COLOR)
    mk.finish(m)
    nav = mk.instance(MATS, "MI_Vehicle_NavBlink", m)
    return {"Veh_LiftMist": mist, "Veh_Nav_Red": nav, "hero": {"Veh_LiftMist": mist_hero, "Veh_Nav_Red": nav}}


def import_vehicles():
    task = mk.setp(unreal.AssetImportTask(), filename=os.path.join(dck.RAW, "flying_vehicles.glb"), destination_path=DIR,
                   automated=True, replace_existing=True, save=True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    meshes = {str(x.asset_name): unreal.load_asset(str(x.package_name)) for x in reg.get_assets_by_path(f"{DIR}/flying_vehicles/StaticMeshes", recursive=True)
              if str(x.asset_class_path.asset_name) == "StaticMesh"}
    for x in reg.get_assets_by_path(f"{DIR}/flying_vehicles/Materials", recursive=True):
        n = str(x.asset_name)
        if n in TR["emissive"]:
            mi = unreal.load_asset(str(x.package_name))
            mk.MEL.set_material_instance_scalar_parameter_value(mi, "EmissiveStrength", TR["emissive"][n])
            mk.MEL.update_material_instance(mi)
            mk.EAL.save_loaded_asset(mi)
    return meshes


def clear_old():
    n = 0
    for actor in dck.ACTORS.get_all_level_actors():
        if actor.get_actor_label().startswith(("Car_", "L_Car_", "Veh_", "L_Veh_", "L_HeroShaft")):
            actor.destroy_actor()
            n += 1
    return n


def attach(child, parent, rel):
    child.attach_to_actor(parent, "", unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.SNAP_TO_TARGET,
                          unreal.AttachmentRule.KEEP_WORLD, False)
    child.set_actor_relative_location(rel, False, False)
    child.set_actor_relative_rotation(unreal.Rotator(0, 0, 0), False, False)


def point_light(label, folder, color, cd, radius_m, vol):
    lt = dck.get_or_spawn(unreal.PointLight, label, unreal.Vector(0, 0, -40000), unreal.Rotator(0, 0, 0), folder)
    c = lt.get_component_by_class(unreal.PointLightComponent)
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    # shadowed, like every moving light: otherwise it shines through the viaduct and towers
    mk.setp(c, intensity_units=unreal.LightUnits.CANDELAS, attenuation_radius=radius_m * 100, cast_shadows=True,
            volumetric_scattering_intensity=vol, source_radius=60.0)
    c.set_intensity(0.0)
    c.set_light_color(unreal.LinearColor(*color, 1.0))
    return lt


def spawn(plan, meshes, mats):
    for a in plan["actors"]:
        typ = a["type"]
        folder = f"Traffic/{typ}"
        car = dck.get_or_spawn(unreal.StaticMeshActor, a["label"], unreal.Vector(0, 0, -40000), unreal.Rotator(0, 0, 0), folder)
        comp = car.static_mesh_component
        comp.modify()
        comp.set_static_mesh(meshes[a["mesh"]])
        comp.set_mobility(unreal.ComponentMobility.MOVABLE)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        swap = mats["hero"] if typ == "Hero" else mats
        for i, slot in enumerate(comp.get_material_slot_names()):
            if str(slot) in swap and str(slot) != "hero":
                comp.set_material(i, swap[str(slot)])
        comp.set_custom_primitive_data_float(0, (zlib.crc32(a["label"].encode()) % 1000) / 1000.0)  # nav-light blink phase
        a["lights"] = []
        cfg = TR["hero"] if typ == "Hero" else TR["types"][typ]
        lc = cfg.get("light")
        if lc:
            lt = point_light(f"L_{a['label']}", folder, lc["color"], lc["cd"], lc["radius_m"], TR["hero"]["light_volumetric"] if typ == "Hero" else 2.5)
            attach(lt, car, unreal.Vector(0, 0, LIGHT_Z_CM.get(typ, -100)))
            a["lights"].append({"label": lt.get_actor_label(), "class": "PointLightComponent", "cd": lc["cd"]})
            if lc.get("head_cd"):  # a soft forward beam that catches the haze
                sp = dck.get_or_spawn(unreal.SpotLight, f"L_{a['label']}_Head", unreal.Vector(0, 0, -40000), unreal.Rotator(0, 0, 0), folder)
                sc = sp.get_component_by_class(unreal.SpotLightComponent)
                sc.set_mobility(unreal.ComponentMobility.MOVABLE)
                mk.setp(sc, intensity_units=unreal.LightUnits.CANDELAS, attenuation_radius=8000.0, outer_cone_angle=10.0, inner_cone_angle=4.0,
                        cast_shadows=True, volumetric_scattering_intensity=3.0)
                sc.set_intensity(0.0)
                sc.set_light_color(unreal.LinearColor(0.85, 0.92, 1.0, 1.0))
                attach(sp, car, unreal.Vector(HEAD_X_CM.get(typ, 250), 0, -30))
                a["lights"].append({"label": sp.get_actor_label(), "class": "SpotLightComponent", "cd": lc["head_cd"]})
        if typ == "Cargo":
            ct = dck.get_or_spawn(unreal.StaticMeshActor, f"{a['label']}_Container", unreal.Vector(0, 0, -40000), unreal.Rotator(0, 0, 0), folder)
            cc = ct.static_mesh_component
            cc.modify()
            cc.set_static_mesh(meshes["SM_Veh_CargoContainer"])
            cc.set_mobility(unreal.ComponentMobility.MOVABLE)
            cc.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            attach(ct, car, unreal.Vector(0, 0, CARGO_ANCHOR_CM))
            a["container"] = ct.get_actor_label()
            a["container_offset_cm"] = [0.0, 0.0, CARGO_ANCHOR_CM]
    sh = plan.get("hero_shaft")
    if sh:  # a shaft of light the hero crosses (always there, so every variant matches)
        hs = TR["hero"]["shaft"]
        pos, tgt = dck.to_ue(*sh["pos"]), dck.to_ue(*sh["target"])
        rot = unreal.MathLibrary.find_look_at_rotation(pos, tgt)
        sp = dck.get_or_spawn(unreal.SpotLight, "L_HeroShaft", pos, rot, "Traffic")
        sc = sp.get_component_by_class(unreal.SpotLightComponent)
        sc.set_mobility(unreal.ComponentMobility.MOVABLE)
        mk.setp(sc, intensity_units=unreal.LightUnits.CANDELAS, attenuation_radius=12000.0, outer_cone_angle=hs["cone_deg"] / 2,
                inner_cone_angle=hs["cone_deg"] / 4, cast_shadows=True, volumetric_scattering_intensity=hs["volumetric_scattering"])
        sc.set_intensity(hs["cd"])
        sc.set_light_color(unreal.LinearColor(*hs["color"], 1.0))


dck.ensure_map()
if "--materials" in sys.argv:  # rebuild the vehicle materials in place only
    build_materials()
    print("setup_traffic: materials rebuilt")
else:
    replan = "--replan" in sys.argv
    plan = TP.main(replan=replan)
    meshes = import_vehicles()
    mats = build_materials()
    print(f"removed {clear_old()} old traffic actors")
    spawn(plan, meshes, mats)
    with open(TP.OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(plan, f)
    dck.LEVELS.save_current_level()
    lights = sum(len(a["lights"]) for a in plan["actors"])
    print(f"setup_traffic: {len(plan['actors'])} vehicles ({lights} lights), meshes {sorted(meshes)}; now run make_sweep.py")
