"""Detailed canopy: plates, framed lightbox faces (front + left lit), riveted rails, corner
posts, soffit seams/conduit/junction boxes, tube-light fixtures, lettering, corner sign.

Massing pass (2026-10-04): the fascia is a deep box around the canopy edge, read from below as
bright yellow face / dark structure: a dark edge beam with a bottom flange hangs below the soffit,
the lit face sits in its rail frame, and a dark coping runs along the top. Heavy posts cap the
corners and dark joists cross the soffit from the walls to the edge beam.

The floor-level camera looks straight at the soffit, so the underside gets real detail.
Face coordinates: u along the face, z height, w outward from the face plane.
"""
import math

from mathutils import Euler

import kiosk_config as C
from . import geo

D = C.CANOPY_DETAIL
F = C.FASCIA
CX0, CX1, CY0, CY1 = C.CANOPY_X0, C.CANOPY_X1, C.CANOPY_Y0, C.CANOPY_Y1
CB, CT = C.CANOPY_BOTTOM, C.CANOPY_TOP
FZ0, FACE0, FACE1 = C.FASCIA_Z0, C.FACE_Z0, C.FACE_Z1

FACES = {
    "front": {"axis": "X", "fixed": CY0, "out": -1, "u": (CX0, CX1), "normal": "-Y", "lit": True},
    "left": {"axis": "Y", "fixed": CX0, "out": -1, "u": (CY0, CY1), "normal": "-X", "lit": True},
    "right": {"axis": "Y", "fixed": CX1, "out": 1, "u": (CY0, CY1), "normal": "+X", "lit": False},
    "back": {"axis": "X", "fixed": CY1, "out": 1, "u": (CX0, CX1), "normal": "+Y", "lit": False},
}


def world(face, u, z, w):
    if face["axis"] == "X":
        return (u, face["fixed"] + face["out"] * w, z)
    return (face["fixed"] + face["out"] * w, u, z)


def face_box(mesh, face, u0, u1, z0, z1, w0, w1, mat, bevel=0.0, segments=1):
    a, b = world(face, u0, z0, w0), world(face, u1, z1, w1)
    geo.box(mesh, a[0], b[0], a[1], b[1], a[2], b[2], mat, bevel, segments)


def build_face(mesh, face):
    rh, rt, dp = D["rail_h"], D["rail_t"], F["depth"]
    u0, u1 = face["u"]
    # dark edge beam hanging below the soffit, with a bottom flange a little further out
    face_box(mesh, face, u0, u1, FZ0, FACE0, -dp, F["beam_proud"], "Steel_Dark", 0.008, 2)
    face_box(mesh, face, u0, u1, FZ0, FZ0 + F["lip_h"], -dp + 0.02, F["lip_proud"], "Steel_Dark", 0.006, 2)
    # dark coping along the top (1 cm above the deck plate)
    face_box(mesh, face, u0, u1, FACE1, CT + 0.01, -dp, F["cap_proud"], "Steel_Dark", 0.008, 2)
    zb, zt = FACE0, FACE1
    # rails (top, bottom) and end stiles around the yellow face
    face_box(mesh, face, u0, u1, zt - rh, zt, -0.02, rt, "Kiosk_YellowPaint_Dark", 0.006, 2)
    face_box(mesh, face, u0, u1, zb, zb + rh, -0.02, rt, "Kiosk_YellowPaint_Dark", 0.006, 2)
    for a, b in ((u0, u0 + rh), (u1 - rh, u1)):
        face_box(mesh, face, a, b, zb + rh, zt - rh, -0.02, rt, "Kiosk_YellowPaint_Dark", 0.006, 2)
    inner = (u0 + rh, u1 - rh, zb + rh, zt - rh)
    if face["lit"]:
        di = D["diffuser_inset"]
        face_box(mesh, face, *inner, -di - 0.01, -di, "Lightbox_Yellow")
        n = max(1, round((inner[1] - inner[0]) / D["mullion_every"]))
        for k in range(1, n):
            u = inner[0] + k * (inner[1] - inner[0]) / n
            face_box(mesh, face, u - 0.009, u + 0.009, inner[2], inner[3], -di, 0.002, "Kiosk_YellowPaint_Dark", 0.002)
    else:
        face_box(mesh, face, *inner, -0.02, 0.004, "Kiosk_YellowPaint_Dark", 0.003)
    # rivets along both rails
    k = int((u1 - u0 - 0.1) / D["rail_rivet_pitch"])
    pts = [world(face, u0 + 0.05 + j * D["rail_rivet_pitch"], z, rt) for j in range(k + 1)
           for z in (zt - rh / 2, zb + rh / 2)]
    geo.rivets(mesh, pts, face["normal"], "Kiosk_YellowPaint_Dark", 0.008)


def build_soffit(mesh):
    # seams across the underside plate
    n = int((CX1 - CX0) / D["soffit_seam_every"])
    for k in range(1, n + 1):
        x = CX0 + k * (CX1 - CX0) / (n + 1)
        geo.box(mesh, x - 0.015, x + 0.015, CY0 + 0.05, CY1 - 0.05, CB - 0.008, CB, "Steel_Grey", 0.002)
    # tube-light fixtures hung on drop rods just inside the edge beam: housing + glowing tube + end caps
    tz = C.SOFFIT_TUBE_Z
    for axis, fixed, a, b in C.SOFFIT_TUBES:
        mid = (a + b) / 2
        if axis == "X":
            geo.box(mesh, a, b, fixed - 0.05, fixed + 0.05, tz + 0.02, tz + 0.065, "Steel_Grey", 0.008, 2)
            geo.cylinder(mesh, (mid, fixed, tz), 0.017, b - a - 0.08, "Tube_WarmWhite", axis="X", segments=12)
            for e in (a + 0.02, b - 0.02):
                geo.box(mesh, e - 0.02, e + 0.02, fixed - 0.03, fixed + 0.03, tz - 0.025, tz + 0.02, "Steel_Dark", 0.004)
            for r in (a + 0.15, b - 0.15):
                geo.pipe(mesh, (r, fixed, tz + 0.065), (r, fixed, CB), 0.008, "Steel_Dark", 6)
        else:
            geo.box(mesh, fixed - 0.05, fixed + 0.05, a, b, tz + 0.02, tz + 0.065, "Steel_Grey", 0.008, 2)
            geo.cylinder(mesh, (fixed, mid, tz), 0.017, b - a - 0.08, "Tube_WarmWhite", axis="Y", segments=12)
            for e in (a + 0.02, b - 0.02):
                geo.box(mesh, fixed - 0.03, fixed + 0.03, e - 0.02, e + 0.02, tz - 0.025, tz + 0.02, "Steel_Dark", 0.004)
            for r in (a + 0.15, b - 0.15):
                geo.pipe(mesh, (fixed, r, tz + 0.065), (fixed, r, CB), 0.008, "Steel_Dark", 6)
    # dark joists from the walls out to the edge beam (between the tube runs), and a diagonal
    # brace from the body's front-left corner out to the canopy corner. Construction pass: the
    # joists are I-sections (flanges and web cast layered shadows on the soffit).
    jh, dp = C.SOFFIT_JOIST_H, F["depth"]
    for x in C.SOFFIT_JOISTS["x"]:
        geo.ibeam(mesh, "Y", x, CY0 + dp - 0.01, C.Y0, CB - jh, CB, "Steel_Dark")
    for y in C.SOFFIT_JOISTS["y"]:
        geo.ibeam(mesh, "X", y, CX0 + dp - 0.01, C.X0, CB - jh, CB, "Steel_Dark")
    cx, cy = (C.X0 + CX0 + dp) / 2, (C.Y0 + CY0 + dp) / 2
    length = math.hypot(C.X0 - CX0 - dp, C.Y0 - CY0 - dp) + 0.06
    geo.box(mesh, cx - length / 2, cx + length / 2, cy - 0.045, cy + 0.045, CB - jh - 0.01, CB, "Steel_Dark", 0.006, 2,
            Euler((0.0, 0.0, math.atan2(C.Y0 - CY0 - dp, C.X0 - CX0 - dp))))
    # conduit runs along the wall lines, with junction boxes and drops into the header beam
    zc = CB - 0.03
    hp, hz = C.MASSING["header_proud"], C.BODY_TOP - C.MASSING["header_h"] / 2
    geo.pipe(mesh, (CX0 + 0.25, C.Y0 - 0.14, zc), (CX1 - 0.25, C.Y0 - 0.14, zc), 0.013, "Steel_Dark")
    geo.pipe(mesh, (C.X0 - 0.14, CY0 + 0.25, zc), (C.X0 - 0.14, CY1 - 0.25, zc), 0.013, "Steel_Dark")
    geo.pipe(mesh, (CX0 + 0.25, C.Y0 - 0.22, zc - 0.01), (CX1 - 0.6, C.Y0 - 0.22, zc - 0.01), 0.009, "Steel_Dark")
    jn = C.SOFFIT_JUNCTIONS
    for x, y, to_wall in [(x, C.Y0 - 0.14, "front") for x in jn["front"]] + [(C.X0 - 0.14, y, "left") for y in jn["left"]]:
        geo.box(mesh, x - 0.07, x + 0.07, y - 0.05, y + 0.05, CB - 0.1, CB, "Steel_Grey", 0.006, 2)
        end = (x, C.Y0 - hp + 0.01, hz) if to_wall == "front" else (C.X0 - hp + 0.01, y, hz)
        geo.pipe(mesh, (x, y, CB - 0.1), end, 0.008, "Steel_Dark")


def build_corner_sign(mesh, B, coll):
    """A vertical lightbox hung off the corner post at the fascia's right end. Signage pass
    (2026-10-05): the sign hangs in front, level with the post, on two brackets on the post's outer
    face; its printed face (コーヒー, the cup) is a graphics card from kiosk/graphics.py, in front of
    the old 3D lettering. The lettering and cup stay so the canopy keeps the same list of parts:
    weather.py keys each part's random history (paint generation, newness, chips) on its part number,
    and the weathering is locked."""
    s = C.CORNER_SIGN
    x0, x1, y0, y1 = s["x"] - s["w"] / 2, s["x"] + s["w"] / 2, s["y"] - s["d"] / 2, s["y"] + s["d"] / 2
    geo.box(mesh, x0, x1, y0, y1, s["z0"], s["z1"], "Kiosk_YellowPaint_Dark", 0.008, 2)
    geo.box(mesh, x0 + 0.03, x1 - 0.03, y0 - 0.006, y0 + 0.002, s["z0"] + 0.03, s["z1"] - 0.03, "Lightbox_Yellow")
    geo.box(mesh, x0 - 0.006, x0 + 0.002, y0 + 0.02, y1 - 0.02, s["z0"] + 0.03, s["z1"] - 0.03, "Lightbox_Yellow")
    post_x = CX1 + F["post_proud"] - 0.03  # into the corner post's outer face (its foot is at FZ0 - 0.05)
    geo.box(mesh, post_x, x0 + 0.01, s["y"] - 0.025, s["y"] + 0.025, FACE1 - 0.12, FACE1 - 0.06, "Steel_Dark", 0.005)
    geo.box(mesh, post_x, x0 + 0.01, s["y"] - 0.025, s["y"] + 0.025, FZ0 + 0.03, FZ0 + 0.09, "Steel_Dark", 0.005)
    # steaming cup icon at the bottom of the face
    cz = s["z0"] + 0.1
    geo.cylinder(mesh, (s["x"], y0 - 0.008, cz), 0.035, 0.006, "Sign_Text_Red", axis="Y", segments=16)
    B.text("Text_CornerSign", "コ\nー\nヒ\nー", 0.12, (s["x"], y0 - 0.009, (s["z0"] + s["z1"]) / 2 + 0.07),
           (90, 0, 0), B.M["sign_text_red"], coll, font=B.JP_FONT)


def build_lettering(B, coll):
    tf, tl = C.CANOPY_TEXT_FRONT, C.CANOPY_TEXT_LEFT
    w = D["diffuser_inset"] - 0.003  # just in front of the recessed diffuser
    ob = B.text("Text_Canopy_Front", "coffee, ramen, implant", 0.30, ((tf["x0"] + tf["x1"]) / 2, CY0 + w, tf["z"]),
                (90, 0, 0), B.M["sign_text"], coll, font=B.EN_FONT)
    B.fit_text_width(ob, tf["x1"] - tf["x0"])
    ob = B.text("Text_Canopy_Left", "珈琲　拉麺　義体", 0.30, (CX0 + w, (tl["y0"] + tl["y1"]) / 2, tl["z"]),
                (90, 0, -90), B.M["sign_text"], coll, font=B.JP_FONT)
    B.fit_text_width(ob, tl["y0"] - tl["y1"])


def build_icons(mesh):
    tf, tl = C.CANOPY_TEXT_FRONT, C.CANOPY_TEXT_LEFT
    w = D["diffuser_inset"] - 0.004
    geo.cylinder(mesh, (tf["ring_x"], CY0 + w, tf["z"]), 0.065, 0.004, "Sign_Text_Black", axis="Y", segments=24)
    # ramen bowl: an upside-down dome + three steam strokes
    import bmesh
    from mathutils import Matrix
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.13)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 1e-4], context="VERTS")
    bmesh.ops.scale(bm, vec=(0.15, 1.0, 1.0), verts=bm.verts)
    mesh.add_bm(bm, "Sign_Text_Black", True, Matrix.Translation((CX0 + w, tl["bowl_y"], tl["z"] - 0.01)))
    for dy in (-0.05, 0.0, 0.05):
        geo.box(mesh, CX0 + w - 0.003, CX0 + w + 0.001, tl["bowl_y"] + dy - 0.008, tl["bowl_y"] + dy + 0.008,
                tl["z"] + 0.03, tl["z"] + 0.15, "Sign_Text_Black")


def corner_posts(mesh):
    """Heavy square posts that cap the four canopy corners, standing proud of both faces and
    running from below the edge beam to above the coping."""
    p, pp = F["post"], F["post_proud"]
    for sx, x in ((-1, CX0), (1, CX1)):
        for sy, y in ((-1, CY0), (1, CY1)):
            xa, ya = x + sx * pp, y + sy * pp  # outer faces
            geo.box(mesh, min(xa, xa - sx * p), max(xa, xa - sx * p), min(ya, ya - sy * p), max(ya, ya - sy * p),
                    FZ0 - 0.05, CT + 0.06, "Steel_Dark", 0.012, 2)
            # cap plate on top
            geo.box(mesh, min(xa, xa - sx * p) - 0.015, max(xa, xa - sx * p) + 0.015, min(ya, ya - sy * p) - 0.015,
                    max(ya, ya - sy * p) + 0.015, CT + 0.06, CT + 0.085, "Steel_Dark", 0.006, 2)


def build(coll, materials, B):
    geo.reseed(77)
    m = geo.Mesh("Canopy_Detail")
    pt = D["plate_t"]
    geo.box(m, CX0 + 0.02, CX1 - 0.02, CY0 + 0.02, CY1 - 0.02, CB + pt, CT - pt, "Steel_Dark")  # closes the volume
    geo.box(m, CX0, CX1, CY0, CY1, CB, CB + pt, "Steel_Dark", 0.004)  # soffit plate
    geo.box(m, CX0 + 0.02, CX1 - 0.02, CY0 + 0.02, CY1 - 0.02, CT - pt, CT, "Steel_Grey", 0.005, 2)  # deck plate
    for face in FACES.values():
        build_face(m, face)
    corner_posts(m)
    build_soffit(m)
    build_corner_sign(m, B, coll)
    build_icons(m)
    build_lettering(B, coll)
    return m.build(coll, materials)
