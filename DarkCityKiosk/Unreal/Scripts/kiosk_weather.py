"""The weathered kiosk materials (surfacing pass, 2026-10-04).

Blender bakes WHERE the kiosk ages (kiosk/weather.py: masks in Unreal/RawContent/weather, read
through the second UV channel); this script decides HOW it looks in Unreal:
  1. imports T_KioskWear_A/B/C (8K masks on WeatherUV), T_KioskWear_D (4K, brief 5B: spatter, sun
     fade, zinc oxide, scuffs) and T_WearDetail (tiling chips, scratches, water spots, mottling on the
     metre-scale UVMap) into /Game/DarkCity/Kiosk/Weather/Textures,
  2. builds M_KioskWeathered: one layered shader (paint generations -> chips to primer and steel ->
     rust -> grime -> splash -> rain streaks -> grease / soot -> hands -> wetness) with roughness and
     metallic following every layer,
  3. makes MI_KW_<material> for each material in scene_config.KIOSK_WEATHER (colour from the glTF
     instance, amounts from the category + overrides),
  4. sets them on the weathered slots of the SM_Kiosk_* actors (overrides on the actors, so a
     re-import keeps them; kiosk_refresh.py re-runs the assignment).

    node Scripts/ue.mjs Scripts/kiosk_weather.py              # everything
    node Scripts/ue.mjs Scripts/kiosk_weather.py --textures   # re-import the masks (after weather_masks.py)
    node Scripts/ue.mjs Scripts/kiosk_weather.py --instances  # only re-apply scene_config numbers
    node Scripts/ue.mjs Scripts/kiosk_weather.py --off        # back to the clean glTF materials (A/B checks)
"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402
import matkit as mk  # noqa: E402
import scene_config as S  # noqa: E402

dck, mk, S = importlib.reload(dck), importlib.reload(mk), importlib.reload(S)
import unreal  # noqa: E402
import wetfx_hlsl as W  # noqa: E402

W = importlib.reload(W)

MEL = unreal.MaterialEditingLibrary
FOLDER = f"{dck.GAME}/Kiosk/Weather"
TEX = f"{FOLDER}/Textures"
MASTER = "M_KioskWeathered"
RAW_W = os.path.join(dck.RAW, "weather")
GLTF_MATS = f"{dck.KIOSK_MESHES}/{dck.KIOSK_GLB}/Materials"
DETAIL_TILE_M = 0.5  # kiosk/weather.py DETAIL_TILE_M
TEXTURES = ("T_KioskWear_A", "T_KioskWear_B", "T_KioskWear_C", "T_KioskWear_D", "T_WearDetail")

SCALARS = ["EdgeWear", "RustAmount", "GrimeAmount", "StreakAmount", "StreakRustAmount", "SootAmount", "GreaseAmount",
           "TouchAmount", "SplashAmount", "WetAmount", "PaintVar", "PrimerAmount", "ScratchAmount", "BaseRough",
           "NewRough", "BareRough", "Metallic", "BareMetallic",
           # brief 5B (the fourth mask, X): spatter, sun fade, zinc oxide, scuffs; the lit diffuser's age
           "SpeckAmount", "FadeAmount", "FadedRough", "OxideAmount", "ScuffAmount", "EmisAge"]
COLORS = ["PaintColor", "PaintAmber", "PaintFaded", "PaintNew", "PrimerColor", "BareColor", "RustDark", "RustOrange",
          "RustBlack", "GrimeColor", "MudColor", "StreakColor", "GreaseColor", "SootColor", "ChalkColor", "OxideColor"]

# A: edge wear, rust, grime, dark streaks | B: rust streaks, soot, touch, wet | W: paint variation,
# newness, splash, grease | X (brief 5B, half resolution): dried rain spatter, sun fade, zinc oxide,
# light scuffs; zero outside the refined zones | D: chip noise, scratches, water spots, mottling
# (0.5 m tile) | D2: the same detail at a coarser scale for broad breakup. Mode 0 returns (base
# colour, roughness), mode 1 (metallic, emissive multiplier rgb); the compiler folds the unused half.
HLSL = r"""
float edge = A.r, rust = A.g, grime = A.b, sdark = A.a;
float srust = B.r, soot = B.g, touch = B.b, wet = B.a;
float pvar = W.r, newness = W.g, splash = W.b, grease = W.a;
float spk0 = X.r, fade0 = X.g, ox0 = X.b, scuff = X.a;

// paint generations: original, darker amber, faded, newer repaint; broad blotchy fading
float amber = saturate((0.45 - pvar) * 3.0);
float faded = saturate((pvar - 0.58) * 2.6);
float fresh = saturate((newness - 0.45) * 2.0);
float3 paint = PaintColor;
paint = lerp(paint, PaintAmber, amber * PaintVar);
paint = lerp(paint, PaintFaded, faded * PaintVar);
paint = lerp(paint, PaintNew, fresh * PaintVar);
// sun-faded, chalky paint (roof housings): paler, flatter
float fd = saturate(fade0 * FadeAmount * lerp(0.8, 1.2, D2.a));
paint = lerp(paint, ChalkColor, fd);
paint *= lerp(1.0 - 0.10 * PaintVar, 1.0 + 0.05 * PaintVar, D2.a);

// chips: the baked edge-wear potential, thresholded by chip noise -> crisp flakes; a primer rim
float n = D.r - 0.5;
float wearT = saturate(edge * EdgeWear) + n * 0.75;
float chip = smoothstep(0.50, 0.55, wearT);
float rim = saturate(smoothstep(0.40, 0.50, wearT) - chip);
float scr = smoothstep(0.5, 0.9, D.g) * saturate(edge * 1.6 + touch + splash * 0.6) * ScratchAmount;
chip = max(chip, scr * 0.85);

// rust: patchy, from dark brown to orange, nearly black where it is oldest
float rustT = saturate(rust * RustAmount);
float rustM = smoothstep(0.30, 0.70, rustT + (D2.r - 0.5) * 0.55 + (D.a - 0.5) * 0.2);
float3 rustCol = lerp(RustDark, RustOrange, smoothstep(0.3, 0.85, D.a * 0.6 + rustT * 0.5));
rustCol = lerp(rustCol, RustBlack, smoothstep(0.7, 1.0, rustT) * 0.55);
float3 bare = BareColor * lerp(0.75, 1.25, D2.r);
bare = lerp(bare, rustCol, saturate(rustT * 1.4) * 0.65);  // exposed steel rusts first

float3 col = lerp(paint, PrimerColor, rim * PrimerAmount);
col = lerp(col, bare, chip);
col = lerp(col, rustCol, rustM * 0.85);

// grime in recesses, under things, along the base
float g = pow(saturate(grime * GrimeAmount * lerp(0.7, 1.15, D2.a)), 1.3);  // concentrated in recesses, open paint stays bright
col = lerp(col, GrimeColor, g * 0.72);
// splash-back: muddy speckles and dried spots near the ground
float sp = saturate(splash * SplashAmount) * smoothstep(0.25, 0.7, D.b + splash * 0.35);
col = lerp(col, MudColor, sp * 0.42);
// rain streaks: dark grime and rust-coloured runs
float sd = saturate(sdark * StreakAmount);
float sr = saturate(srust * StreakRustAmount);
col = lerp(col, StreakColor, sd * 0.75);
col = lerp(col, lerp(RustDark, RustOrange, 0.55), sr * 0.62);
// zinc white rust: pale, matte, patchy
float ox = saturate(ox0 * OxideAmount) * smoothstep(0.25, 0.6, ox0 * 0.55 + D2.r * 0.45 + (D.a - 0.5) * 0.25);
col = lerp(col, OxideColor, ox * 0.75);
// light abrasion: rubbed back lighter, with fine scratches
float sc = saturate(scuff * ScuffAmount) * (0.55 + 0.45 * smoothstep(0.35, 0.9, D.g)) * smoothstep(0.15, 0.55, D2.a * 0.6 + scuff * 0.5);
col = lerp(col, lerp(paint, BareColor * 2.0, 0.5) * 1.35, sc * 0.7);
// kitchen: brown grease film, matte soot
float gr = saturate(grease * GreaseAmount);
float so = saturate(soot * SootAmount);
col = lerp(col, GreaseColor, gr * 0.55);
col = lerp(col, SootColor, so * 0.65);
// dried rain spatter: dark specks from a few mm to ~1.5 cm, denser where the mask is high
float spd = saturate(spk0 * SpeckAmount);
float spk = spd * smoothstep(0.42 - 0.2 * spd, 0.7, max(D2.b, D.b * 0.85));
col = lerp(col, StreakColor, spk * 0.7);
// hands: rubbed clean; worn edges polished back to steel
float t = saturate(touch * TouchAmount);
col = lerp(col, lerp(paint, BareColor * 1.8, chip), t * 0.55);
// rain darkens what soaks it up
float w = saturate(wet * WetAmount);
col *= 1.0 - w * 0.22 * saturate(g + sp + rustM + sd + sr);

float r = lerp(BaseRough, NewRough, fresh) + (D.a - 0.5) * 0.10;
r = lerp(r, BareRough, chip);
r = lerp(r, 0.86, rustM);
r = lerp(r, 0.78, g * 0.7);
r = lerp(r, 0.85, sp * 0.6);
r = lerp(r, 0.5, sd * 0.4);
r = lerp(r, 0.26, gr * 0.85);
r = lerp(r, 0.92, so * 0.6);
r = lerp(r, 0.2, t * 0.75);
r += FadedRough * fd;
r = lerp(r, 0.82, ox * 0.75);
r = lerp(r, 0.34, sc * 0.6);
r = lerp(r, 0.7, spk * 0.4);
r *= lerp(1.0, 0.45, w * (1.0 - rustM * 0.6));
r = clamp(r, 0.05, 1.0);

float m = lerp(Metallic, BareMetallic, chip);
m *= 1.0 - saturate(rustM + g * 0.6 + sd * 0.4 + sr * 0.6 + so + gr * 0.5 + sp + ox * 0.8 + spk * 0.5);
m = max(m, BareMetallic * t * chip);
m = max(m, BareMetallic * sc * 0.6);
float e = 1.0 - saturate(g * 0.55 + sd * 0.6 + sr * 0.6 + so * 0.7 + gr * 0.4 + rustM + spk * 0.6);
// the lit diffuser's age (EmisAge): yellowed panels warmer and dimmer, sun-bleached ones paler,
// a newer replacement a touch brighter (strong enough to survive the tonemapper's shoulder)
float3 eT = float3(1.0, 1.0 - (0.15 * amber - 0.03 * faded) * EmisAge, 1.0 - (0.3 * amber - 0.3 * faded) * EmisAge)
          * (1.0 - (0.25 * amber - 0.03 * faded - 0.06 * fresh) * EmisAge);

if (Mode < 0.5) return float4(col, r);
return float4(m, e * eT);
"""


def import_textures():
    mk.ensure_dir(TEX)
    tasks = []
    for name in TEXTURES:
        src = os.path.join(RAW_W, f"{name}.png")
        if not os.path.exists(src):
            raise RuntimeError(f"missing {src}: run Blender export_kiosk_glb.py (or weather_masks.py)")
        tasks.append(dck.setp(unreal.AssetImportTask(), filename=src, destination_path=TEX, destination_name=name,
                              automated=True, replace_existing=True, save=False))
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for name in TEXTURES:
        tex = unreal.load_asset(f"{TEX}/{name}")
        tex.modify()
        mk.setp(tex, srgb=False, compression_settings=unreal.TextureCompressionSettings.TC_BC7,
                lod_group=unreal.TextureGroup.TEXTUREGROUP_WORLD, never_stream=False)
        dck.EAL.save_loaded_asset(tex)
        print(f"texture {name}: {tex.blueprint_get_size_x()}x{tex.blueprint_get_size_y()}")


def build_material():
    m = mk.material(FOLDER, MASTER)
    X = -3000
    uv1 = mk.expr(m, unreal.MaterialExpressionTextureCoordinate, X, -600, coordinate_index=1)
    uv0 = mk.expr(m, unreal.MaterialExpressionTextureCoordinate, X, 200, coordinate_index=0,
                  u_tiling=1.0 / DETAIL_TILE_M, v_tiling=1.0 / DETAIL_TILE_M)
    uv0b = mk.expr(m, unreal.MaterialExpressionTextureCoordinate, X, 450, coordinate_index=0,
                   u_tiling=1.0 / 2.3, v_tiling=1.0 / 2.3)
    lin = unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
    samp = {}
    for i, (key, tex, uv) in enumerate((("A", "T_KioskWear_A", uv1), ("B", "T_KioskWear_B", uv1), ("W", "T_KioskWear_C", uv1),
                                         ("X", "T_KioskWear_D", uv1), ("D", "T_WearDetail", uv0), ("D2", "T_WearDetail", uv0b))):
        param = {"A": "WearA", "B": "WearB", "W": "WearC", "X": "WearD"}.get(key, "WearDetail")
        s = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, X + 350, -700 + i * 300, parameter_name=param,
                    texture=unreal.load_asset(f"{TEX}/{tex}"), sampler_type=lin)
        mk.link(uv, "", s, "UVs")
        samp[key] = s
    params = {}
    common = S.WEATHER_COMMON
    for i, name in enumerate(SCALARS):
        params[name] = mk.scalar(m, name, common.get(name, 0.0), X + 350, 900 + i * 90)
    for i, name in enumerate(COLORS):
        params[name] = mk.vector(m, name, common.get(name, (0.5, 0.5, 0.5)), X + 700, 900 + i * 110)
    names = ["A", "B", "W", "X", "D", "D2", "Mode"] + SCALARS + COLORS
    outs = []
    for k, mode in enumerate((0.0, 1.0)):
        c = mk.custom(m, HLSL, names, unreal.CustomMaterialOutputType.CMOT_FLOAT4, -1400, -400 + k * 900,
                      "Kiosk weathering" + (" (metal, emissive)" if mode else ""))
        for key, s in samp.items():
            mk.link(s, "RGBA", c, key)
        mk.link(mk.expr(m, unreal.MaterialExpressionConstant, -1700, -400 + k * 900, r=mode), "", c, "Mode")
        for name, p in params.items():
            mk.link(p, "", c, name)
        outs.append(c)
    rgb = mk.expr(m, unreal.MaterialExpressionComponentMask, -1000, -400, r=True, g=True, b=True, a=False)
    rough = mk.expr(m, unreal.MaterialExpressionComponentMask, -1000, -250, r=False, g=False, b=False, a=True)
    metal = mk.expr(m, unreal.MaterialExpressionComponentMask, -1000, 500, r=True, g=False, b=False, a=False)
    emul = mk.expr(m, unreal.MaterialExpressionComponentMask, -1000, 650, r=False, g=True, b=True, a=True)  # rgb glow multiplier
    for mask, src in ((rgb, outs[0]), (rough, outs[0]), (metal, outs[1]), (emul, outs[1])):
        mk.link(src, "", mask, "")
    ecol = mk.vector(m, "EmissiveColor", (1.0, 0.6, 0.07), -1000, 800)
    estr = mk.scalar(m, "EmissiveStrength", 0.0, -1000, 950)
    e1 = mk.expr(m, unreal.MaterialExpressionMultiply, -750, 800)
    mk.link(ecol, "", e1, "A")
    mk.link(estr, "", e1, "B")
    e2 = mk.expr(m, unreal.MaterialExpressionMultiply, -550, 700)
    mk.link(e1, "", e2, "A")
    mk.link(emul, "", e2, "B")
    # rain contact pass (prompt 9): the platform's wet layer, behind a static switch that only
    # MI_KW_Platform_Concrete turns on (wet_fx.py), so every other kiosk material compiles exactly as before
    if dck.EAL.does_asset_exist(W.RAIN_MAP) and dck.EAL.does_asset_exist(W.MPC):
        rc = W.rain_contact_branch(m, outs[0], -1000, 1400, S.WET_FX["contact"])
        rgb2 = mk.expr(m, unreal.MaterialExpressionComponentMask, -500, 1400, r=True, g=True, b=True, a=False)
        rough2 = mk.expr(m, unreal.MaterialExpressionComponentMask, -500, 1550, r=False, g=False, b=False, a=True)
        nws = mk.expr(m, unreal.MaterialExpressionComponentMask, -500, 2100, r=True, g=True, b=True, a=False)
        mk.link(rc[0], "", rgb2, "")
        mk.link(rc[0], "", rough2, "")
        mk.link(rc[1], "", nws, "")
        nts = mk.expr(m, unreal.MaterialExpressionTransform, -350, 2100,
                      transform_source_type=unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD,
                      transform_type=unreal.MaterialVectorCoordTransform.TRANSFORM_TANGENT)
        mk.link(nws, "", nts, "")
        flat = mk.expr(m, unreal.MaterialExpressionConstant3Vector, -350, 2250, constant=unreal.LinearColor(0.0, 0.0, 1.0, 0.0))
        sw = {}
        for key, (on, off) in (("col", (rgb2, rgb)), ("rough", (rough2, rough)), ("nrm", (nts, flat))):
            s_ = mk.expr(m, unreal.MaterialExpressionStaticSwitchParameter, -150, {"col": -400, "rough": -250, "nrm": 2100}[key],
                         parameter_name="UseRainContact", default_value=False)
            mk.link(on, "", s_, "True")
            mk.link(off, "", s_, "False")
            sw[key] = s_
        rgb, rough = sw["col"], sw["rough"]
        mk.out(m, sw["nrm"], "", unreal.MaterialProperty.MP_NORMAL)
    mk.out(m, rgb, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mk.out(m, rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mk.out(m, metal, "", unreal.MaterialProperty.MP_METALLIC)
    mk.out(m, e2, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mk.finish(m)
    print(f"material {FOLDER}/{MASTER}: {len(MEL.get_material_expressions(m))} nodes")
    return m


def _lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def instance_params(name):
    cat, over = S.KIOSK_WEATHER[name]
    p = dict(S.WEATHER_COMMON)
    p.update(S.WEATHER_CATEGORIES[cat])
    p.update(over)
    gl = unreal.load_asset(f"{GLTF_MATS}/{name}")
    if "PaintColor" not in over:
        if name in S.EMISSIVE_COLOR:
            p["PaintColor"] = S.EMISSIVE_COLOR[name]
        else:
            c = MEL.get_material_instance_vector_parameter_value(gl, "BaseColorFactor")
            p["PaintColor"] = (c.r, c.g, c.b)
    if cat in ("galv", "aged") and "Metallic" not in over:
        p["Metallic"] = MEL.get_material_instance_scalar_parameter_value(gl, "MetallicFactor")
    base = p["PaintColor"]
    lum = _lum(base)
    if cat == "yellow":  # generations of one yellow: darker amber, chalky faded, fresher repaint
        p.setdefault("PaintAmber", (base[0] * 0.70, base[1] * 0.55, base[2] * 0.45))
        p.setdefault("PaintFaded", tuple(1.06 * (0.65 * c + 0.35 * t) for c, t in zip(base, (lum * 1.15, lum * 1.06, lum * 0.78))))
        p.setdefault("PaintNew", (base[0] * 1.05, base[1] * 1.03, base[2] * 0.88))
    else:  # other paints and metals only get a little darker / paler with age
        p.setdefault("PaintAmber", tuple(c * 0.84 for c in base))
        p.setdefault("PaintFaded", tuple(1.1 * (0.75 * c + 0.25 * lum) for c in base))
        p.setdefault("PaintNew", tuple(c * 1.02 for c in base))
    # sun-chalked target of the fade mask (5B): paler and greyer than the paint
    p.setdefault("ChalkColor", tuple(min(1.0, 1.4 * (0.65 * c + 0.35 * lum)) for c in base))
    if name in S.EMISSIVE:
        p["EmissiveStrength"] = S.EMISSIVE[name]
        p["EmissiveColor"] = S.EMISSIVE_COLOR.get(name, base)
    return p


def build_instances():
    master = unreal.load_asset(f"{FOLDER}/{MASTER}")
    mis = {}
    for name in S.KIOSK_WEATHER:
        if not dck.EAL.does_asset_exist(f"{GLTF_MATS}/{name}"):
            continue
        p = instance_params(name)
        scal = {k: v for k, v in p.items() if not isinstance(v, tuple)}
        vec = {k: v for k, v in p.items() if isinstance(v, tuple)}
        mis[name] = mk.instance(f"{FOLDER}/Instances", f"MI_KW_{name}", master, scal, vec)
    # plain slots aged on one section only (S.KIOSK_SLOT_AGED): children of the glTF instance
    for section, slots in S.KIOSK_SLOT_AGED.items():
        for slot, params in slots.items():
            scal = {k: v for k, v in params.items() if not isinstance(v, tuple)}
            vec = {k: v for k, v in params.items() if isinstance(v, tuple)}
            mis[(section, slot)] = mk.instance(f"{FOLDER}/Instances", f"MI_KW_{slot}_{section}",
                                               unreal.load_asset(f"{GLTF_MATS}/{slot}"), scal, vec)
    print(f"instances: {len(mis)}")
    return mis


def assign(off=False):
    """Weathered instances on every weathered slot of the kiosk sections that carry WeatherUV."""
    sml = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    sections = {f"SM_Kiosk_{s}" for s in dck.K.WEATHER["sections"]}
    n = 0
    for a in dck.ACTORS.get_all_level_actors():
        label = a.get_actor_label()
        if not isinstance(a, unreal.StaticMeshActor) or label not in sections:
            continue
        comp = a.static_mesh_component
        mesh = comp.static_mesh
        if mesh is None:
            continue
        has_uv1 = sml.get_num_uv_channels(mesh, 0) >= 2
        a.modify()
        comp.modify()
        section = label[len("SM_Kiosk_"):]
        for i, slot in enumerate(mesh.static_materials):
            name = str(slot.material_slot_name)
            path = f"{FOLDER}/Instances/MI_KW_{name}"
            aged = f"{FOLDER}/Instances/MI_KW_{name}_{section}"
            if not off and has_uv1 and name in S.KIOSK_WEATHER and dck.EAL.does_asset_exist(path):
                comp.set_material(i, unreal.load_asset(path))
                n += 1
            elif not off and name in S.KIOSK_SLOT_AGED.get(section, {}) and dck.EAL.does_asset_exist(aged):
                comp.set_material(i, unreal.load_asset(aged))
                n += 1
            elif comp.get_material(i) and comp.get_material(i).get_name().startswith("MI_KW_"):
                comp.set_material(i, slot.material_interface)  # back to the glTF instance
        if not has_uv1:
            print(f"  {label}: no WeatherUV (re-import the weathered glb), left clean")
    dck.LEVELS.save_current_level()
    print(f"assigned {n} weathered slots" if not off else "weathering off: glTF materials restored")


if __name__ == "__main__":
    args = sys.argv[1:]
    dck.ensure_map()
    if "--off" in args:
        assign(off=True)
    elif "--instances" in args:
        build_instances()
        assign()
    else:
        if "--textures" in args or not dck.EAL.does_asset_exist(f"{TEX}/T_KioskWear_A") or "--all" in args or not args:
            import_textures()
        if "--textures" not in args or not dck.EAL.does_asset_exist(f"{FOLDER}/{MASTER}"):
            build_material()
            build_instances()
        assign()
    print("kiosk_weather: done")
