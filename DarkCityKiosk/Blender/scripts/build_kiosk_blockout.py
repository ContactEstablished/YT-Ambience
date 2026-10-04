"""Builds the grey-box kiosk from kiosk_config.py, saves Blender/kiosk_blockout.blend
and (with --render) renders the reference-camera view plus three orbit views.

    blender -b --factory-startup -P build_kiosk_blockout.py -- [--render]

Everything is rebuilt from scratch on each run: edit kiosk_config.py, not the .blend.
"""

import math
import os
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kiosk_config as C  # noqa: E402

BLENDER_DIR = os.path.dirname(HERE)
PROJECT_DIR = os.path.dirname(BLENDER_DIR)
RENDERS = os.path.join(BLENDER_DIR, "renders")
REFERENCE = os.path.join(PROJECT_DIR, "_reference", "PrimaryReference.png")

ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
DO_RENDER = "--render" in ARGV


# ---- Scene helpers ----------------------------------------------------------

def reset_scene():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    for datablocks in (bpy.data.collections, bpy.data.meshes, bpy.data.materials,
                       bpy.data.curves, bpy.data.cameras, bpy.data.lights, bpy.data.images):
        for block in list(datablocks):
            datablocks.remove(block)


def collection(name, parent=None):
    coll = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(coll)
    return coll


_MATS = {}


def mat(name, rgb, emit=0.0):
    """Flat colour for Workbench (diffuse_color) plus a Principled setup for EEVEE/Cycles."""
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1.0)
    if m.node_tree is None:  # Blender 5 materials come with nodes; older ones need use_nodes
        m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF") if m.node_tree else None
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*rgb, 1.0)
        if emit > 0:
            bsdf.inputs["Emission Color"].default_value = (*rgb, 1.0)
            bsdf.inputs["Emission Strength"].default_value = emit
    _MATS[name] = m
    return m


def _mesh_object(name, bm, material, coll):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def box(name, x0, x1, y0, y1, z0, z1, material, coll):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = min(x0, x1) if v.co.x < 0 else max(x0, x1)
        v.co.y = min(y0, y1) if v.co.y < 0 else max(y0, y1)
        v.co.z = min(z0, z1) if v.co.z < 0 else max(z0, z1)
    return _mesh_object(name, bm, material, coll)


def cylinder(name, center, radius, depth, material, coll, axis="Z", segments=24):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=segments,
                          radius1=radius, radius2=radius, depth=depth)
    if axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "Y"))
    elif axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(math.radians(90), 3, "X"))
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(center))
    return _mesh_object(name, bm, material, coll)


def dome(name, center, radius, material, coll, squash=0.5):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=radius)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context="VERTS")
    bmesh.ops.scale(bm, vec=(1, 1, squash), verts=bm.verts)
    bmesh.ops.translate(bm, verts=bm.verts, vec=Vector(center))
    return _mesh_object(name, bm, material, coll)


def text(name, body, size, loc, rot_deg, material, coll, font=None):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    if font:
        cu.font = font
    cu.materials.append(material)
    ob = bpy.data.objects.new(name, cu)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot_deg]
    coll.objects.link(ob)
    return ob


def fit_text_width(ob, width):
    """Scale a text object's font size so its laid-out width equals `width` metres."""
    bpy.context.view_layer.update()
    if ob.dimensions.x > 1e-6:
        ob.data.size *= width / ob.dimensions.x


def load_font(paths):
    for p in paths:
        if os.path.exists(p):
            try:
                return bpy.data.fonts.load(p)
            except RuntimeError as e:
                print(f"font {p} failed: {e}")
    return None


def boolean_cut(target, cutter, name):
    cutter.hide_render = True
    cutter.display_type = "WIRE"
    mod = target.modifiers.new(name, "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cutter
    mod.solver = "EXACT"
    try:
        mod.material_mode = "TRANSFER"
    except AttributeError:
        pass
    return mod


# ---- Palette ----------------------------------------------------------------
def make_palette():
    return {
        "ground": mat("Ground_Wet", (0.035, 0.035, 0.04)),
        "concrete": mat("Platform_Concrete", (0.16, 0.155, 0.15)),
        "paint": mat("Kiosk_YellowPaint", (0.62, 0.42, 0.08)),
        "paint_dark": mat("Kiosk_YellowPaint_Dark", (0.45, 0.30, 0.06)),
        "steel": mat("Steel_Dark", (0.09, 0.09, 0.095)),
        "steel_mid": mat("Steel_Grey", (0.28, 0.28, 0.27)),
        "galv": mat("Steel_Galvanised", (0.40, 0.40, 0.38)),
        "rust": mat("Rust_Red", (0.35, 0.10, 0.05)),
        "lightbox": mat("Lightbox_Yellow", (1.0, 0.82, 0.18), emit=6.0),
        "lightbox_white": mat("Lightbox_White", (0.95, 0.93, 0.85), emit=4.0),
        "sign_text": mat("Sign_Text_Black", (0.02, 0.02, 0.02)),
        "sign_text_red": mat("Sign_Text_Red", (0.6, 0.05, 0.03)),
        "tube": mat("Tube_WarmWhite", (1.0, 0.92, 0.75), emit=12.0),
        "interior": mat("Interior_Warm", (0.75, 0.62, 0.42), emit=0.6),
        "interior_light": mat("Interior_Light", (1.0, 0.85, 0.6), emit=8.0),
        "glass": mat("Glass_Dirty", (0.10, 0.12, 0.11)),
        "glass_lit": mat("Glass_Lit", (0.55, 0.45, 0.28), emit=1.5),
        "lantern": mat("Lantern_Paper", (1.0, 0.80, 0.45), emit=5.0),
        "screen": mat("Screen_Multi", (0.3, 0.7, 0.8), emit=3.0),
        "poster": mat("Poster_Colour", (0.75, 0.55, 0.50)),
        "logo": mat("Logo_Stencil", (0.08, 0.06, 0.03)),
        "wood": mat("Wood_Crate", (0.22, 0.14, 0.08)),
        "red_plastic": mat("Plastic_Red", (0.55, 0.06, 0.05)),
        "green_bin": mat("Bin_Green", (0.10, 0.22, 0.16)),
        "cutter": mat("Interior_Recess", (0.30, 0.26, 0.20)),
    }


# ---- Build ------------------------------------------------------------------

def build_ground(coll):
    box("Ground", -40, 40, -40, 40, -0.02, 0.0, M["ground"], coll)
    m = C.PLATFORM_MARGIN
    box("Platform", C.X0 - m, C.X1 + m, C.Y0 - m, C.Y1 + m, 0.0, C.PLATFORM_H, M["concrete"], coll)


def seams_along(axis, fixed, lo, hi, openings, coll, prefix):
    """Vertical seam strips on one wall. `axis` is the axis the wall runs along;
    `fixed` the wall's coordinate on the other axis (strips stick out 12 mm)."""
    z0, z1 = C.PLATFORM_H, C.BODY_TOP
    n = 1
    s = lo + C.SEAM_SPACING
    while s < hi - 0.25:
        spans = [(z0, z1)]
        for (a0, a1, oz0, oz1) in openings:
            if a0 - 0.04 <= s <= a1 + 0.04:
                spans = [(z0, oz0), (oz1, z1)]
        for i, (sz0, sz1) in enumerate(spans):
            if sz1 - sz0 < 0.05:
                continue
            h = C.SEAM_W / 2
            if axis == "X":
                out = -0.012 if fixed < 0 else 0.012
                box(f"{prefix}_{n}_{i}", s - h, s + h, fixed, fixed + out, sz0, sz1, M["paint_dark"], coll)
            else:
                out = -0.012 if fixed < 0 else 0.012
                box(f"{prefix}_{n}_{i}", fixed, fixed + out, s - h, s + h, sz0, sz1, M["paint_dark"], coll)
        n += 1
        s += C.SEAM_SPACING


def build_body(coll, cutters):
    ph, top = C.PLATFORM_H, C.BODY_TOP
    body = box("Body", C.X0, C.X1, C.Y0, C.Y1, ph, top, M["paint"], coll)

    # Corner posts
    cp = C.CORNER_POST / 2
    for nm, x, y in (("FL", C.X0, C.Y0), ("FR", C.X1, C.Y0), ("BL", C.X0, C.Y1), ("BR", C.X1, C.Y1)):
        box(f"CornerPost_{nm}", x - cp, x + cp, y - cp, y + cp, ph, top, M["paint_dark"], coll)

    # Openings cut into the body (real depth: the orbit looks into them)
    sw = C.SERVICE_WINDOW
    cut = box("Cutter_ServiceWindow", sw["x0"], sw["x1"], C.Y0 - 0.05, C.Y0 + sw["depth"], sw["z0"], sw["z1"], M["cutter"], cutters)
    boolean_cut(body, cut, "Cut_ServiceWindow")
    gw = C.GLAZED_WINDOW
    cut = box("Cutter_GlazedWindow", gw["x0"], gw["x1"], C.Y0 - 0.05, C.Y0 + 0.08, gw["z0"], gw["z1"], M["cutter"], cutters)
    boolean_cut(body, cut, "Cut_GlazedWindow")

    # Seams (skipping openings)
    front_openings = [(sw["x0"], sw["x1"], sw["z0"], sw["z1"]), (gw["x0"], gw["x1"], gw["z0"], gw["z1"])]
    seams_along("X", C.Y0, C.X0, C.X1, front_openings, coll, "Seam_Front")
    seams_along("X", C.Y1, C.X0, C.X1, [], coll, "Seam_Back")
    d = C.DOOR
    door_opening = [(d["y"] - d["w"] / 2, d["y"] + d["w"] / 2, ph, ph + d["h"])]
    seams_along("Y", C.X0, C.Y0, C.Y1, door_opening, coll, "Seam_Left")
    seams_along("Y", C.X1, C.Y0, C.Y1, [], coll, "Seam_Right")
    return body


def build_service_side(coll):
    y0 = C.Y0
    sw = C.SERVICE_WINDOW
    # Interior inside the recess: shelves, back counter stock, a pot, an overhead light
    back = y0 + sw["depth"]
    for i, z in enumerate((sw["z0"] + 0.35, sw["z0"] + 0.62)):
        box(f"Interior_Shelf_{i}", sw["x0"] + 0.05, sw["x1"] - 0.05, back - 0.30, back - 0.01, z, z + 0.025, M["galv"], coll)
    for i, (x, w, h) in enumerate(((-1.35, 0.18, 0.22), (-1.10, 0.14, 0.18), (-0.55, 0.20, 0.26), (-0.32, 0.12, 0.16))):
        box(f"Interior_Stock_{i}", x - w / 2, x + w / 2, back - 0.25, back - 0.08, sw["z0"] + 0.385, sw["z0"] + 0.385 + h, M["steel_mid"], coll)
    cylinder("Interior_RamenPot", (-0.85, back - 0.40, sw["z0"] + 0.15), 0.16, 0.30, M["galv"], coll)
    box("Interior_Light", sw["x0"] + 0.15, sw["x1"] - 0.15, y0 + 0.25, y0 + 0.45, sw["z1"] - 0.03, sw["z1"] - 0.01, M["interior_light"], coll)

    # Counter shelf + brackets + support pipe
    c = C.COUNTER
    box("Counter", c["x0"], c["x1"], y0 - c["projection"], y0, c["z"] - c["thickness"], c["z"], M["steel_mid"], coll)
    for i, x in enumerate((c["x0"] + 0.25, c["x1"] - 0.25)):
        box(f"Counter_Bracket_{i}", x - 0.025, x + 0.025, y0 - c["projection"] + 0.06, y0, c["z"] - 0.32, c["z"] - c["thickness"], M["steel"], coll)
    cylinder("Counter_SupportPipe", (c["x1"] - 0.12, y0 - c["projection"] + 0.08, (C.PLATFORM_H + c["z"]) / 2), 0.03, c["z"] - C.PLATFORM_H, M["steel"], coll)
    for i, (x, h, m) in enumerate(((-0.95, 0.18, "red_plastic"), (-0.88, 0.16, "rust"), (-0.80, 0.20, "red_plastic"), (-0.50, 0.12, "galv"))):
        cylinder(f"Counter_Bottle_{i}", (x, y0 - 0.20, c["z"] + h / 2), 0.03, h, M[m], coll)

    # Ticket machine
    t = C.TICKET_MACHINE
    box("TicketMachine", t["x0"], t["x1"], y0 - t["depth"], y0, t["z0"], t["z1"], M["steel_mid"], coll)
    box("TicketMachine_Screen", t["x0"] + 0.06, t["x1"] - 0.06, y0 - t["depth"] - 0.01, y0 - t["depth"], t["z1"] - 0.30, t["z1"] - 0.08, M["screen"], coll)

    # Under-counter sign
    u = C.UNDER_COUNTER_SIGN
    box("UnderCounterSign", u["x0"], u["x1"], y0 - 0.05, y0, u["z0"], u["z1"], M["lightbox_white"], coll)
    text("Text_UnderCounter", "HOT RAMEN\nCOLD BREW\nBETTER HUMANS", 0.085,
         ((u["x0"] + u["x1"]) / 2, y0 - 0.052, (u["z0"] + u["z1"]) / 2), (90, 0, 0), M["sign_text"], coll)

    # Glazed window: glass at the back of a shallow recess + steel grid
    g = C.GLAZED_WINDOW
    box("GlazedWindow_Glass", g["x0"], g["x1"], y0 + 0.06, y0 + 0.08, g["z0"], g["z1"], M["glass"], coll)
    for i in range(1, g["cols"]):
        x = g["x0"] + (g["x1"] - g["x0"]) * i / g["cols"]
        box(f"GlazedWindow_Mullion_{i}", x - 0.015, x + 0.015, y0 + 0.02, y0 + 0.06, g["z0"], g["z1"], M["steel"], coll)
    for i in range(1, g["rows"]):
        z = g["z0"] + (g["z1"] - g["z0"]) * i / g["rows"]
        box(f"GlazedWindow_Transom_{i}", g["x0"], g["x1"], y0 + 0.02, y0 + 0.06, z - 0.015, z + 0.015, M["steel"], coll)
    # a few panes lit from behind
    pw, phh = (g["x1"] - g["x0"]) / g["cols"], (g["z1"] - g["z0"]) / g["rows"]
    for i, (cx, rz) in enumerate(((0, 3), (1, 3), (2, 2))):
        box(f"GlazedWindow_LitPane_{i}", g["x0"] + cx * pw + 0.02, g["x0"] + (cx + 1) * pw - 0.02, y0 + 0.058, y0 + 0.06,
            g["z0"] + rz * phh + 0.02, g["z0"] + (rz + 1) * phh - 0.02, M["glass_lit"], coll)
    fr = 0.035
    box("GlazedWindow_Frame_T", g["x0"] - fr, g["x1"] + fr, y0 - 0.03, y0, g["z1"], g["z1"] + fr, M["steel"], coll)
    box("GlazedWindow_Frame_B", g["x0"] - fr, g["x1"] + fr, y0 - 0.03, y0, g["z0"] - fr, g["z0"], M["steel"], coll)
    box("GlazedWindow_Frame_L", g["x0"] - fr, g["x0"], y0 - 0.03, y0, g["z0"], g["z1"], M["steel"], coll)
    box("GlazedWindow_Frame_R", g["x1"], g["x1"] + fr, y0 - 0.03, y0, g["z0"], g["z1"], M["steel"], coll)

    # Window lightbox
    w = C.WINDOW_LIGHTBOX
    box("WindowLightbox", w["x0"], w["x1"], y0 - w["depth"], y0, w["z0"], w["z1"], M["steel"], coll)
    box("WindowLightbox_Face", w["x0"] + 0.03, w["x1"] - 0.03, y0 - w["depth"] - 0.005, y0 - w["depth"], w["z0"] + 0.03, w["z1"] - 0.03, M["lightbox_white"], coll)
    text("Text_WindowLightbox", "カフェ・ラーメン\nインプラント", 0.15,
         ((w["x0"] + w["x1"]) / 2, y0 - w["depth"] - 0.008, (w["z0"] + w["z1"]) / 2), (90, 0, 0), M["sign_text"], coll, font=JP_FONT)

    v = C.VENT_GRILLE
    box("VentGrille", v["x0"], v["x1"], y0 - 0.015, y0, v["z0"], v["z1"], M["steel"], coll)
    for name, a0, a1, z0, z1 in C.FRONT_WALL_DECALS:
        box(f"Decal_{name}", a0, a1, y0 - 0.006, y0, z0, z1, M["poster"], coll)

    # Conduit under the canopy
    cylinder("Conduit_Front", ((C.X0 + C.X1) / 2, y0 - 0.06, 2.30), 0.025, C.BODY_W - 0.3, M["steel"], coll, axis="X")


def build_door_side(coll):
    x0, ph = C.X0, C.PLATFORM_H
    d = C.DOOR
    ya, yb = d["y"] - d["w"] / 2, d["y"] + d["w"] / 2
    box("Door_Frame", x0 - 0.02, x0, ya - 0.05, yb + 0.05, ph, ph + d["h"] + 0.05, M["steel"], coll)
    box("Door", x0 - 0.04, x0 - 0.02, ya, yb, ph, ph + d["h"], M["paint_dark"], coll)
    ww, wh, wz = d["window"]
    box("Door_Window", x0 - 0.045, x0 - 0.04, d["y"] - ww / 2, d["y"] + ww / 2, wz, wz + wh, M["glass"], coll)
    box("Door_KickPlate", x0 - 0.045, x0 - 0.04, ya + 0.06, yb - 0.06, ph + 0.12, ph + 0.85, M["galv"], coll)
    box("Door_Handle", x0 - 0.09, x0 - 0.04, ya + 0.06, ya + 0.10, ph + 1.00, ph + 1.15, M["steel"], coll)
    for name, a0, a1, z0, z1, depth in C.LEFT_WALL_BOXES:
        box(f"WallBox_{name}", x0 - depth, x0, a0, a1, z0, z1, M["steel_mid"], coll)
        cylinder(f"WallBox_{name}_Conduit", (x0 - 0.04, (a0 + a1) / 2, (z1 + C.BODY_TOP) / 2), 0.02, C.BODY_TOP - z1, M["steel"], coll)
    for name, a0, a1, z0, z1 in C.LEFT_WALL_DECALS:
        box(f"Decal_{name}", x0 - 0.006, x0, a0, a1, z0, z1, M["logo"] if "Logo" in name else M["poster"], coll)
    cylinder("Conduit_Left", (x0 - 0.06, (C.Y0 + C.Y1) / 2, 2.25), 0.025, C.BODY_D - 0.3, M["steel"], coll, axis="Y")


def build_canopy(coll):
    cx0, cx1, cy0, cy1 = C.CANOPY_X0, C.CANOPY_X1, C.CANOPY_Y0, C.CANOPY_Y1
    cb, ct, f = C.CANOPY_BOTTOM, C.CANOPY_TOP, C.LIGHTBOX_FRAME
    box("Canopy", cx0, cx1, cy0, cy1, cb, ct, M["steel"], coll)
    box("Canopy_Face_Front", cx0 + f, cx1 - f, cy0 - 0.02, cy0, cb + f * 0.75, ct - f * 0.75, M["lightbox"], coll)
    box("Canopy_Face_Left", cx0 - 0.02, cx0, cy0 + f, cy1 - f, cb + f * 0.75, ct - f * 0.75, M["lightbox"], coll)
    mid_z = (cb + ct) / 2
    tf, tl = C.CANOPY_TEXT_FRONT, C.CANOPY_TEXT_LEFT
    ob = text("Text_Canopy_Front", "coffee, ramen, implant", 0.30, ((tf["x0"] + tf["x1"]) / 2, cy0 - 0.025, tf["z"]), (90, 0, 0), M["sign_text"], coll, font=EN_FONT)
    fit_text_width(ob, tf["x1"] - tf["x0"])
    ring = cylinder("Canopy_RingMark", (tf["ring_x"], cy0 - 0.025, tf["z"]), 0.07, 0.01, M["sign_text"], coll, axis="Y")
    ob = text("Text_Canopy_Left", "珈琲　拉麺　義体", 0.30, (cx0 - 0.025, (tl["y0"] + tl["y1"]) / 2, tl["z"]), (90, 0, -90), M["sign_text"], coll, font=JP_FONT)
    fit_text_width(ob, tl["y0"] - tl["y1"])
    # Ramen-bowl icon: a half-disc bowl with three steam strokes
    dome("Canopy_BowlIcon", (cx0 - 0.03, tl["bowl_y"], mid_z - 0.02), 0.13, M["sign_text"], coll, squash=-1.0)  # negative squash = upside-down dome (a bowl)
    for i, dy in enumerate((-0.05, 0.0, 0.05)):
        box(f"Canopy_BowlSteam_{i}", cx0 - 0.03, cx0 - 0.025, tl["bowl_y"] + dy - 0.008, tl["bowl_y"] + dy + 0.008, mid_z + 0.03, mid_z + 0.15, M["sign_text"], coll)

    # Soffit tube fixtures
    for i, (axis, fixed, a, b) in enumerate(C.SOFFIT_TUBES):
        mid, length = (a + b) / 2, b - a
        if axis == "X":
            box(f"Soffit_Fixture_{i}", a, b, fixed - 0.05, fixed + 0.05, cb - 0.04, cb, M["steel_mid"], coll)
            cylinder(f"Soffit_Tube_{i}", (mid, fixed, cb - 0.06), 0.02, length - 0.06, M["tube"], coll, axis="X")
        else:
            box(f"Soffit_Fixture_{i}", fixed - 0.05, fixed + 0.05, a, b, cb - 0.04, cb, M["steel_mid"], coll)
            cylinder(f"Soffit_Tube_{i}", (fixed, mid, cb - 0.06), 0.02, length - 0.06, M["tube"], coll, axis="Y")

    # Corner vertical sign + bracket
    s = C.CORNER_SIGN
    box("CornerSign", s["x"] - s["w"] / 2, s["x"] + s["w"] / 2, s["y"] - s["d"] / 2, s["y"] + s["d"] / 2, s["z0"], s["z1"], M["steel"], coll)
    box("CornerSign_FaceFront", s["x"] - s["w"] / 2 + 0.03, s["x"] + s["w"] / 2 - 0.03, s["y"] - s["d"] / 2 - 0.01, s["y"] - s["d"] / 2,
        s["z0"] + 0.03, s["z1"] - 0.03, M["lightbox"], coll)
    box("CornerSign_FaceLeft", s["x"] - s["w"] / 2 - 0.01, s["x"] - s["w"] / 2, s["y"] - s["d"] / 2 + 0.02, s["y"] + s["d"] / 2 - 0.02,
        s["z0"] + 0.03, s["z1"] - 0.03, M["lightbox"], coll)
    text("Text_CornerSign", "コ\nー\nヒ\nー", 0.13, (s["x"], s["y"] - s["d"] / 2 - 0.012, (s["z0"] + s["z1"]) / 2 + 0.05), (90, 0, 0), M["sign_text_red"], coll, font=JP_FONT)
    box("CornerSign_Bracket", C.CANOPY_X1 - 0.10, s["x"] - s["w"] / 2, s["y"] - 0.03, s["y"] + 0.03, s["z1"] - 0.25, s["z1"] - 0.15, M["steel"], coll)


def build_roof(coll):
    deck = C.CANOPY_TOP
    for name, cx, cy, w, d, h in C.ROOF_BOXES:
        m = M["galv"] if name in ("WhiteBox",) else M["steel_mid"]
        box(f"Roof_{name}", cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, deck, deck + h, m, coll)
        if name in ("TallCabinet", "SmallUnit", "BackBox_A"):
            box(f"Roof_{name}_Lid", cx - w / 2 - 0.02, cx + w / 2 + 0.02, cy - d / 2 - 0.02, cy + d / 2 + 0.02, deck + h, deck + h + 0.05, M["rust"], coll)
    ac = next(b for b in C.ROOF_BOXES if b[0] == "ACCondenser")
    cylinder("Roof_ACCondenser_Fan", (ac[1] - ac[3] / 2 - 0.01, ac[2], deck + ac[5] / 2), 0.30, 0.02, M["steel"], coll, axis="X")
    tc = next(b for b in C.ROOF_BOXES if b[0] == "TallCabinet")
    cylinder("Roof_TallCabinet_Porthole", (tc[1] - 0.1, tc[2] - tc[4] / 2 - 0.01, deck + tc[5] * 0.72), 0.12, 0.02, M["steel"], coll, axis="Y")
    for name, cx, cy, r, h in C.ROOF_TANKS:
        cylinder(f"Roof_{name}", (cx, cy, deck + h / 2), r, h, M["galv"], coll)
        dome(f"Roof_{name}_Dome", (cx, cy, deck + h), r, M["galv"], coll)
    rl = C.CABLE_REEL
    cylinder("Roof_CableReel", (rl["cx"], rl["cy"], deck + rl["radius"]), rl["radius"] * 0.92, rl["width"] - 0.06, M["steel"], coll, axis="Y")
    for i, dy in enumerate((-rl["width"] / 2 + 0.02, rl["width"] / 2 - 0.02)):
        cylinder(f"Roof_CableReel_Flange_{i}", (rl["cx"], rl["cy"] + dy, deck + rl["radius"]), rl["radius"], 0.03, M["steel_mid"], coll, axis="Y")
    mt = C.MAST
    box("Roof_Mast", mt["cx"] - mt["w"] / 2, mt["cx"] + mt["w"] / 2, mt["cy"] - mt["w"] / 2, mt["cy"] + mt["w"] / 2, deck, deck + mt["h"], M["steel"], coll)
    for i, (z, span) in enumerate(((0.95, 0.50), (1.25, 0.40), (1.50, 0.30))):
        box(f"Roof_Mast_Bar_{i}", mt["cx"] - span / 2, mt["cx"] + span / 2, mt["cy"] - 0.02, mt["cy"] + 0.02, deck + z, deck + z + 0.03, M["steel"], coll)
    cylinder("Roof_Pipe", (-0.95, -0.95, deck + 0.30), 0.06, 1.3, M["galv"], coll, axis="X")


def build_props(coll):
    ph = C.PLATFORM_H
    # Left lantern on its pedestal
    ll = C.LANTERN_L
    z = ph
    for i, (s, h) in enumerate(C.LANTERN_L_PEDESTAL):
        box(f"LanternL_Pedestal_{i}", ll["x"] - s / 2, ll["x"] + s / 2, ll["y"] - s / 2, ll["y"] + s / 2, z, z + h, M["rust"] if i % 2 else M["wood"], coll)
        z += h
    bottom = ll["z"] - ll["h"] / 2
    cylinder("LanternL_Post", (ll["x"], ll["y"], (z + bottom) / 2), 0.025, bottom - z, M["steel"], coll)
    cylinder("LanternL", (ll["x"], ll["y"], ll["z"]), ll["radius"], ll["h"] - 0.08, M["lantern"], coll)
    for i, zz in enumerate((bottom + 0.02, ll["z"] + ll["h"] / 2 - 0.02)):
        cylinder(f"LanternL_Cap_{i}", (ll["x"], ll["y"], zz), ll["radius"] * 0.75, 0.04, M["steel"], coll)

    lr = C.LANTERN_R
    bottom = lr["z"] - lr["h"] / 2
    cylinder("LanternR_Post", (lr["x"] + 0.10, lr["y"], (ph + lr["z"] + lr["h"] / 2 + 0.15) / 2), 0.025, lr["z"] + lr["h"] / 2 + 0.15 - ph, M["steel"], coll)
    box("LanternR_Arm", lr["x"], lr["x"] + 0.10, lr["y"] - 0.015, lr["y"] + 0.015, lr["z"] + lr["h"] / 2 + 0.08, lr["z"] + lr["h"] / 2 + 0.11, M["steel"], coll)
    cylinder("LanternR", (lr["x"], lr["y"], lr["z"]), lr["radius"], lr["h"] - 0.07, M["lantern"], coll)
    for i, zz in enumerate((bottom + 0.02, lr["z"] + lr["h"] / 2 - 0.02)):
        cylinder(f"LanternR_Cap_{i}", (lr["x"], lr["y"], zz), lr["radius"] * 0.75, 0.04, M["steel"], coll)

    for name, cx, cy, w, d, h in C.GROUND_BOXES:
        m = M["red_plastic"] if "Red" in name else (M["steel_mid"] if "Cabinet" in name else M["wood"])
        box(name, cx - w / 2, cx + w / 2, cy - d / 2, cy + d / 2, ph, ph + h, m, coll)
    for name, cx, cy, r, h in C.BINS:
        cylinder(name, (cx, cy, ph + h / 2), r, h, M["green_bin"] if "Green" in name else M["steel_mid"], coll)
    for i, (sx, sy) in enumerate(C.STOOLS):
        cylinder(f"Stool_{i}_Seat", (sx, sy, ph + 0.72), 0.18, 0.06, M["red_plastic"], coll)
        for k in range(4):
            a = math.radians(45 + 90 * k)
            cylinder(f"Stool_{i}_Leg_{k}", (sx + 0.12 * math.cos(a), sy + 0.12 * math.sin(a), ph + 0.345), 0.015, 0.69, M["steel"], coll)
    rail = C.RAILING
    y = rail["y0"]
    i = 0
    while y <= rail["y1"] + 1e-6:
        cylinder(f"Railing_Post_{i}", (rail["x"], y, ph + rail["h"] / 2), 0.025, rail["h"], M["steel"], coll)
        y += 0.65
        i += 1
    cylinder("Railing_Top", (rail["x"], (rail["y0"] + rail["y1"]) / 2, ph + rail["h"]), 0.03, rail["y1"] - rail["y0"] + 0.1, M["steel"], coll, axis="Y")


# ---- Cameras ----------------------------------------------------------------

def make_camera(name, theta_deg, height, coll):
    hc = C.HERO_CAM
    px, py = C.ORBIT_PIVOT
    t = math.radians(theta_deg)
    dx, dy = hc["pos_xy"][0] - px, hc["pos_xy"][1] - py
    x = px + dx * math.cos(t) - dy * math.sin(t)
    y = py + dx * math.sin(t) + dy * math.cos(t)
    cam = bpy.data.cameras.new(name)
    cam.lens = hc["lens_mm"]
    cam.sensor_fit = "HORIZONTAL"
    cam.sensor_width = hc["sensor_w_mm"]
    cam.clip_start = 0.05
    cam.clip_end = 500
    ob = bpy.data.objects.new(name, cam)
    ob.location = (x, y, height)
    ob.rotation_euler = (math.radians(90 + hc["pitch_up_deg"]), 0.0, math.radians(hc["heading_deg"] + theta_deg - 90))
    coll.objects.link(ob)
    return ob


def setup_render(scene):
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    sh.show_cavity = True
    sh.cavity_type = "WORLD"
    sh.show_shadows = True
    sh.shadow_intensity = 0.4
    scene.view_settings.view_transform = "Standard"
    world = bpy.data.worlds.new("BlockoutWorld")
    world.color = (0.03, 0.04, 0.05)
    scene.world = world
    scene.render.image_settings.file_format = "PNG"


def render(scene, cam, path, res):
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"rendered {path}")


def init_shared():
    """Palette + fonts used by the build functions (also called by build_kiosk.py)."""
    global M, JP_FONT, EN_FONT
    M = make_palette()
    JP_FONT = load_font([r"C:\Windows\Fonts\YuGothB.ttc", r"C:\Windows\Fonts\meiryob.ttc", r"C:\Windows\Fonts\msgothic.ttc"])
    EN_FONT = load_font([r"C:\Windows\Fonts\seguisb.ttf", r"C:\Windows\Fonts\segoeui.ttf"])


# ---- Main -------------------------------------------------------------------
def main():

    reset_scene()
    init_shared()
    print(f"fonts: jp={JP_FONT and JP_FONT.filepath} en={EN_FONT and EN_FONT.filepath}")

    scene = bpy.context.scene
    kiosk = collection("Kiosk")
    cols = {n: collection(n, kiosk) for n in ("Ground", "Body", "ServiceSide", "DoorSide", "Canopy", "Roof", "Props")}
    cutters = collection("Cutters", kiosk)
    cutters.hide_render = True
    cams = collection("Cameras")

    build_ground(cols["Ground"])
    build_body(cols["Body"], cutters)
    build_service_side(cols["ServiceSide"])
    build_door_side(cols["DoorSide"])
    build_canopy(cols["Canopy"])
    build_roof(cols["Roof"])
    build_props(cols["Props"])

    hc = C.HERO_CAM
    cam_overlay = make_camera("CAM_Reference", 0.0, hc["height_overlay"], cams)
    cam_a = make_camera("CAM_Orbit_A", C.ORBIT_ARC_DEG[0], hc["height_video"], cams)
    cam_mid = make_camera("CAM_Orbit_Mid", 0.0, hc["height_video"], cams)
    cam_b = make_camera("CAM_Orbit_B", C.ORBIT_ARC_DEG[1], hc["height_video"], cams)

    # Reference image as a 50% camera background, for checking by eye in the .blend
    if os.path.exists(REFERENCE):
        img = bpy.data.images.load(REFERENCE)
        cam_overlay.data.show_background_images = True
        bg = cam_overlay.data.background_images.new()
        bg.image = img
        bg.alpha = 0.5
        bg.display_depth = "FRONT"

    setup_render(scene)
    scene.camera = cam_overlay
    scene.render.resolution_x, scene.render.resolution_y = 1672, 941

    os.makedirs(RENDERS, exist_ok=True)
    blend_path = os.path.join(BLENDER_DIR, "kiosk_blockout.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path, check_existing=False)
    print(f"saved {blend_path}")
    print(f"objects: {len(bpy.data.objects)}")

    if DO_RENDER:
        render(scene, cam_overlay, os.path.join(RENDERS, "blockout_reference_cam.png"), (1672, 941))
        for cam, tag in ((cam_a, "A"), (cam_mid, "Mid"), (cam_b, "B")):
            render(scene, cam, os.path.join(RENDERS, f"blockout_orbit_{tag}.png"), (1920, 1080))


if __name__ == "__main__":
    main()
