"""Step 4: roof machinery on the canopy deck (layout in kiosk_config.ROOF_*).

Roof pass (2026-10-04, brief 4): the roof is a crowded mechanical ecosystem of equipment installed
at different times, in four clusters that overlap from the camera side (left to right in frame):
  A  HVAC zone, front-left: the packaged HVAC unit on its roof curb right at the corner (the anchor
     mass: a fan in a square bezel, a service door, a porthole, a heavy lid), the louvred condenser
     behind it along the left edge, and a small unit with a round port behind that;
  B  the horizontal service vessel along the front: flanged into the HVAC through a reducer, two
     shell courses bolted together, a dished end with a blind-flanged nozzle, a gate valve, a relief
     valve and a sight glass, on saddles bolted to dunnage channels;
  C  upright vessels and elbows on a platform: a tall banded tank with a manway, a squat receiver
     with a gooseneck into the tank, and a tiered separator fed from the vessel by an elbowed line;
  D  a hose reel on a swivel base turned toward the street (its open front flange shows the coiled
     hose), the control cabinet under a rain hood, a slim sensor mast with the red beacon, and the
     white terminal box on the front-right corner.
Every unit stands on something (skid, curb, dunnage, stand or plinth), and lines go into the deck
through boots. The back half keeps a few lower units; they only show from above. Paints mark the
generations: faded grey and dull galvanised housings, dark painted steel, and warm aged metal on
the oldest pieces (the vessel). The utility pass (utilities.roof_lines) adds the disconnect switch,
the refrigerant pair, the condensate line and the mast coax.

History: the massing pass put the machinery on skids near the camera-side edges; the proportion
pass (brief 1B) lowered it into a front row and a second row on short stands.
"""
import math

from mathutils import Euler, Vector

import kiosk_config as C
from . import geo

DECK = C.CANOPY_TOP
EDGE_OUT = C.FASCIA["cap_proud"] + 0.02  # cables draped over the edge clear the coping
UP = Vector((0.0, 0.0, 1.0))
X = Vector((1.0, 0.0, 0.0))
Y = Vector((0.0, 1.0, 0.0))

MATERIALS = {
    "Beacon_Red": ((1.0, 0.06, 0.04), 0.4, 0.0, 8.0),
    # roof pass: paints for a second generation of equipment
    "Steel_Aged_Warm": ((0.24, 0.17, 0.12), 0.55, 0.45, 0.0),  # warm aged metal, the oldest pieces
    "Paint_Grey_Faded": ((0.40, 0.41, 0.40), 0.6, 0.15, 0.0),  # faded grey housing (the HVAC)
}


def ensure_materials(B):
    import bpy
    for name, (rgb, rough, metal, emit) in MATERIALS.items():
        m = B.mat(name, rgb, emit)
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return bpy.data.materials


# ---- Layout --------------------------------------------------------------------------------------

def boxes():
    return {b[0]: b for b in C.ROOF_BOXES}


def tanks():
    return {t[0]: t[1:] for t in C.ROOF_TANKS}


def supports():
    """Every support as (name, x0, x1, y0, y1, h): skids, curbs and dunnage rails."""
    return list(C.ROOF_SKIDS) + list(C.ROOF_CURBS) + [r[:6] for r in C.ROOF_RAILS]


def base_z(cx, cy):
    """Top of the highest support under (cx, cy), or the deck."""
    return DECK + max([h for _, x0, x1, y0, y1, h in supports() if x0 <= cx <= x1 and y0 <= cy <= y1], default=0.0)


def item_z(name):
    """Where a roof box stands: on the box it is stacked on, else on base_z, plus its stand (ROOF_LIFT)."""
    b = boxes()[name]
    under = C.ROOF_STACKED.get(name)
    if under:
        u = boxes()[under]
        return base_z(u[1], u[2]) + u[5]
    return base_z(b[1], b[2]) + C.ROOF_LIFT.get(name, 0.0)


def vessel_z():
    """Axis height of the horizontal service vessel."""
    return DECK + C.ROOF_VESSEL["z"]


def spread(a, b, pitch):
    n = max(1, round((b - a) / pitch))
    return [a + (b - a) * (k + 0.5) / n for k in range(n)]


# ---- Shapes --------------------------------------------------------------------------------------

def frame(axis):
    """Unit axis plus two unit vectors across it; (u, v, axis) is right-handed."""
    a = Vector(axis).normalized()
    u = a.cross(UP if abs(a.z) < 0.9 else X).normalized()
    return a, u, a.cross(u)


def revolve(m, center, axis, profile, mat, segments=28, caps=(True, True), closed=False, sharp=40.0):
    """Surface of revolution about any axis through `center`; profile = [(radius, t), ...] with t along
    the axis. The profile is split into separately shaded parts where it turns by more than `sharp`
    degrees, so flanges and shoulders keep crisp edges. closed=True joins its ends (a hose turn)."""
    c = Vector(center)
    a, u, v = frame(axis)
    parts = [list(profile)]
    if not closed and sharp:
        parts = [[profile[0]]]
        for i in range(1, len(profile)):
            parts[-1].append(profile[i])
            if i < len(profile) - 1:
                d0 = Vector((profile[i][0] - profile[i - 1][0], profile[i][1] - profile[i - 1][1]))
                d1 = Vector((profile[i + 1][0] - profile[i][0], profile[i + 1][1] - profile[i][1]))
                if d0.length > 1e-6 and d1.length > 1e-6 and math.degrees(d0.angle(d1)) > sharp:
                    parts.append([profile[i]])
    s = segments
    for pi, part in enumerate(parts):
        verts, faces = [], []
        for r, t in part:
            for k in range(s):
                ang = 2 * math.pi * k / s
                verts.append(c + a * t + (u * math.cos(ang) + v * math.sin(ang)) * r)
        n = len(part)
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            for k in range(s):
                k1 = (k + 1) % s
                faces.append((i * s + k, i * s + k1, j * s + k1, j * s + k))
        if not closed:
            if caps[0] and pi == 0 and part[0][0] > 1e-6:
                faces.append(tuple(reversed(range(s))))
            if caps[1] and pi == len(parts) - 1 and part[-1][0] > 1e-6:
                faces.append(tuple(range((n - 1) * s, n * s)))
        m.add_raw(verts, faces, mat, True)


def disc(m, center, axis, r, t, mat, segments=28):
    """Short solid cylinder centred on `center` along any axis (flange, boss, hub)."""
    revolve(m, center, axis, [(r, -t / 2), (r, t / 2)], mat, segments)


def torus(m, center, axis, R, r, mat, segments=40, sides=8):
    revolve(m, center, axis, [(R + r * math.cos(2 * math.pi * i / sides), r * math.sin(2 * math.pi * i / sides))
                              for i in range(sides)], mat, segments, closed=True)


def line(m, pts, r, mat, bend=None, flex=False):
    """A pipe through the points with rounded bends (or a flexible spline), swept like the utility pass's runs."""
    from .utilities import fillet, sides_for, spline, tube  # utilities imports this module
    pts = [Vector(p) for p in pts]
    tube(m, spline(pts) if flex else fillet(pts, bend if bend is not None else max(0.05, 3 * r)), r, mat, sides_for(r))


def obox(m, c, ax, ay, sx, sy, sz, mat):
    from .utilities import obox as ob
    ob(m, Vector(c), Vector(ax), Vector(ay), None, sx, sy, sz, mat)


def boot(m, x, y, r, z=DECK):
    """Rubber boot where a pipe or conduit goes down through the deck (or a skid's plate)."""
    geo.lathe(m, (x, y, z), [(r + 0.035, 0.0), (r + 0.03, 0.015), (r + 0.01, 0.06), (r + 0.005, 0.075)], "Rubber_Black", 16)


def cabinet(m, cx, cy, w, d, h, body="Steel_Grey", lid=None, z0=DECK):
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2
    geo.box(m, x0 + 0.03, x1 - 0.03, y0 + 0.03, y1 - 0.03, z0, z0 + 0.04, "Steel_Dark", 0.004)  # plinth
    geo.box(m, x0, x1, y0, y1, z0 + 0.04, z0 + h, body, 0.018, 2)
    if lid:
        geo.box(m, x0 - 0.025, x1 + 0.025, y0 - 0.025, y1 + 0.025, z0 + h, z0 + h + 0.05, lid, 0.01, 2)
    return x0, x1, y0, y1, z0 + 0.04, z0 + h


def louvers(m, axis_face, fixed, a0, a1, z0, z1, n, mat="Steel_Dark"):
    """Horizontal slats on a face: axis_face '-X' or '-Y' (the face's outward normal)."""
    for k in range(n):
        z = z0 + (k + 0.5) * (z1 - z0) / n
        if axis_face == "-X":
            geo.box(m, fixed - 0.012, fixed, a0, a1, z - 0.008, z + 0.008, mat, 0.002)
        else:
            geo.box(m, a0, a1, fixed - 0.012, fixed, z - 0.008, z + 0.008, mat, 0.002)


def hood(m, x0, x1, y0, y1, z, front, back, over=0.06, mat="Steel_Dark"):
    """Sloped rain hood (a wedge): `front` high at the -Y edge, `back` at the +Y edge, overhanging by `over`."""
    ax0, ax1, ay0, ay1 = x0 - over, x1 + over, y0 - over, y1 + over * 0.5
    vs = [(ax0, ay0, z), (ax1, ay0, z), (ax1, ay1, z), (ax0, ay1, z),
          (ax0, ay0, z + front), (ax1, ay0, z + front), (ax1, ay1, z + back), (ax0, ay1, z + back)]
    m.add_raw(vs, [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)], mat)


# ---- Supports ------------------------------------------------------------------------------------

def skids(m):
    """Equipment bases: a perimeter of steel channels, cross members, a chequer-plate top and
    short feet onto the deck."""
    for _, x0, x1, y0, y1, h in C.ROOF_SKIDS:
        top = DECK + h
        c = 0.09  # channel width
        for (a0, a1, b0, b1) in ((x0, x1, y0, y0 + c), (x0, x1, y1 - c, y1), (x0, x0 + c, y0, y1), (x1 - c, x1, y0, y1)):
            geo.box(m, a0, a1, b0, b1, DECK + 0.03, top - 0.012, "Steel_Dark", 0.006, 2)
        n = max(1, int((x1 - x0) / 0.7))
        for k in range(1, n + 1):
            x = x0 + k * (x1 - x0) / (n + 1)
            geo.box(m, x - 0.035, x + 0.035, y0 + c, y1 - c, top - 0.09, top - 0.012, "Steel_Dark", 0.004)
        geo.box(m, x0 + 0.01, x1 - 0.01, y0 + 0.01, y1 - 0.01, top - 0.012, top, "Steel_Grey", 0.003)
        for fx in (x0 + 0.06, x1 - 0.06):
            for fy in (y0 + 0.06, y1 - 0.06):
                geo.box(m, fx - 0.06, fx + 0.06, fy - 0.06, fy + 0.06, DECK, DECK + 0.03, "Steel_Dark", 0.004)


def curbs(m):
    """Flashed roof curbs: a galvanised frame with a flashing skirt screwed down to the deck and a dark
    cap; the unit sits on top, its duct and conduits go down through it."""
    for _, x0, x1, y0, y1, h in C.ROOF_CURBS:
        top = DECK + h
        geo.box(m, x0 - 0.05, x1 + 0.05, y0 - 0.05, y1 + 0.05, DECK, DECK + 0.03, "Steel_Dark", 0.006, 2)  # skirt
        geo.box(m, x0, x1, y0, y1, DECK + 0.02, top - 0.02, "Steel_Galv_Dull", 0.006, 2)
        geo.box(m, x0 - 0.012, x1 + 0.012, y0 - 0.012, y1 + 0.012, top - 0.025, top, "Steel_Dark", 0.004)  # cap
        pts = [(x, y0 - 0.032, DECK + 0.03) for x in spread(x0, x1, 0.22)] + [(x0 - 0.032, y, DECK + 0.03) for y in spread(y0, y1, 0.22)]
        geo.bolts(m, pts, "+Z", "Steel_Dark", 0.011)


def post(m, x, y, z1):
    """A short post on a base plate, or a rubber pad where there is no room for one."""
    if z1 - DECK > 0.035:
        geo.box(m, x - 0.025, x + 0.025, y - 0.025, y + 0.025, DECK + 0.012, z1, "Steel_Dark", 0.003)
        geo.box(m, x - 0.055, x + 0.055, y - 0.055, y + 0.055, DECK, DECK + 0.012, "Steel_Dark", 0.003)
    else:
        geo.box(m, x - 0.05, x + 0.05, y - 0.05, y + 0.05, DECK, z1, "Rubber_Black", 0.004)


def rails(m):
    """Dunnage: two steel I-sections along `axis` on short posts (or pads), the unit bolted on top."""
    for _, x0, x1, y0, y1, h, axis in C.ROOF_RAILS:
        top = DECK + h
        lo = top - min(0.08, h - 0.02)
        if axis == "Y":
            for a in (x0 + 0.03, x1 - 0.03):
                geo.ibeam(m, "Y", a, y0, y1, lo, top, "Steel_Charcoal", width=0.06)
                for p in (y0 + 0.07, y1 - 0.07):
                    post(m, a, p, lo)
        else:
            for a in (y0 + 0.03, y1 - 0.03):
                geo.ibeam(m, "X", a, x0, x1, lo, top, "Steel_Charcoal", width=0.06)
                for p in (x0 + 0.07, x1 - 0.07):
                    post(m, p, a, lo)


def stands(m):
    """Short steel stands under the lifted units (ROOF_LIFT): a channel frame on corner legs."""
    for name, lift in C.ROOF_LIFT.items():
        _, cx, cy, w, d, _ = boxes()[name]
        z0, z1 = base_z(cx, cy), item_z(name)
        x0, x1, y0, y1 = cx - w / 2 + 0.02, cx + w / 2 - 0.02, cy - d / 2 + 0.02, cy + d / 2 - 0.02
        c = 0.05
        for (a0, a1, b0, b1) in ((x0, x1, y0, y0 + c), (x0, x1, y1 - c, y1), (x0, x0 + c, y0, y1), (x1 - c, x1, y0, y1)):
            geo.box(m, a0, a1, b0, b1, z1 - 0.04, z1, "Steel_Dark", 0.004)
        for lx in (x0 + 0.025, x1 - 0.025):
            for ly in (y0 + 0.025, y1 - 0.025):
                geo.box(m, lx - 0.025, lx + 0.025, ly - 0.025, ly + 0.025, z0, z1 - 0.04, "Steel_Dark", 0.004)


# ---- Cluster A: HVAC zone ------------------------------------------------------------------------

def hvac(m):
    """The anchor mass: a packaged HVAC unit on its curb at the front-left corner, broad rather than
    tall. Front: the fan in a square bezel behind a guard, a hinged service door with a louvred kick
    panel and a nameplate (the disconnect switch right of the door comes from utilities.roof_lines).
    Left side: an inspection porthole and a screwed filter panel. Top: a heavy lid with a drip edge,
    lifting lugs and an exhaust hood at the back. Right side: the plate the service vessel's stub bolts
    to. Kept low: at the corner it is the nearest unit to the camera and sets the silhouette's top."""
    _, cx, cy, w, d, h = boxes()["TallCabinet"]
    x0, x1, y0, y1, zb, zt = cabinet(m, cx, cy, w, d, h, "Paint_Grey_Faded", z0=item_z("TallCabinet"))
    geo.box(m, x0 - 0.045, x1 + 0.045, y0 - 0.045, y1 + 0.045, zt, zt + 0.05, "Steel_Charcoal", 0.012, 2)  # lid
    geo.box(m, x0 - 0.05, x1 + 0.05, y0 - 0.05, y1 + 0.05, zt - 0.03, zt + 0.004, "Steel_Charcoal", 0.004)  # drip edge
    for lx in (x0 + 0.07, x1 - 0.07):  # lifting lugs, at the back (the front corners would set the silhouette's top)
        geo.box(m, lx - 0.015, lx + 0.015, y1 - 0.07, y1 + 0.01, zt + 0.05, zt + 0.10, "Steel_Dark", 0.006)
    geo.box(m, x0 + 0.755, x0 + 0.77, y0 - 0.006, y0, zb + 0.02, zt - 0.02, "Steel_Dark")  # panel seam

    # fan: bezel plate, shroud ring, dark throat, five pitched blades, a ring-and-bar guard, hub
    fx, fz, r = x0 + 0.40, zb + 0.32, 0.23
    b = r + 0.07
    geo.box(m, fx - b, fx + b, y0 - 0.018, y0, fz - b, fz + b, "Steel_Dark", 0.008, 2)
    geo.rivets(m, [(fx + sx * (b - 0.03), y0 - 0.018, fz + sz * (b - 0.03)) for sx in (-1, 1) for sz in (-1, 1)], "-Y", "Steel_Grey", 0.012)
    disc(m, (fx, y0 - 0.035, fz), Y, r + 0.025, 0.03, "Steel_Dark", 36)
    geo.cylinder(m, (fx, y0 - 0.052, fz), r + 0.004, 0.004, "Rubber_Black", axis="Y", segments=36)
    geo.cylinder(m, (fx, y0 - 0.09, fz), r + 0.025, 0.075, "Steel_Dark", axis="Y", segments=36, cap=False)  # shroud lip
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        c = (fx + r * 0.5 * math.cos(a), y0 - 0.085, fz + r * 0.5 * math.sin(a))
        geo.box(m, c[0] - r * 0.42, c[0] + r * 0.42, c[1] - 0.004, c[1] + 0.004, c[2] - 0.055, c[2] + 0.055, "Steel_Galv_Dull",
                rot=Euler((0.5, -a, 0.0), "XYZ"))
    for rr in (r * 0.98, r * 0.68, r * 0.36):
        torus(m, (fx, y0 - 0.13, fz), Y, rr, 0.0045, "Steel_Grey", 36, 6)
    for a in (0.0, math.pi / 2):
        geo.pipe(m, (fx - r * math.cos(a), y0 - 0.13, fz - r * math.sin(a)), (fx + r * math.cos(a), y0 - 0.13, fz + r * math.sin(a)),
                 0.006, "Steel_Grey", 6)
    disc(m, (fx, y0 - 0.105, fz), Y, 0.045, 0.04, "Steel_Dark", 16)

    # service door with hinges, handle, louvred kick panel and a nameplate
    dx0, dx1, dz0, dz1 = x0 + 0.80, x0 + 1.05, zb + 0.05, zt - 0.06
    geo.box(m, dx0, dx1, y0 - 0.01, y0, dz0, dz1, "Paint_Grey_Faded", 0.004)
    for hz in (dz0 + 0.1, dz1 - 0.1):
        geo.cylinder(m, (dx0 - 0.004, y0 - 0.014, hz), 0.012, 0.07, "Steel_Dark", segments=10)
    geo.box(m, dx1 - 0.05, dx1 - 0.03, y0 - 0.045, y0 - 0.01, dz0 + 0.3, dz0 + 0.46, "Steel_Dark", 0.006)
    louvers(m, "-Y", y0 - 0.01, dx0 + 0.03, dx1 - 0.03, dz0 + 0.04, dz0 + 0.24, 5)
    geo.box(m, dx0 + 0.04, dx0 + 0.16, y0 - 0.014, y0 - 0.01, dz1 - 0.14, dz1 - 0.07, "Stock_White")

    # left side: porthole near the front, a screwed filter access panel with two pull handles behind it
    py, pz, pr = y0 + 0.26, zt - 0.22, 0.10
    geo.cylinder(m, (x0 - 0.012, py, pz), pr + 0.03, 0.024, "Steel_Dark", axis="X", segments=28)
    geo.cylinder(m, (x0 - 0.026, py, pz), pr, 0.006, "Glass_Wired", axis="X", segments=28)
    geo.rivets(m, [(x0 - 0.024, py + (pr + 0.016) * math.cos(2 * math.pi * k / 8), pz + (pr + 0.016) * math.sin(2 * math.pi * k / 8))
                   for k in range(8)], "-X", "Steel_Grey", 0.008)
    a0, a1, b0, b1 = y0 + 0.48, y1 - 0.08, zb + 0.07, zt - 0.09
    geo.box(m, x0 - 0.012, x0, a0, a1, b0, b1, "Paint_Grey_Faded", 0.004)
    geo.bolts(m, [(x0 - 0.012, a, b) for a in (a0 + 0.03, a1 - 0.03) for b in (b0 + 0.03, b1 - 0.03)], "-X", "Steel_Dark", 0.011)
    for b in (b0 + 0.16, b1 - 0.16):
        geo.box(m, x0 - 0.045, x0 - 0.012, (a0 + a1) / 2 - 0.07, (a0 + a1) / 2 + 0.07, b - 0.012, b + 0.012, "Steel_Dark", 0.005)
    louvers(m, "-X", x0 - 0.012, a0 + 0.05, a1 - 0.05, b0 + 0.03, b0 + 0.13, 3)

    # exhaust hood on the lid's front-right (a step in the long lid line; the front-left corner is the
    # silhouette's top and stays clear), louvres facing the street
    hood(m, x1 - 0.44, x1 - 0.12, y0 + 0.12, y0 + 0.40, zt + 0.05, 0.15, 0.07, 0.03, "Steel_Charcoal")
    louvers(m, "-Y", y0 + 0.09, x1 - 0.43, x1 - 0.13, zt + 0.065, zt + 0.185, 3)

    # right side: bolting plate for the vessel's stub
    v = C.ROOF_VESSEL
    vz = vessel_z()
    geo.box(m, x1, x1 + 0.012, v["cy"] - 0.14, v["cy"] + 0.14, vz - 0.14, vz + 0.14, "Steel_Dark", 0.004)
    geo.bolts(m, [(x1 + 0.012, v["cy"] + sy * 0.11, vz + sz * 0.11) for sy in (-1, 1) for sz in (-1, 1)], "+X", "Steel_Dark", 0.012)


def ac_condenser(m):
    """The louvred condenser along the left edge, behind the HVAC (older, dull galvanised): a deep
    grille of angled fins over a dark coil across its street side, a screwed service panel at the front."""
    _, cx, cy, w, d, h = boxes()["ACCondenser"]
    x0, x1, y0, y1, zb, zt = cabinet(m, cx, cy, w, d, h, "Steel_Galv_Dull", "Steel_Dark", z0=item_z("ACCondenser"))
    g0, g1, gz0, gz1 = y0 + 0.10, y1 - 0.10, zb + 0.08, zt - 0.07
    fr = 0.035
    for (a0, a1, b0, b1) in ((g0 - fr, g1 + fr, gz0 - fr, gz0), (g0 - fr, g1 + fr, gz1, gz1 + fr), (g0 - fr, g0, gz0, gz1), (g1, g1 + fr, gz0, gz1)):
        geo.box(m, x0 - 0.032, x0, a0, a1, b0, b1, "Steel_Dark", 0.004)
    geo.box(m, x0 - 0.004, x0 + 0.002, g0, g1, gz0, gz1, "Rubber_Black")  # dark coil behind the fins
    n = int((gz1 - gz0) / 0.042)
    for k in range(n):
        z = gz0 + (k + 0.5) * (gz1 - gz0) / n
        geo.box(m, x0 - 0.036, x0 - 0.006, g0, g1, z - 0.002, z + 0.002, "Steel_Galv_Dull", rot=Euler((0.0, math.radians(-38), 0.0)))
    ym = (g0 + g1) / 2
    geo.box(m, x0 - 0.034, x0, ym - 0.018, ym + 0.018, gz0, gz1, "Steel_Dark", 0.004)  # mullion
    # service panel on the front face, screwed at the corners
    sx0, sx1, sz0, sz1 = x0 + 0.06, x1 - 0.18, zb + 0.06, zt - 0.10
    geo.box(m, sx0, sx1, y0 - 0.008, y0, sz0, sz1, "Steel_Galv_Dull", 0.003)
    geo.bolts(m, [(x, y0 - 0.008, z) for x in (sx0 + 0.025, sx1 - 0.025) for z in (sz0 + 0.025, sz1 - 0.025)], "-Y", "Steel_Dark", 0.011)


def small_unit(m):
    """Small older unit at the back of the left edge, with a round port on its street side."""
    _, cx, cy, w, d, h = boxes()["SmallUnit"]
    x0, x1, y0, y1, zb, zt = cabinet(m, cx, cy, w, d, h, "Machine_Body", "Rust_Red", z0=item_z("SmallUnit"))
    pz = zb + (zt - zb) * 0.55
    geo.cylinder(m, (x0 - 0.015, cy - 0.06, pz), 0.09, 0.03, "Steel_Dark", axis="X", segments=24)
    geo.cylinder(m, (x0 - 0.031, cy - 0.06, pz), 0.065, 0.004, "Rubber_Black", axis="X", segments=24)
    geo.box(m, x0 - 0.03, x0, cy + 0.14, cy + 0.16, pz - 0.08, pz + 0.08, "Steel_Dark", 0.004)  # handle
    louvers(m, "-Y", y0, x0 + 0.08, x1 - 0.08, zb + 0.06, zb + 0.22, 4)


# ---- Cluster B: the horizontal service vessel ----------------------------------------------------

def vessel(m):
    """The oldest piece on the roof (warm aged metal): a horizontal vessel along the front that bridges
    the HVAC and the tanks. Two shell courses bolted at a flanged joint; a reducer and a flanged stub
    into the HVAC's side; a dished right end with a blind-flanged nozzle; on top a gate valve, a relief
    valve and the elbowed line to the separator; a sight glass and a nameplate on the front; two
    saddles bolted to the dunnage channels."""
    v = C.ROOF_VESSEL
    x0, x1, cy, r, sr, jx = v["x0"], v["x1"], v["cy"], v["r"], v["stub_r"], v["joint_x"]
    cz = vessel_z()
    hx1 = boxes()["TallCabinet"][1] + boxes()["TallCabinet"][3] / 2
    red0 = x0 - 0.14
    dish = [(r * 0.95, 0.03), (r * 0.82, 0.06), (r * 0.6, 0.085), (r * 0.3, 0.099), (0.0, 0.103)]
    revolve(m, (0, cy, cz), X, [(sr, red0), (r, x0), (r, x1)] + [(rr, x1 + t) for rr, t in dish], "Steel_Aged_Warm", 36)
    # flanged stub from the HVAC's bolting plate to the reducer
    revolve(m, (0, cy, cz), X, [(sr, hx1 + 0.012), (sr, red0)], "Steel_Aged_Warm", 20)
    for fxc in (hx1 + 0.024, red0 - 0.012, red0 + 0.012):
        disc(m, (fxc, cy, cz), X, sr + 0.045, 0.024, "Steel_Dark", 20)
    # flanged joint between the shell courses, bolts on both faces
    ft = 0.024
    for fxc in (jx - ft / 2, jx + ft / 2):
        disc(m, (fxc, cy, cz), X, r + 0.035, ft, "Steel_Dark", 40)
    ring = [(cy + (r + 0.019) * math.cos(2 * math.pi * k / 14), cz + (r + 0.019) * math.sin(2 * math.pi * k / 14)) for k in range(14)]
    geo.bolts(m, [(jx - ft, y, z) for y, z in ring], "-X", "Steel_Dark", 0.011)
    geo.bolts(m, [(jx + ft, y, z) for y, z in ring], "+X", "Steel_Dark", 0.011)
    # blind-flanged nozzle on the dished end
    revolve(m, (0, cy, cz), X, [(0.07, x1 + 0.08), (0.07, x1 + 0.15)], "Steel_Aged_Warm", 20)
    disc(m, (x1 + 0.1625, cy, cz), X, 0.11, 0.025, "Steel_Dark", 24)
    geo.bolts(m, [(x1 + 0.175, cy + 0.088 * math.cos(2 * math.pi * k / 8), cz + 0.088 * math.sin(2 * math.pi * k / 8)) for k in range(8)],
              "+X", "Steel_Dark", 0.01)

    top = cz + r
    # gate valve on a flanged nozzle, red handwheel
    gx = x0 + 0.25
    geo.cylinder(m, (gx, cy, top + 0.025), 0.045, 0.09, "Steel_Grey", segments=16)
    geo.cylinder(m, (gx, cy, top + 0.075), 0.075, 0.02, "Steel_Dark", segments=20)
    geo.box(m, gx - 0.06, gx + 0.06, cy - 0.045, cy + 0.045, top + 0.085, top + 0.19, "Steel_Dark", 0.01, 2)  # body
    geo.cylinder(m, (gx, cy, top + 0.23), 0.03, 0.08, "Steel_Grey", segments=12)  # bonnet
    geo.pipe(m, (gx, cy, top + 0.27), (gx, cy, top + 0.33), 0.008, "Steel_Grey", 6)
    torus(m, (gx, cy, top + 0.32), UP, 0.07, 0.007, "Stock_Red", 28, 6)
    for a in (0.0, math.pi / 2):
        geo.pipe(m, (gx - 0.07 * math.cos(a), cy - 0.07 * math.sin(a), top + 0.32), (gx + 0.07 * math.cos(a), cy + 0.07 * math.sin(a), top + 0.32),
                 0.005, "Stock_Red", 5)
    # relief valve beside the joint: a short body with a conical cap
    rx = jx + 0.18
    geo.cylinder(m, (rx, cy + 0.06, top + 0.03), 0.032, 0.08, "Steel_Grey", segments=14)
    geo.lathe(m, (rx, cy + 0.06, top + 0.07), [(0.04, 0.0), (0.04, 0.04), (0.015, 0.1), (0.0, 0.105)], "Steel_Dark", 14, cap_top=False)
    # line to the separator: up from a flanged nozzle near the right end, back, and into its upper drum
    sx_, sy_, sr_, _ = tanks()["Separator"]
    nx = x1 - 0.14
    geo.cylinder(m, (nx, cy, top + 0.03), 0.075, 0.02, "Steel_Dark", segments=20)
    zl, zh = base_z(sx_, sy_) + 0.80, top + 0.13
    line(m, [(nx, cy, top - 0.03), (nx, cy, zh), (sx_ - 0.03, cy, zh), (sx_ - 0.03, sy_ + 0.112, zl)], 0.042, "Steel_Grey", bend=0.07)
    disc(m, (sx_ - 0.03, sy_ + 0.13, zl), Y, 0.07, 0.02, "Steel_Dark", 20)
    # sight glass and nameplate on the front
    gxs = x1 - 0.32
    for zz in (cz - 0.12, cz + 0.12):
        yy = cy - math.sqrt(r * r - (zz - cz) ** 2)
        geo.pipe(m, (gxs, yy + 0.01, zz), (gxs, cy - r - 0.06, zz), 0.016, "Steel_Grey", 10)
        geo.cylinder(m, (gxs, cy - r - 0.06, zz), 0.024, 0.04, "Steel_Dark", segments=12)
    geo.pipe(m, (gxs, cy - r - 0.06, cz - 0.10), (gxs, cy - r - 0.06, cz + 0.10), 0.011, "Glass_Wired", 10)
    for dx in (-0.022, 0.022):
        geo.pipe(m, (gxs + dx, cy - r - 0.075, cz - 0.10), (gxs + dx, cy - r - 0.075, cz + 0.10), 0.003, "Steel_Dark", 4)
    geo.box(m, x0 + 0.50, x0 + 0.66, cy - r - 0.004, cy - r + 0.02, cz - 0.04, cz + 0.05, "Stock_White")
    # saddles: a plate following the shell's underside on a base plate bolted to the channel
    for sx in v["saddles"]:
        zb = base_z(sx, cy)
        half = r * 0.8
        arc = math.asin(half / (r + 0.008))
        pts = [(cy - half, zb + 0.016), (cy + half, zb + 0.016)]
        pts += [(cy + (r + 0.008) * math.sin(arc - 2 * arc * k / 10), cz - (r + 0.008) * math.cos(arc - 2 * arc * k / 10)) for k in range(11)]
        geo.prism(m, ([(sx - 0.012, yy, zz) for yy, zz in pts], [(sx + 0.012, yy, zz) for yy, zz in pts]), "Steel_Charcoal")
        geo.box(m, sx - 0.05, sx + 0.05, cy - half - 0.04, cy + half + 0.04, zb, zb + 0.016, "Steel_Dark", 0.003)
        geo.bolts(m, [(sx + dx, cy + sy * (half + 0.015), zb + 0.016) for dx in (-0.028, 0.028) for sy in (-1, 1)], "+Z", "Steel_Dark", 0.011)
        disc(m, (sx, cy, cz), X, r + 0.006, 0.09, "Steel_Aged_Warm", 36)  # wear plate band


# ---- Cluster C: upright vessels and elbows -------------------------------------------------------

def tank(m):
    """Tall banded tank (galvanised) with a domed head: uneven bands, a bolted manway, a top nozzle with
    a relief valve, a pressure gauge, and a side valve with a red handwheel."""
    cx, cy, r, h = tanks()["Tank"]
    zb = base_z(cx, cy)
    geo.cylinder(m, (cx, cy, zb + 0.03), r * 1.1, 0.06, "Steel_Dark", segments=28)  # base ring
    revolve(m, (cx, cy, zb), UP, [(r, 0.06), (r, 0.06 + h), (r * 0.94, h + 0.06 + r * 0.22), (r * 0.72, h + 0.06 + r * 0.42),
                                  (r * 0.38, h + 0.06 + r * 0.53), (0.0, h + 0.06 + r * 0.56)], "Steel_Galvanised", 32)
    for f in (0.16, 0.58, 0.9):
        geo.cylinder(m, (cx, cy, zb + 0.06 + h * f), r + 0.008, 0.03, "Steel_Dark", segments=32, cap=False)
    # manway on the street side, bolted
    mz = zb + 0.06 + h * 0.36
    my = cy - r + 0.01
    geo.cylinder(m, (cx - 0.02, my - 0.02, mz), 0.11, 0.05, "Steel_Galvanised", axis="Y", segments=24)
    geo.cylinder(m, (cx - 0.02, my - 0.052, mz), 0.125, 0.018, "Steel_Dark", axis="Y", segments=24)
    geo.bolts(m, [(cx - 0.02 + 0.105 * math.cos(2 * math.pi * k / 10), my - 0.061, mz + 0.105 * math.sin(2 * math.pi * k / 10))
                  for k in range(10)], "-Y", "Steel_Dark", 0.01)
    # top nozzle, flange and a relief valve
    zt = zb + 0.06 + h + r * 0.56
    geo.cylinder(m, (cx, cy, zt + 0.02), 0.045, 0.06, "Steel_Grey", segments=14)
    geo.cylinder(m, (cx, cy, zt + 0.055), 0.07, 0.018, "Steel_Dark", segments=18)
    geo.lathe(m, (cx, cy, zt + 0.064), [(0.035, 0.0), (0.035, 0.03), (0.012, 0.06), (0.0, 0.065)], "Steel_Dark", 14, cap_top=False)
    # pressure gauge facing the street, valve with a red handwheel at the back
    gz = zb + h * 0.72
    geo.pipe(m, (cx - 0.12, cy - r + 0.03, gz), (cx - 0.12, cy - r - 0.04, gz), 0.01, "Steel_Grey", 6)
    geo.cylinder(m, (cx - 0.12, cy - r - 0.055, gz), 0.04, 0.03, "Steel_Dark", axis="Y", segments=16)
    geo.cylinder(m, (cx - 0.12, cy - r - 0.071, gz), 0.032, 0.004, "Paper_White", axis="Y", segments=16)
    vz, vx = zb + 0.06 + h * 0.25, cx + 0.08
    geo.pipe(m, (vx, cy + r - 0.02, vz), (vx, cy + r + 0.10, vz), 0.022, "Steel_Grey", 10)
    geo.box(m, vx - 0.04, vx + 0.04, cy + r + 0.07, cy + r + 0.15, vz - 0.04, vz + 0.04, "Steel_Dark", 0.008)
    geo.pipe(m, (vx, cy + r + 0.11, vz + 0.04), (vx, cy + r + 0.11, vz + 0.12), 0.007, "Steel_Grey", 6)
    torus(m, (vx, cy + r + 0.11, vz + 0.12), UP, 0.05, 0.006, "Stock_Red", 24, 6)
    # pressure switch on the right side (its flex runs to the control cabinet)
    geo.box(m, cx + r - 0.01, cx + r + 0.06, cy + 0.02, cy + 0.12, zb + h * 0.62, zb + h * 0.62 + 0.1, "Steel_Grey", 0.008)


def receiver(m):
    """Squat receiver on three legs (dark painted), flat bolted top, a gooseneck into the tank's head."""
    cx, cy, r, h = tanks()["Receiver"]
    zb = base_z(cx, cy)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.5
        lx, ly = cx + r * 0.72 * math.cos(a), cy + r * 0.72 * math.sin(a)
        geo.pipe(m, (lx, ly, zb), (lx, ly, zb + 0.11), 0.02, "Steel_Dark", 8)
        geo.box(m, lx - 0.035, lx + 0.035, ly - 0.035, ly + 0.035, zb, zb + 0.012, "Steel_Dark", 0.003)
    z0 = zb + 0.08
    revolve(m, (cx, cy, z0), UP, [(0.0, 0.0), (r * 0.7, 0.005), (r * 0.95, 0.025), (r, 0.05), (r, h)], "Steel_Charcoal", 28)
    zt = z0 + h
    geo.cylinder(m, (cx, cy, zt + 0.015), r + 0.035, 0.03, "Steel_Dark", segments=28)
    geo.cylinder(m, (cx, cy, zt + 0.04), r + 0.025, 0.02, "Steel_Charcoal", segments=28)
    geo.bolts(m, [(cx + (r + 0.016) * math.cos(2 * math.pi * k / 10), cy + (r + 0.016) * math.sin(2 * math.pi * k / 10), zt + 0.05)
                  for k in range(10)], "+Z", "Steel_Dark", 0.011)
    # gooseneck: up from the top, over, into the tank's head (flanged both ends)
    tx, ty, tr, th = tanks()["Tank"]
    d = Vector((tx - cx, ty - cy, 0.0)).normalized()
    zg = base_z(tx, ty) + 0.06 + th * 0.78
    end = Vector((tx, ty, zg)) - d * (tr - 0.006)
    zh = zt + 0.24
    geo.cylinder(m, (cx, cy, zt + 0.065), 0.07, 0.02, "Steel_Dark", segments=18)
    line(m, [(cx, cy, zt + 0.05), (cx, cy, zh), (end.x - d.x * 0.10, end.y - d.y * 0.10, zh), (end.x, end.y, zg)], 0.04,
         "Steel_Galv_Dull", bend=0.08)
    disc(m, end - d * 0.02, d, 0.065, 0.02, "Steel_Dark", 18)
    # a small gauge on the street side
    geo.cylinder(m, (cx, cy - r - 0.02, z0 + h * 0.6), 0.035, 0.03, "Steel_Dark", axis="Y", segments=16)
    geo.cylinder(m, (cx, cy - r - 0.036, z0 + h * 0.6), 0.028, 0.004, "Paper_White", axis="Y", segments=16)


def separator(m):
    """Tiered separator (faded grey): a drum with a domed shoulder, a flanged neck, a narrower upper drum
    under a domed cap and a capped nozzle; a drain at the back goes down into the deck."""
    cx, cy, r, h = tanks()["Separator"]
    zb = base_z(cx, cy)
    k = h / 0.98
    prof = [(r + 0.02, 0.0), (r + 0.02, 0.06), (r, 0.06), (r, 0.5 * k), (r * 0.88, 0.55 * k), (r * 0.7, 0.585 * k), (0.09, 0.6 * k),
            (0.09, 0.66 * k), (0.13, 0.66 * k), (0.13, 0.69 * k), (0.12, 0.69 * k), (0.12, 0.86 * k), (0.1, 0.895 * k),
            (0.06, 0.92 * k), (0.03, 0.93 * k), (0.03, 0.98 * k), (0.0, 0.98 * k)]
    revolve(m, (cx, cy, zb), UP, prof, "Paint_Grey_Faded", 28)
    geo.bolts(m, [(cx + 0.112 * math.cos(2 * math.pi * j / 8), cy + 0.112 * math.sin(2 * math.pi * j / 8), zb + 0.69 * k) for j in range(8)],
              "+Z", "Steel_Dark", 0.01)
    geo.cylinder(m, (cx, cy, zb + 0.95 * k), 0.045, 0.015, "Steel_Dark", segments=14)  # nozzle cap
    # drain from the back of the drum, down through the deck behind the platform
    yb = C.ROOF_SKIDS[0][4] + 0.10
    line(m, [(cx, cy + r - 0.01, zb + 0.14), (cx, yb, zb + 0.14), (cx, yb, DECK - 0.02)], 0.022, "Steel_Grey", bend=0.06)
    boot(m, cx, yb, 0.022)


# ---- Cluster D: reel, control cabinet, mast, terminal box ----------------------------------------

def control_cabinet(m):
    """Control cabinet on a stand (dull galvanised) under a sloped rain hood: a door with a handle and
    hinges, a label, a hazard sticker, two indicator lamps, louvres, and conduits down into the platform."""
    _, cx, cy, w, d, h = boxes()["ControlCabinet"]
    x0, x1, y0, y1, zb, zt = cabinet(m, cx, cy, w, d, h, "Steel_Galv_Dull", z0=item_z("ControlCabinet"))
    hood(m, x0, x1, y0, y1, zt, 0.05, 0.13, 0.05, "Steel_Dark")
    geo.box(m, x0 + 0.03, x1 - 0.03, y0 - 0.006, y0, zb + 0.03, zt - 0.03, "Steel_Galv_Dull", 0.004)  # door
    for hz in (zb + 0.12, zt - 0.12):
        geo.cylinder(m, (x0 + 0.026, y0 - 0.01, hz), 0.011, 0.06, "Steel_Dark", segments=10)
    geo.box(m, x1 - 0.08, x1 - 0.06, y0 - 0.04, y0 - 0.006, zb + 0.32, zb + 0.46, "Steel_Dark", 0.005)
    geo.box(m, x0 + 0.07, x0 + 0.25, y0 - 0.009, y0 - 0.006, zt - 0.14, zt - 0.07, "Stock_White")  # label
    hx0, hz0 = cx - 0.05, zb + 0.30
    geo.box(m, hx0, hx0 + 0.16, y0 - 0.009, y0 - 0.006, hz0, hz0 + 0.14, "Stock_Yellow")  # hazard sticker
    for k in range(3):
        sx = hx0 + 0.02 + k * 0.05
        geo.box(m, sx, sx + 0.02, y0 - 0.01, y0 - 0.009, hz0 + 0.01, hz0 + 0.045, "Rubber_Black")
    for k, mat in enumerate(("Stock_Red", "Stock_Green")):
        geo.cylinder(m, (x0 + 0.10 + k * 0.07, y0 - 0.02, zt - 0.22), 0.018, 0.03, mat, axis="Y", segments=12)
    louvers(m, "-Y", y0 - 0.006, x0 + 0.08, x1 - 0.08, zb + 0.05, zb + 0.18, 3)
    zs = base_z(cx, cy)
    for k, ox in enumerate((0.12, 0.22)):  # conduits out of the bottom into the platform
        geo.pipe(m, (x0 + ox, y1 - 0.1, zb + 0.01), (x0 + ox, y1 - 0.1, zs - 0.01), 0.016, "Conduit_Painted", 10)
        boot(m, x0 + ox, y1 - 0.1, 0.016, zs)


def hose_reel(m):
    """Hose reel on a swivel base, its axis turned toward the street so the coil faces the camera across
    the sweep. A-frame sides on base rails, an axle in bosses, a solid rear flange with ribs, an open
    front flange (ring, spokes, hub, crank) through which the coiled black hose shows; the hose runs
    out through a roller fairlead and over the front edge, ending in a nozzle."""
    rl = C.CABLE_REEL
    R, W = rl["radius"], rl["width"]
    yaw = math.radians(rl["yaw"])
    ax = Vector((-math.cos(yaw), -math.sin(yaw), 0.0))  # out of the open front flange, toward the street
    t = UP.cross(ax)
    zb = base_z(rl["cx"], rl["cy"])
    c0 = Vector((rl["cx"], rl["cy"], zb))
    disc(m, c0 + UP * 0.015, UP, 0.40, 0.03, "Steel_Dark", 40)  # swivel turntable on its bearing ring
    disc(m, c0 + UP * 0.04, UP, 0.36, 0.02, "Steel_Charcoal", 40)
    geo.bolts(m, [(c0.x + 0.38 * math.cos(2 * math.pi * k / 10), c0.y + 0.38 * math.sin(2 * math.pi * k / 10), zb + 0.03) for k in range(10)],
              "+Z", "Steel_Dark", 0.011)
    zt = zb + 0.05
    hc = Vector((c0.x, c0.y, zt + 0.06 + R))
    for s in (-1, 1):  # A-frame sides
        side = hc + ax * s * (W / 2 + 0.05)
        foot = Vector((side.x, side.y, zt))
        obox(m, foot + UP * 0.02, t, ax, 0.66, 0.05, 0.04, "Steel_Charcoal")
        for e in (-1, 1):
            geo.pipe(m, foot + t * e * 0.32 + UP * 0.04, side - UP * 0.03, 0.02, "Steel_Charcoal", 8)
        disc(m, side, ax, 0.055, 0.05, "Steel_Dark", 18)
    geo.pipe(m, hc - ax * (W / 2 + 0.1), hc + ax * (W / 2 + 0.1), 0.024, "Steel_Grey", 12)  # axle
    revolve(m, hc, ax, [(0.13, -W / 2), (0.13, W / 2)], "Steel_Dark", 32)  # drum core
    # rear flange: solid, with ribs on its back
    disc(m, hc - ax * (W / 2 + 0.01), ax, R, 0.02, "Rust_Red", 48)
    a_, u_, v_ = frame(ax)
    for k in range(6):
        dr = u_ * math.cos(2 * math.pi * k / 6) + v_ * math.sin(2 * math.pi * k / 6)
        obox(m, hc - ax * (W / 2 + 0.03) + dr * (R * 0.55), dr, ax, R * 0.8, 0.02, 0.012, "Rust_Red")
    # front flange: a ring on six spokes from the hub, a crank on the hub
    f = hc + ax * (W / 2 + 0.01)
    revolve(m, f, ax, [(R - 0.045, -0.01), (R, -0.01), (R, 0.01), (R - 0.045, 0.01)], "Rust_Red", 48, closed=True)
    for k in range(3):
        dr = u_ * math.cos(2 * math.pi * k / 3 + 0.5) + v_ * math.sin(2 * math.pi * k / 3 + 0.5)
        obox(m, f + dr * ((R - 0.045 + 0.08) / 2), dr, ax, R - 0.045 - 0.08 + 0.01, 0.025, 0.014, "Rust_Red")
    disc(m, f, ax, 0.09, 0.03, "Rust_Red", 24)
    arm = (u_ * 0.6 + v_ * 0.8).normalized()  # crank on the axle end, outboard of the frame
    ce = hc + ax * (W / 2 + 0.11)
    obox(m, ce + arm * 0.08, arm, ax, 0.19, 0.03, 0.02, "Steel_Dark")
    geo.pipe(m, ce + arm * 0.16, ce + ax * 0.10 + arm * 0.16, 0.017, "Rubber_Black", 10)
    # the coil: the outer layer turn by turn across the width, and each layer's front turn under the
    # open flange, each turn a little off true (hand-wound)
    hr = 0.019
    r_in, r_out = 0.13 + hr, R - 0.055
    layers = max(2, int((r_out - r_in) / (hr * 1.8)) + 1)
    turns = max(2, int((W - 0.01) / (hr * 2)))
    t_front = W / 2 - hr - 0.004
    rings = [(r_in + (r_out - r_in) * i / (layers - 1), t_front) for i in range(layers - 1)]
    rings += [(r_out, -W / 2 + hr + 0.004 + (W - 2 * hr - 0.008) * j / (turns - 1)) for j in range(turns)]
    for rr, tt in rings:
        tilt = (ax + u_ * geo.jitter(0.025) + v_ * geo.jitter(0.025)).normalized()
        torus(m, hc + ax * tt, tilt, rr + geo.jitter(0.004), hr, "Rubber_Black", 44, 8)
    # hose out from under the coil through a roller fairlead, across the deck and over the front edge
    from .utilities import spline, tube
    fl = hc + ax * (W / 2 + 0.16)
    fl.z = zt + 0.056
    for e in (-1, 1):  # vertical rollers either side of the hose, on a plate bolted to the turntable
        geo.cylinder(m, (fl + t * e * 0.035).to_tuple(), 0.022, 0.088, "Steel_Grey", segments=12)
    obox(m, fl - ax * 0.06 - UP * 0.05, ax, t, 0.16, 0.12, 0.012, "Steel_Dark")
    edge_y = C.CANOPY_Y0 - EDGE_OUT
    start = hc - UP * r_out + ax * (W / 2 - 0.04) + t * 0.02
    ex = fl.x - 0.12
    path = spline([start, fl, Vector((ex + 0.05, C.ROOF_SKIDS[1][3] + 0.02, base_z(ex, -2.0) + 0.025)), Vector((ex, -2.3, DECK + 0.03)), Vector((ex - 0.02, edge_y + 0.03, DECK + 0.035)),
                   Vector((ex - 0.03, edge_y - 0.005, DECK - 0.05)), Vector((ex - 0.05, edge_y + 0.0, DECK - 0.30))])
    tube(m, path, hr, "Rubber_Black", 10)
    geo.pipe(m, path[-1], path[-1] - Vector((0.0, 0.0, 0.08)), hr + 0.005, "Copper_Aged", 10)  # nozzle
    geo.pipe(m, path[-1] - Vector((0.0, 0.0, 0.08)), path[-1] - Vector((0.0, 0.0, 0.12)), hr - 0.004, "Copper_Aged", 10)


def mast_gland():
    """Where the mast's instrument box lets its coax out (utilities.roof_lines runs it to the white box)."""
    mt = C.MAST
    return Vector((mt["cx"], mt["cy"] - mt["w"] / 2 - 0.05, base_z(mt["cx"], mt["cy"]) + 0.36))


def mast(m):
    """A slim sensor mast, kept restrained: a pipe on a gusseted base plate, an instrument box, a short
    crossarm with an anemometer and a louvred sensor shield, a whip antenna, the red beacon on top."""
    mt = C.MAST
    cx, cy, h = mt["cx"], mt["cy"], mt["h"]
    zb = base_z(cx, cy)
    pr = mt["w"] / 2
    geo.box(m, cx - 0.12, cx + 0.12, cy - 0.12, cy + 0.12, zb, zb + 0.02, "Steel_Dark", 0.004)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        p0 = (cx + dx * pr, cy + dy * pr)
        p1 = (cx + dx * 0.11, cy + dy * 0.11)
        q = (dy * 0.006, dx * 0.006)
        tri = [(p0[0], p0[1], zb + 0.02), (p1[0], p1[1], zb + 0.02), (p0[0], p0[1], zb + 0.17)]
        geo.prism(m, ([(x + q[0], y + q[1], z) for x, y, z in tri], [(x - q[0], y - q[1], z) for x, y, z in tri]), "Steel_Dark")
    geo.bolts(m, [(cx + sx * 0.09, cy + sy * 0.09, zb + 0.02) for sx in (-1, 1) for sy in (-1, 1)], "+Z", "Steel_Dark", 0.013)
    geo.pipe(m, (cx, cy, zb + 0.02), (cx, cy, zb + h), pr, "Steel_Galv_Dull", 14)
    # instrument box on the street side, clamped, with its gland underneath
    g = mast_gland()
    geo.box(m, cx - 0.07, cx + 0.07, g.y - 0.045, g.y + 0.045, g.z + 0.02, g.z + 0.22, "Steel_Grey", 0.008)
    for zz in (g.z + 0.06, g.z + 0.18):
        geo.cylinder(m, (cx, cy, zz), pr + 0.008, 0.02, "Steel_Dark", segments=14, cap=False)
    geo.cylinder(m, (g.x, g.y, g.z + 0.01), 0.014, 0.025, "Steel_Dark", segments=10)
    # crossarm with an anemometer (left end) and a louvred sensor shield (right end)
    za = zb + 0.86
    geo.box(m, cx - 0.22, cx + 0.22, cy - 0.015, cy + 0.015, za - 0.015, za + 0.015, "Steel_Galv_Dull", 0.003)
    geo.cylinder(m, (cx, cy, za), pr + 0.01, 0.06, "Steel_Dark", segments=14, cap=False)
    ax_, ay_ = cx - 0.2, cy
    geo.pipe(m, (ax_, ay_, za + 0.015), (ax_, ay_, za + 0.13), 0.006, "Steel_Grey", 6)
    geo.cylinder(m, (ax_, ay_, za + 0.13), 0.018, 0.025, "Steel_Dark", segments=10)
    for k in range(3):
        a = 2 * math.pi * k / 3 + 0.4
        tip = (ax_ + 0.075 * math.cos(a), ay_ + 0.075 * math.sin(a), za + 0.13)
        geo.pipe(m, (ax_, ay_, za + 0.13), tip, 0.003, "Steel_Grey", 4)
        geo.lathe(m, tip, [(0.0, -0.022), (0.016, -0.018), (0.022, -0.006), (0.024, 0.0)], "Steel_Dark", 10, cap_bottom=False)
    sx_ = cx + 0.2
    geo.pipe(m, (sx_, cy, za - 0.015), (sx_, cy, za - 0.03), 0.008, "Steel_Grey", 6)
    for k in range(5):
        geo.cylinder(m, (sx_, cy, za - 0.04 - k * 0.018), 0.045 - k * 0.002, 0.006, "Stock_White", segments=16)
    # whip antenna on a bracket, below the beacon
    geo.box(m, cx - 0.01, cx + 0.01, cy, cy + 0.08, zb + 0.95, zb + 0.97, "Steel_Dark")
    geo.pipe(m, (cx, cy + 0.075, zb + 0.97), (cx, cy + 0.075, zb + h + 0.04), 0.004, "Steel_Grey", 5)
    # beacon
    geo.cylinder(m, (cx, cy, zb + h + 0.01), 0.04, 0.02, "Steel_Dark", segments=16)
    geo.cylinder(m, (cx, cy, zb + h + 0.05), 0.033, 0.06, "Beacon_Red", segments=16)
    geo.cylinder(m, (cx, cy, zb + h + 0.085), 0.038, 0.012, "Steel_Dark", segments=16)


def white_box(m):
    """Low white terminal box on the front-right corner, red label, a gland at the back for the coax."""
    _, cx, cy, w, d, h = boxes()["WhiteBox"]
    x0, x1, y0, y1, zb, zt = cabinet(m, cx, cy, w, d, h, "Stock_White", z0=item_z("WhiteBox"))
    geo.box(m, x0 + 0.04, x1 - 0.04, y0 - 0.003, y0, zt - 0.14, zt - 0.08, "Stock_Red")
    geo.box(m, x0 + 0.04, x0 + 0.2, y0 - 0.003, y0, zb + 0.05, zb + 0.12, "Paper_White")
    geo.cylinder(m, (cx, y1 + 0.01, zb + 0.08), 0.02, 0.025, "Steel_Dark", axis="Y", segments=10)


# ---- Back of the roof ----------------------------------------------------------------------------

def fan_box(m):
    """Refrigeration condensing unit at the back: a low box with a round fan shroud on top."""
    _, cx, cy, w, d, h = boxes()["FanBox"]
    x0, x1, y0, y1, zb, zt = cabinet(m, cx, cy, w, d, h, "Steel_Galvanised", z0=item_z("FanBox"))
    louvers(m, "-Y", y0, x0 + 0.06, x1 - 0.06, zb + 0.06, zt - 0.06, 5)
    r = min(w, d) * 0.4
    geo.lathe(m, (cx, cy, zt), [(r + 0.03, 0.0), (r + 0.03, 0.12), (r, 0.12), (r, 0.02)], "Steel_Dark", 28,
              cap_bottom=False, cap_top=False)
    geo.cylinder(m, (cx, cy, zt + 0.03), r, 0.01, "Rubber_Black", segments=28)
    for a in (0, 90):
        ar = math.radians(a)
        geo.pipe(m, (cx - r * math.cos(ar), cy - r * math.sin(ar), zt + 0.11), (cx + r * math.cos(ar), cy + r * math.sin(ar), zt + 0.11),
                 0.006, "Steel_Grey", 5)
    geo.cylinder(m, (cx, cy, zt + 0.06), 0.05, 0.06, "Steel_Dark", segments=12)


def vent_housing(m):
    """Louvred ventilation housing with a sloped rain hood (higher at the back)."""
    _, cx, cy, w, d, h = boxes()["VentHousing"]
    x0, x1, y0, y1, zb, zt = cabinet(m, cx, cy, w, d, h, "Steel_Galvanised", z0=item_z("VentHousing"))
    louvers(m, "-Y", y0, x0 + 0.06, x1 - 0.06, zb + 0.08, zt - 0.06, 8)
    louvers(m, "-X", x0, y0 + 0.06, y1 - 0.06, zb + 0.08, zt - 0.06, 8)
    hood(m, x0, x1, y0, y1, zt, 0.06, 0.30, 0.06)


def back_boxes(m):
    for name, cx, cy, w, d, h in C.ROOF_BOXES:
        if name.startswith("BackBox"):
            x0, x1, y0, y1, zb, zt = cabinet(m, cx, cy, w, d, h, "Steel_Grey" if name != "BackBox_B" else "Machine_Body",
                                             "Rust_Red" if name == "BackBox_A" else None, z0=item_z(name))
            louvers(m, "-X", x0, y0 + 0.08, y1 - 0.08, zb + 0.08, zb + 0.3, 5)


def duct(m):
    """Rectangular supply duct out of the HVAC's back on stands, turning along the roof and down into
    the deck through a collar."""
    dc = C.ROOF_DUCT
    hw, hh = dc["w"] / 2, dc["h"] / 2
    zc = DECK + dc["z"]
    pts = dc["path"]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        geo.box(m, min(ax, bx) - hw, max(ax, bx) + hw, min(ay, by) - hw, max(ay, by) + hw, zc - hh, zc + hh, "Steel_Galvanised", 0.01, 2)
        for t in (0.3, 0.7):  # flanged joints
            jx, jy = ax + (bx - ax) * t, ay + (by - ay) * t
            if ax == bx:
                geo.box(m, jx - hw - 0.02, jx + hw + 0.02, jy - 0.025, jy + 0.025, zc - hh - 0.02, zc + hh + 0.02, "Steel_Dark", 0.004)
            else:
                geo.box(m, jx - 0.025, jx + 0.025, jy - hw - 0.02, jy + hw + 0.02, zc - hh - 0.02, zc + hh + 0.02, "Steel_Dark", 0.004)
    sx, sy = pts[0]  # collar on the HVAC's back
    geo.box(m, sx - hw - 0.04, sx + hw + 0.04, sy - 0.01, sy + 0.04, zc - hh - 0.04, zc + hh + 0.04, "Steel_Dark", 0.006)
    ex, ey = pts[-1]  # drop into the deck, with a collar
    geo.box(m, ex - hw, ex + hw, ey - hw, ey + hw, DECK, zc + hh, "Steel_Galvanised", 0.01, 2)
    geo.box(m, ex - hw - 0.05, ex + hw + 0.05, ey - hw - 0.05, ey + hw + 0.05, DECK, DECK + 0.08, "Steel_Dark", 0.006)
    for sx, sy in ((pts[1][0] + 0.35, pts[1][1]), ((pts[1][0] + ex) / 2 + 0.3, ey), (pts[0][0], (pts[0][1] + pts[1][1]) / 2)):  # stands
        if abs(sx - pts[0][0]) < 1e-6:
            geo.box(m, sx - hw - 0.02, sx + hw + 0.02, sy - 0.03, sy + 0.03, DECK, zc - hh, "Steel_Dark", 0.004)
        else:
            geo.box(m, sx - 0.03, sx + 0.03, sy - hw - 0.02, sy + hw + 0.02, DECK, zc - hh, "Steel_Dark", 0.004)


def exhaust_fan(m):
    """Kitchen exhaust at the back: a mushroom (downblast) fan on its own flashed curb, a bird screen
    under the dome."""
    ef = C.EXHAUST_FAN
    cx, cy, s, r = ef["cx"], ef["cy"], ef["curb"] / 2, ef["r"]
    geo.box(m, cx - s - 0.05, cx + s + 0.05, cy - s - 0.05, cy + s + 0.05, DECK, DECK + 0.03, "Steel_Dark", 0.006, 2)
    geo.box(m, cx - s, cx + s, cy - s, cy + s, DECK + 0.02, DECK + 0.16, "Steel_Galv_Dull", 0.006, 2)
    geo.box(m, cx - s - 0.02, cx + s + 0.02, cy - s - 0.02, cy + s + 0.02, DECK + 0.16, DECK + 0.19, "Steel_Dark", 0.004)
    z = DECK + 0.19
    revolve(m, (cx, cy, z), UP, [(0.19, 0.0), (0.19, 0.08)], "Steel_Galvanised", 28)  # neck
    geo.cylinder(m, (cx, cy, z + 0.10), r - 0.03, 0.05, "Rubber_Black", segments=32, cap=False)  # bird screen
    revolve(m, (cx, cy, z), UP, [(r - 0.02, 0.07), (r, 0.08), (r + 0.01, 0.11), (r * 0.92, 0.17), (r * 0.66, 0.23), (r * 0.3, 0.26), (0.0, 0.27)],
            "Steel_Galvanised", 36, caps=(False, False))
    geo.cylinder(m, (cx, cy, z + 0.10), r + 0.012, 0.012, "Steel_Dark", segments=36, cap=False)  # rim band


def exhaust_stack(m):
    st = C.EXHAUST_STACK
    cx, cy, r, h = st["cx"], st["cy"], st["r"], st["h"]
    geo.box(m, cx - r - 0.08, cx + r + 0.08, cy - r - 0.08, cy + r + 0.08, DECK, DECK + 0.05, "Steel_Dark", 0.006)
    geo.cylinder(m, (cx, cy, DECK + h / 2), r, h, "Steel_Galvanised", segments=20)
    for f in (0.3, 0.62):  # bands
        geo.cylinder(m, (cx, cy, DECK + h * f), r + 0.012, 0.04, "Steel_Dark", segments=20, cap=False)
    # rain cap on three legs
    geo.lathe(m, (cx, cy, DECK + h + 0.10), [(r * 2.0, 0.0), (r * 1.6, 0.05), (r * 0.5, 0.12), (0.0, 0.13)], "Steel_Dark", 20,
              cap_bottom=True, cap_top=False)
    for k in range(3):
        a = 2 * math.pi * k / 3
        geo.pipe(m, (cx + r * 0.9 * math.cos(a), cy + r * 0.9 * math.sin(a), DECK + h - 0.02),
                 (cx + r * 1.3 * math.cos(a), cy + r * 1.3 * math.sin(a), DECK + h + 0.11), 0.008, "Steel_Dark", 5)


def links(m):
    """Short tie-ins between the clusters: the tank's pressure switch to the control cabinet (flex)."""
    tx, ty, tr, th = tanks()["Tank"]
    zb = base_z(tx, ty)
    _, cx, cy, w, d, h = boxes()["ControlCabinet"]
    cz = item_z("ControlCabinet") + 0.04
    zs = zb + th * 0.62 + 0.05
    zd = base_z(cx, cy) + 0.012
    rl = C.CABLE_REEL
    yb = rl["cy"] + 0.47  # behind the turntable
    line(m, [(tx + tr + 0.06, ty + 0.07, zs), (tx + tr + 0.10, ty + 0.10, zs - 0.10), (tx + tr + 0.12, ty + 0.16, zb + 0.012),
             (rl["cx"] - 0.30, yb, zd), (cx - w / 2 - 0.12, yb + 0.02, zd), (cx - w / 2 - 0.04, cy - 0.10, cz + 0.12),
             (cx - w / 2 + 0.005, cy - 0.10, cz + 0.12)], 0.011, "Cable_Black", flex=True)


def build(coll, materials):
    geo.reseed(8080)
    m = geo.Mesh("Roof_Detail")
    skids(m)
    curbs(m)
    rails(m)
    stands(m)
    # A
    hvac(m)
    ac_condenser(m)
    small_unit(m)
    # B
    vessel(m)
    # C
    tank(m)
    receiver(m)
    separator(m)
    # D
    control_cabinet(m)
    hose_reel(m)
    mast(m)
    white_box(m)
    # back
    fan_box(m)
    vent_housing(m)
    back_boxes(m)
    duct(m)
    exhaust_fan(m)
    exhaust_stack(m)
    links(m)
    return m.build(coll, materials)
