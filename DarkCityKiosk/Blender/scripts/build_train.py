"""Builds the commuter train (city_config.TRAIN) and exports Unreal/RawContent/train.glb.

    blender -b --factory-startup -P build_train.py -- [--render]

Local frame: nose of the lead car at x = 0 facing +X, cars trailing toward -X, rail top at
z = 0, centred on y = 0. Three cars with rounded cabs at both ends, a band of lit windows
(some with passenger silhouettes), doors, a cyan accent strip, roof units, underframe,
bogies with wheels, gangways, headlights and tail lights.
"""
import math
import os
import random
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import city_config as CC  # noqa: E402
import build_kiosk_blockout as B  # noqa: E402
from build_city import make_mat  # noqa: E402
from kiosk import geo  # noqa: E402

T = CC.TRAIN
RNG = random.Random(T["seed"])
BLENDER_DIR = os.path.dirname(HERE)
RAW = os.path.join(os.path.dirname(BLENDER_DIR), "Unreal", "RawContent")
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

MATS = {  # rgb, roughness, metallic, emission
    "Train_Body": ((0.42, 0.44, 0.47), 0.32, 0.7, 0.0),
    "Train_Dark": ((0.02, 0.022, 0.025), 0.3, 0.3, 0.0),
    "Train_Glass": ((0.02, 0.03, 0.035), 0.05, 0.0, 0.0),
    "Train_Window_Lit": ((1.0, 0.93, 0.8), 0.3, 0.0, 6.0),
    "Train_Window_Dim": ((0.8, 0.85, 1.0), 0.3, 0.0, 2.0),
    "Train_Strip": ((0.3, 0.95, 1.0), 0.4, 0.0, 6.0),
    "Train_Head": ((1.0, 0.97, 0.9), 0.3, 0.0, 12.0),
    "Train_Tail": ((1.0, 0.05, 0.03), 0.3, 0.0, 8.0),
    "Train_Sign": ((1.0, 0.6, 0.15), 0.3, 0.0, 6.0),
}


def car(m, x_front, lead, tail):
    L, hw = T["car_len"], T["width"] / 2
    fz, rz = T["floor_z"], T["roof_z"]
    x0, x1 = x_front - L, x_front
    # body: rounded in cross-section; cab ends get a curved nose seen from the side
    body0 = x0 + (2.2 if tail else 0.0)
    body1 = x1 - (2.2 if lead else 0.0)
    geo.rounded_box(m, body0, body1, -hw, hw, fz, rz, "Train_Body", "X", 0.4, 4)
    if lead:
        geo.rounded_box(m, x1 - 3.2, x1, -hw + 0.05, hw - 0.05, fz, rz - 0.15, "Train_Body", "Y", 1.1, 6)
        geo.rounded_box(m, x1 - 1.05, x1 - 0.32, -hw + 0.35, hw - 0.35, 2.35, 3.45, "Train_Glass", "Y", 0.25, 3)  # windscreen
        geo.box(m, x1 - 1.0, x1 - 0.6, -hw + 0.5, hw - 0.5, 3.5, 3.72, "Train_Sign")  # destination sign
        for s in (-1, 1):
            geo.box(m, x1 - 0.18, x1 - 0.02, s * 0.95 - 0.18, s * 0.95 + 0.18, 1.25, 1.42, "Train_Head")
    if tail:
        geo.rounded_box(m, x0, x0 + 3.2, -hw + 0.05, hw - 0.05, fz, rz - 0.15, "Train_Body", "Y", 1.1, 6)
        geo.rounded_box(m, x0 + 0.32, x0 + 1.05, -hw + 0.35, hw - 0.35, 2.35, 3.45, "Train_Glass", "Y", 0.25, 3)
        for s in (-1, 1):
            geo.box(m, x0 + 0.02, x0 + 0.18, s * 0.95 - 0.18, s * 0.95 + 0.18, 1.25, 1.42, "Train_Tail")
    # window band, windows (some with passenger silhouettes), doors, accent strip on both sides
    a, b = x0 + (3.0 if tail else 1.0), x1 - (3.0 if lead else 1.0)
    doors = [a + (b - a) * 0.25, a + (b - a) * 0.75]
    for s in (-1, 1):
        y = s * hw
        geo.box(m, a, b, min(y, y + s * 0.02), max(y, y + s * 0.02), 1.95, 3.1, "Train_Dark")
        geo.box(m, x0 + 0.5, x1 - 0.5, min(y, y + s * 0.03), max(y, y + s * 0.03), 1.6, 1.68, "Train_Strip")
        x = a + 0.2
        while x + T["window_w"] < b:
            if all(abs(x + T["window_w"] / 2 - d) > 1.0 for d in doors):
                mat = "Train_Window_Lit" if RNG.random() < T["lit_fraction"] else "Train_Window_Dim"
                yy = (y + s * 0.02, y + s * 0.03)
                geo.box(m, x, x + T["window_w"], min(yy), max(yy), 2.05, 3.0, mat)
                if RNG.random() < T["silhouette_chance"]:  # head and shoulders against the light
                    cx = x + RNG.uniform(0.35, T["window_w"] - 0.35)
                    yy2 = (y + s * 0.03, y + s * 0.036)
                    geo.box(m, cx - 0.26, cx + 0.26, min(yy2), max(yy2), 2.05, 2.32, "Train_Dark", 0.0)
                    geo.cylinder(m, (cx, y + s * 0.033, 2.48), 0.12, 0.006, "Train_Dark", axis="Y", segments=12)
            x += T["window_every"]
        for d in doors:
            yy = (y + s * 0.02, y + s * 0.035)
            geo.box(m, d - 0.68, d + 0.68, min(yy), max(yy), fz + 0.05, 3.25, "Train_Dark")
            geo.box(m, d - 0.5, d + 0.5, min(y + s * 0.035, y + s * 0.04), max(y + s * 0.035, y + s * 0.04), 2.2, 3.0, "Train_Window_Dim")
    # roof units
    for k in (0.3, 0.7):
        cx = x0 + L * k
        geo.rounded_box(m, cx - 1.6, cx + 1.6, -0.9, 0.9, rz - 0.1, rz + 0.35, "Train_Body", "X", 0.15, 2)
    # underframe and bogies
    geo.box(m, x0 + 0.8, x1 - 0.8, -hw + 0.25, hw - 0.25, 0.35, fz, "Train_Dark")
    for k in (0.17, 0.83):
        cx = x0 + L * k
        geo.box(m, cx - 1.4, cx + 1.4, -1.2, 1.2, 0.25, 0.75, "Train_Dark", 0.03)
        for dx in (-0.9, 0.9):
            for s in (-1, 1):
                geo.cylinder(m, (cx + dx, s * 0.72, 0.42), 0.42, 0.12, "Rail_Steel" if False else "Train_Dark", axis="Y", segments=16)


def build(coll):
    for name, (rgb, r, mt, e) in MATS.items():
        make_mat(name, rgb, r, mt, e)
    m = geo.Mesh("SM_Train")
    n, L, gap = T["cars"], T["car_len"], T["gap"]
    for i in range(n):
        xf = -i * (L + gap)
        car(m, xf, lead=(i == 0), tail=(i == n - 1))
        if i > 0:  # gangway bellows
            geo.box(m, xf, xf + gap, -1.15, 1.15, T["floor_z"] + 0.1, T["roof_z"] - 0.3, "Train_Dark")
    return m.build(coll, bpy.data.materials)


def main():
    B.reset_scene()
    coll = B.collection("Train")
    ob = build(coll)
    print(f"train: {len(ob.data.polygons)} faces, length {T['cars'] * T['car_len'] + (T['cars'] - 1) * T['gap']:.1f} m")
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(RAW, "train.glb"), export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True, export_cameras=False, export_lights=False)
    print("exported train.glb")
    if "--render" in ARGV:
        from kiosk import review
        rc = B.collection("Review")
        cam = review.look_camera(rc, "CAM_Train", (8, -14, 3.2), (-14, 0, 2.0), 30)
        B.init_shared()
        scene = bpy.context.scene
        review.setup_scene(scene, rc, bpy.data.materials)
        review.render(scene, cam, os.path.join(BLENDER_DIR, "renders", "train_check.png"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLENDER_DIR, "train.blend"), check_existing=False)


if __name__ == "__main__":
    main()
