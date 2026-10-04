"""Builds the umbrella variants and exports Unreal/RawContent/umbrellas.glb.

    blender -b --factory-startup -P build_umbrella.py -- [--render]

Each variant is its own mesh with the GRIP at the origin (where the fist closes round the
handle) and the shaft along +Z, so Unreal attaches it straight to the hand_r bone. Eight ribs,
taut panels between them with a little wet sag, a second shell under the canopy (the camera
sits on the floor and sees the underside), ribs and stretchers underneath, a J-hook handle.
  SM_Umbrella_Black / _Navy / _Red   plain fabric
  SM_Umbrella_Clear                  clear PVC (Tokyo convenience-store umbrella)
  SM_Umbrella_LED                    black, with a glowing shaft (Blade Runner)
"""
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_kiosk_blockout as B  # noqa: E402
from build_city import make_mat  # noqa: E402
from kiosk import geo  # noqa: E402

BLENDER_DIR = os.path.dirname(HERE)
RAW = os.path.join(os.path.dirname(BLENDER_DIR), "Unreal", "RawContent")
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

U = {
    "ribs": 8,
    "radius": 0.52,  # canopy, horizontal
    "hub_z": 0.80,  # top of the shaft above the grip
    "drop": 0.24,  # rib tips sit this far below the hub
    "dome": 1.6,  # profile exponent (higher = flatter crown, steeper edge)
    "sag": 0.025,  # panels droop between the ribs (wet fabric)
    "runner_z": 0.56,
}

MATS = {  # rgb, roughness, metallic, emission
    "Umbrella_Black": ((0.014, 0.014, 0.016), 0.35, 0.0, 0.0),
    "Umbrella_Navy": ((0.016, 0.024, 0.055), 0.35, 0.0, 0.0),
    "Umbrella_Red": ((0.09, 0.012, 0.016), 0.35, 0.0, 0.0),
    "Umbrella_Clear": ((0.75, 0.8, 0.85), 0.08, 0.0, 0.0),
    "Umbrella_Metal": ((0.35, 0.35, 0.37), 0.35, 1.0, 0.0),
    "Umbrella_Handle": ((0.02, 0.018, 0.016), 0.45, 0.0, 0.0),
    "Umbrella_LED": ((0.3, 0.85, 1.0), 0.3, 0.0, 12.0),
}
VARIANTS = {  # mesh: (canopy material, shaft material)
    "SM_Umbrella_Black": ("Umbrella_Black", "Umbrella_Metal"),
    "SM_Umbrella_Navy": ("Umbrella_Navy", "Umbrella_Metal"),
    "SM_Umbrella_Red": ("Umbrella_Red", "Umbrella_Metal"),
    "SM_Umbrella_Clear": ("Umbrella_Clear", "Umbrella_Metal"),
    "SM_Umbrella_LED": ("Umbrella_Black", "Umbrella_LED"),
}


def rib_point(k, s):
    """Point on rib k at fraction s (0 = hub, 1 = tip)."""
    a = 2 * math.pi * k / U["ribs"]
    r = U["radius"] * s
    return Vector((r * math.cos(a), r * math.sin(a), U["hub_z"] - U["drop"] * s ** U["dome"]))


def canopy(m, mat, offset):
    """Taut panels between the ribs; offset < 0 builds the underside shell (faces flipped)."""
    rings, sub = 10, 6
    n = U["ribs"] * sub
    verts, faces = [], []
    for i in range(rings + 1):
        s = max(i / rings, 0.02)
        for j in range(n):
            k, t = divmod(j, sub)
            t /= sub
            p = rib_point(k, s).lerp(rib_point(k + 1, s), t)
            p.z -= U["sag"] * 4 * t * (1 - t) * s  # droop between the ribs
            p.z += offset
            verts.append(p)
    for i in range(rings):
        for j in range(n):
            a, b = i * n + j, i * n + (j + 1) % n
            f = (a, b, b + n, a + n)
            faces.append(f if offset < 0 else tuple(reversed(f)))
    m.add_raw(verts, faces, mat, smooth=True)


def frame(m, shaft_mat):
    hz, rz = U["hub_z"], U["runner_z"]
    geo.cylinder(m, (0, 0, -0.03), 0.014, 0.18, "Umbrella_Handle", segments=12)  # grip
    c, r = Vector((0.045, 0, -0.12)), 0.045  # J-hook
    pts = [c + Vector((r * math.cos(t), 0, r * math.sin(t))) for t in (math.pi + (math.pi + 0.5) * i / 10 for i in range(11))]
    for p, q in zip([Vector((0, 0, -0.12))] + pts, pts):
        geo.pipe(m, p, q, 0.012, "Umbrella_Handle", 10)
    geo.pipe(m, (0, 0, 0.06), (0, 0, hz + 0.01), 0.0065, shaft_mat, 10)  # shaft
    geo.pipe(m, (0, 0, hz), (0, 0, hz + 0.09), 0.004, "Umbrella_Metal", 8)  # ferrule
    geo.cylinder(m, (0, 0, rz), 0.012, 0.05, "Umbrella_Metal", segments=10)  # runner
    for k in range(U["ribs"]):
        pts = [rib_point(k, i / 8) - Vector((0, 0, 0.006)) for i in range(9)]
        for p, q in zip(pts, pts[1:]):
            geo.pipe(m, p, q, 0.0035, "Umbrella_Metal", 6)  # rib under the fabric
        geo.pipe(m, (0, 0, rz), rib_point(k, 0.55) - Vector((0, 0, 0.008)), 0.003, "Umbrella_Metal", 6)  # stretcher
        tip = rib_point(k, 1.0)
        geo.pipe(m, tip, tip - Vector((0, 0, 0.022)), 0.005, "Umbrella_Handle", 6)  # tip cap


def main():
    B.reset_scene()
    for name, (rgb, r, mt, e) in MATS.items():
        mat = make_mat(name, rgb, r, mt, e)
        if name == "Umbrella_Clear":
            mat.node_tree.nodes.get("Principled BSDF").inputs["Alpha"].default_value = 0.28
            for attr, val in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
                if hasattr(mat, attr):
                    try:
                        setattr(mat, attr, val)
                    except (TypeError, ValueError):
                        pass
    coll = B.collection("Umbrellas")
    obs = []
    for name, (cmat, smat) in VARIANTS.items():
        m = geo.Mesh(name)
        canopy(m, cmat, 0.0)
        canopy(m, cmat, -0.003)
        frame(m, smat)
        ob = m.build(coll, bpy.data.materials)
        obs.append(ob)
        print(f"{name}: {len(ob.data.polygons)} faces")
    bpy.ops.object.select_all(action="DESELECT")
    for ob in obs:
        ob.select_set(True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(RAW, "umbrellas.glb"), export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True, export_cameras=False, export_lights=False)
    print("exported umbrellas.glb")
    if "--render" in ARGV:
        from kiosk import review
        for i, ob in enumerate(obs):
            ob.location = (0, i * 1.3 - 2.6, 1.3)
        B.init_shared()
        rc = B.collection("Review")
        scene = bpy.context.scene
        review.setup_scene(scene, rc, bpy.data.materials)
        cam = review.look_camera(rc, "CAM_Umbrellas", (4.5, -3.0, 0.4), (0, 0, 1.8), 35)
        review.render(scene, cam, os.path.join(BLENDER_DIR, "renders", "umbrellas_check.png"))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLENDER_DIR, "umbrellas.blend"), check_existing=False)


if __name__ == "__main__":
    main()
