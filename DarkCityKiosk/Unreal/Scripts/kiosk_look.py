"""Re-applies the kiosk's light levels and glow strengths from scene_config to the existing scene
(no rebuild): kiosk light intensities (SOFFIT, CANOPY_SPILL, INTERIOR, LANTERN_LIGHT,
WINDOW_LIGHTBOX_LIGHT, CORNER_SIGN_LIGHT x LIGHT_SCALE), their fog glow (KIOSK_LIGHT_VOLUMETRIC) and
the emissive strengths of the kiosk's glowing materials (EMISSIVE). setup_scene.py builds the same
values from scratch.

    node Scripts/ue.mjs Scripts/kiosk_look.py
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402
import scene_config as S  # noqa: E402

dck, S = importlib.reload(dck), importlib.reload(S)
import unreal  # noqa: E402

MEL = unreal.MaterialEditingLibrary
LIGHTS = {  # label prefix -> intensity (cd)
    "L_Soffit_": S.SOFFIT["intensity_cd"],
    "L_CanopySpill_": S.CANOPY_SPILL["intensity_cd"],
    "L_Interior": S.INTERIOR["intensity_cd"],
    "L_Lantern_R": S.SIGN_24H_LIGHT["intensity_cd"],  # lights the 24h lightbox since the signage pass (10/5)
    "L_Lantern_": S.LANTERN_LIGHT["intensity_cd"],
    "L_WindowLightbox": S.WINDOW_LIGHTBOX_LIGHT["intensity_cd"],
    "L_CornerSign": S.CORNER_SIGN_LIGHT["intensity_cd"],
}

dck.ensure_map()
n = 0
for a in dck.ACTORS.get_all_level_actors():
    if str(a.get_folder_path()) != "Lights/Kiosk":
        continue
    lab = a.get_actor_label()
    cd = next((v for k, v in LIGHTS.items() if lab.startswith(k)), None)
    if cd is None:
        continue
    c = a.get_component_by_class(unreal.LightComponent)
    a.modify()
    c.modify()
    c.set_intensity(cd * S.LIGHT_SCALE)
    c.set_editor_property("volumetric_scattering_intensity", S.KIOSK_LIGHT_VOLUMETRIC)
    n += 1
folder = f"{dck.KIOSK_MESHES}/{dck.KIOSK_GLB}/Materials"
m = 0
for name, strength in S.EMISSIVE.items():
    path = f"{folder}/{name}"
    if dck.EAL.does_asset_exist(path):
        mi = unreal.load_asset(path)
        MEL.set_material_instance_scalar_parameter_value(mi, "EmissiveStrength", strength)
        MEL.update_material_instance(mi)
        dck.EAL.save_loaded_asset(mi)
        m += 1
    weathered = f"{dck.GAME}/Kiosk/Weather/Instances/MI_KW_{name}"  # surfacing pass: the instance on the actors
    if dck.EAL.does_asset_exist(weathered):
        mi = unreal.load_asset(weathered)
        MEL.set_material_instance_scalar_parameter_value(mi, "EmissiveStrength", strength)
        MEL.update_material_instance(mi)
        dck.EAL.save_loaded_asset(mi)
if dck.EAL.does_asset_exist(f"{dck.GAME}/Kiosk/Kitchen/M_Kitchen"):  # kitchen pass (10/9): its lights and L_Interior's new range
    import kiosk_kitchen  # noqa: E402
    importlib.reload(kiosk_kitchen).lights(kiosk_kitchen.data())
dck.LEVELS.save_current_level()
print(f"kiosk_look: {n} kiosk lights (x{S.LIGHT_SCALE}, fog glow {S.KIOSK_LIGHT_VOLUMETRIC}), {m} glowing materials")
