"""Step 4: roof machinery on the canopy deck (layout fitted to the reference in kiosk_config).

AC condenser with fan grille, small utility unit, tall cabinet with porthole, hazard-sticker
cabinet, white box with red label, back boxes, banded tanks with domes, valves and gauges,
connecting pipes, the cable reel on its stand, the lattice antenna mast with a red beacon,
and loose cables draped over the canopy edge.
"""
import math

import kiosk_config as C
from . import geo

DECK = C.CANOPY_TOP

MATERIALS = {
    "Beacon_Red": ((1.0, 0.06, 0.04), 0.4, 0.0, 8.0),
}


def ensure_materials(B):
    import bpy
    for name, (rgb, rough, metal, emit) in MATERIALS.items():
        m = B.mat(name, rgb, emit)
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return bpy.data.materials


def boxes():
    return {b[0]: b for b in C.ROOF_BOXES}


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


def ac_condenser(m):
    _, cx, cy, w, d, h = boxes()["ACCondenser"]
    x0, x1, y0, y1, zb, zt = cabinet(m, cx, cy, w, d, h, "Steel_Grey")
    # feet rails
    for yy in (y0 + 0.08, y1 - 0.08):
        geo.box(m, x0 - 0.02, x1 + 0.02, yy - 0.03, yy + 0.03, DECK, DECK + 0.045, "Steel_Dark", 0.004)
    # fan grille on the -X face: ring, concentric rings, cross bars, hub
    fz, fy, r = (zb + zt) / 2, cy, min(d, h) * 0.38
    geo.cylinder(m, (x0 - 0.008, fy, fz), r + 0.03, 0.016, "Steel_Dark", axis="X", segments=32)
    geo.cylinder(m, (x0 - 0.004, fy, fz), r, 0.012, "Rubber_Black", axis="X", segments=32)
    for k in range(1, 5):
        rr = r * k / 5
        pts = [(x0 - 0.018, fy + rr * math.cos(2 * math.pi * j / 24), fz + rr * math.sin(2 * math.pi * j / 24)) for j in range(25)]
        for p, q in zip(pts, pts[1:]):
            geo.pipe(m, p, q, 0.003, "Steel_Grey", 4)
    for a in (0, 90):
        ar = math.radians(a)
        geo.pipe(m, (x0 - 0.018, fy - r * math.cos(ar), fz - r * math.sin(ar)), (x0 - 0.018, fy + r * math.cos(ar), fz + r * math.sin(ar)),
                 0.005, "Steel_Grey", 5)
    geo.cylinder(m, (x0 - 0.02, fy, fz), 0.05, 0.02, "Steel_Dark", axis="X", segments=16)
    # side louvers on the -Y face, pipe stubs at the back
    louvers(m, "-Y", y0, x0 + 0.06, x1 - 0.06, zb + 0.08, zt - 0.1, 9)
    for k, zz in enumerate((zb + 0.12, zb + 0.22)):
        geo.pipe(m, (x1, cy + 0.25, zz), (x1 + 0.25, cy + 0.25, zz), 0.02 - k * 0.006, "Interior_Steel", 10)


def small_unit(m):
    _, cx, cy, w, d, h = boxes()["SmallUnit"]
    x0, x1, y0, y1, zb, zt = cabinet(m, cx, cy, w, d, h, "Machine_Body", "Rust_Red")
    louvers(m, "-X", x0, y0 + 0.06, y1 - 0.06, zb + 0.06, zt - 0.08, 6)
    geo.pipe(m, (cx, y0, zb + 0.15), (cx, y0 - 0.2, zb + 0.15), 0.025, "Steel_Galvanised", 10)


def tall_cabinet(m):
    _, cx, cy, w, d, h = boxes()["TallCabinet"]
    x0, x1, y0, y1, zb, zt = cabinet(m, cx, cy, w, d, h, "Steel_Grey", "Rust_Red")
    # porthole on the -Y face with bolted rim
    px, pz, r = cx - 0.1, zb + (zt - zb) * 0.68, 0.13
    geo.cylinder(m, (px, y0 - 0.012, pz), r + 0.035, 0.024, "Steel_Dark", axis="Y", segments=28)
    geo.cylinder(m, (px, y0 - 0.026, pz), r, 0.006, "Glass_Wired", axis="Y", segments=28)
    geo.rivets(m, [(px + (r + 0.02) * math.cos(2 * math.pi * k / 10), y0 - 0.024, pz + (r + 0.02) * math.sin(2 * math.pi * k / 10))
                   for k in range(10)], "-Y", "Steel_Grey", 0.008)
    # door seam + handle on the -Y face, vent grille on the -X face
    geo.box(m, x0 + 0.05, x1 - 0.05, y0 - 0.004, y0, zb + 0.06, zb + 0.065, "Steel_Dark")
    geo.box(m, x1 - 0.1, x1 - 0.08, y0 - 0.035, y0, zb + 0.25, zb + 0.4, "Steel_Dark", 0.005)
    louvers(m, "-X", x0, y0 + 0.1, y1 - 0.1, zb + 0.15, zb + 0.5, 7)


def sticker_cabinet(m):
    _, cx, cy, w, d, h = boxes()["StickerCabinet"]
    x0, x1, y0, y1, zb, zt = cabinet(m, cx, cy, w, d, h, "Steel_Galvanised")
    # yellow hazard sticker with black stripes, vent slots, handle
    hx0, hx1, hz0, hz1 = cx - 0.12, cx + 0.12, zb + (zt - zb) * 0.55, zb + (zt - zb) * 0.55 + 0.2
    geo.box(m, hx0, hx1, y0 - 0.003, y0, hz0, hz1, "Stock_Yellow")
    for k in range(4):
        sx = hx0 + 0.02 + k * 0.06
        geo.box(m, sx, sx + 0.025, y0 - 0.004, y0 - 0.003, hz0 + 0.01, hz0 + 0.05, "Rubber_Black", 0.0, rot=None)
    louvers(m, "-Y", y0, x0 + 0.08, x1 - 0.08, zb + 0.06, zb + 0.22, 4)
    geo.box(m, x1 - 0.07, x1 - 0.05, y0 - 0.03, y0, zb + 0.3, zb + 0.42, "Steel_Dark", 0.004)


def white_box(m):
    _, cx, cy, w, d, h = boxes()["WhiteBox"]
    x0, x1, y0, y1, zb, zt = cabinet(m, cx, cy, w, d, h, "Stock_White")
    geo.box(m, x0 + 0.04, x1 - 0.04, y0 - 0.003, y0, zt - 0.14, zt - 0.08, "Stock_Red")
    geo.box(m, x0 + 0.04, x0 + 0.2, y0 - 0.003, y0, zb + 0.05, zb + 0.12, "Paper_White")


def back_boxes(m):
    for name, cx, cy, w, d, h in C.ROOF_BOXES:
        if name.startswith("BackBox"):
            x0, x1, y0, y1, zb, zt = cabinet(m, cx, cy, w, d, h, "Steel_Grey" if name != "BackBox_B" else "Machine_Body",
                                             "Rust_Red" if name == "BackBox_A" else None)
            louvers(m, "-X", x0, y0 + 0.08, y1 - 0.08, zb + 0.08, zb + 0.3, 5)


def tanks(m):
    for name, cx, cy, r, h in C.ROOF_TANKS:
        geo.cylinder(m, (cx, cy, DECK + 0.03), r * 1.08, 0.06, "Steel_Dark", segments=24)  # base ring
        geo.cylinder(m, (cx, cy, DECK + 0.06 + h / 2), r, h - 0.06, "Steel_Galvanised", segments=28)
        geo.lathe(m, (cx, cy, DECK + h), [(r, 0.0), (r * 0.92, r * 0.25), (r * 0.7, r * 0.42), (r * 0.35, r * 0.52), (0.0, r * 0.55)],
                  "Steel_Galvanised", 28, cap_bottom=False, cap_top=False)
        for f in (0.25, 0.6, 0.9):  # bands
            geo.cylinder(m, (cx, cy, DECK + 0.06 + (h - 0.06) * f), r + 0.008, 0.03, "Steel_Dark", segments=28, cap=False)
        # valve with handwheel near the top, facing the camera side
        vx, vy, vz = cx - r * 0.72, cy - r * 0.72, DECK + h - 0.12
        geo.pipe(m, (cx - r * 0.6, cy - r * 0.6, vz), (vx - 0.05, vy - 0.05, vz), 0.018, "Steel_Grey", 8)
        ring = [(vx - 0.06, vy - 0.06 + 0.045 * math.cos(2 * math.pi * k / 12), vz + 0.045 * math.sin(2 * math.pi * k / 12)) for k in range(13)]
        for p, q in zip(ring, ring[1:]):
            geo.pipe(m, p, q, 0.006, "Stock_Red", 5)
        # pressure gauge
        geo.cylinder(m, (cx, cy - r - 0.03, DECK + h * 0.55), 0.035, 0.025, "Steel_Dark", axis="Y", segments=16)
        geo.cylinder(m, (cx, cy - r - 0.044, DECK + h * 0.55), 0.028, 0.004, "Paper_White", axis="Y", segments=16)
    # pipes linking the tanks and running to the tall cabinet
    t = {n: (cx, cy, r, h) for n, cx, cy, r, h in C.ROOF_TANKS}
    za = DECK + 0.32
    path = [(t["Tank_A"][0], t["Tank_A"][1], za), (t["Tank_B"][0], t["Tank_A"][1], za), (t["Tank_B"][0], t["Tank_B"][1], za)]
    for p, q in zip(path, path[1:]):
        geo.pipe(m, p, q, 0.03, "Interior_Steel", 12)
    tc = boxes()["TallCabinet"]
    geo.pipe(m, (t["Tank_A"][0], t["Tank_A"][1], DECK + 0.55), (tc[1] + tc[3] / 2, t["Tank_A"][1], DECK + 0.55), 0.028, "Interior_Steel", 12)
    geo.pipe(m, (t["Tank_C"][0], t["Tank_C"][1], DECK + 0.2), (t["Tank_C"][0], t["Tank_C"][1] + 0.6, DECK + 0.2), 0.025, "Steel_Grey", 10)
    for p in path[:-1]:
        geo.box(m, p[0] - 0.04, p[0] + 0.04, p[1] - 0.04, p[1] + 0.04, DECK, za - 0.03, "Steel_Dark", 0.004)


def cable_reel(m):
    rl = C.CABLE_REEL
    cx, cy, r, w = rl["cx"], rl["cy"], rl["radius"], rl["width"]
    cz = DECK + r + 0.06
    for sy in (-1, 1):  # A-frame stand
        yy = cy + sy * (w / 2 + 0.04)
        geo.pipe(m, (cx - r * 0.7, yy, DECK), (cx, yy, cz), 0.022, "Steel_Dark", 8)
        geo.pipe(m, (cx + r * 0.7, yy, DECK), (cx, yy, cz), 0.022, "Steel_Dark", 8)
    geo.pipe(m, (cx, cy - w / 2 - 0.06, cz), (cx, cy + w / 2 + 0.06, cz), 0.025, "Steel_Grey", 10)  # axle
    for sy in (-1, 1):  # flanges with lightening holes (dark discs)
        yy = cy + sy * (w / 2 - 0.015)
        geo.cylinder(m, (cx, yy, cz), r, 0.025, "Steel_Grey", axis="Y", segments=32)
        for k in range(6):
            a = 2 * math.pi * k / 6
            geo.cylinder(m, (cx + r * 0.55 * math.cos(a), yy + sy * 0.014, cz + r * 0.55 * math.sin(a)), r * 0.16, 0.004, "Steel_Dark",
                         axis="Y", segments=16)
    # wound cable: stacked turns with slightly varying radius
    n = int((w - 0.06) / 0.022)
    for k in range(n):
        yy = cy - (w - 0.06) / 2 + (k + 0.5) * (w - 0.06) / n
        geo.cylinder(m, (cx, yy, cz), r * 0.86 + 0.012 * math.sin(k * 1.7), 0.02, "Rubber_Black", axis="Y", segments=28)
    # loose end trailing off the reel and over the canopy front edge
    geo.cable(m, (cx - r * 0.5, cy - w / 2, cz - r * 0.6), (cx - 0.6, C.CANOPY_Y0 - 0.05, DECK + 0.02), 0.05, 0.012, "Rubber_Black", 10)
    geo.cable(m, (cx - 0.6, C.CANOPY_Y0 - 0.05, DECK + 0.02), (cx - 0.75, C.CANOPY_Y0 - 0.08, DECK - 0.35), 0.0, 0.012, "Rubber_Black", 4)


def mast(m):
    mt = C.MAST
    cx, cy, h = mt["cx"], mt["cy"], mt["h"]
    s = 0.13
    legs = [(cx - s / 2, cy - s / 2), (cx + s / 2, cy - s / 2), (cx + s / 2, cy + s / 2), (cx - s / 2, cy + s / 2)]
    geo.box(m, cx - 0.14, cx + 0.14, cy - 0.14, cy + 0.14, DECK, DECK + 0.03, "Steel_Dark", 0.004)
    for lx, ly in legs:
        geo.pipe(m, (lx, ly, DECK), (lx, ly, DECK + h), 0.008, "Steel_Dark", 6)
    seg = 0.22
    z = DECK
    k = 0
    while z + seg <= DECK + h + 1e-6:  # zig-zag bracing on each face
        for i in range(4):
            a, b = legs[i], legs[(i + 1) % 4]
            p, q = (a, b) if k % 2 == 0 else (b, a)
            geo.pipe(m, (p[0], p[1], z), (q[0], q[1], z + seg), 0.004, "Steel_Dark", 4)
        z += seg
        k += 1
    for i, (zz, span) in enumerate(((0.95, 0.55), (1.25, 0.42), (1.5, 0.3))):  # crossbars with small antennas
        geo.box(m, cx - span / 2, cx + span / 2, cy - 0.012, cy + 0.012, DECK + zz, DECK + zz + 0.025, "Steel_Dark", 0.003)
        for sx in (-1, 1):
            ex = cx + sx * span / 2
            geo.pipe(m, (ex, cy, DECK + zz), (ex, cy, DECK + zz + 0.18 - i * 0.03), 0.005, "Steel_Grey", 5)
    # dish, top whip and the red beacon
    geo.lathe(m, (cx + 0.12, cy - 0.1, DECK + 1.05), [(0.0, 0.0), (0.06, 0.01), (0.11, 0.035), (0.13, 0.05)], "Stock_White", 20,
              cap_bottom=False, cap_top=False)
    geo.pipe(m, (cx, cy, DECK + h), (cx, cy, DECK + h + 0.35), 0.006, "Steel_Grey", 5)
    geo.cylinder(m, (cx, cy, DECK + h + 0.03), 0.035, 0.06, "Beacon_Red", segments=16)


def drapes(m):
    """Loose cables from the machinery over the canopy edge (silhouette detail)."""
    b = boxes()
    sm = b["SmallUnit"]
    geo.cable(m, (sm[1] - sm[3] / 2, sm[2], DECK + 0.2), (C.CANOPY_X0 - 0.03, sm[2] - 0.3, DECK + 0.01), 0.04, 0.01, "Rubber_Black", 8)
    geo.cable(m, (C.CANOPY_X0 - 0.03, sm[2] - 0.3, DECK + 0.01), (C.CANOPY_X0 - 0.08, sm[2] - 0.45, DECK - 0.55), 0.0, 0.01, "Rubber_Black", 4)
    ac = b["ACCondenser"]
    geo.cable(m, (ac[1], ac[2] - ac[4] / 2, DECK + 0.1), (ac[1] + 0.5, C.CANOPY_Y0 - 0.03, DECK + 0.01), 0.03, 0.009, "Rubber_Black", 8)
    geo.cable(m, (ac[1] + 0.5, C.CANOPY_Y0 - 0.03, DECK + 0.01), (ac[1] + 0.55, C.CANOPY_Y0 - 0.06, DECK - 0.4), 0.0, 0.009, "Rubber_Black", 4)


def build(coll, materials):
    geo.reseed(8080)
    m = geo.Mesh("Roof_Detail")
    ac_condenser(m)
    small_unit(m)
    tall_cabinet(m)
    sticker_cabinet(m)
    white_box(m)
    back_boxes(m)
    tanks(m)
    cable_reel(m)
    mast(m)
    drapes(m)
    return m.build(coll, materials)
