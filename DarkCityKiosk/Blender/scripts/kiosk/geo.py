"""Geometry toolkit for the scripted kiosk: a mesh accumulator plus primitives.

Parts are generated in world space (kiosk frame, metres) and merged into a few meshes
per section, so the .blend stays light and the glTF export stays simple. Randomness is
seeded, so every rebuild is identical until a number in kiosk_config changes.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

RNG = random.Random(1979)


def reseed(seed):
    RNG.seed(seed)


class Mesh:
    """Collects faces (with material + smooth flags) and builds one object at the end."""

    def __init__(self, name):
        self.name = name
        self.verts, self.faces, self.face_mat, self.face_smooth, self.mats = [], [], [], [], []

    def _mat(self, name):
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def add_raw(self, verts, faces, mat, smooth=False):
        off, mi = len(self.verts), self._mat(mat)
        self.verts.extend(verts)
        for f in faces:
            self.faces.append(tuple(off + i for i in f))
            self.face_mat.append(mi)
            self.face_smooth.append(smooth)

    def add_bm(self, bm, mat, smooth=False, matrix=None):
        if matrix is not None:
            bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
        bm.verts.index_update()
        self.add_raw([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in bm.faces], mat, smooth)
        bm.free()

    def build(self, coll, materials):
        me = bpy.data.meshes.new(self.name)
        me.from_pydata([tuple(v) for v in self.verts], [], self.faces)
        me.update()
        for m in self.mats:
            me.materials.append(materials[m])
        me.polygons.foreach_set("material_index", self.face_mat)
        me.polygons.foreach_set("use_smooth", self.face_smooth)
        planar_uvs(me)
        ob = bpy.data.objects.new(self.name, me)
        coll.objects.link(ob)
        return ob


# ---- Primitives ---------------------------------------------------------------------

def box(mesh, x0, x1, y0, y1, z0, z1, mat, bevel=0.0, segments=1, rot=None, smooth=False):
    """Axis-aligned box from bounds; optional bevel (m) and rotation (Euler, radians) about its centre."""
    sx, sy, sz = abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    b = min(bevel, 0.45 * min(sx, sy, sz))
    if b > 1e-5:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=b, offset_type="OFFSET", segments=segments,
                        profile=0.5, affect="EDGES", clamp_overlap=True)
    m = Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    if rot is not None:
        m = m @ rot.to_matrix().to_4x4()
    mesh.add_bm(bm, mat, smooth, m)


def cylinder(mesh, center, radius, depth, mat, axis="Z", segments=16, smooth=True, cap=True):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=cap, cap_tris=False, segments=segments, radius1=radius, radius2=radius, depth=depth)
    rot = {"Z": Matrix.Identity(4), "X": Matrix.Rotation(math.radians(90), 4, "Y"),
           "Y": Matrix.Rotation(math.radians(90), 4, "X")}[axis]
    mesh.add_bm(bm, mat, smooth, Matrix.Translation(center) @ rot)


def pipe(mesh, a, b, radius, mat, segments=10):
    """Cylinder between two points (any direction)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=radius, radius2=radius, depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    mesh.add_bm(bm, mat, True, Matrix.Translation((a + b) / 2) @ rot)


_RIVET = None


def _rivet_template():
    """Low-poly dome, unit radius, height 0.6, along +Z."""
    global _RIVET
    if _RIVET is None:
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=4, radius=1.0)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context="VERTS")
        bmesh.ops.scale(bm, vec=(1, 1, 0.6), verts=bm.verts)
        bm.verts.index_update()
        _RIVET = ([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in bm.faces])
        bm.free()
    return _RIVET


_NORMAL_ROT = {
    "+Z": Matrix.Identity(3), "-Y": Matrix.Rotation(math.radians(90), 3, "X"),
    "+Y": Matrix.Rotation(math.radians(-90), 3, "X"), "-X": Matrix.Rotation(math.radians(-90), 3, "Y"),
    "+X": Matrix.Rotation(math.radians(90), 3, "Y"), "-Z": Matrix.Rotation(math.radians(180), 3, "X"),
}


def rivets(mesh, points, normal, mat, radius=0.009):
    """Domed rivet heads at world points, facing `normal` ('-Y', '+X', ...)."""
    tv, tf = _rivet_template()
    rot = _NORMAL_ROT[normal]
    for p in points:
        p = Vector(p)
        mesh.add_raw([p + rot @ (v * radius) for v in tv], tf, mat, smooth=True)


_BOLT = None


def _bolt_template():
    """Hex bolt head on a round washer, unit radius (across the hex corners), along +Z."""
    global _BOLT
    if _BOLT is None:
        bm = bmesh.new()
        ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=10, radius1=1.35, radius2=1.35, depth=0.14)
        bmesh.ops.translate(bm, vec=(0, 0, 0.07), verts=ret["verts"])
        ret = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=6, radius1=1.0, radius2=1.0, depth=0.6)
        bmesh.ops.translate(bm, vec=(0, 0, 0.14 + 0.3), verts=ret["verts"])
        bm.verts.index_update()
        _BOLT = ([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in bm.faces])
        bm.free()
    return _BOLT


def bolts(mesh, points, normal, mat, radius=0.016):
    """Hex bolt heads with washers at world points, facing `normal`; each hex turned at random."""
    tv, tf = _bolt_template()
    base = _NORMAL_ROT[normal]
    for p in points:
        rot = base @ Matrix.Rotation(RNG.uniform(0, math.pi / 3), 3, "Z")
        p = Vector(p)
        mesh.add_raw([p + rot @ (v * radius) for v in tv], tf, mat, smooth=False)


def prism(mesh, outline, mat, smooth=False):
    """Closed solid from two matching loops of world points (`outline` = (front_loop, back_loop)),
    e.g. a gusset plate: the same polygon at two depths. Normals are made to point outward."""
    front, back = outline
    n = len(front)
    bm = bmesh.new()
    vf = [bm.verts.new(Vector(p)) for p in front]
    vb = [bm.verts.new(Vector(p)) for p in back]
    bm.faces.new(vf)
    bm.faces.new(list(reversed(vb)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((vf[j], vf[i], vb[i], vb[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh.add_bm(bm, mat, smooth)


def ibeam(mesh, axis, fixed, a, b, z0, z1, mat, width=0.08, flange=0.012, web=0.012):
    """I-section beam hanging between z0 (bottom flange) and z1 (top flange) along `axis`
    ('X' or 'Y') from a to b, centred on `fixed` (the other horizontal coordinate)."""
    def part(lo, hi, h0, h1):
        if axis == "X":
            box(mesh, a, b, fixed + lo, fixed + hi, h0, h1, mat, 0.002)
        else:
            box(mesh, fixed + lo, fixed + hi, a, b, h0, h1, mat, 0.002)
    part(-width / 2, width / 2, z0, z0 + flange)
    part(-web / 2, web / 2, z0 + flange, z1 - flange)
    part(-width / 2, width / 2, z1 - flange, z1)


# ---- Rectangles (wall layout) --------------------------------------------------------

def subtract_rects(rect, holes, min_size=0.02):
    """rect/holes = (u0, u1, z0, z1). Returns the pieces of rect not covered by any hole."""
    rects = [rect]
    for h in holes:
        out = []
        for a0, a1, b0, b1 in rects:
            if h[0] >= a1 or h[1] <= a0 or h[2] >= b1 or h[3] <= b0:
                out.append((a0, a1, b0, b1))
                continue
            if h[0] > a0:
                out.append((a0, h[0], b0, b1))
            if h[1] < a1:
                out.append((h[1], a1, b0, b1))
            c0, c1 = max(a0, h[0]), min(a1, h[1])
            if h[2] > b0:
                out.append((c0, c1, b0, h[2]))
            if h[3] < b1:
                out.append((c0, c1, h[3], b1))
        rects = out
    return [r for r in rects if r[1] - r[0] > min_size and r[3] - r[2] > min_size]


def jitter(amount):
    return RNG.uniform(-amount, amount)


def rounded_box(mesh, x0, x1, y0, y1, z0, z1, mat, axis, radius, segments=4, smooth=False):
    """Box whose outline (seen along `axis`: 'X', 'Y' or 'Z') has rounded corners, e.g. a door leaf."""
    sx, sy, sz = abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=bm.verts)
    ai = "XYZ".index(axis)
    edges = [e for e in bm.edges if abs((e.verts[1].co - e.verts[0].co).normalized()[ai]) > 0.99]
    dims = [d for i, d in enumerate((sx, sy, sz)) if i != ai]
    r = min(radius, 0.49 * min(dims))
    if r > 1e-5:
        bmesh.ops.bevel(bm, geom=edges, offset=r, offset_type="OFFSET", segments=segments, profile=0.5,
                        affect="EDGES", clamp_overlap=True)
    mesh.add_bm(bm, mat, smooth, Matrix.Translation(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)))


def lathe(mesh, center, profile, mat, segments=24, smooth=True, cap_bottom=True, cap_top=True):
    """Surface of revolution about a vertical axis at `center`; profile = [(radius, z), ...] bottom to top."""
    cx, cy, cz = center
    verts, faces = [], []
    for r, z in profile:
        for k in range(segments):
            a = 2 * math.pi * k / segments
            verts.append(Vector((cx + r * math.cos(a), cy + r * math.sin(a), cz + z)))
    for i in range(len(profile) - 1):
        for k in range(segments):
            a, b = i * segments + k, i * segments + (k + 1) % segments
            faces.append((a, b, b + segments, a + segments))
    if cap_bottom:
        faces.append(tuple(reversed(range(segments))))
    if cap_top:
        top = (len(profile) - 1) * segments
        faces.append(tuple(range(top, top + segments)))
    mesh.add_raw(verts, faces, mat, smooth)


def cable(mesh, a, b, sag, radius, mat, steps=10):
    """A hanging cable between two points, sagging by `sag` metres at the middle."""
    a, b = Vector(a), Vector(b)
    pts = [a.lerp(b, i / steps) - Vector((0, 0, sag * 4 * (i / steps) * (1 - i / steps))) for i in range(steps + 1)]
    for p, q in zip(pts, pts[1:]):
        pipe(mesh, p, q, radius, mat, 6)


def planar_uvs(me):
    """UVs in metres: vertical faces get u = distance along the face (horizontal tangent) and
    v = height; flat faces get u, v = world x, y. Unreal materials use these for window grids
    and world-scale textures without caring how a part is rotated."""
    uv = me.uv_layers.new(name="UVMap")
    co = [v.co for v in me.vertices]
    out = [0.0] * (len(me.loops) * 2)
    for p in me.polygons:
        n = p.normal
        if abs(n.z) > 0.7:
            for li in p.loop_indices:
                c = co[me.loops[li].vertex_index]
                out[2 * li], out[2 * li + 1] = c.x, c.y
        else:
            t = Vector((-n.y, n.x, 0.0))
            t = t.normalized() if t.length > 1e-6 else Vector((1.0, 0.0, 0.0))
            for li in p.loop_indices:
                c = co[me.loops[li].vertex_index]
                out[2 * li], out[2 * li + 1] = c.dot(t), c.z
    # Screens get 0..1 UVs per face (image fills the face, upright, unmirrored seen from the front)
    screen_mats = {i for i, m in enumerate(me.materials) if m and m.name.startswith(("City_Screen_", "Veh_LiftMist"))}
    if screen_mats:
        for p in me.polygons:
            if p.material_index not in screen_mats:
                continue
            us = [out[2 * li] for li in p.loop_indices]
            vs = [out[2 * li + 1] for li in p.loop_indices]
            du, dv = (max(us) - min(us)) or 1.0, (max(vs) - min(vs)) or 1.0
            for li in p.loop_indices:
                out[2 * li] = (out[2 * li] - min(us)) / du
                out[2 * li + 1] = (out[2 * li + 1] - min(vs)) / dv
    uv.data.foreach_set("uv", out)
