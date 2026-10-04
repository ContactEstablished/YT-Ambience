"""Builds the six flying-vehicle types (docs/FlyingVehicles) and exports Unreal/RawContent/flying_vehicles.glb.

    blender -b --factory-startup -P build_flying_vehicles.py -- [--render]

Each vehicle is its own mesh, origin at the body centre, facing +X, Z up, real size in metres:
  SM_Veh_Courier         1.6 x 1.3 m faceted dark gem, one cyan lift ring underneath, red nav lights
  SM_Veh_Taxi            5.2 x 2.2 m streamlined cab, continuous smoked canopy with a warm-lit cabin,
                         two racetrack lift rails underneath
  SM_Veh_Pod             asymmetric commuter pod: egg cabin beside a tall hollow ring (cyan inner edge)
  SM_Veh_Transit         16 x 4.4 m aerial bus, rows of dim windows, two long lift rails
  SM_Veh_Cargo           10 x 5.6 m industrial lifter, four corner lift nodes, clamps, markings
  SM_Veh_CargoContainer  container on four 5 m cables, origin at the cable anchors (it swings about there)
  SM_Veh_Hero            7.2 x 3.6 m flattened teardrop, slim canopy, a huge elliptical lift aperture
Materials named Veh_* (Unreal sets emissive strengths and swaps Veh_LiftMist / Veh_Nav_Red for its own).
--render writes Blender/renders/vehicles_check.png (one low three-quarter view per vehicle).
"""
import math
import os
import random
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_kiosk_blockout as B  # noqa: E402
from build_city import make_mat  # noqa: E402
from kiosk import geo  # noqa: E402
from vehicles import shapes as V  # noqa: E402

BLENDER_DIR = os.path.dirname(HERE)
RAW = os.path.join(os.path.dirname(BLENDER_DIR), "Unreal", "RawContent")
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

MATS = {  # rgb, roughness, metallic, emission (Blender preview strength)
    "Veh_Body_Graphite": ((0.030, 0.032, 0.037), 0.28, 0.65, 0.0),
    "Veh_Body_Ceramic": ((0.016, 0.017, 0.019), 0.16, 0.2, 0.0),
    "Veh_Body_Industrial": ((0.045, 0.045, 0.043), 0.55, 0.5, 0.0),
    "Veh_Trim": ((0.30, 0.32, 0.35), 0.3, 1.0, 0.0),
    "Veh_Glass_Smoked": ((0.008, 0.010, 0.013), 0.05, 0.0, 0.0),
    "Veh_Glass_Lit": ((0.05, 0.035, 0.022), 0.08, 0.0, 0.6),  # smoked glass over a warm-lit cabin
    "Veh_Lift_Cyan": ((0.55, 0.92, 1.0), 0.3, 0.0, 6.0),
    "Veh_Lift_Hero": ((0.70, 0.95, 1.0), 0.3, 0.0, 9.0),
    "Veh_Lift_Dark": ((0.0, 0.0, 0.0), 0.9, 0.0, 0.0),
    "Veh_Nav_Red": ((1.0, 0.05, 0.03), 0.3, 0.0, 12.0),
    "Veh_Nav_White": ((0.95, 0.97, 1.0), 0.3, 0.0, 10.0),
    "Veh_Accent_Cyan": ((0.35, 0.9, 1.0), 0.3, 0.0, 4.0),
    "Veh_Window_Warm": ((1.0, 0.82, 0.6), 0.3, 0.0, 2.5),
    "Veh_Window_Dim": ((0.9, 0.85, 0.75), 0.3, 0.0, 0.9),
    "Veh_Marking_Amber": ((1.0, 0.6, 0.15), 0.4, 0.0, 2.0),
    "Veh_Cable": ((0.02, 0.02, 0.02), 0.5, 0.8, 0.0),
    "Veh_LiftMist": ((0.4, 0.8, 1.0), 0.5, 0.0, 0.4),
}


# ---- 01 Courier drone ---------------------------------------------------------------------
def courier(m):
    prof = [(0.36, -0.105), (0.55, -0.095), (0.66, -0.03), (0.66, 0.0), (0.56, 0.08), (0.38, 0.22), (0.2, 0.31), (0.04, 0.34)]

    def mat(x, y, z):
        return "Veh_Glass_Smoked" if z > 0.17 else ("Veh_Body_Ceramic" if z > -0.02 else "Veh_Body_Graphite")
    V.lathe_scaled(m, prof, 8, 1.2, 1.0, mat)  # 8 facets with a vertex forward: a flattened diamond
    V.lift_ring(m, (0.0, 0.0, -0.11), 0.42, 0.032)
    for s in (-1, 1):
        geo.box(m, -0.04, 0.04, s * 0.62 - 0.04, s * 0.62 + 0.04, -0.03, 0.03, "Veh_Nav_Red")
        geo.box(m, -0.62, -0.42, s * 0.16 - 0.01, s * 0.16 + 0.01, 0.02, 0.17, "Veh_Body_Graphite")  # stabiliser fins
    geo.box(m, 0.74, 0.79, -0.05, 0.05, -0.05, -0.01, "Veh_Glass_Smoked")  # forward sensor
    geo.box(m, 0.785, 0.795, -0.015, 0.015, -0.04, -0.02, "Veh_Accent_Cyan")
    V.mist_disc(m, (0.0, 0.0, -0.5), 0.6, 0.6)


# ---- 02 Air taxi --------------------------------------------------------------------------
def taxi(m):
    L, W = 2.6, 1.1
    st = []
    for i in range(17):
        x = -L + 2 * L * i / 16
        xn = x / L
        w = max(0.03, W * (1 - abs(xn) ** 2.4) ** (1 / 2.4))
        zb = -0.42 + 0.18 * xn ** 2
        hump = max(0.0, 1 - ((x + 0.25) / 2.55) ** 2) ** 0.7
        zt = -0.1 + 0.85 * hump
        st.append((x, w, zb, max(zt, zb + 0.06), -0.12 + 0.04 * xn, 2.3, 3.2))

    def mat(x, y, z, nz):
        belt = 0.12 + 0.05 * (x / L)
        if z > belt and -1.95 < x < 2.05:
            return "Veh_Glass_Lit"
        return "Veh_Body_Graphite" if z > -0.25 else "Veh_Body_Ceramic"
    V.hull(m, st, mat)
    for s in (-1, 1):  # lift rails: housings + racetrack rings underneath
        geo.rounded_box(m, -1.65, 1.95, s * 0.55 - 0.32, s * 0.55 + 0.32, -0.56, -0.36, "Veh_Body_Ceramic", "Z", 0.3, 4)
        V.tube_loop(m, V.stadium_path((0.15, s * 0.55, -0.57), 3.4, 0.5), 0.045, "Veh_Lift_Cyan")
        V.flat_poly(m, V.stadium_path((0.15, s * 0.55, -0.565), 3.3, 0.4), "Veh_Lift_Dark")
        V.mist_disc(m, (0.15, s * 0.55, -1.0), 1.8, 0.35)
        geo.box(m, -1.6, 1.85, s * 1.05 - 0.01, s * 1.05 + 0.01, -0.2, -0.16, "Veh_Accent_Cyan")  # side line
        geo.box(m, 2.5, 2.56, s * 0.55 - 0.1, s * 0.55 + 0.1, -0.16, -0.1, "Veh_Nav_White")
        geo.box(m, -2.6, -2.54, s * 0.62 - 0.12, s * 0.62 + 0.12, -0.05, 0.02, "Veh_Nav_Red")
    geo.box(m, -2.2, 1.6, -0.02, 0.02, 0.73, 0.76, "Veh_Trim")  # roof spine


# ---- 03 Commuter pod ----------------------------------------------------------------------
def pod(m):
    st = []
    for i in range(13):
        x = -1.3 + 2.6 * i / 12
        xn = x / 1.3
        f = max(0.02, (1 - abs(xn) ** 2.2) ** (1 / 2.2))
        st.append((x, 0.68 * f, -0.78 * f, 0.8 * f, 0.0, 2.2, 2.4))

    def mat(x, y, z, nz):
        if x > 0.15 and -0.35 < z < 0.65:
            return "Veh_Glass_Lit"
        return "Veh_Body_Ceramic" if z > 0 else "Veh_Body_Graphite"
    shifted = geo.Mesh("tmp")
    V.hull(shifted, st, mat)
    for v in shifted.verts:
        v.y += 0.4
    for f, mi in zip(shifted.faces, shifted.face_mat):
        m.add_raw([shifted.verts[i] for i in f], [tuple(range(len(f)))], shifted.mats[mi], True)
    yc = -1.1  # the hollow levitation ring beside the cabin, standing up, axis sideways
    V.torus(m, (0.0, yc, 0.0), 1.18, 0.16, "Veh_Body_Ceramic", "Y", seg=48, rseg=10)
    V.torus(m, (0.0, yc + 0.0, 0.0), 1.0, 0.03, "Veh_Lift_Cyan", "Y", seg=48, rseg=6)  # inner edge glow
    for a in (150.0, 210.0):  # struts from the cabin's rear flank to the ring's rear arc: the opening stays clear
        ra = math.radians(a)
        rx, rz = 1.18 * math.cos(ra), 1.18 * math.sin(ra)
        geo.pipe(m, (rx + 0.25, -0.2, rz * 0.75), (rx, yc + 0.1, rz), 0.09, "Veh_Body_Graphite")
    geo.box(m, -0.95, -0.55, -0.32, -0.18, -0.45, 0.45, "Veh_Body_Graphite", bevel=0.05)  # hub plate on the cabin
    geo.box(m, -0.05, 0.05, 0.35, 0.45, 0.8, 0.86, "Veh_Nav_Red")
    geo.box(m, -1.0, 0.9, 1.07, 1.09, -0.1, -0.07, "Veh_Accent_Cyan")
    geo.box(m, 1.27, 1.3, 0.25, 0.55, -0.3, -0.26, "Veh_Nav_White")
    V.mist_disc(m, (0.0, yc, -1.6), 0.7, 0.35)


# ---- 04 Aerial transit --------------------------------------------------------------------
def transit(m, rng):
    L, W = 8.0, 2.2
    st = []
    for i in range(25):
        x = -L + 2 * L * i / 24
        xn = x / L
        f = max(0.05, (1 - abs(xn) ** 9) ** (1 / 9))
        st.append((x, W * f, -1.55 + 0.35 * abs(xn) ** 8, 1.4 - 0.35 * abs(xn) ** 8, 0.0, 4.5, 4.5))

    def mat(x, y, z, nz):
        if abs(x) > 7.35 and -0.1 < z < 1.0:
            return "Veh_Glass_Smoked"
        return "Veh_Body_Graphite" if z > -0.6 else "Veh_Body_Ceramic"
    V.hull(m, st, mat)
    for s in (-1, 1):
        x = -6.3
        while x < 6.2:
            geo.box(m, x, x + 0.9, s * 2.2 - 0.03, s * 2.2 + 0.03, 0.12, 0.88, "Veh_Window_Warm" if rng.random() < 0.7 else "Veh_Window_Dim")
            x += 1.2
        geo.box(m, -6.8, 6.8, s * 2.21 - 0.02, s * 2.21 + 0.02, -0.62, -0.56, "Veh_Accent_Cyan")
        V.tube_loop(m, V.stadium_path((0.0, s * 1.15, -1.6), 11.0, 0.7), 0.07, "Veh_Lift_Cyan")
        V.flat_poly(m, V.stadium_path((0.0, s * 1.15, -1.595), 10.9, 0.56), "Veh_Lift_Dark")
        V.mist_disc(m, (0.0, s * 1.15, -2.5), 5.5, 0.6)
        geo.box(m, 7.95, 8.02, s * 1.6 - 0.15, s * 1.6 + 0.15, -0.9, -0.75, "Veh_Nav_White")
        geo.box(m, -8.02, -7.95, s * 1.7 - 0.15, s * 1.7 + 0.15, -0.9, -0.75, "Veh_Nav_Red")
    for x in (-5.0, 5.0):
        geo.box(m, x - 0.1, x + 0.1, -0.1, 0.1, 1.38, 1.5, "Veh_Nav_Red")


# ---- 05 Cargo lifter ----------------------------------------------------------------------
CARGO_ANCHOR_Z = -1.25  # the cable anchors under the lifter; SM_Veh_CargoContainer's origin goes here


def cargo(m, rng):
    geo.box(m, -5.0, 5.0, -2.8, 2.8, -0.9, 0.9, "Veh_Body_Industrial", bevel=0.25, segments=2)
    geo.box(m, -3.6, 3.4, -1.3, 1.3, 0.9, 1.55, "Veh_Body_Industrial", bevel=0.12)  # spine
    geo.box(m, 3.5, 4.8, -1.0, 1.0, 0.9, 1.75, "Veh_Body_Graphite", bevel=0.15)  # control module
    geo.box(m, 4.82, 4.86, -0.7, 0.7, 1.25, 1.55, "Veh_Glass_Lit")
    for x in (-2.8, -1.4, 0.0, 1.4):  # equipment boxes and tanks on the spine
        if rng.random() < 0.75:
            geo.box(m, x - 0.5, x + 0.5, -0.9 + rng.uniform(0, 0.6), 0.2 + rng.uniform(0, 0.6), 1.55, 1.55 + rng.uniform(0.3, 0.8),
                    "Veh_Body_Graphite", bevel=0.05)
    for s in (-1, 1):
        for x in (-3.0, -1.0, 1.0, 3.0):  # side reinforcement ribs
            geo.box(m, x - 0.12, x + 0.12, s * 2.8 - 0.06, s * 2.8 + 0.06, -0.8, 0.8, "Veh_Body_Graphite")
        geo.box(m, -4.2, -3.4, s * 2.85 - 0.02, s * 2.85 + 0.02, 0.3, 0.55, "Veh_Marking_Amber")  # maintenance plates
        geo.box(m, 2.0, 2.4, s * 2.85 - 0.02, s * 2.85 + 0.02, 0.3, 0.42, "Veh_Marking_Amber")
        for sx in (-1, 1):
            cx, cy = sx * 3.6, s * 2.0  # corner lift nodes
            geo.cylinder(m, (cx, cy, -1.05), 1.2, 0.36, "Veh_Body_Graphite", segments=24)
            V.lift_ring(m, (cx, cy, -1.24), 0.95, 0.06, seg=32)
            V.mist_disc(m, (cx, cy, -1.9), 0.95, 0.95)
            geo.box(m, sx * 4.95 - 0.06, sx * 4.95 + 0.06, s * 2.7 - 0.06, s * 2.7 + 0.06, 0.7, 0.82, "Veh_Nav_Red")
            geo.box(m, sx * 2.4 - 0.2, sx * 2.4 + 0.2, s * 0.9 - 0.2, s * 0.9 + 0.2, CARGO_ANCHOR_Z, -0.9, "Veh_Body_Graphite")  # clamps
    geo.box(m, 4.95, 5.02, -0.3, 0.3, 0.0, 0.15, "Veh_Nav_White")


def container(m):
    """Hangs on four cables; origin at the anchor plane (swing pivot)."""
    top, bot = -5.0, -7.6
    geo.box(m, -3.0, 3.0, -1.25, 1.25, bot, top, "Veh_Body_Industrial", bevel=0.05)
    for s in (-1, 1):
        x = -2.7
        while x <= 2.71:
            geo.box(m, x - 0.05, x + 0.05, s * 1.25 - 0.04, s * 1.25 + 0.04, bot + 0.1, top - 0.1, "Veh_Body_Graphite")
            x += 0.6
        geo.box(m, -3.0, 3.0, s * 1.27 - 0.03, s * 1.27 + 0.03, top - 0.15, top, "Veh_Body_Graphite")
        for sx in (-1, 1):
            geo.pipe(m, (sx * 2.4, s * 0.9, 0.0), (sx * 2.6, s * 1.05, top), 0.035, "Veh_Cable")
            geo.box(m, sx * 2.95 - 0.06, sx * 2.95 + 0.06, s * 1.2 - 0.06, s * 1.2 + 0.06, top - 0.45, top - 0.3, "Veh_Marking_Amber")


# ---- 06 Hero vehicle ----------------------------------------------------------------------
def hero(m):
    st = []
    n = 21
    for i in range(n):
        x = -3.6 + 7.2 * i / (n - 1)
        if x >= 0.6:
            w = 1.8 * max(0.0, 1 - ((x - 0.6) / 3.0) ** 2) ** 0.5
        else:
            w = 1.8 * max(0.0, 1 - ((0.6 - x) / 4.25) ** 1.7) ** 0.75
        w = max(0.03, w)
        th = 0.55 * max(0.0, 1 - ((x - 0.4) / 3.7) ** 2) ** 0.6  # thickest just behind the middle
        st.append((x, w, -0.3 * max(0.15, th / 0.55), 0.05 + th, -0.05, 2.0, 4.0))

    def mat(x, y, z, nz):
        if 0.1 < x < 2.4 and abs(y) < 0.42 and z > 0.42:
            return "Veh_Glass_Smoked"
        return "Veh_Body_Ceramic"
    V.hull(m, st, mat, n=32)
    V.lift_ring(m, (0.15, 0.0, -0.31), 2.6, 0.07, Ry=1.22, ring_mat="Veh_Lift_Hero", seg=64)
    V.mist_disc(m, (0.15, 0.0, -1.3), 2.5, 1.15, seg=32)
    for s in (-1, 1):
        geo.box(m, 0.5, 0.7, s * 1.79 - 0.05, s * 1.79 + 0.05, -0.08, 0.0, "Veh_Nav_Red")
        geo.box(m, -2.6, 2.2, s * 1.55 - 0.01, s * 1.55 + 0.01, -0.12, -0.1, "Veh_Accent_Cyan")
    geo.box(m, -3.62, -3.55, -0.08, 0.08, -0.08, 0.0, "Veh_Nav_Red")
    geo.box(m, 3.55, 3.6, -0.1, 0.1, -0.06, -0.02, "Veh_Nav_White")


VEHICLES = {"SM_Veh_Courier": courier, "SM_Veh_Taxi": taxi, "SM_Veh_Pod": pod, "SM_Veh_Transit": transit,
            "SM_Veh_Cargo": cargo, "SM_Veh_CargoContainer": container, "SM_Veh_Hero": hero}


def main():
    B.reset_scene()
    for name, (rgb, r, mt, e) in MATS.items():
        make_mat(name, rgb, r, mt, e)
    coll = B.collection("FlyingVehicles")
    rng = random.Random(7)
    obs = {}
    for name, fn in VEHICLES.items():
        m = geo.Mesh(name)
        fn(m, rng) if fn in (transit, cargo) else fn(m)
        obs[name] = m.build(coll, bpy.data.materials)
        print(f"{name}: {len(obs[name].data.polygons)} faces")
    bpy.ops.object.select_all(action="DESELECT")
    for ob in obs.values():
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(RAW, "flying_vehicles.glb"), export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True, export_cameras=False, export_lights=False)
    print("exported flying_vehicles.glb")
    if "--render" in ARGV:
        render_sheet(obs)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLENDER_DIR, "flying_vehicles.blend"), check_existing=False)


def render_sheet(obs):
    """One low three-quarter view per vehicle (the shot looks up at them), composed into a 3 x 2 sheet."""
    from kiosk import review
    from mathutils import Vector
    scene = bpy.context.scene
    review._engine(scene)
    scene.view_settings.view_transform = "AgX"
    world = bpy.data.worlds.new("VehNight")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.03, 0.04, 1.0)
    scene.world = world
    for name, loc, energy, size in (("Key", (6, -4, 9), 1500, 6), ("Rim", (-8, 6, 3), 900, 5), ("Under", (2, -6, -6), 250, 6)):
        ld = bpy.data.lights.new(name, "AREA")
        ld.energy, ld.size = energy, size
        ld.color = (0.75, 0.85, 1.0)
        lo = bpy.data.objects.new(name, ld)
        lo.location = loc
        lo.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        scene.collection.objects.link(lo)
    mist = bpy.data.materials["Veh_LiftMist"]  # preview only: a faint see-through glow, like the Unreal material
    mist.surface_render_method = "BLENDED"
    mist.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.12
    obs["SM_Veh_CargoContainer"].location = (0, 0, CARGO_ANCHOR_Z)
    obs["SM_Veh_CargoContainer"].parent = obs["SM_Veh_Cargo"]
    rc = B.collection("Review")
    out = os.path.join(BLENDER_DIR, "renders")
    os.makedirs(out, exist_ok=True)
    views = {"SM_Veh_Courier": 2.6, "SM_Veh_Taxi": 8.5, "SM_Veh_Pod": 5.5, "SM_Veh_Transit": 24.0, "SM_Veh_Cargo": 20.0, "SM_Veh_Hero": 11.0}
    for name, ob in obs.items():
        ob.hide_render = True
    for name, dist in views.items():
        for n2, ob in obs.items():
            ob.hide_render = n2 not in (name, "SM_Veh_CargoContainer" if name == "SM_Veh_Cargo" else name)
        tgt = Vector((0, 0, -2.5 if name == "SM_Veh_Cargo" else 0))
        cam = review.look_camera(rc, f"CAM_{name}", tgt + Vector((0.75, -0.6, -0.28)).normalized() * dist, tgt, 40)
        review.render(scene, cam, os.path.join(out, f"veh_{name[7:]}.png"), res=(960, 540))


if __name__ == "__main__":
    main()
