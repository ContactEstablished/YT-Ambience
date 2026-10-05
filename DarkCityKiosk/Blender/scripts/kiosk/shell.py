"""Detailed body shell: core, steel panels, riveted battens, corner posts, skirt, top beam,
service-window frame, and the concrete platform.

Wall coordinates: u runs along the wall (front/back: +X, left/right: +Y), z is height,
w is distance outward from the wall plane. The panels' outer faces sit on the wall plane,
so everything the grey box attached to the walls still lines up.

Construction pass (2026-10-04): the panels no longer follow an even grid. Joints come from
kiosk_config.PANEL_JOINTS (uneven, with narrow fillers by the door), and each joint has its own
treatment: a bare seam, a riveted batten, a lap (the next sheet overlaps), or a wide bolted
reinforcement strip. Sheets are split at uneven heights, the upper sheet often lapping over the
lower one, and some are replacement sheets in a different paint, standing a few mm proud.
"""
import math
import random

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


def joint_plan(name):
    """Panel joints along a wall, [(u, kind)]: PANEL_JOINTS if the wall is listed, else seeded
    uneven widths (the walls the camera never sees squarely)."""
    if name in C.PANEL_JOINTS:
        return list(C.PANEL_JOINTS[name])
    wall = WALLS[name]
    u, u_end = wall["u"][0] + POST, wall["u"][1] - POST
    rng = random.Random("panels-" + name)
    out = []
    while True:
        u += rng.uniform(*C.PANEL_WIDTHS)
        if u > u_end - 0.8 * C.PANEL_WIDTHS[0]:
            return out
        out.append((u, rng.choice(("seam", "batten", "lap", "seam", "batten", "strip"))))


# Raised shell parts per wall, [(u0, u1, z0, z1, outer w)], filled in by build_wall. Parts laid on the
# wall later (posters, stickers, plates) ask surface_w() how far out the shell stands under them.
LAYOUT = {}


def surface_w(name, u0, u1, z0, z1):
    """Outermost w of the shell skin (sheets, battens, strips) under the rectangle."""
    return max([p[4] for p in LAYOUT.get(name, []) if p[0] < u1 and p[1] > u0 and p[2] < z1 and p[3] > z0], default=0.0)


def _clear(holes, u, z, margin=0.025):
    return not any(h[0] - margin < u < h[1] + margin and h[2] - margin < z < h[3] + margin for h in holes)


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


def wall_rivets(mesh, wall, pts_uz, w, mat, radius=None):
    geo.rivets(mesh, [world(wall, u, z, w) for u, z in pts_uz], wall["normal"], mat, radius or S["rivet_r"])


def wall_bolts(mesh, wall, pts_uz, w, mat, radius=None):
    geo.bolts(mesh, [world(wall, u, z, w) for u, z in pts_uz], wall["normal"], mat, radius or C.FASTENERS["bolt_r"])


def _steps(a, b, pitch):
    """Points from a to b (both ends) about `pitch` apart."""
    if b <= a:
        return [(a + b) / 2]
    n = max(1, round((b - a) / pitch))
    return [a + k * (b - a) / n for k in range(n + 1)]


def _sheet_paint(rng):
    r = rng.random()
    for mat, p in C.PANEL_PAINT.items():
        if r < p:
            return mat
        r -= p
    return "Kiosk_YellowPaint"


def build_wall(mesh, name):
    wall = WALLS[name]
    holes = openings(name)
    u_start, u_end = wall["u"][0] + POST, wall["u"][1] - POST
    z_lo, z_hi = PH + S["skirt_h"], TOP - S["topbeam_h"]
    gap, t, lap_w, lap_t = S["panel_gap"], S["panel_t"], S["lap_w"], S["lap_t"]
    plan = joint_plan(name)
    edges = [u_start] + [u for u, _ in plan] + [u_end]
    kinds = [None] + [k for _, k in plan] + [None]
    raised = LAYOUT.setdefault(name, [])
    raised.clear()
    rng, sp = geo.RNG, C.PANEL_SPLITS

    # Sheets between the joints. At a "lap" joint the right-hand sheet runs over the left one; a
    # split sheet's upper part often laps down over the lower part (sheds rain). Lapping parts
    # stand out by lap_t, with a rivet row along the lap.
    for i in range(len(edges) - 1):
        laps_left = kinds[i] == "lap"
        u0 = edges[i] - lap_w if laps_left else edges[i] + gap / 2
        u1 = edges[i + 1] - gap / 2
        proud = lap_t if laps_left else 0.0
        if rng.random() < S["refit_chance"]:  # a later replacement sheet, a few mm proud
            proud += rng.uniform(0.002, S["panel_jitter_out"])
        mat = _sheet_paint(rng)
        r = rng.random()
        cuts = []
        if r < sp["two"]:
            cuts = [rng.uniform(*sp["z2"][0]), rng.uniform(*sp["z2"][1])]
        elif r < sp["two"] + sp["one"]:
            cuts = [rng.uniform(*sp["z1"])]
        zs = [z_lo] + cuts + [z_hi]
        for k in range(len(zs) - 1):
            lap_below = k > 0 and rng.random() < sp["lap"]
            b0 = zs[k] - lap_w if lap_below else zs[k] + (gap / 2 if k > 0 else 0.0)
            b1 = zs[k + 1] - (gap / 2 if k < len(zs) - 2 else 0.0)
            w_out = proud + (lap_t if lap_below else 0.0)
            band_mat = mat if k == 0 or rng.random() < 0.7 else _sheet_paint(rng)
            for rr in geo.subtract_rects((u0, u1, b0, b1), holes):
                wall_box(mesh, wall, rr[0], rr[1], rr[2], rr[3], -t + 0.002, w_out, band_mat,
                         S["panel_bevel"], 1, geo.jitter(S["panel_jitter_tilt_deg"]))
                raised.append((rr[0], rr[1], rr[2], rr[3], w_out))
            pitch = rng.uniform(0.08, 0.12)
            pts = []
            if lap_below:  # rivet row along the horizontal lap
                zr = zs[k] - lap_w / 2
                pts += [(u, zr) for u in _steps(u0 + 0.03, u1 - 0.03, pitch)]
            if laps_left:  # rivet column along the vertical lap
                ur = edges[i] - lap_w / 2
                pts += [(ur, z) for z in _steps(b0 + 0.04, b1 - 0.04, pitch)]
            wall_rivets(mesh, wall, [p for p in pts if _clear(holes, *p)], w_out, band_mat, C.FASTENERS["rivet_r"])

    # Joint covers: battens (flat bar, two rivet columns), strips (wide plate, paired bolts),
    # and rivet columns either side of some bare seams. Covers sit on the sheets under them.
    bw, bt = S["batten_w"], S["batten_t"]
    covers = []
    for uj, kind in plan:
        if kind == "batten":
            for rr in geo.subtract_rects((uj - bw / 2, uj + bw / 2, z_lo, z_hi), holes):
                w0 = surface_w(name, *rr) - 0.002
                wall_box(mesh, wall, rr[0], rr[1], rr[2], rr[3], w0, w0 + bt, "Kiosk_YellowPaint_Dark", 0.003)
                covers.append((rr[0], rr[1], rr[2], rr[3], w0 + bt))
                pts = [(uj + side * bw * 0.31, z) for side in (-1, 1) for z in _steps(rr[2] + 0.04, rr[3] - 0.04, rng.uniform(0.08, 0.11))]
                wall_rivets(mesh, wall, pts, w0 + bt, "Kiosk_YellowPaint_Dark")
        elif kind == "strip":
            sw_, st = S["strip_w"], S["strip_t"]
            for rr in geo.subtract_rects((uj - sw_ / 2, uj + sw_ / 2, z_lo, z_hi), holes):
                w0 = surface_w(name, *rr) - 0.002
                wall_box(mesh, wall, rr[0], rr[1], rr[2], rr[3], w0, w0 + st, "Kiosk_YellowPaint_Dark", 0.005, 2)
                covers.append((rr[0], rr[1], rr[2], rr[3], w0 + st))
                pts = [(uj + side * sw_ * 0.27, z) for side in (-1, 1) for z in _steps(rr[2] + 0.06, rr[3] - 0.06, rng.uniform(0.22, 0.28))]
                wall_bolts(mesh, wall, pts, w0 + st, "Kiosk_YellowPaint_Dark", C.FASTENERS["bolt_small_r"])
        elif kind == "seam" and rng.random() < 0.5:
            pitch = rng.uniform(0.13, 0.18)
            pts = [(uj + side * 0.03, z) for side in (-1, 1) for z in _steps(z_lo + 0.08, z_hi - 0.06, pitch)]
            for p in pts:
                if _clear(holes, *p):
                    wall_rivets(mesh, wall, [p], surface_w(name, p[0] - 0.005, p[0] + 0.005, p[1] - 0.005, p[1] + 0.005),
                                "Kiosk_YellowPaint_Dark", C.FASTENERS["rivet_r"])
    raised.extend(covers)

    # Skirt (dark plinth band), interrupted by the door
    sk_holes = [(h[0], h[1], PH - 1, PH + S["skirt_h"] + 1) for h in holes if h[2] <= PH + 0.01]
    for r in geo.subtract_rects((wall["u"][0] + POST, wall["u"][1] - POST, PH, PH + S["skirt_h"]), sk_holes):
        wall_box(mesh, wall, r[0], r[1], r[2], r[3], -t, S["skirt_t"], "Steel_Dark", 0.004)
        k = int((r[1] - r[0] - 0.1) / 0.15)
        wall_rivets(mesh, wall, [(r[0] + 0.05 + j * 0.15, r[3] - 0.03) for j in range(k + 1)], S["skirt_t"], "Steel_Dark")

    # Top beam under the canopy
    wall_box(mesh, wall, wall["u"][0] + POST, wall["u"][1] - POST, TOP - S["topbeam_h"], TOP, -t, S["topbeam_t"],
             "Kiosk_YellowPaint_Dark", 0.005, 1)
    k = int((u_end - u_start - 0.1) / 0.12)
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
