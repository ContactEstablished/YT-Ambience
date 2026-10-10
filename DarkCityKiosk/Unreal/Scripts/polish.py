"""Final polish (prompt 10, 2026-10-10): the roof's reflected light (scene_config.ROOF_LIGHT).

From the 10 cm floor camera the roof machinery read as one dark silhouette. Two soft spot lights stand in for light
that is really around the roof: the city glow and wet street behind the camera (cool, front-left, high) and the SAME
CITY screen to the right (its blue, a rim). They shine on lighting channel 1 only, and only the roof machinery's actor
joins channel 1, so nothing else in the frame changes; no fog scattering; shadowed, so the gaps between units stay dark.
The other prompt-10 changes live where their systems do (steam: wet_fx.py; counter: make_kitchen_textures.py +
kiosk_kitchen.py; bin: EXTERIOR_LOOK; KAZE poster: Graphics/art/paper.js + GRAPHICS_CARDS; the loop: make_sweep.py,
wetfx_hlsl.loop_time, encode_loop.mjs).

    node Scripts/ue.mjs Scripts/polish.py          # place / update the roof lights
    node Scripts/ue.mjs Scripts/polish.py --off    # hide them (before / after checks)
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402
import scene_config as S  # noqa: E402

dck, S = importlib.reload(dck), importlib.reload(S)
import unreal  # noqa: E402

FOLDER = "Lights/Kiosk/Roof"


def channels(c0, c1):
    lc = unreal.LightingChannels()
    lc.set_editor_property("channel0", c0)
    lc.set_editor_property("channel1", c1)
    lc.set_editor_property("channel2", False)
    return lc


def setp(obj, **props):
    for k, v in props.items():
        try:
            obj.set_editor_property(k, v)
        except Exception as e:  # noqa: BLE001
            print(f"  (skip {k}: {str(e).splitlines()[0][:90]})")


def roof_lights(on=True):
    cfg = S.ROOF_LIGHT
    for label in cfg["actors"]:  # the roof machinery also receives channel 1
        a = dck.find_actor(label)
        if not a:
            print(f"  !! no {label}")
            continue
        for comp in a.get_components_by_class(unreal.PrimitiveComponent):
            comp.modify()
            comp.set_editor_property("lighting_channels", channels(True, True))
    for label, L in cfg["lights"].items():
        pos, tgt = dck.to_ue(*L["pos"]), dck.to_ue(*L["target"])
        rot = unreal.MathLibrary.find_look_at_rotation(pos, tgt)
        a = dck.get_or_spawn(unreal.SpotLight, label, pos, rot, folder=FOLDER)
        c = a.get_component_by_class(unreal.SpotLightComponent)
        c.modify()
        setp(c, intensity_units=unreal.LightUnits.CANDELAS)
        c.set_intensity(L["cd"])
        c.set_light_color(unreal.LinearColor(*L["color"], 1.0))
        setp(c, outer_cone_angle=L["outer_deg"], inner_cone_angle=L["inner_deg"], source_radius=L["source_radius_m"] * 100.0,
             soft_source_radius=L["source_radius_m"] * 50.0, attenuation_radius=L["radius_m"] * 100.0, specular_scale=L["specular"],
             volumetric_scattering_intensity=0.0, cast_shadows=True, lighting_channels=channels(False, True), allow_mega_lights=False,
             use_inverse_squared_falloff=True)
        a.set_actor_hidden_in_game(not on)
        a.set_is_temporarily_hidden_in_editor(not on)
        c.set_visibility(on)
    print(f"roof lights {'on' if on else 'off'}: {', '.join(cfg['lights'])}; channel 1 on {', '.join(cfg['actors'])}")


if __name__ == "__main__":
    dck.ensure_map()
    roof_lights(on="--off" not in sys.argv)
    dck.LEVELS.save_current_level()
