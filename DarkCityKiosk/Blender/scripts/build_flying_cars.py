"""Builds the flying-car variants and exports Unreal/RawContent/flying_cars.glb.

    blender -b --factory-startup -P build_flying_cars.py -- [--render]

Each variant is its own mesh, centred on its origin, facing +X:
  SM_Car_Spinner  sleek sedan, glass canopy, side pods, cyan running lights, blue underglow
  SM_Car_Taxi     boxy yellow sky-taxi with a lit window band and an amber roof sign
  SM_Car_Courier  small drone-car with four ducted fans and red/green navigation lights
  SM_Car_Skybus   long sky-bus with a band of lit windows and roof pods
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_kiosk_blockout as B  # noqa: E402
from build_city import make_mat  # noqa: E402
from kiosk import geo  # noqa: E402

BLENDER_DIR = os.path.dirname(HERE)
RAW = os.path.join(os.path.dirname(BLENDER_DIR), "Unreal", "RawContent")
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

MATS = {  # rgb, roughness, metallic, emission
    "Car_Body_Dark": ((0.05, 0.055, 0.065), 0.25, 0.8, 0.0),
    "Car_Body_Taxi": ((0.75, 0.52, 0.08), 0.3, 0.2, 0.0),
    "Car_Glass": ((0.02, 0.03, 0.04), 0.05, 0.0, 0.0),
    "Car_Light_Front": ((0.95, 0.97, 1.0), 0.3, 0.0, 15.0),
    "Car_Light_Rear": ((1.0, 0.05, 0.03), 0.3, 0.0, 10.0),
    "Car_Glow_Blue": ((0.25, 0.75, 1.0), 0.3, 0.0, 8.0),
    "Car_Glow_Amber": ((1.0, 0.62, 0.15), 0.3, 0.0, 8.0),
    "Car_Nav_Green": ((0.15, 1.0, 0.35), 0.3, 0.0, 10.0),
    "Car_Window_Lit": ((1.0, 0.9, 0.75), 0.3, 0.0, 5.0),
}


def spinner(m):
    geo.rounded_box(m, -2.6, 1.7, -1.1, 1.1, -0.45, 0.25, "Car_Body_Dark", "X", 0.3, 3)
    geo.rounded_box(m, 1.5, 2.85, -1.0, 1.0, -0.42, 0.12, "Car_Body_Dark", "Y", 0.35, 4)  # nose
    geo.rounded_box(m, -0.9, 1.15, -0.8, 0.8, 0.2, 0.78, "Car_Glass", "X", 0.35, 3)  # canopy
    for s in (-1, 1):
        geo.rounded_box(m, -2.3, -0.6, s * 1.05 - 0.22, s * 1.05 + 0.22, -0.32, 0.02, "Car_Body_Dark", "Y", 0.15, 2)  # pods
        geo.box(m, -2.4, 2.4, min(s * 1.1, s * 1.13), max(s * 1.1, s * 1.13), -0.06, -0.01, "Car_Glow_Blue")  # running light
    geo.box(m, 2.78, 2.86, -0.75, 0.75, -0.18, -0.1, "Car_Light_Front")
    geo.box(m, -2.66, -2.6, -0.95, 0.95, -0.06, 0.04, "Car_Light_Rear")
    geo.box(m, -2.0, 2.0, -0.85, 0.85, -0.48, -0.46, "Car_Glow_Blue")  # underglow
    geo.box(m, -2.5, -2.1, -0.04, 0.04, 0.2, 0.75, "Car_Body_Dark")  # tail fin


def taxi(m):
    geo.rounded_box(m, -2.8, 2.8, -1.2, 1.2, -0.6, 0.9, "Car_Body_Taxi", "X", 0.35, 3)
    geo.rounded_box(m, 2.2, 3.05, -1.1, 1.1, -0.55, 0.45, "Car_Body_Taxi", "Y", 0.35, 3)
    for s in (-1, 1):
        y = s * 1.2
        for k in range(4):
            x = -2.2 + k * 1.15
            geo.box(m, x, x + 0.9, min(y, y + s * 0.02), max(y, y + s * 0.02), 0.25, 0.72, "Car_Window_Lit" if k % 3 else "Car_Glass")
        geo.box(m, -2.7, 2.7, min(y, y + s * 0.03), max(y, y + s * 0.03), 0.05, 0.1, "Car_Glow_Amber")
    geo.box(m, 2.6, 2.75, -0.7, 0.7, 0.35, 0.75, "Car_Glass")  # windscreen
    geo.box(m, -0.45, 0.45, -0.28, 0.28, 0.9, 1.18, "Car_Glow_Amber")  # roof sign
    geo.box(m, 3.0, 3.08, -0.9, 0.9, -0.25, -0.12, "Car_Light_Front")
    geo.box(m, -2.86, -2.8, -1.0, 1.0, -0.1, 0.02, "Car_Light_Rear")
    geo.box(m, -2.2, 2.2, -0.9, 0.9, -0.63, -0.61, "Car_Glow_Amber")


def courier(m):
    geo.rounded_box(m, -1.4, 1.4, -0.6, 0.6, -0.3, 0.3, "Car_Body_Dark", "X", 0.25, 3)
    geo.rounded_box(m, 0.2, 1.3, -0.45, 0.45, 0.2, 0.5, "Car_Glass", "X", 0.2, 2)
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * 1.25, sy * 1.05
            geo.lathe(m, (cx, cy, -0.12), [(0.55, 0.0), (0.62, 0.0), (0.62, 0.24), (0.55, 0.24), (0.55, 0.0)], "Car_Body_Dark", 20,
                      cap_bottom=False, cap_top=False)
            geo.cylinder(m, (cx, cy, 0.0), 0.08, 0.1, "Car_Body_Dark", segments=10)
            geo.pipe(m, (cx * 0.55, cy * 0.5, 0.0), (cx, cy, 0.0), 0.05, "Car_Body_Dark", 6)
    geo.box(m, -0.1, 0.1, -0.68, -0.6, 0.0, 0.1, "Car_Light_Rear")  # port: red
    geo.box(m, -0.1, 0.1, 0.6, 0.68, 0.0, 0.1, "Car_Nav_Green")  # starboard: green
    geo.box(m, 1.38, 1.44, -0.3, 0.3, -0.12, -0.04, "Car_Light_Front")
    geo.box(m, -1.0, 1.0, -0.4, 0.4, -0.33, -0.31, "Car_Glow_Blue")


def skybus(m):
    geo.rounded_box(m, -6.0, 6.0, -1.4, 1.4, -1.1, 1.1, "Car_Body_Dark", "X", 0.55, 4)
    geo.rounded_box(m, 5.2, 6.6, -1.3, 1.3, -1.0, 0.9, "Car_Body_Dark", "Y", 0.7, 4)
    for s in (-1, 1):
        y = s * 1.4
        x = -5.4
        while x < 4.8:
            geo.box(m, x, x + 0.85, min(y, y + s * 0.02), max(y, y + s * 0.02), -0.05, 0.6, "Car_Window_Lit")
            x += 1.05
        geo.box(m, -5.8, 5.8, min(y, y + s * 0.03), max(y, y + s * 0.03), -0.35, -0.28, "Car_Glow_Blue")
    geo.box(m, 6.1, 6.55, -0.9, 0.9, 0.1, 0.65, "Car_Glass")
    geo.box(m, 6.55, 6.62, -1.0, 1.0, -0.55, -0.42, "Car_Light_Front")
    geo.box(m, -6.06, -6.0, -1.2, 1.2, -0.4, -0.25, "Car_Light_Rear")
    for k in (-3.0, 0.0, 3.0):
        geo.rounded_box(m, k - 1.0, k + 1.0, -0.7, 0.7, 1.05, 1.4, "Car_Body_Dark", "X", 0.12, 2)
    geo.box(m, -5.0, 5.0, -1.0, 1.0, -1.13, -1.11, "Car_Glow_Blue")


VARIANTS = {"SM_Car_Spinner": spinner, "SM_Car_Taxi": taxi, "SM_Car_Courier": courier, "SM_Car_Skybus": skybus}


def main():
    B.reset_scene()
    for name, (rgb, r, mt, e) in MATS.items():
        make_mat(name, rgb, r, mt, e)
    coll = B.collection("FlyingCars")
    obs = []
    for i, (name, fn) in enumerate(VARIANTS.items()):
        m = geo.Mesh(name)
        fn(m)
        ob = m.build(coll, bpy.data.materials)
        obs.append(ob)
        print(f"{name}: {len(ob.data.polygons)} faces")
    bpy.ops.object.select_all(action="DESELECT")
    for ob in obs:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(RAW, "flying_cars.glb"), export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True, export_cameras=False, export_lights=False)
    print("exported flying_cars.glb")
    if "--render" in ARGV:
        from kiosk import review
        for i, ob in enumerate(obs):  # line them up for a look
            ob.location = (0, i * 5.0 - 7.5, 2.0)
        B.init_shared()
        rc = B.collection("Review")
        scene = bpy.context.scene
        review.setup_scene(scene, rc, bpy.data.materials)
        cam = review.look_camera(rc, "CAM_Cars", (11, -12, 5.5), (0, 0, 2.0), 35)
        review.render(scene, cam, os.path.join(BLENDER_DIR, "renders", "cars_check.png"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLENDER_DIR, "flying_cars.blend"), check_existing=False)


if __name__ == "__main__":
    main()
