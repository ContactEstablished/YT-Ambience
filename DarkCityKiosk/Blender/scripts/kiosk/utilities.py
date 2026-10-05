"""Utility pass (2026-10-04, brief 3): exposed conduit, cables, pipes and drainage, exported as its
own mesh (SM_Kiosk_Utilities).

The construction pass left the kiosk mechanically dense but made of separate objects. This pass
connects them: every run starts and ends at real equipment (a box, a gland, a roof penetration, a
soffit penetration "toward the roof"), so the kiosk reads as one working machine. Roughly 75% is
organised, clamped infrastructure and 25% later improvisation (a cable tied along an old conduit, a
newer conduit crossing in front of an older one, a slack coil left by an electrician, a drip loop).

  door wall  service entrance from the platform (power -> meter, comms -> data box, with a jog),
             fuse box -> LB body -> pull box, data box -> up behind that feed -> tee into the old wall
             conduit, pull box -> armoured flex -> card reader by the door, fan -> flex -> cabinet,
             cabinet -> three conduits with nested elbows -> up past the header into the soffit
  front      ticket machine -> two conduits up into the soffit junction box, isolator -> kitchen
             extract, extract -> gooseneck vent, copper water line with a valve, drain hose to a
             floor grate, a retrofit cable tied along the old conduit into the window lightbox
  soffit     galvanised trunk hung under the joists, a run along the left to the controller, the
             sign circuit under both edge beams (power supply -> corner box -> sign feeds, lantern
             box, corner-sign drip loop), thin cables to the tube drivers, a slack coil, the
             24h lantern feed draped over the drain
  drainage   outlet under the front edge beam -> horizontal run -> cast downpipe -> shoe -> splash
             block (front-right); the old back-left downpipe gets a soffit collar and a cleanout
  roof       disconnect switch on the HVAC (conduit up from a roof boot, flex whip into the unit),
             insulated refrigerant pair arching from the condenser, condensate line, mast coax

Rigid lines are swept tubes with rounded bends (fillet); flexible ones follow Catmull-Rom splines,
some corrugated. Everything is static geometry merged into one mesh (no simulated cables), so it
renders as cheaply as the rest of the kiosk. RUNS records each line's faces for the overlap check.
"""
import json
import math

from mathutils import Quaternion, Vector

import kiosk_config as C
from . import geo, roof
from .shell import WALLS, surface_w, world

U, M = C.UTILITIES, C.MASSING
PH, TOP, CB = C.PLATFORM_H, C.BODY_TOP, C.CANOPY_BOTTOM
BASE_TOP = PH + M["base_h"]
HEADER_Z0 = TOP - M["header_h"]
OLD_CONDUIT_Z = TOP - C.SHELL["topbeam_h"] - 0.05  # the step-2 conduit along the front and door walls (openings.py)
OLD_CONDUIT_W, OLD_CONDUIT_R = 0.035, 0.02
UP = Vector((0.0, 0.0, 1.0))
UDIR = {"front": Vector((1.0, 0.0, 0.0)), "left": Vector((0.0, 1.0, 0.0))}  # +u on each wall
NOUT = {"front": Vector((0.0, -1.0, 0.0)), "left": Vector((-1.0, 0.0, 0.0))}  # outward normal

# Materials introduced in this pass: (rgb, roughness, metallic, emission). Kept clean (the grime pass
# comes later); slight differences separate overlapping systems.
MATERIALS = {
    "Conduit_Painted": ((0.075, 0.08, 0.085), 0.45, 0.35, 0.0),  # dark painted rigid conduit
    "Cable_Black": ((0.018, 0.018, 0.02), 0.55, 0.0, 0.0),  # PVC-sheathed cable and flex conduit
    "Hose_Grey": ((0.30, 0.31, 0.31), 0.75, 0.0, 0.0),  # faded rubber hose, condensate line
    "Copper_Aged": ((0.42, 0.20, 0.11), 0.45, 0.9, 0.0),  # water and refrigerant lines (sparingly)
    "Insulation_Black": ((0.035, 0.035, 0.035), 0.9, 0.0, 0.0),  # foam lagging on the HVAC suction line
    "Pipe_Cast": ((0.13, 0.135, 0.14), 0.6, 0.2, 0.0),  # drain pipe and its fittings
}


def ensure_materials(B):
    import bpy
    for name, (rgb, rough, metal, emit) in MATERIALS.items():
        m = B.mat(name, rgb, emit)
        bsdf = m.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Roughness"].default_value = rough
        bsdf.inputs["Metallic"].default_value = metal
    return bpy.data.materials


# ---- Paths -------------------------------------------------------------------------------------

def V(x, y, z):
    return Vector((x, y, z))


def P(wall, u, z, w):
    return Vector(world(WALLS[wall], u, z, w))


def _dedupe(pts, eps=1e-5):
    out = []
    for p in pts:
        p = Vector(p)
        if not out or (p - out[-1]).length > eps:
            out.append(p)
    return out


def fillet(pts, radius, radii=None, seg90=6):
    """Rounded corners: each interior corner of the polyline becomes an arc of `radius`, shrunk to
    fit its segments (the end segments can be used whole, inner ones half each). radii overrides
    per corner (None = default, 0 = a sharp corner, e.g. under an LB body)."""
    pts = _dedupe(pts)
    if len(pts) < 3:
        return pts
    out = [pts[0]]
    last = len(pts) - 2
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        d0, d1 = b - a, c - b
        l0, l1 = d0.length, d1.length
        d0n, d1n = d0 / l0, d1 / l1
        ang = d0n.angle(d1n)
        r = radius if radii is None or radii[i - 1] is None else radii[i - 1]
        if ang < 1e-3 or r <= 0:
            out.append(b)
            continue
        lim = min(l0 if i == 1 else l0 / 2, l1 if i == last else l1 / 2) * 0.999
        t = min(r * math.tan(ang / 2), lim)
        r = t / math.tan(ang / 2)
        p0, p1 = b - d0n * t, b + d1n * t
        centre = b + (d1n - d0n).normalized() * (r / math.cos(ang / 2))
        v0, v1 = p0 - centre, p1 - centre
        axis = v0.cross(v1).normalized()
        n = max(2, math.ceil(seg90 * ang / (math.pi / 2)))
        out.append(p0)
        for k in range(1, n):
            out.append(centre + Quaternion(axis, ang * k / n) @ v0)
        out.append(p1)
    out.append(pts[-1])
    return _dedupe(out)


def spline(pts, step=0.025):
    """Catmull-Rom curve through the points (flexible cable, hose)."""
    p = _dedupe(pts)
    p = [p[0] + (p[0] - p[1])] + p + [p[-1] + (p[-1] - p[-2])]
    out = []
    for i in range(1, len(p) - 2):
        p0, p1, p2, p3 = p[i - 1], p[i], p[i + 1], p[i + 2]
        n = max(3, math.ceil((p2 - p1).length / step))
        for k in range(n):
            t = k / n
            out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (3 * p1 - p0 - 3 * p2 + p3) * t * t * t))
    out.append(p[-2])
    return _dedupe(out)


def sag(a, b, depth, n=14):
    """Points of a cable hanging between a and b, `depth` below the chord at the middle."""
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, k / n) - UP * (depth * 4 * (k / n) * (1 - k / n)) for k in range(n + 1)]


def path_length(path):
    return sum((q - p).length for p, q in zip(path, path[1:]))


def at(path, s):
    """Point and unit tangent at arc length s along the path (negative s counts from the end)."""
    if s < 0:
        s += path_length(path)
    for p, q in zip(path, path[1:]):
        seg = (q - p).length
        if s <= seg or q is path[-1]:
            t = (q - p).normalized()
            return p + t * min(s, seg), t
        s -= seg
    return path[-1], (path[-1] - path[-2]).normalized()


def _resample(path, step):
    total = path_length(path)
    n = max(2, math.ceil(total / step))
    return [at(path, total * k / n)[0] for k in range(n + 1)]


# ---- Geometry ----------------------------------------------------------------------------------

def tube(m, path, r, mat, sides=10, rib=None):
    """Sweep a circle of radius r along the path with parallel-transport frames (no twist), with
    flat caps. rib = (pitch, depth): corrugate the radius (flexible conduit, hose)."""
    if rib:
        path = _resample(path, rib[0] / 4)
    dense = [path[0]]
    for q in path[1:]:  # rings at most 6 cm apart (the export's mask bake wants short edges anyway)
        k = math.ceil((q - dense[-1]).length / 0.06)
        dense += [dense[-1].lerp(q, j / k) for j in range(1, k)] + [q]
    path = dense
    n = len(path)
    tans = []
    for i in range(n):
        if i == 0:
            t = path[1] - path[0]
        elif i == n - 1:
            t = path[-1] - path[-2]
        else:
            t = (path[i + 1] - path[i]).normalized() + (path[i] - path[i - 1]).normalized()
        tans.append(t.normalized())
    ref = UP if abs(tans[0].z) < 0.9 else Vector((1.0, 0.0, 0.0))
    nrm = tans[0].cross(ref).normalized()
    verts, s = [], 0.0
    for i in range(n):
        if i:
            nrm = tans[i - 1].rotation_difference(tans[i]) @ nrm
            nrm = (nrm - tans[i] * nrm.dot(tans[i])).normalized()
            s += (path[i] - path[i - 1]).length
        bi = tans[i].cross(nrm)
        rr = r * (1 + rib[1] * (0.5 + 0.5 * math.cos(2 * math.pi * s / rib[0]))) if rib else r
        for k in range(sides):
            a = 2 * math.pi * k / sides
            verts.append(path[i] + (nrm * math.cos(a) + bi * math.sin(a)) * rr)
    faces = [(i * sides + k, i * sides + (k + 1) % sides, (i + 1) * sides + (k + 1) % sides, (i + 1) * sides + k)
             for i in range(n - 1) for k in range(sides)]
    m.add_raw(verts, faces, mat, smooth=True)
    caps = verts[:sides] + verts[-sides:]
    m.add_raw(caps, [tuple(reversed(range(sides))), tuple(range(sides, 2 * sides))], mat, smooth=False)


RUNS = []  # {"name", "faces": [f0, f1], "ends": [p0, p1], "r"}: for the overlap check


def sides_for(r):
    return 14 if r >= 0.03 else 12 if r >= 0.018 else 10 if r >= 0.01 else 8 if r >= 0.006 else 6


def run(m, name, pts, r, mat, bend=None, radii=None, flex=False, rib=None, raw=False):
    """A line through the points: rigid (filleted corners, bend radius default 3r, at least 5 cm),
    flexible (spline) or raw (the points as given, e.g. a coil). Returns the swept path."""
    if raw:
        path = _dedupe(pts)
    elif flex:
        path = spline(pts)
    else:
        path = fillet(pts, bend if bend is not None else max(0.05, 3 * r), radii)
    f0 = len(m.faces)
    tube(m, path, r, mat, sides_for(r), rib)
    RUNS.append({"name": name, "faces": [f0, len(m.faces)], "ends": [list(path[0]), list(path[-1])], "r": r})
    return path


def axes(t, n):
    """Right-handed frame: x along t, z along n (made perpendicular to t), y = z x x."""
    t = t.normalized()
    n = (n - t * n.dot(t)).normalized()
    return t, n.cross(t), n


def obox(m, c, ax, ay, az, sx, sy, sz, mat):
    """Oriented box: centre c, axes ax/ay (az is recomputed so the frame is right-handed), full sizes."""
    ax, ay = ax.normalized(), ay.normalized()
    az = ax.cross(ay)
    verts = [c + ax * (dx * sx / 2) + ay * (dy * sy / 2) + az * (dz * sz / 2)
             for dz in (-1, 1) for dy in (-1, 1) for dx in (-1, 1)]
    m.add_raw(verts, [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)], mat)


def ring(m, p, t, r, length, mat):
    """Short cylinder round a line (coupling, band, hub, collar)."""
    geo.pipe(m, p - t * (length / 2), p + t * (length / 2), r, mat, sides_for(r) + 2)


def couplings(m, path, every, r, mat="Steel_Galv_Dull", margin=0.15):
    """Couplings along a rigid run (where the 3 m sticks would join), kept off the bends' ends."""
    total = path_length(path)
    s = every
    while s < total - margin:
        if s > margin:
            p, t = at(path, s)
            ring(m, p, t, r * 1.22 + 0.002, 0.04, mat)
        s += every


def surf(wall, u, z, half=0.012):
    """How far out the wall surface stands at (u, z): sheets and plates (shell.LAYOUT), the base
    frame, the header, the corner angles, the window bay and the service-opening posts."""
    s = surface_w(wall, u - half, u + half, z - half, z + half)
    if z < BASE_TOP:
        s = max(s, M["base_proud"])
    if z > HEADER_Z0:
        s = max(s, M["header_proud"])
    t = M["corner_t"]
    for (xw, yw), (fx, fy) in M["corners"].items():
        if wall == "front" and yw == "front":
            x, sx = (C.X0, -1) if xw == "left" else (C.X1, 1)
            a, b = sorted((x + sx * t, x + sx * t - sx * fx))
        elif wall == "left" and xw == "left":
            y, sy = (C.Y0, -1) if yw == "front" else (C.Y1, 1)
            a, b = sorted((y, y + sy * t - sy * fy))
        else:
            continue
        if a - half <= u <= b + half:
            s = max(s, t)
    if wall == "front":
        b = M["bay"]
        if BASE_TOP <= z <= HEADER_Z0 and (b["x0"] <= u <= b["x0"] + b["post_w"] or b["x1"] - b["post_w"] <= u <= b["x1"]):
            s = max(s, b["proud"])
        sw, fw, jw, pw = C.SERVICE_WINDOW, C.SHELL["frame_w"], M["service_jamb_w"], C.SERVICE_POSTS["w"]
        for a0 in (sw["x0"] - fw - jw - pw, sw["x1"] + fw + jw):
            if a0 <= u <= a0 + pw and BASE_TOP <= z <= M["service_hood"]["z0"]:
                s = max(s, C.SERVICE_POSTS["proud"])
    return s


def foot(m, p, along, n, size=(0.05, 0.03), t=0.005, mat="Steel_Galv_Dull"):
    """Flat mounting foot lying on a surface at p (n = surface normal), with two bolt heads."""
    obox(m, p + n * (t / 2), along, n.cross(along), n, size[0], size[1], t + 0.002, mat)
    for k in (-1, 1):
        geo.pipe(m, p + n * t + along * (k * size[0] * 0.32), p + n * (t + 0.007) + along * (k * size[0] * 0.32), 0.007,
                 "Steel_Dark", 6)


def clamp_wall(m, wall, us_zs, w, rs, direction, mat="Steel_Galv_Dull"):
    """Clamps holding lines that run along `direction` ('z' vertical, 'u' horizontal), all w out from
    the wall: one strut channel across them on the wall surface when there are several, a band and a
    standoff for each. us_zs: the (u, z) of each line at the clamp."""
    n, ud = NOUT[wall], UDIR[wall]
    t = UP if direction == "z" else ud  # along the lines
    across = ud if direction == "z" else UP
    s = max(surf(wall, u, z) for u, z in us_zs)
    gap_min = min(w - r - s for r in rs)
    depth = max(0.0, min(0.035, gap_min - 0.004)) if len(us_zs) > 1 else 0.0
    if len(us_zs) > 1 and depth > 0.008:
        cs = [P(wall, u, z, 0.0) for u, z in us_zs]
        a = min(c.dot(across) for c in cs) - max(rs) - 0.035
        b = max(c.dot(across) for c in cs) + max(rs) + 0.035
        c0 = cs[0] - across * cs[0].dot(across) + across * ((a + b) / 2) + n * (s + depth / 2)
        obox(m, c0, across, t, n, b - a, 0.042, depth + 0.002, mat)
        obox(m, c0 + n * (depth / 2), across, t, n, b - a - 0.02, 0.016, 0.003, "Steel_Dark")  # the slot
        for k in (-1, 1):
            geo.pipe(m, c0 + across * (k * ((b - a) / 2 - 0.018)) + n * (depth / 2),
                     c0 + across * (k * ((b - a) / 2 - 0.018)) + n * (depth / 2 + 0.008), 0.008, "Steel_Dark", 6)
        channel = True
    else:
        channel = False
    for (u, z), r in zip(us_zs, rs):
        base = s + depth if channel else surf(wall, u, z)
        p = P(wall, u, z, w)
        ring(m, p, t, r + 0.005, 0.022, mat)
        gap = w - r - base
        if gap > 0.002:
            obox(m, P(wall, u, z, base + gap / 2), across, t, n, 0.026, 0.02, gap + 0.004, mat)
        if not channel:
            foot(m, P(wall, u, z, base), across, n, (0.06, 0.026))


def hanger(m, p, t, r, top, mat="Steel_Galv_Dull"):
    """Clevis hanger: a band round a hung line at p (direction t) on a threaded rod up to z = top."""
    ring(m, p, t, r + 0.006, 0.026, mat)
    geo.pipe(m, p + UP * r, V(p.x, p.y, top), 0.005, mat, 6)
    obox(m, V(p.x, p.y, top - 0.004), t, UP.cross(t), UP, 0.05, 0.05, 0.008, "Steel_Dark")


def fascia_boxes():
    """Sign-circuit boxes hung under the fascia edge beams, {name: (centre, sx, sy, sz)}: the corner
    box (fed from the sign power supply), the lantern box on the left run and the end box for the
    corner sign. clutter.py ends the lantern feed and the fuse-box cable on them."""
    fc = U["fascia_conduit"]
    xl, yf = C.CANOPY_X0 + fc["inset"], C.CANOPY_Y0 + fc["inset"]
    zbox = C.FASCIA_Z0 - 0.045
    xr = C.CANOPY_X1 - C.FASCIA["depth"] - 0.07  # clear of the right edge beam
    return {"corner": (V(xl, yf, zbox), 0.12, 0.12, 0.09), "lantern": (V(xl, fc["lantern_box_y"], zbox + 0.01), 0.08, 0.08, 0.07),
            "end": (V(xr, yf, zbox), 0.12, 0.10, 0.09)}


def tie(m, p, t, r):
    ring(m, p, t, r + 0.0025, 0.007, "Rubber_Black")


def jbox(m, c, ax, ay, sx, sy, sz, mat="Steel_Grey", cover="Steel_Galv_Dull"):
    """Junction box: a body, a cover plate on its +az face (az = ax x ay) and four cover screws."""
    ax, ay = ax.normalized(), ay.normalized()
    az = ax.cross(ay)
    obox(m, c, ax, ay, az, sx, sy, sz, mat)
    obox(m, c + az * (sz / 2 + 0.002), ax, ay, az, sx - 0.012, sy - 0.012, 0.006, cover)
    for i in (-1, 1):
        for j in (-1, 1):
            q = c + az * (sz / 2 + 0.005) + ax * (i * (sx / 2 - 0.016)) + ay * (j * (sy / 2 - 0.016))
            geo.pipe(m, q, q + az * 0.004, 0.006, "Steel_Dark", 6)


def lb_body(m, p, t_in, t_out, r, mat="Steel_Galv_Dull"):
    """Conduit body (an LB / LL fitting) at a sharp 90-degree corner: a cast box along the incoming
    run with a hub on the outgoing side and a cover on its back."""
    t_in, t_out = t_in.normalized(), t_out.normalized()
    s = 2.3 * r + 0.016
    obox(m, p - t_in * (s * 0.55), t_in, t_out, None, s * 2.2, s, s, mat)
    ring(m, p + t_out * (s * 0.55), t_out, r * 1.3, 0.025, mat)
    ring(m, p - t_in * (s * 1.65 + 0.012), t_in, r * 1.3, 0.025, mat)
    obox(m, p - t_in * (s * 0.55) - t_out * (s / 2 + 0.003), t_in, t_in.cross(t_out), -t_out, s * 2.0, s * 0.8, 0.006, "Steel_Dark")


# ---- Door wall -----------------------------------------------------------------------------------

def door_wall(m):
    L = "left"
    boxes = {b[0]: b for b in C.LEFT_WALL_BOXES}
    housing = {h[0]: h for h in C.WALL_HOUSINGS}["UtilityBox_L"]
    meter, fuse = boxes["MeterBox"], boxes["FuseBox"]

    # Service entrance: power (galvanised, the heaviest conduit on the wall) up into the meter box and
    # comms beside it into the data box, sharing strut clamps; the comms line jogs over to its box.
    en = U["entrance"]
    (up, uc), w, (rp, rc), (j0, j1, uj) = en["u"], en["w"], en["r"], en["jog"]
    run(m, "entrance_power", [P(L, up, PH - 0.03, w), P(L, up, meter[3] + 0.008, w)], rp, "Steel_Galv_Dull")
    run(m, "entrance_comms", [P(L, uc, PH - 0.03, w), P(L, uc, j0, w), P(L, uj, j1, w), P(L, uj, housing[4] + 0.008, w)], rc,
        "Steel_Galv_Dull", bend=0.06)
    for u, r in ((up, rp), (uc, rc)):
        ring(m, P(L, u, PH + 0.025, w), UP, r + 0.012, 0.05, "Steel_Dark")  # sleeve out of the platform
        obox(m, P(L, u, PH + 0.003, w), UDIR[L], NOUT[L], UP, 2 * r + 0.06, 2 * r + 0.06, 0.006, "Steel_Dark")
    ring(m, P(L, up, meter[3] - 0.012, w), UP, rp + 0.01, 0.024, "Steel_Dark")  # meter hub
    ring(m, P(L, uj, housing[4] - 0.01, w), UP, rc + 0.008, 0.02, "Steel_Dark")
    ring(m, P(L, up, 0.98, w), UP, rp * 1.22 + 0.002, 0.04, "Steel_Galv_Dull")  # coupling
    for z in (0.56, 0.86):
        clamp_wall(m, L, [(up, z), (uc, z)], w, [rp, rc], "z")
    clamp_wall(m, L, [(up, 1.08)], w, [rp], "z")

    # Fuse box -> pull box: out of the fuse box's side, an LB body turns it down, a bend into the pull box
    ff, pb = U["fuse_feed"], C.PULL_BOX
    s_riser = surface_w(L, pb["riser_u"] - 0.021, pb["riser_u"] + 0.021, BASE_TOP + 0.7, HEADER_Z0)
    wc = s_riser + 0.035 + pb["depth"] / 2  # the pull box's mid-depth (construction.door_wall)
    ud, zt, zi, r = ff["u_drop"], ff["z_top"], ff["z_in"], ff["r"]
    run(m, "fuse_to_pullbox", [P(L, fuse[2] - 0.006, zt, wc), P(L, ud, zt, wc), P(L, ud, zi, wc), P(L, pb["u0"] + 0.006, zi, wc)], r,
        "Conduit_Painted", radii=[0.0, 0.045])
    lb_body(m, P(L, ud, zt, wc), UDIR[L], -UP, r)
    ring(m, P(L, fuse[2] + 0.008, zt, wc), UDIR[L], r + 0.008, 0.018, "Steel_Dark")
    clamp_wall(m, L, [(ud, 1.80)], wc, [r], "z")

    # Data box -> up the wall, hugging it, behind the fuse feed -> a tee on the old wall conduit
    dr = U["data_riser"]
    run(m, "data_riser", [P(L, dr["u"], housing[5] - 0.006, dr["w"]), P(L, dr["u"], OLD_CONDUIT_Z, dr["w"])], dr["r"], "Conduit_Painted")
    obox(m, P(L, dr["u"], OLD_CONDUIT_Z, OLD_CONDUIT_W), UDIR[L], UP, NOUT[L], 0.075, 0.055, 0.058, "Steel_Galv_Dull")  # tee
    obox(m, P(L, dr["u"], OLD_CONDUIT_Z, OLD_CONDUIT_W + 0.031), UDIR[L], UP, NOUT[L], 0.062, 0.042, 0.005, "Steel_Dark")
    for z in (1.84, 2.03):
        clamp_wall(m, L, [(dr["u"], z)], dr["w"], [dr["r"]], "z")

    # Pull box -> armoured flex, clipped once, curling into a card reader beside the door
    u0, u1, z0, z1, dep = U["card_reader"]
    s = surface_w(L, u0, u1, z0, z1)
    c = P(L, (u0 + u1) / 2, (z0 + z1) / 2, s + dep / 2)
    obox(m, c, UDIR[L], UP, NOUT[L], u1 - u0, z1 - z0, dep, "Steel_Charcoal")
    obox(m, P(L, (u0 + u1) / 2, z1 - 0.045, s + dep + 0.001), UDIR[L], UP, NOUT[L], u1 - u0 - 0.02, 0.04, 0.004, "Rubber_Black")
    geo.pipe(m, P(L, u1 - 0.016, z0 + 0.02, s + dep), P(L, u1 - 0.016, z0 + 0.02, s + dep + 0.004), 0.005, "Button_Lit_Green", 8)
    stub = (pb["riser_u"] + 0.04, pb["z0"] - 0.09)  # the pull box's bottom stub (construction.door_wall)
    ue = (u0 + u1) / 2 + 0.01
    path = run(m, "reader_flex", [P(L, stub[0], stub[1] + 0.006, wc), P(L, stub[0], stub[1] - 0.05, wc - 0.004),
                                  P(L, stub[0] + 0.04, 1.30, 0.06), P(L, ue - 0.06, 1.285, s + 0.03),
                                  P(L, ue, 1.27, s + 0.02), P(L, ue, z1 - 0.004, s + 0.02)],
               0.007, "Steel_Galv_Dull", flex=True, rib=(0.012, 0.18))
    p, t = at(path, path_length(path) * 0.55)
    clamp_wall(m, L, [((p - P(L, 0, 0, 0)).dot(UDIR[L]), p.z)], (p - P(L, 0, 0, 0)).dot(NOUT[L]), [0.008], "u")

    # Exhaust fan -> liquid-tight flex out of a gland on its mount plate, over the fan, up into the
    # cabinet's first gland stub
    e, f = C.ELEC_CABINET, C.FAN_COVER
    w0 = e["rail_t"] + surface_w(L, e["u0"], e["u1"], e["z0"], e["z1"])
    gw = w0 + e["depth"] / 2  # the gland stubs' depth (construction.door_wall)
    gu, gz = e["u0"] + 0.08, e["z0"] - 0.018 - 0.055
    sp = surface_w(L, f["u"] - f["plate"], f["u"] + f["plate"], f["z"] - f["plate"], f["z"] + f["plate"]) + 0.012
    fu, fz = f["u"] + 0.155, f["z"] + 0.205
    geo.pipe(m, P(L, fu, fz, sp), P(L, fu, fz, sp + 0.03), 0.017, "Steel_Dark", 10)  # gland on the plate
    run(m, "fan_flex", [P(L, fu, fz, sp + 0.026), P(L, fu - 0.01, fz + 0.005, sp + 0.07), P(L, fu - 0.09, fz + 0.022, gw - 0.01),
                        P(L, gu + 0.1, fz + 0.025, gw + 0.005), P(L, gu, gz - 0.035, gw), P(L, gu, gz + 0.006, gw)],
        0.012, "Cable_Black", flex=True, rib=(0.014, 0.14))
    ring(m, P(L, gu, gz - 0.008, gw), UP, 0.019, 0.018, "Steel_Dark")

    # Electrical cabinet -> three conduits out of its side, nested elbows, up past the header and the
    # old conduit (a newer line crossing in front of an older one) into a sealed soffit penetration
    db = U["door_bundle"]
    w = db["w"]
    for k, (u, z, r) in enumerate(zip(db["u"], db["z"], db["r"])):
        path = run(m, f"cabinet_bundle_{k}", [P(L, e["u1"] - 0.006, z, w), P(L, u, z, w), P(L, u, CB + 0.012, w)], r, "Conduit_Painted",
                   bend=0.045 + 0.02 * k)
        ring(m, P(L, e["u1"] + 0.008, z, w), UDIR[L], r + 0.008, 0.018, "Steel_Dark")  # locknut / hub
        ring(m, P(L, u, CB - 0.014, w), UP, r + 0.008, 0.026, "Steel_Dark")  # seal collar
        if k == 1:
            ring(m, P(L, u, 1.72, w), UP, r * 1.22 + 0.002, 0.04, "Steel_Galv_Dull")
    for z in (1.84, 1.98):
        clamp_wall(m, L, [(u, z) for u in db["u"]], w, list(db["r"]), "z")
    obox(m, V(C.X0 - w, sum(db["u"]) / 3, CB - 0.004), Vector((1, 0, 0)), Vector((0, 1, 0)), UP, 0.07,
         db["u"][2] - db["u"][0] + 0.09, 0.008, "Steel_Galv_Dull")  # penetration plate


# ---- Front wall -----------------------------------------------------------------------------------

def front_wall(m):
    F = "front"
    # Ticket machine -> two conduits straight up into the corner junction box on the soffit conduit
    tm, jx = C.TICKET_MACHINE, C.SOFFIT_JUNCTIONS["front"][0]
    us, rs, w = (jx - 0.035, jx + 0.025), (0.013, 0.011), 0.10
    for k, (u, r) in enumerate(zip(us, rs)):
        run(m, f"ticket_feed_{k}", [P(F, u, tm["z1"] - 0.005, w), P(F, u, CB - 0.1 + 0.006, w)], r, "Conduit_Painted")
        ring(m, P(F, u, tm["z1"] + 0.012, w), UP, r + 0.008, 0.02, "Steel_Dark")
        ring(m, P(F, u, CB - 0.11, w), UP, r + 0.008, 0.02, "Steel_Dark")
    clamp_wall(m, F, [(us[0], 1.95), (us[1], 1.95)], w, list(rs), "z")

    # Isolator switch on the right post -> an offset round the hood bracket -> the kitchen extract's side
    sw, fw, jw, pw = C.SERVICE_WINDOW, C.SHELL["frame_w"], M["service_jamb_w"], C.SERVICE_POSTS["w"]
    a0 = sw["x1"] + fw + jw
    uc, wi = (a0 + a0 + pw) / 2 + 0.002, C.SERVICE_POSTS["proud"] + 0.032
    zs = C.SERVICE_SWITCH["z1"] + 0.16  # top of the switch's stub (construction.service_opening)
    ex = C.KITCHEN_EXHAUST
    uo = a0 + pw + 0.012
    run(m, "isolator_to_extract", [P(F, uc, zs - 0.006, wi), P(F, uc, zs + 0.025, wi), P(F, uo, zs + 0.07, wi),
                                   P(F, uo, 1.83, wi), P(F, ex[0] + 0.006, 1.83, wi)], 0.012, "Conduit_Painted", bend=0.03)
    ring(m, P(F, ex[0] - 0.008, 1.83, wi), UDIR[F], 0.02, 0.018, "Steel_Dark")

    # Kitchen extract -> gooseneck vent through its rain cap, turning out and down under the canopy
    vx, vw, vr = (ex[0] + ex[1]) / 2, 0.11, 0.042
    path = run(m, "extract_vent", [P(F, vx, ex[3] - 0.01, vw), P(F, vx, 2.035, vw), P(F, vx, 2.035, 0.26), P(F, vx, 1.97, 0.26)],
               vr, "Steel_Galvanised", bend=0.06)
    ring(m, P(F, vx, ex[3] + 0.03, vw), UP, vr + 0.014, 0.03, "Steel_Dark")  # collar through the cap
    p, t = at(path, -0.012)
    ring(m, p, t, vr + 0.006, 0.024, "Steel_Galvanised")  # lip
    geo.pipe(m, p - t * 0.02, p - t * 0.016, vr - 0.003, "Rubber_Black", 14)  # bird screen
    p, t = at(path, path_length(path) * 0.5)
    ring(m, p, t, vr + 0.004, 0.03, "Steel_Dark")  # duct joint

    # Front housing -> two conduits out of its side, nested elbows, up the yellow strip beside the
    # extract, past the old conduit and the header into a sealed soffit penetration (feeds to the canopy)
    fh = C.FRONT_HOUSING
    hr = U["housing_risers"]
    w = hr["w"]
    for k, (u, z, r) in enumerate(zip(hr["u"], hr["z"], hr["r"])):
        run(m, f"housing_riser_{k}", [P(F, fh[0] + 0.006, z, w), P(F, u, z, w), P(F, u, CB + 0.012, w)], r, "Conduit_Painted",
            bend=0.045 + 0.025 * k)
        ring(m, P(F, fh[0] - 0.008, z, w), UDIR[F], r + 0.008, 0.018, "Steel_Dark")
        ring(m, P(F, u, CB - 0.014, w), UP, r + 0.008, 0.026, "Steel_Dark")
        for zc in (1.80, 2.02):
            clamp_wall(m, F, [(u, zc)], w, [r], "z")
    obox(m, V(sum(hr["u"]) / 2, C.Y0 - w, CB - 0.004), Vector((1, 0, 0)), Vector((0, 1, 0)), UP, abs(hr["u"][1] - hr["u"][0]) + 0.08,
         0.07, 0.008, "Steel_Galv_Dull")  # penetration plate

    # Copper water line out of the service-entry enclosure, a valve, into the wall under the counter
    se = C.SERVICE_ENTRY
    xu, zw = -1.40, 0.72
    run(m, "water_line", [P(F, se[1] - 0.006, zw, 0.075), P(F, xu, zw, 0.075), P(F, xu, 0.90, 0.075), P(F, xu, 0.90, 0.004)], 0.009,
        "Copper_Aged", bend=0.035)
    ring(m, P(F, se[1] + 0.006, zw, 0.075), UDIR[F], 0.014, 0.014, "Copper_Aged")
    obox(m, P(F, xu, 0.81, 0.075), UDIR[F], UP, NOUT[F], 0.032, 0.05, 0.032, "Copper_Aged")  # valve body
    geo.pipe(m, P(F, xu, 0.81, 0.091), P(F, xu, 0.81, 0.104), 0.004, "Steel_Dark", 6)
    obox(m, P(F, xu + 0.03, 0.81, 0.106), UDIR[F], UP, NOUT[F], 0.07, 0.012, 0.006, "Stock_Red")  # lever
    ring(m, P(F, xu, 0.90, 0.006), NOUT[F], 0.022, 0.006, "Steel_Galv_Dull")  # escutcheon
    clamp_wall(m, F, [(-1.49, zw)], 0.075, [0.009], "u")

    # Drain hose from the enclosure's underside, slack, down onto a floor grate in the platform
    hx = se[1] - 0.05
    run(m, "drain_hose", [P(F, hx, se[2] + 0.006, 0.09), P(F, hx, se[2] - 0.06, 0.095), P(F, hx + 0.04, 0.27, 0.15),
                          P(F, hx + 0.12, 0.15, 0.24), P(F, hx + 0.21, PH + 0.016, 0.31), P(F, hx + 0.25, PH + 0.016, 0.335)],
        0.014, "Hose_Grey", flex=True, rib=(0.03, 0.06))
    ring(m, P(F, hx, se[2] - 0.006, 0.09), UP, 0.019, 0.02, "Steel_Galv_Dull")  # hose barb
    gc = P(F, hx + 0.28, PH + 0.002, 0.34)
    obox(m, gc, UDIR[F], NOUT[F], UP, 0.15, 0.12, 0.006, "Steel_Dark")  # floor grate
    for k in range(5):
        obox(m, gc + UP * 0.004 + UDIR[F] * (-0.05 + k * 0.025), UDIR[F], NOUT[F], UP, 0.008, 0.09, 0.004, "Rubber_Black")

    # Retrofit cable for the window lightbox: out of the front housing's LB fitting, tied along the
    # outside of the old wall conduit (resting on its clamps), dropping into the lightbox top
    fh, lb = C.FRONT_HOUSING, C.WINDOW_LIGHTBOX
    lu = (fh[0] + fh[1]) / 2
    wt = OLD_CONDUIT_W + OLD_CONDUIT_R + 0.015
    ud = lb["x0"] + 0.11
    bay = M["bay"]
    wb = bay["proud"] + 0.016  # over the bay post
    path = run(m, "lightbox_cable", [P(F, lu + 0.025, OLD_CONDUIT_Z - 0.01, 0.07), P(F, lu + 0.06, OLD_CONDUIT_Z, wt),
                                     P(F, bay["x0"] - 0.03, OLD_CONDUIT_Z, wt + 0.012), P(F, bay["x0"] + 0.03, OLD_CONDUIT_Z - 0.004, wb),
                                     P(F, bay["x0"] + bay["post_w"] + 0.03, OLD_CONDUIT_Z - 0.008, wb),
                                     P(F, ud - 0.03, OLD_CONDUIT_Z - 0.02, lb["depth"] / 2 + 0.01),
                                     P(F, ud, lb["z1"] + 0.015, lb["depth"] / 2), P(F, ud, lb["z1"] - 0.004, lb["depth"] / 2)],
               0.006, "Cable_Black", flex=True)
    for k in (0.04, 0.075):  # ties onto the old conduit
        p, t = at(path, k)
        tie(m, p, t, 0.006)
    ring(m, P(F, ud, lb["z1"] + 0.004, lb["depth"] / 2), UP, 0.011, 0.012, "Rubber_Black")  # grommet


# ---- Under the canopy --------------------------------------------------------------------------

def soffit(m):
    X = Vector((1.0, 0.0, 0.0))
    Y = Vector((0.0, 1.0, 0.0))
    # Galvanised trunk hung under the joists along the front: down out of the soffit at the left,
    # trapeze-free clevis hangers, couplings, a tee dropping onto the service hood, into an end box
    tr = U["trunk"]
    y, z, r = tr["y"], tr["z"], tr["r"]
    path = run(m, "soffit_trunk", [V(tr["x0"], y, CB + 0.012), V(tr["x0"], y, z), V(tr["x1"] + 0.006, y, z)], r, "Steel_Galv_Dull", bend=0.08)
    ring(m, V(tr["x0"], y, CB - 0.012), UP, r + 0.01, 0.024, "Steel_Dark")
    couplings(m, path, 1.05, r)
    for x in tr["hangers"]:
        hanger(m, V(x, y, z), X, r, CB)
    hood = M["service_hood"]
    tx = (hood["x0"] + hood["x1"]) / 2 + 0.25
    obox(m, V(tx, y, z - 0.006), X, Y, UP, 0.07, 2 * r + 0.026, 2 * r + 0.026, "Steel_Galv_Dull")  # tee onto the hood
    geo.pipe(m, V(tx, y, z - r - 0.01), V(tx, y, hood["z1"] - 0.005), 0.013, "Steel_Galv_Dull", 10)
    ring(m, V(tx, y, hood["z1"] + 0.004), UP, 0.02, 0.01, "Steel_Dark")
    end = V(tr["x1"] + 0.08, y, 2.1225)
    jbox(m, end, X, UP, 0.16, 0.095, 0.12)  # end box, its cover facing the fascia
    obox(m, V(2.28, y, (end.z + 0.0475 + 2.175) / 2), X, Y, UP, 0.03, 0.03, 2.175 - end.z - 0.0475 + 0.002, "Steel_Galv_Dull")

    # Left run: down out of the soffit, along the left wall under the joists, into the controller box
    lr = U["left_run"]
    x, z, r = lr["x"], lr["z"], lr["r"]
    ctrl = C.SOFFIT_FRAME["controller"]
    path = run(m, "soffit_left_run", [V(x, lr["y0"], CB + 0.012), V(x, lr["y0"], z), V(x, ctrl[2] + 0.006, z)], r, "Conduit_Painted",
               bend=0.07)
    ring(m, V(x, lr["y0"], CB - 0.012), UP, r + 0.01, 0.024, "Steel_Dark")
    ring(m, V(x, ctrl[2] - 0.008, z), Y, r + 0.008, 0.018, "Steel_Dark")
    couplings(m, path, 1.0, r, "Steel_Dark")
    for yy in lr["hangers"]:
        hanger(m, V(x, yy, z), Y, r, CB)

    # Sign circuit: sign power supply -> corner box -> conduits under both fascia edge beams, with
    # feeds up into the lit faces, a box for the lantern, an end box for the corner sign
    fc, fb = U["fascia_conduit"], fascia_boxes()
    z, r = fc["z"], fc["r"]
    for c, sx, sy, sz in fb.values():
        jbox(m, c, X, -Y, sx, sy, sz, cover="Steel_Grey")  # covers facing down
    xl, yf, zbox = fb["corner"][0]
    xr, yl = fb["end"][0].x, fb["lantern"][0].y
    sf = C.SOFFIT_FRAME
    ex, ey = C.CANOPY_X0 + C.FASCIA["depth"] - C.X0, C.CANOPY_Y0 + C.FASCIA["depth"] - C.Y0
    ln = math.hypot(ex, ey)
    dx, dy = ex / ln, ey / ln
    pc = V(C.X0 + dx * (sf["psu_along_brace"] + 0.17), C.Y0 + dy * (sf["psu_along_brace"] + 0.17), 2.085)
    run(m, "psu_to_corner", [pc - V(dx, dy, 0) * 0.006, V(xl + 0.054, yf + 0.054, zbox)], 0.011, "Conduit_Painted")
    front = run(m, "fascia_front", [V(xl + 0.054, yf, z), V(xr - 0.054, yf, z)], r, "Conduit_Painted")
    left = run(m, "fascia_left", [V(xl, yf + 0.054, z), V(xl, yl - 0.036, z)], r, "Conduit_Painted")
    for pth, axis in ((front, X), (left, Y)):
        total = path_length(pth)
        s = 0.35
        while s < total - 0.2:  # one-hole straps up to the beam's bottom flange
            p, t = at(pth, s)
            ring(m, p, t, r + 0.004, 0.02, "Steel_Galv_Dull")
            obox(m, V(p.x, p.y, (p.z + r + C.FASCIA_Z0) / 2), t, UP.cross(t), UP, 0.02, 0.02, C.FASCIA_Z0 - p.z - r + 0.004, "Steel_Galv_Dull")
            s += 0.62
    for xs in (-2.05, -0.62, 0.80, 2.05):  # feeds up into the lit front face: small bodies on the conduit
        obox(m, V(xs, yf, z + r + 0.008), X, Y, UP, 0.05, 0.036, 0.016, "Steel_Galv_Dull")
    for ys in (-1.40, -0.20, 0.75):
        obox(m, V(xl, ys, z + r + 0.008), Y, X, UP, 0.05, 0.036, 0.016, "Steel_Galv_Dull")

    # Corner sign: a drip loop out of the end box, under the right edge beam, up into the sign
    cs = C.CORNER_SIGN
    zl = cs["z0"] - 2.02  # the loop hangs relative to the sign's bottom (2.02 when it was drawn; moved down 10/5)
    run(m, "corner_sign_loop", [V(xr + 0.054, yf, zbox), V(xr + 0.14, yf, zbox - 0.03), V(xr + 0.26, yf + 0.004, 1.95 + zl),
                                V(cs["x"] - 0.06, cs["y"] - 0.02, 1.915 + zl), V(cs["x"], cs["y"] - 0.01, 1.96 + zl),
                                V(cs["x"], cs["y"] - 0.01, cs["z0"] + 0.006)], 0.009, "Cable_Black", flex=True)
    ring(m, V(cs["x"], cs["y"] - 0.01, cs["z0"] - 0.006), UP, 0.015, 0.014, "Rubber_Black")

    # Thin cables to the tube drivers: hung in small sags on J-hooks along the fascia side of the
    # front purlin (through the joists' webs), with a drop into each driver's gland
    db = U["driver_bundle"]
    yb, zb = db["y"], db["z"]
    drivers = [d for d in sf["drivers"] if d[0] == "front"]
    xe = drivers[-1][2] + 0.10
    hooks = [db["x0"]] + [db["x0"] + 0.1 + k * 0.42 for k in range(1, 30) if db["x0"] + 0.1 + k * 0.42 < xe - 0.1] + [xe]
    for j, (oy, oz) in enumerate(((0.0, 0.0), (0.0092, 0.0), (0.0046, -0.008))):
        pts = [V(db["x0"] - oz, yb + oy, CB + 0.01), V(db["x0"] - oz, yb + oy, zb + oz)]
        for a, b in zip(hooks, hooks[1:]):
            pts += sag(V(a - (oz if a == hooks[0] else 0.0), yb + oy, zb + oz), V(b, yb + oy, zb + oz), 0.012, 6)[1:]
        run(m, f"driver_cable_{j}", pts, 0.0045, "Cable_Black", raw=True)
    for xh in hooks[1:-1]:
        geo.pipe(m, V(xh, yb, zb + 0.006), V(xh, yb, CB), 0.003, "Steel_Galv_Dull", 6)  # J-hook rod
        ring(m, V(xh, yb, zb - 0.002), X, 0.014, 0.008, "Steel_Galv_Dull")
    for side, a0, a1 in drivers:
        gx = a1 + 0.024
        run(m, f"driver_drop_{a0:.2f}", [V(a1 + 0.12, yb, zb - 0.01), V(a1 + 0.07, yb + 0.02, 2.175), V(gx - 0.004, -2.01, CB - 0.06 - 0.035)],
            0.0045, "Cable_Black", flex=True)

    # A slack service coil: out of the right soffit junction box, over the trunk, coiled twice and
    # tied, then into the end of the right tube driver
    jxr = C.SOFFIT_JUNCTIONS["front"][-1]
    d_right = drivers[-1]
    cy, cz, R = -2.01, 2.035, 0.07
    cx = (jxr + d_right[1]) / 2 + 0.02
    lead = spline([V(jxr + 0.03, C.Y0 - 0.14 - 0.045, 2.20), V(jxr + 0.06, -1.95, 2.18), V(cx - 0.11, cy + 0.006, cz + R + 0.02),
                   V(cx, cy + 0.012, cz + R)])
    coil = [V(cx + R * math.sin(a), cy + 0.012 - 0.024 * a / (4 * math.pi), cz + R * math.cos(a))
            for a in [4 * math.pi * k / 48 for k in range(1, 49)]]
    tail = spline([V(cx, cy - 0.012, cz + R), V(cx + 0.11, cy - 0.006, cz + R + 0.01), V(d_right[1] - 0.06, -2.01, 2.15),
                   V(d_right[1] - 0.012, -2.01, CB - 0.06 - 0.035)])
    run(m, "service_coil", lead + coil + tail[1:], 0.0085, "Cable_Black", raw=True)
    for zz in (cz + R, cz - R):
        obox(m, V(cx, cy, zz), X, Y, UP, 0.012, 0.05, 0.026, "Rubber_Black")  # ties holding the turns
    geo.cylinder(m, (d_right[1] - 0.006, -2.01, CB - 0.06 - 0.035), 0.012, 0.016, "Rubber_Black", axis="X", segments=10)

    # The 24h lantern: its feed leaves the trunk's end box, drapes over the drain run, and drops
    # into the cap of the lantern's pole
    lr_ = C.LANTERN_R
    pole = V(lr_["x"] + 0.12, lr_["y"], lr_["z"] + lr_["h"] / 2 + 0.16)
    dr = U["drain"]
    run(m, "lantern_r_feed", [end + V(0.074, 0.0, 0.0), end + V(0.13, -0.02, -0.005), V(dr["x"], -2.0, dr["run_z"] + dr["r"] + 0.012),
                              V(dr["x"] + 0.05, -2.02, dr["run_z"] + dr["r"]), V(pole.x - 0.03, pole.y + 0.04, pole.z + 0.08), V(pole.x, pole.y, pole.z + 0.03), V(pole.x, pole.y, pole.z - 0.01)],
        0.007, "Cable_Black", flex=True)
    geo.cylinder(m, (pole.x, pole.y, pole.z + 0.01), 0.028, 0.03, "Steel_Dark", segments=12)  # weather cap


# ---- Drainage ----------------------------------------------------------------------------------

def drainage(m):
    """Front-right: the canopy's edge box drains through an outlet under the front edge beam, a short
    run back under the soffit, a cast downpipe on the window bay's corner, a shoe onto a splash block.
    Back-left: the old downpipe gets a soffit collar and a cleanout."""
    F, d = "front", U["drain"]
    x, w, r = d["x"], d["w"], d["r"]
    yw = C.Y0 - w
    zr = d["run_z"]
    sw_, sz = d["shoe"]
    path = run(m, "drain", [V(x, d["outlet_y"], C.FASCIA_Z0 + 0.006), V(x, d["outlet_y"], zr), V(x, yw, zr), V(x, yw, 0.40),
                            V(x, C.Y0 - sw_, sz)], r, "Pipe_Cast", bend=0.09)
    X = Vector((1.0, 0.0, 0.0))
    obox(m, V(x, d["outlet_y"], C.FASCIA_Z0 - 0.006), X, Vector((0, 1, 0)), UP, 0.13, 0.13, 0.012, "Pipe_Cast")  # outlet flange
    ring(m, V(x, d["outlet_y"], C.FASCIA_Z0 - 0.03), UP, r + 0.012, 0.035, "Pipe_Cast")
    for zz in (1.72, 1.08):  # socket joints on the downpipe
        ring(m, V(x, yw, zz), UP, r + 0.009, 0.06, "Pipe_Cast")
    ring(m, V(x, (d["outlet_y"] + yw) / 2, zr), Vector((0, 1, 0)), r + 0.009, 0.06, "Pipe_Cast")
    for zz in (1.86, 1.30, 0.74):  # bracket bands bolted back to the bay post / corner angle
        clamp_wall(m, F, [(x, zz)], w, [r + 0.004], "z", "Steel_Dark")
    hanger(m, V(x, -2.20, zr), Vector((0, 1, 0)), r, CB, "Steel_Dark")  # clear of the tube end and the lantern feed
    # cleanout: a short stub with a square-headed plug, facing the camera side
    zc = 0.60
    geo.pipe(m, V(x, yw, zc), V(x - 0.075, yw, zc), r * 0.7, "Pipe_Cast", 12)
    geo.pipe(m, V(x - 0.075, yw, zc), V(x - 0.085, yw, zc), r * 0.8, "Pipe_Cast", 12)
    obox(m, V(x - 0.092, yw, zc), X, Vector((0, 1, 0)), UP, 0.012, 0.03, 0.03, "Steel_Dark")
    p, t = at(path, -0.01)
    ring(m, p, t, r + 0.006, 0.02, "Pipe_Cast")  # lip of the shoe
    geo.pipe(m, p - t * 0.03, p - t * 0.026, r - 0.004, "Rubber_Black", 14)
    obox(m, V(x - 0.02, C.Y0 - sw_ - 0.04, PH + 0.015), X, Vector((0, 1, 0)), UP, 0.14, 0.22, 0.03, "Platform_Concrete")  # splash block

    # the older back-left downpipe (clutter.downpipe): collar where it leaves the soffit, a cleanout
    ox, oy = C.X0 - 0.11, C.Y1 + 0.11
    ring(m, V(ox, oy, CB - 0.03), UP, 0.05, 0.06, "Steel_Galvanised")
    obox(m, V(ox, oy, CB - 0.004), X, Vector((0, 1, 0)), UP, 0.14, 0.14, 0.008, "Steel_Dark")
    geo.pipe(m, V(ox, oy, 0.80), V(ox - 0.07, oy, 0.80), 0.026, "Steel_Galvanised", 12)
    geo.pipe(m, V(ox - 0.07, oy, 0.80), V(ox - 0.08, oy, 0.80), 0.03, "Steel_Dark", 12)


# ---- Roof ---------------------------------------------------------------------------------------

def roof_lines(m):
    """Installed at different times, so not every unit is equally connected: a disconnect switch on
    the HVAC's front (seen from the floor camera) with its conduit up from a roof boot and a flex whip
    into the unit, an insulated refrigerant pair from the condenser's side round into the HVAC's back,
    a condensate line to a splash pad, and the mast's coax down the pole and across the platform into
    the white box.
    Roof pass (brief 4): the routes are the utility pass's, re-anchored on the regrouped equipment."""
    X, Y = Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0))
    deck = C.CANOPY_TOP
    b = roof.boxes()
    _, hcx, hcy, hw, hd, hh = b["TallCabinet"]  # the HVAC
    hz0 = roof.item_z("TallCabinet") + 0.04  # cabinet body bottom (roof.cabinet)
    hx0, hx1, hy0 = hcx - hw / 2, hcx + hw / 2, hcy - hd / 2

    ds = U["roof_disconnect"]
    x0, x1, z0, z1, dd = ds["x0"], ds["x1"], ds["z0"], ds["z1"], ds["d"]
    c = V((x0 + x1) / 2, hy0 - dd / 2, (z0 + z1) / 2)
    jbox(m, c, X, UP, x1 - x0, z1 - z0, dd, "Steel_Grey", "Steel_Grey")  # cover faces -Y (the camera side)
    obox(m, c + V(0.0, -dd / 2 - 0.02, 0.03), UP, X, Vector((0, -1, 0)), 0.09, 0.02, 0.03, "Stock_Red")  # handle
    obox(m, c + V(-0.04, -dd / 2 - 0.007, -0.07), X, UP, Vector((0, -1, 0)), 0.06, 0.035, 0.003, "Stock_Yellow")  # label
    rx, ry = ds["riser"]
    side, sgn = (x1, 1.0) if rx > x1 else (x0, -1.0)  # the conduit enters the switch's nearer side
    run(m, "roof_disconnect_feed", [V(rx, ry, deck - 0.01), V(rx, ry, z0 + 0.08), V(side - sgn * 0.006, ry, z0 + 0.08)], 0.014,
        "Conduit_Painted", bend=0.05)
    geo.lathe(m, (rx, ry, deck), [(0.045, 0.0), (0.04, 0.02), (0.022, 0.07), (0.018, 0.08)], "Rubber_Black", 16)  # roof boot
    ring(m, V(side + sgn * 0.008, ry, z0 + 0.08), X, 0.02, 0.016, "Steel_Dark")
    run(m, "roof_disconnect_whip", [V(c.x + 0.03, c.y, z0 + 0.006), V(c.x + 0.03, c.y - 0.01, z0 - 0.08), V(c.x - 0.01, c.y + 0.02, z0 - 0.17),
                                    V(c.x - 0.04, hy0 - 0.03, z0 - 0.19), V(c.x - 0.04, hy0 + 0.006, z0 - 0.19)],
        0.011, "Cable_Black", flex=True, rib=(0.014, 0.14))

    # refrigerant pair: suction (lagged) and liquid (copper) out of the condenser's right side, across,
    # and forward into the HVAC's back (the condenser stands right behind it along the left edge)
    _, acx, acy, aw, ad, ah = b["ACCondenser"]
    az = roof.item_z("ACCondenser")
    ax1 = acx + aw / 2
    hy1 = hcy + hd / 2
    for k, (oy, oz, xo, r, mat) in enumerate(((0.0, 0.0, -0.04, 0.028, "Insulation_Black"), (0.09, -0.08, 0.02, 0.009, "Copper_Aged"))):
        ys, zs, xe = hy1 + 0.30 + oy, az + 0.42 + oz, ax1 + 0.10 + xo
        run(m, f"refrigerant_{k}", [V(ax1 - 0.006, ys, zs), V(xe, ys, zs), V(xe, ys, zs + 0.10), V(xe, hy1 + 0.10, zs + 0.10),
                                    V(xe, hy1 - 0.006, zs + 0.10)], r, mat, bend=0.06)
        ring(m, V(ax1 + 0.012, ys, zs), X, r + 0.008, 0.024, "Steel_Dark")
    obox(m, V(ax1 + 0.012, hy1 + 0.36, az + 0.25), Y, UP, X, 0.18, 0.07, 0.024, "Steel_Dark")  # service valve block

    # condensate: out of the HVAC's +X side near the bottom, down to the deck, to a splash pad
    zc = hz0 + 0.06
    run(m, "condensate", [V(hx1 - 0.006, hcy + 0.30, zc), V(hx1 + 0.08, hcy + 0.30, zc), V(hx1 + 0.08, hcy + 0.30, deck + 0.03),
                          V(hx1 + 0.36, hcy + 0.30, deck + 0.03)], 0.012, "Hose_Grey", bend=0.04)
    obox(m, V(hx1 + 0.44, hcy + 0.30, deck + 0.012), X, Y, UP, 0.22, 0.16, 0.024, "Platform_Concrete")

    # mast coax: out of the instrument box's gland, taped down the pole's street side, across the
    # platform and into the gland on the white box's back
    mt = C.MAST
    g = roof.mast_gland()
    zp = roof.base_z(mt["cx"], mt["cy"])
    _, wx, wy, ww, wd, wh = b["WhiteBox"]
    wz = roof.item_z("WhiteBox")
    ly, lx = mt["cy"] - mt["w"] / 2 - 0.012, mt["cx"] + 0.016  # beside the street-side base gusset
    run(m, "mast_coax", [V(g.x, g.y, g.z - 0.004), V(g.x + 0.01, g.y + 0.02, g.z - 0.06), V(lx, ly, g.z - 0.12),
                         V(lx, ly, zp + 0.10), V(lx, ly - 0.10, zp + 0.045), V(lx - 0.02, wy + wd / 2 + 0.06, zp + 0.04),
                         V(wx + 0.01, wy + wd / 2 + 0.04, wz + 0.09), V(wx, wy + wd / 2 + 0.024, wz + 0.12)], 0.006, "Cable_Black", flex=True)
    for zz in (zp + 0.15, zp + 0.22):  # tape round the coax and the pole
        geo.pipe(m, V(mt["cx"] - 0.02, ly - 0.004, zz), V(lx + 0.014, ly - 0.004, zz), 0.009, "Rubber_Black", 6)


def roof_drapes(m):
    """Cables from the roof machinery over the canopy edge (from roof.py, step 4). They used to hang
    across the lettering and end in mid-air; now they go over the coping at the blank ends of the lit
    faces, down the face, under the edge beam and into the sign circuit: the back box feeds the
    lantern box, the corner box a pull elbow on the front fascia conduit."""
    b = roof.boxes()
    out = C.FASCIA["cap_proud"] + 0.02
    lx, fy, top = C.CANOPY_X0 - out, C.CANOPY_Y0 - out, C.CANOPY_TOP + 0.03
    below = C.FASCIA_Z0 - 0.03
    fb = fascia_boxes()

    _, bx, by, bw, bd, bh = b["BackBox_B"]
    lb, lsx, _, _ = fb["lantern"]
    y = lb.y + 0.10  # past the end of the left lettering (CANOPY_TEXT_LEFT y0)
    run(m, "drape_backbox", [V(bx - bw / 2 + 0.006, by + 0.08, roof.item_z("BackBox_B") + 0.22), V(bx - bw / 2 - 0.12, by + 0.02, top + 0.06),
                             V(lx + 0.03, y + 0.02, top + 0.012), V(lx - 0.012, y, top - 0.08), V(lx - 0.02, y - 0.01, 2.45),
                             V(lx - 0.015, y - 0.03, below + 0.01), V(lx + 0.12, lb.y + 0.03, below - 0.035),
                             V(lb.x - lsx / 2 + 0.006, lb.y, lb.z - 0.005)], 0.01, "Cable_Black", flex=True)

    # roof pass: the corner box is gone (the HVAC took the corner), so this cable now leaves the HVAC's
    # curb through a gland; the drop down the fascia and the pull elbow are unchanged
    _, cx0, cx1, cy0, cy1, _ = C.ROOF_CURBS[0]
    xd = -2.885  # left of "coffee" (CANOPY_TEXT_FRONT x0)
    fc = U["fascia_conduit"]
    pe = V(xd + 0.01, C.CANOPY_Y0 + fc["inset"] - fc["r"] - 0.022, fc["z"])
    obox(m, pe, Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0)), UP, 0.06, 0.05, 0.05, "Steel_Galv_Dull")  # pull elbow
    zg = C.CANOPY_TOP + 0.04  # low in the curb: the unit overhangs it a little
    ring(m, V(xd, cy0 - 0.012, zg), Vector((0.0, 1.0, 0.0)), 0.016, 0.026, "Steel_Dark")  # gland in the curb
    run(m, "drape_cornerbox", [V(xd, cy0 + 0.006, zg), V(xd + 0.01, cy0 - 0.09, C.CANOPY_TOP + 0.05),
                               V(xd + 0.02, fy + 0.03, top + 0.012), V(xd + 0.02, fy - 0.012, top - 0.08), V(xd + 0.025, fy - 0.02, 2.45),
                               V(xd + 0.02, fy - 0.015, below + 0.01), V(xd + 0.015, fy + 0.12, below - 0.03),
                               V(pe.x, pe.y - 0.019, pe.z)], 0.009, "Cable_Black", flex=True)


def build(coll, materials):
    geo.reseed(3303)
    RUNS.clear()
    m = geo.Mesh("Utilities")
    door_wall(m)
    front_wall(m)
    soffit(m)
    drainage(m)
    roof_lines(m)
    roof_drapes(m)
    ob = m.build(coll, materials)
    ob["runs"] = json.dumps(RUNS)
    return ob
