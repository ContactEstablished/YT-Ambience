"""LED ad screens and neon signs for the city (run after setup_city.py).

Imports RawContent/screens/T_Screen_*.png (made by make_screens.ps1), builds M_LEDScreen
(LED dot grid that fades with distance, slow refresh band, rare flicker, pixel-dissolve slide
changes) and M_NeonSign (occasional stutter), one instance per screen, assigns them to the
screen slots on the city meshes, and tints each screen's glow light with its average colour.

All motion repeats on whole fractions of the loop: slides every slide_seconds (7.5 s -> a
15 s two-slide cycle; 30 s and 300 s loops hold whole cycles), refresh band 0.7 Hz (21 per 30 s).

    node Scripts/ue.mjs Scripts/setup_screens.py
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

SCREENS = f"{dck.GAME}/City/Screens"
SRC = os.path.join(dck.RAW, "screens")
LED_PER_M = 8.0  # LED pixels per metre (12.5 cm pitch: chunky enough to read as an LED wall)

LED_UV_HLSL = "return (floor(UV * Res) + 0.5) / Res;"

LED_HLSL = r"""
float t = Time + Offset;
float period = 2.0 * Slot;
float ph = fmod(t, period);
float2 g = UV * Res;
float2 cell = floor(g);
float h = frac(sin(dot(cell, float2(12.9898, 78.233))) * 43758.5453);
// pixel-dissolve: the last Trans seconds of each slot hand over cell by cell
float a2b = saturate((ph - (Slot - Trans)) / Trans);
float b2a = saturate((ph - (period - Trans)) / Trans);
float showB = (ph < Slot) ? step(h, a2b) : 1.0 - step(h, b2a);
float3 c = lerp(A, B, showB);
// round LED dots with dark gaps, fading to flat when a dot is smaller than ~2 screen pixels
float2 f = frac(g) - 0.5;
float dotm = saturate(1.0 - (dot(f, f) * 4.0 - 0.45) * 3.0);
float fw = max(fwidth(g.x), fwidth(g.y));
dotm = lerp(dotm, 0.62, saturate(fw * 1.5 - 0.5));
// slow refresh band rolling down + rare one-frame dips
float band = 1.0 + Scan * (0.5 + 0.5 * sin((UV.y * 3.0 - t * 0.7) * 6.2831853));
float fl = 1.0 - 0.08 * step(0.985, frac(sin(floor(t * 24.0) * 91.7 + Offset * 13.1) * 4375.5));
return c * lerp(0.18, 1.0, dotm) * band * fl * Intensity;
"""

NEON_HLSL = r"""
float t = Time + Offset;
float k = floor(t * 12.0);
float r = frac(sin(k * 12.9898 + Offset * 78.233) * 43758.5453);
float stutter = (r > 0.988) ? 0.2 : ((r > 0.975) ? 0.65 : 1.0);
return stutter;
"""


def build_led_material():
    m = mk.material(SCREENS, "M_LEDScreen")
    tc = mk.expr(m, unreal.MaterialExpressionTextureCoordinate, -1800, 0)
    rx, ry = mk.scalar(m, "LedResX", 128, -1800, 120), mk.scalar(m, "LedResY", 240, -1800, 210)
    res = mk.expr(m, unreal.MaterialExpressionAppendVector, -1600, 150)
    mk.link(rx, "", res, "A")
    mk.link(ry, "", res, "B")
    quv = mk.custom(m, LED_UV_HLSL, ["UV", "Res"], unreal.CustomMaterialOutputType.CMOT_FLOAT2, -1400, 0, "LED cell centre")
    mk.link(tc, "", quv, "UV")
    mk.link(res, "", quv, "Res")
    sa = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, -1150, -100, parameter_name="SlideA")
    sb = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, -1150, 200, parameter_name="SlideB")
    for s in (sa, sb):
        mk.link(quv, "", s, "UVs")
    time = mk.expr(m, unreal.MaterialExpressionTime, -1150, 450)
    names = ["UV", "Res", "A", "B", "Time", "Slot", "Trans", "Offset", "Intensity", "Scan"]
    led = mk.custom(m, LED_HLSL, names, unreal.CustomMaterialOutputType.CMOT_FLOAT3, -800, 0, "LED screen")
    mk.link(tc, "", led, "UV")
    mk.link(res, "", led, "Res")
    mk.link(sa, "RGB", led, "A")
    mk.link(sb, "RGB", led, "B")
    mk.link(time, "", led, "Time")
    for i, (n, v) in enumerate((("Slot", 7.5), ("Trans", 0.8), ("Offset", 0.0), ("Intensity", 6.0), ("Scan", 0.08))):
        mk.link(mk.scalar(m, n if n not in ("Slot", "Trans") else {"Slot": "SlotSeconds", "Trans": "TransSeconds"}[n], v, -1150, 600 + i * 90), "", led, n)
    base = mk.expr(m, unreal.MaterialExpressionConstant3Vector, -500, 250, constant=unreal.LinearColor(0.01, 0.01, 0.012, 1))
    rough = mk.expr(m, unreal.MaterialExpressionConstant, -500, 350, r=0.25)
    mk.out(m, led, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mk.out(m, base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mk.out(m, rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mk.finish(m)
    return m


def build_neon_material():
    m = mk.material(SCREENS, "M_NeonSign")
    tex = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, -900, 0, parameter_name="Sign")
    time = mk.expr(m, unreal.MaterialExpressionTime, -900, 300)
    off = mk.scalar(m, "Offset", 0.0, -900, 400)
    st = mk.custom(m, NEON_HLSL, ["Time", "Offset"], unreal.CustomMaterialOutputType.CMOT_FLOAT1, -650, 300, "Neon stutter")
    mk.link(time, "", st, "Time")
    mk.link(off, "", st, "Offset")
    inten = mk.scalar(m, "Intensity", 6.0, -650, 450)
    mul = mk.expr(m, unreal.MaterialExpressionMultiply, -400, 100)
    mk.link(tex, "RGB", mul, "A")
    mk.link(st, "", mul, "B")
    mul2 = mk.expr(m, unreal.MaterialExpressionMultiply, -250, 100)
    mk.link(mul, "", mul2, "A")
    mk.link(inten, "", mul2, "B")
    dim = mk.expr(m, unreal.MaterialExpressionMultiply, -400, 300)
    mk.link(tex, "RGB", dim, "A")
    mk.link(mk.expr(m, unreal.MaterialExpressionConstant, -550, 400, r=0.05), "", dim, "B")
    mk.out(m, mul2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mk.out(m, dim, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mk.out(m, mk.expr(m, unreal.MaterialExpressionConstant, -250, 400, r=0.35), "", unreal.MaterialProperty.MP_ROUGHNESS)
    mk.finish(m)
    return m


def import_textures():
    tasks = []
    for f in sorted(os.listdir(SRC)):
        if f.startswith("T_Screen_") and f.endswith(".png"):
            tasks.append(mk.setp(unreal.AssetImportTask(), filename=os.path.join(SRC, f), destination_path=f"{SCREENS}/Textures",
                                 automated=True, replace_existing=True, save=True))
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    texs = {}
    for t in tasks:
        name = os.path.splitext(os.path.basename(t.get_editor_property("filename")))[0]
        tex = unreal.load_asset(f"{SCREENS}/Textures/{name}")
        if tex:
            mk.setp(tex, srgb=True, never_stream=True)
            mk.EAL.save_loaded_asset(tex)
            texs[name] = tex
    return texs


def set_tex(mi, param, tex):
    mk.MEL.set_material_instance_texture_parameter_value(mi, param, tex)


dck.ensure_map()
# Rebuild the screen images first (picks up any new art in DarkCityKiosk/_ads/)
import subprocess  # noqa: E402
r = subprocess.run(["pwsh", "-NoProfile", "-File", os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_screens.ps1")],
                   capture_output=True, text=True, encoding="utf-8")
print(r.stdout.strip() or r.stderr.strip())
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "screens.json"), encoding="utf-8") as f:
    cfg = json.load(f)
with open(os.path.join(dck.RAW, "city_manifest.json"), encoding="utf-8") as f:
    manifest = {s["name"]: s for s in json.load(f)["screens"]}
with open(os.path.join(SRC, "screen_colors.json"), encoding="utf-8-sig") as f:
    colours = json.load(f)

led_m, neon_m = build_led_material(), build_neon_material()
texs = import_textures()
mis = {}
for name, sc in cfg["screens"].items():
    ms = manifest.get(name)
    if not ms:
        print(f"  (no screen {name} in the city manifest)")
        continue
    a = texs.get(f"T_Screen_{name}_0")
    if sc["type"] == "ad":
        b = texs.get(f"T_Screen_{name}_1", a)
        mi = mk.instance(f"{SCREENS}/Instances", f"MI_Screen_{name}", led_m, {
            "LedResX": round(ms["width"] * LED_PER_M), "LedResY": round(ms["height"] * LED_PER_M),
            "SlotSeconds": cfg["slide_seconds"] if b is not a else 1.0e6, "TransSeconds": cfg["transition_seconds"],
            "Offset": sc.get("offset", 0.0), "Intensity": 6.0})
        set_tex(mi, "SlideA", a)
        set_tex(mi, "SlideB", b)
    else:
        mi = mk.instance(f"{SCREENS}/Instances", f"MI_Screen_{name}", neon_m, {"Offset": sc.get("offset", 0.0), "Intensity": 7.0})
        set_tex(mi, "Sign", a)
    mk.MEL.update_material_instance(mi)
    mk.EAL.save_loaded_asset(mi)
    mis[ms["material"]] = mi

# Assign to the city actors' screen slots, and tint each glow light with the screen's colour
n = 0
for actor in dck.ACTORS.get_all_level_actors():
    if isinstance(actor, unreal.StaticMeshActor) and actor.get_actor_label().startswith("City_"):
        comp = actor.static_mesh_component
        for i, slot in enumerate(comp.get_material_slot_names()):
            if str(slot) in mis:
                comp.modify()
                comp.set_material(i, mis[str(slot)])
                n += 1
for name, rgb in colours.items():
    light = dck.find_actor(f"L_Screen_{name}")
    if light:
        mx = max(rgb) or 1.0
        c = light.get_component_by_class(unreal.RectLightComponent)
        c.modify()
        c.set_light_color(unreal.LinearColor(rgb[0] / mx, rgb[1] / mx, rgb[2] / mx, 1.0))
dck.LEVELS.save_current_level()
print(f"setup_screens: {len(texs)} textures, {len(mis)} screen materials, {n} slots assigned")
