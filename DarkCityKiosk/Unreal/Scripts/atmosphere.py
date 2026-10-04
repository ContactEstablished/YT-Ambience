"""Height fog and sky light from scene_config (FOG, SKY, SKYLIGHT_INTENSITY).

    node Scripts/ue.mjs Scripts/atmosphere.py

setup_scene.py calls apply() too. The mist waves in LS_Sweep key the fog's main-layer density,
volumetric extinction and volumetric emissive over time (make_sweep.py); everything else is set
here. The sky light uses a small generated night-sky cubemap (RawContent/sky/T_NightSky.hdr,
lat-long): real-time capture needs a SkyAtmosphere, clouds or an IsSky mesh to capture, and with
none it lit the scene black and printed an on-screen warning.
"""
import importlib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402
import matkit as mk  # noqa: E402
import scene_config as S  # noqa: E402

dck, mk, S = importlib.reload(dck), importlib.reload(mk), importlib.reload(S)
import unreal  # noqa: E402

SKY_DIR = f"{dck.GAME}/Sky"


def write_sky_hdr(path):
    """Radiance RGBE (RLE scanlines) lat-long: dark navy zenith, a blue-gray glow at the horizon, black below."""
    sk = S.SKY
    w, h = sk["hdr_size"]
    rows = []
    for y in range(h):
        elev = 90.0 - 180.0 * (y + 0.5) / h
        if elev < 0:
            rgb = (0.0, 0.0, 0.0)
        else:
            k = math.exp(-elev / sk["glow_falloff_deg"])
            rgb = tuple(z + (hz - z) * k for z, hz in zip(sk["zenith"], sk["horizon"]))
        v = max(rgb)
        if v < 1e-32:
            px = (0, 0, 0, 0)
        else:
            m, e = math.frexp(v)
            sc = m * 256.0 / v
            px = (int(rgb[0] * sc), int(rgb[1] * sc), int(rgb[2] * sc), e + 128)
        line = bytearray([2, 2, w >> 8, w & 255])
        for ch in range(4):  # each channel as literal runs of up to 128 bytes
            left = w
            while left:
                n = min(128, left)
                line.append(n)
                line.extend([px[ch]] * n)
                left -= n
        rows.append(bytes(line))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"#?RADIANCE\nFORMAT=32-bit_rle_rgbe\n\n" + f"-Y {h} +X {w}\n".encode())
        for r in rows:
            f.write(r)


def import_sky_cubemap():
    src = os.path.join(dck.RAW, "sky", "T_NightSky.hdr")
    write_sky_hdr(src)
    task = mk.setp(unreal.AssetImportTask(), filename=src, destination_path=SKY_DIR, automated=True, replace_existing=True, save=True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    tex = unreal.load_asset(f"{SKY_DIR}/T_NightSky")
    print(f"  sky texture: {tex.get_class().get_name() if tex else None}")
    return tex


def apply_fog():
    fog = dck.get_or_spawn(unreal.ExponentialHeightFog, "HeightFog", unreal.Vector(0, 0, 0), folder="Atmosphere")
    fc = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    fc.modify()
    f = S.FOG
    mk.setp(fc, fog_density=f["density"], fog_height_falloff=f["height_falloff"],
            fog_inscattering_luminance=unreal.LinearColor(*f["inscatter"], 1.0),
            volumetric_fog_scattering_distribution=f["volumetric_distribution"],
            volumetric_fog_albedo=unreal.Color(*[int(255 * v) for v in reversed(f["volumetric_albedo"])], 255),
            volumetric_fog_extinction_scale=f["volumetric_extinction"],
            volumetric_fog_distance=f["volumetric_view_distance_m"] * 100.0)
    sf = fc.get_editor_property("second_fog_data")
    mk.setp(sf, fog_density=f["second"]["density"], fog_height_falloff=f["second"]["height_falloff"],
            fog_height_offset=f["second"]["height_offset"] * 100.0)
    fc.set_editor_property("second_fog_data", sf)
    fc.set_volumetric_fog(True)
    fc.set_volumetric_fog_emissive(unreal.LinearColor(*f["volumetric_emissive"], 1.0))
    fc.set_fog_inscattering_color(unreal.LinearColor(*f["inscatter"], 1.0))
    return fc


def apply_sky():
    sky = dck.get_or_spawn(unreal.SkyLight, "SkyLight", unreal.Vector(0, 0, 500), folder="Atmosphere")
    sc = sky.get_component_by_class(unreal.SkyLightComponent)
    sc.modify()
    sc.set_mobility(unreal.ComponentMobility.MOVABLE)
    tex = import_sky_cubemap()
    mk.setp(sc, real_time_capture=False, source_type=unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP, cubemap=tex,
            lower_hemisphere_is_black=True, intensity=S.SKYLIGHT_INTENSITY)
    sc.recapture_sky()
    return sc


def apply_light_glow():
    """How strongly the city's screen lights glow in the fog (scene_config.CITY screen_light), on the
    existing lights (setup_city.py builds them with the same values)."""
    sl = S.CITY["screen_light"]
    n = 0
    for a in dck.ACTORS.get_all_level_actors():
        lab = a.get_actor_label()
        if lab.startswith("L_Screen_"):
            c = a.get_component_by_class(unreal.LightComponent)
            a.modify()
            c.modify()
            c.set_editor_property("volumetric_scattering_intensity", sl.get("volumetric_per_screen", {}).get(lab[len("L_Screen_"):], sl["volumetric_scattering"]))
            n += 1
    return n


def apply():
    apply_fog()
    apply_sky()
    apply_light_glow()


if __name__ == "__main__":
    dck.ensure_map()
    apply()
    dck.LEVELS.save_current_level()
    print("atmosphere: fog + sky light applied")
