"""The crowd: imports the umbrellas (RawContent/umbrellas.glb), makes root-locked copies of the walk
clips and the idle, builds dark coat materials, and spawns the walkers and standing people from
RawContent/crowd_plan.json (crowd_paths.py). Everyone wears a belted coat (setup_outfits.py);
most carry an umbrella in the right hand, some have a hood; about a fifth walk without one,
arms crossed against the cold, in a hat or a hood.
Writes RawContent/crowd.json for make_sweep.py, which keys the walks. Re-runnable; same seed ->
same people.

    "C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe" Scripts/crowd_paths.py   # plan (offline)
    node Scripts/ue.mjs Scripts/setup_outfits.py     # dressed bodies (after Blender build_outfits.py)
    node Scripts/ue.mjs Scripts/setup_crowd.py

Bodies are the packs' mannequins (Quinn from the Female NPC pack, Manny from the NPC Animation
pack). Both play the Female pack's umbrella clips: Manny's skeleton lists Quinn's as compatible.
"""
import importlib
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402
import matkit as mk  # noqa: E402
import scene_config as S  # noqa: E402

dck, mk, S = importlib.reload(dck), importlib.reload(mk), importlib.reload(S)
import unreal  # noqa: E402

C = S.CROWD
P = S.CROWD_LOOK
DIR = f"{dck.GAME}/Crowd"
EAL = unreal.EditorAssetLibrary


def import_umbrellas():
    task = mk.setp(unreal.AssetImportTask(), filename=os.path.join(dck.RAW, "umbrellas.glb"), destination_path=f"{DIR}/Umbrellas",
                   automated=True, replace_existing=True, save=True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    meshes = {str(x.asset_name): unreal.load_asset(str(x.package_name))
              for x in reg.get_assets_by_path(f"{DIR}/Umbrellas", recursive=True) if str(x.asset_class_path.asset_name) == "StaticMesh"}
    led = f"{DIR}/Umbrellas/umbrellas/Materials/Umbrella_LED"
    if EAL.does_asset_exist(led):
        mi = unreal.load_asset(led)
        mk.MEL.set_material_instance_scalar_parameter_value(mi, "EmissiveStrength", P["led_emissive"])
        mk.MEL.update_material_instance(mi)
        EAL.save_loaded_asset(mi)
    return meshes


def root_locked(src, name):
    """Our own copy of a pack clip with root motion locked (the actor carries the walker)."""
    dst = f"{DIR}/Anims/{name}"
    if not EAL.does_asset_exist(dst):
        mk.ensure_dir(f"{DIR}/Anims")
        EAL.duplicate_asset(src, dst)
    a = unreal.load_asset(dst)
    a.set_editor_property("force_root_lock", True)
    EAL.save_loaded_asset(a)
    return a


def look_materials():
    m = mk.material(f"{DIR}/Materials", "M_Figure")
    out_col = mk.vector(m, "BaseColor", (0.02, 0.02, 0.022), -400, 0)
    rough = mk.scalar(m, "Roughness", 0.6, -400, 150)
    mk.out(m, out_col, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mk.out(m, rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mk.finish(m)
    coats = [mk.instance(f"{DIR}/Materials", f"MI_Coat_{i}", m, {"Roughness": r}, {"BaseColor": c}) for i, (c, r) in enumerate(P["coats"])]
    c, r = P["trousers"]
    trousers = mk.instance(f"{DIR}/Materials", "MI_Trousers", m, {"Roughness": r}, {"BaseColor": c})
    c, r = P["belt"]
    belt = mk.instance(f"{DIR}/Materials", "MI_Belt", m, {"Roughness": r}, {"BaseColor": c})
    return coats, trousers, belt


def grip_rotation():
    d = P["grip"]["shaft_dir"]
    n = math.sqrt(sum(x * x for x in d))
    return unreal.MathLibrary.make_rot_from_z(unreal.Vector(d[0] / n, d[1] / n, d[2] / n))


def attach(child, parent, socket, rel):
    child.attach_to_actor(parent, socket, unreal.AttachmentRule.SNAP_TO_TARGET, unreal.AttachmentRule.SNAP_TO_TARGET,
                          unreal.AttachmentRule.KEEP_WORLD, False)
    child.set_actor_relative_location(rel.translation, False, False)
    child.set_actor_relative_rotation(rel.rotation.rotator(), False, False)
    child.set_actor_relative_scale3d(unreal.Vector(1, 1, 1))


def spawn_person(label, p, mesh, coat, umbrella, hat, loc, yaw):
    a = dck.get_or_spawn(unreal.SkeletalMeshActor, label, loc, unreal.Rotator(0, 0, yaw), "Crowd")
    comp = a.skeletal_mesh_component
    comp.modify()
    comp.set_skinned_asset_and_update(mesh) if hasattr(comp, "set_skinned_asset_and_update") else comp.set_editor_property("skeletal_mesh_asset", mesh)
    for i, slot in enumerate(mesh.materials):  # slots are "NN_<garment material>"; the bare body reads as trousers
        name = str(slot.material_slot_name)
        comp.set_material(i, BELT if "Belt" in name else coat if ("Coat_" in name or "Hood_" in name) else TROUSERS)
    a.set_actor_scale3d(unreal.Vector(p["scale"], p["scale"], p["scale"]))
    if umbrella:
        u = dck.get_or_spawn(unreal.StaticMeshActor, f"{label}_Umbrella", loc, unreal.Rotator(0, 0, 0), "Crowd")
        uc = u.static_mesh_component
        uc.modify()
        uc.set_static_mesh(umbrella)
        uc.set_mobility(unreal.ComponentMobility.MOVABLE)
        rot = unreal.MathLibrary.compose_rotators(unreal.Rotator(roll=0, pitch=0, yaw=p["twist"]), grip_rotation())  # spin the hook, then align
        attach(u, a, P["grip"]["socket"], unreal.Transform(unreal.Vector(*P["grip"]["offset_cm"]), rot, unreal.Vector(1, 1, 1)))
        if umbrella.get_name() == "SM_Umbrella_LED":  # a soft cyan glow from the shaft onto the walker and the rain
            lt = dck.get_or_spawn(unreal.PointLight, f"L_{label}", loc, unreal.Rotator(0, 0, 0), "Crowd")
            c = lt.get_component_by_class(unreal.PointLightComponent)
            c.set_mobility(unreal.ComponentMobility.MOVABLE)
            mk.setp(c, intensity_units=unreal.LightUnits.CANDELAS, attenuation_radius=P["led_light_radius_m"] * 100, cast_shadows=True,
                    volumetric_scattering_intensity=2.0, source_radius=2.0, source_length=60.0)
            c.set_intensity(P["led_light_cd"])
            c.set_light_color(unreal.LinearColor(0.3, 0.85, 1.0, 1.0))
            attach(lt, u, "", unreal.Transform(unreal.Vector(0, 0, 45), unreal.Rotator(0, 90, 0), unreal.Vector(1, 1, 1)))  # tube along the shaft
    if hat:
        h = dck.get_or_spawn(unreal.StaticMeshActor, f"{label}_Hat", loc, unreal.Rotator(0, 0, 0), "Crowd")
        hc = h.static_mesh_component
        hc.modify()
        hc.set_static_mesh(hat)
        hc.set_mobility(unreal.ComponentMobility.MOVABLE)
        attach(h, a, "head", HEAD_INV[p["body"]])  # built in the body's reference pose: undo the head bone's ref transform
    return a


dck.ensure_map()
with open(os.path.join(dck.RAW, "crowd_plan.json"), encoding="utf-8") as f:
    plan = json.load(f)
umbrellas = import_umbrellas()
walk = root_locked(P["walk_anim"], "A_Walk_Umbrella")
walk_arms = root_locked(P["walk_no_umbrella_anim"], "A_Walk_CrossedArms")
stand = root_locked(P["stand_anim"], "A_Stand_Umbrella")
manny_skel = unreal.load_asset(P["manny_skeleton"])
quinn_skel = unreal.load_asset(P["quinn_skeleton"])
compat = list(manny_skel.get_editor_property("compatible_skeletons"))
if not any(str(c).endswith(quinn_skel.get_name()) or (hasattr(c, "get_name") and c.get_name() == quinn_skel.get_name()) for c in compat):
    manny_skel.set_editor_property("compatible_skeletons", compat + [quinn_skel])
    EAL.save_loaded_asset(manny_skel)
coats, TROUSERS, BELT = look_materials()
reg = unreal.AssetRegistryHelpers.get_asset_registry()
garments = {str(x.asset_name): unreal.load_asset(str(x.package_name))
            for x in reg.get_assets_by_path(f"{DIR}/Outfits/Garments", recursive=True) if str(x.asset_class_path.asset_name) == "StaticMesh"}
HEAD_INV = {}
for body in P["bodies"]:
    with open(os.path.join(dck.RAW, "bodies", f"{body}.json"), encoding="utf-8") as f:
        hj = json.load(f)["joints"]["head"]
    q = unreal.Quat(*hj["rot"])
    HEAD_INV[body] = unreal.Transform(unreal.Vector(*hj["pos"]), q.rotator(), unreal.Vector(1, 1, 1)).inverse()
for actor in dck.ACTORS.get_all_level_actors():  # rebuild the crowd each run
    if actor.get_actor_label().startswith(("Walker_", "Standing_", "L_Walker_", "L_Standing_")):
        actor.destroy_actor()

rng = random.Random(P["seed"])
uw = P["umbrella_weights"]
n_people = len(plan["walkers"]) + len(plan["standing"])
no_umbrella = set(rng.sample(range(len(plan["walkers"])), round(P["no_umbrella_share"] * n_people)))  # walkers only
people = []


def pick(has_umbrella):
    p = {"body": "Manny" if rng.random() < P["manny_share"] else "Quinn", "coat": rng.randrange(len(coats)),
         "scale": round(rng.uniform(*P["scale_range"]), 3), "twist": rng.uniform(0, 360)}
    if has_umbrella:
        p["umbrella"] = rng.choices(list(uw), weights=list(uw.values()))[0]
        p["head"] = "Hood" if rng.random() < P["hood_share_with_umbrella"] else None
    else:
        p["umbrella"] = None
        hw = P["headwear_without_umbrella"]
        p["head"] = rng.choices(list(hw), weights=list(hw.values()))[0]
    p["outfit"] = "CoatHood" if p["head"] == "Hood" else "Coat"
    return p


def place(label, p, loc, yaw):
    mesh = unreal.load_asset(f"{DIR}/Outfits/SKM_{p['body']}_{p['outfit']}")
    hat = garments.get(f"{p['head']}_{p['body']}") if p["head"] and p["head"].startswith("Hat_") else None
    spawn_person(label, p, mesh, coats[p["coat"]], umbrellas[p["umbrella"]] if p["umbrella"] else None, hat, loc, yaw)


for i, w in enumerate(plan["walkers"]):
    p = pick(i not in no_umbrella)
    p0, p1 = w["path"][0], w["path"][1]
    heading = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
    label = f"Walker_{i:02d}"
    place(label, p, dck.to_ue(p0[0], p0[1], 0.0), dck.heading_to_ue_yaw(heading) - 90.0)
    clip = walk if p["umbrella"] else walk_arms
    people.append(dict(p, label=label, kind="walker", anim=clip.get_path_name(), rate=w["rate"], speed=w["speed"], start_s=w["start_s"],
                       travel_s=w["travel_s"], spacing_m=plan["spacing_m"], anim_offset_s=round(rng.uniform(0, clip.get_play_length()), 3),
                       path=w["path"]))
for i, st in enumerate(plan["standing"]):
    p = pick(True)
    label = f"Standing_{i:02d}"
    place(label, p, dck.to_ue(st["pos"][0], st["pos"][1], 0.0), dck.heading_to_ue_yaw(st["facing_deg"]) - 90.0)
    people.append(dict(p, label=label, kind="standing", anim=stand.get_path_name(), anim_offset_s=round(rng.uniform(0, stand.get_play_length()), 3)))

with open(os.path.join(dck.RAW, "crowd.json"), "w", encoding="utf-8") as f:
    json.dump({"loop_s": plan["loop_s"], "people": people}, f)
dck.LEVELS.save_current_level()
print(f"setup_crowd: {len(plan['walkers'])} walkers + {len(plan['standing'])} standing, {len(no_umbrella)} without umbrellas")
for p in people:
    print(f"  {p['label']:12s} {p['body']:5s} {p['outfit']:9s} {str(p['umbrella']):18s} {str(p['head']):10s} coat {p['coat']} x{p['scale']:.2f}")
