"""Exports the crowd's mannequin bodies (reference pose) for the Blender outfit builder:
RawContent/bodies/<Body>.json = vertices (cm, Unreal component space), triangles, the dominant
bone of every vertex, and every joint's reference-pose position. build_outfits.py fits the coats
and hoods round these; setup_outfits.py then skins them with the bodies' own weights.

    node Scripts/ue.mjs Scripts/export_bodies.py
"""
import importlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dck  # noqa: E402
import scene_config as S  # noqa: E402

dck, S = importlib.reload(dck), importlib.reload(S)
import unreal  # noqa: E402

GA, BW, Q = unreal.GeometryScript_AssetUtils, unreal.GeometryScript_BoneWeights, unreal.GeometryScript_MeshQueries
LU = getattr(unreal, "GeometryScript_ListUtilities", None) or getattr(unreal, "GeometryScript_List", None)
OUT = os.path.join(dck.RAW, "bodies")
os.makedirs(OUT, exist_ok=True)


def as_list(ret, conv):
    lst = next(r for r in (ret if isinstance(ret, tuple) else (ret,)) if "List" in type(r).__name__)
    for name in (conv, conv.replace("convert_", "")):
        f = getattr(LU, name, None)
        if f:
            return f(lst)
    raise RuntimeError(f"no list conversion {conv}: {[m for m in dir(LU) if 'convert' in m]}")


for body, path in S.CROWD_LOOK["bodies"].items():
    sk = unreal.load_asset(path)
    dm, outcome = GA.copy_mesh_from_skeletal_mesh(sk, unreal.DynamicMesh(), unreal.GeometryScriptCopyMeshFromAssetOptions(),
                                                  unreal.GeometryScriptMeshReadLOD())
    assert not Q.get_has_vertex_id_gaps(dm) and not Q.get_has_triangle_id_gaps(dm)  # ids == list positions
    pos = as_list(Q.get_all_vertex_positions(dm, False), "convert_vector_list_to_array")
    tris = as_list(Q.get_all_triangle_indices(dm, False), "convert_triangle_list_to_array")
    bones = [str(b.name) for b in BW.get_all_bones_info(dm)[1]]
    dom = [BW.get_largest_vertex_bone_weight(dm, v)[1].bone_index for v in range(len(pos))]
    joints = {}  # the MESH's own reference pose (Quinn is shorter than the shared skeleton's Manny pose)
    for info in BW.get_all_bones_info(dm)[1]:
        t = info.get_editor_property("world_transform")
        q = t.rotation
        joints[str(info.name)] = {"pos": [round(t.translation.x, 3), round(t.translation.y, 3), round(t.translation.z, 3)],
                                  "rot": [round(q.x, 6), round(q.y, 6), round(q.z, 6), round(q.w, 6)]}
    data = {"body": body, "mesh": path, "verts": [[round(p.x, 3), round(p.y, 3), round(p.z, 3)] for p in pos],
            "tris": [[t.x, t.y, t.z] if hasattr(t, "x") else list(t) for t in tris], "bones": bones, "dominant_bone": dom, "joints": joints}
    with open(os.path.join(OUT, f"{body}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f)
    print(f"export_bodies: {body}: {len(pos)} verts, {len(tris)} tris, {len(bones)} bones; head at {joints['head']['pos']}")
