"""Signage pass (2026-10-05, brief 6): graphics on the kiosk.

Lays the textured cards (posters, notices, labels, stickers, plates, lit sign faces) from
kiosk_config.GRAPHICS_CARDS onto the exported kiosk, builds the 24h lightbox and the ramen lantern's
lettering, and works out where Unreal's paint decals go (GRAPHICS_DECALS). The art comes from
Graphics/make_kiosk_graphics.mjs; graphics_manifest.json gives every item's atlas rectangle and size.

Each card is a grid laid onto the kiosk by raycasting from in front of its wall: paper bridges over
battens, laps and rivets (the proudest hit near each grid point wins), sits on proud sheets and slips
behind conduits that stand off the wall. A card can lift at one corner (peeling).

UV0 is the card's atlas rectangle. UV1 is the WeatherUV of the kiosk surface under each triangle,
taken from kiosk_detail.glb's TEXCOORD_1, so in Unreal the card samples the same weathering masks as
the wall it is stuck to: rain streaks, grime, wetness and splash carry on across it. Vertex colour:
R a per-card random, G age (0 new .. 1 old), B unused, A 1 where the surface under it is weathered.
"""
import math
import re

import bmesh  # noqa: F401
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

import kiosk_config as C
from . import geo

WEATHERED = set(C.WEATHER["materials"])
SECTIONS = {f"SM_Kiosk_{s}" for s in C.WEATHER["sections"]}
SLOTS = {"Paper": "KG_Paper", "Labels": "KG_Labels", "Signs": "KG_Signs", "Decals": "KG_Decals"}
BASE_OFF = 0.0012  # card above the surface it lies on (m)
LAYER_OFF = 0.0009  # per stacking layer
CELL = {"Paper": 0.01, "Labels": 0.008, "Signs": 0.03}  # grid spacing of a card (m)
TENT = 0.006  # neighbourhood for bridging over rivets and seams (m)


def wall_frame(wall):
    """(normal out of the wall, the viewer's right, up) for a wall name."""
    if wall == "left":
        return Vector((-1, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))
    if wall == "front":
        return Vector((0, -1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1))
    raise ValueError(wall)


def wall_point(wall, u, z):
    return Vector((C.X0, u, z)) if wall == "left" else Vector((u, C.Y0, z))


class Target:
    """The exported kiosk as raycast targets, with each hit's WeatherUV."""

    def __init__(self, objects):
        self.objs = []
        for ob in objects:
            me = ob.data
            uv1 = me.uv_layers[1] if len(me.uv_layers) > 1 else None
            mats = [re.sub(r"\.\d{3}$", "", m.name) if m else "" for m in me.materials]  # imported names may clash (.001)
            weathered = ob.name in SECTIONS
            mw = ob.matrix_world.copy()
            # world space: some sections import with a node transform (the joined mesh took a text
            # object's pivot, e.g. SM_Kiosk_Canopy and SM_Kiosk_ServiceSide)
            co = np.empty(len(me.vertices) * 3, np.float32)
            me.vertices.foreach_get("co", co)
            co = co.reshape(-1, 3) @ np.array(mw.to_3x3()).T + np.array(mw.translation)
            bvh = BVHTree.FromPolygons([tuple(v) for v in co], [tuple(p.vertices) for p in me.polygons], epsilon=0.0)
            self.objs.append((ob, bvh, uv1, mats, weathered, mw))

    def cast(self, origin, direction, dist):
        """Nearest hit: (location, normal, object index, polygon index, distance) or None."""
        best = None
        for k, (ob, bvh, *_rest) in enumerate(self.objs):
            loc, nrm, idx, d = bvh.ray_cast(origin, direction, dist)
            if loc is not None and (best is None or d < best[4]):
                best = (loc, nrm, k, idx, d)
        return best

    def weather_uv(self, hit, points):
        """WeatherUV (Blender convention) at points near the hit's polygon, extrapolated in its plane;
        and whether that surface is weathered."""
        loc, nrm, k, idx, d = hit
        ob, bvh, uv1, mats, weathered, mw = self.objs[k]
        poly = ob.data.polygons[idx]
        ok = weathered and uv1 is not None and mats[poly.material_index] in WEATHERED
        if not ok:
            return [(0.0, 0.0)] * len(points), False
        vs = [mw @ ob.data.vertices[i].co for i in poly.vertices[:3]]
        uvs = [Vector((*uv1.data[li].uv, 0.0)) for li in list(poly.loop_indices)[:3]]
        out = []
        for p in points:
            q = barycentric_transform(p, vs[0], vs[1], vs[2], uvs[0], uvs[1], uvs[2])
            out.append((q.x, q.y))
        return out, True


class CardMesh:
    """Triangles with per-loop UV0, UV1 and colour, built into one object at the end."""

    def __init__(self, name):
        self.name = name
        self.verts, self.tris, self.uv0, self.uv1, self.col, self.mat = [], [], [], [], [], []
        self.mats = []

    def add_tri(self, ps, uv0, uv1, col, mat, idx=None):
        """A triangle with per-corner UV0, UV1 and colour. `idx` reuses existing vertices (a card's grid
        shares them, so its normals smooth across the bumps it bridges); else new vertices at `ps`."""
        if mat not in self.mats:
            self.mats.append(mat)
        if idx is None:
            base = len(self.verts)
            self.verts.extend(ps)
            idx = (base, base + 1, base + 2)
        self.tris.append(tuple(idx))
        self.uv0.extend(uv0)
        self.uv1.extend(uv1)
        self.col.extend(col)
        self.mat.append(self.mats.index(mat))

    def add_vert(self, p):
        self.verts.append(p)
        return len(self.verts) - 1

    def build(self, coll, materials):
        me = bpy.data.meshes.new(self.name)
        me.from_pydata([tuple(v) for v in self.verts], [], self.tris)
        me.update()
        for m in self.mats:
            me.materials.append(materials[m])
        me.polygons.foreach_set("material_index", self.mat)
        me.polygons.foreach_set("use_smooth", [True] * len(self.tris))
        for name, data in (("UVMap", self.uv0), ("WeatherUV", self.uv1)):
            layer = me.uv_layers.new(name=name)
            layer.data.foreach_set("uv", np.array(data, np.float32).ravel())
        ca = me.color_attributes.new("Col", "FLOAT_COLOR", "CORNER")
        ca.data.foreach_set("color", np.array(self.col, np.float32).ravel())
        me.color_attributes.active_color = ca
        ob = bpy.data.objects.new(self.name, me)
        coll.objects.link(ob)
        return ob


def _hash01(s):
    h = 2166136261
    for ch in s:
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return (h % 10007) / 10007.0


def lay_card(cm, target, man, item, wall, u, z, rot, layer, opt, key):
    m = man["items"][item]
    scale = opt.get("scale", 1.0)
    W, H = m["size_m"][0] * scale, m["size_m"][1] * scale
    n, r0, up0 = wall_frame(wall)
    a = math.radians(rot)
    r = r0 * math.cos(a) + up0 * math.sin(a)
    up = up0 * math.cos(a) - r0 * math.sin(a)
    centre = wall_point(wall, u, z)
    depth = opt.get("depth", 0.04)
    cell = CELL.get(m["atlas"], 0.012)
    nu, nv = max(2, math.ceil(W / cell)), max(2, math.ceil(H / cell))
    # surface height (w, out of the wall plane) at every grid point: the proudest of a few nearby rays
    grid = {}
    misses = 0
    for j in range(nv + 1):
        for i in range(nu + 1):
            s, t = i / nu, j / nv
            p0 = centre + r * ((s - 0.5) * W) + up * ((t - 0.5) * H)
            best = None
            for dr, du in ((0, 0), (TENT, 0), (-TENT, 0), (0, TENT), (0, -TENT)):
                hit = target.cast(p0 + r * dr + up * du + n * depth, -n, depth + 0.12)
                if hit is not None:
                    w = depth - hit[4]
                    best = w if best is None else max(best, w)
            if best is None:
                misses += 1
                best = 0.0
            grid[i, j] = (p0, best)
    if opt.get("flat"):
        wmax = max(w for _, w in grid.values())
        grid = {k: (p, wmax) for k, (p, w) in grid.items()}
    elif m["atlas"] == "Paper":
        # paper bridges steps (battens, laps, a hatch frame) in a ramp a few cm wide instead of
        # following them in sharp steps (which stair-step where an edge runs across the grid diagonally):
        # dilate the surface (stays clear of every proud edge), then soften the ramp
        wf = np.array([[grid[i, j][1] for i in range(nu + 1)] for j in range(nv + 1)])
        for _ in range(2):
            p = np.pad(wf, 1, mode="edge")
            wf = np.max([p[dj:dj + nv + 1, di:di + nu + 1] for dj in range(3) for di in range(3)], axis=0)
        for _ in range(2):
            p = np.pad(wf, 1, mode="edge")
            wf = np.mean([p[dj:dj + nv + 1, di:di + nu + 1] for dj in range(3) for di in range(3)], axis=0)
        grid = {(i, j): (grid[i, j][0], max(float(wf[j, i]), grid[i, j][1])) for (i, j) in grid}
    lift = opt.get("lift")
    corners = {"tl": (0, 1), "tr": (1, 1), "bl": (0, 0), "br": (1, 0)}
    off = BASE_OFF + layer * LAYER_OFF + (0.002 if opt.get("flat") else 0.0)
    pts = {}
    for (i, j), (p0, w) in grid.items():
        s, t = i / nu, j / nv
        extra = 0.0
        if lift:
            cs, ct = corners[lift[0]]
            d = math.hypot((s - cs) * W, (t - ct) * H)
            if d < lift[1]:
                extra = lift[2] * ((lift[1] - d) / lift[1]) ** 2
        pts[i, j] = p0 + n * (w + off + extra)
    u0, v0, u1, v1 = m["uv"]
    seed = _hash01(key)
    age = opt.get("age", 0.5)
    slot = SLOTS[m["atlas"]]
    weathered = 0
    vid = {k: cm.add_vert(p) for k, p in pts.items()}  # shared grid vertices: smooth normals over the bumps
    for j in range(nv):
        for i in range(nu):
            quad = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            for tri in ((quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])):
                ps = [pts[k] for k in tri]
                c = (ps[0] + ps[1] + ps[2]) / 3
                hit = target.cast(c + n * 0.03, -n, 0.2)
                if hit is not None:
                    uv1, ok = target.weather_uv(hit, ps)
                else:
                    uv1, ok = [(0.0, 0.0)] * 3, False
                weathered += ok
                uv0 = [(u0 + (ii / nu) * (u1 - u0), 1.0 - (v0 + (1.0 - jj / nv) * (v1 - v0))) for ii, jj in tri]
                col = [(seed, age, 0.0, 1.0 if ok else 0.0)] * 3
                cm.add_tri(ps, uv0, uv1, col, slot, idx=[vid[k] for k in tri])
    return misses, weathered, 2 * nu * nv


def place_decal(target, man, item, wall, u, z, rot, w, h, opt):
    m = man["items"][item]
    W = w if w is not None else m["size_m"][0]
    H = h if h is not None else m["size_m"][1]
    n, r0, up0 = wall_frame(wall)
    a = math.radians(rot)
    r = r0 * math.cos(a) + up0 * math.sin(a)
    up = up0 * math.cos(a) - r0 * math.sin(a)
    depth = opt.get("depth", 0.04)
    p0 = wall_point(wall, u, z)
    hit = target.cast(p0 + n * depth, -n, depth + 0.12)
    surface = hit[0] if hit is not None else p0
    return {"item": item, "pos": list(surface), "normal": list(n), "right": list(r), "up": list(up), "size": [W, H],
            "uv": m["uv"], "thickness": 0.03}


def fascia_uv1(target):
    """Affine map (lettering plane -> WeatherUV, glTF/Unreal V) of the front and left lit diffusers, for
    the fascia lettering's material in Unreal: uv = A @ (u, z, 1), u = x (front) or y (left). A diffuser
    can be split over several UV islands; the fit uses the island under the middle of its lettering
    and reports the u range it covers (the lettering has to lie inside it)."""
    out = {}
    tf, tl = C.CANOPY_TEXT_FRONT, C.CANOPY_TEXT_LEFT
    for k, (ob, bvh, uv1, mats, weathered, mw) in enumerate(target.objs):
        if ob.name != "SM_Kiosk_Canopy" or uv1 is None:
            continue
        me = ob.data
        R = mw.to_3x3()
        sides = (("front", Vector((0, -1, 0)), 0, (tf["x0"] + tf["x1"]) / 2, (tf["x0"], tf["ring_x"])),
                 ("left", Vector((-1, 0, 0)), 1, (tl["y0"] + tl["y1"]) / 2, (tl["bowl_y"], tl["y0"])))
        for side, nrm, axis, u_mid, span in sides:
            islands = []  # [affine, polygons, u range]
            for p in me.polygons:
                if mats[p.material_index] != "Lightbox_Yellow" or (R @ p.normal).dot(nrm) < 0.99:
                    continue
                cw = mw @ p.center
                ref = (C.CANOPY_Y0 if side == "front" else C.CANOPY_X0) + C.CANOPY_DETAIL["diffuser_inset"]
                if abs(cw[1 - axis] - ref) > 0.02:
                    continue
                li = list(p.loop_indices)[:3]
                P = np.array([[(mw @ me.vertices[me.loops[l].vertex_index].co)[axis], (mw @ me.vertices[me.loops[l].vertex_index].co).z, 1.0]
                              for l in li])
                U = np.array([(uv1.data[l].uv[0], 1.0 - uv1.data[l].uv[1]) for l in li])
                try:
                    Aff = np.linalg.solve(P, U)
                except np.linalg.LinAlgError:
                    continue
                us = [(mw @ me.vertices[v].co)[axis] for v in p.vertices]
                for isl in islands:
                    if np.abs(isl[0] - Aff).max() < 1e-4:
                        isl[1].append(p.index)
                        isl[2] = (min(isl[2][0], min(us)), max(isl[2][1], max(us)))
                        break
                else:
                    islands.append([Aff, [p.index], (min(us), max(us))])
            pick = [isl for isl in islands if isl[2][0] <= u_mid <= isl[2][1]]
            if not pick:
                continue
            isl = max(pick, key=lambda i: len(i[1]))
            rows, uvs = [], []
            for pi in isl[1]:
                for l in me.polygons[pi].loop_indices:
                    v = mw @ me.vertices[me.loops[l].vertex_index].co
                    rows.append((v[axis], v.z, 1.0))
                    uvs.append((uv1.data[l].uv[0], 1.0 - uv1.data[l].uv[1]))
            A = np.array(rows)
            B = np.array(uvs)
            coef, *_ = np.linalg.lstsq(A, B, rcond=None)
            err = float(np.abs(A @ coef - B).max())
            covers = isl[2][0] <= min(span) and max(span) <= isl[2][1]
            out[side] = {"uv": coef.T.tolist(), "max_err": err, "loops": len(rows), "islands": len(islands),
                         "u_range": list(isl[2]), "covers_lettering": covers}
    return out


# ---- the 24h sign -----------------------------------------------------------------------------------

def sign_24h(cm, hw, man):
    """Narrow lightbox clamped to the old lantern pole, wired from a small box on the pole."""
    s = C.SIGN_24H
    px, py = s["pole"]
    yaw = math.radians(s["yaw"])
    n = Vector((-math.sin(yaw), -math.cos(yaw), 0.0))  # face normal
    r = Vector((math.cos(yaw), -math.sin(yaw), 0.0))  # the viewer's right
    up = Vector((0, 0, 1))
    w, h, d = s["w"], s["h"], s["d"]
    gap = s["pole_r"] + 0.022  # clamp plates between the pole and the housing's back
    c = Vector((px, py, s["z"])) + n * (gap + d / 2)
    # housing: a box with its own atlas skin (KG_SignFrame tiles the painted-steel cell)
    corners = {}
    for i, a in enumerate((-w / 2, w / 2)):
        for j, b in enumerate((-d / 2, d / 2)):
            for k, e in enumerate((-h / 2, h / 2)):
                corners[i, j, k] = c + r * a + n * b + up * e
    faces = [((0, 1, 0), (1, 1, 0), (1, 1, 1), (0, 1, 1)),  # front (+n)
             ((1, 0, 0), (0, 0, 0), (0, 0, 1), (1, 0, 1)),  # back
             ((0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)),  # left side
             ((1, 1, 0), (1, 0, 0), (1, 0, 1), (1, 1, 1)),  # right side
             ((0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1)),  # top
             ((0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0))]  # bottom
    for f in faces:
        ps = [corners[q] for q in f]
        e0, e1 = (ps[1] - ps[0]).length, (ps[3] - ps[0]).length
        uv = [(0, 0), (e0, 0), (e0, e1), (0, e1)]
        col = [(0.3, 0.6, 0.0, 0.0)] * 3
        cm.add_tri([ps[0], ps[1], ps[2]], [uv[0], uv[1], uv[2]], [(0, 0)] * 3, col, "KG_SignFrame")
        cm.add_tri([ps[0], ps[2], ps[3]], [uv[0], uv[2], uv[3]], [(0, 0)] * 3, col, "KG_SignFrame")
    # lit face, inset in the front
    m = man["items"]["sign24_face"]
    u0, v0, u1, v1 = m["uv"]
    fi = s["face_inset"]
    fc = c + n * (d / 2 + 0.002)
    fw, fh = w - 2 * fi, h - 2 * fi
    q = [fc + r * (-fw / 2) + up * (-fh / 2), fc + r * (fw / 2) + up * (-fh / 2), fc + r * (fw / 2) + up * (fh / 2),
         fc + r * (-fw / 2) + up * (fh / 2)]
    quv = [(u0, 1 - v1), (u1, 1 - v1), (u1, 1 - v0), (u0, 1 - v0)]
    col = [(0.5, 0.2, 0.0, 0.0)] * 3
    cm.add_tri([q[0], q[1], q[2]], [quv[0], quv[1], quv[2]], [(0, 0)] * 3, col, "KG_Signs")
    cm.add_tri([q[0], q[2], q[3]], [quv[0], quv[2], quv[3]], [(0, 0)] * 3, col, "KG_Signs")
    # frame lip round the face (dark steel), so the face reads recessed
    lip = 0.008
    for a0, a1, b0, b1 in ((-w / 2, w / 2, h / 2 - fi, h / 2), (-w / 2, w / 2, -h / 2, -h / 2 + fi),
                           (-w / 2, -w / 2 + fi, -h / 2, h / 2), (w / 2 - fi, w / 2, -h / 2, h / 2)):
        _obox(hw, c + r * ((a0 + a1) / 2) + up * ((b0 + b1) / 2) + n * (d / 2 + lip / 2), r, n, up, a1 - a0, lip, b1 - b0, "Steel_Dark")
    # clamps: a ring round the pole and a plate to the housing's back, bolted
    pole = Vector((px, py, 0.0))
    for zc in (s["z"] - h / 2 + 0.09, s["z"] + h / 2 - 0.09):
        geo.cylinder(hw, (px, py, zc), s["pole_r"] + 0.006, 0.035, "Steel_Galv_Dull", segments=14, cap=False)
        pc = Vector((px, py, zc)) + n * (s["pole_r"] + gap) / 2
        _obox(hw, pc, r, n, up, 0.05, gap + 0.004, 0.035, "Steel_Galv_Dull")
        for side in (-1, 1):
            b = Vector((px, py, zc)) + n * (gap + 0.002) + r * (side * 0.018)
            geo.cylinder(hw, tuple(b), 0.006, 0.012, "Steel_Dark", segments=6, cap=True,
                         axis="Y" if abs(n.y) > abs(n.x) else "X")
    # junction box on the pole near its top, and a drip-looped cable into the sign's top
    jz = s["pole_top"] - 0.12
    jc = Vector((px, py, jz)) + n * (s["pole_r"] + 0.03)
    _obox(hw, jc, r, n, up, 0.075, 0.055, 0.10, "Steel_Grey")
    _obox(hw, jc - up * 0.055, r, n, up, 0.02, 0.02, 0.012, "Rubber_Black")  # gland
    top = c + up * (h / 2) + r * (w * 0.25)
    geo.cable(hw, tuple(jc - up * 0.06), tuple(top + up * 0.004), 0.05, 0.006, "Cable_Black", 10)
    geo.cylinder(hw, tuple(top + up * 0.006), 0.012, 0.014, "Rubber_Black", segments=10)
    return c, n


def _obox(m, centre, ax, ay, az, sx, sy, sz, mat):
    """Oriented box: centre, unit axes, full sizes."""
    hx, hy, hz = ax * (sx / 2), ay * (sy / 2), az * (sz / 2)
    vs = [centre + hx * a + hy * b + hz * c for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)]
    faces = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    m.add_raw(vs, faces, mat)


# ---- the ramen lantern's lettering ------------------------------------------------------------------

def lantern_lettering(m, B, coll):
    """Vertical lettering bent onto the left lantern's bulging paper (as clutter.lantern_text did), in
    the signage pass's ink, plus a smaller second line beside it."""
    ll = C.LANTERN_L
    x, y, zc0, radius, height = ll["x"], ll["y"], ll["z"], ll["radius"], ll["h"]
    hd = math.radians(C.HERO_CAM["heading_deg"])
    nf = Vector((-math.cos(hd), -math.sin(hd), 0.0))  # facing the camera
    tf = Vector((-nf.y, nf.x, 0.0))
    body_h = height - 0.08
    dg = bpy.context.evaluated_depsgraph_get()
    for body, size, ang, dz in C.LANTERN_LETTERING:
        ob = B.text("_tmp_lantern_text", body, size, (0, 0, 0), (0, 0, 0), B.M["sign_text"], coll, font=B.JP_FONT)
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
        zc = zc0 + dz
        verts = []
        for v in me.vertices:
            z = zc + v.co.y
            tt = min(max((z - (zc0 - body_h / 2)) / body_h, 0.0), 1.0)
            rr = radius * (0.78 + 0.22 * math.sin(math.pi * tt)) + 0.003
            a = v.co.x / rr + ang
            verts.append(Vector((x, y, z)) + nf * (rr * math.cos(a)) + tf * (rr * math.sin(a)))
        m.add_raw(verts, [list(p.vertices) for p in me.polygons], "KG_LanternInk")
        bpy.data.objects.remove(ob, do_unlink=True)
        bpy.data.meshes.remove(me)
