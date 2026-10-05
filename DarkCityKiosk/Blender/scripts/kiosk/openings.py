"""Step 2: openings and what's behind them.

Service side (front wall, Y = Y0, outward = -Y): the service-window interior (tiled walls,
stainless worktop, shelves with stock, pots and a coffee machine, hanging ladles, menu
cards, overhead light), shutter guide rails, the outside counter on gussets with
condiments, the retro ticket machine, the backlit under-counter sign, the glazed steel
grid window (frosted glass, a few lit panes), window lightbox and vent grille.

Door side (left wall, X = X0, outward = -X): framed door leaf with rounded corners,
stiffeners, a wired-glass window, kick plate, lever handle, lock box, hinges and closer,
plus the simple wall boxes / decals / conduit (detailed in step 3).
"""
import math

import kiosk_config as C
from . import geo

Y0, X0, PH = C.Y0, C.X0, C.PLATFORM_H

# Materials introduced in this step: (rgb, roughness, metallic, emission strength)
MATERIALS = {
    "Interior_Tile": ((0.72, 0.68, 0.58), 0.25, 0.0, 0.0),
    "Interior_Steel": ((0.62, 0.62, 0.60), 0.3, 0.85, 0.0),
    "Stock_Red": ((0.55, 0.06, 0.04), 0.5, 0.0, 0.0),
    "Stock_White": ((0.80, 0.78, 0.72), 0.5, 0.0, 0.0),
    "Stock_Green": ((0.12, 0.35, 0.18), 0.5, 0.0, 0.0),
    "Stock_Yellow": ((0.85, 0.65, 0.12), 0.5, 0.0, 0.0),
    "Stock_Blue": ((0.12, 0.22, 0.45), 0.5, 0.0, 0.0),
    "Paper_White": ((0.82, 0.80, 0.74), 0.7, 0.0, 0.0),
    "Broth": ((0.35, 0.18, 0.06), 0.15, 0.0, 0.0),
    "Wood_Light": ((0.45, 0.30, 0.16), 0.6, 0.0, 0.0),
    "Rubber_Black": ((0.02, 0.02, 0.02), 0.8, 0.0, 0.0),
    "Glass_Frosted": ((0.16, 0.18, 0.17), 0.18, 0.0, 0.0),
    "Glass_Wired": ((0.10, 0.12, 0.12), 0.08, 0.0, 0.0),
    "Machine_Body": ((0.42, 0.40, 0.36), 0.45, 0.3, 0.0),
    "Button_Lit_Red": ((1.0, 0.12, 0.08), 0.4, 0.0, 4.0),
    "Button_Lit_Green": ((0.2, 1.0, 0.35), 0.4, 0.0, 4.0),
    "Button_Lit_Yellow": ((1.0, 0.8, 0.15), 0.4, 0.0, 4.0),
}


def ensure_materials(B):
    import bpy
    for name, (rgb, rough, metal, emit) in MATERIALS.items():
        m = B.mat(name, rgb, emit)
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return bpy.data.materials


# ---- Service side ---------------------------------------------------------------------

def service_interior(m):
    sw = C.SERVICE_WINDOW
    x0, x1, z0, z1 = sw["x0"], sw["x1"], sw["z0"], sw["z1"]
    back = Y0 + sw["depth"]
    # tiled lining on the three inner walls and ceiling (just inside the boolean recess)
    geo.box(m, x0 + 0.01, x1 - 0.01, back - 0.02, back - 0.01, z0, z1, "Interior_Tile")
    for xa, xb in ((x0, x0 + 0.01), (x1 - 0.01, x1)):
        geo.box(m, xa, xb, Y0 + 0.03, back - 0.01, z0, z1, "Interior_Tile")
    # tile grout lines on the back wall
    for k in range(1, 6):
        z = z0 + k * (z1 - z0) / 6
        geo.box(m, x0 + 0.01, x1 - 0.01, back - 0.024, back - 0.02, z - 0.002, z + 0.002, "Steel_Grey")
    # stainless worktop with a front lip (the sill)
    geo.box(m, x0 - 0.02, x1 + 0.02, Y0 - 0.01, back - 0.02, z0, z0 + 0.03, "Interior_Steel", 0.004)
    geo.box(m, x0 - 0.02, x1 + 0.02, Y0 - 0.02, Y0 + 0.01, z0 - 0.03, z0 + 0.035, "Interior_Steel", 0.004)
    # overhead light: housing + glowing panel facing down
    geo.box(m, x0 + 0.12, x1 - 0.12, Y0 + 0.22, Y0 + 0.42, z1 - 0.04, z1, "Steel_Grey", 0.005)
    geo.box(m, x0 + 0.15, x1 - 0.15, Y0 + 0.24, Y0 + 0.40, z1 - 0.045, z1 - 0.04, "Interior_Light")
    # two shelves on brackets against the back wall
    for zs in (z0 + 0.38, z0 + 0.62):
        geo.box(m, x0 + 0.04, x1 - 0.04, back - 0.27, back - 0.02, zs, zs + 0.018, "Interior_Steel", 0.003)
        for xb in (x0 + 0.12, (x0 + x1) / 2, x1 - 0.12):
            geo.box(m, xb - 0.008, xb + 0.008, back - 0.22, back - 0.02, zs - 0.07, zs, "Interior_Steel")
        # stock: jars, cans and boxes in seeded colours
        x = x0 + 0.08
        while x < x1 - 0.1:
            kind = geo.RNG.random()
            mat = geo.RNG.choice(["Stock_Red", "Stock_White", "Stock_Green", "Stock_Yellow", "Stock_Blue", "Stock_White"])
            yc = back - geo.RNG.uniform(0.09, 0.17)
            if kind < 0.55:
                r, h = geo.RNG.uniform(0.028, 0.045), geo.RNG.uniform(0.07, 0.15)
                geo.cylinder(m, (x + r, yc, zs + 0.018 + h / 2), r, h, mat, segments=12)
                geo.cylinder(m, (x + r, yc, zs + 0.018 + h + 0.006), r * 0.9, 0.012, "Steel_Grey", segments=12)
                x += 2 * r + geo.RNG.uniform(0.008, 0.03)
            else:
                w, d, h = geo.RNG.uniform(0.07, 0.14), geo.RNG.uniform(0.06, 0.12), geo.RNG.uniform(0.08, 0.18)
                geo.box(m, x, x + w, yc - d / 2, yc + d / 2, zs + 0.018, zs + 0.018 + h, mat, 0.004)
                x += w + geo.RNG.uniform(0.01, 0.03)
    # menu cards above the top shelf
    n = 5
    for k in range(n):
        cx = x0 + 0.15 + k * (x1 - x0 - 0.3) / (n - 1)
        geo.box(m, cx - 0.085, cx + 0.085, back - 0.03, back - 0.022, z0 + 0.69, z0 + 0.82,
                "Paper_White" if k % 2 == 0 else "Stock_Yellow")
    # ladle rail with hanging ladles under the top shelf
    zr = z0 + 0.55
    geo.pipe(m, (x0 + 0.1, back - 0.05, zr), (x1 - 0.1, back - 0.05, zr), 0.006, "Interior_Steel", 8)
    for k in range(5):
        cx = x0 + 0.25 + k * (x1 - x0) * 0.089
        geo.pipe(m, (cx, back - 0.05, zr), (cx, back - 0.055, zr - 0.2), 0.004, "Interior_Steel", 6)
        geo.cylinder(m, (cx, back - 0.055, zr - 0.22), 0.03, 0.03, "Interior_Steel", segments=10)
    # equipment on the worktop: coffee machine at the left end, the rest spread along the window
    wz = z0 + 0.03
    ux = lambda f: x0 + f * (x1 - x0)  # noqa: E731 (fraction of the way along the window)
    geo.box(m, x0 + 0.08, x0 + 0.38, back - 0.33, back - 0.03, wz, wz + 0.40, "Interior_Steel", 0.012, 2)  # coffee machine
    geo.box(m, x0 + 0.10, x0 + 0.36, back - 0.335, back - 0.32, wz + 0.22, wz + 0.36, "Rubber_Black", 0.004)
    for sx in (x0 + 0.17, x0 + 0.27):
        geo.cylinder(m, (sx, back - 0.36, wz + 0.17), 0.012, 0.05, "Steel_Grey", segments=8)
    bx = ux(0.467)
    geo.box(m, bx - 0.18, bx + 0.18, Y0 + 0.40, Y0 + 0.76, wz, wz + 0.07, "Rubber_Black", 0.008)  # burner
    geo.cylinder(m, (bx, Y0 + 0.58, wz + 0.07 + 0.14), 0.16, 0.28, "Interior_Steel", segments=24)  # ramen pot
    geo.cylinder(m, (bx, Y0 + 0.58, wz + 0.07 + 0.255), 0.148, 0.01, "Broth", segments=24)
    geo.cylinder(m, (ux(0.726), Y0 + 0.63, wz + 0.10), 0.12, 0.20, "Interior_Steel", segments=20)  # stock pot
    geo.cylinder(m, (ux(0.889), Y0 + 0.70, wz + 0.11), 0.09, 0.22, "Stock_White", segments=16)  # rice cooker


def shutter_rails(m):
    """Guide rails on the faces of the reveal lining (massing.py) and a top bar under its head."""
    sw, t = C.SERVICE_WINDOW, C.MASSING["service_reveal"]["t"]
    x0, x1, z1 = sw["x0"] + t, sw["x1"] - t, sw["z1"] - t
    for xa, xb in ((x0, x0 + 0.03), (x1 - 0.03, x1)):
        geo.box(m, xa, xb, Y0 - 0.005, Y0 + 0.05, sw["z0"], z1, "Steel_Grey", 0.003)
    geo.box(m, x0 + 0.02, x1 - 0.02, Y0 - 0.01, Y0 + 0.04, z1 - 0.045, z1, "Steel_Grey", 0.004)


def outside_counter(m):
    c = C.COUNTER
    y_front = Y0 - c["projection"]
    geo.box(m, c["x0"], c["x1"], y_front, Y0, c["z"] - c["thickness"], c["z"], "Steel_Galvanised", 0.004)
    geo.box(m, c["x0"], c["x1"], y_front - 0.004, y_front + 0.02, c["z"] - 0.07, c["z"], "Steel_Galvanised", 0.003)
    u = C.UNDER_COUNTER_SIGN
    for x in (c["x0"] + 0.2, u["x0"] - 0.12, u["x1"] + 0.12, c["x1"] - 0.2):  # gussets either side of the sign
        geo.box(m, x - 0.012, x + 0.012, Y0 - 0.03, Y0, c["z"] - 0.38, c["z"] - c["thickness"], "Steel_Dark", 0.003)
        geo.pipe(m, (x, Y0 - 0.02, c["z"] - 0.36), (x, y_front + 0.04, c["z"] - c["thickness"] - 0.005), 0.012, "Steel_Dark")
    lx, ly = c["x1"] - 0.1, y_front + 0.07  # support leg with foot plate
    geo.pipe(m, (lx, ly, PH), (lx, ly, c["z"] - c["thickness"]), 0.022, "Steel_Dark", 12)
    geo.box(m, lx - 0.06, lx + 0.06, ly - 0.06, ly + 0.06, PH, PH + 0.008, "Steel_Dark", 0.002)
    # condiments: sauce bottles, soy, shichimi shakers, napkin box, chopstick pot
    # (placed along the service window, so they spread with it)
    zt = c["z"]
    sw = C.SERVICE_WINDOW
    ux = lambda f: sw["x0"] + f * (sw["x1"] - sw["x0"])  # noqa: E731
    for x, r, h, mat in ((ux(0.40) - 0.06, 0.028, 0.17, "Stock_Red"), (ux(0.40), 0.028, 0.16, "Stock_Red"),
                         (ux(0.40) + 0.06, 0.03, 0.14, "Rubber_Black"), (ux(0.667) - 0.02, 0.018, 0.07, "Stock_Red"),
                         (ux(0.667) + 0.02, 0.018, 0.07, "Stock_Yellow"), (ux(0.963), 0.03, 0.14, "Rubber_Black")):
        geo.cylinder(m, (x, Y0 - 0.2, zt + h / 2), r, h, mat, segments=12)
        geo.cylinder(m, (x, Y0 - 0.2, zt + h + 0.012), r * 0.55, 0.024, "Stock_White", segments=10)
    nx, cx = ux(0.556), ux(0.815)  # napkin box, chopstick pot
    geo.box(m, nx - 0.05, nx + 0.05, Y0 - 0.26, Y0 - 0.16, zt, zt + 0.12, "Interior_Steel", 0.006)
    geo.cylinder(m, (cx, Y0 - 0.18, zt + 0.075), 0.04, 0.15, "Wood_Light", segments=14)
    for k in range(6):
        a = k * math.pi / 3
        geo.pipe(m, (cx + 0.018 * math.cos(a), Y0 - 0.18 + 0.018 * math.sin(a), zt + 0.1),
                 (cx + 0.022 * math.cos(a), Y0 - 0.18 + 0.022 * math.sin(a), zt + 0.26), 0.003, "Wood_Light", 5)


def ticket_machine(m):
    t = C.TICKET_MACHINE
    x0, x1, z0, z1 = t["x0"], t["x1"], t["z0"], t["z1"]
    yf = Y0 - t["depth"]
    geo.rounded_box(m, x0, x1, yf, Y0, z0, z1, "Machine_Body", "Y", 0.04, 4)
    geo.box(m, x0 - 0.01, x1 + 0.01, yf - 0.06, yf + 0.04, z1 - 0.02, z1 + 0.015, "Machine_Body", 0.008)  # hood
    geo.box(m, x0 + 0.04, x1 - 0.04, yf - 0.006, yf + 0.01, z1 - 0.29, z1 - 0.07, "Rubber_Black", 0.005)  # bezel
    geo.box(m, x0 + 0.06, x1 - 0.06, yf - 0.008, yf - 0.004, z1 - 0.27, z1 - 0.09, "Screen_Multi")
    mats = ["Button_Lit_Red", "Button_Lit_Green", "Button_Lit_Yellow"]
    for row in range(3):
        for col in range(4):
            bx = x0 + 0.055 + col * (x1 - x0 - 0.11) / 3
            bz = z1 - 0.34 - row * 0.05
            geo.box(m, bx - 0.017, bx + 0.017, yf - 0.012, yf, bz - 0.014, bz + 0.014, mats[(row + col) % 3], 0.003)
    geo.box(m, x1 - 0.09, x1 - 0.05, yf - 0.012, yf, z0 + 0.20, z0 + 0.26, "Rubber_Black", 0.003)  # coin slot
    geo.box(m, x0 + 0.06, x0 + 0.20, yf - 0.03, yf + 0.01, z0 + 0.05, z0 + 0.11, "Rubber_Black", 0.006)  # ticket tray


def under_counter_sign(m, B, coll):
    u = C.UNDER_COUNTER_SIGN
    geo.box(m, u["x0"] - 0.03, u["x1"] + 0.03, Y0 - 0.07, Y0, u["z0"] - 0.03, u["z1"] + 0.03, "Steel_Dark", 0.006, 2)
    geo.box(m, u["x0"], u["x1"], Y0 - 0.075, Y0 - 0.065, u["z0"], u["z1"], "Lightbox_White")
    ob = B.text("Text_UnderCounter", "HOT RAMEN\nCOLD BREW\nBETTER HUMANS", 0.085,
                ((u["x0"] + u["x1"]) / 2, Y0 - 0.077, (u["z0"] + u["z1"]) / 2), (90, 0, 0), B.M["sign_text"], coll)
    B.fit_text_width(ob, (u["x1"] - u["x0"]) * 0.82)


def glazed_window(m):
    g = C.GLAZED_WINDOW
    x0, x1, z0, z1 = g["x0"], g["x1"], g["z0"], g["z1"]
    fw = 0.045
    for (a0, a1, b0, b1) in ((x0 - fw, x1 + fw, z1, z1 + fw), (x0 - fw, x0, z0, z1), (x1, x1 + fw, z0, z1)):
        geo.box(m, a0, a1, Y0 - 0.035, Y0 + 0.01, b0, b1, "Steel_Dark", 0.005, 2)
    geo.box(m, x0 - fw - 0.03, x1 + fw + 0.03, Y0 - 0.08, Y0 + 0.01, z0 - 0.05, z0, "Steel_Grey", 0.008, 2)  # sill
    geo.box(m, x0, x1, Y0 + 0.05, Y0 + 0.06, z0, z1, "Glass_Frosted")
    pw, ph = (x1 - x0) / g["cols"], (z1 - z0) / g["rows"]
    for cx, rz in ((0, 3), (1, 3), (2, 2), (1, 1)):  # panes lit from behind
        geo.box(m, x0 + cx * pw + 0.02, x0 + (cx + 1) * pw - 0.02, Y0 + 0.048, Y0 + 0.05,
                z0 + rz * ph + 0.02, z0 + (rz + 1) * ph - 0.02, "Glass_Lit")
    for k in range(1, g["cols"]):
        x = x0 + k * pw
        geo.box(m, x - 0.015, x + 0.015, Y0 + 0.01, Y0 + 0.05, z0, z1, "Steel_Dark", 0.003)
    for k in range(1, g["rows"]):
        z = z0 + k * ph
        geo.box(m, x0, x1, Y0 + 0.01, Y0 + 0.05, z - 0.015, z + 0.015, "Steel_Dark", 0.003)


def window_lightbox(m, B, coll):
    w = C.WINDOW_LIGHTBOX
    geo.box(m, w["x0"], w["x1"], Y0 - w["depth"], Y0, w["z0"], w["z1"], "Steel_Dark", 0.01, 2)
    geo.box(m, w["x0"] + 0.03, w["x1"] - 0.03, Y0 - w["depth"] - 0.006, Y0 - w["depth"] + 0.002,
            w["z0"] + 0.03, w["z1"] - 0.03, "Lightbox_White")
    for xb in (w["x0"] + 0.15, w["x1"] - 0.15):  # wall brackets
        geo.box(m, xb - 0.015, xb + 0.015, Y0 - w["depth"], Y0, w["z1"], w["z1"] + 0.05, "Steel_Dark", 0.003)
    B.text("Text_WindowLightbox", "カフェ・ラーメン\nインプラント", min(0.15, (w["z1"] - w["z0"]) * 0.34),
           ((w["x0"] + w["x1"]) / 2, Y0 - w["depth"] - 0.009, (w["z0"] + w["z1"]) / 2), (90, 0, 0), B.M["sign_text"], coll,
           font=B.JP_FONT)


def vent_grille(m):
    """Louvred grille set into the face of the base frame (massing pass), below the glazed window."""
    v = C.VENT_GRILLE
    yf = Y0 - C.MASSING["base_proud"]
    z1 = min(v["z1"], PH + C.MASSING["base_h"] - C.MASSING["base_lip_h"] - 0.01)
    geo.box(m, v["x0"], v["x1"], yf - 0.02, yf + 0.01, v["z0"], z1, "Steel_Dark", 0.004)
    n = 6
    for k in range(n):
        z = v["z0"] + 0.025 + k * (z1 - v["z0"] - 0.05) / (n - 1)
        geo.box(m, v["x0"] + 0.02, v["x1"] - 0.02, yf - 0.03, yf - 0.02, z - 0.008, z + 0.008, "Steel_Grey", 0.002,
                rot=None)


def front_conduit(m):
    zc, yc = C.BODY_TOP - C.SHELL["topbeam_h"] - 0.05, Y0 - 0.035
    geo.pipe(m, (C.X0 + 0.2, yc, zc), (C.X1 - 0.2, yc, zc), 0.02, "Steel_Dark", 12)
    x = C.X0 + 0.4
    while x < C.X1 - 0.2:
        geo.box(m, x - 0.02, x + 0.02, yc - 0.028, Y0, zc - 0.028, zc + 0.028, "Steel_Grey", 0.003)
        x += 0.6


def build_service_side(coll, materials, B):
    geo.reseed(4242)
    m = geo.Mesh("ServiceSide_Detail")
    service_interior(m)
    shutter_rails(m)
    outside_counter(m)
    ticket_machine(m)
    under_counter_sign(m, B, coll)
    glazed_window(m)
    window_lightbox(m, B, coll)
    vent_grille(m)
    front_conduit(m)
    return m.build(coll, materials)


# ---- Door side -------------------------------------------------------------------------

def door(m):
    d = C.DOOR
    ya, yb = d["y"] - d["w"] / 2, d["y"] + d["w"] / 2
    top = PH + d["h"]
    jw, jt = 0.06, 0.04
    # frame: two jambs + head, flush with the battens
    for (a0, a1, b0, b1) in ((ya - jw, ya, PH, top + jw), (yb, yb + jw, PH, top + jw), (ya - jw, yb + jw, top, top + jw)):
        geo.box(m, X0 - jt, X0 + 0.02, a0, a1, b0, b1, "Kiosk_YellowPaint_Dark", 0.006, 2)
    geo.box(m, X0 - 0.01, X0 + 0.02, ya - 0.01, yb + 0.01, PH, PH + 0.02, "Steel_Dark", 0.003)  # threshold
    # leaf with rounded corners, slightly recessed in the frame
    lx0, lx1 = X0 - 0.018, X0 + 0.01
    geo.rounded_box(m, lx0, lx1, ya + 0.006, yb - 0.006, PH + 0.02, top - 0.006, "Kiosk_YellowPaint", "X", 0.07, 5)
    # raised border + two stiffeners
    inset = 0.07
    yi0, yi1, zi0, zi1 = ya + inset, yb - inset, PH + inset, top - inset
    for (a0, a1, b0, b1) in ((yi0, yi1, zi1 - 0.025, zi1), (yi0, yi1, zi0, zi0 + 0.025),
                             (yi0, yi0 + 0.025, zi0, zi1), (yi1 - 0.025, yi1, zi0, zi1)):
        geo.box(m, lx0 - 0.008, lx0, a0, a1, b0, b1, "Kiosk_YellowPaint_Dark", 0.003)
    for zs in (PH + 0.95, PH + 1.15):
        geo.box(m, lx0 - 0.008, lx0, yi0, yi1, zs - 0.02, zs + 0.02, "Kiosk_YellowPaint_Dark", 0.003)
    # wired-glass window: frame ring + glass + wire grid
    ww, wh, wz = d["window"]
    wy0, wy1, wz0, wz1 = d["y"] - ww / 2, d["y"] + ww / 2, wz, wz + wh
    geo.rounded_box(m, lx0 - 0.016, lx0, wy0 - 0.035, wy1 + 0.035, wz0 - 0.035, wz1 + 0.035, "Steel_Dark", "X", 0.03, 3)
    geo.box(m, lx0 - 0.018, lx0 - 0.016, wy0, wy1, wz0, wz1, "Glass_Wired")
    for k in range(1, 2):
        y = wy0 + k * (wy1 - wy0) / 2
        geo.box(m, lx0 - 0.02, lx0 - 0.017, y - 0.006, y + 0.006, wz0, wz1, "Steel_Dark")
    for k in range(1, 3):
        z = wz0 + k * (wz1 - wz0) / 3
        geo.box(m, lx0 - 0.02, lx0 - 0.017, wy0, wy1, z - 0.006, z + 0.006, "Steel_Dark")
    # kick plate with rivets
    ky0, ky1, kz0, kz1 = ya + 0.06, yb - 0.06, PH + 0.10, PH + 0.75
    geo.box(m, lx0 - 0.012, lx0 - 0.008, ky0, ky1, kz0, kz1, "Steel_Galvanised", 0.002)
    pts = [(lx0 - 0.012, y, z) for y in (ky0 + 0.025, ky1 - 0.025) for z in [kz0 + 0.025 + k * 0.1 for k in range(7)]]
    pts += [(lx0 - 0.012, ky0 + 0.025 + k * 0.1, z) for z in (kz0 + 0.025, kz1 - 0.025) for k in range(1, 7)]
    geo.rivets(m, pts, "-X", "Steel_Galvanised", 0.007)
    # lever handle + lock box on the corner side, hinges + closer on the back side
    hy, hz = ya + 0.08, PH + 1.0
    geo.cylinder(m, (lx0 - 0.02, hy, hz), 0.032, 0.02, "Steel_Grey", axis="X", segments=16)
    geo.box(m, lx0 - 0.07, lx0 - 0.045, hy - 0.012, hy + 0.13, hz - 0.012, hz + 0.012, "Steel_Grey", 0.006, 2)
    geo.pipe(m, (lx0 - 0.02, hy, hz), (lx0 - 0.058, hy, hz), 0.009, "Steel_Grey")
    geo.box(m, lx0 - 0.05, lx0, hy - 0.04, hy + 0.04, hz + 0.12, hz + 0.24, "Steel_Dark", 0.006, 2)
    geo.cylinder(m, (lx0 - 0.052, hy, hz + 0.18), 0.012, 0.006, "Steel_Grey", axis="X", segments=12)
    for hzz in (PH + 0.3, PH + 1.0, PH + 1.68):  # the strap hinges (construction.py) line up with these
        geo.cylinder(m, (X0 - 0.03, yb + 0.005, hzz), 0.018, 0.13, "Steel_Dark", segments=12)
    geo.box(m, lx0 - 0.06, lx0, yb - 0.32, yb - 0.04, top - 0.12, top - 0.05, "Steel_Dark", 0.008, 2)  # closer
    geo.pipe(m, (lx0 - 0.04, yb - 0.3, top - 0.085), (X0 - 0.045, yb + 0.03, top + 0.03), 0.008, "Steel_Dark")


def door_wall_items(m):
    """Horizontal conduit along the door wall (boxes, posters, stickers: clutter.py)."""
    zc = C.BODY_TOP - C.SHELL["topbeam_h"] - 0.05
    geo.pipe(m, (X0 - 0.035, C.Y0 + 0.2, zc), (X0 - 0.035, C.Y1 - 0.2, zc), 0.02, "Steel_Dark", 12)


def build_door_side(coll, materials, B):
    geo.reseed(5151)
    m = geo.Mesh("DoorSide_Detail")
    door(m)
    door_wall_items(m)
    return m.build(coll, materials)
