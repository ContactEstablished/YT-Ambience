"""Imports the commuter train (RawContent/train.glb), places it on the railway, sets its
emissive strengths, and attaches its headlight. The lit windows and strips are emissive; the
old unshadowed interior lights shone through the deck onto its underside (removed 10/3), and
the headlight casts shadows for the same reason.
The run itself is keyed into LS_Sweep by make_sweep.py (scene_config.TRAIN["keys"]).

    node Scripts/ue.mjs Scripts/setup_train.py
"""
import importlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402
import matkit as mk  # noqa: E402
import scene_config as S  # noqa: E402

dck, mk, S = importlib.reload(dck), importlib.reload(mk), importlib.reload(S)
import unreal  # noqa: E402

TRAIN_DIR = f"{dck.GAME}/Train"
EMISSIVE = {"Train_Window_Lit": 6.0, "Train_Window_Dim": 2.5, "Train_Strip": 6.0, "Train_Head": 20.0, "Train_Tail": 10.0, "Train_Sign": 8.0}

dck.ensure_map()
with open(os.path.join(dck.RAW, "city_manifest.json"), encoding="utf-8") as f:
    rail = json.load(f)["railway"]

task = mk.setp(unreal.AssetImportTask(), filename=os.path.join(dck.RAW, "train.glb"), destination_path=TRAIN_DIR,
               automated=True, replace_existing=True, save=True)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
# a single-mesh glTF imports as a mesh named after the file, so take whatever mesh is there
reg = unreal.AssetRegistryHelpers.get_asset_registry()
sm = next(unreal.load_asset(str(x.package_name)) for x in reg.get_assets_by_path(f"{TRAIN_DIR}/train/StaticMeshes", recursive=True)
          if str(x.asset_class_path.asset_name) == "StaticMesh")
for name, strength in EMISSIVE.items():
    path = f"{TRAIN_DIR}/train/Materials/{name}"
    if mk.EAL.does_asset_exist(path):
        mi = unreal.load_asset(path)
        mk.MEL.set_material_instance_scalar_parameter_value(mi, "EmissiveStrength", strength)
        mk.MEL.update_material_instance(mi)
        mk.EAL.save_loaded_asset(mi)

x_park = S.TRAIN["keys"][0][1]
train = dck.get_or_spawn(unreal.StaticMeshActor, "Train", dck.to_ue(x_park, rail["y"], rail["rail_top"]), unreal.Rotator(0, 0, 0), "Railway")
comp = train.static_mesh_component
comp.modify()
comp.set_static_mesh(sm)
comp.set_mobility(unreal.ComponentMobility.MOVABLE)

for actor in dck.ACTORS.get_all_level_actors():
    if actor.get_actor_label().startswith("L_Train_"):
        actor.destroy_actor()
T = S.TRAIN
base = dck.to_ue(x_park, rail["y"], rail["rail_top"])


def attach(light):
    light.attach_to_actor(train, "", unreal.AttachmentRule.KEEP_WORLD, unreal.AttachmentRule.KEEP_WORLD,
                          unreal.AttachmentRule.KEEP_WORLD, False)


head = dck.get_or_spawn(unreal.SpotLight, "L_Train_Head", unreal.Vector(base.x + 20, base.y, base.z + 135), unreal.Rotator(roll=0, pitch=-4, yaw=0), "Railway")
c = head.get_component_by_class(unreal.SpotLightComponent)
c.set_mobility(unreal.ComponentMobility.MOVABLE)
mk.setp(c, intensity_units=unreal.LightUnits.CANDELAS, attenuation_radius=T["head_radius_m"] * 100, outer_cone_angle=16.0,
        inner_cone_angle=8.0, cast_shadows=True, volumetric_scattering_intensity=3.0)
c.set_intensity(T["head_cd"])
c.set_light_color(unreal.LinearColor(0.9, 0.95, 1.0, 1.0))
attach(head)
dck.LEVELS.save_current_level()
print(f"setup_train: train parked at x={x_park} m on y={rail['y']} m, rail top {rail['rail_top']} m; headlight")
