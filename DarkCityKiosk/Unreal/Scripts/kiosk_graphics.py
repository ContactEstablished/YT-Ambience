"""Signage pass (2026-10-05, brief 6): the kiosk's graphics in Unreal.

Blender lays the cards (kiosk/graphics.py, build_graphics.py -> RawContent/kiosk_graphics.glb and
graphics/kiosk_decals.json); the art is Graphics/make_kiosk_graphics.mjs (RawContent/graphics/
T_KG_<Atlas>_{C,N,S}.png). This script:
  1. imports the atlases (Paper, Labels, Signs, Decals: albedo+opacity, normal, rough/metal/emissive/
     weather-response) into /Game/DarkCity/Kiosk/Graphics/Textures,
  2. imports kiosk_graphics.glb (SM_Kiosk_Graphics: the cards; SM_Kiosk_Signs: the 24h lightbox, its
     hardware, the lantern lettering) and places both at the kiosk origin, not receiving decals,
  3. builds M_KioskGraphic: masked, two-sided; samples its atlas cell through UV0 and the kiosk's
     weathering masks (T_KioskWear_A..D) through UV1, which Blender set to the WeatherUV of the
     surface under each card, so the wall's rain streaks, rust runs, grime, splash, kitchen grease and
     wetness carry on across the paper (scaled per texel by how much each material soaks up),
  4. builds M_KioskDecal (deferred decal, one instance per item) and spawns the paint decals (adhesive
     ghosts, holes, residue, marker writing, the stencilled stall number),
  5. ages the fascia lettering: M_KioskLettering on the canopy's Sign_Text_Black slot (faded vinyl,
     fine crazing that leaks the light behind, the diffuser's own streaks and dust carried over the
     letters through its WeatherUV, mapped from world position),
  6. moves the 24h sign's light (L_Lantern_R) to the new lightbox.

    node Scripts/ue.mjs Scripts/kiosk_graphics.py            # everything
    node Scripts/ue.mjs Scripts/kiosk_graphics.py --apply    # numbers, overrides, decals, light only
Tunables: scene_config.GRAPHICS_LOOK.
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

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
FOLDER = f"{dck.GAME}/Kiosk/Graphics"
TEX = f"{FOLDER}/Textures"
INST = f"{FOLDER}/Instances"
GLB = "kiosk_graphics"
WX_TEX = f"{dck.GAME}/Kiosk/Weather/Textures"
KIOSK_MATS = f"{dck.KIOSK_MESHES}/{dck.KIOSK_GLB}/Materials"
RAW_G = os.path.join(dck.RAW, "graphics")
ATLASES = ("Paper", "Labels", "Signs", "Decals", "Kitchen", "Exterior")  # Kitchen: kitchen pass (10/9); Exterior: exterior pass (10/9)
LOOK = S.GRAPHICS_LOOK

# ---- 1. textures ---------------------------------------------------------------------------------

def import_textures():
    mk.ensure_dir(TEX)
    tasks = []
    for a in ATLASES:
        for mp in ("C", "N", "S"):
            src = os.path.join(RAW_G, f"T_KG_{a}_{mp}.png")
            tasks.append(dck.setp(unreal.AssetImportTask(), filename=src, destination_path=TEX, destination_name=f"T_KG_{a}_{mp}",
                                  automated=True, replace_existing=True, save=False))
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    TC = unreal.TextureCompressionSettings
    for a in ATLASES:
        for mp, srgb, comp in (("C", True, TC.TC_BC7), ("N", False, TC.TC_NORMALMAP), ("S", False, TC.TC_BC7)):
            t = unreal.load_asset(f"{TEX}/T_KG_{a}_{mp}")
            t.modify()
            mk.setp(t, srgb=srgb, compression_settings=comp, lod_group=unreal.TextureGroup.TEXTUREGROUP_WORLD, never_stream=True)
            EAL.save_loaded_asset(t)
    print(f"textures: {len(tasks)} imported")


# ---- 2. meshes -----------------------------------------------------------------------------------

def import_meshes():
    src = os.path.join(dck.RAW, f"{GLB}.glb")
    task = dck.setp(unreal.AssetImportTask(), filename=src, destination_path=FOLDER, automated=True, replace_existing=True, save=True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    sml = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    for name in ("SM_Kiosk_Graphics", "SM_Kiosk_Signs"):
        mesh = unreal.load_asset(f"{FOLDER}/{GLB}/StaticMeshes/{name}")
        ns = mesh.get_editor_property("nanite_settings")
        if ns.enabled:  # small, masked cards: plain rendering is cheaper and keeps the alpha clip exact
            ns.enabled = False
            sml.set_nanite_settings(mesh, ns, apply_changes=True)  # rebuilds; setting the property alone kept the Nanite fallback
            EAL.save_loaded_asset(mesh)
        print(f"mesh {name}: {mesh.get_num_triangles(0)} tris")


# ---- 3. the card material ------------------------------------------------------------------------

CARD_SCALARS = ["GrimeAmount", "StreakAmount", "StreakRustAmount", "SplashAmount", "WetAmount", "SootAmount", "GreaseAmount",
                "SpeckAmount", "TouchAmount", "AgeTint", "EmissiveStrength"]
CARD_COLORS = ["GrimeColor", "StreakColor", "RustStain", "MudColor", "SootColor", "GreaseColor", "EmissiveTint"]
CARD_HLSL = r"""
// Cl: atlas albedo + opacity; Sm: roughness, metallic, emissive mask, weather response.
// A/B/W/X: the kiosk's weathering masks at the surface under this card (UV1); D: wear detail.
// VC: R per-card random, G age; VA: 1 where the surface under the card is weathered.
float3 base = Cl.rgb;
float3 col = base;
float wf = VA * Sm.a;
float age = VC.g;
float grime = A.b, sdark = A.a;
float srust = B.r, soot = B.g, touch = B.b, wet = B.a;
float splash = W.b, grease = W.a;
float g = pow(saturate(grime * GrimeAmount * (0.6 + 0.8 * age)), 1.2) * wf;
col = lerp(col, GrimeColor, g * 0.6);
float sd = saturate(sdark * StreakAmount) * wf;
col = lerp(col, StreakColor, sd * 0.7);
float sr = saturate(srust * StreakRustAmount) * wf;
col = lerp(col, RustStain, sr * 0.65);
float sp = saturate(splash * SplashAmount) * smoothstep(0.25, 0.7, D.b + splash * 0.35) * wf;
col = lerp(col, MudColor, sp * 0.5);
float gr = saturate(grease * GreaseAmount) * wf;
col = lerp(col, GreaseColor, gr * 0.5);
float so = saturate(soot * SootAmount) * wf;
col = lerp(col, SootColor, so * 0.6);
float spk = saturate(X.r * SpeckAmount) * smoothstep(0.45, 0.72, max(D.b, D.r)) * wf;
col = lerp(col, StreakColor, spk * 0.6);
float t = saturate(touch * TouchAmount) * wf;
col = lerp(col, col * 0.78, t * 0.6);
col = lerp(col, col * float3(0.93, 0.9, 0.83), saturate(age * AgeTint * Sm.a));
float w = saturate(wet * WetAmount) * wf;
col *= 1.0 - w * 0.28;
float r = Sm.r;
r = lerp(r, 0.85, g * 0.5);
r = lerp(r, 0.6, sd * 0.3);
r *= lerp(1.0, 0.45, w);
if (Mode < 0.5) return float4(col, clamp(r, 0.05, 1.0));
float dim = 1.0 - saturate(g * 0.8 + sd * 0.7 + sr * 0.7 + so * 0.8 + spk * 0.6);
float3 e = base * Sm.b * EmissiveStrength * EmissiveTint * dim;
float m = Sm.g * (1.0 - saturate(g + sd * 0.5 + sr));
return float4(m, e);
"""
UV_HLSL = r"""
// atlas UV: the card's own UV0, or (TileM > 0) metre-scale UV0 tiled inside one atlas cell
float2 t = Cell.xy + frac(UV / max(TileM, 1e-4)) * Cell.zw;
return TileM > 0 ? t : UV;
"""


def build_card_material():
    m = mk.material(FOLDER, "M_KioskGraphic")
    mk.setp(m, blend_mode=unreal.BlendMode.BLEND_MASKED, two_sided=True, opacity_mask_clip_value=0.5)
    X = -3000
    uv0 = mk.expr(m, unreal.MaterialExpressionTextureCoordinate, X, -900, coordinate_index=0)
    uv1 = mk.expr(m, unreal.MaterialExpressionTextureCoordinate, X, -100, coordinate_index=1)
    cellp = mk.vector(m, "Cell", (0, 0, 1), X, -800)
    tile = mk.scalar(m, "TileM", 0.0, X, -700)
    uvc = mk.custom(m, UV_HLSL, ["UV", "Cell", "TileM"], unreal.CustomMaterialOutputType.CMOT_FLOAT2, X + 300, -850, "atlas UV")
    mk.link(uv0, "", uvc, "UV")
    mk.link(cellp, "RGBA", uvc, "Cell")
    mk.link(tile, "", uvc, "TileM")
    lin, col_s, nrm_s = (unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
                         unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tC = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, X + 650, -1000, parameter_name="Color",
                 texture=unreal.load_asset(f"{TEX}/T_KG_Paper_C"), sampler_type=col_s)
    tN = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, X + 650, -700, parameter_name="Normal",
                 texture=unreal.load_asset(f"{TEX}/T_KG_Paper_N"), sampler_type=nrm_s)
    tS = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, X + 650, -400, parameter_name="Mask",
                 texture=unreal.load_asset(f"{TEX}/T_KG_Paper_S"), sampler_type=lin)
    for t in (tC, tN, tS):
        mk.link(uvc, "", t, "UVs")
    det = mk.expr(m, unreal.MaterialExpressionMultiply, X + 300, 500)
    mk.link(uv1, "", det, "A")
    mk.link(mk.scalar(m, "DetailScale", 40.0, X, 550), "", det, "B")
    samp = {}
    for i, (key, tex, uv) in enumerate((("A", "T_KioskWear_A", uv1), ("B", "T_KioskWear_B", uv1), ("W", "T_KioskWear_C", uv1),
                                         ("X", "T_KioskWear_D", uv1), ("D", "T_WearDetail", det))):
        s = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, X + 650, -100 + i * 300,
                    parameter_name={"A": "WearA", "B": "WearB", "W": "WearC", "X": "WearD"}.get(key, "WearDetail"),
                    texture=unreal.load_asset(f"{WX_TEX}/{tex}"), sampler_type=lin)
        mk.link(uv, "", s, "UVs")
        samp[key] = s
    vc = mk.expr(m, unreal.MaterialExpressionVertexColor, X + 650, 1500)
    params = {}
    for i, n in enumerate(CARD_SCALARS):
        params[n] = mk.scalar(m, n, LOOK["paper"].get(n, 0.0), X + 1000, 900 + i * 90)
    for i, n in enumerate(CARD_COLORS):
        params[n] = mk.vector(m, n, LOOK["colors"].get(n, (0.5, 0.5, 0.5)), X + 1300, 900 + i * 110)
    names = ["Cl", "Sm", "A", "B", "W", "X", "D", "VC", "VA", "Mode"] + CARD_SCALARS + CARD_COLORS
    outs = []
    for k, mode in enumerate((0.0, 1.0)):
        c = mk.custom(m, CARD_HLSL, names, unreal.CustomMaterialOutputType.CMOT_FLOAT4, -1200, -500 + k * 900,
                      "Card weathering" + (" (metal, emissive)" if mode else ""))
        mk.link(tC, "RGBA", c, "Cl")
        mk.link(tS, "RGBA", c, "Sm")
        for key, s in samp.items():
            mk.link(s, "RGBA", c, key)
        mk.link(vc, "", c, "VC")
        mk.link(vc, "A", c, "VA")
        mk.link(mk.expr(m, unreal.MaterialExpressionConstant, -1500, -500 + k * 900, r=mode), "", c, "Mode")
        for n, p in params.items():
            mk.link(p, "", c, n)
        outs.append(c)
    rgb = mk.expr(m, unreal.MaterialExpressionComponentMask, -800, -500, r=True, g=True, b=True, a=False)
    rough = mk.expr(m, unreal.MaterialExpressionComponentMask, -800, -350, r=False, g=False, b=False, a=True)
    metal = mk.expr(m, unreal.MaterialExpressionComponentMask, -800, 400, r=True, g=False, b=False, a=False)
    emis = mk.expr(m, unreal.MaterialExpressionComponentMask, -800, 550, r=False, g=True, b=True, a=True)
    for mask, src in ((rgb, outs[0]), (rough, outs[0]), (metal, outs[1]), (emis, outs[1])):
        mk.link(src, "", mask, "")
    alpha = mk.expr(m, unreal.MaterialExpressionComponentMask, -800, -800, r=False, g=False, b=False, a=True)
    mk.link(tC, "RGBA", alpha, "")
    mk.out(m, rgb, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mk.out(m, rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mk.out(m, metal, "", unreal.MaterialProperty.MP_METALLIC)
    mk.out(m, emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mk.out(m, tN, "RGB", unreal.MaterialProperty.MP_NORMAL)
    mk.out(m, alpha, "", unreal.MaterialProperty.MP_OPACITY_MASK)
    mk.finish(m)
    print(f"material M_KioskGraphic: {len(MEL.get_material_expressions(m))} nodes")
    return m


# ---- 4. the decal material -----------------------------------------------------------------------

def build_decal_material():
    m = mk.material(FOLDER, "M_KioskDecal")
    mk.setp(m, material_domain=unreal.MaterialDomain.MD_DEFERRED_DECAL, blend_mode=unreal.BlendMode.BLEND_TRANSLUCENT)
    X = -1600
    uv0 = mk.expr(m, unreal.MaterialExpressionTextureCoordinate, X, -300, coordinate_index=0)
    cellp = mk.vector(m, "Cell", (0, 0, 1), X, -200)
    code = ("float2 s = SwapUV > 0.5 ? UV.yx : UV; float2 u = float2(lerp(s.x, 1.0 - s.x, FlipU), lerp(s.y, 1.0 - s.y, FlipV)); "
            "return Cell.xy + u * Cell.zw;")
    uvc = mk.custom(m, code, ["UV", "Cell", "SwapUV", "FlipU", "FlipV"], unreal.CustomMaterialOutputType.CMOT_FLOAT2, X + 300, -250,
                    "decal atlas UV")
    mk.link(uv0, "", uvc, "UV")
    mk.link(cellp, "RGBA", uvc, "Cell")
    for i, (n, v) in enumerate(LOOK["decal_uv"].items()):
        mk.link(mk.scalar(m, n, v, X, -100 + i * 100), "", uvc, n)
    lin, col_s, nrm_s = (unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR, unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
                         unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    tC = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, X + 650, -500, parameter_name="Color",
                 texture=unreal.load_asset(f"{TEX}/T_KG_Decals_C"), sampler_type=col_s)
    tN = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, X + 650, -200, parameter_name="Normal",
                 texture=unreal.load_asset(f"{TEX}/T_KG_Decals_N"), sampler_type=nrm_s)
    tS = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, X + 650, 100, parameter_name="Mask",
                 texture=unreal.load_asset(f"{TEX}/T_KG_Decals_S"), sampler_type=lin)
    for t in (tC, tN, tS):
        mk.link(uvc, "", t, "UVs")
    tint = mk.vector(m, "Tint", (1, 1, 1), X + 650, 400)
    colm = mk.expr(m, unreal.MaterialExpressionMultiply, X + 1000, -500)
    mk.link(tC, "RGB", colm, "A")
    mk.link(tint, "", colm, "B")
    op = mk.expr(m, unreal.MaterialExpressionMultiply, X + 1000, -300)
    mk.link(tC, "A", op, "A")
    mk.link(mk.scalar(m, "Opacity", 1.0, X + 650, 550), "", op, "B")
    mk.out(m, colm, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mk.out(m, op, "", unreal.MaterialProperty.MP_OPACITY)
    mk.out(m, tN, "RGB", unreal.MaterialProperty.MP_NORMAL)
    mk.out(m, tS, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    mk.finish(m)
    print(f"material M_KioskDecal: {len(MEL.get_material_expressions(m))} nodes")
    return m


# ---- 5. the fascia lettering ---------------------------------------------------------------------

LETTER_UV_HLSL = r"""
// world (cm) -> the lit diffuser's WeatherUV: front letters (kiosk y < -2 m) map on (x, z), the left
// band's on (y, z); Unreal's y is the kiosk's -y
float3 p = WP / 100.0;
bool front = WP.y > 200.0;
float3 q = front ? float3(p.x, p.z, 1.0) : float3(-p.y, p.z, 1.0);
float2 uvF = float2(dot(F0.xyz, q), dot(F1.xyz, q));
float2 uvL = float2(dot(L0.xyz, q), dot(L1.xyz, q));
return front ? uvF : uvL;
"""
LETTER_HLSL = r"""
// vinyl lettering on the old lit panels: per-letter fade, fine crazing that leaks the light behind,
// and the diffuser's own rain runs, dust and spatter carried over the letters (lighter than black)
float3 p = WP / 100.0;
float2 q = (WP.y > 200.0) ? float2(p.x, p.z) : float2(-p.y, p.z);
float cellN = frac(sin(dot(floor(q * 3.2), float2(12.9898, 78.233))) * 43758.5453);
float3 ink = lerp(InkColor, FadedInk, step(1.0 - FadeOdds, cellN) * (0.6 + 0.4 * frac(cellN * 7.1)));
// crazing: distance to the nearest edge of a jittered cell grid (~CrackScale cells per metre)
float2 g = q * CrackScale;
float2 ip = floor(g), fp = frac(g);
float d1 = 8.0, d2 = 8.0;
for (int j = -1; j <= 1; j++)
for (int i = -1; i <= 1; i++) {
    float2 o = float2(i, j);
    float2 h = frac(sin(float2(dot(ip + o, float2(127.1, 311.7)), dot(ip + o, float2(269.5, 183.3)))) * 43758.5453);
    float dd = length(o + h - fp);
    if (dd < d1) { d2 = d1; d1 = dd; } else if (dd < d2) { d2 = dd; }
}
float crack = 1.0 - smoothstep(0.0, 0.1, d2 - d1);
float patchy = smoothstep(0.45, 0.8, frac(sin(dot(floor(q * 9.0), float2(41.3, 17.7))) * 9731.17));
crack *= patchy;
float sd = saturate(A.a * StreakAmount), gm = saturate(A.b * GrimeAmount), spk = saturate(X.r * SpeckAmount);
float3 col = lerp(ink, DustColor, saturate(sd * 0.7 + gm * 0.5 + spk * 0.4));
if (Mode < 0.5) return float4(col, lerp(0.38, 0.7, saturate(gm + sd)));
return float4(LeakColor * crack * LeakStrength * (1.0 - saturate(gm + sd)), 0.0);
"""
LETTER_SCALARS = ["FadeOdds", "CrackScale", "StreakAmount", "GrimeAmount", "SpeckAmount", "LeakStrength"]
LETTER_COLORS = ["InkColor", "FadedInk", "DustColor", "LeakColor"]


def build_letter_material():
    m = mk.material(FOLDER, "M_KioskLettering")
    X = -2400
    wp = mk.expr(m, unreal.MaterialExpressionWorldPosition, X, 0)
    rows = {n: mk.vector(m, n, (0, 0, 0), X, 150 + i * 110) for i, n in enumerate(("F0", "F1", "L0", "L1"))}
    uvc = mk.custom(m, LETTER_UV_HLSL, ["WP", "F0", "F1", "L0", "L1"], unreal.CustomMaterialOutputType.CMOT_FLOAT2, X + 350, 100,
                    "lettering WeatherUV")
    mk.link(wp, "", uvc, "WP")
    for n, p in rows.items():
        mk.link(p, "", uvc, n)
    lin = unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
    sA = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, X + 700, 0, parameter_name="WearA",
                 texture=unreal.load_asset(f"{WX_TEX}/T_KioskWear_A"), sampler_type=lin)
    sX = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, X + 700, 300, parameter_name="WearD",
                 texture=unreal.load_asset(f"{WX_TEX}/T_KioskWear_D"), sampler_type=lin)
    for s in (sA, sX):
        mk.link(uvc, "", s, "UVs")
    lk = LOOK["lettering"]
    params = {n: mk.scalar(m, n, lk[n], X + 700, 700 + i * 90) for i, n in enumerate(LETTER_SCALARS)}
    params.update({n: mk.vector(m, n, lk[n], X + 1000, 700 + i * 110) for i, n in enumerate(LETTER_COLORS)})
    names = ["WP", "A", "X", "Mode"] + LETTER_SCALARS + LETTER_COLORS
    outs = []
    for k, mode in enumerate((0.0, 1.0)):
        c = mk.custom(m, LETTER_HLSL, names, unreal.CustomMaterialOutputType.CMOT_FLOAT4, -900, -300 + k * 700,
                      "Lettering" + (" (light leak)" if mode else ""))
        mk.link(wp, "", c, "WP")
        mk.link(sA, "RGBA", c, "A")
        mk.link(sX, "RGBA", c, "X")
        mk.link(mk.expr(m, unreal.MaterialExpressionConstant, -1200, -300 + k * 700, r=mode), "", c, "Mode")
        for n, p in params.items():
            mk.link(p, "", c, n)
        outs.append(c)
    rgb = mk.expr(m, unreal.MaterialExpressionComponentMask, -500, -300, r=True, g=True, b=True, a=False)
    rough = mk.expr(m, unreal.MaterialExpressionComponentMask, -500, -150, r=False, g=False, b=False, a=True)
    emis = mk.expr(m, unreal.MaterialExpressionComponentMask, -500, 400, r=True, g=True, b=True, a=False)
    for mask, src in ((rgb, outs[0]), (rough, outs[0]), (emis, outs[1])):
        mk.link(src, "", mask, "")
    mk.out(m, rgb, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mk.out(m, rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mk.out(m, emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mk.finish(m)
    print(f"material M_KioskLettering: {len(MEL.get_material_expressions(m))} nodes")
    return m


# ---- instances -----------------------------------------------------------------------------------

def _tex(mi, name, path):
    MEL.set_material_instance_texture_parameter_value(mi, name, unreal.load_asset(path))


def build_instances(manifest):
    master = unreal.load_asset(f"{FOLDER}/M_KioskGraphic")
    mis = {}
    for slot, (atlas, look) in LOOK["slots"].items():
        p = dict(LOOK["paper"])
        p.update(look)
        scal = {k: v for k, v in p.items() if not isinstance(v, (tuple, list))}
        vec = dict(LOOK["colors"])
        vec.update({k: v for k, v in p.items() if isinstance(v, (tuple, list))})
        if slot == "KG_SignFrame":  # metre-scale UV0 tiled inside the painted-steel cell
            u0, v0, u1, v1 = manifest["items"]["frame_steel"]["uv"]
            mi = mk.instance(INST, f"MI_{slot}", master, scal, {k: v for k, v in vec.items() if k != "Cell"})
            MEL.set_material_instance_vector_parameter_value(mi, "Cell", unreal.LinearColor(u0, v0, u1 - u0, v1 - v0))
        else:
            mi = mk.instance(INST, f"MI_{slot}", master, scal, vec)
        for mp, param in (("C", "Color"), ("N", "Normal"), ("S", "Mask")):
            _tex(mi, param, f"{TEX}/T_KG_{atlas}_{mp}")
        MEL.update_material_instance(mi)
        EAL.save_loaded_asset(mi)
        mis[slot] = mi
    ink = mk.instance(INST, "MI_KG_LanternInk", unreal.load_asset(f"{KIOSK_MATS}/Sign_Text_Black"), {}, {})
    MEL.set_material_instance_vector_parameter_value(ink, "BaseColorFactor", unreal.LinearColor(*LOOK["lantern_ink"], 1.0))
    MEL.set_material_instance_scalar_parameter_value(ink, "RoughnessFactor", 0.65)
    MEL.update_material_instance(ink)
    EAL.save_loaded_asset(ink)
    mis["KG_LanternInk"] = ink
    print(f"instances: {len(mis)}")
    return mis


def decal_instances(manifest):
    master = unreal.load_asset(f"{FOLDER}/M_KioskDecal")
    out = {}
    for name, it in manifest["items"].items():
        if it["atlas"] != "Decals":
            continue
        u0, v0, u1, v1 = it["uv"]
        look = LOOK["decals"].get(name, {})
        mi = mk.instance(f"{INST}/Decals", f"MI_KGD_{name}", master, {"Opacity": look.get("opacity", 1.0)},
                         {"Tint": look.get("tint", (1, 1, 1))})
        MEL.set_material_instance_vector_parameter_value(mi, "Cell", unreal.LinearColor(u0, v0, u1 - u0, v1 - v0))
        MEL.update_material_instance(mi)
        EAL.save_loaded_asset(mi)
        out[name] = mi
    return out


# ---- placement -----------------------------------------------------------------------------------

def place_meshes(mis):
    for name in ("SM_Kiosk_Graphics", "SM_Kiosk_Signs"):
        mesh = unreal.load_asset(f"{FOLDER}/{GLB}/StaticMeshes/{name}")
        a = dck.get_or_spawn(unreal.StaticMeshActor, name, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0), "Kiosk")
        comp = a.static_mesh_component
        comp.modify()
        if comp.static_mesh != mesh:
            comp.set_static_mesh(mesh)
        comp.set_editor_property("receives_decals", False)
        n = 0
        for i, slot in enumerate(mesh.static_materials):
            s = str(slot.material_slot_name)
            if s in mis:
                comp.set_material(i, mis[s])
                n += 1
            elif EAL.does_asset_exist(f"{KIOSK_MATS}/{s}"):  # sign hardware: the kiosk's own materials
                comp.set_material(i, unreal.load_asset(f"{KIOSK_MATS}/{s}"))
                n += 1
        print(f"{name}: {n}/{len(mesh.static_materials)} slots assigned")


def place_decals(data, dmis):
    folder = "Kiosk/Decals"
    for a in dck.ACTORS.get_all_level_actors():
        if str(a.get_folder_path()) == folder:
            dck.ACTORS.destroy_actor(a)
    order = {k: i for i, k in enumerate(LOOK["decal_order"])}
    for k, d in enumerate(data["decals"]):
        n = unreal.Vector(d["normal"][0], -d["normal"][1], d["normal"][2])
        up = unreal.Vector(d["up"][0], -d["up"][1], d["up"][2])
        rot = unreal.MathLibrary.make_rot_from_xz(n * -1.0, up)
        pos = dck.to_ue(*d["pos"])
        a = dck.ACTORS.spawn_actor_from_class(unreal.DecalActor, pos, rot)
        a.set_actor_label(f"D_KG_{k:02d}_{d['item']}")
        a.set_folder_path(folder)
        c = a.get_editor_property("decal")
        c.set_decal_material(dmis[d["item"]])
        c.set_editor_property("decal_size", unreal.Vector(d["thickness"] * 50.0, d["size"][0] * 50.0, d["size"][1] * 50.0))
        c.set_editor_property("sort_order", order.get(d["item"], 0))
        c.set_editor_property("fade_screen_size", 0.0)
    print(f"decals: {len(data['decals'])}")


def lettering(data):
    f = data["fascia_uv1"]
    mi = mk.instance(INST, "MI_KG_Lettering", unreal.load_asset(f"{FOLDER}/M_KioskLettering"),
                     {k: v for k, v in LOOK["lettering"].items() if not isinstance(v, (tuple, list))},
                     {k: v for k, v in LOOK["lettering"].items() if isinstance(v, (tuple, list))})
    for side, key in (("front", "F"), ("left", "L")):
        if side not in f:
            raise RuntimeError(f"kiosk_decals.json has no fascia WeatherUV fit for the {side} face: re-run Blender build_graphics.py")
        rows = f[side]["uv"]
        for r, row in enumerate(rows):
            MEL.set_material_instance_vector_parameter_value(mi, f"{key}{r}", unreal.LinearColor(row[0], row[1], row[2], 0.0))
    MEL.update_material_instance(mi)
    EAL.save_loaded_asset(mi)
    a = dck.find_actor("SM_Kiosk_Canopy")
    comp = a.static_mesh_component
    a.modify()
    comp.modify()
    for i, slot in enumerate(comp.static_mesh.static_materials):
        if str(slot.material_slot_name) == "Sign_Text_Black":
            comp.set_material(i, mi if LOOK["lettering_on"] else slot.material_interface)
    print(f"fascia lettering: {'aged' if LOOK['lettering_on'] else 'clean'} (fit error front {f['front']['max_err']:.1e}, "
          f"left {f['left']['max_err']:.1e})")


def sign_light(data):
    s = data["sign_24h"]
    pos = [c + n * 0.16 for c, n in zip(s["centre"], s["normal"])]
    a = dck.find_actor("L_Lantern_R")
    if a is None:
        print("  (no L_Lantern_R)")
        return
    a.modify()
    a.set_actor_location(dck.to_ue(*pos), False, False)
    c = a.get_component_by_class(unreal.PointLightComponent)
    c.modify()
    c.set_editor_property("source_radius", 10.0)
    c.set_intensity(S.SIGN_24H_LIGHT["intensity_cd"] * S.LIGHT_SCALE)
    c.set_editor_property("temperature", S.SIGN_24H_LIGHT["temperature"])
    print(f"L_Lantern_R -> the 24h sign ({S.SIGN_24H_LIGHT['intensity_cd']} cd)")


def apply():
    manifest = json.load(open(os.path.join(RAW_G, "graphics_manifest.json"), encoding="utf-8"))
    data = json.load(open(os.path.join(RAW_G, "kiosk_decals.json"), encoding="utf-8"))
    mis = build_instances(manifest)
    place_meshes(mis)
    place_decals(data, decal_instances(manifest))
    lettering(data)
    sign_light(data)
    dck.LEVELS.save_current_level()


if __name__ == "__main__":
    args = sys.argv[1:]
    dck.ensure_map()
    if "--apply" not in args:
        import_textures()
        import_meshes()
        build_card_material()
        build_decal_material()
        build_letter_material()
    apply()
    print("kiosk_graphics: done")
