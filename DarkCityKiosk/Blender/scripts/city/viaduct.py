"""Elevated railway behind the kiosk: box girder on piers, running along +X into tower RightA.

Box girder with steel fascias and a cyan light strip, parapets with railings, slab track and
rails, catenary masts with a contact wire, lamps under the deck, concrete piers with pier caps,
and a tunnel portal on RightA's front face (dark opening + frame + light band), so the train
visibly runs into the building. Lamp and portal positions go into the manifest for Unreal.
"""
import city_config as CC
from kiosk import geo

V = CC.VIADUCT


def build(m, x1, manifest):
    x0, z = V["x0"], V["deck_z"]
    yc = (V["y0"] + V["y1"]) / 2
    hw = (V["y1"] - V["y0"]) / 2
    rail_top = z + 0.35
    # girder, deck slab (slight overhang), underside taper
    geo.box(m, x0, x1, yc - hw, yc + hw, z - 1.3, z - 0.2, "Viaduct_Concrete", 0.05)
    geo.box(m, x0, x1, yc - hw + 0.4, yc + hw - 0.4, z - 1.6, z - 1.3, "Viaduct_Concrete", 0.05)
    geo.box(m, x0, x1, yc - hw - 0.15, yc + hw + 0.15, z - 0.2, z, "Viaduct_Concrete", 0.03)
    for s in (-1, 1):
        y = yc + s * (hw + 0.15)
        # steel fascia with stiffeners and the light strip
        geo.box(m, x0, x1, min(y, y + s * 0.08), max(y, y + s * 0.08), z - 1.25, z - 0.05, "Viaduct_Steel")
        x = x0 + 1.0
        while x < x1:
            geo.box(m, x - 0.06, x + 0.06, min(y, y + s * 0.16), max(y, y + s * 0.16), z - 1.25, z - 0.05, "Viaduct_Steel")
            x += 2.0
        geo.box(m, x0, x1, min(y, y + s * 0.12), max(y, y + s * 0.12), z - 0.62, z - 0.56, "Viaduct_Strip")
        # parapet + railing
        yp = yc + s * (hw - 0.05)
        geo.box(m, x0, x1, yp - 0.08, yp + 0.08, z, z + 0.5, "Viaduct_Concrete", 0.02)
        x = x0 + 0.5
        while x < x1:
            geo.box(m, x - 0.03, x + 0.03, yp - 0.03, yp + 0.03, z + 0.5, z + 1.15, "Viaduct_Steel")
            x += 2.0
        geo.pipe(m, (x0, yp, z + 1.15), (x1, yp, z + 1.15), 0.035, "Viaduct_Steel", 8)
    # slab track and rails (standard gauge)
    for s in (-1, 1):
        yr = yc + s * 0.72
        geo.box(m, x0, x1, yr - 0.3, yr + 0.3, z, z + 0.2, "Viaduct_Concrete")
        geo.box(m, x0, x1, yr - 0.035, yr + 0.035, z + 0.2, rail_top, "Rail_Steel")
    # piers every 24 m back from the portal, each with a catenary mast and under-deck lamps
    manifest["viaduct_lamps"] = []
    manifest["viaduct_piers"] = []  # [x, y, half footing width, column top z] for the crowd paths
    x = x1 - 12.0
    while x > x0 + 2.0:
        manifest["viaduct_piers"].append([x, yc, 1.2, z - 2.3])
        geo.box(m, x - 1.2, x + 1.2, yc - 1.2, yc + 1.2, 0.0, 0.35, "Viaduct_Concrete", 0.05)  # footing
        geo.box(m, x - 0.7, x + 0.7, yc - 0.7, yc + 0.7, 0.35, z - 2.3, "Viaduct_Concrete", 0.08, 2)  # column
        geo.box(m, x - 0.95, x + 0.95, yc - hw - 0.4, yc + hw + 0.4, z - 2.4, z - 1.6, "Viaduct_Concrete", 0.08, 2)  # cap
        geo.pipe(m, (x + 0.75, yc - 0.3, 0.4), (x + 0.75, yc - 0.3, z - 2.4), 0.09, "Viaduct_Steel", 10)  # drain pipe
        geo.box(m, x + 0.7, x + 0.95, yc + 0.2, yc + 0.6, 2.0, 2.6, "Viaduct_Steel", 0.02)  # junction box
        ym = yc + hw + 0.05  # mast on the far side, cantilever over the track
        geo.box(m, x - 0.12, x + 0.12, ym - 0.12, ym + 0.12, z, z + 5.6, "Viaduct_Steel")
        geo.pipe(m, (x, ym, z + 5.0), (x, yc, z + 5.0), 0.05, "Viaduct_Steel", 8)
        x -= 24.0
    geo.pipe(m, (x0, yc, rail_top + 4.6), (x1, yc, rail_top + 4.6), 0.018, "Rail_Steel", 6)  # contact wire
    x = x0 + 6.0
    while x < x1 - 3:
        for s in (-1, 1):
            yl = yc + s * (hw - 0.3)
            geo.box(m, x - 0.25, x + 0.25, yl - 0.12, yl + 0.12, z - 1.75, z - 1.6, "Viaduct_Lamp")
            manifest["viaduct_lamps"].append([x, yl, z - 1.8])
        x += 12.0
    # tunnel portal on RightA: dark opening straddling the facade, frame, light band
    pw, ph = 5.4, 6.2
    pz0 = z - 1.7
    geo.box(m, x1 - 0.3, x1 + 0.4, yc - pw / 2, yc + pw / 2, pz0, pz0 + ph, "Portal_Dark")
    geo.box(m, x1 - 0.8, x1 + 0.1, yc - pw / 2 - 0.7, yc - pw / 2, pz0 - 0.3, pz0 + ph + 0.8, "Viaduct_Concrete", 0.05)
    geo.box(m, x1 - 0.8, x1 + 0.1, yc + pw / 2, yc + pw / 2 + 0.7, pz0 - 0.3, pz0 + ph + 0.8, "Viaduct_Concrete", 0.05)
    geo.box(m, x1 - 0.8, x1 + 0.1, yc - pw / 2 - 0.7, yc + pw / 2 + 0.7, pz0 + ph, pz0 + ph + 0.8, "Viaduct_Concrete", 0.05)
    geo.box(m, x1 - 0.85, x1 - 0.8, yc - pw / 2, yc + pw / 2, pz0 + ph + 0.25, pz0 + ph + 0.55, "Viaduct_Strip")
    manifest["railway"] = {"x0": x0, "x1": x1, "y": yc, "rail_top": rail_top, "portal_x": x1}
