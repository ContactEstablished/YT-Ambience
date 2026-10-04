"""Shapes for the scripted flying vehicles (build_flying_vehicles.py), on top of kiosk/geo.Mesh.

Vehicles are built in their own frame: metres, +X forward, +Y left, +Z up, origin at the body centre.
"""
import math

from mathutils import Matrix, Vector


def _se(c, e):
    """Superellipse coordinate: sign(c) * |c|^(2/e)."""
    return math.copysign(abs(c) ** (2.0 / e), c)


def hull(mesh, stations, mat_fn, n=24, smooth=True):
    """Loft of superellipse cross-sections along X.

    stations: [(x, half_width, z_bottom, z_top, z_mid, e_top, e_bottom), ...] from tail to nose. A
    half_width of ~0 closes the end to a point. mat_fn(cx, cy, cz, nz) -> material for a face at
    its centre (nz = the face normal's z), so canopies and trim follow the shape."""
    rings = []
    for x, w, zb, zt, zm, et, eb in stations:
        ring = []
        for k in range(n):
            a = 2 * math.pi * k / n
            ca, sa = math.cos(a), math.sin(a)
            y = w * _se(ca, et if sa >= 0 else eb)
            z = zm + (zt - zm) * _se(sa, et) if sa >= 0 else zm + (zm - zb) * _se(sa, eb)
            ring.append(Vector((x, y, z)))
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(n):
            a, b = rings[i][k], rings[i][(k + 1) % n]
            c, d = rings[i + 1][(k + 1) % n], rings[i + 1][k]
            ctr = (a + b + c + d) / 4
            nrm = (c - a).cross(d - b)
            nz = nrm.normalized().z if nrm.length > 1e-9 else 0.0
            mesh.add_raw([a, d, c, b], [(0, 1, 2, 3)], mat_fn(ctr.x, ctr.y, ctr.z, nz), smooth)
    for ring, rev in ((rings[0], False), (rings[-1], True)):  # end caps (tiny when the end closes to a point)
        verts = list(reversed(ring)) if rev else ring
        ctr = sum(ring, Vector()) / len(ring)
        mesh.add_raw(verts, [tuple(range(len(verts)))], mat_fn(ctr.x, ctr.y, ctr.z, 0.0), smooth)


def torus(mesh, c, R, r, mat, axis="Z", Ry=None, seg=40, rseg=8, smooth=True):
    """Ring (elliptical when Ry is given). axis = the ring's axis: 'Z' lies flat, 'Y' stands up facing sideways."""
    Ry = R if Ry is None else Ry
    rot = {"Z": Matrix.Identity(3), "Y": Matrix.Rotation(math.radians(90), 3, "X"), "X": Matrix.Rotation(math.radians(90), 3, "Y")}[axis]
    verts, faces = [], []
    for i in range(seg):
        u = 2 * math.pi * i / seg
        p = Vector((R * math.cos(u), Ry * math.sin(u), 0.0))
        radial = Vector((Ry * math.cos(u), R * math.sin(u), 0.0)).normalized()  # outward normal of the ellipse
        for j in range(rseg):
            v = 2 * math.pi * j / rseg
            q = p + radial * (r * math.cos(v)) + Vector((0, 0, r * math.sin(v)))
            verts.append(Vector(c) + rot @ q)
    for i in range(seg):
        for j in range(rseg):
            a = i * rseg + j
            b = i * rseg + (j + 1) % rseg
            cc = ((i + 1) % seg) * rseg + (j + 1) % rseg
            d = ((i + 1) % seg) * rseg + j
            faces.append((a, d, cc, b))
    mesh.add_raw(verts, faces, mat, smooth)


def stadium_path(c, length, width, seg=12):
    """Closed racetrack outline (flat, in XY) centred at c: straight sides along X, round ends."""
    r = width / 2
    half = max(0.0, length / 2 - r)
    pts = []
    for sx, a0 in ((half, -math.pi / 2), (-half, math.pi / 2)):
        for k in range(seg + 1):
            a = a0 + math.pi * k / seg
            pts.append(Vector((c[0] + sx + r * math.cos(a), c[1] + r * math.sin(a), c[2])))
    return pts


def tube_loop(mesh, pts, r, mat, rseg=6, smooth=True):
    """Tube of radius r swept round a closed flat polyline (lift rails)."""
    n = len(pts)
    verts, faces = [], []
    for i in range(n):
        t = (pts[(i + 1) % n] - pts[i - 1]).normalized()
        side = t.cross(Vector((0, 0, 1))).normalized()
        for j in range(rseg):
            v = 2 * math.pi * j / rseg
            verts.append(pts[i] + side * (r * math.cos(v)) + Vector((0, 0, r * math.sin(v))))
    for i in range(n):
        for j in range(rseg):
            a, b = i * rseg + j, i * rseg + (j + 1) % rseg
            c, d = ((i + 1) % n) * rseg + (j + 1) % rseg, ((i + 1) % n) * rseg + j
            faces.append((a, b, c, d))
    mesh.add_raw(verts, faces, mat, smooth)


def flat_poly(mesh, pts, mat, down=True):
    """One flat n-gon through pts (facing down by default: seen from below)."""
    pts = [Vector(p) for p in pts]
    mesh.add_raw(list(reversed(pts)) if down else pts, [tuple(range(len(pts)))], mat, False)


def ellipse_pts(c, rx, ry, seg=32):
    return [Vector((c[0] + rx * math.cos(2 * math.pi * k / seg), c[1] + ry * math.sin(2 * math.pi * k / seg), c[2])) for k in range(seg)]


def lift_ring(mesh, c, R, r, Ry=None, ring_mat="Veh_Lift_Cyan", inner_mat="Veh_Lift_Dark", seg=40):
    """A glowing levitation ring with a dark recessed centre, seen from below."""
    Ry = R if Ry is None else Ry
    torus(mesh, c, R, r, ring_mat, "Z", Ry, seg)
    flat_poly(mesh, ellipse_pts((c[0], c[1], c[2] + r * 0.3), R - r * 0.6, Ry - r * 0.6, seg), inner_mat)


def mist_disc(mesh, c, rx, ry, seg=24):
    """Flat glow card under a lift ring (Unreal swaps in a soft additive radial-gradient material)."""
    flat_poly(mesh, ellipse_pts(c, rx, ry, seg), "Veh_LiftMist")


def lathe_scaled(mesh, profile, segs, sx, sy, mat_fn, smooth=False):
    """Surface of revolution about Z (profile [(r, z)] bottom to top), stretched by sx/sy: faceted gems."""
    rings = [[Vector((r * math.cos(2 * math.pi * k / segs) * sx, r * math.sin(2 * math.pi * k / segs) * sy, z)) for k in range(segs)]
             for r, z in profile]
    for i in range(len(rings) - 1):
        for k in range(segs):
            a, b = rings[i][k], rings[i][(k + 1) % segs]
            c, d = rings[i + 1][(k + 1) % segs], rings[i + 1][k]
            ctr = (a + b + c + d) / 4
            mesh.add_raw([a, b, c, d], [(0, 1, 2, 3)], mat_fn(ctr.x, ctr.y, ctr.z), smooth)
    mesh.add_raw(list(reversed(rings[0])), [tuple(range(segs))], mat_fn(0, 0, profile[0][1]), smooth)
    mesh.add_raw(rings[-1], [tuple(range(segs))], mat_fn(0, 0, profile[-1][1]), smooth)
