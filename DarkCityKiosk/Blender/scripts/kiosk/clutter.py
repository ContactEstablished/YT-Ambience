"""Step 3: wall clutter, lanterns, posters/stickers and ground props.

Electrical cluster (meter box with dial, breaker box with lamps, junction box, conduit with
clamps, sagging cables), ribbed paper lanterns (chochin) with lettering, poster boards and
scattered stickers, a downpipe, and the ground props: slatted crates, an equipment cabinet,
the red bottle crate, bins with lids, the utility cabinet, cushioned stools and the railing.
"""
import math

import kiosk_config as C
from . import geo, shell

X0, Y0, Y1, PH = C.X0, C.Y0, C.Y1, C.PLATFORM_H
BEAM_Z = C.BODY_TOP - C.SHELL["topbeam_h"]  # underside of the top beam

MATERIALS = {
    "Lantern_Rib": ((0.25, 0.14, 0.06), 0.6, 0.0, 0.0),
    "Cardboard": ((0.42, 0.30, 0.18), 0.8, 0.0, 0.0),
    "Cabinet_Green": ((0.10, 0.20, 0.16), 0.45, 0.2, 0.0),
    "Cushion_Red": ((0.50, 0.05, 0.04), 0.35, 0.0, 0.0),
}


def ensure_materials(B):
    import bpy
    for name, (rgb, rough, metal, emit) in MATERIALS.items():
        m = B.mat(name, rgb, emit)
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return bpy.data.materials


# ---- Electrical cluster -----------------------------------------------------------------

def conduit_up(m, x, y, z_from, clamp_every=0.3):
    geo.pipe(m, (x, y, z_from), (x, y, BEAM_Z), 0.012, "Steel_Dark")
    z = z_from + 0.12
    while z < BEAM_Z - 0.05:
        geo.box(m, x - 0.018, X0, y - 0.022, y + 0.022, z - 0.012, z + 0.012, "Steel_Grey", 0.002)
        z += clamp_every


def electrical(m):
    boxes = {b[0]: b for b in C.LEFT_WALL_BOXES}
    # meter box: rounded box, door seam, round dial window with rim, hasp, label plate
    _, a0, a1, z0, z1, d = boxes["MeterBox"]
    geo.box(m, X0 - d, X0, a0, a1, z0, z1, "Steel_Grey", 0.012, 2)
    geo.box(m, X0 - d - 0.002, X0 - d + 0.002, a0 + 0.02, a1 - 0.02, z0 + 0.02, z0 + 0.024, "Steel_Dark")
    yc = (a0 + a1) / 2
    geo.cylinder(m, (X0 - d - 0.004, yc, z1 - 0.13), 0.068, 0.008, "Steel_Dark", axis="X", segments=24)
    geo.cylinder(m, (X0 - d - 0.007, yc, z1 - 0.13), 0.058, 0.004, "Glass_Wired", axis="X", segments=24)
    geo.box(m, X0 - d - 0.004, X0 - d, yc - 0.06, yc + 0.06, z0 + 0.12, z0 + 0.16, "Paper_White")
    geo.box(m, X0 - d - 0.03, X0 - d, a0 + 0.02, a0 + 0.045, (z0 + z1) / 2 - 0.03, (z0 + z1) / 2 + 0.03, "Steel_Dark", 0.003)
    conduit_up(m, X0 - 0.04, yc, z1)
    # breaker box: lamps + vent slots
    _, a0, a1, z0, z1, d = boxes["FuseBox"]
    geo.box(m, X0 - d, X0, a0, a1, z0, z1, "Machine_Body", 0.01, 2)
    for k, mat in enumerate(("Button_Lit_Red", "Button_Lit_Green")):
        yl = a0 + 0.06 + k * 0.05
        geo.cylinder(m, (X0 - d - 0.006, yl, z1 - 0.06), 0.012, 0.012, mat, axis="X", segments=12)
    for k in range(3):
        zv = z0 + 0.06 + k * 0.03
        geo.box(m, X0 - d - 0.003, X0 - d, a0 + 0.05, a1 - 0.05, zv - 0.005, zv + 0.005, "Rubber_Black")
    conduit_up(m, X0 - 0.04, (a0 + a1) / 2, z1)
    # junction box with glands and a cable dropping to the platform
    _, a0, a1, z0, z1, d = boxes["JunctionBox"]
    geo.box(m, X0 - d, X0, a0, a1, z0, z1, "Steel_Grey", 0.008, 2)
    for yg in (a0 + 0.05, a1 - 0.05):
        geo.cylinder(m, (X0 - d / 2, yg, z0 - 0.015), 0.014, 0.03, "Rubber_Black", segments=10)
    geo.cable(m, (X0 - d / 2, a1 - 0.05, z0 - 0.03), (X0 - 0.35, a1 + 0.25, PH + 0.01), 0.05, 0.007, "Rubber_Black")
    conduit_up(m, X0 - 0.04, (a0 + a1) / 2, z1)
    # small box on the front wall by the corner, wired across the corner post
    geo.box(m, -2.05, -1.88, Y0 - 0.08, Y0, 1.75, 1.95, "Steel_Grey", 0.008, 2)
    geo.cable(m, (-1.96, Y0 - 0.05, 1.95), (X0 - 0.06, -1.24, 1.75), 0.10, 0.006, "Rubber_Black")
    # loose cables sagging from the breaker box and the front wall up to the soffit
    geo.cable(m, (X0 - 0.07, -0.86, 2.20), (C.CANOPY_X0 + 0.35, C.CANOPY_Y0 + 0.35, C.CANOPY_BOTTOM - 0.02), 0.16, 0.008, "Rubber_Black")
    geo.cable(m, (-1.2, Y0 - 0.04, BEAM_Z - 0.02), (0.2, Y0 - 0.04, BEAM_Z - 0.02), 0.22, 0.006, "Rubber_Black", 14)
    geo.cable(m, (0.9, Y0 - 0.05, BEAM_Z - 0.02), (2.05, Y0 - 0.05, BEAM_Z - 0.05), 0.15, 0.006, "Rubber_Black", 12)


# ---- Lanterns -----------------------------------------------------------------------------

def chochin(m, x, y, zc, radius, height):
    """Ribbed paper lantern centred at zc, with lacquered caps."""
    body = height - 0.08
    z0 = zc - body / 2
    prof = [(radius * (0.78 + 0.22 * math.sin(math.pi * t / 12)), z0 + body * t / 12) for t in range(13)]
    geo.lathe(m, (x, y, 0), prof, "Lantern_Paper", 24, cap_bottom=False, cap_top=False)
    n_ribs = int(body / 0.035)
    for k in range(1, n_ribs):
        t = k / n_ribs
        r = radius * (0.78 + 0.22 * math.sin(math.pi * t)) + 0.0015
        geo.cylinder(m, (x, y, z0 + body * t), r, 0.003, "Lantern_Rib", segments=24, cap=False)
    for zz in (z0 - 0.02, z0 + body + 0.02):
        geo.cylinder(m, (x, y, zz), radius * 0.74, 0.04, "Rubber_Black", segments=24)


def lantern_text(m, B, coll, body, x, y, zc, radius, height, size):
    """Vertical lettering wrapped onto the lantern's bulging paper, centred on the side that
    faces the camera's average direction. The text is laid out flat, converted to a mesh, and
    every vertex is bent around the lantern axis at the paper's radius for its height."""
    import bpy
    from mathutils import Vector
    ob = B.text("_tmp_lantern_text", body, size, (0, 0, 0), (0, 0, 0), B.M["sign_text"], coll, font=B.JP_FONT)
    deps = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(deps))
    h = math.radians(C.HERO_CAM["heading_deg"])
    n = Vector((-math.cos(h), -math.sin(h), 0.0))  # facing the camera
    t = Vector((-n.y, n.x, 0.0))  # the viewer's right
    body_h = height - 0.08
    verts = []
    for v in me.vertices:
        z = zc + v.co.y
        tt = min(max((z - (zc - body_h / 2)) / body_h, 0.0), 1.0)
        r = radius * (0.78 + 0.22 * math.sin(math.pi * tt)) + 0.003
        a = v.co.x / r
        verts.append(Vector((x, y, z)) + n * (r * math.cos(a)) + t * (r * math.sin(a)))
    m.add_raw(verts, [list(p.vertices) for p in me.polygons], "Sign_Text_Black")
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)


def lanterns(m, B, coll):
    ll = C.LANTERN_L
    z = PH
    for i, (s, h) in enumerate(C.LANTERN_L_PEDESTAL):  # pedestal: crate, rusty box, small box
        mat = ("Wood_Crate", "Rust_Red", "Steel_Dark")[i % 3]
        geo.box(m, ll["x"] - s / 2, ll["x"] + s / 2, ll["y"] - s / 2, ll["y"] + s / 2, z, z + h, mat, 0.01, 2)
        z += h
    bottom = ll["z"] - ll["h"] / 2
    geo.pipe(m, (ll["x"], ll["y"], z), (ll["x"], ll["y"], bottom - 0.04), 0.02, "Steel_Dark", 10)
    geo.box(m, ll["x"] - 0.06, ll["x"] + 0.06, ll["y"] - 0.06, ll["y"] + 0.06, bottom - 0.045, bottom - 0.035, "Steel_Dark")
    chochin(m, ll["x"], ll["y"], ll["z"], ll["radius"], ll["h"])
    geo.cable(m, (ll["x"], ll["y"], ll["z"] + ll["h"] / 2), (C.CANOPY_X0 + 0.2, ll["y"] - 0.2, C.CANOPY_BOTTOM - 0.02), 0.08, 0.006, "Rubber_Black", 8)
    lantern_text(m, B, coll, "ラ\n｜\nメ\nン", ll["x"], ll["y"], ll["z"] + 0.01, ll["radius"], ll["h"], 0.095)

    lr = C.LANTERN_R
    top = lr["z"] + lr["h"] / 2
    px = lr["x"] + 0.12
    geo.pipe(m, (px, lr["y"], PH), (px, lr["y"], top + 0.16), 0.02, "Steel_Dark", 10)
    geo.box(m, px - 0.08, px + 0.08, lr["y"] - 0.08, lr["y"] + 0.08, PH, PH + 0.01, "Steel_Dark", 0.003)
    geo.pipe(m, (px, lr["y"], top + 0.14), (lr["x"], lr["y"], top + 0.14), 0.012, "Steel_Dark", 8)
    geo.pipe(m, (lr["x"], lr["y"], top + 0.14), (lr["x"], lr["y"], top + 0.02), 0.004, "Steel_Dark", 6)
    chochin(m, lr["x"], lr["y"], lr["z"], lr["radius"], lr["h"])
    lantern_text(m, B, coll, "24\n時\n間\n営\n業", lr["x"], lr["y"], lr["z"], lr["radius"], lr["h"], 0.075)


# ---- Posters and stickers -------------------------------------------------------------------

STICKER_MATS = ["Stock_Red", "Stock_White", "Stock_Yellow", "Stock_Blue", "Stock_Green", "Paper_White", "Poster_Colour"]


def posters_and_stickers(m):
    walls = shell.WALLS
    for name, a0, a1, z0, z1 in C.LEFT_WALL_DECALS:
        shell.wall_box(m, walls["left"], a0, a1, z0, z1, 0.004, 0.008, "Logo_Stencil" if "Logo" in name else "Poster_Colour",
                       0.0, 1, geo.jitter(1.5))
    for name, a0, a1, z0, z1 in C.FRONT_WALL_DECALS:
        shell.wall_box(m, walls["front"], a0, a1, z0, z1, 0.004, 0.008, "Poster_Colour", 0.0, 1, geo.jitter(1.5))
    # stickers: (wall, u range, z range, count)
    zones = [("left", (-1.48, -0.30), (0.30, 0.72), 7), ("left", (-1.05, -0.30), (1.20, 1.80), 4),
             ("front", (-2.08, -1.88), (0.50, 1.70), 5),
             ("front", (-0.12, 0.56), (0.25, 1.95), 8), ("front", (1.90, 2.08), (0.40, 2.10), 4),
             ("left", (0.75, 1.45), (0.35, 1.90), 5)]
    joints = {"front": [-1.045, 0.0, 1.045], "left": [-0.497, 0.497]}
    for wall, (u0, u1), (z0, z1), n in zones:
        for _ in range(n):
            w, h = geo.RNG.uniform(0.04, 0.13), geo.RNG.uniform(0.04, 0.11)
            u, z = geo.RNG.uniform(u0, u1 - w), geo.RNG.uniform(z0, z1 - h)
            on_batten = any(abs(u + w / 2 - j) < C.SHELL["batten_w"] / 2 + w / 2 for j in joints[wall])
            wbase = C.SHELL["batten_t"] if on_batten else 0.004
            shell.wall_box(m, walls[wall], u, u + w, z, z + h, wbase, wbase + 0.002, geo.RNG.choice(STICKER_MATS),
                           0.0, 1, geo.jitter(12.0))


def downpipe(m):
    x, y = X0 - 0.11, Y1 + 0.11
    geo.pipe(m, (x, y, C.CANOPY_BOTTOM), (x, y, PH + 0.12), 0.035, "Steel_Galvanised", 14)
    geo.pipe(m, (x, y, PH + 0.12), (x - 0.12, y + 0.08, PH + 0.03), 0.035, "Steel_Galvanised", 14)
    for zz in (0.6, 1.3, 2.0):
        geo.box(m, x - 0.045, x + 0.045, y - 0.045, Y1 + 0.06, zz - 0.015, zz + 0.015, "Steel_Dark", 0.003)


# ---- Ground props ---------------------------------------------------------------------------

def slat_crate(m, cx, cy, w, d, h, z0, mat="Wood_Crate"):
    """Open-top crate with three slats per side and corner posts."""
    t, ph = 0.018, h / 3
    for k in range(3):
        za, zb = z0 + k * ph + 0.012, z0 + (k + 1) * ph - 0.012
        geo.box(m, cx - w / 2, cx + w / 2, cy - d / 2, cy - d / 2 + t, za, zb, mat, 0.003)
        geo.box(m, cx - w / 2, cx + w / 2, cy + d / 2 - t, cy + d / 2, za, zb, mat, 0.003)
        geo.box(m, cx - w / 2, cx - w / 2 + t, cy - d / 2, cy + d / 2, za, zb, mat, 0.003)
        geo.box(m, cx + w / 2 - t, cx + w / 2, cy - d / 2, cy + d / 2, za, zb, mat, 0.003)
    for sx in (-1, 1):
        for sy in (-1, 1):
            geo.box(m, cx + sx * w / 2 - (0.035 if sx > 0 else 0), cx + sx * w / 2 + (0.035 if sx < 0 else 0),
                    cy + sy * d / 2 - (0.035 if sy > 0 else 0), cy + sy * d / 2 + (0.035 if sy < 0 else 0), z0, z0 + h, mat, 0.004)
    geo.box(m, cx - w / 2 + t, cx + w / 2 - t, cy - d / 2 + t, cy + d / 2 - t, z0, z0 + 0.015, mat)


def bottle_crate(m, cx, cy, w, d, h, z0):
    mat = "Plastic_Red"
    geo.box(m, cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, z0, z0 + 0.02, mat, 0.004)
    for zz in (z0 + h - 0.03, z0 + h * 0.45):
        for (a0, a1, b0, b1) in ((-w / 2, w / 2, -d / 2, -d / 2 + 0.02), (-w / 2, w / 2, d / 2 - 0.02, d / 2),
                                 (-w / 2, -w / 2 + 0.02, -d / 2, d / 2), (w / 2 - 0.02, w / 2, -d / 2, d / 2)):
            geo.box(m, cx + a0, cx + a1, cy + b0, cy + b1, zz, zz + 0.03, mat, 0.003)
    for k in range(5):
        u = -w / 2 + 0.01 + k * (w - 0.02) / 4
        for yy in (cy - d / 2 + 0.01, cy + d / 2 - 0.01):
            geo.box(m, cx + u - 0.01, cx + u + 0.01, yy - 0.01, yy + 0.01, z0, z0 + h, mat, 0.003)
    for k in range(4):
        v = -d / 2 + 0.01 + k * (d - 0.02) / 3
        for xx in (cx - w / 2 + 0.01, cx + w / 2 - 0.01):
            geo.box(m, xx - 0.01, xx + 0.01, cy + v - 0.01, cy + v + 0.01, z0, z0 + h, mat, 0.003)
    for gx in (-0.1, 0.0, 0.1):  # inner grid
        geo.box(m, cx + gx - 0.004, cx + gx + 0.004, cy - d / 2, cy + d / 2, z0, z0 + h * 0.7, mat)


def bin_(m, cx, cy, r, h, mat):
    geo.lathe(m, (cx, cy, PH), [(r * 0.88, 0.0), (r, h * 0.92), (r * 1.04, h * 0.92), (r * 1.04, h)], mat, 24)
    geo.cylinder(m, (cx, cy, PH + h + 0.012), r * 1.06, 0.025, mat, segments=24)
    for zz in (0.25, 0.55):
        geo.cylinder(m, (cx, cy, PH + h * zz), r * (0.88 + 0.12 * zz) + 0.006, 0.012, mat, segments=24, cap=False)
    for s in (-1, 1):
        geo.box(m, cx + s * (r + 0.01), cx + s * (r + 0.035), cy - 0.05, cy + 0.05, PH + h * 0.8, PH + h * 0.86, "Rubber_Black", 0.004)


def utility_cabinet(m, cx, cy, w, d, h):
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2
    geo.box(m, x0, x1, y0, y1, PH, PH + h, "Steel_Grey", 0.015, 2)
    geo.box(m, x0 + 0.03, x1 - 0.03, y0 - 0.004, y0, PH + 0.05, PH + h - 0.05, "Steel_Dark", 0.002)
    geo.box(m, x0 + 0.035, x1 - 0.035, y0 - 0.006, y0 - 0.002, PH + 0.055, PH + h - 0.055, "Steel_Grey", 0.004)
    for k in range(6):
        zz = PH + h - 0.2 + k * 0.025
        geo.box(m, x0 + 0.08, x1 - 0.08, y0 - 0.01, y0 - 0.006, zz, zz + 0.01, "Rubber_Black")
    geo.box(m, x1 - 0.08, x1 - 0.06, y0 - 0.03, y0 - 0.006, PH + h * 0.45, PH + h * 0.6, "Steel_Dark", 0.004)
    geo.box(m, x0 + 0.1, x0 + 0.22, y0 - 0.008, y0 - 0.006, PH + 0.25, PH + 0.33, "Stock_Yellow")


def stool(m, sx, sy):
    seat_z = PH + 0.72
    geo.lathe(m, (sx, sy, seat_z), [(0.17, 0.0), (0.18, 0.02), (0.18, 0.045), (0.16, 0.06), (0.0, 0.065)],
              "Cushion_Red", 24, cap_top=False)
    geo.cylinder(m, (sx, sy, seat_z - 0.015), 0.15, 0.03, "Steel_Dark", segments=20)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        geo.pipe(m, (sx + 0.10 * math.cos(a), sy + 0.10 * math.sin(a), seat_z - 0.03),
                 (sx + 0.16 * math.cos(a), sy + 0.16 * math.sin(a), PH), 0.012, "Steel_Dark", 8)
    ring_z, ring_r = PH + 0.26, 0.145
    pts = [(sx + ring_r * math.cos(2 * math.pi * k / 12), sy + ring_r * math.sin(2 * math.pi * k / 12), ring_z) for k in range(13)]
    for p, q in zip(pts, pts[1:]):
        geo.pipe(m, p, q, 0.008, "Steel_Dark", 6)


def railing(m):
    r = C.RAILING
    y = r["y0"]
    while y <= r["y1"] + 1e-6:
        geo.pipe(m, (r["x"], y, PH), (r["x"], y, PH + r["h"]), 0.022, "Steel_Dark", 10)
        geo.box(m, r["x"] - 0.05, r["x"] + 0.05, y - 0.05, y + 0.05, PH, PH + 0.008, "Steel_Dark")
        y += 0.65
    for zz in (r["h"], r["h"] * 0.5):
        geo.pipe(m, (r["x"], r["y0"] - 0.03, PH + zz), (r["x"], r["y1"] + 0.03, PH + zz), 0.02, "Steel_Dark", 10)


def ground_props(m):
    boxes = {b[0]: b for b in C.GROUND_BOXES}
    _, cx, cy, w, d, h = boxes["CrateStack_A"]
    slat_crate(m, cx, cy, w, d, h / 2, PH)
    slat_crate(m, cx + 0.02, cy - 0.01, w * 0.95, d * 0.95, h / 2, PH + h / 2)
    _, cx, cy, w, d, h = boxes["CrateStack_B"]  # equipment cabinet with a lit display
    geo.box(m, cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, PH, PH + h, "Cabinet_Green", 0.012, 2)
    geo.box(m, cx - w / 2 - 0.004, cx - w / 2, cy - 0.15, cy + 0.1, PH + h - 0.3, PH + h - 0.12, "Screen_Multi")
    geo.box(m, cx - w / 2 - 0.006, cx - w / 2, cy - 0.2, cy + 0.2, PH + 0.1, PH + 0.5, "Steel_Dark", 0.004)
    _, cx, cy, w, d, h = boxes["RedCrate"]
    bottle_crate(m, cx, cy, w, d, h, PH)
    _, cx, cy, w, d, h = boxes["UtilityCabinet"]
    utility_cabinet(m, cx, cy, w, d, h)
    for name, cx, cy, r, h in C.BINS:
        bin_(m, cx, cy, r, h, "Bin_Green" if "Green" in name else "Steel_Grey")
    for sx, sy in C.STOOLS:
        stool(m, sx, sy)
    railing(m)
    geo.box(m, -2.95, -2.55, 2.25, 2.5, PH, PH + 0.18, "Cardboard", 0.006, rot=None)  # flattened boxes
    geo.box(m, -3.0, -2.62, 2.2, 2.48, PH + 0.18, PH + 0.3, "Cardboard", 0.006)


def build(coll, materials, B):
    geo.reseed(31337)
    m = geo.Mesh("Clutter_Detail")
    electrical(m)
    lanterns(m, B, coll)
    posters_and_stickers(m)
    downpipe(m)
    ground_props(m)
    return m.build(coll, materials)
