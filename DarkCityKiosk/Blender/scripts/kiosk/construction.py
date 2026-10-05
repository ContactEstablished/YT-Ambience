"""Construction pass (2026-10-04, brief 2): the industrial build-up of the walls and the soffit,
exported as its own mesh (SM_Kiosk_Construction).

The kiosk should read as an old steel shell that has been repaired, retrofitted, reinforced and
rewired over decades, through geometry alone (weathering, signage and the cable network come in
later passes). Proportions are locked; everything here is layered onto the approved walls.
Detail comes in three scales that overlap:

  large   the steel posts carrying the service hood, the electrical cabinet, the exhaust fan,
          the kitchen extract, the utility housings
  medium  patch plates, access doors, a blanked-off frame, reinforcement strips, the door
          channel and gussets, unistrut rails, junction and pull boxes, soffit purlins,
          joist end plates, gussets, splice plates, tube drivers, the sign power supply
  small   hex bolts, rivets, mounting tabs, gland stubs, latches, straps

Nothing is mirrored: every box, vent and bracket has its own size, height and style.
Conduit appears only as short stubs and risers that explain where power enters each box;
the cable/pipe network itself is a later pass, and the stubs, rails and boxes are its anchors.
Wall coordinates as in shell.py: u along the wall, z height, w outward from the wall plane.
"""
import math

from mathutils import Euler, Matrix, Vector

import kiosk_config as C
from . import geo, shell
from .shell import WALLS, surface_w, wall_bolts, wall_box, wall_rivets, world

M, FA = C.MASSING, C.FASTENERS
PH, TOP = C.PLATFORM_H, C.BODY_TOP
FRONT, LEFT = WALLS["front"], WALLS["left"]
BASE_TOP = PH + M["base_h"]  # top of the dark base frame
HEADER_Z0 = TOP - M["header_h"]  # underside of the header beam

# Materials introduced in this pass: (rgb, roughness, metallic, emission strength). Darker and duller
# variants separate the layers while the kiosk stays predominantly yellow.
MATERIALS = {
    "Kiosk_YellowPaint_Faded": ((0.58, 0.46, 0.20), 0.45, 0.0, 0.0),  # replacement sheets, plates
    "Steel_Charcoal": ((0.12, 0.12, 0.125), 0.5, 0.25, 0.0),  # painted equipment, posts, channels
    "Steel_Galv_Dull": ((0.31, 0.31, 0.29), 0.55, 0.6, 0.0),  # unistrut, mounting plates, facings
}


def ensure_materials(B):
    import bpy
    for name, (rgb, rough, metal, emit) in MATERIALS.items():
        m = B.mat(name, rgb, emit)
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return bpy.data.materials


# ---- Helpers ----------------------------------------------------------------------------------

def lay(wall_name, u0, u1, z0, z1, w):
    """Record a flat layer on the wall, so parts laid later (tabs, rails, stickers) sit on top of it."""
    shell.LAYOUT.setdefault(wall_name, []).append((u0, u1, z0, z1, w))


def steps(a, b, pitch, jitter=0.0, drop=0.0):
    """Points from a to b about `pitch` apart, nudged by up to `jitter`; a fraction `drop` go
    missing (bolts lost or never refitted)."""
    pts = shell._steps(a, b, pitch)
    out = []
    for i, p in enumerate(pts):
        if 0 < i < len(pts) - 1 and geo.RNG.random() < drop:
            continue
        out.append(p + (geo.jitter(jitter) if 0 < i < len(pts) - 1 else 0.0))
    return out


def ring_pts(u0, u1, z0, z1, pitch, inset):
    """Fastener points round a rectangle's edge, `inset` in from it."""
    a0, a1, b0, b1 = u0 + inset, u1 - inset, z0 + inset, z1 - inset
    pts = [(u, b) for b in (b0, b1) for u in shell._steps(a0, a1, pitch)]
    pts += [(a, z) for a in (a0, a1) for z in shell._steps(b0, b1, pitch)[1:-1]]
    return pts


def tilt_uz(wall, du, dz, deg):
    """In-plane rotation of an offset (du, dz), matching wall_box's tilt for that wall."""
    t = math.radians(deg)
    c, s = math.cos(t), math.sin(t)
    if wall["axis"] == "X":
        return du * c + dz * s, -du * s + dz * c
    return du * c - dz * s, du * s + dz * c


def frame(wall):
    """Proper rotation whose columns are the viewer's right, up and out for a wall seen from outside
    (the left wall's u runs to the viewer's left, so a plain (u, z, w) frame would be mirrored)."""
    out = Vector({"-Y": (0, -1, 0), "+Y": (0, 1, 0), "-X": (-1, 0, 0), "+X": (1, 0, 0)}[wall["normal"]])
    up = Vector((0, 0, 1))
    return Matrix((up.cross(out), up, out)).transposed()


def disc(mesh, wall, u, z, w0, w1, r_out, mat, r_in=0.0, segments=24):
    """Round plate / ring on a wall (axis along the wall normal), from w0 out to w1."""
    rot = frame(wall)
    c = Vector(world(wall, u, z, 0.0))
    import bmesh
    bm = bmesh.new()
    if r_in <= 0:
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments, radius1=r_out, radius2=r_out, depth=w1 - w0)
        bmesh.ops.translate(bm, vec=(0, 0, (w0 + w1) / 2), verts=bm.verts)
    else:
        rings = []
        for r, w in ((r_out, w0), (r_out, w1), (r_in, w1), (r_in, w0)):
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / segments), r * math.sin(2 * math.pi * k / segments), w))
                          for k in range(segments)])
        for a, b in zip(rings, rings[1:] + rings[:1]):
            for k in range(segments):
                j = (k + 1) % segments
                bm.faces.new((a[k], a[j], b[j], b[k]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh.add_bm(bm, mat, True, Matrix.Translation(c) @ rot.to_4x4())


def wall_pipe(mesh, wall, a_uzw, b_uzw, r, mat, segments=10):
    geo.pipe(mesh, world(wall, *a_uzw), world(wall, *b_uzw), r, mat, segments)


def wall_prism(mesh, wall, pts_uz, w0, w1, mat):
    geo.prism(mesh, ([world(wall, u, z, w1) for u, z in pts_uz], [world(wall, u, z, w0) for u, z in pts_uz]), mat)


def stub(mesh, wall, u, z, w, length, r, mat, down=True):
    """Short conduit stub with a lock ring, out of the top or bottom of a box: an anchor for the
    cable pass."""
    sgn = -1 if down else 1
    wall_pipe(mesh, wall, (u, z, w), (u, z + sgn * length, w), r, mat)
    wall_pipe(mesh, wall, (u, z + sgn * 0.004, w), (u, z + sgn * 0.016, w), r * 1.45, "Steel_Dark", 12)


def tabs(mesh, wall_name, u0, u1, z0, z1, sides, mat="Steel_Galv_Dull"):
    """Mounting tabs past a box's edges ('tb' top + bottom or 'lr' sides), each with a bolt,
    lying on whatever the wall surface is under them."""
    wall = WALLS[wall_name]
    parts = []  # (bolt u, bolt z, tab u0, u1, z0, z1)
    if sides == "tb":
        for u in (u0 + 0.25 * (u1 - u0), u1 - 0.25 * (u1 - u0)):
            parts += [(u, z1 + 0.018, u - 0.026, u + 0.026, z1 - 0.01, z1 + 0.036),
                      (u, z0 - 0.018, u - 0.026, u + 0.026, z0 - 0.036, z0 + 0.01)]
    else:
        zc = (z0 + z1) / 2
        for ub, ua, uc in ((u0 - 0.018, u0 - 0.036, u0 + 0.01), (u1 + 0.018, u1 - 0.01, u1 + 0.036)):
            for z in (zc - 0.25 * (z1 - z0), zc + 0.25 * (z1 - z0)):
                parts.append((ub, z, ua, uc, z - 0.026, z + 0.026))
    for bu, bz, a0, a1, b0, b1 in parts:
        w = surface_w(wall_name, a0, a1, b0, b1)
        wall_box(mesh, wall, a0, a1, b0, b1, w - 0.002, w + 0.006, mat, 0.002)
        wall_bolts(mesh, wall, [(bu, bz)], w + 0.006, mat, FA["bolt_small_r"])


def louvres(mesh, wall, u0, u1, z0, z1, w, n, mat="Steel_Dark"):
    for k in range(n):
        z = z0 + (k + 0.5) * (z1 - z0) / n
        wall_box(mesh, wall, u0, u1, z - 0.009, z + 0.009, w, w + 0.012, mat, 0.002, 1, 0.0)


# ---- 1. Fasteners on the existing structure ----------------------------------------------------

def structure_fasteners(m):
    """Bolts along the base frame and the header, columns on the corner angles and the window-bay
    posts, rows on the service hood, and bent corner plates on some corners."""
    d = C.DOOR
    skip = {"left": [(d["y"] - d["w"] / 2 - 0.08, d["y"] + d["w"] / 2 + 0.08)],
            "front": [(C.VENT_GRILLE["x0"] - 0.03, C.VENT_GRILLE["x1"] + 0.03)]}
    for name, wall in WALLS.items():
        u0, u1 = wall["u"]
        pitch = {"front": 0.31, "left": 0.27, "right": 0.36, "back": 0.4}[name]
        pts = [(u, PH + 0.105) for u in steps(u0 + 0.26, u1 - 0.26, pitch, 0.03, 0.12)
               if not any(a < u < b for a, b in skip.get(name, []))]
        wall_bolts(m, wall, pts, M["base_proud"], "Steel_Dark")
        pts = [(u, TOP - M["header_h"] / 2) for u in steps(u0 + 0.24, u1 - 0.24, pitch * 0.85, 0.02, 0.08)]
        wall_bolts(m, wall, pts, M["header_proud"], "Steel_Dark", FA["bolt_small_r"])

    # corner angles: a bolt column down the middle of each flange (on its own wall)
    t = M["corner_t"]
    for (xw, yw), (fx, fy) in M["corners"].items():
        x = C.X0 if xw == "left" else C.X1
        y = C.Y0 if yw == "front" else C.Y1
        sx, sy = (-1 if xw == "left" else 1), (-1 if yw == "front" else 1)
        ox, oy = x + sx * t, y + sy * t
        zs = steps(BASE_TOP + 0.09, HEADER_Z0 - 0.07, geo.RNG.uniform(0.26, 0.34), 0.02)
        geo.bolts(m, [((x + ox - sx * fx) / 2, oy, z) for z in zs], "-Y" if yw == "front" else "+Y", "Kiosk_YellowPaint_Dark",
                  FA["bolt_small_r"])
        zs = steps(BASE_TOP + 0.09, HEADER_Z0 - 0.07, geo.RNG.uniform(0.26, 0.34), 0.02)
        geo.bolts(m, [(ox, (y + oy - sy * fy) / 2, z) for z in zs], "-X" if xw == "left" else "+X", "Kiosk_YellowPaint_Dark",
                  FA["bolt_small_r"])
    # bent plates wrapping two corners at different heights (later repairs)
    for (xw, yw), (z0, z1) in ((("left", "front"), (0.40, 0.64)), (("right", "front"), (1.58, 1.78))):
        x = C.X0 if xw == "left" else C.X1
        sx = -1 if xw == "left" else 1
        ox, oy = x + sx * (t + 0.012), C.Y0 - t - 0.012
        geo.box(m, min(ox, ox - sx * 0.17), max(ox, ox - sx * 0.17), oy, oy + 0.012, z0, z1, "Kiosk_YellowPaint_Faded", 0.003)
        geo.box(m, min(ox, ox - sx * 0.012), max(ox, ox - sx * 0.012), oy, oy + 0.17, z0, z1, "Kiosk_YellowPaint_Faded", 0.003)
        for z in (z0 + 0.05, z1 - 0.05):
            geo.bolts(m, [(ox - sx * 0.11, oy, z)], "-Y", "Steel_Dark", FA["bolt_small_r"])
            geo.bolts(m, [(ox, oy + 0.11, z)], "-X" if xw == "left" else "+X", "Steel_Dark", FA["bolt_small_r"])

    # window-bay posts (different pitches) and the service hood face
    b = M["bay"]
    for (a0, a1), pitch in (((b["x0"], b["x0"] + b["post_w"]), 0.27), ((b["x1"] - b["post_w"], b["x1"]), 0.33)):
        wall_bolts(m, FRONT, [((a0 + a1) / 2, z) for z in steps(b["sill_z1"] + 0.1, HEADER_Z0 - 0.08, pitch, 0.02)],
                   b["proud"], "Kiosk_YellowPaint_Dark", FA["bolt_small_r"])
    hood = M["service_hood"]
    for z in (hood["z0"] + 0.035, hood["z1"] - 0.085):
        wall_bolts(m, FRONT, [(u, z) for u in steps(hood["x0"] + 0.05, hood["x1"] - 0.05, 0.21, 0.015)], hood["proud"],
                   "Steel_Dark", FA["bolt_small_r"])


# ---- 2. Plates, access doors, framed sections, strips -----------------------------------------

def plate(m, wall_name, u0, u1, z0, z1, tilt, mat, fastener, t=0.012):
    """A plate bolted or riveted over whatever is there (sheets, seams, battens)."""
    wall = WALLS[wall_name]
    w0 = surface_w(wall_name, u0, u1, z0, z1)
    wall_box(m, wall, u0, u1, z0, z1, w0 - 0.002, w0 + t, mat, 0.004, 1, tilt)
    lay(wall_name, u0, u1, z0, z1, w0 + t)
    cu, cz = (u0 + u1) / 2, (z0 + z1) / 2
    pitch, inset = (0.075, 0.022) if fastener == "rivet" else (0.13, 0.03)
    pts = []
    for u, z in ring_pts(u0, u1, z0, z1, pitch, inset):
        du, dz = tilt_uz(wall, u - cu, z - cz, tilt)
        pts.append((cu + du, cz + dz))
    if fastener == "rivet":
        wall_rivets(m, wall, pts, w0 + t, mat, FA["rivet_r"])
    else:
        wall_bolts(m, wall, pts, w0 + t, "Steel_Dark", FA["bolt_small_r"])


def access_panel(m, wall_name, u0, u1, z0, z1):
    """Inset maintenance door: a raised riveted frame, a recessed leaf with quarter-turn latches,
    two hinge knuckles and a pull."""
    wall = WALLS[wall_name]
    s = surface_w(wall_name, u0, u1, z0, z1)
    fw, ft = 0.032, 0.02
    for a0, a1, b0, b1 in ((u0, u1, z1 - fw, z1), (u0, u1, z0, z0 + fw), (u0, u0 + fw, z0 + fw, z1 - fw), (u1 - fw, u1, z0 + fw, z1 - fw)):
        wall_box(m, wall, a0, a1, b0, b1, s - 0.002, s + ft, "Kiosk_YellowPaint_Dark", 0.004, 1)
    wall_box(m, wall, u0 + fw + 0.006, u1 - fw - 0.006, z0 + fw + 0.006, z1 - fw - 0.006, s - 0.002, s + 0.005,
             "Kiosk_YellowPaint_Faded", 0.003)
    lay(wall_name, u0, u1, z0, z1, s + ft)
    wall_rivets(m, wall, ring_pts(u0, u1, z0, z1, 0.09, fw / 2), s + ft, "Kiosk_YellowPaint_Dark", FA["rivet_r"])
    for u, z in ((u0 + fw + 0.04, z0 + fw + 0.045), (u0 + fw + 0.04, z1 - fw - 0.045), (u1 - fw - 0.04, (z0 + z1) / 2)):
        disc(m, wall, u, z, s + 0.005, s + 0.016, 0.017, "Steel_Galv_Dull", segments=12)
        wall_box(m, wall, u - 0.013, u + 0.013, z - 0.004, z + 0.004, s + 0.016, s + 0.02, "Steel_Dark")
    for z in (z0 + 0.12, z1 - 0.12):  # hinge knuckles on the right-hand frame edge
        wall_pipe(m, wall, (u1 - 0.006, z - 0.04, s + ft + 0.01), (u1 - 0.006, z + 0.04, s + ft + 0.01), 0.011, "Steel_Dark")


def framed_blank(m, wall_name, u0, u1, z0, z1):
    """An old opening, closed with a plate set in a bolted steel angle frame."""
    wall = WALLS[wall_name]
    s = surface_w(wall_name, u0, u1, z0, z1)
    wall_box(m, wall, u0 + 0.02, u1 - 0.02, z0 + 0.02, z1 - 0.02, s - 0.002, s + 0.008, "Kiosk_YellowPaint_Dark", 0.003)
    fw = 0.04
    for a0, a1, b0, b1 in ((u0, u1, z1 - fw, z1), (u0, u1, z0, z0 + fw), (u0, u0 + fw, z0 + fw, z1 - fw), (u1 - fw, u1, z0 + fw, z1 - fw)):
        wall_box(m, wall, a0, a1, b0, b1, s - 0.002, s + 0.03, "Steel_Dark", 0.004, 1)
    wall_bolts(m, wall, ring_pts(u0, u1, z0, z1, 0.11, fw / 2), s + 0.03, "Steel_Dark", FA["bolt_small_r"])
    lay(wall_name, u0, u1, z0, z1, s + 0.03)
    # a stencilled tag plate, riveted
    wall_box(m, wall, u0 + 0.07, u0 + 0.19, z1 - 0.13, z1 - 0.07, s + 0.008, s + 0.011, "Steel_Galv_Dull", 0.002)


def plates_and_strips(m):
    for wall_name, u0, u1, z0, z1, tilt, mat, fastener in C.PATCH_PLATES:
        plate(m, wall_name, u0, u1, z0, z1, tilt, mat, fastener)
    # the massing pass's repair plates get bolted down too
    for wall_name, u0, u1, z0, z1, proud, tilt, _ in C.REPAIR_PLATES:  # (massing.py lays them on the sheets)
        wall = WALLS[wall_name]
        cu, cz = (u0 + u1) / 2, (z0 + z1) / 2
        pts = [(cu + du, cz + dz) for du, dz in (tilt_uz(wall, u - cu, z - cz, tilt) for u, z in ring_pts(u0, u1, z0, z1, 0.14, 0.03))]
        wall_bolts(m, wall, pts, surface_w(wall_name, cu - 0.01, cu + 0.01, cz - 0.01, cz + 0.01), "Steel_Dark", FA["bolt_small_r"])
    for wall_name, u0, u1, z0, z1 in C.ACCESS_PANELS:
        access_panel(m, wall_name, u0, u1, z0, z1)
    for wall_name, u0, u1, z0, z1 in C.FRAMED_BLANKS:
        framed_blank(m, wall_name, u0, u1, z0, z1)
    for wall_name, u0, u1, z0, z1 in C.H_STRIPS:
        wall = WALLS[wall_name]
        s = surface_w(wall_name, u0, u1, z0, z1)
        wall_box(m, wall, u0, u1, z0, z1, s - 0.002, s + 0.016, "Kiosk_YellowPaint_Dark", 0.004, 2)
        lay(wall_name, u0, u1, z0, z1, s + 0.016)
        wall_bolts(m, wall, [(u, (z0 + z1) / 2) for u in steps(u0 + 0.05, u1 - 0.05, 0.19, 0.02)], s + 0.016, "Kiosk_YellowPaint_Dark",
                   FA["bolt_small_r"])


# ---- 3. The service opening -----------------------------------------------------------------

def service_opening(m):
    """Layers from the wall in: steel posts carrying the hood (with knee brackets under it), the
    jambs with a bolted steel facing, the reveal, and an inner steel frame stepping in at the back
    of the reveal. Around it: an isolator switch on the right post, the kitchen extract, a narrow
    utility housing with a perforated grille, and a service-entry enclosure under the counter."""
    sw, hood = C.SERVICE_WINDOW, M["service_hood"]
    fw, jw, jp = C.SHELL["frame_w"], M["service_jamb_w"], M["service_jamb_proud"]
    pw, pp = C.SERVICE_POSTS["w"], C.SERVICE_POSTS["proud"]
    posts = ((sw["x0"] - fw - jw - pw, sw["x0"] - fw - jw), (sw["x1"] + fw + jw, sw["x1"] + fw + jw + pw))
    for i, (a0, a1) in enumerate(posts):
        uc = (a0 + a1) / 2
        # H-section post: back flange, web, front flange (the web recess reads from the orbit's ends)
        wall_box(m, FRONT, a0, a1, BASE_TOP, hood["z0"], -0.005, 0.014, "Steel_Charcoal", 0.002)
        wall_box(m, FRONT, uc - 0.007, uc + 0.007, BASE_TOP, hood["z0"], 0.014, pp - 0.014, "Steel_Charcoal", 0.002)
        wall_box(m, FRONT, a0, a1, BASE_TOP, hood["z0"], pp - 0.014, pp, "Steel_Charcoal", 0.003)
        wall_box(m, FRONT, a0 - 0.025, a1 + 0.025, BASE_TOP, BASE_TOP + 0.016, -0.005, pp + 0.03, "Steel_Charcoal", 0.003)  # base plate
        geo.bolts(m, [world(FRONT, a0 - 0.012, BASE_TOP + 0.016, pp + 0.012), world(FRONT, a1 + 0.012, BASE_TOP + 0.016, pp + 0.012)], "+Z",
                  "Steel_Dark", FA["bolt_small_r"])
        wall_bolts(m, FRONT, [(uc, z) for z in steps(BASE_TOP + 0.12, hood["z0"] - 0.1, (0.24, 0.29)[i], 0.015)], pp,
                   "Steel_Dark", FA["bolt_small_r"])
        # knee bracket under the hood, in the post's plane
        ub = uc if i == 0 else uc - 0.01
        geo.prism(m, ([world(FRONT, ub + 0.006, z, w) for w, z in ((pp, hood["z0"] - 0.22), (pp, hood["z0"]), (hood["proud"] - 0.02, hood["z0"]))],
                      [world(FRONT, ub - 0.006, z, w) for w, z in ((pp, hood["z0"] - 0.22), (pp, hood["z0"]), (hood["proud"] - 0.02, hood["z0"]))]),
                  "Steel_Charcoal")
    # steel facing on the jamb fronts, lapping over the reveal edge
    lip, ft = C.SERVICE_FACE["lip"], C.SERVICE_FACE["t"]
    for a0, a1, side in ((sw["x0"] - fw - jw - 0.006, sw["x0"] - fw + lip, 1), (sw["x1"] + fw - lip, sw["x1"] + fw + jw + 0.006, -1)):
        wall_box(m, FRONT, a0, a1, C.COUNTER["z"], hood["z0"], jp - 0.002, jp + ft, "Steel_Galv_Dull", 0.003)
        ub = a0 + 0.035 if side == 1 else a1 - 0.035
        wall_bolts(m, FRONT, [(ub, z) for z in steps(C.COUNTER["z"] + 0.07, hood["z0"] - 0.06, 0.15)], jp + ft, "Steel_Dark",
                   FA["bolt_small_r"])
    # inner frame at the back of the reveal (steps in from the reveal lining)
    t, f = M["service_reveal"]["t"], C.SERVICE_INNER_FRAME
    x0, x1, zt = sw["x0"] + t, sw["x1"] - t, sw["z1"] - t
    for a0, a1 in ((x0, x0 + f["w"]), (x1 - f["w"], x1)):
        wall_box(m, FRONT, a0, a1, sw["z0"] + 0.03, zt, f["w0"], f["w1"], "Steel_Charcoal", 0.003)
    wall_box(m, FRONT, x0, x1, zt - f["w"], zt, f["w0"], f["w1"], "Steel_Charcoal", 0.003)

    # isolator switch on the right post's face, a rotary handle, and a conduit stub up toward the hood
    ub = posts[1]
    s = C.SERVICE_SWITCH
    wall_box(m, FRONT, ub[0] - 0.005, ub[1] + 0.01, s["z0"], s["z1"], pp, pp + 0.065, "Steel_Galv_Dull", 0.006, 2)
    uc = (ub[0] + ub[1]) / 2 + 0.002
    disc(m, FRONT, uc, s["z0"] + 0.05, pp + 0.065, pp + 0.08, 0.022, "Steel_Dark", segments=14)
    wall_box(m, FRONT, uc - 0.007, uc + 0.007, s["z0"] + 0.03, s["z0"] + 0.1, pp + 0.08, pp + 0.095, "Plastic_Red", 0.003)
    stub(m, FRONT, uc, s["z1"], pp + 0.032, 0.16, 0.012, "Steel_Dark", down=False)

    # kitchen extract: a box with a sloped rain cap and downward louvres, on a bolted flange
    u0, u1, z0, z1, d = C.KITCHEN_EXHAUST
    sflange = surface_w("front", u0, u1, z0, z1)
    wall_box(m, FRONT, u0 - 0.015, u1 + 0.015, z0 - 0.015, z1 + 0.015, sflange - 0.002, sflange + 0.01, "Steel_Galv_Dull", 0.003)
    lay("front", u0 - 0.015, u1 + 0.015, z0 - 0.015, z1 + 0.015, sflange + 0.01)
    wall_bolts(m, FRONT, ring_pts(u0 - 0.015, u1 + 0.015, z0 - 0.015, z1 + 0.015, 0.12, 0.012), sflange + 0.01, "Steel_Dark",
               FA["bolt_small_r"])
    zb = z0 + 0.08  # louvres below this
    wall_box(m, FRONT, u0, u1, zb, z1, sflange + 0.01, d, "Steel_Charcoal", 0.008, 2)
    for uu0, uu1 in ((u0 - 0.012, u1 + 0.012),):  # rain cap: falls from the wall to the front edge
        geo.prism(m, ([world(FRONT, uu1, z, w) for w, z in ((sflange, z1 + 0.035), (d + 0.025, z1 + 0.005), (d + 0.025, z1 - 0.005), (sflange, z1))],
                      [world(FRONT, uu0, z, w) for w, z in ((sflange, z1 + 0.035), (d + 0.025, z1 + 0.005), (d + 0.025, z1 - 0.005), (sflange, z1))]),
                  "Steel_Charcoal")
    for a0, a1 in ((u0, u0 + 0.012), (u1 - 0.012, u1)):  # side cheeks round the louvre bank
        wall_box(m, FRONT, a0, a1, z0, zb, sflange + 0.01, d, "Steel_Charcoal", 0.002)
    for k in range(4):  # blades angled down and out
        z = z0 + 0.012 + k * (zb - z0 - 0.02) / 3
        geo.box(m, u0 + 0.012, u1 - 0.012, *sorted((FRONT["fixed"] - (sflange + 0.03), FRONT["fixed"] - (d - 0.01))), z - 0.005, z + 0.005,
                "Steel_Dark", 0.0, 1, Euler((math.radians(-35), 0.0, 0.0)))
    wall_box(m, FRONT, u0 + 0.03, u0 + 0.13, z1 - 0.07, z1 - 0.035, d, d + 0.003, "Steel_Galv_Dull")  # rating plate

    # narrow utility housing on a galvanised mounting plate: perforated grille below, a door above
    u0, u1, z0, z1, d = C.FRONT_HOUSING
    s0 = surface_w("front", u0, u1, z0, z1)
    wall_box(m, FRONT, u0 - 0.015, u1 + 0.015, z0 - 0.06, z1 + 0.06, s0 - 0.002, s0 + 0.008, "Steel_Galv_Dull", 0.003)
    lay("front", u0 - 0.015, u1 + 0.015, z0 - 0.06, z1 + 0.06, s0 + 0.008)
    wall_bolts(m, FRONT, [(u0 - 0.002, z0 - 0.035), (u1 + 0.002, z0 - 0.035), (u0 - 0.002, z1 + 0.035), (u1 + 0.002, z1 + 0.035)],
               s0 + 0.008, "Steel_Dark", FA["bolt_small_r"])
    wall_box(m, FRONT, u0, u1, z0, z1, s0 + 0.008, d, "Steel_Charcoal", 0.01, 2)
    gz0, gz1 = z0 + 0.06, z0 + 0.38
    wall_box(m, FRONT, u0 + 0.025, u1 - 0.025, gz0, gz1, d - 0.012, d + 0.001, "Steel_Dark", 0.002)  # recess behind the grille
    for k in range(9):  # grille: a mesh of thin bars
        z = gz0 + 0.02 + k * (gz1 - gz0 - 0.04) / 8
        wall_box(m, FRONT, u0 + 0.025, u1 - 0.025, z - 0.004, z + 0.004, d - 0.004, d + 0.004, "Steel_Galv_Dull")
    for k in range(6):
        u = u0 + 0.035 + k * (u1 - u0 - 0.07) / 5
        wall_box(m, FRONT, u - 0.004, u + 0.004, gz0, gz1, d - 0.004, d + 0.006, "Steel_Galv_Dull")
    wall_box(m, FRONT, u0 + 0.02, u1 - 0.02, gz1 + 0.03, gz1 + 0.036, d - 0.004, d + 0.002, "Steel_Dark")  # door seam
    wall_box(m, FRONT, u1 - 0.05, u1 - 0.035, gz1 + 0.2, gz1 + 0.32, d, d + 0.03, "Steel_Dark", 0.004)  # handle
    for z in (gz1 + 0.08, z1 - 0.08):
        wall_pipe(m, FRONT, (u0 + 0.004, z - 0.03, d + 0.008), (u0 + 0.004, z + 0.03, d + 0.008), 0.009, "Steel_Dark")
    wall_box(m, FRONT, u0 + 0.04, u1 - 0.07, z1 - 0.12, z1 - 0.07, d, d + 0.003, "Paper_White")  # label
    for u in (u0 + 0.06, u1 - 0.07):  # glands below; a riser into the wall conduit above
        stub(m, FRONT, u, z0, d / 2, 0.06, 0.014, "Steel_Dark")
    uc = (u0 + u1) / 2
    zc = C.BODY_TOP - C.SHELL["topbeam_h"] - 0.05  # the wall conduit (openings.front_conduit)
    wall_pipe(m, FRONT, (uc, z1, 0.07), (uc, zc - 0.03, 0.07), 0.014, "Steel_Dark")
    wall_box(m, FRONT, uc - 0.03, uc + 0.03, zc - 0.045, zc + 0.03, 0.02, 0.1, "Steel_Galv_Dull", 0.006, 2)  # LB fitting

    # service-entry enclosure under the counter: two doors, slots, gland plate with pipe stubs
    u0, u1, z0, z1, d = C.SERVICE_ENTRY
    s1 = surface_w("front", u0, u1, z0, z1)
    wall_box(m, FRONT, u0 - 0.04, u1 + 0.04, z0 - 0.04, z1 + 0.04, s1 - 0.002, s1 + 0.008, "Steel_Galv_Dull", 0.003)
    lay("front", u0 - 0.04, u1 + 0.04, z0 - 0.04, z1 + 0.04, s1 + 0.008)
    wall_bolts(m, FRONT, [(u0 - 0.022, z0 - 0.022), (u1 + 0.022, z0 - 0.022), (u0 - 0.022, z1 + 0.022), (u1 + 0.022, z1 + 0.022)],
               s1 + 0.008, "Steel_Dark", FA["bolt_small_r"])
    wall_box(m, FRONT, u0, u1, z0, z1, s1 + 0.008, d, "Steel_Charcoal", 0.012, 2)
    um = (u0 + u1) / 2 + 0.04
    wall_box(m, FRONT, um - 0.003, um + 0.003, z0 + 0.02, z1 - 0.02, d - 0.004, d + 0.002, "Steel_Dark")
    for u in (um - 0.035, um + 0.035):
        wall_box(m, FRONT, u - 0.007, u + 0.007, (z0 + z1) / 2 - 0.05, (z0 + z1) / 2 + 0.05, d, d + 0.028, "Steel_Dark", 0.003)
    for k in range(5):
        z = z0 + 0.06 + k * 0.035
        wall_box(m, FRONT, um + 0.07, u1 - 0.05, z - 0.006, z + 0.006, d - 0.002, d + 0.002, "Rubber_Black")
    wall_box(m, FRONT, u0 + 0.05, u0 + 0.17, z1 - 0.09, z1 - 0.05, d, d + 0.003, "Stock_Yellow")  # warning label
    for u in (u0 + 0.10, u0 + 0.22):
        wall_pipe(m, FRONT, (u, z0, 0.06), (u, BASE_TOP + 0.012, 0.06), 0.018, "Steel_Galv_Dull", 12)
        wall_pipe(m, FRONT, (u, BASE_TOP + 0.012, 0.06), (u, BASE_TOP + 0.03, 0.06), 0.026, "Steel_Dark", 12)
    stub(m, FRONT, u1 - 0.08, z0, 0.07, 0.05, 0.012, "Steel_Dark")


# ---- 4. The door wall ----------------------------------------------------------------------

def unistrut(m, wall, u0, u1, z0, z1, w0, depth=0.035):
    """Galvanised strut channel (slot facing out), bolted to the wall at both ends."""
    wall_box(m, wall, u0, u1, z0, z1, w0 - 0.002, w0 + depth, "Steel_Galv_Dull", 0.003)
    if u1 - u0 > z1 - z0:  # horizontal
        zc = (z0 + z1) / 2
        wall_box(m, wall, u0 + 0.01, u1 - 0.01, zc - 0.009, zc + 0.009, w0 + depth - 0.006, w0 + depth + 0.001, "Steel_Dark")
        wall_bolts(m, wall, [(u0 + 0.03, zc), (u1 - 0.03, zc)], w0 + depth, "Steel_Dark", FA["bolt_small_r"])
    else:
        uc = (u0 + u1) / 2
        wall_box(m, wall, uc - 0.009, uc + 0.009, z0 + 0.01, z1 - 0.01, w0 + depth - 0.006, w0 + depth + 0.001, "Steel_Dark")
        wall_bolts(m, wall, [(uc, z0 + 0.03), (uc, z1 - 0.03)], w0 + depth, "Steel_Dark", FA["bolt_small_r"])


def door_wall(m):
    d, e = C.DOOR, C.ELEC_CABINET
    # electrical cabinet on two unistrut rails, with a rain hood, hinged door, louvres, gland plate
    # and two conduit risers up into the canopy (where its supply comes from)
    rt, dep = e["rail_t"], e["depth"]
    u0, u1, z0, z1 = e["u0"], e["u1"], e["z0"], e["z1"]
    for z in (z0 + 0.11, z1 - 0.13):
        unistrut(m, LEFT, u0 - 0.03, u1 + 0.07, z - 0.021, z + 0.021, surface_w("left", u0, u1 + 0.07, z - 0.02, z + 0.02))
    w0 = rt + surface_w("left", u0, u1, z0, z1)
    wall_box(m, LEFT, u0, u1, z0, z1, w0, w0 + dep, "Steel_Charcoal", 0.012, 2)
    wf = w0 + dep
    for a0, a1, b0, b1 in ((u0 + 0.025, u1 - 0.025, z1 - 0.03, z1 - 0.024), (u0 + 0.025, u1 - 0.025, z0 + 0.024, z0 + 0.03),
                           (u0 + 0.024, u0 + 0.03, z0 + 0.03, z1 - 0.03), (u1 - 0.03, u1 - 0.024, z0 + 0.03, z1 - 0.03)):
        wall_box(m, LEFT, a0, a1, b0, b1, wf - 0.004, wf + 0.002, "Steel_Dark")  # door seam
    # handle + lock on the edge nearer the door (low u), hinge knuckles on the far edge
    wall_box(m, LEFT, u0 + 0.045, u0 + 0.065, (z0 + z1) / 2 - 0.09, (z0 + z1) / 2 + 0.09, wf, wf + 0.03, "Steel_Galv_Dull", 0.004)
    disc(m, LEFT, u0 + 0.055, (z0 + z1) / 2 + 0.14, wf, wf + 0.012, 0.016, "Steel_Galv_Dull", segments=12)
    for z in (z0 + 0.12, (z0 + z1) / 2, z1 - 0.12):
        wall_pipe(m, LEFT, (u1 - 0.004, z - 0.045, wf - 0.005), (u1 - 0.004, z + 0.045, wf - 0.005), 0.012, "Steel_Dark")
    louvres(m, LEFT, u0 + 0.08, u1 - 0.08, z0 + 0.06, z0 + 0.2, wf - 0.004, 4)
    wall_box(m, LEFT, u0 + 0.12, u1 - 0.12, z1 - 0.16, z1 - 0.09, wf, wf + 0.003, "Stock_Yellow")  # hazard label
    geo.prism(m, ([world(LEFT, u0 - 0.025, z, w) for w, z in ((w0 - 0.01, z1 + 0.065), (wf + 0.03, z1 + 0.012), (wf + 0.03, z1), (w0 - 0.01, z1))],
                  [world(LEFT, u1 + 0.025, z, w) for w, z in ((w0 - 0.01, z1 + 0.065), (wf + 0.03, z1 + 0.012), (wf + 0.03, z1), (w0 - 0.01, z1))]),
              "Steel_Charcoal")  # rain hood
    wall_box(m, LEFT, u0 + 0.03, u1 - 0.03, z0 - 0.018, z0, w0 + 0.02, wf - 0.02, "Steel_Dark", 0.003)  # gland plate
    for u in (u0 + 0.08, u0 + 0.19, u1 - 0.09):
        stub(m, LEFT, u, z0 - 0.018, (w0 + wf) / 2, 0.055, 0.015, "Steel_Dark")
    for u, w in ((u0 + 0.12, w0 + 0.06), (u0 + 0.26, w0 + 0.11)):
        wall_pipe(m, LEFT, (u, z1 + 0.04, w), (u, TOP, w), 0.016, "Steel_Dark", 12)
        wall_box(m, LEFT, u - 0.03, u + 0.03, HEADER_Z0 + 0.03, HEADER_Z0 + 0.06, M["header_proud"], w + 0.02, "Steel_Galv_Dull")  # strap

    # exhaust fan below the cabinet: square bolted mount plate, shroud, guard rings, spokes, blades
    f = C.FAN_COVER
    u, z, r, h = f["u"], f["z"], f["r"], f["plate"]
    s = surface_w("left", u - h, u + h, z - h, z + h)
    wall_box(m, LEFT, u - h, u + h, z - h, z + h, s - 0.002, s + 0.012, "Steel_Galv_Dull", 0.004)
    lay("left", u - h, u + h, z - h, z + h, s + 0.012)
    wall_bolts(m, LEFT, [(u + a * (h - 0.03), z + b * (h - 0.03)) for a in (-1, 1) for b in (-1, 1)], s + 0.012, "Steel_Dark")
    wall_bolts(m, LEFT, [(u, z + h - 0.03), (u, z - h + 0.03), (u - h + 0.03, z), (u + h - 0.03, z)], s + 0.012, "Steel_Dark",
               FA["bolt_small_r"])
    wb = s + 0.012
    disc(m, LEFT, u, z, wb, wb + 0.075, r, "Steel_Charcoal", r_in=r - 0.022, segments=32)  # shroud
    disc(m, LEFT, u, z, wb, wb + 0.006, r - 0.02, "Steel_Dark", segments=32)  # dark throat
    for k in range(5):  # blades, pitched
        a = 2 * math.pi * k / 5 + 0.3
        ca, sa = math.cos(a), math.sin(a)
        pts = []
        for rr, side in ((0.045, -1), (r - 0.035, -1), (r - 0.035, 1), (0.045, 1)):
            half = 0.035 if rr > 0.1 else 0.02
            pts.append((u + rr * ca - side * half * sa, z + rr * sa + side * half * ca, wb + 0.03 + side * 0.012))
        geo.prism(m, ([world(LEFT, pu, pz, pw) for pu, pz, pw in pts], [world(LEFT, pu, pz, pw - 0.005) for pu, pz, pw in pts]),
                  "Steel_Grey")
    disc(m, LEFT, u, z, wb, wb + 0.06, 0.045, "Steel_Dark", segments=16)  # hub
    for rr in (0.07, 0.125, r - 0.01):  # guard rings
        disc(m, LEFT, u, z, wb + 0.07, wb + 0.078, rr + 0.005, "Steel_Galv_Dull", r_in=rr - 0.005, segments=32)
    for k in range(8):  # guard spokes
        a = 2 * math.pi * k / 8
        p0 = (u + 0.03 * math.cos(a), z + 0.03 * math.sin(a), wb + 0.074)
        p1 = (u + (r - 0.005) * math.cos(a), z + (r - 0.005) * math.sin(a), wb + 0.074)
        wall_pipe(m, LEFT, p0, p1, 0.004, "Steel_Galv_Dull", 6)

    # pull box on a unistrut riser beside the door, with a conduit up into the canopy and a stub down
    pb = C.PULL_BOX
    ru = pb["riser_u"]
    s = surface_w("left", ru - 0.021, ru + 0.021, BASE_TOP + 0.7, HEADER_Z0)
    unistrut(m, LEFT, ru - 0.021, ru + 0.021, pb["z0"] - 0.42, HEADER_Z0 - 0.01, s)
    wb = s + 0.035
    wall_box(m, LEFT, pb["u0"], pb["u1"], pb["z0"], pb["z1"], wb, wb + pb["depth"], "Steel_Grey", 0.008, 2)
    wall_box(m, LEFT, pb["u0"] + 0.012, pb["u1"] - 0.012, pb["z0"] + 0.012, pb["z1"] - 0.012, wb + pb["depth"], wb + pb["depth"] + 0.006,
             "Steel_Grey", 0.003)  # cover
    wall_rivets(m, LEFT, ring_pts(pb["u0"], pb["u1"], pb["z0"], pb["z1"], 0.2, 0.024), wb + pb["depth"] + 0.006, "Steel_Dark",
                FA["rivet_r"])
    wc = wb + pb["depth"] / 2
    wall_pipe(m, LEFT, (ru, pb["z1"], wc), (ru, TOP, wc), 0.014, "Steel_Dark")
    stub(m, LEFT, ru + 0.04, pb["z0"], wc, 0.09, 0.013, "Steel_Dark")
    for z in (pb["z0"] - 0.3, pb["z1"] + 0.17):  # strut clamps waiting for the cable pass
        wall_box(m, LEFT, ru - 0.03, ru + 0.03, z - 0.012, z + 0.012, wb - 0.002, wb + 0.03, "Steel_Galv_Dull", 0.003)

    # door frame reinforcement: a steel channel up the hinge side, gussets at both top corners,
    # strap hinges across the leaf
    ch = C.DOOR_CHANNEL
    dp = ch["depth"]
    for a0, a1 in ((ch["u0"], ch["u0"] + 0.01), (ch["u1"] - 0.01, ch["u1"])):
        wall_box(m, LEFT, a0, a1, BASE_TOP, HEADER_Z0, -0.005, dp, "Steel_Charcoal", 0.002)
    wall_box(m, LEFT, ch["u0"], ch["u1"], BASE_TOP, HEADER_Z0, dp - 0.012, dp, "Steel_Charcoal", 0.003)
    wall_bolts(m, LEFT, [((ch["u0"] + ch["u1"]) / 2, z) for z in steps(BASE_TOP + 0.1, HEADER_Z0 - 0.08, 0.26, 0.02)], dp,
               "Steel_Dark", FA["bolt_small_r"])
    ya, yb = d["y"] - d["w"] / 2 - 0.06, ch["u1"]
    for corner, pts_uz in (("latch", [(ya, HEADER_Z0), (ya - 0.2, HEADER_Z0), (ya, HEADER_Z0 - 0.19)]),
                           ("hinge", [(yb, HEADER_Z0), (yb + 0.17, HEADER_Z0), (yb, HEADER_Z0 - 0.16)])):
        w0 = 0.035 if corner == "latch" else 0.02
        wall_prism(m, LEFT, pts_uz, w0, w0 + 0.012, "Kiosk_YellowPaint_Dark")
        cu = sum(p[0] for p in pts_uz) / 3
        cz = sum(p[1] for p in pts_uz) / 3
        wall_bolts(m, LEFT, [(cu, cz), ((pts_uz[0][0] + pts_uz[1][0]) / 2, HEADER_Z0 - 0.025), (pts_uz[0][0] + (0.025 if corner == "hinge" else -0.025), cz - 0.03)],
                   w0 + 0.012, "Steel_Dark", FA["bolt_small_r"])
    hinge_u = d["y"] + d["w"] / 2 - 0.006
    for z, length in ((PH + 0.3, 0.33), (PH + 1.0, 0.33), (PH + 1.68, 0.19)):  # the top one stops short of the window
        wall_box(m, LEFT, hinge_u - length, hinge_u, z - 0.026, z + 0.026, 0.018, 0.038, "Steel_Dark", 0.004)
        wall_bolts(m, LEFT, [(hinge_u - k, z) for k in (0.07, 0.17, 0.28) if k < length - 0.02], 0.038, "Steel_Dark", 0.011)
    # rivets round the leaf's raised border (openings.door: inset 0.07, 0.008 proud of the leaf)
    yi0, yi1 = d["y"] - d["w"] / 2 + 0.07, d["y"] + d["w"] / 2 - 0.07
    zi0, zi1 = PH + 0.07, PH + d["h"] - 0.07
    wall_rivets(m, LEFT, [p for p in ring_pts(yi0, yi1, zi0, zi1, 0.11, 0.0125)
                          if not (p[0] > hinge_u - 0.35 and any(abs(p[1] - z) < 0.04 for z in (PH + 0.3, PH + 1.0, PH + 1.68)))],
                0.026, "Kiosk_YellowPaint_Dark", 0.008)

    # mounting tabs on the existing wall boxes (some top/bottom, some at the sides)
    for (name, a0, a1, z0, z1, _), sides in zip(C.LEFT_WALL_BOXES, ("lr", "tb", "tb")):
        tabs(m, "left", a0, a1, z0, z1, sides)
    for name, wall_name, a0, a1, z0, z1, _ in C.WALL_HOUSINGS:
        if wall_name == "left":
            tabs(m, "left", a0, a1, z0, z1, "tb", "Steel_Dark")


# ---- 5. Under the canopy -----------------------------------------------------------------------

def soffit(m):
    """Purlins parallel to the fascia, unistrut rails carrying the soffit conduits on hanger rods,
    extra joists beyond the tube runs, bolted end plates and cleats where joists meet the edge beam
    and the header, gussets under the edge beam, splice plates on its face, tube drivers hung from
    the purlins, the sign power supply strapped to the corner brace and a controller box."""
    sf, F = C.SOFFIT_FRAME, C.FASCIA
    CB, dp = C.CANOPY_BOTTOM, F["depth"]
    by0, bx0 = C.CANOPY_Y0 + dp, C.CANOPY_X0 + dp  # inner faces of the front and left edge beams
    bx1, by1 = C.CANOPY_X1 - dp, C.CANOPY_Y1 - dp  # (right and back)
    hy, hx = C.Y0 - M["header_proud"], C.X0 - M["header_proud"]  # header faces
    ph, pwid = sf["purlin_h"], sf["purlin_w"]
    geo.ibeam(m, "X", sf["purlin_front_y"], bx0, bx1, CB - ph, CB, "Steel_Dark", pwid, 0.008, 0.008)
    geo.ibeam(m, "Y", sf["purlin_left_x"], by0, by1, CB - ph, CB, "Steel_Dark", pwid, 0.008, 0.008)

    jh = C.SOFFIT_JOIST_H
    for x in sf["extra_joists"]["x"]:
        geo.ibeam(m, "Y", x, by0, C.Y0, CB - jh, CB, "Steel_Dark")
    for y in sf["extra_joists"]["y"]:
        geo.ibeam(m, "X", y, bx0, C.X0, CB - jh, CB, "Steel_Dark")
    # end plates on the edge beam and cleats on the header, for every joist
    for x in list(C.SOFFIT_JOISTS["x"]) + sf["extra_joists"]["x"]:
        geo.box(m, x - 0.07, x + 0.07, by0, by0 + 0.012, CB - jh - 0.005, CB, "Steel_Dark", 0.002)
        geo.bolts(m, [(x + a, by0 + 0.012, z) for a in (-0.045, 0.045) for z in (CB - jh + 0.02, CB - 0.03)], "+Y", "Steel_Dark",
                  FA["bolt_small_r"])
        geo.box(m, x - 0.065, x + 0.065, hy - 0.012, hy, HEADER_Z0 + 0.005, CB - 0.005, "Steel_Dark", 0.002)
        geo.bolts(m, [(x + a, hy - 0.012, z) for a in (-0.042, 0.042) for z in (HEADER_Z0 + 0.03, CB - 0.03)], "-Y", "Steel_Dark",
                  FA["bolt_small_r"])
    for y in list(C.SOFFIT_JOISTS["y"]) + sf["extra_joists"]["y"]:
        geo.box(m, bx0, bx0 + 0.012, y - 0.07, y + 0.07, CB - jh - 0.005, CB, "Steel_Dark", 0.002)
        geo.bolts(m, [(bx0 + 0.012, y + a, z) for a in (-0.045, 0.045) for z in (CB - jh + 0.02, CB - 0.03)], "+X", "Steel_Dark",
                  FA["bolt_small_r"])
        geo.box(m, hx - 0.012, hx, y - 0.065, y + 0.065, HEADER_Z0 + 0.005, CB - 0.005, "Steel_Dark", 0.002)
        geo.bolts(m, [(hx - 0.012, y + a, z) for a in (-0.042, 0.042) for z in (HEADER_Z0 + 0.03, CB - 0.03)], "-X", "Steel_Dark",
                  FA["bolt_small_r"])
    # gussets under the edge beams (only where no tube hangs)
    gz0 = C.FASCIA_Z0 + 0.01
    for x in (-3.00, -0.96, 0.66, 2.55):
        geo.prism(m, ([(x + 0.006, by0, gz0), (x + 0.006, by0, CB), (x + 0.006, by0 + 0.12, CB)],
                      [(x - 0.006, by0, gz0), (x - 0.006, by0, CB), (x - 0.006, by0 + 0.12, CB)]), "Steel_Dark")
    for y in (-2.05, -0.15, 1.55):
        geo.prism(m, ([(bx0, y + 0.006, gz0), (bx0, y + 0.006, CB), (bx0 + 0.12, y + 0.006, CB)],
                      [(bx0, y - 0.006, gz0), (bx0, y - 0.006, CB), (bx0 + 0.12, y - 0.006, CB)]), "Steel_Dark")
    # splice plates on the edge beam's outer face (dark band under the lit face)
    fy, fx = C.CANOPY_Y0 - F["beam_proud"], C.CANOPY_X0 - F["beam_proud"]
    z0, z1 = C.FASCIA_Z0 + F["lip_h"] + 0.005, C.FACE_Z0 - 0.008
    for x in sf["splice_front_x"]:
        geo.box(m, x - 0.06, x + 0.06, fy - 0.012, fy, z0, z1, "Steel_Dark", 0.003)
        geo.bolts(m, [(x + a, fy - 0.012, z) for a in (-0.035, 0.035) for z in (z0 + 0.025, z1 - 0.025)], "-Y", "Steel_Dark",
                  FA["bolt_small_r"])
    for y in sf["splice_left_y"]:
        geo.box(m, fx - 0.012, fx, y - 0.06, y + 0.06, z0, z1, "Steel_Dark", 0.003)
        geo.bolts(m, [(fx - 0.012, y + a, z) for a in (-0.035, 0.035) for z in (z0 + 0.025, z1 - 0.025)], "-X", "Steel_Dark",
                  FA["bolt_small_r"])

    # unistrut rails under the conduits, on hanger rods, with a clamp over each conduit
    rz0, rz1 = sf["rail_z"]
    py, px = sf["purlin_front_y"] + pwid / 2, sf["purlin_left_x"] + pwid / 2
    for x in sf["rails_front_x"]:
        geo.box(m, x - 0.0205, x + 0.0205, py, hy, rz0, rz1, "Steel_Galv_Dull", 0.003)
        geo.box(m, x - 0.009, x + 0.009, py + 0.01, hy - 0.01, rz0 - 0.001, rz0 + 0.005, "Steel_Dark")
        for y in (py + 0.025, hy - 0.025):
            geo.pipe(m, (x, y, rz1), (x, y, CB), 0.005, "Steel_Galv_Dull", 6)
        for y in (C.Y0 - 0.14, C.Y0 - 0.22):
            geo.box(m, x - 0.012, x + 0.012, y - 0.02, y + 0.02, rz1, CB - 0.012, "Steel_Galv_Dull", 0.002)
    for y in sf["rails_left_y"]:
        geo.box(m, px, hx, y - 0.0205, y + 0.0205, rz0, rz1, "Steel_Galv_Dull", 0.003)
        geo.box(m, px + 0.01, hx - 0.01, y - 0.009, y + 0.009, rz0 - 0.001, rz0 + 0.005, "Steel_Dark")
        for x in (px + 0.025, hx - 0.025):
            geo.pipe(m, (x, y, rz1), (x, y, CB), 0.005, "Steel_Galv_Dull", 6)
        geo.box(m, C.X0 - 0.14 - 0.02, C.X0 - 0.14 + 0.02, y - 0.012, y + 0.012, rz1, CB - 0.012, "Steel_Galv_Dull", 0.002)

    # tube drivers hung under the purlins, each with a gland at one end
    for side, a0, a1 in sf["drivers"]:
        if side == "front":
            y = sf["purlin_front_y"]
            geo.box(m, a0, a1, y - 0.035, y + 0.035, CB - ph - 0.075, CB - ph, "Steel_Grey", 0.006, 2)
            geo.cylinder(m, (a1 + 0.012, y, CB - ph - 0.035), 0.012, 0.024, "Rubber_Black", axis="X", segments=10)
        else:
            x = sf["purlin_left_x"]
            geo.box(m, x - 0.035, x + 0.035, a0, a1, CB - ph - 0.075, CB - ph, "Steel_Grey", 0.006, 2)
            geo.cylinder(m, (x, a1 + 0.012, CB - ph - 0.035), 0.012, 0.024, "Rubber_Black", axis="Y", segments=10)

    # the sign power supply, strapped under the diagonal corner brace, with a red pilot lamp
    ex, ey = bx0 - C.X0, by0 - C.Y0
    length = math.hypot(ex, ey)
    dx, dy = ex / length, ey / length
    s = sf["psu_along_brace"]
    cx, cy = C.X0 + dx * s, C.Y0 + dy * s
    ang = Euler((0.0, 0.0, math.atan2(dy, dx)))
    zb = CB - jh - 0.01  # underside of the brace
    geo.box(m, cx - 0.17, cx + 0.17, cy - 0.10, cy + 0.10, zb - 0.125, zb - 0.005, "Steel_Charcoal", 0.01, 2, ang)
    for a in (-0.1, 0.1):
        geo.box(m, cx + dx * a - 0.012, cx + dx * a + 0.012, cy + dy * a - 0.105, cy + dy * a + 0.105, zb - 0.13, CB,
                "Steel_Galv_Dull", 0.002, 1, ang)
    nx, ny = -dy, dx  # across the brace
    geo.cylinder(m, (cx + nx * 0.105 + dx * 0.08, cy + ny * 0.105 + dy * 0.08, zb - 0.06), 0.012, 0.02, "Button_Lit_Red",
                 axis="Z", segments=10)
    geo.cylinder(m, (cx - dx * 0.175, cy - dy * 0.175, zb - 0.065), 0.014, 0.03, "Rubber_Black", axis="Z", segments=10)

    # controller box by the left wall under the conduit, with a gland up into it
    x0, x1, y0, y1, z0, z1 = sf["controller"]
    geo.box(m, x0, x1, y0, y1, z0, z1, "Steel_Grey", 0.008, 2)
    geo.box(m, x0 - 0.004, x0, y0 + 0.02, y1 - 0.02, z0 + 0.02, z1 - 0.02, "Steel_Dark")
    geo.pipe(m, ((x0 + x1) / 2 + 0.035, (y0 + y1) / 2, z1), ((x0 + x1) / 2 + 0.035, (y0 + y1) / 2, CB - 0.03), 0.011, "Steel_Dark")


def build(coll, materials):
    geo.reseed(8086)
    m = geo.Mesh("Construction")
    structure_fasteners(m)
    plates_and_strips(m)
    service_opening(m)
    door_wall(m)
    soffit(m)
    return m.build(coll, materials)
