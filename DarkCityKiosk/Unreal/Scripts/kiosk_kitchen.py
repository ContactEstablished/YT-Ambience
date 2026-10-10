"""Kitchen pass (2026-10-09, prompt 7): the working kitchen behind the service opening, in Unreal.

Blender builds it on its own (Blender/scripts/build_kitchen.py + kiosk/kitchen.py -> RawContent/
kiosk_kitchen.glb + kitchen/kitchen.json), so the kiosk export and its weathering bake are untouched.
This script:
  1. trims the old step-2 interior (stock shelves, coffee machine, pots, condiments, the ticket
     machine, the 0.9 m recess's lining) out of COPIES of SM_Kiosk_ServiceSide and SM_Kiosk_Body
     (GeometryScript; rules in kitchen.json "trim") and puts the copies on those actors. Every kept
     triangle keeps its WeatherUV, so the weathering is exactly as before;
  2. imports kiosk_kitchen.glb (SM_Kiosk_Kitchen, SM_Kiosk_KitchenCounter, SM_Kiosk_KitchenCards and
     the SM_KP_* prototypes) and the wear textures (T_CounterWear, T_KitchenDetail);
  3. builds M_Kitchen (one master: base colour / roughness / metal per instance, worn edges and grime
     from the baked vertex masks, smudges / brushed grain / water spots from a tiling detail map, and
     the customer counter's own wear map through UV1) and MI_KK_<material> from KITCHEN_LOOK;
  4. places the kitchen actors and SM_Kiosk_KitchenProps: one instanced-mesh component per prototype
     (bowls, cups, bottles, tubs, tools...), instances from kitchen.json;
  5. places the kitchen lights (KITCHEN_LIGHTS): the bright prep light at the opening, warm pools under
     the hood, warm shelf strips, the dim rear fill (L_Interior), the terminal's screen glow.
The printed cards use the signage pass's M_KioskGraphic through MI_KG_Kitchen (kiosk_graphics.py builds it
from the Kitchen atlas).

    node Scripts/ue.mjs Scripts/kiosk_kitchen.py            # everything
    node Scripts/ue.mjs Scripts/kiosk_kitchen.py --apply    # numbers: instances' parameters, lights
    node Scripts/ue.mjs Scripts/kiosk_kitchen.py --off      # A/B: the old interior back, kitchen hidden
Tunables: scene_config.KITCHEN_LOOK, KITCHEN_LIGHTS, INTERIOR.
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
FOLDER = f"{dck.GAME}/Kiosk/Kitchen"
GLB = "kiosk_kitchen"
MESHES = f"{FOLDER}/{GLB}/StaticMeshes"
TEX = f"{FOLDER}/Textures"
INST = f"{FOLDER}/Instances"
RAW_K = os.path.join(dck.RAW, "kitchen")
LOOK = S.KITCHEN_LOOK
UNIQUE = ("SM_Kiosk_Kitchen", "SM_Kiosk_KitchenCounter", "SM_Kiosk_KitchenCards")
PROPS_ACTOR = "SM_Kiosk_KitchenProps"
ACTOR_FOLDER = "Kiosk/Kitchen"
LIGHT_FOLDER = "Lights/Kitchen"


def data():
    return json.load(open(os.path.join(RAW_K, "kitchen.json"), encoding="utf-8"))


def ue_box(lo, hi):
    b = unreal.Box()
    b.min = unreal.Vector(lo[0] * 100.0, -hi[1] * 100.0, lo[2] * 100.0)
    b.max = unreal.Vector(hi[0] * 100.0, -lo[1] * 100.0, hi[2] * 100.0)
    b.is_valid = True
    return b


# ---- 1. trim the old interior out of copies of the kiosk meshes ----------------------------------

def trim(rules):
    mk.ensure_dir(f"{FOLDER}/Trim")
    out = {}
    for name, rule in rules.items():
        src_path = f"{dck.KIOSK_MESHES}/{dck.KIOSK_GLB}/StaticMeshes/{name}"
        dst_path = f"{FOLDER}/Trim/{name}_K"
        src = unreal.load_asset(src_path)
        if not EAL.does_asset_exist(dst_path):
            EAL.duplicate_asset(src_path, dst_path)
        dst = unreal.load_asset(dst_path)
        dst.set_editor_property("static_materials", src.static_materials)  # slot order may change on a re-import
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
            for sid in sec.get(mname, []):
                _, a = SEL.select_mesh_elements_by_material_id(dm, sid)
                _, b = SEL.select_mesh_elements_in_box(dm, ue_box(lo, hi), min_num_triangle_points=3)
                sels.append(SEL.combine_mesh_selections(a, b, unreal.GeometryScriptCombineSelectionMode.INTERSECTION))
        if not sels:
            continue
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


def use_trimmed(trimmed, on=True):
    for name, dst in trimmed.items():
        a = dck.find_actor(name)
        if a is None:
            continue
        comp = a.static_mesh_component
        a.modify()
        comp.modify()
        mesh = dst if on else unreal.load_asset(f"{dck.KIOSK_MESHES}/{dck.KIOSK_GLB}/StaticMeshes/{name}")
        if comp.static_mesh != mesh:
            comp.set_static_mesh(mesh)


# ---- 2. import -----------------------------------------------------------------------------------

def import_all(glb=True):
    mk.ensure_dir(TEX)
    tasks = [dck.setp(unreal.AssetImportTask(), filename=os.path.join(RAW_K, f"{n}.png"), destination_path=TEX, destination_name=n,
                      automated=True, replace_existing=True, save=False) for n in ("T_CounterWear", "T_KitchenDetail")]
    if glb:
        tasks.append(dck.setp(unreal.AssetImportTask(), filename=os.path.join(dck.RAW, f"{GLB}.glb"), destination_path=FOLDER,
                              automated=True, replace_existing=True, save=True))
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    texture_settings()
    if not glb:
        return
    mesh_settings()


def import_textures():
    """The wear maps only (prompt 10: after a make_kitchen_textures.py change)."""
    import_all(glb=False)


def texture_settings():
    for n in ("T_CounterWear", "T_KitchenDetail"):
        t = unreal.load_asset(f"{TEX}/{n}")
        t.modify()
        mk.setp(t, srgb=False, compression_settings=unreal.TextureCompressionSettings.TC_BC7, never_stream=True,
                lod_group=unreal.TextureGroup.TEXTUREGROUP_WORLD,
                address_x=unreal.TextureAddress.TA_CLAMP if n == "T_CounterWear" else unreal.TextureAddress.TA_WRAP,
                address_y=unreal.TextureAddress.TA_CLAMP if n == "T_CounterWear" else unreal.TextureAddress.TA_WRAP)
        EAL.save_loaded_asset(t)


def mesh_settings():
    sml = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    meshes = {str(a.asset_name): unreal.load_asset(str(a.package_name)) for a in reg.get_assets_by_path(MESHES, recursive=True)
              if str(a.asset_class_path.asset_name) == "StaticMesh"}
    for name, mesh in meshes.items():
        changed = False
        bs = sml.get_lod_build_settings(mesh, 0)
        if bs.get_editor_property("generate_lightmap_u_vs"):  # the counter's UV1 is its wear map
            bs.set_editor_property("generate_lightmap_u_vs", False)
            sml.set_lod_build_settings(mesh, 0, bs)
            changed = True
        ns = mesh.get_editor_property("nanite_settings")
        want = name != "SM_Kiosk_KitchenCards"  # the cards are small and masked: plain rendering, exact alpha clip
        if ns.enabled != want:
            ns.enabled = want
            sml.set_nanite_settings(mesh, ns, apply_changes=True)
            changed = True
        if changed:
            EAL.save_loaded_asset(mesh)
    print(f"imported: {len(meshes)} meshes ({sum(1 for n in meshes if n.startswith('SM_KP_'))} prototypes); "
          f"counter UV channels {sml.get_num_uv_channels(meshes['SM_Kiosk_KitchenCounter'], 0)}")
    return meshes


# ---- 3. the master material ----------------------------------------------------------------------

SCALARS = ["Roughness", "Metallic", "EdgeWear", "EdgeRough", "EdgeMetal", "Grime", "AOStart", "Smudge", "Scratch", "Stain",
           "WearAmount", "EmissiveStrength", "Polish"]
COLORS = ["BaseColor", "EdgeColor", "GrimeColor", "Emissive"]
HLSL = r"""
// VC: baked masks (R convex edges, G occlusion, B cavity). D: tiling detail (R brushed grain, G smudges +
// fingerprints, B water spots, A grime noise). W: the customer counter's own wear map (UV1; R polish,
// G scratches, B stains, A seams), scaled by WearAmount (0 elsewhere).
float edge = VC.r, ao = VC.g, cav = VC.b;
float3 col = BaseColor;
float r = Roughness;
float m = Metallic;
float g = saturate((AOStart - ao) / max(AOStart, 1e-3)) * 0.8 + cav * 0.6;
g = saturate(g * (0.55 + 0.9 * D.a)) * Grime;
col = lerp(col, GrimeColor, g * 0.65);
r = lerp(r, 0.85, g * 0.45);
float e = saturate(edge * 1.6) * smoothstep(0.3, 0.7, D.a * 0.8 + edge * 0.5) * EdgeWear;
col = lerp(col, EdgeColor, e);
m = lerp(m, EdgeMetal, e);
r = lerp(r, EdgeRough, e);
float s = D.g * Smudge;
r = saturate(r + 0.28 * s);
col *= 1.0 - 0.07 * s;
r = saturate(r + (D.r - 0.5) * Scratch * 0.22);
float st = D.b * Stain;
col = lerp(col, col * float3(0.80, 0.77, 0.72), st);
r = saturate(r + 0.22 * st);
float pol = W.r * WearAmount * Polish, scr = W.g * WearAmount, ring = W.b * WearAmount, seam = W.a * WearAmount;
r = lerp(r, r * 0.45, pol);
col = col * (1.0 + 0.10 * pol);
r = saturate(r + 0.16 * scr);
col = col + scr * 0.012;
col = lerp(col, col * float3(0.78, 0.74, 0.68), saturate(ring * 0.9));
r = lerp(r, 0.65, saturate(ring * 0.7));
col = lerp(col, GrimeColor, saturate(seam * 0.85));
r = lerp(r, 0.9, saturate(seam));
if (Mode < 0.5) return float4(col, clamp(r, 0.03, 1.0));
return float4(m, Emissive * EmissiveStrength);
"""


def build_material():
    m = mk.material(FOLDER, "M_Kitchen")
    mk.setp(m, used_with_instanced_static_meshes=True, used_with_nanite=True)
    X = -2600
    uv0 = mk.expr(m, unreal.MaterialExpressionTextureCoordinate, X, -600, coordinate_index=0)
    uv1 = mk.expr(m, unreal.MaterialExpressionTextureCoordinate, X, -200, coordinate_index=1)
    tile = mk.scalar(m, "DetailTile", LOOK["detail_tile"], X, -500)
    div = mk.expr(m, unreal.MaterialExpressionDivide, X + 300, -600)
    mk.link(uv0, "", div, "A")
    mk.link(tile, "", div, "B")
    lin = unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
    tD = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, X + 600, -650, parameter_name="Detail",
                 texture=unreal.load_asset(f"{TEX}/T_KitchenDetail"), sampler_type=lin)
    tW = mk.expr(m, unreal.MaterialExpressionTextureSampleParameter2D, X + 600, -250, parameter_name="WearMap",
                 texture=unreal.load_asset(f"{TEX}/T_CounterWear"), sampler_type=lin)
    mk.link(div, "", tD, "UVs")
    mk.link(uv1, "", tW, "UVs")
    vc = mk.expr(m, unreal.MaterialExpressionVertexColor, X + 600, 150)
    params = {}
    defaults = LOOK["defaults"]
    for i, n in enumerate(SCALARS):
        params[n] = mk.scalar(m, n, defaults.get(n, 0.0), X + 900, 300 + i * 90)
    for i, n in enumerate(COLORS):
        params[n] = mk.vector(m, n, defaults.get(n, (0.5, 0.5, 0.5)), X + 1200, 300 + i * 110)
    names = ["VC", "D", "W", "Mode"] + SCALARS + COLORS
    outs = []
    for k, mode in enumerate((0.0, 1.0)):
        c = mk.custom(m, HLSL, names, unreal.CustomMaterialOutputType.CMOT_FLOAT4, -1100, -400 + k * 800,
                      "Kitchen surface" + (" (metal, emissive)" if mode else ""))
        mk.link(vc, "", c, "VC")
        mk.link(tD, "RGBA", c, "D")
        mk.link(tW, "RGBA", c, "W")
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
    print(f"material M_Kitchen: {len(MEL.get_material_expressions(m))} nodes")
    return m


def look_for(name, base):
    """Parameters for one kitchen material: the category preset, the Blender colour, then overrides."""
    cat, over = LOOK["materials"].get(name, ("plastic", {}))
    p = dict(LOOK["defaults"])
    p.update(LOOK["categories"][cat])
    rgb, rough, metal, emit = base
    p.update({"BaseColor": tuple(rgb), "Roughness": rough, "Metallic": metal})
    if emit > 0:
        p.update({"Emissive": tuple(rgb), "EmissiveStrength": LOOK["emissive"].get(name, 4.0)})
    p.update(over)
    return p


def build_instances(materials):
    master = unreal.load_asset(f"{FOLDER}/M_Kitchen")
    mis = {}
    for name, base in materials.items():
        p = look_for(name, base)
        mi = mk.instance(INST, f"MI_{name}", master, {k: v for k, v in p.items() if not isinstance(v, (tuple, list))},
                         {k: v for k, v in p.items() if isinstance(v, (tuple, list))})
        mis[name] = mi
    card = f"{dck.GAME}/Kiosk/Graphics/Instances/MI_KG_Kitchen"
    if EAL.does_asset_exist(card):
        mis["KG_Kitchen"] = unreal.load_asset(card)
    else:
        print("  !! no MI_KG_Kitchen: run kiosk_graphics.py (the Kitchen atlas slot) first")
    print(f"instances: {len(mis)}")
    return mis


# ---- 4. actors -----------------------------------------------------------------------------------

def assign(comp, mesh, mis):
    n = 0
    for i, slot in enumerate(mesh.static_materials):
        s = str(slot.material_slot_name)
        if s in mis:
            comp.set_material(i, mis[s])
            n += 1
        else:
            print(f"  !! {mesh.get_name()}: no instance for slot {s}")
    return n


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
        mesh = meshes.get(f"SM_KP_{name}")
        if mesh is None:
            print(f"  !! no prototype SM_KP_{name}")
            continue
        h, fail = sds.add_new_subobject(unreal.AddNewSubobjectParams(parent_handle=root, new_class=unreal.InstancedStaticMeshComponent,
                                                                     blueprint_context=None))
        sds.rename_subobject(h, unreal.Text(f"KP_{name}"))
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


# ---- 5. lights -----------------------------------------------------------------------------------

def ue_dir(v):
    return unreal.Vector(v[0], -v[1], v[2])


def lights(d):
    rig = d["lights"]
    n = 0
    for label, L in rig.items():
        cfg = S.INTERIOR if label == "L_Interior" else next((v for k, v in S.KITCHEN_LIGHTS.items() if label.startswith(k)), None)
        if cfg is None:
            continue
        folder = "Lights/Kiosk" if label == "L_Interior" else LIGHT_FOLDER
        pos = dck.to_ue(*L["pos"])
        if L["type"] == "rect":
            rot = unreal.MathLibrary.make_rot_from_xy(ue_dir(L["x_dir"]), ue_dir(L["y_dir"]))
            a = dck.get_or_spawn(unreal.RectLight, label, pos, rot, folder)
            c = a.get_component_by_class(unreal.RectLightComponent)
            c.modify()
            mk.setp(c, source_width=L["w"] * 100.0, source_height=max(L["h"] * 100.0, 1.0), barn_door_angle=cfg.get("barn_deg", 70.0),
                    barn_door_length=cfg.get("barn_cm", 6.0))
        elif L["type"] == "spot":
            rot = unreal.MathLibrary.make_rot_from_x(ue_dir(L["dir"]))
            a = dck.get_or_spawn(unreal.SpotLight, label, pos, rot, folder)
            c = a.get_component_by_class(unreal.SpotLightComponent)
            c.modify()
            mk.setp(c, inner_cone_angle=cfg.get("inner_deg", 25.0), outer_cone_angle=L["cone"], source_radius=3.0)
        else:
            a = dck.get_or_spawn(unreal.PointLight, label, pos, unreal.Rotator(0, 0, 0), folder)
            c = a.get_component_by_class(unreal.PointLightComponent)
            c.modify()
            mk.setp(c, source_radius=L.get("radius_cm", 5.0))
        a.modify()
        a.set_actor_location_and_rotation(pos, a.get_actor_rotation() if L["type"] == "point" else rot, False, False)
        c.set_mobility(unreal.ComponentMobility.MOVABLE)
        mk.setp(c, intensity_units=unreal.LightUnits.CANDELAS, attenuation_radius=cfg.get("radius_m", 3.0) * 100.0,
                volumetric_scattering_intensity=cfg.get("volumetric", S.KIOSK_LIGHT_VOLUMETRIC), cast_shadows=cfg.get("shadows", True))
        c.set_intensity(cfg["intensity_cd"] * S.LIGHT_SCALE)
        if "temperature" in cfg:
            mk.setp(c, use_temperature=True, temperature=float(cfg["temperature"]))
            c.set_light_color(unreal.LinearColor(1, 1, 1, 1))
        else:
            mk.setp(c, use_temperature=False)
            c.set_light_color(unreal.LinearColor(*cfg["color"], 1.0))
        n += 1
    print(f"lights: {n}")


def show(on):
    for name in UNIQUE + (PROPS_ACTOR,):
        a = dck.find_actor(name)
        if a:
            a.set_actor_hidden_in_game(not on)
            a.set_is_temporarily_hidden_in_editor(not on)
    for a in dck.ACTORS.get_all_level_actors():
        if str(a.get_folder_path()) == LIGHT_FOLDER:
            a.set_actor_hidden_in_game(not on)
            c = a.get_component_by_class(unreal.LightComponent)
            if c:
                c.set_editor_property("visible", on)


def apply(full=False):
    d = data()
    trimmed = trim(d["trim"]) if full or not EAL.does_asset_exist(f"{FOLDER}/Trim/SM_Kiosk_ServiceSide_K") else {
        n: unreal.load_asset(f"{FOLDER}/Trim/{n}_K") for n in d["trim"]}
    use_trimmed(trimmed, True)
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    meshes = {str(a.asset_name): unreal.load_asset(str(a.package_name)) for a in reg.get_assets_by_path(MESHES, recursive=True)
              if str(a.asset_class_path.asset_name) == "StaticMesh"}
    mis = build_instances(d["materials"])
    place(meshes, mis, d)
    lights(d)
    show(True)
    dck.LEVELS.save_current_level()


if __name__ == "__main__":
    args = sys.argv[1:]
    dck.ensure_map()
    if "--off" in args:
        d = data()
        use_trimmed({n: None for n in d["trim"]}, False)
        show(False)
        dck.LEVELS.save_current_level()
        print("kiosk_kitchen: off (old interior back)")
    elif "--textures" in args:  # re-import the wear maps only (after make_kitchen_textures.py)
        import_textures()
        print("kiosk_kitchen: wear textures re-imported")
    else:
        if "--apply" not in args:
            import_all()
            build_material()
        apply(full="--apply" not in args)
        print("kiosk_kitchen: done")
