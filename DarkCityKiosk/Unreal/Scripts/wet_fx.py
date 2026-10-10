"""Rain contact pass (2026-10-09, prompt 9): water and steam on the finished kiosk, in Unreal.

Blender decides WHERE (Blender/scripts/build_rain_contact.py -> RawContent/rain/T_RainContact.png, the platform's
top-down wet map, and rain/rain_contact.json: drip sources and landing spots, downpipe mouths, steam sources, all
ray-cast against the kiosk and its props). This script decides HOW it looks and moves (scene_config.WET_FX):
  1. MPC_WetFX: the loop clock (LoopTime, keyed 0 -> loop length over LS_Sweep by make_sweep.py; LoopLength) and the
     master amounts WaterAmount / SteamAmount. Every effect below completes whole cycles per loop, so the last frame
     leads into the first exactly;
  2. the platform's wet layer: M_KioskWeathered's UseRainContact branch, switched on for MI_KW_Platform_Concrete only
     (damp darkening, standing water, contact darkening, concrete detail, loop-clock raindrop rings where rain lands,
     rings where each canopy drip lands, wet streaks down the slab's sides);
  3. M_FX_Water: canopy drips (a falling streak as long as half a frame's travel, the next drop swelling at the
     source, a few droplets thrown up where it lands) and the downpipe trickles, on camera-facing strips;
  4. M_FX_Steam: the stock pot's wisp and the roof exhaust fan's plume, on camera-facing cards, scrolling noise lit
     by the scene's own lights (translucency volume), soft where they meet geometry;
  5. the actors (outliner Kiosk/WetFX/Water, Kiosk/WetFX/Steam).

    node Scripts/ue.mjs Scripts/wet_fx.py                       # everything (rebuilds M_KioskWeathered if it lacks the branch)
    node Scripts/ue.mjs Scripts/wet_fx.py --rebuild             # also rebuild M_KioskWeathered (after a wetfx_hlsl.py change)
    node Scripts/ue.mjs Scripts/wet_fx.py --apply               # numbers only: instances, placements, MPC
    node Scripts/ue.mjs Scripts/wet_fx.py --water off|on        # drips + trickles (review water and steam separately)
    node Scripts/ue.mjs Scripts/wet_fx.py --steam off|on
    node Scripts/ue.mjs Scripts/wet_fx.py --contact off|on      # the platform's wet layer (off = the slab as before)
After: make_sweep.py (keys the loop clock), make_review.py. ground.py puts the street puddles' rings on the clock.
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
import wetfx_hlsl as W  # noqa: E402

dck, mk, S, W = importlib.reload(dck), importlib.reload(mk), importlib.reload(S), importlib.reload(W)
import unreal  # noqa: E402

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
FOLDER = f"{dck.GAME}/WetFX"
INST = f"{FOLDER}/Instances"
QUAD = f"{FOLDER}/SM_FX_Quad"
RAW_R = os.path.join(dck.RAW, "rain")
FX = S.WET_FX
PLATFORM_MI = f"{dck.GAME}/Kiosk/Weather/Instances/MI_KW_Platform_Concrete"
WATER_FOLDER, STEAM_FOLDER = "Kiosk/WetFX/Water", "Kiosk/WetFX/Steam"


def data():
    return json.load(open(os.path.join(RAW_R, "rain_contact.json"), encoding="utf-8"))


# ---- assets --------------------------------------------------------------------------------------------------

def import_map():
    mk.ensure_dir(f"{FOLDER}/Textures")
    t = dck.setp(unreal.AssetImportTask(), filename=os.path.join(RAW_R, "T_RainContact.png"), destination_path=f"{FOLDER}/Textures",
                 destination_name="T_RainContact", automated=True, replace_existing=True, save=False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t])
    tex = unreal.load_asset(W.RAIN_MAP)
    tex.modify()
    mk.setp(tex, srgb=False, compression_settings=unreal.TextureCompressionSettings.TC_BC7,
            lod_group=unreal.TextureGroup.TEXTUREGROUP_WORLD, address_x=unreal.TextureAddress.TA_CLAMP,
            address_y=unreal.TextureAddress.TA_CLAMP, never_stream=True)
    EAL.save_loaded_asset(tex)
    print(f"texture T_RainContact: {tex.blueprint_get_size_x()}x{tex.blueprint_get_size_y()}")


def quad_mesh():
    """The engine's 1 m plane (local X across, Y along, pivot at its centre), with its bounds pushed out of plane:
    the materials turn it to the camera, and an infinitely thin box would be culled at the frame edges."""
    if not EAL.does_asset_exist(QUAD):
        EAL.duplicate_asset("/Engine/BasicShapes/Plane", QUAD)
    sm = unreal.load_asset(QUAD)
    sm.modify()
    sm.set_editor_property("positive_bounds_extension", unreal.Vector(0.0, 0.0, 60.0))
    sm.set_editor_property("negative_bounds_extension", unreal.Vector(0.0, 0.0, 60.0))
    EAL.save_loaded_asset(sm)
    return sm


def frame_nodes(m, x, y):
    """LocalPosition (cm, without shader offsets), the local X / Y axes in world space, camera minus object."""
    lp = mk.expr(m, unreal.MaterialExpressionLocalPosition, x, y, included_offsets=unreal.PositionIncludedOffsets.EXCLUDE_OFFSETS)
    axes = []
    for k, v in enumerate(((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))):
        c = mk.expr(m, unreal.MaterialExpressionConstant3Vector, x, y + 100 + k * 150, constant=unreal.LinearColor(v[0], v[1], v[2], 0.0))
        t = mk.expr(m, unreal.MaterialExpressionTransform, x + 200, y + 100 + k * 150,
                    transform_source_type=unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL,
                    transform_type=unreal.MaterialVectorCoordTransform.TRANSFORM_WORLD)
        mk.link(c, "", t, "")
        axes.append(t)
    cam = mk.expr(m, unreal.MaterialExpressionCameraPositionWS, x, y + 420)
    obj = mk.expr(m, unreal.MaterialExpressionObjectPositionWS, x, y + 480)
    sub = mk.expr(m, unreal.MaterialExpressionSubtract, x + 200, y + 440)
    mk.link(cam, "", sub, "A")
    mk.link(obj, "", sub, "B")
    cd = sub
    if hasattr(unreal, "MaterialExpressionTruncateLWC"):
        cd = mk.expr(m, unreal.MaterialExpressionTruncateLWC, x + 350, y + 440)
        mk.link(sub, "", cd, "")
    return lp, axes[0], axes[1], cd


def billboard(m, lp, ax, ay, cd, x, y, wind=(0.0, 0.0), lean=0.0):
    c = mk.custom(m, W.BILLBOARD_HLSL, ["LP", "AX", "AY", "CD", "Wind", "Lean"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, x, y,
                  "Turn to the camera about the axis")
    for n, node in (("LP", lp), ("AX", ax), ("AY", ay), ("CD", cd)):
        mk.link(node, "", c, n)
    mk.link(mk.expr(m, unreal.MaterialExpressionConstant2Vector, x - 200, y + 300, r=wind[0], g=wind[1]), "", c, "Wind")
    mk.link(mk.scalar(m, "Lean", lean, x - 200, y + 360), "", c, "Lean")
    return c


WATER_PRELUDE = r"""
float W = length(AX);
float H = length(AY);
float X = LP.x / 100.0 * W;
float Y = (0.5 - LP.y / 100.0) * H;
#if PIXELSHADER
float px = fwidth(X);
#else
float px = 0.002;
#endif
"""
WATER_SCALARS = ["Mode", "Period", "Skip", "Seed", "Size", "Streak", "SplashDur", "SplashV", "Grow", "Flow"]


def water_material():
    m = mk.material(FOLDER, "M_FX_Water")
    # lit per pixel by the scene's lights, with a rounded normal across the streak: a drop picks up a thin glint from
    # the soffit tubes and the canopy spill as it falls past them, and no glow of its own
    mk.setp(m, blend_mode=unreal.BlendMode.BLEND_TRANSLUCENT, two_sided=True, tangent_space_normal=False,
            translucency_lighting_mode=unreal.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
    lp, ax, ay, cd = frame_nodes(m, -2400, 600)
    look = FX["drip_look"]
    names = ["LP", "AX", "AY", "Time", "Len"] + WATER_SCALARS  # the fall height is the strip length (H)
    c = mk.custom(m, WATER_PRELUDE + W.WATER_HLSL.replace("float t = Time;", "float t = Time;\nfloat Fall = H;", 1), names,
                  unreal.CustomMaterialOutputType.CMOT_FLOAT2, -1200, -200, "Drips and trickles")
    for n, node in (("LP", lp), ("AX", ax), ("AY", ay)):
        mk.link(node, "", c, n)
    mk.link(W.mpc_param(m, "LoopTime", -1500, -400), "", c, "Time")
    mk.link(W.mpc_param(m, "LoopLength", -1500, -340), "", c, "Len")
    defaults = {"Mode": 0.0, "Period": 2.0, "Skip": 0.3, "Seed": 1.0, "Size": 0.0045, "Streak": look["Streak"],
                "SplashDur": look["SplashDur"], "SplashV": look["SplashV"], "Grow": look["Grow"], "Flow": 0.5}
    for i, n in enumerate(WATER_SCALARS):
        mk.link(mk.scalar(m, n, defaults[n], -1500, -200 + i * 60), "", c, n)
    a_ = mk.expr(m, unreal.MaterialExpressionComponentMask, -1000, -200, r=True, g=False, b=False, a=False)
    un = mk.expr(m, unreal.MaterialExpressionComponentMask, -1000, 300, r=False, g=True, b=False, a=False)
    mk.link(c, "", a_, "")
    mk.link(c, "", un, "")
    wn = mk.custom(m, W.WATER_NORMAL_HLSL, ["AY", "CD", "UN"], unreal.CustomMaterialOutputType.CMOT_FLOAT3, -800, 300, "Rounded normal")
    mk.link(ay, "", wn, "AY")
    mk.link(cd, "", wn, "CD")
    mk.link(un, "", wn, "UN")
    mk.out(m, wn, "", unreal.MaterialProperty.MP_NORMAL)
    op = mk.expr(m, unreal.MaterialExpressionMultiply, -800, -200)
    mk.link(a_, "", op, "A")
    mk.link(mk.scalar(m, "Opacity", look["Opacity"], -1000, -100), "", op, "B")
    op2 = mk.expr(m, unreal.MaterialExpressionMultiply, -650, -200)
    mk.link(op, "", op2, "A")
    mk.link(W.mpc_param(m, "WaterAmount", -900, -40), "", op2, "B")
    sat = mk.expr(m, unreal.MaterialExpressionSaturate, -500, -200)
    mk.link(op2, "", sat, "")
    mk.out(m, sat, "", unreal.MaterialProperty.MP_OPACITY)
    mk.out(m, mk.vector(m, "WaterColor", look["WaterColor"], -800, -500), "", unreal.MaterialProperty.MP_BASE_COLOR)
    # refraction pickup: the scene a little above the drop (the fascia it falls from), times Refract
    off = mk.expr(m, unreal.MaterialExpressionMultiply, -1100, -800)
    mk.link(mk.expr(m, unreal.MaterialExpressionConstant2Vector, -1300, -850, r=0.0, g=-1.0), "", off, "A")
    mk.link(mk.scalar(m, "RefractUp", look["RefractUp"], -1300, -760), "", off, "B")
    sc = mk.expr(m, unreal.MaterialExpressionSceneColor, -900, -800, input_mode=unreal.MaterialSceneAttributeInputMode.OFFSET_FRACTION)
    mk.link(off, "", sc, "")
    em = mk.expr(m, unreal.MaterialExpressionMultiply, -700, -800)
    mk.link(sc, "", em, "A")
    mk.link(mk.scalar(m, "Refract", look["Refract"], -900, -700), "", em, "B")
    mk.out(m, em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mk.out(m, mk.scalar(m, "Roughness", look["Roughness"], -800, -400), "", unreal.MaterialProperty.MP_ROUGHNESS)
    mk.out(m, mk.scalar(m, "Specular", look["Specular"], -800, -340), "", unreal.MaterialProperty.MP_SPECULAR)
    mk.out(m, billboard(m, lp, ax, ay, cd, -1200, 600), "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    mk.finish(m)
    return m


STEAM_PRELUDE = r"""
float U = LP.x / 100.0 + 0.5;
float V = LP.y / 100.0 + 0.5;
"""
STEAM_SCALARS = ["Rise", "Sway", "SwayAmp", "Base", "Thresh", "Seed", "Spread", "Scale", "Breakup", "Soft"]


def steam_material():
    m = mk.material(FOLDER, "M_FX_Steam")
    mk.setp(m, blend_mode=unreal.BlendMode.BLEND_TRANSLUCENT, two_sided=True,
            translucency_lighting_mode=unreal.TranslucencyLightingMode.TLM_VOLUMETRIC_NON_DIRECTIONAL)
    lp, ax, ay, cd = frame_nodes(m, -2400, 600)
    names = ["LP", "AX", "AY", "Time", "Len", "Noise"] + STEAM_SCALARS
    c = mk.custom(m, STEAM_PRELUDE + W.STEAM_HLSL, names, unreal.CustomMaterialOutputType.CMOT_FLOAT1, -1200, -200, "Steam")
    mk.link(lp, "", c, "LP")
    mk.link(ax, "", c, "AX")  # the card's size in metres (prompt 10: the noise is laid out in metres)
    mk.link(ay, "", c, "AY")
    mk.link(W.mpc_param(m, "LoopTime", -1500, -400), "", c, "Time")
    mk.link(W.mpc_param(m, "LoopLength", -1500, -340), "", c, "Len")
    mk.link(W.texobj(m, W.NOISE_TEX, -1500, -280), "", c, "Noise")
    defaults = {"Rise": 0.3, "Sway": 0.1, "SwayAmp": 0.05, "Base": 0.1, "Thresh": 0.3, "Seed": 0.5, "Spread": 0.15, "Scale": 1.0,
                "Breakup": 0.12, "Soft": 0.3}
    for i, n in enumerate(STEAM_SCALARS):
        mk.link(mk.scalar(m, n, defaults[n], -1500, -200 + i * 60), "", c, n)
    op = mk.expr(m, unreal.MaterialExpressionMultiply, -800, -200)
    mk.link(c, "", op, "A")
    mk.link(mk.scalar(m, "Opacity", 0.2, -1000, -100), "", op, "B")
    op2 = mk.expr(m, unreal.MaterialExpressionMultiply, -650, -200)
    mk.link(op, "", op2, "A")
    mk.link(W.mpc_param(m, "SteamAmount", -900, -40), "", op2, "B")
    fade = mk.expr(m, unreal.MaterialExpressionDepthFade, -450, -200)  # soft where the card meets the pot, the dome, the hood
    mk.link(op2, "", fade, "Opacity")
    mk.link(mk.scalar(m, "Fade", 8.0, -650, -60), "", fade, "FadeDistance")
    sat = mk.expr(m, unreal.MaterialExpressionSaturate, -300, -200)
    mk.link(fade, "", sat, "")
    mk.out(m, sat, "", unreal.MaterialProperty.MP_OPACITY)
    look = FX["steam_look"]
    mk.out(m, mk.vector(m, "SteamColor", look["SteamColor"], -800, -500), "", unreal.MaterialProperty.MP_BASE_COLOR)
    # in-scattered ambient light (translucent emissive is weighted by the opacity, so it follows the density)
    mk.out(m, mk.vector(m, "Ambient", look["Ambient"], -800, -700), "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mk.out(m, billboard(m, lp, ax, ay, cd, -1200, 600, wind=look["wind"], lean=0.0), "", unreal.MaterialProperty.MP_WORLD_POSITION_OFFSET)
    mk.finish(m)
    return m


# ---- instances and actors ------------------------------------------------------------------------------------

def place(label, folder, mi, loc, rot, scale):
    a = dck.get_or_spawn(unreal.StaticMeshActor, label, loc, rot, folder=folder)
    a.set_actor_scale3d(scale)
    comp = a.static_mesh_component
    comp.modify()
    comp.set_static_mesh(unreal.load_asset(QUAD))
    comp.set_material(0, mi)
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    for prop, v in (("cast_shadow", False), ("visible_in_ray_tracing", False), ("affect_distance_field_lighting", False),
                    ("affect_dynamic_indirect_lighting", False), ("bounds_scale", 2.0)):
        try:
            comp.set_editor_property(prop, v)
        except Exception as e:  # noqa: BLE001
            print(f"  (skip {prop}: {str(e).splitlines()[0][:80]})")
    return a


def axis_rot(up, side=None):
    """Rotation whose local Y is `up` (the strip's / card's axis) and local X horizontal."""
    up = up.normal()
    if side is None:
        side = unreal.Vector(1.0, 0.0, 0.0) if abs(up.z) > 0.95 else unreal.Vector(up.y, -up.x, 0.0).normal()
    return unreal.MathLibrary.make_rot_from_yx(up, side)


def water(d):
    m = unreal.load_asset(f"{FOLDER}/M_FX_Water")
    look, tl = FX["drip_look"], FX["trickle_look"]
    placed = []
    for name, p in FX["drips"].items():
        r = d["drips"][name]
        (x, y, zs), zl = r["src"], r["land"][2]
        fall = zs - zl
        mi = mk.instance(INST, f"MI_FX_Drip_{name}", m, {"Mode": 0.0, "Period": p["period"], "Skip": p["skip"], "Seed": p["seed"], "Size": p["size"],
                                                           "Streak": look["Streak"], "SplashDur": look["SplashDur"], "SplashV": look["SplashV"],
                                                           "Grow": look["Grow"], "Opacity": look["Opacity"],
                                                           "Refract": look["Refract"], "RefractUp": look["RefractUp"]})
        place(f"FX_Drip_{name}", WATER_FOLDER, mi, dck.to_ue(x, y, (zs + zl) / 2.0), axis_rot(unreal.Vector(0, 0, 1)),
              unreal.Vector(look["width_m"], fall, 1.0))
        placed.append(name)
    for name, p in FX["trickles"].items():
        o = d["outlets"][name]
        a, b = dck.to_ue(*o["mouth"]), dck.to_ue(*o["land"])
        up = a - b
        length = up.length() / 100.0
        mi = mk.instance(INST, f"MI_FX_Trickle_{name}", m, {"Mode": 1.0, "Flow": p["flow"], "Skip": p["skip"], "Seed": p["seed"], "Size": p["size"],
                                                              "Streak": tl["Streak"], "SplashDur": tl["SplashDur"], "SplashV": tl["SplashV"],
                                                              "Opacity": look["Opacity"], "Refract": tl["Refract"], "RefractUp": 0.02})
        place(f"FX_Trickle_{name}", WATER_FOLDER, mi, (a + b) * 0.5, axis_rot(up), unreal.Vector(tl["width_m"], length, 1.0))
        placed.append(name)
    print(f"water: {len(FX['drips'])} drips, {len(FX['trickles'])} trickles")


def steam(d):
    m = unreal.load_asset(f"{FOLDER}/M_FX_Steam")
    for name, s in FX["steam"].items():
        src = d["steam"][name]
        x, y = src["xy"]
        z0 = src["z"]
        for k, card in enumerate(s["cards"]):
            scal = {n: s[n] for n in ("Opacity", "Rise", "Sway", "SwayAmp", "Base", "Thresh", "Lean", "Fade", "Spread", "Scale", "Breakup", "Soft")}
            scal["Seed"] = card["seed"]
            mi = mk.instance(INST, f"MI_FX_Steam_{name}_{k}", m, scal, {"Ambient": s.get("Ambient", (0.0, 0.0, 0.0))})
            dx = card.get("dx", 0.0)
            loc = dck.to_ue(x + dx, y + dx * 0.5, z0 + card["h"] / 2.0)
            place(f"FX_Steam_{name}_{k}", STEAM_FOLDER, mi, loc, axis_rot(unreal.Vector(0, 0, 1)), unreal.Vector(card["w"], card["h"], 1.0))
    print(f"steam: {sum(len(s['cards']) for s in FX['steam'].values())} cards")


def platform(d, on=True):
    """M_KioskWeathered's rain-contact branch on the platform's instance; the drips' landing spots and timing."""
    mi = unreal.load_asset(PLATFORM_MI)
    if mi is None:
        print(f"  !! no {PLATFORM_MI} (run kiosk_weather.py)")
        return
    names = [str(n) for n in MEL.get_static_switch_parameter_names(mi.get_editor_property("parent"))]
    if "UseRainContact" not in names or "--rebuild" in sys.argv:
        import kiosk_weather as KW
        importlib.reload(KW)
        print("rebuilding M_KioskWeathered (rain-contact branch)")
        KW.build_material()
        KW.build_instances()
        mi = unreal.load_asset(PLATFORM_MI)
    MEL.set_material_instance_static_switch_parameter_value(mi, "UseRainContact", bool(on))
    c = dict(FX["contact"])
    c["MapHalf"] = d["map"]["half_m"]
    for k, v in c.items():
        MEL.set_material_instance_scalar_parameter_value(mi, k, float(v))
    for i, (name, p) in enumerate(list(FX["drips"].items())[:5]):
        r = d["drips"][name]
        spot = dck.to_ue(r["land"][0], r["land"][1], r["land"][2])
        MEL.set_material_instance_vector_parameter_value(mi, f"DripSpot{i}", unreal.LinearColor(spot.x, spot.y, p["period"], p["skip"]))
        MEL.set_material_instance_vector_parameter_value(mi, f"DripInfo{i}", unreal.LinearColor(p["seed"], r["fall_m"], 0.0, 0.0))
    MEL.update_material_instance(mi)
    EAL.save_loaded_asset(mi)
    print(f"platform wet layer {'on' if on else 'off'} ({PLATFORM_MI.rsplit('/', 1)[1]})")


def show(prefix, on):
    n = 0
    for a in dck.ACTORS.get_all_level_actors():
        if a.get_actor_label().startswith(prefix):
            a.modify()
            a.set_actor_hidden_in_game(not on)
            a.set_is_temporarily_hidden_in_editor(not on)
            n += 1
    return n


def loop_clock():
    W.collection()
    W.set_mpc_default("LoopLength", S.SWEEP["seconds"])


if __name__ == "__main__":
    args = sys.argv[1:]
    dck.ensure_map()

    def flag(name):
        return args[args.index(name) + 1] if name in args else None
    toggles = {k: flag(f"--{k}") for k in ("water", "steam", "contact")}
    if any(toggles.values()):
        if toggles["water"]:
            on = toggles["water"] == "on"
            W.set_mpc_default("WaterAmount", 1.0 if on else 0.0)
            print(f"water {toggles['water']}: {show('FX_Drip_', on) + show('FX_Trickle_', on)} actors")
        if toggles["steam"]:
            on = toggles["steam"] == "on"
            W.set_mpc_default("SteamAmount", 1.0 if on else 0.0)
            print(f"steam {toggles['steam']}: {show('FX_Steam_', on)} actors")
        if toggles["contact"]:
            platform(data(), toggles["contact"] == "on")
    else:
        d = data()
        loop_clock()
        if "--apply" not in args:
            import_map()
            quad_mesh()
            water_material()
            steam_material()
        platform(d)
        water(d)
        steam(d)
    dck.LEVELS.save_current_level()
    print("wet_fx: done")
