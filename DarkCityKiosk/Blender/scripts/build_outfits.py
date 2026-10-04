"""Builds the crowd's clothing round the mannequin bodies and exports Unreal/RawContent/outfits.glb.

    blender -b --factory-startup -P build_outfits.py -- [--render]

Reads Unreal/RawContent/bodies/<Body>.json (export_bodies.py: the mesh in its reference pose,
each vertex's dominant bone, the joints) and fits, per body:
  Coat_<Body>    knee-length coat: the torso and arms of the body, smoothed and pushed out
                 (sleeves end at the wrists), a turned-up collar, and a flared skirt from the
                 hips to below the knee with a slit at the front. Skirt faces use their own
                 material (Coat_Skirt) so Unreal can weight them to the hips and thighs.
  Hood_<Body>    a rounded hood over the head and neck with the face open
  Hat_Fedora_<Body>, Hat_Cap_<Body>, Hat_Beanie_<Body>   rigid hats (attached to the head bone)
Everything is built in the body's Unreal component space (cm) and written so that the glTF
import lands it back exactly there: Blender (x, y, z) m = Unreal (x, -y, z) / 100.
setup_outfits.py skins the coat and hood with the body's own weights.
"""
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_kiosk_blockout as B  # noqa: E402
from build_city import make_mat  # noqa: E402
from kiosk import geo  # noqa: E402

BLENDER_DIR = os.path.dirname(HERE)
RAW = os.path.join(os.path.dirname(BLENDER_DIR), "Unreal", "RawContent")
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
BODIES = ("Quinn", "Manny")

O = {
    "torso_offset_cm": 2.8, "sleeve_offset_cm": 2.0,
    "torso": {"slices": 26, "segments": 48, "slab_cm": 1.5, "smooth_passes": 3, "vertical_passes": 14, "below_neck_cm": 3.0},
    "sleeve": {"segments": 20, "step_cm": 3.0, "start_cm": 2.0, "end_short_cm": 1.5, "cuff_cm": 0.8},
    "thickness_cm": 0.6,
    "collar": {"below_cm": 7.0, "above_cm": 4.0, "gap_cm": (2.2, 3.6)},
    "skirt": {"top_below_pelvis_cm": 2.0, "overlap_cm": 5.0, "hem_below_knee_cm": 12.0, "pad_cm": 3.5,
              "flare": 1.18, "belt_cm": 4.5, "back_shift_cm": 3.0, "rings": 14, "segments": 44, "slit_deg": 7.0, "slit_from": 0.45},
    "hood": {"offset_cm": 3.8, "neck_offset_cm": 5.5, "smooth_iters": 40, "face_cos": 0.42, "face_z": (-7.0, 15.0)},
}
MATS = {  # rgb, roughness, metallic, emission
    "Coat_Fabric": ((0.02, 0.02, 0.022), 0.7, 0.0, 0.0),
    "Coat_Skirt": ((0.02, 0.02, 0.022), 0.7, 0.0, 0.0),
    "Coat_Belt": ((0.008, 0.008, 0.009), 0.45, 0.0, 0.0),
    "Hood_Fabric": ((0.016, 0.016, 0.018), 0.75, 0.0, 0.0),
    "Hat_Felt": ((0.022, 0.02, 0.019), 0.65, 0.0, 0.0),
    "Hat_Band": ((0.008, 0.008, 0.009), 0.4, 0.0, 0.0),
    "Hat_Knit": ((0.02, 0.022, 0.026), 0.85, 0.0, 0.0),
}
COAT_BONES = ("spine", "pelvis", "clavicle", "upperarm", "lowerarm", "wrist")
HOOD_BONES = ("head", "neck")


def bl(p):
    """Unreal component space (cm) -> Blender (m), so the glTF import lands back on p."""
    return Vector((p[0] / 100.0, -p[1] / 100.0, p[2] / 100.0))


def bone_group(name):
    return name.split("_")[0]


def region(body, groups, extra=None):
    """bmesh of the body triangles whose three vertices are all dominated by bones in `groups`."""
    keep = [bone_group(body["bones"][b]) in groups for b in body["dominant_bone"]]
    if extra:
        keep = [k or extra(i) for i, k in enumerate(keep)]
    bm = bmesh.new()
    remap = {}
    for tri in body["tris"]:
        if all(keep[i] for i in tri):
            vs = []
            for i in tri:
                if i not in remap:
                    remap[i] = bm.verts.new(bl(body["verts"][i]))
                vs.append(remap[i])
            try:
                bm.faces.new(vs)  # the Y flip makes Unreal's winding face outward here
            except ValueError:
                pass
    bm.verts.ensure_lookup_table()
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0002)
    src = {v: i for i, v in remap.items()}
    return bm, src


def inflate(bm, iters, offset_of):
    """Smooth away anatomy, then push each vertex back out along its new normal until it sits at
    least offset_of(vert) metres outside where the body surface was: grooves fill, bumps get
    covered, and nothing ends up inside the body (cloth over a body, not a body cast)."""
    orig = {v: v.co.copy() for v in bm.verts}
    for _ in range(iters):
        bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if not v.is_boundary], factor=0.5,
                              use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.normal_update()
    moves = []
    for v in bm.verts:
        n = v.normal.copy()
        moves.append((v, n * (max(0.0, (orig[v] - v.co).dot(n)) + offset_of(v))))
    for v, d in moves:
        v.co += d


def solidify(bm, cm):
    """Give a shell thickness: an inner copy pushed in along the normals, faces reversed, and a
    rim joining the open edges (bmesh's solidify spikes at the tight folds of the head)."""
    bm.normal_update()
    t = cm / 100.0
    faces = list(bm.faces)
    inner = {v: bm.verts.new(v.co - v.normal * t) for v in list(bm.verts)}
    for f in faces:
        try:
            bm.faces.new([inner[v] for v in reversed(f.verts)])
        except ValueError:
            pass
    for e in [e for e in bm.edges if e.is_boundary and e.verts[0] in inner and e.verts[1] in inner]:
        a, b = e.verts
        f = e.link_faces[0]
        # keep the rim's winding consistent with the outer face
        loop = next(l for l in f.loops if l.edge == e)
        if loop.vert != a:
            a, b = b, a
        try:
            bm.faces.new((b, a, inner[a], inner[b]))
        except ValueError:
            pass


def add_bm(mesh, bm, mat):
    bm.verts.index_update()
    mesh.add_raw([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in bm.faces], mat, smooth=True)
    bm.free()


def cross_section(body, z, half=1.5, xy_filter=None):
    pts = [v for v in body["verts"] if abs(v[2] - z) < half and (xy_filter is None or xy_filter(v))]
    return pts


def hull2d(pts):
    """Convex hull (monotone chain) of 2D points."""
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0:
            lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0:
            up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def ray_radius(hull, c, a):
    """Distance from c to the hull boundary along angle a."""
    dx, dy = math.cos(a), math.sin(a)
    best = 0.0
    for p, q in zip(hull, hull[1:] + hull[:1]):
        ex, ey = q[0] - p[0], q[1] - p[1]
        den = dx * ey - dy * ex
        if abs(den) < 1e-9:
            continue
        t = ((p[0] - c[0]) * ey - (p[1] - c[1]) * ex) / den
        u = ((p[0] - c[0]) * dy - (p[1] - c[1]) * dx) / den
        if t > 0 and -1e-6 <= u <= 1 + 1e-6:
            best = max(best, t)
    return best


def loft(m, rings, mat, cap=False):
    """Quads between consecutive rings (lists of Unreal-cm points, equal length), thickened."""
    lb = bmesh.new()
    vs = [[lb.verts.new(bl(p)) for p in ring] for ring in rings]
    n = len(rings[0])
    for i in range(len(rings) - 1):
        for k in range(n):
            lb.faces.new((vs[i][k], vs[i][(k + 1) % n], vs[i + 1][(k + 1) % n], vs[i + 1][k]))
    bmesh.ops.recalc_face_normals(lb, faces=lb.faces)
    return lb


def torso(body, m, z0, z1):
    """Coat body: horizontal slices of the torso, each wrapped by its convex hull plus the offset."""
    t = O["torso"]
    pts3 = [v for v, b in zip(body["verts"], body["dominant_bone"]) if bone_group(body["bones"][b]) in ("spine", "pelvis", "clavicle")]
    seg, rings, radii = t["segments"], [], []
    zs = [z0 + (z1 - z0) * i / t["slices"] for i in range(t["slices"] + 1)]
    centres = []
    for z in zs:
        sl = [(p[0], p[1]) for p in pts3 if abs(p[2] - z) < t["slab_cm"]]
        h = hull2d(sl)
        c = (sum(p[0] for p in h) / len(h), sum(p[1] for p in h) / len(h))
        centres.append(c)
        radii.append([ray_radius(h, c, 2 * math.pi * k / seg) for k in range(seg)])
    for _ in range(t["smooth_passes"]):  # round the corners a little
        radii = [[(r[k - 1] + 2 * r[k] + r[(k + 1) % seg]) / 4 for k in range(seg)] for r in radii]
    for _ in range(t["vertical_passes"]):  # even out slice-to-slice noise (it read as ribbing)
        radii = [radii[0]] + [[max(radii[i][k], (radii[i - 1][k] + 2 * radii[i][k] + radii[i + 1][k]) / 4) * 0.5
                               + (radii[i - 1][k] + 2 * radii[i][k] + radii[i + 1][k]) / 8 for k in range(seg)]
                              for i in range(1, len(radii) - 1)] + [radii[-1]]
        centres = [centres[0]] + [((centres[i - 1][0] + 2 * centres[i][0] + centres[i + 1][0]) / 4,
                                   (centres[i - 1][1] + 2 * centres[i][1] + centres[i + 1][1]) / 4)
                                  for i in range(1, len(centres) - 1)] + [centres[-1]]
    for z, c, r in zip(zs, centres, radii):
        rings.append([(c[0] + (r[k] + O["torso_offset_cm"]) * math.cos(2 * math.pi * k / seg),
                       c[1] + (r[k] + O["torso_offset_cm"]) * math.sin(2 * math.pi * k / seg), z) for k in range(seg)])
    lb = loft(m, rings, "Coat_Fabric")
    solidify(lb, O["thickness_cm"])
    add_bm(m, lb, "Coat_Fabric")


def sleeve(body, m, side):
    """A tube along shoulder -> elbow -> wrist, sized from the arm's own thickness."""
    s = O["sleeve"]
    J = {k: v["pos"] for k, v in body["joints"].items()}
    chain = [Vector(J[f"upperarm_{side}"]), Vector(J[f"lowerarm_{side}"]), Vector(J[f"hand_{side}"])]
    lens = [(chain[i + 1] - chain[i]).length for i in range(2)]
    total = sum(lens)
    arm = [Vector(v) for v, b in zip(body["verts"], body["dominant_bone"])
           if bone_group(body["bones"][b]) in ("upperarm", "lowerarm", "wrist") and body["bones"][b].endswith(side)]

    def at(u):  # point and direction on the chain at arc length u
        if u <= lens[0]:
            return chain[0] + (chain[1] - chain[0]) * (u / lens[0]), (chain[1] - chain[0]).normalized()
        w = min(1.0, (u - lens[0]) / lens[1])
        return chain[1] + (chain[2] - chain[1]) * w, (chain[2] - chain[1]).normalized()

    n = int(total / s["step_cm"])
    us = [s["start_cm"] + (total - s["start_cm"] - s["end_short_cm"]) * i / n for i in range(n + 1)]
    radii = []
    for u in us:
        p, d = at(u)
        ds = [((v - p) - d * (v - p).dot(d)).length for v in arm if abs((v - p).dot(d)) < s["step_cm"]]
        ds.sort()
        radii.append(ds[int(0.95 * (len(ds) - 1))] if ds else (radii[-1] if radii else 6.0))
    for _ in range(3):
        radii = [radii[0]] + [(radii[i - 1] + 2 * radii[i] + radii[i + 1]) / 4 for i in range(1, len(radii) - 1)] + [radii[-1]]
    rings, seg = [], s["segments"]
    up = Vector((0, 0, 1))
    for i, (u, r) in enumerate(zip(us, radii)):
        p, d = at(u)
        if 0 < i < len(us) - 1:  # bend smoothly through the elbow
            d = ((at(us[i + 1])[0] - at(us[i - 1])[0])).normalized()
        a = d.cross(up).normalized()
        b = d.cross(a).normalized()
        rr = r + O["sleeve_offset_cm"] + (s["cuff_cm"] if i == len(us) - 1 else 0.0)
        rings.append([tuple(p + (a * math.cos(2 * math.pi * k / seg) + b * math.sin(2 * math.pi * k / seg)) * rr) for k in range(seg)])
    lb = loft(m, rings, "Coat_Fabric")
    solidify(lb, O["thickness_cm"])
    add_bm(m, lb, "Coat_Fabric")


def coat(body, m):
    J = {k: v["pos"] for k, v in body["joints"].items()}
    # body of the coat (hips to the base of the neck) and the sleeves
    s = O["skirt"]
    torso(body, m, J["pelvis"][2] - s["top_below_pelvis_cm"], J["neck_01"][2] - O["torso"]["below_neck_cm"])
    for side in ("l", "r"):
        sleeve(body, m, side)
    # collar: a flared band round the base of the neck
    c = O["collar"]
    nz = J["neck_01"][2]
    pts = cross_section(body, nz, 1.5, lambda v: abs(v[0]) < 9)
    cx, cy = sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
    r = sum(math.hypot(p[0] - cx, p[1] - cy) for p in pts) / len(pts)
    seg = 28
    verts, faces = [], []
    for k, (z, gap) in enumerate(((nz - c["below_cm"], c["gap_cm"][0]), (nz + c["above_cm"], c["gap_cm"][1]))):
        for s in range(seg):
            a = 2 * math.pi * s / seg
            verts.append(bl((cx + (r + gap) * math.cos(a), cy + (r + gap) * 1.1 * math.sin(a), z)))
    for s in range(seg):
        faces.append((s, (s + 1) % seg, seg + (s + 1) % seg, seg + s))
    cb = bmesh.new()
    vs = [cb.verts.new(p) for p in verts]
    for f in faces:
        cb.faces.new([vs[i] for i in f])
    bmesh.ops.recalc_face_normals(cb, faces=cb.faces)
    solidify(cb, O["thickness_cm"])
    add_bm(m, cb, "Coat_Fabric")
    # skirt: hips to below the knee, flaring, slit at the front (+Y is forward)
    s = O["skirt"]
    z_top = J["pelvis"][2] - s["top_below_pelvis_cm"]
    z_hem = J["calf_l"][2] - s["hem_below_knee_cm"]
    pts = cross_section(body, z_top, 1.5, lambda v: abs(v[0]) < 30)
    cx = sum(p[0] for p in pts) / len(pts)
    cy = (max(p[1] for p in pts) + min(p[1] for p in pts)) / 2
    rx = max(abs(p[0] - cx) for p in pts) + s["pad_cm"]
    ry_f = max(p[1] - cy for p in pts) + s["pad_cm"]
    ry_b = max(cy - p[1] for p in pts) + s["pad_cm"]
    n, seg = s["rings"], s["segments"]
    slit = math.radians(s["slit_deg"])
    sb = bmesh.new()
    rings = []
    legs = [v for v, b in zip(body["verts"], body["dominant_bone"]) if bone_group(body["bones"][b]) in ("thigh", "calf", "pelvis")]
    # each ring: the flared base ellipse, widened wherever the (A-pose) legs would poke through
    dims = []
    for i in range(n + 1):
        t = i / n
        z = (z_top + s["overlap_cm"]) + (z_hem - z_top - s["overlap_cm"]) * t
        fl = 1.0 + (s["flare"] - 1.0) * t ** 1.4
        yc = cy - s["back_shift_cm"] * t
        sl = [v for v in legs if abs(v[2] - z) < 1.5]
        need_x = max((abs(v[0] - cx) for v in sl), default=0) + s["pad_cm"]
        need_f = max((v[1] - yc for v in sl), default=0) + s["pad_cm"]
        need_b = max((yc - v[1] for v in sl), default=0) + s["pad_cm"]
        dims.append([z, yc, max(rx * fl, need_x), max(ry_f * fl, need_f), max(ry_b * fl, need_b)])
    for i in range(1, len(dims)):  # a coat only gets wider towards the hem
        for j in (2, 3, 4):
            dims[i][j] = max(dims[i][j], dims[i - 1][j])
    for z, yc, ex, ef, eb in dims:
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            ry = ef if math.sin(a) > 0 else eb
            ring.append(sb.verts.new(bl((cx + ex * math.cos(a), yc + ry * math.sin(a), z))))
        rings.append(ring)
    for i in range(n):
        for k in range(seg):
            a_mid = 2 * math.pi * (k + 0.5) / seg
            if i / n >= s["slit_from"] and abs(a_mid - math.pi / 2) < slit:
                continue  # the coat opens at the front below mid-thigh
            sb.faces.new((rings[i][k], rings[i][(k + 1) % seg], rings[i + 1][(k + 1) % seg], rings[i + 1][k]))
    bmesh.ops.recalc_face_normals(sb, faces=sb.faces)
    # recalc points normals consistently; make sure they face outward
    sb.normal_update()
    if sum((f.calc_center_median() - Vector((cx / 100, -cy / 100, f.calc_center_median().z))).dot(f.normal) for f in sb.faces) < 0:
        bmesh.ops.reverse_faces(sb, faces=sb.faces)
    solidify(sb, O["thickness_cm"])
    add_bm(m, sb, "Coat_Skirt")
    # belt over the seam between the body of the coat and the skirt
    zt = z_top + s["overlap_cm"]
    p = 1.06
    ellipse_lathe(m, cx, cy, [(rx * p, zt - s["belt_cm"] / 2), (rx * p + 0.6, zt - s["belt_cm"] / 2 + 0.6),
                              (rx * p + 0.6, zt + s["belt_cm"] / 2 - 0.6), (rx * p, zt + s["belt_cm"] / 2)],
                  1.0, (ry_f + ry_b) / 2 / rx, "Coat_Belt", seg=44, cy_off=(ry_f - ry_b) / 2)


def hood(body, m):
    J = {k: v["pos"] for k, v in body["joints"].items()}
    h = O["hood"]
    bm, _ = region(body, HOOD_BONES)
    hz = J["head"][2]

    def off(v):
        return (h["offset_cm"] if v.co.z * 100 > hz - 2 else h["neck_offset_cm"]) / 100.0

    inflate(bm, h["smooth_iters"], off)
    centre = bl((J["head"][0], J["head"][1] + 2.0, hz + 8.0))
    fwd = Vector((0, -1, 0))  # Unreal +Y (forward) in Blender
    face = [f for f in bm.faces
            if (f.calc_center_median() - centre).normalized().dot(fwd) > h["face_cos"]
            and hz + h["face_z"][0] < f.calc_center_median().z * 100 < hz + h["face_z"][1]]
    bmesh.ops.delete(bm, geom=face, context="FACES")
    # a slight peak at the back of the crown, like a parka hood
    for v in bm.verts:
        d = v.co - centre
        if d.z > 0.04 and d.dot(fwd) < -0.03:
            v.co += -fwd * 0.012 * min(1.0, d.z / 0.1)
    solidify(bm, O["thickness_cm"])
    add_bm(m, bm, "Hood_Fabric")


def head_frame(body):
    J = {k: v["pos"] for k, v in body["joints"].items()}
    head = [body["verts"][i] for i, b in enumerate(body["dominant_bone"]) if body["bones"][b] == "head"]
    top = max(p[2] for p in head)
    band = [p for p in head if top - 9 < p[2] < top - 5]
    cx, cy = sum(p[0] for p in band) / len(band), sum(p[1] for p in band) / len(band)
    rx = max(abs(p[0] - cx) for p in band)
    ry = max(abs(p[1] - cy) for p in band)
    return cx, cy, top, rx, ry, J


def ellipse_lathe(m, cx, cy, profile, sx, sy, mat, seg=32, cy_off=0.0):
    """Lathe in Unreal cm with an elliptical cross-section (sx, sy scale the radius)."""
    verts, faces = [], []
    for r, z in profile:
        for k in range(seg):
            a = 2 * math.pi * k / seg
            verts.append(bl((cx + r * sx * math.cos(a), cy + cy_off + r * sy * math.sin(a), z)))
    for i in range(len(profile) - 1):
        for k in range(seg):
            a, b = i * seg + k, i * seg + (k + 1) % seg
            faces.append((a, b, b + seg, a + seg))
    hb = bmesh.new()
    vs = [hb.verts.new(p) for p in verts]
    for f in faces:
        try:
            hb.faces.new([vs[i] for i in f])
        except ValueError:
            pass
    bmesh.ops.remove_doubles(hb, verts=hb.verts, dist=0.0001)
    bmesh.ops.recalc_face_normals(hb, faces=hb.faces)
    add_bm(m, hb, mat)


def hats(body, coll, mats):
    cx, cy, top, rx, ry, _ = head_frame(body)
    r0 = max(rx, ry) + 1.0
    sx, sy = (rx + 1.0) / r0, (ry + 1.0) / r0
    out = []
    # fedora: pinched crown, band, wide brim
    m = geo.Mesh(f"Hat_Fedora_{body['body']}")
    zb = top - 7.0
    ellipse_lathe(m, cx, cy, [(r0, zb), (r0 + 0.2, zb + 4), (r0 - 0.3, zb + 9), (r0 - 1.5, zb + 11.5), (r0 - 4, zb + 12.3), (0.01, zb + 11.2)],
                  sx, sy, "Hat_Felt")
    ellipse_lathe(m, cx, cy, [(r0 + 0.25, zb + 0.2), (r0 + 0.25, zb + 2.6)], sx, sy, "Hat_Band")
    ellipse_lathe(m, cx, cy, [(r0, zb + 0.3), (r0 + 4, zb + 0.1), (r0 + 6.5, zb + 0.6), (r0 + 6.6, zb + 0.1), (r0 + 4, zb - 0.4), (r0, zb - 0.3)],
                  sx, sy, "Hat_Felt")
    out.append(m.build(coll, mats))
    # flat cap: low crown, short peak at the front
    m = geo.Mesh(f"Hat_Cap_{body['body']}")
    zb = top - 5.5
    ellipse_lathe(m, cx, cy + 1.0, [(r0, zb), (r0 + 0.8, zb + 3.5), (r0 - 1.0, zb + 6.2), (0.01, zb + 7.0)], sx * 1.02, sy * 1.12, "Hat_Felt")
    pb = bmesh.new()
    peak = []
    for k in range(13):
        a = math.pi * (0.25 + 0.5 * k / 12)  # front arc
        inner = (cx + r0 * sx * math.cos(a), cy + 1.0 + r0 * sy * 1.12 * math.sin(a), zb + 0.5)
        outer = (cx + (r0 + 5.5) * sx * math.cos(a), cy + 1.0 + (r0 + 6.5) * sy * math.sin(a), zb - 0.8)
        peak.append((pb.verts.new(bl(inner)), pb.verts.new(bl(outer))))
    for (a0, b0), (a1, b1) in zip(peak, peak[1:]):
        pb.faces.new((a0, a1, b1, b0))
    solidify(pb, 0.5)
    add_bm(m, pb, "Hat_Felt")
    out.append(m.build(coll, mats))
    # beanie: knit dome with a turned-up band
    m = geo.Mesh(f"Hat_Beanie_{body['body']}")
    zb = top - 10.0
    ellipse_lathe(m, cx, cy, [(r0 - 0.3, zb), (r0 + 0.6, zb + 0.3), (r0 + 0.6, zb + 4.0), (r0 + 0.1, zb + 4.3), (r0 + 0.2, zb + 7),
                              (r0 - 1.2, zb + 10.5), (r0 - 4.5, zb + 12.6), (0.01, zb + 13.3)], sx, sy, "Hat_Knit")
    out.append(m.build(coll, mats))
    return out


def main():
    B.reset_scene()
    for name, (rgb, r, mt, e) in MATS.items():
        make_mat(name, rgb, r, mt, e)
    mats = bpy.data.materials
    coll = B.collection("Outfits")
    obs = []
    for name in BODIES:
        with open(os.path.join(RAW, "bodies", f"{name}.json"), encoding="utf-8") as f:
            body = json.load(f)
        m = geo.Mesh(f"Coat_{name}")
        coat(body, m)
        obs.append(m.build(coll, mats))
        m = geo.Mesh(f"Hood_{name}")
        hood(body, m)
        obs.append(m.build(coll, mats))
        obs += hats(body, coll, mats)
        if "--render" in ARGV:  # the body too, for the check render only
            bm, _ = region(body, set(bone_group(b) for b in body["bones"]))
            bm.verts.index_update()
            mb = geo.Mesh(f"Body_{name}")
            mb.add_raw([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in bm.faces], "Hat_Knit", smooth=True)
            bm.free()
            ob = mb.build(coll, mats)
            ob["review_only"] = True
    for ob in obs:
        print(f"{ob.name}: {len(ob.data.polygons)} faces")
    bpy.ops.object.select_all(action="DESELECT")
    for ob in obs:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(RAW, "outfits.glb"), export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True, export_cameras=False, export_lights=False)
    print("exported outfits.glb")
    if "--render" in ARGV:
        from kiosk import review
        # three looks side by side per body: coat + fedora, coat + hood, coat + cap (+ the body)
        looks = [("Coat", "Hat_Fedora"), ("Coat", "Hood"), ("Coat", "Hat_Cap", "Hat_Beanie")]
        for bi, name in enumerate(BODIES):
            for li, parts in enumerate(looks):
                dx = (bi * 3 + li) * 0.9 - 2.2
                for part in list(parts) + ["Body"]:
                    src = bpy.data.objects[f"{part}_{name}"]
                    ob = src.copy()
                    coll.objects.link(ob)
                    ob.location = (dx, 0, 0)
                    if part == "Hat_Beanie":
                        ob.location = (dx, 0, 0.0)
                        ob.hide_render = True
            for part in ("Coat", "Hood", "Hat_Fedora", "Hat_Cap", "Hat_Beanie", "Body"):
                bpy.data.objects[f"{part}_{name}"].hide_render = True
        B.init_shared()
        rc = B.collection("Review")
        scene = bpy.context.scene
        review.setup_scene(scene, rc, mats)
        cam = review.look_camera(rc, "CAM_Outfits", (0.2, -6.5, 1.3), (0.2, 0, 1.0), 35)
        review.render(scene, cam, os.path.join(BLENDER_DIR, "renders", "outfits_check.png"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLENDER_DIR, "outfits.blend"), check_existing=False)


if __name__ == "__main__":
    main()
