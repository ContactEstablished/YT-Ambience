"""Overlap check for the utility pass (kiosk/utilities.py). Each swept line (utilities.RUNS, stored
as JSON on the Utilities object) is tested against every other kiosk mesh and against the other
runs. Contact within a few cm of either run's ends is ignored, since lines enter boxes there by
design. Prints one HIT block per run that passes through something, with its location.
Run it after build_kiosk.py:
    blender -b ../kiosk_detail.blend --factory-startup -P check_utility_overlaps.py
Known and intended: the driver cables pass through a joist web (as through a drilled hole) and
touch each other where they bend out of the soffit.
"""
import json

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

JOINS = (("driver_drop", "driver_cable"),)  # runs that branch off each other by design

deps = bpy.context.evaluated_depsgraph_get()
ob = bpy.data.objects["Utilities"]
runs = json.loads(ob["runs"])
me = ob.data
V = [ob.matrix_world @ v.co for v in me.vertices]

others = {}
for o in bpy.data.objects:
    if o.type != "MESH" or o.name in ("Utilities", "Ground") or o.name.startswith("Cutter_"):
        continue
    oe = o.evaluated_get(deps)
    m2 = oe.to_mesh()
    verts = [o.matrix_world @ v.co for v in m2.vertices]
    polys = [tuple(p.vertices) for p in m2.polygons]
    others[o.name] = (BVHTree.FromPolygons(verts, polys), verts, polys)
    oe.to_mesh_clear()


def run_tree(r):
    f0, f1 = r["faces"]
    polys = [tuple(me.polygons[i].vertices) for i in range(f0, f1)]
    used = sorted({i for p in polys for i in p})
    remap = {v: k for k, v in enumerate(used)}
    verts = [V[i] for i in used]
    polys2 = [tuple(remap[i] for i in p) for p in polys]
    return BVHTree.FromPolygons(verts, polys2), verts, polys2


def joined(a, b):
    return any(a.startswith(x) and b.startswith(y) or a.startswith(y) and b.startswith(x) for x, y in JOINS)


trees = {r["name"]: run_tree(r) for r in runs}
ends_of = {r["name"]: [Vector(e) for e in r["ends"]] for r in runs}
bad = 0
for r in runs:
    tree, verts, polys = trees[r["name"]]
    margin = r["r"] + 0.035
    hits = []
    targets = list(others.items()) + [(n, t) for n, t in trees.items() if n != r["name"] and not joined(r["name"], n)]
    for name, (otree, ov, op) in targets:
        near = ends_of[r["name"]] + ends_of.get(name, [])
        pts = []
        for a, b in tree.overlap(otree):
            c = sum((verts[i] for i in polys[a]), Vector()) / len(polys[a])
            if min((c - e).length for e in near) >= margin:
                pts.append(c)
        if pts:
            zs = sorted(p.z for p in pts)
            c = pts[len(pts) // 2]
            hits.append(f"{name}: {len(pts)} @ ({c.x:.3f},{c.y:.3f},{c.z:.3f}) z {zs[0]:.3f}..{zs[-1]:.3f}")
    if hits:
        bad += 1
        print(f"HIT {r['name']} (r {r['r']}):")
        for h in hits:
            print("    " + h)
print(f"check_utility_overlaps: {len(runs)} runs, {bad} with overlaps; utilities faces {len(me.polygons)}")
