"""Detailed body shell: core, steel panels, riveted battens, corner posts, skirt, top beam,
service-window frame, and the concrete platform.

Wall coordinates: u runs along the wall (front/back: +X, left/right: +Y), z is height,
w is distance outward from the wall plane. The panels' outer faces sit on the wall plane,
so everything the grey box attached to the walls still lines up.
"""
import math

from mathutils import Euler

import kiosk_config as C
from . import geo

S = C.SHELL
PH, TOP = C.PLATFORM_H, C.BODY_TOP
POST = C.CORNER_POST / 2

WALLS = {
    "front": {"axis": "X", "fixed": C.Y0, "out": -1, "u": (C.X0, C.X1), "normal": "-Y"},
    "back": {"axis": "X", "fixed": C.Y1, "out": 1, "u": (C.X0, C.X1), "normal": "+Y"},
    "left": {"axis": "Y", "fixed": C.X0, "out": -1, "u": (C.Y0, C.Y1), "normal": "-X"},
    "right": {"axis": "Y", "fixed": C.X1, "out": 1, "u": (C.Y0, C.Y1), "normal": "+X"},
}


def openings(name):
    """Holes in the panel skin, (u0, u1, z0, z1)."""
    if name == "front":
        sw, gw = C.SERVICE_WINDOW, C.GLAZED_WINDOW
        return [(sw["x0"], sw["x1"], sw["z0"], sw["z1"]), (gw["x0"], gw["x1"], gw["z0"], gw["z1"])]
    if name == "left":
        d = C.DOOR
        return [(d["y"] - d["w"] / 2, d["y"] + d["w"] / 2, PH, PH + d["h"])]
    return []


def world(wall, u, z, w):
    if wall["axis"] == "X":
        return (u, wall["fixed"] + wall["out"] * w, z)
    return (wall["fixed"] + wall["out"] * w, u, z)


def wall_box(mesh, wall, u0, u1, z0, z1, w0, w1, mat, bevel=0.0, segments=1, tilt_deg=0.0):
    a, b = world(wall, u0, z0, w0), world(wall, u1, z1, w1)
    rot = None
    if tilt_deg:
        t = math.radians(tilt_deg)
        rot = Euler((0.0, t, 0.0)) if wall["axis"] == "X" else Euler((t, 0.0, 0.0))
    geo.box(mesh, a[0], b[0], a[1], b[1], a[2], b[2], mat, bevel, segments, rot)


def wall_rivets(mesh, wall, pts_uz, w, mat):
    geo.rivets(mesh, [world(wall, u, z, w) for u, z in pts_uz], wall["normal"], mat, S["rivet_r"])


def build_wall(mesh, name):
    wall = WALLS[name]
    holes = openings(name)
    u_start, u_end = wall["u"][0] + POST, wall["u"][1] - POST
    z_lo, z_hi = PH + S["skirt_h"], TOP - S["topbeam_h"]
    length = u_end - u_start
    n = max(1, round(length / C.SEAM_SPACING))
    pw, gap, t = length / n, S["panel_gap"], S["panel_t"]

    # Panels (some split horizontally), skipping openings
    for i in range(n):
        u0, u1 = u_start + i * pw + gap / 2, u_start + (i + 1) * pw - gap / 2
        bands = [(z_lo, z_hi)]
        if geo.RNG.random() < S["split_chance"]:
            zs = geo.RNG.uniform(*S["split_z"])
            bands = [(z_lo, zs - gap / 2), (zs + gap / 2, z_hi)]
        for b0, b1 in bands:
            for r in geo.subtract_rects((u0, u1, b0, b1), holes):
                proud = geo.RNG.uniform(0.0, S["panel_jitter_out"])
                wall_box(mesh, wall, r[0], r[1], r[2], r[3], -t + 0.002, proud, "Kiosk_YellowPaint",
                         S["panel_bevel"], 1, geo.jitter(S["panel_jitter_tilt_deg"]))

    # Battens over the joints, with two rivet columns each
    bw, bt, rp = S["batten_w"], S["batten_t"], S["rivet_pitch"]
    for i in range(1, n):
        uj = u_start + i * pw
        for r in geo.subtract_rects((uj - bw / 2, uj + bw / 2, z_lo, z_hi), holes):
            wall_box(mesh, wall, r[0], r[1], r[2], r[3], 0.0, bt, "Kiosk_YellowPaint_Dark", 0.003)
            steps = int((r[3] - r[2] - 0.08) / rp)
            pts = [(uj + side * bw * 0.31, r[2] + 0.04 + k * rp) for side in (-1, 1) for k in range(steps + 1)]
            wall_rivets(mesh, wall, pts, bt, "Kiosk_YellowPaint_Dark")

    # Skirt (dark plinth band), interrupted by the door
    sk_holes = [(h[0], h[1], PH - 1, PH + S["skirt_h"] + 1) for h in holes if h[2] <= PH + 0.01]
    for r in geo.subtract_rects((wall["u"][0] + POST, wall["u"][1] - POST, PH, PH + S["skirt_h"]), sk_holes):
        wall_box(mesh, wall, r[0], r[1], r[2], r[3], -t, S["skirt_t"], "Steel_Dark", 0.004)
        k = int((r[1] - r[0] - 0.1) / 0.15)
        wall_rivets(mesh, wall, [(r[0] + 0.05 + j * 0.15, r[3] - 0.03) for j in range(k + 1)], S["skirt_t"], "Steel_Dark")

    # Top beam under the canopy
    wall_box(mesh, wall, wall["u"][0] + POST, wall["u"][1] - POST, TOP - S["topbeam_h"], TOP, -t, S["topbeam_t"],
             "Kiosk_YellowPaint_Dark", 0.005, 1)
    k = int((length - 0.1) / 0.12)
    wall_rivets(mesh, wall, [(u_start + 0.05 + j * 0.12, TOP - S["topbeam_h"] + 0.025) for j in range(k + 1)],
                S["topbeam_t"], "Kiosk_YellowPaint_Dark")


def build_service_frame(mesh):
    wall, sw, fw, ft = WALLS["front"], C.SERVICE_WINDOW, S["frame_w"], S["frame_t"]
    u0, u1, z0, z1 = sw["x0"], sw["x1"], sw["z0"], sw["z1"]
    for (a0, a1, b0, b1) in ((u0 - fw, u1 + fw, z1, z1 + fw), (u0 - fw, u0, z0, z1), (u1, u1 + fw, z0, z1)):
        wall_box(mesh, wall, a0, a1, b0, b1, 0.0, ft, "Kiosk_YellowPaint_Dark", 0.006, 2)
    # roller-shutter box above the opening
    wall_box(mesh, wall, u0 - fw, u1 + fw, z1 + fw, z1 + fw + 0.14, 0.0, 0.11, "Steel_Grey", 0.012, 2)


def build_body(coll, cutters, materials):
    geo.reseed(1979)
    core = geo.Mesh("Body_Core")
    t = S["panel_t"]
    geo.box(core, C.X0 + t, C.X1 - t, C.Y0 + t, C.Y1 - t, PH, TOP, "Kiosk_Core")
    core_ob = core.build(coll, materials)
    # Openings cut through the core (real depth: the orbit looks into them)
    sw, gw = C.SERVICE_WINDOW, C.GLAZED_WINDOW
    for name, (x0, x1, y1, z0, z1) in {"ServiceWindow": (sw["x0"], sw["x1"], C.Y0 + sw["depth"], sw["z0"], sw["z1"]),
                                       "GlazedWindow": (gw["x0"], gw["x1"], C.Y0 + 0.08, gw["z0"], gw["z1"])}.items():
        cm = geo.Mesh(f"Cutter_{name}")
        geo.box(cm, x0, x1, C.Y0 - 0.1, y1, z0, z1, "Interior_Recess")
        cut = cm.build(cutters, materials)
        cut.hide_render = True
        cut.display_type = "WIRE"
        mod = core_ob.modifiers.new(f"Cut_{name}", "BOOLEAN")
        mod.operation, mod.object, mod.solver = "DIFFERENCE", cut, "EXACT"
        try:
            mod.material_mode = "TRANSFER"
        except AttributeError:
            pass

    skin = geo.Mesh("Body_Shell")
    for name in WALLS:
        build_wall(skin, name)
    for x, y in ((C.X0, C.Y0), (C.X1, C.Y0), (C.X0, C.Y1), (C.X1, C.Y1)):
        geo.box(skin, x - POST, x + POST, y - POST, y + POST, PH, TOP, "Kiosk_YellowPaint_Dark", S["post_bevel"], 3)
    build_service_frame(skin)
    return core_ob, skin.build(coll, materials)


def build_platform(coll, materials):
    m = C.PLATFORM_MARGIN
    plat = geo.Mesh("Platform")
    geo.box(plat, C.X0 - m, C.X1 + m, C.Y0 - m, C.Y1 + m, 0.0, PH, "Platform_Concrete", 0.018, 2)
    # steel edge angle along the two camera-facing edges
    geo.box(plat, C.X0 - m - 0.01, C.X1 + m, C.Y0 - m - 0.01, C.Y0 - m + 0.03, PH - 0.03, PH + 0.004, "Steel_Dark", 0.003)
    geo.box(plat, C.X0 - m - 0.01, C.X0 - m + 0.03, C.Y0 - m - 0.01, C.Y1 + m, PH - 0.03, PH + 0.004, "Steel_Dark", 0.003)
    return plat.build(coll, materials)
