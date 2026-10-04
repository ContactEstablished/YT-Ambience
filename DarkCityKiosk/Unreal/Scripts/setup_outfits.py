"""Dresses the crowd's mannequins: imports RawContent/outfits.glb (Blender build_outfits.py), skins
the coat and hood with each body's own bone weights, and saves one skeletal mesh per outfit:
  /Game/DarkCity/Crowd/Outfits/SKM_<Body>_Coat       body + belted coat
  /Game/DarkCity/Crowd/Outfits/SKM_<Body>_CoatHood   body + coat + hood
The coat's skirt is weighted by hand (hips into the thighs, split by side) so it swings with
the stride instead of folding at the knee. Hats stay static meshes on the head bone
(setup_crowd.py). Same skeletons as the bodies, so every clip still plays.

    node Scripts/ue.mjs Scripts/export_bodies.py        # bodies -> Blender (once)
    blender -b --factory-startup -P build_outfits.py    # garments -> RawContent/outfits.glb
    node Scripts/ue.mjs Scripts/setup_outfits.py
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

GA, BW, NA, Q, MAT = (unreal.GeometryScript_AssetUtils, unreal.GeometryScript_BoneWeights, unreal.GeometryScript_NewAssetUtils,
                      unreal.GeometryScript_MeshQueries, unreal.GeometryScript_Materials)
ED = unreal.GeometryScript_MeshEdits
DIR = f"{dck.GAME}/Crowd/Outfits"
P = S.CROWD_LOOK
READ = (unreal.GeometryScriptCopyMeshFromAssetOptions(), unreal.GeometryScriptMeshReadLOD())


def import_outfits():
    task = mk.setp(unreal.AssetImportTask(), filename=os.path.join(dck.RAW, "outfits.glb"), destination_path=f"{DIR}/Garments",
                   automated=True, replace_existing=True, save=True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    reg = unreal.AssetRegistryHelpers.get_asset_registry()
    return {str(x.asset_name): unreal.load_asset(str(x.package_name))
            for x in reg.get_assets_by_path(f"{DIR}/Garments", recursive=True) if str(x.asset_class_path.asset_name) == "StaticMesh"}


def body_mesh(sk):
    dm, _ = GA.copy_mesh_from_skeletal_mesh(sk, unreal.DynamicMesh(), *READ)
    return dm


def garment(sm, body_dm):
    """The garment as a DynamicMesh with the body's bones, weighted from the nearest body surface."""
    dm, _ = GA.copy_mesh_from_static_mesh(sm, unreal.DynamicMesh(), *READ)
    opts = unreal.GeometryScriptTransferBoneWeightsOptions()
    opts.set_editor_property("output_target_mesh_bones", unreal.OutputTargetMeshBones.SOURCE_BONES)
    dm = BW.transfer_bone_weights_from_mesh(body_dm, dm, opts)
    return dm, [m.material_interface for m in sm.static_materials], [str(m.material_slot_name) for m in sm.static_materials]


def weight_skirt(dm, slot_names):
    """Skirt vertices: pelvis at the waist, handing over to the thigh on the same side toward the hem."""
    ids = [i for i, n in enumerate(slot_names) if n.startswith("Coat_Skirt")]
    if not ids:
        print("  (no Coat_Skirt slot)")
        return 0
    bone = {n: next(r for r in BW.get_bone_index(dm, n) if type(r) is int) for n in ("pelvis", "thigh_l", "thigh_r")}
    verts = set()
    for mid in ids:
        tris = MAT.get_triangles_by_material_id(dm, mid)
        tri_list = next(t for t in (tris if isinstance(tris, tuple) else (tris,)) if "List" in type(t).__name__)
        for tid in unreal.GeometryScript_List.convert_index_list_to_array(tri_list):
            tri = Q.get_triangle_indices(dm, tid)
            tri = tri[0] if isinstance(tri, tuple) else tri
            verts.update((tri.x, tri.y, tri.z))
    zs = {v: Q.get_vertex_position(dm, v)[0] for v in verts}
    ztop, zhem = max(p.z for p in zs.values()), min(p.z for p in zs.values())
    sk = P["skirt_weights"]
    for v, p in zs.items():
        t = max(0.0, min(1.0, (ztop - p.z) / (ztop - zhem)))
        leg = sk["thigh_at_hem"] * t ** sk["curve"]
        x = max(-1.0, min(1.0, p.x / sk["side_blend_cm"]))  # +X is the body's left
        left = 0.5 + 0.5 * x
        w = [(bone["pelvis"], 1.0 - leg), (bone["thigh_l"], leg * left), (bone["thigh_r"], leg * (1.0 - left))]
        BW.set_vertex_bone_weights(dm, v, [unreal.GeometryScriptBoneWeight(bone_index=b, weight=wt) for b, wt in w if wt > 1e-4])
    return len(verts)


def build(body_name, sk, garments):
    body_dm = body_mesh(sk)
    out = body_mesh(sk)
    mats = [m.material_interface for m in sk.materials]
    names = [str(m.material_slot_name) for m in sk.materials]
    for g in garments:
        dm, gm, gn = garment(g, body_dm)
        n = weight_skirt(dm, gn) if gn and any(s.startswith("Coat_Skirt") for s in gn) else 0
        res = ED.append_mesh_with_materials(out, mats, dm, gm, unreal.Transform(), False, unreal.GeometryScriptAppendMeshOptions(), True)
        mats = list(res[1]) if isinstance(res, tuple) else mats + gm
        print(f"  {body_name}: + {g.get_name()} ({n} skirt vertices hand-weighted)")
    return out, mats, [m.get_name() for m in mats]  # slot names follow the merged material list


garments = import_outfits()
results = []
for body_name, path in P["bodies"].items():
    sk = unreal.load_asset(path)
    skel = sk.get_editor_property("skeleton")
    for outfit, parts in P["outfits"].items():
        dm, mats, names = build(body_name, sk, [garments[f"{p}_{body_name}"] for p in parts])
        asset = f"{DIR}/SKM_{body_name}_{outfit}"
        if mk.EAL.does_asset_exist(asset):
            mk.EAL.delete_asset(asset)
        o = unreal.GeometryScriptCreateNewSkeletalMeshAssetOptions()
        o.set_editor_property("use_mesh_bone_proportions", True)
        o.set_editor_property("materials", {unreal.Name(f"{i:02d}_{n}"): m for i, (n, m) in enumerate(zip(names, mats))})
        new, outcome = NA.create_new_skeletal_mesh_asset_from_mesh(dm, skel, asset, o)
        mk.EAL.save_loaded_asset(new)
        results.append((asset, outcome, len(new.materials), Q.get_vertex_count(dm)))
for r in results:
    print("setup_outfits:", *r)
