"""Exterior pass (2026-10-09, prompt 8): the ground props round the kiosk's footprint: deliveries, storage,
cleaning and maintenance gear that make the stall look settled into its street.

Built on its own (build_exterior.py -> Unreal/RawContent/kiosk_exterior.glb) so the kiosk export and its
weathering bake stay untouched; Unreal trims the old step-3 ground props out of a copy of SM_Kiosk_Props
(Unreal/Scripts/kiosk_exterior.py). Placement: kiosk_config.EXTERIOR; sizes of the standard objects
(crates, totes, bottles, cylinders) are here.

Groups, each with open ground left round it:
  door side, back-left (inside the railing): the lantern's pedestal rebuilt as a ballasted timber crate, a
      steel case and a timber riser under the pole's flange; two stacking delivery crates with the red crate of
      empties on top;
      the dry-stock locker (door to the work space behind the corner); a splash block under the old downpipe
  front-left corner: the customer bin (flap toward the counter) and a lidded tote of cup stock; the junction
      box's floor cable re-run to a floor gland behind them
  front-right corner: the utility cabinet on its stand (the 24h pole clamped to it), the gas cylinders' cage
      (two 10 kg cylinders chained in, regulator, pigtails, the pipe into the right wall's base hidden behind
      the corner, a wash-down hose hung on it) and the cans bin in front of the bay's corner
What the glb holds:
  SM_Kiosk_Exterior       one-off parts in place (kiosk frame)
  SM_Kiosk_ExteriorCards  printed things from the Exterior atlas (M_KioskGraphic, no kiosk weathering)
  SM_XP_<name>            repeated props at the origin (crates, tote, bottle crate, bottles, cylinders),
                          placed in Unreal as instances from exterior.json
"""
import math

from mathutils import Matrix, Vector

import kiosk_config as C
from . import geo
from .kitchen import Cards, at, merge, ring

E = C.EXTERIOR
X0, X1, Y0, Y1, PH = C.X0, C.X1, C.Y0, C.Y1, C.PLATFORM_H
UP = Vector((0, 0, 1))

# (rgb linear, roughness, metallic, emission). Unreal builds its own instances of M_Exterior from
# scene_config.EXTERIOR_LOOK; these drive Blender's review renders and seed the Unreal colours.
MATERIALS = {
    "KX_CrateBlue": ((0.12, 0.21, 0.29), 0.55, 0.0, 0.0),  # faded blue-grey stacking crate
    "KX_CrateGreen": ((0.10, 0.23, 0.13), 0.55, 0.0, 0.0),
    "KX_CrateRed": ((0.62, 0.035, 0.025), 0.42, 0.0, 0.0),  # the bottle crate (the scene's red accent)
    "KX_ToteGrey": ((0.26, 0.26, 0.25), 0.6, 0.0, 0.0),
    "KX_ToteLid": ((0.06, 0.13, 0.28), 0.5, 0.0, 0.0),
    "KX_BinBody": ((0.10, 0.13, 0.115), 0.55, 0.0, 0.0),  # dark green-grey moulded bin
    "KX_BinLid": ((0.035, 0.30, 0.25), 0.45, 0.0, 0.0),  # teal lid, like the reference's
    "KX_LockerPaint": ((0.10, 0.125, 0.07), 0.55, 0.1, 0.0),  # old olive enamel on steel
    "KX_CabinetPaint": ((0.17, 0.17, 0.16), 0.5, 0.1, 0.0),  # grey enamel utility cabinet
    "KX_CaseOlive": ((0.10, 0.095, 0.055), 0.6, 0.1, 0.0),  # the steel case under the lantern
    "KX_CylinderGrey": ((0.20, 0.20, 0.20), 0.45, 0.1, 0.0),  # Japanese LPG cylinder grey
    "KX_Galv": ((0.30, 0.30, 0.29), 0.45, 0.85, 0.0),  # stands, cage, chain, bin steel
    "KX_SteelDark": ((0.03, 0.03, 0.03), 0.45, 0.4, 0.0),  # hinges, frames, handles
    "KX_Wood": ((0.26, 0.19, 0.12), 0.8, 0.0, 0.0),  # weathered crate boards
    "KX_WoodDark": ((0.09, 0.065, 0.045), 0.75, 0.0, 0.0),  # timber riser
    "KX_Concrete": ((0.17, 0.17, 0.16), 0.85, 0.0, 0.0),  # ballast blocks, splash block
    "KX_Cardboard": ((0.34, 0.24, 0.14), 0.85, 0.0, 0.0),
    "KX_Rubber": ((0.02, 0.02, 0.02), 0.7, 0.0, 0.0),
    "KX_HoseGreen": ((0.035, 0.10, 0.05), 0.5, 0.0, 0.0),
    "KX_Brass": ((0.42, 0.30, 0.11), 0.35, 1.0, 0.0),
    "KX_Copper": ((0.40, 0.18, 0.09), 0.4, 1.0, 0.0),
    "KX_GasPipe": ((0.50, 0.36, 0.03), 0.5, 0.1, 0.0),  # yellow-painted gas pipe
    "KX_Chrome": ((0.55, 0.55, 0.55), 0.25, 1.0, 0.0),
    "KX_GlassBrown": ((0.07, 0.03, 0.01), 0.06, 0.0, 0.0),
    "KX_GlassGreen": ((0.025, 0.07, 0.035), 0.06, 0.0, 0.0),
    "KX_Cabbage": ((0.22, 0.34, 0.11), 0.6, 0.0, 0.0),
    "KX_Negi": ((0.10, 0.30, 0.06), 0.55, 0.0, 0.0),
    "KX_NegiWhite": ((0.62, 0.62, 0.52), 0.5, 0.0, 0.0),
}


def ensure_materials(B):
    import bpy
    for name, (rgb, rough, metal, emit) in MATERIALS.items():
        m = B.mat(name, rgb, emit)
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return bpy.data.materials


# ---- helpers ---------------------------------------------------------------------------------------

def put(dst, matrix, builder, *args, **kw):
    """Build in a local frame and merge through `matrix` (kitchen.part, with keyword args)."""
    tmp = geo.Mesh("tmp")
    builder(tmp, *args, **kw)
    merge(dst, tmp, matrix)


def rrect_loop(w, d, r, z, n=3):
    """Rounded-rectangle outline at height z, counter-clockwise seen from above, n segments per corner."""
    r = max(1e-4, min(r, w / 2 - 1e-4, d / 2 - 1e-4))
    pts = []
    for ox, oy, a0 in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)):
        for k in range(n + 1):
            a = math.radians(a0 + 90 * k / n)
            pts.append(Vector((ox + r * math.cos(a), oy + r * math.sin(a), z)))
    return pts


def loft(m, loops, mat, cap_bottom=True, cap_top=True, smooth=False):
    """Skin between matching loops (bottom to top); outward normals for counter-clockwise loops."""
    n = len(loops[0])
    verts = [v for lp in loops for v in lp]
    faces = []
    for i in range(len(loops) - 1):
        for k in range(n):
            a, b = i * n + k, i * n + (k + 1) % n
            faces.append((a, b, b + n, a + n))
    if cap_bottom:
        faces.append(tuple(reversed(range(n))))
    if cap_top:
        faces.append(tuple(range((len(loops) - 1) * n, len(loops) * n)))
    m.add_raw(verts, faces, mat, smooth)


def slab(m, w, d, r, z0, z1, mat, n=3):
    """Rounded-corner slab (bands, rims, lids)."""
    loft(m, [rrect_loop(w, d, r, z0, n), rrect_loop(w, d, r, z1, n)], mat)


def arc_shell(m, r0, r1, z0, z1, a0, a1, mat, segs=8):
    """Part of a thick cylindrical wall between angles a0..a1 (degrees)."""
    verts, faces = [], []
    for k in range(segs + 1):
        a = math.radians(a0 + (a1 - a0) * k / segs)
        c, s = math.cos(a), math.sin(a)
        for r, z in ((r1, z0), (r1, z1), (r0, z1), (r0, z0)):
            verts.append(Vector((r * c, r * s, z)))
    for k in range(segs):
        for j in range(4):
            a, b = k * 4 + j, k * 4 + (j + 1) % 4
            faces.append((a, a + 4, b + 4, b))
    faces.append((0, 1, 2, 3))
    e = segs * 4
    faces.append((e + 3, e + 2, e + 1, e))
    m.add_raw(verts, faces, mat, True)


def frame_to(p, t, n=None):
    """4x4 matrix at p whose local X runs along t (and Z toward n, default up)."""
    t = Vector(t).normalized()
    n = Vector(n if n is not None else (0, 0, 1))
    b = n.cross(t)
    if b.length < 1e-6:
        b = Vector((0, 1, 0)).cross(t)
    b.normalize()
    n = t.cross(b)
    M = Matrix.Identity(4)
    for i in range(3):
        M[i][0], M[i][1], M[i][2] = t[i], b[i], n[i]
    M.translation = Vector(p)
    return M


def tube_path(m, pts, r, mat, seg=8):
    """Smooth tube through points (joints hidden by small spheres-as-cylinders)."""
    for a, b in zip(pts, pts[1:]):
        geo.pipe(m, a, b, r, mat, seg)
    for p in pts[1:-1]:
        geo.cylinder(m, tuple(p), r * 1.02, r * 2.0, mat, segments=seg)


def bezier(p0, p1, p2, p3, n=10):
    p0, p1, p2, p3 = (Vector(p) for p in (p0, p1, p2, p3))
    return [p0 * (1 - t) ** 3 + p1 * 3 * t * (1 - t) ** 2 + p2 * 3 * t * t * (1 - t) + p3 * t ** 3 for t in (k / n for k in range(n + 1))]


def chain(m, pts, mat, link=0.024, r=0.0105, tube=0.0028):
    """Welded-link chain along a polyline: elongated torus links, every other one turned 90 degrees."""
    path = [Vector(p) for p in pts]
    L = [0.0]
    for a, b in zip(path, path[1:]):
        L.append(L[-1] + (b - a).length)
    k, s = 0, link / 2
    while s < L[-1] - link / 2:
        i = max(j for j in range(len(L) - 1) if L[j] <= s)
        a, b = path[i], path[i + 1]
        f = (s - L[i]) / max(L[i + 1] - L[i], 1e-6)
        p, t = a.lerp(b, f), (b - a).normalized()
        M = frame_to(p, t) @ Matrix.Rotation(math.radians(90 * (k % 2)), 4, "X") @ Matrix.Diagonal((1.55, 1.0, 1.0, 1.0))
        put(m, M, ring, (0, 0, 0), r, tube, mat, 10, 4)
        k += 1
        s += link * 0.78


def card_on(cards, item, M, c, right, up, w=None, h=None, age=0.4, bend=None):
    """A card placed in an object's local frame (matrix M)."""
    R = M.to_3x3()
    cards.card(item, M @ Vector(c), R @ Vector(right), R @ Vector(up), w, h, age=age,
               bend=None if bend is None else (M @ Vector(bend[0]), bend[1]))


# ---- prototypes (local frame: base at z = 0, centred, long side along X, front toward -Y) -----------

CRATE = {"L": 0.49, "W": 0.34, "H": 0.27, "t": 0.007, "foot": 0.015}
CRATE_STEP = CRATE["H"] - CRATE["foot"]  # stacked: the foot sits down inside the crate below
TOTE = {"L": 0.50, "W": 0.35, "H": 0.245, "lid": 0.022}
BCRATE = {"L": 0.43, "W": 0.34, "H": 0.25}
LPG = {"r": 0.125, "h": 0.615}


def _wall(m, axis, s, a0, a1, z0, z1, t, mat, out=0.0):
    """A wall piece on the side at s * half-size: axis 'x' = a wall along X (front/back), 'y' = an end.
    a0..a1 along the wall, z0..z1; t thick inward from the face, `out` proud outward."""
    if axis == "x":
        hw = CRATE_HALF[1]
        y_in, y_out = s * (hw - t), s * (hw + out)
        geo.box(m, a0, a1, min(y_in, y_out), max(y_in, y_out), z0, z1, mat, 0.0015)
    else:
        hl = CRATE_HALF[0]
        x_in, x_out = s * (hl - t), s * (hl + out)
        geo.box(m, min(x_in, x_out), max(x_in, x_out), a0, a1, z0, z1, mat, 0.0015)


CRATE_HALF = [0.0, 0.0]


def p_crate(m, mat, contents=None):
    """Stacking delivery crate: open ribbed walls in two rows, a mid rail, a solid label panel on the
    front, hand holes in the ends, a stacking lip round the top and an inset foot underneath."""
    L, W, H, t, foot = CRATE["L"], CRATE["W"], CRATE["H"], CRATE["t"], CRATE["foot"]
    hl, hw = L / 2, W / 2
    CRATE_HALF[:] = [hl, hw]
    geo.box(m, -hl + 0.02, hl - 0.02, -hw + 0.02, hw - 0.02, 0.0, foot, mat, 0.003)  # foot (sits inside the rim below)
    geo.box(m, -hl + t, hl - t, -hw + t, hw - t, foot, foot + 0.008, mat)  # floor
    for k in range(-5, 6):  # floor grid ribs
        geo.box(m, k * 0.04 - 0.003, k * 0.04 + 0.003, -hw + t, hw - t, foot + 0.008, foot + 0.016, mat)
    zb1, zm0, zm1, zt0 = foot + 0.035, 0.128, 0.142, H - 0.048
    for s in (-1, 1):
        for axis, half in (("x", hl), ("y", hw)):
            _wall(m, axis, s, -half, half, foot, zb1, t, mat)  # bottom band
            _wall(m, axis, s, -half, half, zm0, zm1, t, mat, 0.002)  # mid rail
            if axis == "x":
                _wall(m, axis, s, -half, half, zt0, H - 0.014, t, mat)  # top band
            else:  # ends: a deeper top band with a hand hole
                hz0, hz1 = H - 0.075, H - 0.042
                _wall(m, axis, s, -half, half, H - 0.09, hz0, t, mat)
                _wall(m, axis, s, -half, -0.065, hz0, hz1, t, mat)
                _wall(m, axis, s, 0.065, half, hz0, hz1, t, mat)
                _wall(m, axis, s, -half, half, hz1, H - 0.014, t, mat)
                geo.box(m, s * (hl - 0.012) - 0.004, s * (hl - 0.012) + 0.004, -0.062, 0.062, hz0 - 0.004, hz0 + 0.002, mat)  # grip lip
            _wall(m, axis, s, -half - 0.004, half + 0.004, H - 0.022, H, t + 0.002, mat, 0.008)  # stacking lip
            ribs = [k * 0.0805 for k in range(-3, 4)] if axis == "x" else [-0.105, 0.0, 0.105]
            top = H - 0.014 if axis == "x" else H - 0.09
            for a in ribs:
                if abs(a) > half - 0.02:
                    continue
                low = axis == "x" and s < 0 and abs(a) < 0.075  # under the label panel: lower row only
                _wall(m, axis, s, a - 0.0065, a + 0.0065, foot, zm0 if low else top, t, mat, 0.004)
    _wall(m, "x", -1, -0.074, 0.074, zm1, zt0, t - 0.001, mat, 0.001)  # label panel: the front's upper row, solid between two ribs
    for sx in (-1, 1):  # rounded corner posts
        for sy in (-1, 1):
            x0, x1 = sorted((sx * (hl + 0.003), sx * (hl - 0.016)))
            y0, y1 = sorted((sy * (hw + 0.003), sy * (hw - 0.016)))
            geo.box(m, x0, x1, y0, y1, foot, H - 0.016, mat, 0.006, 2)
    if contents == "cabbage":
        rng = geo.RNG
        for (x, y, z) in ((-0.13, -0.07, 0.10), (0.0, -0.07, 0.10), (0.13, -0.07, 0.10), (-0.12, 0.08, 0.10), (0.03, 0.08, 0.10),
                          (0.14, 0.07, 0.10), (-0.06, 0.0, 0.17), (0.09, 0.01, 0.165)):
            r = 0.078 + rng.uniform(-0.006, 0.006)
            prof = [(0.0, -r * 0.85)] + [(r * math.sin(math.pi * k / 8) * (1.0 + 0.04 * (k % 2)), -r * 0.85 * math.cos(math.pi * k / 8)) for k in range(1, 8)] + [(0.0, r * 0.85)]
            geo.lathe(m, (x, y, z), prof, "KX_Cabbage", 12, cap_bottom=False, cap_top=False)
    elif contents == "negi":
        for k in range(9):
            y = -0.12 + k * 0.03
            z = 0.06 + (k % 3) * 0.035
            geo.cylinder(m, (-0.10, y, z), 0.011, 0.24, "KX_NegiWhite", axis="X", segments=8)
            geo.cylinder(m, (0.12, y, z + 0.004), 0.010, 0.22, "KX_Negi", axis="X", segments=8)


def p_tote(m):
    """Lidded tote: solid tapered walls with two ribs, end grips under the rim, an attached two-flap lid."""
    L, W, H, lid = TOTE["L"], TOTE["W"], TOTE["H"], TOTE["lid"]
    slab(m, L - 0.05, W - 0.05, 0.02, 0.0, 0.014, "KX_ToteGrey")  # foot
    loft(m, [rrect_loop(L - 0.03, W - 0.03, 0.025, 0.014), rrect_loop(L, W, 0.03, H - 0.02)], "KX_ToteGrey")
    for z in (0.085, 0.16):
        f = (z - 0.014) / (H - 0.034)
        w, d = L - 0.03 + 0.03 * f, W - 0.03 + 0.03 * f
        slab(m, w + 0.008, d + 0.008, 0.03, z, z + 0.011, "KX_ToteGrey")
    slab(m, L + 0.012, W + 0.012, 0.032, H - 0.022, H, "KX_ToteGrey")  # rim
    for s in (-1, 1):  # end grips
        geo.box(m, s * (L / 2 + 0.006) - 0.008, s * (L / 2 + 0.006) + 0.008, -0.075, 0.075, H - 0.05, H - 0.024, "KX_ToteGrey", 0.004)
    # lid: two flaps meeting along the middle, a raised rib round each, hinge knuckles along the long edges
    for s in (-1, 1):
        y0, y1 = sorted((s * 0.0015, s * (W / 2 + 0.008)))
        geo.box(m, -L / 2 - 0.006, L / 2 + 0.006, y0, y1, H, H + lid * 0.55, "KX_ToteLid", 0.004)
        ya, yb = sorted((s * 0.03, s * (W / 2 - 0.03)))
        geo.box(m, -L / 2 + 0.04, L / 2 - 0.04, ya, yb, H + lid * 0.55, H + lid, "KX_ToteLid", 0.006, 2)
        for k in range(4):
            x = -0.18 + k * 0.12
            geo.cylinder(m, (x, s * (W / 2 + 0.006), H + 0.006), 0.007, 0.05, "KX_ToteLid", axis="X", segments=8)
    geo.box(m, -L / 2 + 0.01, L / 2 - 0.01, -0.0015, 0.0015, H + 0.002, H + lid * 0.5, "KX_Rubber")  # the seam's shadow line
    geo.box(m, -0.06, 0.06, -W / 2 - 0.0035, -W / 2 + 0.002, 0.10, 0.15, "KX_ToteGrey", 0.002)  # label recess frame


def p_bottle_crate(m):
    """Returnable bottle crate (20 bottles): solid lower walls with the moulded logo panel, open bars above,
    hand holds in the ends, divider grid inside."""
    L, W, H = BCRATE["L"], BCRATE["W"], BCRATE["H"]
    hl, hw, t, mat = L / 2, W / 2, 0.008, "KX_CrateRed"
    geo.box(m, -hl + 0.006, hl - 0.006, -hw + 0.006, hw - 0.006, 0.0, 0.012, mat, 0.003)
    for s in (-1, 1):
        for y0, y1 in (sorted((s * hw, s * (hw - t))),):
            geo.box(m, -hl, hl, y0, y1, 0.0, 0.11, mat, 0.003)  # lower panel (logo on the front one)
            geo.box(m, -hl, hl, y0 - 0.002 * s if s < 0 else y0, y1 + 0.002 if s > 0 else y1, 0.205, H, mat, 0.004)  # top rail
            for x in (-0.17, -0.085, 0.0, 0.085, 0.17):
                geo.box(m, x - 0.009, x + 0.009, y0, y1, 0.11, 0.205, mat, 0.002)
        x0, x1 = sorted((s * hl, s * (hl - t)))
        geo.box(m, x0, x1, -hw, hw, 0.0, 0.11, mat, 0.003)
        for y in (-0.11, 0.11):
            geo.box(m, x0, x1, y - 0.01, y + 0.01, 0.11, 0.175, mat, 0.002)
        geo.box(m, x0, x1, -hw, hw, 0.175, 0.19, mat)
        geo.box(m, x0, x1, -hw, -0.055, 0.19, 0.228, mat)
        geo.box(m, x0, x1, 0.055, hw, 0.19, 0.228, mat)
        geo.box(m, x0, x1, -hw, hw, 0.228, H, mat, 0.003)
    for sx in (-1, 1):
        for sy in (-1, 1):
            xa, xb = sorted((sx * (hl + 0.002), sx * (hl - 0.014)))
            ya, yb = sorted((sy * (hw + 0.002), sy * (hw - 0.014)))
            geo.box(m, xa, xb, ya, yb, 0.0, H, mat, 0.005, 2)
    for k in range(1, 5):  # dividers
        x = -hl + k * L / 5
        geo.box(m, x - 0.002, x + 0.002, -hw + t, hw - t, 0.012, 0.19, mat)
    for k in range(1, 4):
        y = -hw + k * W / 4
        geo.box(m, -hl + t, hl - t, y - 0.002, y + 0.002, 0.012, 0.19, mat)
    geo.box(m, -0.10, 0.10, -hw - 0.003, -hw + 0.001, 0.025, 0.098, mat, 0.003)  # raised logo panel


BOTTLE_CELLS = [(-BCRATE["L"] / 2 + (i + 0.5) * BCRATE["L"] / 5, -BCRATE["W"] / 2 + (j + 0.5) * BCRATE["W"] / 4) for j in range(4) for i in range(5)]


def p_bottle(m, glass):
    """Empty returnable beer bottle (633 ml), no cap."""
    prof = [(0.0, 0.0), (0.027, 0.0), (0.031, 0.006), (0.032, 0.02), (0.032, 0.165), (0.0295, 0.185), (0.0205, 0.208), (0.0145, 0.232),
            (0.0135, 0.262), (0.016, 0.266), (0.016, 0.272), (0.0115, 0.274), (0.0115, 0.25)]
    geo.lathe(m, (0, 0, 0), prof, glass, 14, cap_bottom=True, cap_top=False)


def p_lpg(m):
    """10 kg LPG cylinder: foot ring, welded body, protective collar with hand holes, brass valve."""
    r, mat = LPG["r"], "KX_CylinderGrey"
    arc_shell(m, 0.088, 0.096, 0.0, 0.045, 0, 360, "KX_SteelDark", 20)  # foot ring
    prof = [(0.0, 0.03), (0.07, 0.032), (0.105, 0.046), (0.121, 0.075), (r, 0.11), (r, 0.40), (0.121, 0.44), (0.105, 0.47), (0.07, 0.49),
            (0.03, 0.497), (0.0, 0.498)]
    geo.lathe(m, (0, 0, 0), prof, mat, 28)
    geo.cylinder(m, (0, 0, 0.255), r + 0.003, 0.012, mat, segments=28)  # girth weld
    for a0, a1 in ((20, 150), (200, 330)):  # collar, two hand holes
        arc_shell(m, 0.072, 0.079, 0.49, 0.535, a0 - 20, a1 + 20, mat, 10)
        arc_shell(m, 0.072, 0.079, 0.535, 0.585, a0, a1, mat, 10)
    arc_shell(m, 0.072, 0.079, 0.585, 0.605, 0, 360, mat, 24)
    ring(m, (0, 0, 0.607), 0.0755, 0.006, mat, 24, 6)
    geo.cylinder(m, (0, 0, 0.515), 0.022, 0.035, "KX_Brass", segments=12)  # valve body
    geo.cylinder(m, (0.035, 0, 0.52), 0.009, 0.05, "KX_Brass", axis="X", segments=10)  # outlet (toward +X)
    geo.cylinder(m, (0, 0, 0.552), 0.006, 0.03, "KX_Brass", segments=8)
    ring(m, (0, 0, 0.565), 0.022, 0.004, "KX_SteelDark", 16, 5)  # handwheel
    for k in range(3):
        a = math.radians(120 * k)
        geo.pipe(m, (0, 0, 0.565), (0.022 * math.cos(a), 0.022 * math.sin(a), 0.565), 0.003, "KX_SteelDark", 5)


def p_box(m, sx, sy, sz):
    geo.box(m, -sx / 2, sx / 2, -sy / 2, sy / 2, 0.0, sz, "KX_Cardboard", 0.004)


PROTOS = {
    "crate_blue": lambda m: p_crate(m, "KX_CrateBlue", "cabbage"),
    "crate_green": lambda m: p_crate(m, "KX_CrateGreen", "negi"),
    "tote": p_tote,
    "bottle_crate": p_bottle_crate,
    "bottle_brown": lambda m: p_bottle(m, "KX_GlassBrown"),
    "bottle_green": lambda m: p_bottle(m, "KX_GlassGreen"),
    "lpg": p_lpg,
}


class Props:
    """Placements of the prototypes: (name, (x, y, z), yaw deg, scale). Unreal instances them."""

    def __init__(self):
        self.items = []

    def put(self, name, x, y, z, yaw=0.0, s=1.0):
        assert name in PROTOS, name
        self.items.append((name, (x, y, z), yaw, s))
        return at(x, y, z, yaw)


# ---- door side, back-left --------------------------------------------------------------------------

def pedestal(m, cards):
    """The lantern's pedestal: a slatted timber crate weighted with two concrete blocks, a steel case on it,
    a timber riser with the pole's flange and socket. Same top as before (PH + 0.90)."""
    p = E["pedestal"]
    x, y = p["x"], p["y"]
    h1, h2, h3 = p["tiers"]
    # tier 1: crate on two skids
    w, d = 0.42, 0.40
    for sy in (-1, 1):
        geo.box(m, x - w / 2 + 0.01, x + w / 2 - 0.01, y + sy * 0.15 - 0.03, y + sy * 0.15 + 0.03, PH, PH + 0.035, "KX_Wood", 0.004)
    z0 = PH + 0.035
    hs = (h1 - 0.035) / 3
    for k in range(3):
        za, zb = z0 + k * hs + 0.004, z0 + (k + 1) * hs - 0.012
        geo.box(m, x - w / 2, x + w / 2, y - d / 2, y - d / 2 + 0.018, za, zb, "KX_Wood", 0.003)
        geo.box(m, x - w / 2, x + w / 2, y + d / 2 - 0.018, y + d / 2, za, zb, "KX_Wood", 0.003)
        geo.box(m, x - w / 2, x - w / 2 + 0.018, y - d / 2 + 0.018, y + d / 2 - 0.018, za, zb, "KX_Wood", 0.003)
        geo.box(m, x + w / 2 - 0.018, x + w / 2, y - d / 2 + 0.018, y + d / 2 - 0.018, za, zb, "KX_Wood", 0.003)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = x + sx * (w / 2 - 0.035), y + sy * (d / 2 - 0.035)
            geo.box(m, cx - 0.017, cx + 0.017, cy - 0.017, cy + 0.017, z0, PH + h1, "KX_Wood", 0.003)
    geo.box(m, x - w / 2 + 0.018, x + w / 2 - 0.018, y - d / 2 + 0.018, y + d / 2 - 0.018, z0, z0 + 0.012, "KX_Wood")
    for sy in (-1, 1):  # ballast: two hollow concrete blocks
        cy = y + sy * 0.095
        geo.box(m, x - 0.185, x + 0.185, cy - 0.088, cy + 0.088, z0 + 0.012, z0 + 0.012 + 0.18, "KX_Concrete", 0.008)
    geo.rivets(m, [(x - w / 2 - 0.001, y + yy, z0 + k * hs + hs / 2) for yy in (-0.16, 0.16) for k in range(3)], "-X", "KX_SteelDark", 0.006)
    cards.card("x_crate_wood", (x - w / 2 - 0.0015, y + 0.02, z0 + 1.5 * hs), Vector((0, -1, 0)), UP, 0.17, 0.06, age=0.8)
    # tier 2: the steel case, turned a little
    zc = PH + h1
    M = at(x + 0.008, y - 0.006, zc, 4.0)
    put(m, M, steel_case, h2)
    card_on(cards, "x_case_stencil", M, (0.0, -0.1525, 0.105), (1, 0, 0), (0, 0, 1), 0.12, 0.04, age=0.7)
    # tier 3: timber riser (two layers crossed), flange plate, socket round the pole
    z3 = PH + h1 + h2
    for k, (sx, sy) in enumerate(((0.22, 0.095), (0.095, 0.22))):
        zz = z3 + k * 0.1
        for s in (-1, 1):
            ox, oy = (0, s * 0.055) if k == 0 else (s * 0.055, 0)
            geo.box(m, x + ox - sx / 2, x + ox + sx / 2, y + oy - sy / 2, y + oy + sy / 2, zz, zz + 0.1, "KX_WoodDark", 0.006, 2)
    zf = z3 + 0.2
    geo.box(m, x - 0.09, x + 0.09, y - 0.09, y + 0.09, zf, zf + 0.012, "KX_SteelDark", 0.003)
    geo.bolts(m, [(x + sx * 0.065, y + sy * 0.065, zf + 0.012) for sx in (-1, 1) for sy in (-1, 1)], "+Z", "KX_SteelDark", 0.011)
    geo.cylinder(m, (x, y, zf + 0.012 + 0.03), 0.031, 0.06, "KX_SteelDark", segments=16)
    for a in (0, 90, 180, 270):  # gussets round the socket
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        geo.box(m, x + c * 0.045 - (0.004 if c == 0 else 0.014), x + c * 0.045 + (0.004 if c == 0 else 0.014),
                y + s * 0.045 - (0.004 if s == 0 else 0.014), y + s * 0.045 + (0.004 if s == 0 else 0.014), zf + 0.012, zf + 0.04, "KX_SteelDark")
    assert abs(zf + 0.012 + 0.048 - (PH + h1 + h2 + h3)) < 0.03


def steel_case(m, h):
    """Steel storage case (local, base at 0): body, overlapping lid, latches, folding end handles, swages."""
    w, d = 0.36, 0.30
    hb = h * 0.74
    geo.box(m, -w / 2 + 0.01, w / 2 - 0.01, -d / 2 + 0.01, d / 2 - 0.01, 0.0, 0.015, "KX_SteelDark", 0.004)  # base rails
    geo.box(m, -w / 2, w / 2, -d / 2, d / 2, 0.012, hb, "KX_CaseOlive", 0.008, 2)
    geo.box(m, -w / 2 - 0.006, w / 2 + 0.006, -d / 2 - 0.006, d / 2 + 0.006, hb - 0.004, h, "KX_CaseOlive", 0.01, 2)  # lid
    geo.box(m, -w / 2 + 0.03, w / 2 - 0.03, -d / 2 + 0.03, d / 2 - 0.03, h, h + 0.006, "KX_CaseOlive", 0.004)  # pressed lid panel
    for s in (-1, 1):
        for zz in (hb * 0.35, hb * 0.68):  # swages
            ya, yb = sorted((s * d / 2, s * (d / 2 + 0.005)))
            geo.box(m, -w / 2 + 0.03, w / 2 - 0.03, ya, yb, zz - 0.006, zz + 0.006, "KX_CaseOlive", 0.003)
        # folding bail handle on each end, hanging down
        xa = s * (w / 2 + 0.012)
        geo.box(m, s * w / 2, xa, -0.05, -0.035, hb - 0.06, hb - 0.03, "KX_SteelDark", 0.002)
        geo.box(m, s * w / 2, xa, 0.035, 0.05, hb - 0.06, hb - 0.03, "KX_SteelDark", 0.002)
        tube_path(m, [Vector((xa, -0.045, hb - 0.045)), Vector((xa + s * 0.006, -0.045, hb - 0.12)), Vector((xa + s * 0.006, 0.045, hb - 0.12)),
                      Vector((xa, 0.045, hb - 0.045))], 0.005, "KX_SteelDark", 6)
    for x in (-0.11, 0.11):  # over-centre latches on the front
        geo.box(m, x - 0.022, x + 0.022, -d / 2 - 0.012, -d / 2, hb - 0.05, hb - 0.012, "KX_SteelDark", 0.003)
        geo.box(m, x - 0.016, x + 0.016, -d / 2 - 0.016, -d / 2 - 0.006, hb - 0.012, hb + 0.022, "KX_SteelDark", 0.003)


def crate_stack(props, cards):
    """This morning's delivery against the railing: two stacking crates, each a little off the one below, and
    on top the red crate of empties going back with the driver."""
    c = E["crate_stack"]
    x, y, yaw = c["x"], c["y"], c["yaw"]
    z = PH
    M1 = props.put("crate_blue", x, y, z, yaw + 1.0)
    M2 = props.put("crate_green", x + 0.003, y - 0.005, z + CRATE_STEP + 0.001, yaw - 0.5)
    hw = CRATE["W"] / 2
    zl = (0.142 + CRATE["H"] - 0.048) / 2
    card_on(cards, "x_crate_marusan", M1, (0.0, -hw - 0.0035, zl), (1, 0, 0), (0, 0, 1), 0.135, 0.042, age=0.5)
    card_on(cards, "x_crate_kaze", M2, (0.0, -hw - 0.0035, zl), (1, 0, 0), (0, 0, 1), 0.135, 0.039, age=0.5)
    # the delivery slip tucked under the green crate's end grip, facing the front of the stall
    card_on(cards, "x_crate_slip", M2, (CRATE["L"] / 2 + 0.0065, 0.0, 0.16), (0, 1, 0), (0, 0, 1), 0.086, 0.058, age=0.5)
    # the empties sit on the green crate's rim (the bottle crate has no stacking foot)
    bottle_crate(props, cards, x - 0.004, y + 0.008, z + CRATE_STEP + CRATE["H"] + 0.002, yaw + c["top_yaw"])


def tote(props, cards):
    """The lidded tote of cup stock, waiting by the bin under the canopy."""
    t = E["tote"]
    M = props.put("tote", t["x"], t["y"], PH, t["yaw"])
    W, H = TOTE["W"], TOTE["H"]
    card_on(cards, "x_tote_tape", M, (0.0, -W / 2 - 0.0045, 0.125), (1, 0, 0), (0, 0, 1), 0.11, 0.024, age=0.5)
    card_on(cards, "x_tote_note", M, (-0.08, -0.09, H + TOTE["lid"] + 0.0015), (1, 0, 0), (0, 1, 0), 0.074, 0.052, age=0.6)


def locker(m, cards):
    """Dry-stock locker: steel cabinet on feet, rain hood, door on the +X side (to the work space behind the
    corner) with hinges at the back, a padlocked hasp; louvres and a stencil on the sides the street sees."""
    L = E["locker"]
    cx, cy = L["x"], L["y"]
    w, d, h = L["size"]
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2
    zb, zt = PH + 0.04, PH + h
    for sx in (x0 + 0.03, x1 - 0.03):
        for sy in (y0 + 0.03, y1 - 0.03):
            geo.box(m, sx - 0.02, sx + 0.02, sy - 0.02, sy + 0.02, PH, zb, "KX_SteelDark", 0.003)
    geo.box(m, x0, x1, y0, y1, zb, zt - 0.02, "KX_LockerPaint", 0.008, 2)
    geo.box(m, x0 - 0.02, x1 + 0.025, y0 - 0.02, y1 + 0.02, zt - 0.02, zt, "KX_LockerPaint", 0.004)  # hood
    geo.box(m, x0 - 0.022, x1 + 0.027, y0 - 0.022, y1 + 0.022, zt - 0.03, zt - 0.02, "KX_LockerPaint", 0.002)  # drip edge
    # door (+X): panel, hinges at the back edge, handle + hasp + padlock at the front edge
    geo.box(m, x1 - 0.002, x1 + 0.006, y0 + 0.02, y1 - 0.02, zb + 0.03, zt - 0.05, "KX_LockerPaint", 0.004)
    for zz in (zb + 0.12, zt - 0.17):
        geo.cylinder(m, (x1 + 0.008, y1 - 0.012, zz), 0.008, 0.07, "KX_SteelDark", segments=10)
    zh = zb + (zt - zb) * 0.55
    geo.box(m, x1 + 0.006, x1 + 0.03, y0 + 0.04, y0 + 0.055, zh - 0.06, zh + 0.06, "KX_SteelDark", 0.004)
    geo.box(m, x1 + 0.006, x1 + 0.012, y0 + 0.03, y0 + 0.08, zh + 0.09, zh + 0.13, "KX_SteelDark", 0.002)
    ring(m, (x1 + 0.018, y0 + 0.07, zh + 0.11), 0.012, 0.003, "KX_SteelDark", 12, 5, axis="Y")
    geo.box(m, x1 + 0.012, x1 + 0.03, y0 + 0.055, y0 + 0.085, zh + 0.045, zh + 0.09, "KX_Brass", 0.004)  # padlock
    # street sides: two swages each, louvres low on the -Y side, a lifting handle on the -X side
    for zz in (zb + 0.33, zb + 0.66):
        geo.box(m, x0 - 0.004, x0, y0 + 0.04, y1 - 0.04, zz - 0.006, zz + 0.006, "KX_LockerPaint", 0.002)
    for k in range(6):
        zz = zb + 0.08 + k * 0.024
        geo.box(m, x0 + 0.08, x1 - 0.08, y0 - 0.007, y0, zz, zz + 0.011, "KX_LockerPaint", 0.002)
        geo.box(m, x0 + 0.08, x1 - 0.08, y0 - 0.0005, y0 + 0.0005, zz - 0.012, zz, "KX_Rubber")
    geo.box(m, x0 + 0.08, x1 - 0.08, y0 - 0.0035, y0, zt - 0.20, zt - 0.06, "KX_LockerPaint", 0.003)  # data plate boss
    cards.card("x_locker_stencil", (x0 - 0.0015, cy + 0.01, zb + 0.82), Vector((0, -1, 0)), UP, 0.25, 0.08, age=0.8)
    cards.card("x_crate_slip", (cx - 0.07, y0 - 0.0045, zt - 0.13), Vector((1, 0, 0)), UP, 0.086, 0.058, age=0.9)


def cartons(m, cards):
    """Two cartons (noodles, cups) on timber bearers behind the back-left corner, under the canopy's back
    overhang: off the wet slab, the long sides with their print toward the street."""
    c = E["cartons"]
    M = at(c["x"], c["y"], PH, c["yaw"] + 90.0)  # local X (the cartons' long side) runs along the wall

    def stack(mm):
        for sy in (-1, 1):
            geo.box(mm, -0.20, 0.20, sy * 0.075 - 0.025, sy * 0.075 + 0.025, 0.0, 0.05, "KX_WoodDark", 0.004)
        for (L, W, H, z, yaw) in ((0.32, 0.24, 0.16, 0.05, 0.0), (0.30, 0.22, 0.15, 0.21, 6.0)):
            R = Matrix.Rotation(math.radians(yaw), 4, "Z")
            tmp = geo.Mesh("tmp")
            geo.box(tmp, -L / 2, L / 2, -W / 2, W / 2, 0.0, H, "KX_Cardboard", 0.005)
            geo.box(tmp, -L / 2 + 0.004, L / 2 - 0.004, -0.0015, 0.0015, H, H + 0.0012, "KX_SteelDark")  # flap seam, dark
            merge(mm, tmp, Matrix.Translation((0.0, 0.0, z)) @ R)
    put(m, M, stack)
    card_on(cards, "x_carton_noodle", M, (0.0, -0.1215, 0.13), (1, 0, 0), (0, 0, 1), 0.29, 0.14, age=0.5)
    R6 = at(0, 0, 0.21, 6.0)
    card_on(cards, "x_carton_cups", M @ R6, (0.0, -0.1115, 0.075), (1, 0, 0), (0, 0, 1), 0.26, 0.12, age=0.5)
    card_on(cards, "x_tape_strip", M @ R6, (0.0, 0.0, 0.1515), (0, 1, 0), (1, 0, 0), 0.26, 0.048, age=0.4)


def splash_block(m, key):
    s = E[key]
    w, d, h = s["size"]
    M = at(s["x"], s["y"], PH, s["yaw"])

    def blk(mm):
        geo.box(mm, -w / 2, w / 2, -d / 2, d / 2, 0.0, h * 0.45, "KX_Concrete", 0.006)
        for sy in (-1, 1):
            geo.box(mm, -w / 2, w / 2, sy * d / 2 - (0.028 if sy > 0 else -0.028), sy * d / 2, h * 0.45, h, "KX_Concrete", 0.005)
        geo.box(mm, w / 2 - 0.03, w / 2, -d / 2 + 0.03, d / 2 - 0.03, h * 0.45, h * 0.8, "KX_Concrete", 0.004)  # back stop under the shoe
    put(m, M, blk)


# ---- front-left corner -------------------------------------------------------------------------------

def bin_burnable(m, cards):
    """Moulded customer bin: tapered body with corner ribs, base skirt on feet, side grips, rim lip, a hinged
    lid with a push-flap opening toward the counter."""
    b = E["bin_burnable"]
    w, d, h = b["size"]
    M = at(b["x"], b["y"], PH, b["yaw"])

    def body(mm):
        slab(mm, w - 0.05, d - 0.05, 0.03, 0.0, 0.03, "KX_BinBody")  # skirt
        for sx in (-1, 1):
            for sy in (-1, 1):
                geo.box(mm, sx * (w / 2 - 0.05) - 0.025, sx * (w / 2 - 0.05) + 0.025, sy * (d / 2 - 0.05) - 0.025, sy * (d / 2 - 0.05) + 0.025,
                        -0.0, 0.012, "KX_Rubber", 0.004)
        loft(mm, [rrect_loop(w - 0.04, d - 0.04, 0.035, 0.03), rrect_loop(w - 0.005, d - 0.005, 0.045, h - 0.04)], "KX_BinBody")
        slab(mm, w + 0.012, d + 0.012, 0.048, h - 0.045, h - 0.02, "KX_BinBody")  # rim lip
        for sx in (-1, 1):  # corner ribs, following the taper
            for sy in (-1, 1):
                a = Vector((sx * (w / 2 - 0.03), sy * (d / 2 - 0.03), 0.035))
                c = Vector((sx * (w / 2 - 0.012), sy * (d / 2 - 0.012), h - 0.05))
                geo.pipe(mm, a, c, 0.011, "KX_BinBody", 8)
        for zz in (0.22, 0.44):  # moulded hoops
            f = (zz - 0.03) / (h - 0.07)
            slab(mm, w - 0.04 + 0.035 * f + 0.008, d - 0.04 + 0.035 * f + 0.008, 0.04, zz, zz + 0.014, "KX_BinBody")
        for sx in (-1, 1):  # side grips under the rim
            geo.box(mm, sx * (w / 2 + 0.006) - 0.012, sx * (w / 2 + 0.006) + 0.012, -0.08, 0.08, h - 0.075, h - 0.052, "KX_BinBody", 0.005)
        # lid: hinged at the back, domed, a framed opening with a swinging flap at the front
        hz = h - 0.02
        slab(mm, w + 0.016, d + 0.016, 0.05, hz, hz + 0.022, "KX_BinLid")
        loft(mm, [rrect_loop(w - 0.02, d - 0.02, 0.045, hz + 0.022), rrect_loop(w - 0.10, d - 0.10, 0.04, hz + 0.055)], "KX_BinLid")
        geo.box(mm, -0.12, 0.12, -d / 2 - 0.006, -d / 2 + 0.07, hz + 0.022, hz + 0.075, "KX_BinLid", 0.01, 2)  # flap hood
        geo.box(mm, -0.10, 0.10, -d / 2 - 0.0075, -d / 2 + 0.005, hz + 0.026, hz + 0.066, "KX_Rubber", 0.002)  # the opening, dark
        geo.box(mm, -0.096, 0.096, -d / 2 - 0.004, -d / 2 + 0.002, hz + 0.032, hz + 0.064, "KX_BinLid", 0.002)  # the flap, slightly in
        for sx in (-1, 1):
            geo.cylinder(mm, (sx * 0.12, d / 2 - 0.005, hz + 0.02), 0.012, 0.07, "KX_BinLid", axis="X", segments=10)  # hinge knuckles
    put(m, M, body)
    # labels between the moulded hoops, following the taper (the walls lean out ~0.028 per metre of height)
    half = lambda z: (d - 0.04 + 0.035 * (z - 0.03) / (h - 0.07)) / 2  # noqa: E731
    card_on(cards, "x_bin_burnable", M, (0.0, -half(0.33) - 0.002, 0.33), (1, 0, 0), (0, -0.028, 1), 0.15, 0.096, age=0.5)
    card_on(cards, "x_bin_scraped", M, (-half(0.385) - 0.002, 0.03, 0.385), (0, -1, 0), (-0.028, 0, 1), 0.07, 0.05, age=0.9)


def bottle_crate(props, cards, x, y, z, yaw):
    """The red crate of returnable bottles, a few cells already empty."""
    M = props.put("bottle_crate", x, y, z, yaw)
    empty = {2, 7, 13, 16, 19, 11}  # cells already handed back / broken
    rng = geo.RNG
    for k, (bx_, by_) in enumerate(BOTTLE_CELLS):
        if k in empty:
            continue
        p = M @ Vector((bx_ + rng.uniform(-0.0015, 0.0015), by_ + rng.uniform(-0.0015, 0.0015), 0.0125))
        props.put("bottle_green" if k in (4, 9) else "bottle_brown", p.x, p.y, p.z, yaw + rng.uniform(0, 360))
    card_on(cards, "x_bottle_logo", M, (0.0, -BCRATE["W"] / 2 - 0.0045, 0.0615), (1, 0, 0), (0, 0, 1), 0.19, 0.068, age=0.5)
    # the empties tag tied to the front handhold
    card_on(cards, "x_bottle_tag", M, (BCRATE["L"] / 2 + 0.006, 0.075, 0.185), (0, 1, 0), (0, 0.15, 1), 0.04, 0.06, age=0.6)


def jb_cable(m):
    """The junction box's floor cable, re-run down the wall (clear of the base frame's lip) into a floor gland."""
    j = E["jb_cable"]
    x, y = j["x"], j["y"]
    top = (X0 - 0.05, y, 0.92)
    pts = [Vector(top), Vector((X0 - 0.05, y, 0.70))] + bezier((X0 - 0.05, y, 0.70), (X0 - 0.05, y, 0.55), (x, y, 0.52), (x, y, 0.40), 6)[1:] + \
        [Vector((x, y, PH + 0.075))]
    tube_path(m, pts, 0.0075, "KX_Rubber", 8)
    for zz, wall in ((0.80, X0 - 0.002), (0.62, X0 - 0.034)):  # saddle clips to the wall (the lower one on the repair plate)
        geo.box(m, X0 - 0.064, wall, y - 0.012, y + 0.012, zz - 0.008, zz + 0.008, "KX_SteelDark", 0.002)
    geo.box(m, x - 0.05, x + 0.05, y - 0.045, y + 0.045, PH, PH + 0.06, "KX_Galv", 0.006)  # floor gland box
    geo.cylinder(m, (x, y, PH + 0.067), 0.014, 0.016, "KX_Rubber", segments=10)
    geo.bolts(m, [(x + sx * 0.038, y + sy * 0.033, PH + 0.06) for sx in (-1, 1) for sy in (-1, 1)], "+Z", "KX_SteelDark", 0.007)


# ---- front-right service cluster --------------------------------------------------------------------

def utility_cabinet(m, cards):
    """Utility cabinet on a galvanised stand: rain hood, door on the street side hinged on the right, T-handle
    lock and padlock hasp, louvres, flexible conduit down into the platform, the 24h sign's pole clamped to
    its left side."""
    u = E["utility_cabinet"]
    cx, cy = u["x"], u["y"]
    w, d, h = u["size"]
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2
    zs = PH + u["stand"]
    # stand: two channels front-to-back, two cross members, foot plates with anchor bolts
    for sx in (x0 + 0.095, x1 - 0.04):  # the left channel set in, so its feet clear the 24h pole's base plate
        geo.box(m, sx - 0.02, sx + 0.02, y0 + 0.01, y1 - 0.01, zs - 0.05, zs, "KX_Galv", 0.003)
        geo.box(m, sx - 0.005, sx + 0.005, y0 + 0.01, y1 - 0.01, PH + 0.012, zs - 0.05, "KX_Galv", 0.002)
        for sy in (y0 + 0.04, y1 - 0.04):
            geo.box(m, sx - 0.04, sx + 0.04, sy - 0.035, sy + 0.035, PH, PH + 0.012, "KX_Galv", 0.003)
            geo.bolts(m, [(sx - 0.026, sy, PH + 0.012), (sx + 0.026, sy, PH + 0.012)], "+Z", "KX_SteelDark", 0.009)
            geo.box(m, sx - 0.005, sx + 0.005, sy - 0.02, sy + 0.02, PH + 0.012, zs - 0.05, "KX_Galv", 0.002)
    for sy in (y0 + 0.05, y1 - 0.05):
        geo.box(m, x0 + 0.02, x1 - 0.02, sy - 0.015, sy + 0.015, zs - 0.035, zs - 0.005, "KX_Galv", 0.003)
    zt = zs + h
    geo.box(m, x0, x1, y0, y1, zs, zt, "KX_CabinetPaint", 0.01, 2)
    # sloped rain hood with a drip edge
    hl_ = 0.008  # the hood barely overhangs on the left: the 24h pole stands 1.5 cm off that side
    hood = [(x0 - hl_, y0 - 0.035, zt + 0.012), (x1 + 0.025, y0 - 0.035, zt + 0.012), (x1 + 0.025, y1 + 0.015, zt + 0.032),
            (x0 - hl_, y1 + 0.015, zt + 0.032)]
    geo.prism(m, ([Vector(p) for p in hood], [Vector((p[0], p[1], p[2] + 0.016)) for p in hood]), "KX_CabinetPaint")
    geo.box(m, x0 - hl_, x1 + 0.026, y0 - 0.037, y0 - 0.031, zt, zt + 0.014, "KX_CabinetPaint", 0.002)
    geo.box(m, x0 + 0.02, x1 - 0.02, y0 + 0.02, y1 - 0.02, zt, zt + 0.012, "KX_CabinetPaint", 0.003)
    # door
    dx0, dx1, dz0, dz1 = x0 + 0.018, x1 - 0.022, zs + 0.025, zt - 0.03
    geo.box(m, dx0, dx1, y0 - 0.006, y0 + 0.001, dz0, dz1, "KX_CabinetPaint", 0.004)
    geo.box(m, dx0 + 0.02, dx1 - 0.02, y0 - 0.009, y0 - 0.005, dz0 + 0.02, dz1 - 0.02, "KX_CabinetPaint", 0.003)  # pressed panel
    for zz in (dz0 + 0.08, (dz0 + dz1) / 2, dz1 - 0.08):
        geo.cylinder(m, (x1 - 0.012, y0 - 0.012, zz), 0.008, 0.06, "KX_SteelDark", segments=10)
        geo.box(m, x1 - 0.05, x1 - 0.012, y0 - 0.011, y0 - 0.006, zz - 0.02, zz + 0.02, "KX_SteelDark", 0.002)
    zl = (dz0 + dz1) / 2
    geo.box(m, dx0 + 0.02, dx0 + 0.05, y0 - 0.016, y0 - 0.006, zl - 0.06, zl + 0.06, "KX_SteelDark", 0.003)  # T-handle housing
    geo.box(m, dx0 + 0.028, dx0 + 0.042, y0 - 0.04, y0 - 0.016, zl - 0.005, zl + 0.005, "KX_Chrome", 0.002)
    geo.box(m, dx0 + 0.026, dx0 + 0.044, y0 - 0.044, y0 - 0.036, zl - 0.04, zl + 0.04, "KX_Chrome", 0.003)
    geo.box(m, x0 - 0.004, x0 + 0.004, y0 + 0.06, y0 + 0.12, zl + 0.08, zl + 0.12, "KX_SteelDark")  # hasp staple on the side
    geo.box(m, dx0 + 0.006, dx0 + 0.024, y0 - 0.012, y0 - 0.006, zl + 0.08, zl + 0.12, "KX_SteelDark")
    ring(m, (x0 + 0.004, y0 - 0.002, zl + 0.10), 0.014, 0.0035, "KX_SteelDark", 12, 5, axis="X")
    geo.box(m, x0 - 0.002, x0 + 0.012, y0 - 0.024, y0 + 0.004, zl + 0.055, zl + 0.09, "KX_Brass", 0.004)  # padlock
    for k in range(5):  # louvres at the top of the door
        zz = dz1 - 0.05 - k * 0.022
        geo.box(m, dx0 + 0.07, dx1 - 0.04, y0 - 0.016, y0 - 0.006, zz, zz + 0.01, "KX_CabinetPaint", 0.002)
        geo.box(m, dx0 + 0.07, dx1 - 0.04, y0 - 0.0065, y0 - 0.0055, zz - 0.011, zz, "KX_Rubber")
    # gland plate and flexible conduit into the platform
    geo.box(m, cx - 0.07, cx + 0.07, cy - 0.05, cy + 0.05, zs - 0.012, zs, "KX_SteelDark", 0.003)
    for k in range(9):
        z = PH + 0.008 + k * (zs - PH - 0.02) / 8
        geo.cylinder(m, (cx, cy + 0.01, z), 0.024 + (0.003 if k % 2 else 0.0), 0.012, "KX_Rubber", segments=12)
    geo.cylinder(m, (cx, cy + 0.01, PH + 0.006), 0.04, 0.012, "KX_SteelDark", segments=14)
    # the 24h pole clamped to the cabinet's side: U-bolt rings round the pole, stand-off plates
    px, py = C.LANTERN_R["x"] + 0.12, C.LANTERN_R["y"]
    for zz in (zs + 0.20, zt - 0.10):
        ring(m, (px, py, zz), 0.024, 0.005, "KX_Galv", 16, 6)
        geo.box(m, px + 0.02, x0, py - 0.016, py + 0.016, zz - 0.02, zz + 0.02, "KX_Galv", 0.002)
        geo.bolts(m, [(x0 - 0.001, py, zz)], "-X", "KX_SteelDark", 0.008)
    cards.card("x_cab_warn", (dx0 + 0.11, y0 - 0.0095, dz1 - 0.21), Vector((1, 0, 0)), UP, 0.07, 0.092, age=0.5)
    cards.card("x_cab_owner", (dx0 + 0.20, y0 - 0.0095, dz0 + 0.09), Vector((1, 0, 0)), UP, 0.064, 0.022, age=0.6)
    cards.card("x_cab_card", (x0 - 0.0015, cy + 0.08, zl), Vector((0, -1, 0)), UP, 0.064, 0.09, age=0.7)


def cylinder_cage(m, props, cards):
    """Two 10 kg gas cylinders in a galvanised cage: angle frame, bars, a sloped roof over the valves, the
    gate on the platform-edge side, chains, regulator and pigtails, the supply pipe into the right wall's base
    (behind the corner, unseen from the street), a coiled wash-down hose hung on the front."""
    c = E["cylinder_cage"]
    cx, cy = c["x"], c["y"]
    w, d, h = c["size"]
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2
    zt = PH + h
    G = "KX_Galv"
    geo.box(m, x0, x1, y0, y1, PH, PH + 0.012, G, 0.003)  # floor plate
    a = 0.035
    for sx, xx in ((1, x0), (-1, x1)):  # corner angles
        for sy, yy in ((1, y0), (-1, y1)):
            geo.box(m, *sorted((xx, xx + sx * a)), *sorted((yy, yy + sy * 0.004)), PH, zt, G, 0.001)
            geo.box(m, *sorted((xx, xx + sx * 0.004)), *sorted((yy, yy + sy * a)), PH, zt, G, 0.001)
    for zz in (PH + 0.012, PH + 0.40, zt - 0.03):  # rails round all four sides
        geo.box(m, x0, x1, y0, y0 + 0.004, zz, zz + 0.03, G, 0.001)
        geo.box(m, x0, x1, y1 - 0.004, y1, zz, zz + 0.03, G, 0.001)
        geo.box(m, x0, x0 + 0.004, y0, y1, zz, zz + 0.03, G, 0.001)
    for xx in [x0 + 0.06 + k * 0.057 for k in range(7)]:  # bars: front and back
        if xx > x1 - 0.04:
            break
        for yy in (y0, y1 - 0.004):
            geo.box(m, xx - 0.006, xx + 0.006, yy, yy + 0.004, PH + 0.04, zt - 0.03, G)
    for yy in [y0 + 0.06 + k * 0.057 for k in range(9)]:  # bars: the -X side
        if yy > y1 - 0.04:
            break
        geo.box(m, x0, x0 + 0.004, yy - 0.006, yy + 0.006, PH + 0.04, zt - 0.03, G)
    # gate on the +X side: own frame and bars, hinges at the back, a drop latch at the front
    for zz in (PH + 0.03, PH + 0.40, zt - 0.05):
        geo.box(m, x1 - 0.004, x1 + 0.004, y0 + 0.02, y1 - 0.02, zz, zz + 0.026, G, 0.001)
    for yy in [y0 + 0.05 + k * 0.057 for k in range(10)]:
        if yy > y1 - 0.04:
            break
        geo.box(m, x1 - 0.004, x1 + 0.004, yy - 0.006, yy + 0.006, PH + 0.05, zt - 0.05, G)
    for zz in (PH + 0.12, zt - 0.12):
        geo.cylinder(m, (x1 + 0.008, y1 - 0.02, zz), 0.009, 0.06, "KX_SteelDark", segments=10)
    geo.box(m, x1 + 0.004, x1 + 0.016, y0 + 0.03, y0 + 0.06, zt - 0.20, zt - 0.10, "KX_SteelDark", 0.002)
    # sloped roof sheet over the valves (lower at the front), with folded edges
    roof = [(x0 - 0.03, y0 - 0.04, zt + 0.01), (x1 + 0.03, y0 - 0.04, zt + 0.01), (x1 + 0.03, y1 + 0.02, zt + 0.06), (x0 - 0.03, y1 + 0.02, zt + 0.06)]
    geo.prism(m, ([Vector(p) for p in roof], [Vector((p[0], p[1], p[2] + 0.008)) for p in roof]), G)
    geo.box(m, x0 - 0.03, x1 + 0.03, y0 - 0.042, y0 - 0.036, zt - 0.012, zt + 0.016, G, 0.001)
    for xx in (x0 + 0.02, x1 - 0.02):  # roof brackets onto the corner angles
        for yy, zz in ((y0 + 0.01, zt + 0.004), (y1 - 0.01, zt + 0.05)):
            geo.box(m, xx - 0.012, xx + 0.012, yy - 0.012, yy + 0.012, zt - 0.02, zz + 0.002, G, 0.002)
    for (xx, yy) in ((x0 + 0.03, y0 + 0.03), (x1 - 0.03, y0 + 0.03), (x0 + 0.03, y1 - 0.03), (x1 - 0.03, y1 - 0.03)):
        geo.bolts(m, [(xx, yy, PH + 0.012)], "+Z", "KX_SteelDark", 0.009)
    # cylinders, valve outlets turned toward the back post, chains round their fronts
    cyl = [(cx, y1 - 0.155, 200.0), (cx + 0.004, y0 + 0.155, 160.0)]
    reg = Vector((x0 + 0.05, y1 - 0.03, PH + 0.70))
    view = Vector((-0.9, -0.44, 0.0)).normalized()  # from the cage toward the cinematic camera
    for k, (px, py, yaw) in enumerate(cyl):
        M = props.put("lpg", px, py, PH + 0.013, yaw)
        lv = (M.inverted().to_3x3() @ view).normalized()  # the same direction in the cylinder's own frame
        rt = Vector((-lv.y, lv.x, 0.0))
        rl = LPG["r"] + 0.0015
        card_on(cards, "x_lpg_label", M, (lv.x * rl, lv.y * rl, 0.27), rt, (0, 0, 1), 0.11, 0.07, age=0.6, bend=((0, 0, 0.27), rl))
        if k == 1:  # the filling tag hung on the collar
            card_on(cards, "x_lpg_tag", M, (lv.x * 0.084, lv.y * 0.084, 0.50), rt, (0, 0, 1), 0.046, 0.072, age=0.6)
        zc = PH + 0.42
        r = LPG["r"] + 0.018
        side = -1 if py < cy else 1  # chain round the side away from the cage's middle
        arc = [Vector((px + r * math.cos(math.radians(a)), py + side * r * math.sin(math.radians(a)), zc)) for a in range(175, 5, -15)]
        chain(m, [Vector((x0 + 0.01, py, zc))] + arc + [Vector((x1 - 0.01, py, zc))], G)
        # pigtail from the valve outlet to the regulator
        vo = M @ Vector((0.06, 0, 0.52))
        top = M @ Vector((0.06, 0, 0.66))  # straight up out of the collar first
        pts = [vo] + bezier(top, top + Vector((0, 0, 0.06)), reg + Vector((0.08, -0.06 * side, 0.12)), reg + Vector((0.0, 0.0, 0.02)), 10)
        tube_path(m, pts, 0.0045, "KX_Copper", 6)
    # regulator on a bracket on the back-left post, gauge facing the gate
    geo.box(m, x0 + 0.004, x0 + 0.03, y1 - 0.05, y1 - 0.01, reg.z - 0.06, reg.z + 0.06, G, 0.002)
    geo.box(m, reg.x - 0.022, reg.x + 0.022, reg.y - 0.02, reg.y + 0.02, reg.z - 0.04, reg.z + 0.02, "KX_Brass", 0.005)
    geo.cylinder(m, (reg.x, reg.y - 0.035, reg.z + 0.035), 0.028, 0.02, "KX_SteelDark", axis="Y", segments=16)  # regulator bonnet
    geo.cylinder(m, (reg.x + 0.035, reg.y, reg.z - 0.01), 0.02, 0.012, "KX_Chrome", axis="X", segments=14)  # gauge
    # supply pipe: out the back, down, along the right wall's foot (behind the corner) into the base
    px_ = x0 + 0.0885  # between the first two back bars
    pp = [reg + Vector((0, 0.0, -0.04)), Vector((px_, reg.y, reg.z - 0.04)), Vector((px_, y1 + 0.03, reg.z - 0.04)), Vector((px_, y1 + 0.03, PH + 0.13)),
          Vector((px_, Y0 + 0.40, PH + 0.13)), Vector((X1 + 0.075, Y0 + 0.40, PH + 0.13))]
    tube_path(m, pp, 0.011, "KX_GasPipe", 8)
    geo.cylinder(m, (X1 + 0.062, Y0 + 0.40, PH + 0.13), 0.022, 0.02, "KX_SteelDark", axis="X", segments=12)  # wall sleeve
    for yy in (Y0 + 0.0, Y0 + 0.25):
        geo.box(m, px_ - 0.02, px_ + 0.02, yy - 0.012, yy + 0.012, PH, PH + 0.125, "KX_SteelDark", 0.002)  # pipe saddles
    # the no-flames plate on the front, a hose coil hung on a hook on the front's right half
    cards.card("x_no_fire", (x0 + 0.14, y0 - 0.0035, zt - 0.10), Vector((1, 0, 0)), UP, 0.15, 0.064, age=0.6)
    geo.box(m, x0 + 0.06, x0 + 0.22, y0 - 0.003, y0, zt - 0.14, zt - 0.06, G, 0.002)  # plate backing
    hc = Vector((x1 - 0.13, y0 - 0.045, PH + 0.43))
    geo.box(m, hc.x - 0.012, hc.x + 0.012, y0 - 0.02, y0, hc.z + 0.12, hc.z + 0.16, "KX_SteelDark", 0.002)  # hook
    geo.pipe(m, (hc.x, y0 - 0.02, hc.z + 0.14), (hc.x, y0 - 0.05, hc.z + 0.15), 0.006, "KX_SteelDark", 6)
    for k in range(5):
        rr = 0.118 + 0.006 * (k % 2)
        put(m, Matrix.Translation(hc + Vector((0.004 * k - 0.008, -0.011 * k, -0.003 * k))) @ Matrix.Rotation(math.radians(90), 4, "X")
            @ Matrix.Rotation(math.radians(6 * k), 4, "Z"), ring, (0, 0, 0), rr, 0.0115, "KX_HoseGreen", 28, 6)
    tail = bezier(hc + Vector((0.11, -0.03, -0.06)), hc + Vector((0.16, -0.05, -0.18)), hc + Vector((0.10, -0.06, -0.30)), hc + Vector((0.06, -0.05, -0.33)), 8)
    tube_path(m, tail, 0.0115, "KX_HoseGreen", 8)
    geo.pipe(m, tail[-1], tail[-1] + Vector((-0.06, 0.0, -0.02)), 0.014, "KX_Brass", 10)  # spray nozzle


def bin_cans(m, cards):
    """Galvanised cans bin: corrugated body, rolled rim, base ring, side handles, a lid with a can hole."""
    b = E["bin_cans"]
    x, y, r, h = b["x"], b["y"], b["radius"], b["h"]
    z = PH
    prof = [(r * 0.92, 0.012), (r * 0.94, 0.03)]
    for zz in (0.10, 0.24, 0.38):
        prof += [(r * 0.955 + 0.0 * zz, zz - 0.03), (r * 0.985, zz - 0.012), (r * 0.985, zz + 0.012), (r * 0.96, zz + 0.03)]
    prof += [(r, h - 0.02), (r + 0.008, h - 0.006), (r + 0.004, h)]
    geo.lathe(m, (x, y, z), prof, "KX_Galv", 32, cap_top=False)
    geo.lathe(m, (x, y, z), [(r * 0.94, 0.0), (r * 0.96, 0.0), (r * 0.96, 0.02), (r * 0.94, 0.02)], "KX_Galv", 32, cap_bottom=False, cap_top=False)
    geo.lathe(m, (x, y, z), [(r * 0.94, h - 0.025), (0.0, h - 0.025)], "KX_Rubber", 24, cap_bottom=False, cap_top=False)  # inside, dark
    lid = [(0.046, h + 0.006), (0.046, h + 0.022), (0.06, h + 0.03), (r - 0.02, h + 0.026), (r + 0.012, h + 0.012), (r + 0.014, h - 0.004),
           (r + 0.006, h - 0.006)]
    geo.lathe(m, (x, y, z), lid, "KX_Galv", 32, cap_bottom=False, cap_top=False)
    geo.lathe(m, (x, y, z), [(0.0, h - 0.02), (0.046, h - 0.02), (0.046, h + 0.006)], "KX_Rubber", 20, cap_bottom=False, cap_top=False)  # can hole
    for s in (-1, 1):  # side handles across the gaze line (from the bin toward the cinematic camera)
        hx, hy = x + s * (r + 0.004) * 0.45, y + s * (r + 0.004) * 0.89
        geo.box(m, hx - 0.03, hx + 0.03, hy - 0.006, hy + 0.006, z + h - 0.10, z + h - 0.085, "KX_Galv", 0.003)
        ring(m, (hx + s * 0.002, hy + s * 0.004, z + h - 0.112), 0.026, 0.004, "KX_Galv", 12, 5, axis="X")
    face = Vector((-0.9, -0.44, 0.0)).normalized()  # toward the Mid camera
    cards.card("x_bin_cans", (x + face.x * (r * 0.985 + 0.002), y + face.y * (r * 0.985 + 0.002), z + 0.31 - 0.07), Vector((-face.y, face.x, 0)), UP,
               0.12, 0.084, age=0.6, bend=((x, y, z), r * 0.985 + 0.002))


# ---- build ---------------------------------------------------------------------------------------------

def build(B, coll, manifest):
    """Builds everything; returns (unique objects, prototype meshes {name: geo.Mesh}, placements)."""
    import bpy
    geo.reseed(808)
    materials = bpy.data.materials
    props = Props()
    cards = Cards(manifest)
    m = geo.Mesh("SM_Kiosk_Exterior")
    pedestal(m, cards)
    crate_stack(props, cards)
    locker(m, cards)
    cartons(m, cards)
    splash_block(m, "splash_left")
    bin_burnable(m, cards)
    tote(props, cards)
    jb_cable(m)
    utility_cabinet(m, cards)
    cylinder_cage(m, props, cards)
    bin_cans(m, cards)
    objs = {"exterior": m.build(coll, materials), "cards": cards.build(coll, materials, "SM_Kiosk_ExteriorCards", "KG_Exterior")}
    protos = {}
    for name in sorted({p[0] for p in props.items}):
        pm = geo.Mesh(f"SM_XP_{name}")
        PROTOS[name](pm)
        protos[name] = pm
    return objs, protos, props.items
