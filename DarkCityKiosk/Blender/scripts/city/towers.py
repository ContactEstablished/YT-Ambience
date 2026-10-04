"""Scripted towers for the city around the kiosk.

Each tower is built in its own local frame (origin at its footprint centre on the ground,
local +X pointing away from the kiosk, local +Y along its front face, front face at
local x = -depth/2 looking back at the kiosk), then placed by azimuth/distance.

Styles
  glass    podium, tall shaft with vertical fins, a setback crown, floor bands
  slab     podium, concrete shaft with floor ledges and clusters of AC units / balconies
  terraced podium and 3-4 stepped tiers with ledges at each step
All styles: shopfront band at street level, rooftop plant, optional antenna + red beacon.
Windows are not modelled: facades carry window materials and Unreal's window shader draws
the lit/unlit grid using the metre-scale UVs (floor height per style).
"""
import math
import random

from mathutils import Euler, Vector

import city_config as CC
from kiosk import geo

RNG = random.Random(CC.SEED)

WINDOW_MAT = {"glass": "City_Window_Glass", "slab": "City_Window_Slab", "terraced": "City_Window_Glass"}
SIGN_COLOURS = [(1.0, 0.25, 0.6), (0.3, 0.9, 1.0), (1.0, 0.7, 0.25), (0.6, 0.4, 1.0), (1.0, 0.2, 0.15), (0.4, 1.0, 0.6)]


class Placed:
    """A tower's frame: local (x, y, z) -> world, plus helpers that add rotated boxes."""

    def __init__(self, mesh, cx, cy, az_deg):
        self.m, self.c, self.az = mesh, Vector((cx, cy, 0.0)), math.radians(az_deg)
        self.rot = Euler((0.0, 0.0, self.az))
        ca, sa = math.cos(self.az), math.sin(self.az)
        self._R = ((ca, -sa), (sa, ca))

    def world(self, x, y, z):
        (a, b), (c, d) = self._R
        return Vector((self.c.x + a * x + b * y, self.c.y + c * x + d * y, z))

    def box(self, x0, x1, y0, y1, z0, z1, mat, bevel=0.0):
        cw = self.world((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2)
        sx, sy, sz = abs(x1 - x0), abs(y1 - y0), abs(z1 - z0)
        geo.box(self.m, cw.x - sx / 2, cw.x + sx / 2, cw.y - sy / 2, cw.y + sy / 2, cw.z - sz / 2, cw.z + sz / 2,
                mat, bevel, 1, self.rot)

    def cylinder(self, x, y, z, r, h, mat, segments=16):
        geo.cylinder(self.m, tuple(self.world(x, y, z)), r, h, mat, segments=segments)

    def normal(self, lx, ly):
        (a, b), (c, d) = self._R
        return (a * lx + b * ly, c * lx + d * ly, 0.0)


def ring_ledges(p, w, d, z, t, out, mat):
    """A thin ledge all round a w x d tier at height z (t thick, protruding `out`)."""
    p.box(-d / 2 - out, d / 2 + out, -w / 2 - out, w / 2 + out, z, z + t, mat)


def podium(p, w, d, manifest, name):
    ph = CC.PODIUM_H
    p.box(-d / 2 - 1.5, d / 2 + 1.5, -w / 2 - 1.5, w / 2 + 1.5, 0, ph, "City_Shop")
    p.box(-d / 2 - 2.6, d / 2 + 2.6, -w / 2 - 2.6, w / 2 + 2.6, ph, ph + 0.5, "City_Facade")  # canopy slab
    # glowing sign bands above the shopfronts on the front and sides
    col = RNG.choice(SIGN_COLOURS)
    mat = f"City_Sign_{SIGN_COLOURS.index(col)}"
    p.box(-d / 2 - 2.65, -d / 2 - 2.55, -w / 2 + 2, w / 2 - 2, ph - 1.6, ph - 0.4, mat)
    for s in (-1, 1):
        p.box(-d / 2 + 1, d / 2 - 3, s * (w / 2 + 2.55) - 0.05, s * (w / 2 + 2.65) + 0.05, ph - 1.4, ph - 0.6, mat)
    manifest["shops"].append({"tower": name, "pos": list(p.world(-d / 2 - 4, 0, 3.0)), "colour": list(col)})


def roof(p, w, d, top, manifest, beacon=True):
    p.box(-d * 0.25, d * 0.2, -w * 0.3, w * 0.25, top, top + 4.5, "City_Facade")  # plant room
    for k in range(RNG.randint(1, 3)):
        p.cylinder(RNG.uniform(-d * 0.35, d * 0.3), RNG.uniform(-w * 0.35, w * 0.35), top + 2.0, RNG.uniform(1.2, 2.2), 4.0, "City_Roof", 12)
    for k in range(RNG.randint(2, 5)):
        x, y = RNG.uniform(-d * 0.4, d * 0.4), RNG.uniform(-w * 0.4, w * 0.4)
        p.box(x - 1.2, x + 1.2, y - 0.9, y + 0.9, top, top + 1.6, "City_Roof")
    if beacon:
        h = RNG.uniform(8, 22)
        x, y = RNG.uniform(-d * 0.2, d * 0.2), RNG.uniform(-w * 0.2, w * 0.2)
        p.box(x - 0.25, x + 0.25, y - 0.25, y + 0.25, top, top + h, "City_Roof")
        p.cylinder(x, y, top + h + 0.4, 0.5, 0.8, "Beacon_Red", 12)
        manifest["beacons"].append(list(p.world(x, y, top + h + 0.4)))


def tower(mesh, name, az, dist, w, d, h, style, screens, manifest, detail=True):
    rad = math.radians(az)
    p = Placed(mesh, dist * math.cos(rad), dist * math.sin(rad), az)
    fh = CC.FLOOR_H[style]
    win = WINDOW_MAT[style]
    podium(p, w, d, manifest, name)
    z0 = CC.PODIUM_H + 0.5
    if style == "terraced":
        tiers, ww, dd, zz = RNG.randint(3, 4), w, d, z0
        for i in range(tiers):
            zt = z0 + (h - z0) * (i + 1) / tiers
            p.box(-dd / 2, dd / 2, -ww / 2, ww / 2, zz, zt, win)
            if detail:
                ring_ledges(p, ww, dd, zt - 0.6, 0.6, 0.6, "City_Facade")
                for zl in [zz + k * fh * 4 for k in range(1, int((zt - zz) / (fh * 4)))]:
                    ring_ledges(p, ww, dd, zl, 0.35, 0.25, "City_Facade")
            ww, dd, zz = ww * 0.8, dd * 0.82, zt
        top, tw, td = zz, ww / 0.8, dd / 0.82
    else:
        shaft_top = h * (0.78 if style == "glass" else 1.0)
        p.box(-d / 2, d / 2, -w / 2, w / 2, z0, shaft_top, win)
        top, tw, td = shaft_top, w, d
        if style == "glass":
            p.box(-d * 0.38, d * 0.38, -w * 0.4, w * 0.4, shaft_top, h, win)  # setback crown
            top, tw, td = h, w * 0.8, d * 0.76
            if detail:
                for k in range(1, int(w / 4.5)):  # vertical fins on the front and back
                    y = -w / 2 + k * 4.5
                    for x0, x1 in ((-d / 2 - 0.6, -d / 2), (d / 2, d / 2 + 0.6)):
                        p.box(x0, x1, y - 0.15, y + 0.15, z0, shaft_top, "City_Facade")
                for zl in [z0 + k * fh * 5 for k in range(1, int((shaft_top - z0) / (fh * 5)))]:
                    ring_ledges(p, w, d, zl, 0.5, 0.35, "City_Facade")
        elif detail:  # slab: a ledge every floor + AC units / balconies on the front
            for zl in [z0 + k * fh for k in range(1, int((shaft_top - z0) / fh))]:
                ring_ledges(p, w, d, zl, 0.18, 0.2, "City_Facade")
            for _ in range(int(w * h / 90)):
                y = RNG.uniform(-w / 2 + 1, w / 2 - 1)
                zf = z0 + fh * RNG.randint(1, int((shaft_top - z0) / fh) - 1)
                if RNG.random() < 0.6:
                    p.box(-d / 2 - 0.7, -d / 2, y - 0.5, y + 0.5, zf + 0.2, zf + 0.9, "City_Roof")  # AC unit
                else:
                    p.box(-d / 2 - 1.2, -d / 2, y - 1.4, y + 1.4, zf, zf + 0.12, "City_Facade")  # balcony slab
                    p.box(-d / 2 - 1.2, -d / 2 - 1.1, y - 1.4, y + 1.4, zf + 0.12, zf + 1.1, "City_Facade")
        if style == "slab":
            top, tw, td = shaft_top, w, d
    roof(p, tw, td, top, manifest, beacon=RNG.random() < CC.BEACON_CHANCE or detail)
    # screens on the front face (local -X), standing 0.3 m proud on a dark frame
    for i, (kind, off, zb, sw, sh, col) in enumerate(screens):
        x = -d / 2
        p.box(x - 0.35, x, off - sw / 2 - 0.4, off + sw / 2 + 0.4, zb - 0.4, zb + sh + 0.4, "City_Facade")
        mat = f"City_Screen_{name}_{i}"
        p.box(x - 0.45, x - 0.35, off - sw / 2, off + sw / 2, zb, zb + sh, mat)
        manifest["screens"].append({"name": f"{name}_{i}", "material": mat, "kind": kind, "colour": list(col),
                                    "center": list(p.world(x - 0.45, off, zb + sh / 2)), "normal": list(p.normal(-1, 0)),
                                    "width": sw, "height": sh})
    manifest["towers"].append({"name": name, "azimuth": az, "distance": dist, "width": w, "depth": d, "height": h,
                               "style": style, "front_distance": dist - d / 2})


def landmark(mesh, manifest):
    L = CC.LANDMARK
    rad = math.radians(L["azimuth"])
    cx, cy = L["distance"] * math.cos(rad), L["distance"] * math.sin(rad)
    r, h = L["radius"], L["height"]
    geo.lathe(mesh, (cx, cy, 0), [(r * 1.4, 0), (r * 1.4, 12), (r, 14), (r, h * 0.7), (r * 0.85, h * 0.9), (r * 0.6, h), (0.0, h + 2)],
              "City_Window_Glass", 32)
    z = 30.0
    while z < h * 0.9:  # glowing rings
        rr = r if z < h * 0.7 else r - (r * 0.15) * (z - h * 0.7) / (h * 0.2)
        geo.lathe(mesh, (cx, cy, z), [(rr + 0.2, 0), (rr + 0.6, 0), (rr + 0.6, 1.2), (rr + 0.2, 1.2)], "Landmark_Ring", 32,
                  cap_bottom=False, cap_top=False)
        z += L["ring_every"]
    hz, (ri, ro), hh = L["halo_z"], L["halo_r"], L["halo_h"]
    geo.lathe(mesh, (cx, cy, hz), [(ri, 0), (ro, 0), (ro, hh), (ri, hh), (ri, 0)], "Landmark_Ring", 48, cap_bottom=False, cap_top=False)
    for k in range(4):
        a = k * math.pi / 2
        geo.pipe(mesh, (cx + r * 0.7 * math.cos(a), cy + r * 0.7 * math.sin(a), hz + 1), (cx + ri * math.cos(a), cy + ri * math.sin(a), hz + 1), 0.6, "City_Facade", 8)
    geo.pipe(mesh, (cx, cy, h), (cx, cy, h + L["spire"]), 0.8, "City_Facade", 8)
    geo.cylinder(mesh, (cx, cy, h + L["spire"] + 0.6), 0.7, 1.2, "Beacon_Red", segments=12)
    manifest["beacons"].append([cx, cy, h + L["spire"] + 0.6])
    manifest["landmark"] = {"center": [cx, cy], "radius": r, "height": h}


# ---- Layout -------------------------------------------------------------------------------

def _corners(az, dist, w, d, pad=1.5):
    rad = math.radians(az)
    c = Vector((dist * math.cos(rad), dist * math.sin(rad)))
    ux, uy = Vector((math.cos(rad), math.sin(rad))), Vector((-math.sin(rad), math.cos(rad)))
    hx, hy = d / 2 + pad, w / 2 + pad
    return [c + ux * sx * hx + uy * sy * hy for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]


def _overlap(a, b):
    """Separating-axis test for two convex quads (lists of 2D Vectors)."""
    for poly in (a, b):
        for i in range(4):
            e = poly[(i + 1) % 4] - poly[i]
            n = Vector((-e.y, e.x))
            pa = [n.dot(p) for p in a]
            pb = [n.dot(p) for p in b]
            if max(pa) < min(pb) or max(pb) < min(pa):
                return False
    return True


def _viaduct_quad():
    v = CC.VIADUCT
    return [Vector((v["x0"], v["y0"] - 2)), Vector((v["x1"] + 200, v["y0"] - 2)), Vector((v["x1"] + 200, v["y1"] + 2)), Vector((v["x0"], v["y1"] + 2))]


def layout():
    """Resolve the hero towers, then scatter mid/far fill around them. Returns tower specs."""
    placed, specs = [], []
    via = _viaduct_quad()
    for name, az, dist, w, d, h, style, screens in CC.HERO_TOWERS:
        allow_viaduct = name == "RightA"  # the train runs into this tower
        while True:
            q = _corners(az, dist, w, d)
            hit = any(_overlap(q, o) for o in placed) or (not allow_viaduct and _overlap(q, via))
            if not hit and dist - d / 2 >= CC.PLAZA_RADIUS:
                break
            dist += 1.0
        placed.append(q)
        specs.append((name, az, dist, w, d, h, style, screens, True))
    L = CC.LANDMARK
    lw = 2 * L["radius"] * 1.4 + 6
    placed.append(_corners(L["azimuth"], L["distance"], lw, lw))
    styles, weights = zip(*CC.STYLE_WEIGHTS.items())
    for label, (count, dmin, dmax, hmin, hmax, smin, smax) in (("Mid", CC.MID_FIELD), ("Far", CC.FAR_FIELD)):
        made, tries = 0, 0
        while made < count and tries < count * 60:
            tries += 1
            az = RNG.uniform(*CC.FILL_AZIMUTH)
            dist = math.sqrt(RNG.uniform(dmin ** 2, dmax ** 2))
            if abs(az - L["azimuth"]) < CC.LANDMARK_SIGHTLINE_DEG and dist < L["distance"]:
                continue
            w, d = RNG.uniform(smin, smax), RNG.uniform(smin, smax)
            q = _corners(az, dist, w, d, pad=3.0)
            if any(_overlap(q, o) for o in placed) or _overlap(q, via):
                continue
            placed.append(q)
            hh = RNG.uniform(hmin, hmax) * (0.8 + 0.4 * (dist - dmin) / (dmax - dmin))
            specs.append((f"{label}{made:03d}", az, dist, w, d, hh, RNG.choices(styles, weights)[0], [], label == "Mid"))
            made += 1
    return specs
