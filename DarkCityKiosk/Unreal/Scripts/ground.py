"""Street ground: poured-concrete slabs with joints, damp, with puddles only in the low spots.

The puddle layer is our own (EasyRain's MF_EasyRain_Puddles tiles one puddle texture every
150 m, so around the kiosk it read as a flooded pool). A height mask decides where water
lies: macro + two blurred noise octaves, unevenly settled slabs, the joints, and a dip in the
band just in front of the lens along the orbit, so the kiosk stays mirrored in the foreground
(from 10 cm up it can only be mirrored in water within ~1.5 m of the camera).
Puddles (height < coverage) are dark mirrors with EasyRain's raindrop ripples; a damp band
rings each one; the concrete between them is only slightly wet.

setup_scene.py builds it with the rest of the scene. Run alone to rebuild just the ground:

    node Scripts/ue.mjs Scripts/ground.py
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

MAT = f"{dck.GAME}/Materials"
SC = "/Game/StarterContent/Textures"
ER = "/Game/EasyRain/System/MaterialFunctions"

# -> float4(joint, slab tint, height, puddle)
MASKS_HLSL = """
// joints: distance (cm) to the nearest slab edge
float2 g = P / Slab;
float2 d = abs(frac(g + 0.5) - 0.5) * Slab;
float joint = 1.0 - smoothstep(Joint * 0.5, Joint * 1.5, min(d.x, d.y));
// per-slab tone and settling
float hsh = frac(sin(dot(floor(g), float2(12.9898, 78.233))) * 43758.5453);
float tint = lerp(1.0 - SlabVar, 1.0 + SlabVar, hsh);
// height: high = dry, low = water (each noise averages ~0.5)
float h = 0.45 * Macro + 0.45 * NoiseA + 0.1 * NoiseB + (hsh - 0.5) * 0.08 - joint * JointDip;
// dip in the band just in front of the lens all along the orbit (P in cm, kiosk at the origin):
// from 10 cm up, the kiosk is mirrored only in water within ~1.5 m of the camera
float2 m = P * 0.01;
float r = length(m);
float side = dot(m / max(r, 0.001), FgDir);
h -= FgDip * smoothstep(FgBand.x, FgBand.y, r) * (1.0 - smoothstep(FgBand.z, FgBand.w, r)) * smoothstep(0.35, 0.75, side);
float puddle = smoothstep(Coverage + Edge, Coverage - Edge, h);
return float4(joint, tint, h, puddle);
"""

# -> float4(base colour, roughness)
SURFACE_HLSL = """
float3 c = Concrete * Tint * Masks.y;
c *= lerp(1.0, Grime * 1.6, GrimeAmt);
c *= lerp(0.8, 1.15, Macro);
c *= lerp(1.0, JointDark, Masks.x);
float rough = saturate(lerp(Rough, RoughJoint, Masks.x) + (0.5 - Grime) * 0.25);
// wetness: a little everywhere, fully damp in a band around each puddle
float damp = smoothstep(Coverage + DampBand, Coverage, Masks.z);
float w = saturate(Wetness + damp * (1.0 - Wetness));
c *= 1.0 - Darkening * w;
rough = lerp(rough, WetRough, w);
// puddle: dark, mirror-flat water
c = lerp(c, c * PuddleDark, Masks.w);
rough = lerp(rough, PuddleRough, Masks.w);
return float4(c, rough);
"""


def sample(m, path, uv, x, y, mip=None):
    """Texture sample with the sampler type its compression needs; mip = a fixed (blurred) mip level."""
    tex = unreal.load_asset(path)
    cs = tex.get_editor_property("compression_settings")
    srgb = tex.get_editor_property("srgb")
    st = unreal.MaterialSamplerType
    kind = {unreal.TextureCompressionSettings.TC_NORMALMAP: st.SAMPLERTYPE_NORMAL,
            unreal.TextureCompressionSettings.TC_MASKS: st.SAMPLERTYPE_MASKS,
            unreal.TextureCompressionSettings.TC_GRAYSCALE: st.SAMPLERTYPE_GRAYSCALE if srgb else st.SAMPLERTYPE_LINEAR_GRAYSCALE,
            }.get(cs, st.SAMPLERTYPE_COLOR if srgb else st.SAMPLERTYPE_LINEAR_COLOR)
    s = mk.expr(m, unreal.MaterialExpressionTextureSample, x, y, texture=tex, sampler_type=kind)
    if mip is not None:
        mk.setp(s, mip_value_mode=unreal.TextureMipValueMode.TMVM_MIP_LEVEL, const_mip_value=int(mip))
    mk.link(uv, "", s, "UVs")
    return s


def build():
    g = S.GROUND
    m = mk.material(MAT, "M_Ground_Wet")
    m.set_editor_property("use_material_attributes", False)
    wp = mk.expr(m, unreal.MaterialExpressionWorldPosition, -2800, 0)
    xy = mk.expr(m, unreal.MaterialExpressionComponentMask, -2600, 0, r=True, g=True, b=False, a=False)
    mk.link(wp, "", xy, "")
    if hasattr(unreal, "MaterialExpressionTruncateLWC"):  # world position is LWC; we only need metres near the origin
        tr = mk.expr(m, unreal.MaterialExpressionTruncateLWC, -2450, 0)
        mk.link(xy, "", tr, "")
        xy = tr

    def uv(scale_cm, y):
        d = mk.expr(m, unreal.MaterialExpressionDivide, -2250, y, const_b=float(scale_cm))
        mk.link(xy, "", d, "A")
        return d

    def const(v, x, y):
        return mk.expr(m, unreal.MaterialExpressionConstant, x, y, r=float(v))

    def fn(path, x, y):
        return mk.expr(m, unreal.MaterialExpressionMaterialFunctionCall, x, y, material_function=unreal.load_asset(path))

    concrete = sample(m, f"{SC}/T_Concrete_Poured_D", uv(g["concrete_tile_cm"], -600), -2000, -600)
    concrete_n = sample(m, f"{SC}/T_Concrete_Poured_N", uv(g["concrete_tile_cm"], -400), -2000, -400)
    grime = sample(m, f"{SC}/T_Concrete_Grime_D", uv(g["grime_tile_cm"], -200), -2000, -200)
    # the height noise comes from blurred mips: full-res grain made hundreds of tiny puddles
    macro = sample(m, f"{SC}/T_MacroVariation", uv(g["macro_tile_cm"], 0), -2000, 0, g["macro_mip"])
    noise_a = sample(m, f"{SC}/T_Perlin_Noise_M", uv(g["noise_a_tile_cm"], 200), -2000, 200, g["noise_a_mip"])
    noise_b = sample(m, f"{SC}/T_Perlin_Noise_M", uv(g["noise_b_tile_cm"], 400), -2000, 400, g["noise_b_mip"])
    detail_n = sample(m, f"{SC}/T_Detail_Rocky_N", uv(g["detail_tile_cm"], 600), -2000, 600)

    # masks: joint, slab tint, height, puddle
    hc = dck.K.HERO_CAM["pos_xy"]
    fg = (hc[0], -hc[1])  # toward the camera at the middle of the orbit, Unreal frame
    n = math.hypot(*fg)
    masks = mk.custom(m, MASKS_HLSL, ["P", "Macro", "NoiseA", "NoiseB", "Slab", "Joint", "SlabVar", "JointDip", "FgDir", "FgDip", "FgBand", "Coverage", "Edge"],
                      unreal.CustomMaterialOutputType.CMOT_FLOAT4, -1500, 300, "GroundMasks")
    mk.link(xy, "", masks, "P")
    mk.link(macro, "R", masks, "Macro")
    mk.link(noise_a, "R", masks, "NoiseA")
    mk.link(noise_b, "R", masks, "NoiseB")
    params = {"Slab": g["slab_cm"], "Joint": g["joint_cm"], "SlabVar": g["slab_variation"], "JointDip": g["joint_dip"],
              "FgDip": g["foreground_dip"], "Coverage": g["puddle_coverage"], "Edge": g["puddle_edge"]}
    pnodes = {k: mk.scalar(m, k, v, -1800, 800 + i * 70) for i, (k, v) in enumerate(params.items())}
    for k, node in pnodes.items():
        mk.link(node, "", masks, k)
    fgdir = mk.expr(m, unreal.MaterialExpressionConstant2Vector, -1800, 1350, r=fg[0] / n, g=fg[1] / n)
    mk.link(fgdir, "", masks, "FgDir")
    band = mk.expr(m, unreal.MaterialExpressionConstant4Vector, -1800, 1420, constant=unreal.LinearColor(*g["foreground_band_m"]))
    mk.link(band, "", masks, "FgBand")

    surf = mk.custom(m, SURFACE_HLSL, ["Concrete", "Grime", "Macro", "Masks", "Tint", "GrimeAmt", "JointDark", "Rough", "RoughJoint",
                                       "Coverage", "DampBand", "Wetness", "Darkening", "WetRough", "PuddleDark", "PuddleRough"],
                     unreal.CustomMaterialOutputType.CMOT_FLOAT4, -1100, -300, "GroundSurface")
    mk.link(concrete, "RGB", surf, "Concrete")
    mk.link(grime, "R", surf, "Grime")
    mk.link(macro, "R", surf, "Macro")
    mk.link(masks, "", surf, "Masks")
    mk.link(mk.vector(m, "Tint", g["tint"], -1500, -700), "", surf, "Tint")
    sparams = {"GrimeAmt": g["grime"], "JointDark": g["joint_dark"], "Rough": g["roughness"], "RoughJoint": g["roughness_joint"],
               "DampBand": g["damp_band"], "Wetness": g["wetness"], "Darkening": g["wet_darkening"], "WetRough": g["wet_roughness"],
               "PuddleDark": g["puddle_darkening"], "PuddleRough": g["puddle_roughness"]}
    for i, (k, v) in enumerate(sparams.items()):
        mk.link(mk.scalar(m, k, v, -1500, -1450 + i * 70), "", surf, k)
    mk.link(pnodes["Coverage"], "", surf, "Coverage")
    base = mk.expr(m, unreal.MaterialExpressionComponentMask, -800, -300, r=True, g=True, b=True, a=False)
    mk.link(surf, "", base, "")
    rough = mk.expr(m, unreal.MaterialExpressionComponentMask, -800, -200, r=False, g=False, b=False, a=True)
    mk.link(surf, "", rough, "")

    # concrete normal: big pores (calmed: at grazing angles they read as waves) + fine grit
    flat_a = fn("/Engine/Functions/Engine_MaterialFunctions01/Texturing/FlattenNormal", -1500, -400)
    mk.link(concrete_n, "RGB", flat_a, "Normal")
    mk.link(mk.scalar(m, "NormalFlatness", g["normal_flatness"], -1800, -350), "", flat_a, "Flatness")
    flat_b = fn("/Engine/Functions/Engine_MaterialFunctions01/Texturing/FlattenNormal", -1500, 600)
    mk.link(detail_n, "RGB", flat_b, "Normal")
    mk.link(mk.scalar(m, "DetailFlatness", g["detail_flatness"], -1800, 650), "", flat_b, "Flatness")
    blend = fn("/Engine/Functions/Engine_MaterialFunctions02/Utility/BlendAngleCorrectedNormals", -1100, 300)
    mk.link(flat_a, "", blend, "BaseNormal")
    mk.link(flat_b, "", blend, "AdditionalNormal")

    # puddle normal: EasyRain's raindrop rings plus a breath of wind
    r = g["ripples"]
    rain = fn(f"{ER}/MF_EasyRain_ripplesRain", -1100, 700)
    mk.link(xy, "", rain, "World Position XY")
    for pin, key in (("Speed", "speed"), ("Normal Intensity", "normal"), ("Tiling", "tiling"), ("Intensity", "amount")):
        mk.link(const(r[key], -1300, 700 + len(pin) * 3), "", rain, pin)
    wind = fn(f"{ER}/MF_EasyRain_ripplesWind", -1100, 950)
    mk.link(xy, "", wind, "World Position XY")
    for pin, key in (("Wind Speed", "wind_speed"), ("Normal Intensity", "wind_normal"), ("Tiling", "wind_tiling")):
        mk.link(const(r[key], -1300, 950 + len(pin) * 3), "", wind, pin)
    add = mk.expr(m, unreal.MaterialExpressionAdd, -850, 800)
    mk.link(rain, "Result", add, "A")
    mk.link(wind, "", add, "B")
    rg = mk.expr(m, unreal.MaterialExpressionComponentMask, -700, 800, r=True, g=True, b=False, a=False)
    mk.link(add, "", rg, "")
    pn = mk.expr(m, unreal.MaterialExpressionAppendVector, -550, 800)
    mk.link(rg, "", pn, "A")
    mk.link(const(1.0, -700, 900), "", pn, "B")

    pmask = mk.expr(m, unreal.MaterialExpressionComponentMask, -800, 500, r=False, g=False, b=False, a=True)
    mk.link(masks, "", pmask, "")
    nrm = mk.expr(m, unreal.MaterialExpressionLinearInterpolate, -400, 400)
    mk.link(blend, "", nrm, "A")
    mk.link(pn, "", nrm, "B")
    mk.link(pmask, "", nrm, "Alpha")
    nn = mk.expr(m, unreal.MaterialExpressionNormalize, -250, 400)
    mk.link(nrm, "", nn, "")

    mk.out(m, base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mk.out(m, rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mk.out(m, const(0.5, -400, 150), "", unreal.MaterialProperty.MP_SPECULAR)
    mk.out(m, nn, "", unreal.MaterialProperty.MP_NORMAL)
    mk.finish(m)
    return mk.instance(MAT, "MI_Ground_Wet", m)


if __name__ != "ground":  # run directly (not imported by setup_scene)
    dck.ensure_map()
    mi = build()
    ground = dck.find_actor("Ground")
    if ground:
        ground.static_mesh_component.set_material(0, mi)
    dck.LEVELS.save_current_level()
    st = unreal.MaterialEditingLibrary.get_statistics(unreal.load_asset(f"{MAT}/M_Ground_Wet"))
    print(f"ground: rebuilt M_Ground_Wet / MI_Ground_Wet ({st.num_pixel_shader_instructions} PS instructions, {st.num_samplers} samplers)")
