"""Massing pass (2026-10-04): heavy structural forms around the body, exported as their own mesh
(SM_Kiosk_Structure) so the earlier steps stay as they were.

The body walls and the openings fitted to the reference don't move. Mass is added outward:
a dark base frame, corner angles, a header beam under the soffit, a deep surround and hood
around the service window, a framed bay around the glazed window, wall-mounted equipment
housings and a few overlapping repair plates. Large forms only; no rivets or small parts.
Wall coordinates as in shell.py: u along the wall, z height, w outward from the wall plane.
"""
import kiosk_config as C
from . import geo
from . import shell
from .shell import WALLS, wall_box

M = C.MASSING
PH, TOP = C.PLATFORM_H, C.BODY_TOP


def ring(mesh, z0, z1, proud, mat, bevel, holes=None):
    """A band around all four walls. The front/back pieces run past the corners to wrap them;
    the side pieces stop at the corners, so no two faces are coplanar."""
    holes = holes or {}
    for name, wall in WALLS.items():
        u0, u1 = wall["u"]
        if wall["axis"] == "X":
            u0, u1 = u0 - proud, u1 + proud
        for r in geo.subtract_rects((u0, u1, z0, z1), holes.get(name, [])):
            wall_box(mesh, wall, r[0], r[1], r[2], r[3], -0.012, proud, mat, bevel, 2)


def base_and_header(mesh):
    d = C.DOOR
    door = [(d["y"] - d["w"] / 2 - 0.065, d["y"] + d["w"] / 2 + 0.065, PH - 1, TOP + 1)]  # outside the jambs
    bh, bp = M["base_h"], M["base_proud"]
    ring(mesh, PH, PH + bh, bp, "Steel_Dark", 0.01, {"left": door})
    ring(mesh, PH + bh - M["base_lip_h"], PH + bh, M["base_lip_proud"], "Steel_Dark", 0.008, {"left": door})  # drip ledge
    ring(mesh, TOP - M["header_h"], TOP, M["header_proud"], "Steel_Dark", 0.01)


def corner_angles(mesh):
    """Steel angles wrapping each vertical corner: one flange on each wall, proud of the base and
    header. Flange widths come from MASSING['corners'] so they clear the parts by the corners."""
    t = M["corner_t"]
    for (xw, yw), (fx, fy) in M["corners"].items():
        x = C.X0 if xw == "left" else C.X1
        y = C.Y0 if yw == "front" else C.Y1
        sx, sy = (-1 if xw == "left" else 1), (-1 if yw == "front" else 1)
        ox, oy = x + sx * t, y + sy * t  # outer corner
        # flange on the front/back wall (runs along X), then on the left/right wall (runs along Y)
        geo.box(mesh, min(ox, ox - sx * fx), max(ox, ox - sx * fx), min(y, oy), max(y, oy), PH, TOP, "Kiosk_YellowPaint_Dark", 0.008, 2)
        geo.box(mesh, min(x, ox), max(x, ox), min(oy - sy * t, oy - sy * fy), max(oy - sy * t, oy - sy * fy), PH, TOP,
                "Kiosk_YellowPaint_Dark", 0.008, 2)


def service_surround(mesh):
    """Thick jambs either side of the service window and a deep hood over it, so the opening
    reads as cut through a heavy wall. A lit strip under the hood, as in the reference."""
    front, sw, hood = WALLS["front"], C.SERVICE_WINDOW, M["service_hood"]
    fw, jw, jp = C.SHELL["frame_w"], M["service_jamb_w"], M["service_jamb_proud"]
    for a0, a1 in ((sw["x0"] - fw - jw, sw["x0"] - fw), (sw["x1"] + fw, sw["x1"] + fw + jw)):
        wall_box(mesh, front, a0, a1, C.COUNTER["z"], hood["z0"], 0.0, jp, "Kiosk_YellowPaint_Dark", 0.01, 2)
    wall_box(mesh, front, hood["x0"], hood["x1"], hood["z0"], hood["z1"], -0.01, hood["proud"], "Steel_Dark", 0.012, 2)
    wall_box(mesh, front, hood["x0"] - 0.02, hood["x1"] + 0.02, hood["z1"] - 0.05, hood["z1"], -0.01, hood["proud"] + 0.03,
             "Steel_Dark", 0.008, 2)  # top flange
    wall_box(mesh, front, sw["x0"], sw["x1"], hood["z0"] - 0.012, hood["z0"], hood["proud"] - 0.07, hood["proud"] - 0.035,
             "Tube_WarmWhite")
    # Reveal: dark steel lining the sides and head of the opening, from just behind the jamb faces
    # back past the wall plane, so the first part of the opening reads as the wall's thickness
    # (the tiled interior starts behind it). It stands t inside the opening's edges.
    rv = M["service_reveal"]
    t, w0, w1 = rv["t"], -rv["depth"], jp - 0.02
    for a0, a1 in ((sw["x0"] - fw, sw["x0"] + t), (sw["x1"] - t, sw["x1"] + fw)):
        wall_box(mesh, front, a0, a1, sw["z0"], sw["z1"] - t, w0, w1, "Steel_Dark", 0.006, 2)
    wall_box(mesh, front, sw["x0"] - fw, sw["x1"] + fw, sw["z1"] - t, hood["z0"], w0, hood["proud"] - 0.075,
             "Steel_Dark", 0.006, 2)


def window_bay(mesh):
    """Box-out frame around the glazed window and its lightbox: two posts and a sill block."""
    front, b = WALLS["front"], M["bay"]
    z_lo, z_hi = PH + M["base_h"], TOP - M["header_h"]
    for a0, a1 in ((b["x0"], b["x0"] + b["post_w"]), (b["x1"] - b["post_w"], b["x1"])):
        wall_box(mesh, front, a0, a1, z_lo, z_hi, 0.0, b["proud"], "Kiosk_YellowPaint_Dark", 0.01, 2)
    wall_box(mesh, front, b["x0"], b["x1"], z_lo, b["sill_z1"], 0.0, b["proud"], "Kiosk_YellowPaint_Dark", 0.01, 2)


def slats(mesh, wall, u0, u1, z0, z1, w, n, horizontal=True):
    for k in range(n):
        if horizontal:
            z = z0 + (k + 0.5) * (z1 - z0) / n
            wall_box(mesh, wall, u0, u1, z - 0.012, z + 0.012, w, w + 0.018, "Steel_Dark", 0.003)
        else:
            u = u0 + (k + 0.5) * (u1 - u0) / n
            wall_box(mesh, wall, u - 0.012, u + 0.012, z0, z1, w, w + 0.018, "Steel_Dark", 0.003)


def housings(mesh):
    """Wall-mounted equipment: a big louvred ventilation housing on the right wall (it breaks
    the body's right edge from the camera) with a duct up into the canopy, and a shallow
    utility box on the door wall."""
    for name, wall_name, u0, u1, z0, z1, depth in C.WALL_HOUSINGS:
        wall = WALLS[wall_name]
        wall_box(mesh, wall, u0, u1, z0, z1, 0.0, depth, "Steel_Grey", 0.015, 2)
        if name.startswith("VentHousing"):
            # frame band round the front, louvre bank on the face, a side louvre bank, a duct to the soffit
            wall_box(mesh, wall, u0 - 0.02, u1 + 0.02, z1 - 0.08, z1 + 0.02, 0.0, depth + 0.025, "Steel_Dark", 0.008, 2)
            wall_box(mesh, wall, u0 - 0.02, u1 + 0.02, z0 - 0.02, z0 + 0.06, 0.0, depth + 0.025, "Steel_Dark", 0.008, 2)
            slats(mesh, wall, u0 + 0.08, u1 - 0.08, z0 + 0.25, z1 - 0.2, depth, 11)
            uc = (u0 + u1) / 2
            wall_box(mesh, wall, uc - 0.13, uc + 0.13, z1, TOP, 0.05, 0.31, "Steel_Galvanised", 0.01, 2)
            wall_box(mesh, wall, uc - 0.16, uc + 0.16, z1, z1 + 0.06, 0.03, 0.34, "Steel_Dark", 0.006)
            # camera-side end of the housing: louvres on its -Y face
            ya = u0  # the right wall runs along +Y; u0 is the end nearer the front
            for k in range(7):
                z = z0 + 0.3 + k * (z1 - z0 - 0.6) / 6
                geo.box(mesh, C.X1 + 0.05, C.X1 + depth - 0.05, ya - 0.018, ya, z - 0.012, z + 0.012, "Steel_Dark", 0.003)
        else:
            # door panel inset, handle, a short louvre strip
            wall_box(mesh, wall, u0 + 0.035, u1 - 0.035, z0 + 0.035, z1 - 0.035, depth - 0.004, depth + 0.006, "Steel_Galvanised", 0.004)
            wall_box(mesh, wall, u1 - 0.08, u1 - 0.06, (z0 + z1) / 2 - 0.07, (z0 + z1) / 2 + 0.07, depth, depth + 0.035, "Steel_Dark", 0.004)
            slats(mesh, wall, u0 + 0.07, u1 - 0.12, z0 + 0.06, z0 + 0.16, depth + 0.006, 3)


def repair_plates(mesh):
    """Big overlapping plates bolted over old damage: the body reads as refitted over years."""
    for wall_name, u0, u1, z0, z1, proud, tilt, mat in C.REPAIR_PLATES:
        w0 = shell.surface_w(wall_name, u0, u1, z0, z1)  # on top of the sheets (some stand proud)
        wall_box(mesh, WALLS[wall_name], u0, u1, z0, z1, w0 - 0.002, w0 + proud, mat, 0.004, 1, tilt)
        shell.LAYOUT.setdefault(wall_name, []).append((u0, u1, z0, z1, w0 + proud))


def build(coll, materials):
    geo.reseed(2604)
    m = geo.Mesh("Structure")
    base_and_header(m)
    corner_angles(m)
    service_surround(m)
    window_bay(m)
    housings(m)
    repair_plates(m)
    return m.build(coll, materials)
