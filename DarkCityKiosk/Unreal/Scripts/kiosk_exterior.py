"""Exterior pass (2026-10-09, prompt 8): the ground props round the kiosk's footprint, in Unreal.

Blender builds them on their own (Blender/scripts/build_exterior.py + kiosk/exterior.py -> RawContent/
kiosk_exterior.glb + exterior/exterior.json), so the kiosk export and its weathering bake are untouched.
This script:
  1. trims the old step-3 ground props (the slatted crates, the green cabinet, the red crate, both bins, the
     utility cabinet, the lantern's box pedestal, the flattened cartons, the junction box's floor cable) out
     of a COPY of SM_Kiosk_Props (GeometryScript; rules in exterior.json "trim") and puts it on that actor;
     the railing, the stools, the lantern, both poles and the electrical cluster stay as they were;
  2. imports kiosk_exterior.glb (SM_Kiosk_Exterior, SM_Kiosk_ExteriorCards, the SM_XP_* prototypes) and the
     Exterior atlas (T_KG_Exterior_C/N/S, for MI_KG_Exterior on the shared M_KioskGraphic);
  3. builds M_Exterior (one master: base colour / roughness / metal per instance; grime from the baked
     occlusion and cavity, oxidation in seams, rubbed or chipped edges, sun fade, smudges and scratches
     from the kitchen's tiling detail map; a splash band of dried mud above the slab; and rain exposure
     from world position: wet and glossy outside the canopy's footprint, wind-driven rain a little way under
     its edges, dry tops under it) and MI_KX_<material> from EXTERIOR_LOOK;
  4. places SM_Kiosk_Exterior, SM_Kiosk_ExteriorCards and SM_Kiosk_ExteriorProps (one instanced-mesh
     component per prototype: crates, tote, bottle crate, bottles, gas cylinders).

    node Scripts/ue.mjs Scripts/kiosk_exterior.py            # everything
    node Scripts/ue.mjs Scripts/kiosk_exterior.py --apply    # numbers only: instances' parameters, placements
    node Scripts/ue.mjs Scripts/kiosk_exterior.py --off      # A/B: the old ground props back, the new ones hidden
Tunables: scene_config.EXTERIOR_LOOK (and GRAPHICS_LOOK "KG_Exterior" for the printed marks).
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

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
GA = unreal.GeometryScript_AssetUtils
SEL = unreal.GeometryScript_MeshSelection
ED = unreal.GeometryScript_MeshEdits
FOLDER = f"{dck.GAME}/Kiosk/Exterior"
GLB = "kiosk_exterior"
MESHES = f"{FOLDER}/{GLB}/StaticMeshes"
INST = f"{FOLDER}/Instances"
RAW_X = os.path.join(dck.RAW, "exterior")
RAW_G = os.path.join(dck.RAW, "graphics")
DETAIL = f"{dck.GAME}/Kiosk/Kitchen/Textures/T_KitchenDetail"  # the kitchen pass's tiling detail map
GTEX = f"{dck.GAME}/Kiosk/Graphics/Textures"
GINST = f"{dck.GAME}/Kiosk/Graphics/Instances"
LOOK = S.EXTERIOR_LOOK
UNIQUE = ("SM_Kiosk_Exterior", "SM_Kiosk_ExteriorCards")
PROPS_ACTOR = "SM_Kiosk_ExteriorProps"
ACTOR_FOLDER = "Kiosk/Exterior"


def data():
    return json.load(open(os.path.join(RAW_X, "exterior.json"), encoding="utf-8"))


def ue_box(lo, hi):
    b = unreal.Box()
    b.min = unreal.Vector(lo[0] * 100.0, -hi[1] * 100.0, lo[2] * 100.0)
    b.max = unreal.Vector(hi[0] * 100.0, -lo[1] * 100.0, hi[2] * 100.0)
    b.is_valid = True
    return b


def src_mesh(name):
    return f"{dck.KIOSK_MESHES}/{dck.KIOSK_GLB}/StaticMeshes/{name}"


# ---- 1. trim the old ground props out of a copy of SM_Kiosk_Props --------------------------------------

def trim(rules):
    mk.ensure_dir(f"{FOLDER}/Trim")
    out = {}
    for name, rule in rules.items():
        dst_path = f"{FOLDER}/Trim/{name}_X"
        src = unreal.load_asset(src_mesh(name))
        if not EAL.does_asset_exist(dst_path):
            EAL.duplicate_asset(src_mesh(name), dst_path)
        dst = unreal.load_asset(dst_path)
        dst.set_editor_property("static_materials", src.static_materials)
        _, _, slot_names, _ = GA.get_section_material_list_from_static_mesh(src, unreal.GeometryScriptMeshReadLOD())
        sec = {}
        for i, n in enumerate(slot_names):
            sec.setdefault(str(n), []).append(i)
        dm, _ = GA.copy_mesh_from_static_mesh(src, unreal.DynamicMesh(), unreal.GeometryScriptCopyMeshFromAssetOptions(),
                                             unreal.GeometryScriptMeshReadLOD())
        n0 = dm.get_triangle_count()
        sels = []
        for mname in rule.get("materials", []):
            for sid in sec.get(mname, []):
                _, s = SEL.select_mesh_elements_by_material_id(dm, sid)
                sels.append(s)
        for lo, hi in rule.get("boxes", []):
            _, s = SEL.select_mesh_elements_in_box(dm, ue_box(lo, hi), min_num_triangle_points=3)
            sels.append(s)
        for mname, (lo, hi) in rule.get("materials_in_box", []):
            if mname not in sec:
                print(f"  !! {name}: no slot {mname}")
            for sid in sec.get(mname, []):
                _, a = SEL.select_mesh_elements_by_material_id(dm, sid)
                _, b = SEL.select_mesh_elements_in_box(dm, ue_box(lo, hi), min_num_triangle_points=3)
                sels.append(SEL.combine_mesh_selections(a, b, unreal.GeometryScriptCombineSelectionMode.INTERSECTION))
        sel = sels[0]
        for s in sels[1:]:
            sel = SEL.combine_mesh_selections(sel, s, unreal.GeometryScriptCombineSelectionMode.ADD)
        _, deleted = ED.delete_selected_triangles_from_mesh(dm, sel)
        opts = unreal.GeometryScriptCopyMeshToAssetOptions()
        mk.setp(opts, enable_recompute_normals=False, enable_recompute_tangents=False, enable_remove_degenerates=False,
                replace_materials=False, generate_lightmap_u_vs=False, emit_transaction=False)
        GA.copy_mesh_to_static_mesh(dm, dst, opts, unreal.GeometryScriptMeshWriteLOD(), use_section_materials=True)
        EAL.save_loaded_asset(dst)
        out[name] = dst
        print(f"trim {name}: {deleted}/{n0} triangles removed -> {dst_path}")
    return out


def use_trimmed(names, on=True):
    for name in names:
        a = dck.find_actor(name)
        if a is None:
            print(f"  !! no actor {name}")
            continue
        comp = a.static_mesh_component
        a.modify()
        comp.modify()
        mesh = unreal.load_asset(f"{FOLDER}/Trim/{name}_X" if on else src_mesh(name))
        if comp.static_mesh != mesh:
            comp.set_static_mesh(mesh)


# ---- 2. import -----------------------------------------------------------------------------------------

def import_all():
    mk.ensure_dir(GTEX)
    tasks = [dck.setp(unreal.AssetImportTask(), filename=os.path.join(RAW_G, f"T_KG_Exterior_{mp}.png"), destination_path=GTEX,
                      destination_name=f"T_KG_Exterior_{mp}", automated=True, replace_existing=True, save=False) for mp in ("C", "N", "S")]
    tasks.append(dck.setp(unreal.AssetImportTask(), filename=os.path.join(dck.RAW, f"{GLB}.glb"), destination_path=FOLDER,
                          automated=True, replace_existing=True, save=True))
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    TC = unreal.TextureCompressionSettings
    for mp, srgb, comp in (("C", True, TC.TC_BC7), ("N", False, TC.TC_NORMALMAP), ("S", False, TC.TC_BC7)):  # as kiosk_graphics.py
        t = unreal.load_asset(f"{GTEX}/T_KG_Exterior_{mp}")
        t.modify()
        mk.setp(t, srgb=srgb, compression_settings=comp, lod_group=unreal.TextureGroup.TEXTUREGROUP_WORLD, never_stream=True)
        EAL.save_loaded_asset(t)
    sml = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    meshes = {str(a.asset_name): unreal.load_asset(str(a.package_name)) for a in reg.get_assets_by_path(MESHES, recursive=True)
              if str(a.asset_class_path.asset_name) == "StaticMesh"}
    for name, mesh in meshes.items():
        changed = False
        bs = sml.get_lod_build_settings(mesh, 0)
        if bs.get_editor_property("generate_lightmap_u_vs"):
            bs.set_editor_property("generate_lightmap_u_vs", False)
            sml.set_lod_build_settings(mesh, 0, bs)
            changed = True
        ns = mesh.get_editor_property("nanite_settings")
        want = name != "SM_Kiosk_ExteriorCards"  # small masked cards: plain rendering, exact alpha clip
        if ns.enabled != want:
            ns.enabled = want
            sml.set_nanite_settings(mesh, ns, apply_changes=True)
            changed = True
        if changed:
            EAL.save_loaded_asset(mesh)
    print(f"imported: {len(meshes)} meshes ({sum(1 for n in meshes if n.startswith('SM_XP_'))} prototypes)")
    return meshes


# ---- 3. the master material ------------------------------------------------------------------------------

SCALARS = ["Roughness", "Metallic", "EdgeWear", "EdgeRough", "EdgeMetal", "Grime", "AOStart", "Rust", "Smudge", "Scratch", "Fade", "Var",
           "Splash", "SplashH", "Wet", "WetDarken", "Reach", "WetSoft", "CanX0", "CanX1", "CanY0", "CanY1", "CanZ", "PlatZ",
           "EmissiveStrength", "SlabWick", "Beads", "Runoff", "MapHalf"]
COLORS = ["BaseColor", "EdgeColor", "GrimeColor", "RustColor", "FadeColor", "MudColor", "Emissive"]
HLSL = r"""
// VC: baked masks (R convex edges, G occlusion incl. the kiosk and the slab, B cavity). D / D2: the tiling
// detail map at two scales (R scratches / grain, G smudges, B water spots, A grime noise). WP: world
// position (cm), N: world normal, PR: per-instance random (0 off instances).
float edge = VC.r, ao = VC.g, cav = VC.b;
float n1 = D.a, n2 = D2.a;
float3 col = BaseColor * (1.0 + (PR - 0.5) * Var);
// sun fade / chalking: broad patches, more on faces that see the sky
float fd = saturate(Fade * (0.55 + 0.9 * n2) * (0.75 + 0.25 * saturate(N.z + 0.5)));
col = lerp(col, FadeColor, fd);
float r = Roughness + (n2 - 0.5) * 0.08 + fd * 0.12;
float m = Metallic;
// grime where things are occluded (feet, wall sides, inside corners) and in creases
float g = saturate((AOStart - ao) / max(AOStart, 1e-3)) * 0.8 + cav * 0.6;
g = saturate(g * (0.55 + 0.9 * n1)) * Grime;
col = lerp(col, GrimeColor, g * 0.65);
r = lerp(r, 0.85, g * 0.4);
// oxidation in seams and creases and the most sheltered corners: patchy, darker where it is oldest
float rs = saturate((cav * 1.6 + saturate(0.28 - ao) * 1.5) * Rust) * smoothstep(0.45, 0.8, n1 * 0.65 + n2 * 0.55);
col = lerp(col, RustColor * (0.7 + 0.6 * n2), rs);
r = lerp(r, 0.88, rs);
m = lerp(m, 0.0, rs);
// edges: rubbed back (plastics, wood) or chipped to bare metal (paint)
float e = saturate(edge * 1.6) * smoothstep(0.3, 0.7, n1 * 0.8 + edge * 0.5) * EdgeWear;
col = lerp(col, EdgeColor, e);
m = lerp(m, EdgeMetal, e);
r = lerp(r, EdgeRough, e);
// handling: smudges, fine scratches
r = saturate(r + 0.25 * D.g * Smudge);
col *= 1.0 - 0.06 * D.g * Smudge;
float sc = smoothstep(0.55, 0.9, D.r) * Scratch;
col = lerp(col, col * 1.3 + 0.012, sc * 0.45);
r = saturate(r + (D.r - 0.5) * Scratch * 0.15);
// rain: wet outside the canopy's footprint; wind-driven rain reaches a little under its edges, more lower down,
// never onto tops under it
float dx = max(CanX0 - WP.x, WP.x - CanX1);
float dy = max(CanY0 - WP.y, WP.y - CanY1);
float dout = max(dx, dy);
float reach = Reach * max(CanZ - WP.z, 0.0) * (1.0 - saturate(N.z * 1.4));
float wet = saturate((dout + reach) / max(WetSoft, 1.0) + 0.5) * Wet;
// splash band: dried mud specks above the slab, heavier where the rain lands
float zb = WP.z - PlatZ;
float sb = saturate(1.0 - zb / max(SplashH, 1.0));
float spk = saturate(smoothstep(0.40, 0.60, D.b * 0.85 + sb * 0.35 + n2 * 0.1) + sb * sb * 0.45);  // distinct specks, a faint haze at the foot
float sp = saturate(sb * spk * Splash * (0.5 + 0.5 * saturate(wet * 1.5 + 0.2)));
col = lerp(col, MudColor * (0.8 + 0.4 * n1), sp * 0.95);
r = lerp(r, 0.9, sp * 0.7);
// rain contact pass (prompt 9): feet standing in the slab's wet patches wick it up a few cm (the platform's wet map)
float2 pk = float2(WP.x, -WP.y) * 0.01;
float4 mp = Texture2DSample(Map, MapSampler, (pk + MapHalf) / (2.0 * MapHalf));
wet = max(wet, mp.r * saturate(1.0 - (WP.z - PlatZ) / max(SlabWick, 0.1)) * max(Wet, 0.5));
// wet: porous surfaces darken, everything goes glossier
col *= 1.0 - wet * WetDarken;
r *= lerp(1.0, 0.45, wet);
// on wet, exposed surfaces: scattered beads on the tops, narrow runoff paths down the sides (world-mapped)
float bead = smoothstep(0.62, 0.8, D.b) * saturate(N.z * 2.0 - 1.0) * saturate(wet * 1.5 - 0.3) * Beads;
float2 nk = float2(N.x, -N.y);
float along = dot(pk, float2(-nk.y, nk.x));
float rn = Texture2DSample(Noise, NoiseSampler, float2(along * 5.0, WP.z * 0.008)).r;
float run = smoothstep(0.6, 0.82, rn) * (1.0 - abs(N.z)) * saturate(wet * 1.5 - 0.3) * Runoff;
col *= 1.0 - 0.08 * max(bead, run);
r = lerp(r, 0.05, max(bead, run * 0.8));
if (Mode < 0.5) return float4(col, clamp(r, 0.04, 1.0));
return float4(m, Emissive * EmissiveStrength);
"""


def build_material():
    m = mk.material(FOLDER, "M_Exterior")
    mk.setp(m, used_with_instanced_static_meshes=True, used_with_nanite=True)
    X = -2700
    uv0 = mk.expr(m, unreal.MaterialExpressionTextureCoordinate, X, -700, coordinate_index=0)
    lin = unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
    tex = unreal.load_asset(DETAIL)
    samples = []
    for k, (pname, scale) in enumerate((("DetailTile", LOOK["detail_tile"]), ("BroadTile", LOOK["broad_tile"]))):
        tile = mk.scalar(m, pname, scale, X, -600 + k * 300)
        div = mk.expr(m, unreal.MaterialExpressionDivide, X + 300, -700 + k * 300)
        mk.link(uv0, "", div, "A")
        mk.link(tile, "", div, "B")
        t = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, X + 600, -750 + k * 300, parameter_name=f"Detail{k}",
                    texture=tex, sampler_type=lin)
        mk.link(div, "", t, "UVs")
        samples.append(t)
    vc = mk.expr(m, unreal.MaterialExpressionVertexColor, X + 600, -100)
    wp = mk.expr(m, unreal.MaterialExpressionWorldPosition, X + 600, 50)
    if hasattr(unreal, "MaterialExpressionTruncateLWC"):  # LWC world position; we only need centimetres near the origin
        tr = mk.expr(m, unreal.MaterialExpressionTruncateLWC, X + 800, 50)
        mk.link(wp, "", tr, "")
        wp = tr
    nrm = mk.expr(m, unreal.MaterialExpressionVertexNormalWS, X + 600, 150)
    pr = mk.expr(m, unreal.MaterialExpressionPerInstanceRandom, X + 600, 250)
    params = {}
    defaults = dict(LOOK["defaults"])
    defaults.update(canopy_params())
    defaults.update({"SlabWick": 5.0, "Beads": 1.0, "Runoff": 1.0, "MapHalf": 4.096})  # prompt 9 (cm, -, -, m)
    for i, n in enumerate(SCALARS):
        params[n] = mk.scalar(m, n, defaults.get(n, 0.0), X + 1000, 350 + i * 90)
    for i, n in enumerate(COLORS):
        params[n] = mk.vector(m, n, defaults.get(n, (0.5, 0.5, 0.5)), X + 1300, 350 + i * 110)
    names = ["VC", "D", "D2", "WP", "N", "PR", "Mode", "Map", "Noise"] + SCALARS + COLORS
    rain_map = unreal.load_asset(f"{dck.GAME}/WetFX/Textures/T_RainContact")  # wet_fx.py imports it (prompt 9)
    tmap = mk.expr(m, unreal.MaterialExpressionTextureObject, X + 600, 650, texture=rain_map)
    tnoise = mk.expr(m, unreal.MaterialExpressionTextureObject, X + 600, 750, texture=unreal.load_asset("/Game/StarterContent/Textures/T_Perlin_Noise_M"))
    outs = []
    for k, mode in enumerate((0.0, 1.0)):
        c = mk.custom(m, HLSL, names, unreal.CustomMaterialOutputType.CMOT_FLOAT4, -1100, -400 + k * 800,
                      "Exterior surface" + (" (metal, emissive)" if mode else ""))
        mk.link(vc, "", c, "VC")
        mk.link(samples[0], "RGBA", c, "D")
        mk.link(samples[1], "RGBA", c, "D2")
        mk.link(wp, "", c, "WP")
        mk.link(nrm, "", c, "N")
        mk.link(pr, "", c, "PR")
        mk.link(tmap, "", c, "Map")
        mk.link(tnoise, "", c, "Noise")
        mk.link(mk.expr(m, unreal.MaterialExpressionConstant, -1400, -400 + k * 800, r=mode), "", c, "Mode")
        for n, p in params.items():
            mk.link(p, "", c, n)
        outs.append(c)
    rgb = mk.expr(m, unreal.MaterialExpressionComponentMask, -700, -450, r=True, g=True, b=True, a=False)
    rough = mk.expr(m, unreal.MaterialExpressionComponentMask, -700, -300, r=False, g=False, b=False, a=True)
    metal = mk.expr(m, unreal.MaterialExpressionComponentMask, -700, 400, r=True, g=False, b=False, a=False)
    emis = mk.expr(m, unreal.MaterialExpressionComponentMask, -700, 550, r=False, g=True, b=True, a=True)
    for mask, src in ((rgb, outs[0]), (rough, outs[0]), (metal, outs[1]), (emis, outs[1])):
        mk.link(src, "", mask, "")
    mk.out(m, rgb, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mk.out(m, rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mk.out(m, metal, "", unreal.MaterialProperty.MP_METALLIC)
    mk.out(m, emis, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mk.finish(m)
    st = MEL.get_statistics(m)
    print(f"material M_Exterior: {len(MEL.get_material_expressions(m))} nodes, {st.num_pixel_shader_instructions} PS instructions")
    return m


def canopy_params():
    """The canopy's footprint and underside in Unreal centimetres (Blender y flips), the slab's top."""
    x0, x1, y0, y1, zc = dck.K.EXTERIOR["canopy"]
    return {"CanX0": x0 * 100.0, "CanX1": x1 * 100.0, "CanY0": -y1 * 100.0, "CanY1": -y0 * 100.0, "CanZ": zc * 100.0,
            "PlatZ": dck.K.PLATFORM_H * 100.0}


def _lum(c):
    return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]


def look_for(name, base):
    """Parameters for one material: defaults, the category preset, colours derived from the Blender colour
    (rubbed edges, sun-faded tone) unless the preset or the override gives them, then the overrides."""
    cat, over = LOOK["materials"].get(name, ("plastic", {}))
    p = dict(LOOK["defaults"])
    p.update(canopy_params())
    preset = dict(LOOK["categories"][cat])
    rgb, rough, metal, emit = base
    p.update({"BaseColor": tuple(rgb), "Roughness": rough, "Metallic": metal})
    lum = _lum(rgb)
    k = preset.pop("edge_lift", None)
    if k is not None:  # rubbed plastic / wood: lighter, greyer, matte
        p["EdgeColor"] = tuple(min(1.0, (c * 0.5 + lum * 0.5) * k + 0.025) for c in rgb)
    f = preset.pop("fade_to", None)
    if f is not None:  # chalky sun fade: toward a paler grey of the same tone
        p["FadeColor"] = tuple(c * (1 - f) + (lum * 1.35 + 0.035) * f for c in rgb)
    p.update(preset)
    if emit > 0:
        p.update({"Emissive": tuple(rgb), "EmissiveStrength": LOOK["emissive"].get(name, 4.0)})
    p.update(over)
    return p


def build_instances(materials):
    master = unreal.load_asset(f"{FOLDER}/M_Exterior")
    mis = {}
    for name, base in materials.items():
        p = look_for(name, base)
        mis[name] = mk.instance(INST, f"MI_{name}", master, {k: v for k, v in p.items() if not isinstance(v, (tuple, list))},
                                {k: v for k, v in p.items() if isinstance(v, (tuple, list))})
    mis["KG_Exterior"] = card_instance()
    print(f"instances: {len(mis)}")
    return mis


def card_instance():
    """MI_KG_Exterior: the signage pass's card material on the Exterior atlas (as kiosk_graphics.build_instances)."""
    G = S.GRAPHICS_LOOK
    atlas, look = G["slots"]["KG_Exterior"]
    p = dict(G["paper"])
    p.update(look)
    vec = dict(G["colors"])
    vec.update({k: v for k, v in p.items() if isinstance(v, (tuple, list))})
    mi = mk.instance(GINST, "MI_KG_Exterior", unreal.load_asset(f"{dck.GAME}/Kiosk/Graphics/M_KioskGraphic"),
                     {k: v for k, v in p.items() if not isinstance(v, (tuple, list))}, vec)
    for mp, param in (("C", "Color"), ("N", "Normal"), ("S", "Mask")):
        MEL.set_material_instance_texture_parameter_value(mi, param, unreal.load_asset(f"{GTEX}/T_KG_{atlas}_{mp}"))
    MEL.update_material_instance(mi)
    EAL.save_loaded_asset(mi)
    return mi


# ---- 4. actors -----------------------------------------------------------------------------------------

def assign(comp, mesh, mis):
    for i, slot in enumerate(mesh.static_materials):
        s = str(slot.material_slot_name)
        if s in mis:
            comp.set_material(i, mis[s])
        else:
            print(f"  !! {mesh.get_name()}: no instance for slot {s}")


def place(meshes, mis, d):
    for name in UNIQUE:
        a = dck.get_or_spawn(unreal.StaticMeshActor, name, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0), ACTOR_FOLDER)
        comp = a.static_mesh_component
        a.modify()
        comp.modify()
        if comp.static_mesh != meshes[name]:
            comp.set_static_mesh(meshes[name])
        comp.set_editor_property("receives_decals", False)
        assign(comp, meshes[name], mis)
        a.set_actor_hidden_in_game(False)
        a.set_is_temporarily_hidden_in_editor(False)
    old = dck.find_actor(PROPS_ACTOR)
    if old:
        dck.ACTORS.destroy_actor(old)
    actor = dck.ACTORS.spawn_actor_from_class(unreal.Actor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 0, 0))
    actor.set_actor_label(PROPS_ACTOR)
    actor.set_folder_path(ACTOR_FOLDER)
    sds = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
    root = sds.k2_gather_subobject_data_for_instance(actor)[0]
    groups = {}
    for p in d["props"]:
        groups.setdefault(p["name"], []).append(p)
    total = 0
    for name, items in sorted(groups.items()):
        mesh = meshes.get(f"SM_XP_{name}")
        if mesh is None:
            print(f"  !! no prototype SM_XP_{name}")
            continue
        h, _ = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.InstancedStaticMeshComponent,
                                                                  blueprint_context=None))
        sds.rename_subobject(h, unreal.Text(f"XP_{name}"))
        comp = unreal.SubobjectDataBlueprintFunctionLibrary.get_associated_object(unreal.SubobjectDataBlueprintFunctionLibrary.get_data(h))
        comp.set_static_mesh(mesh)
        assign(comp, mesh, mis)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comp.set_editor_property("receives_decals", False)
        xs = [unreal.Transform(location=dck.to_ue(*p["pos"]), rotation=unreal.Rotator(roll=0.0, pitch=0.0, yaw=dck.heading_to_ue_yaw(p["yaw"])),
                               scale=unreal.Vector(p["scale"], p["scale"], p["scale"])) for p in items]
        comp.add_instances(xs, False, True)
        total += len(xs)
    print(f"{PROPS_ACTOR}: {len(groups)} instanced components, {total} instances")


def show(on):
    for name in UNIQUE + (PROPS_ACTOR,):
        a = dck.find_actor(name)
        if a:
            a.set_actor_hidden_in_game(not on)
            a.set_is_temporarily_hidden_in_editor(not on)


def meshes_now():
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    return {str(a.asset_name): unreal.load_asset(str(a.package_name)) for a in reg.get_assets_by_path(MESHES, recursive=True)
            if str(a.asset_class_path.asset_name) == "StaticMesh"}


def apply(full=False):
    d = data()
    if full or not EAL.does_asset_exist(f"{FOLDER}/Trim/SM_Kiosk_Props_X"):
        trim(d["trim"])
    use_trimmed(d["trim"], True)
    mis = build_instances(d["materials"])
    place(meshes_now(), mis, d)
    show(True)
    dck.LEVELS.save_current_level()


if __name__ == "__main__":
    args = sys.argv[1:]
    dck.ensure_map()
    if "--off" in args:
        use_trimmed(data()["trim"], False)
        show(False)
        dck.LEVELS.save_current_level()
        print("kiosk_exterior: off (old ground props back)")
    else:
        if "--apply" not in args:
            import_all()
            build_material()
        apply(full="--apply" not in args)
        print("kiosk_exterior: done")
