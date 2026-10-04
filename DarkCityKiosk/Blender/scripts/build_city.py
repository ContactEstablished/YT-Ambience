"""Builds the scripted city around the kiosk into Blender/city.blend.

    blender -b --factory-startup -P build_city.py -- [--render] [--export]

--render  preview renders from the video cameras (A/Mid/B) and a top-down map, with the
          kiosk appended from kiosk_detail.blend for scale (EEVEE, no fog: framing only)
--export  Unreal/RawContent/city.glb (city meshes only) + city_manifest.json (screens,
          beacons, shopfront glows, viaduct end) for the Unreal setup script
"""
import json
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import city_config as CC  # noqa: E402
import kiosk_config as C  # noqa: E402
import build_kiosk_blockout as B  # noqa: E402
from city import towers as T  # noqa: E402
from city import viaduct as VD  # noqa: E402
from kiosk import geo, review  # noqa: E402

BLENDER_DIR = os.path.dirname(HERE)
RAW = os.path.join(os.path.dirname(BLENDER_DIR), "Unreal", "RawContent")
RENDERS = os.path.join(BLENDER_DIR, "renders")
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

# Preview materials: (rgb, roughness, metallic, emission). Unreal swaps the window/screen ones
# for its own shaders by name, so only the names matter there.
BASE_MATS = {
    "City_Window_Glass": ((0.03, 0.05, 0.07), 0.08, 0.6, 0.12),
    "City_Window_Slab": ((0.06, 0.06, 0.06), 0.6, 0.0, 0.08),
    "City_Shop": ((0.30, 0.25, 0.20), 0.4, 0.0, 1.2),
    "City_Facade": ((0.05, 0.055, 0.06), 0.5, 0.2, 0.0),
    "City_Roof": ((0.08, 0.08, 0.085), 0.6, 0.2, 0.0),
    "Landmark_Ring": ((1.0, 0.75, 0.4), 0.4, 0.0, 6.0),
    "Beacon_Red": ((1.0, 0.06, 0.04), 0.4, 0.0, 8.0),
    "Viaduct_Concrete": ((0.11, 0.11, 0.115), 0.7, 0.0, 0.0),
    "Viaduct_Steel": ((0.06, 0.065, 0.07), 0.45, 0.6, 0.0),
    "Viaduct_Strip": ((0.3, 0.95, 1.0), 0.4, 0.0, 5.0),
    "Viaduct_Lamp": ((1.0, 0.85, 0.6), 0.4, 0.0, 6.0),
    "Rail_Steel": ((0.35, 0.35, 0.36), 0.25, 0.9, 0.0),
    "Portal_Dark": ((0.0, 0.0, 0.0), 0.9, 0.0, 0.0),
}


def make_mat(name, rgb, rough=0.5, metal=0.0, emit=0.0, emit_rgb=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.diffuse_color = (*rgb, 1.0)
    if m.node_tree is None:
        m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1.0)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*(emit_rgb or rgb), 1.0)
        b.inputs["Emission Strength"].default_value = emit
    return m


def make_materials(specs):
    for name, (rgb, r, mt, e) in BASE_MATS.items():
        make_mat(name, rgb, r, mt, e, (0.6, 0.75, 0.9) if name == "City_Window_Glass" else (1.0, 0.8, 0.55) if "Window" in name else None)
    for i, col in enumerate(T.SIGN_COLOURS):
        make_mat(f"City_Sign_{i}", col, 0.4, 0.0, 4.0)
    for s in specs:
        for i, sc in enumerate(s[7]):
            make_mat(f"City_Screen_{s[0]}_{i}", sc[5], 0.3, 0.0, 3.0)


def viaduct_end_x(specs):
    """Where the railway (along +X at the corridor centre) meets RightA's front face."""
    ra = next(s for s in specs if s[0] == "RightA")
    az = math.radians(ra[1])
    fd = ra[2] - ra[4] / 2
    fx, fy = fd * math.cos(az), fd * math.sin(az)
    yc = (CC.VIADUCT["y0"] + CC.VIADUCT["y1"]) / 2
    return fx - (yc - fy) * math.tan(az)


def build(coll):
    specs = T.layout()
    make_materials(specs)
    mats = bpy.data.materials
    manifest = {"screens": [], "beacons": [], "shops": [], "towers": []}
    far = [geo.Mesh(f"City_Far_{k}") for k in range(4)]
    for k, (name, az, dist, w, d, h, style, screens, detailed) in enumerate(specs):
        if detailed:
            m = geo.Mesh(f"City_{name}")
            T.tower(m, name, az, dist, w, d, h, style, screens, manifest, detail=True)
            m.build(coll, mats)
        else:
            T.tower(far[k % 4], name, az, dist, w, d, h, style, screens, manifest, detail=False)
    for m in far:
        m.build(coll, mats)
    lm = geo.Mesh("City_Landmark")
    T.landmark(lm, manifest)
    lm.build(coll, mats)
    v = dict(CC.VIADUCT)
    v["x1"] = round(viaduct_end_x(specs), 2)
    manifest["viaduct"] = v
    vm = geo.Mesh("City_Viaduct")
    VD.build(vm, v["x1"], manifest)
    vm.build(coll, mats)
    return specs, manifest


def append_kiosk():
    path = os.path.join(BLENDER_DIR, "kiosk_detail.blend")
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c == "Kiosk"]
    for c in dst.collections:
        bpy.context.scene.collection.children.link(c)


def map_camera(coll):
    cam = bpy.data.cameras.new("CAM_Map")
    cam.type, cam.ortho_scale, cam.clip_end = "ORTHO", 760, 3000
    ob = bpy.data.objects.new("CAM_Map", cam)
    ob.location = (110, 90, 1500)
    coll.objects.link(ob)
    return ob


def main():
    B.reset_scene()
    B.init_shared()
    scene = bpy.context.scene
    city = B.collection("City")
    specs, manifest = build(city)
    n_faces = sum(len(o.data.polygons) for o in city.objects)
    print(f"city: {len(specs)} towers + landmark, {len(city.objects)} objects, {n_faces} faces, "
          f"{len(manifest['screens'])} screens, {len(manifest['beacons'])} beacons; viaduct ends at x={manifest['viaduct']['x1']}")

    if "--export" in ARGV:
        os.makedirs(RAW, exist_ok=True)
        with open(os.path.join(RAW, "city_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=1)
        bpy.ops.object.select_all(action="DESELECT")
        for o in city.objects:
            o.select_set(True)
        bpy.ops.export_scene.gltf(filepath=os.path.join(RAW, "city.glb"), export_format="GLB", use_selection=True,
                                  export_apply=True, export_yup=True, export_cameras=False, export_lights=False)
        print("exported city.glb + city_manifest.json")

    if "--render" in ARGV:
        append_kiosk()
        review_coll = B.collection("Review")
        review.setup_scene(scene, review_coll, bpy.data.materials)
        g = bpy.data.objects["Ground"]
        g.scale = (12, 12, 1)  # the review ground is 120 m; the city reaches ~430 m
        cams = review.cameras(review_coll)
        for c in cams.values():
            c.data.clip_end = 2500
        cams["Map"] = map_camera(review_coll)
        scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.02, 0.035, 0.045, 1.0)
        # preview fog so depth reads (Unreal has the real volumetric fog)
        nt = scene.world.node_tree
        vol = nt.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Color"].default_value = (0.35, 0.55, 0.5, 1.0)
        vol.inputs["Density"].default_value = 0.004
        nt.links.new(vol.outputs["Volume"], nt.nodes["World Output"].inputs["Volume"])
        for name, e in (("L_Fill", 120), ("L_Rim", 150), ("L_Rake", 0)):
            bpy.data.objects[name].data.energy = e
        os.makedirs(RENDERS, exist_ok=True)
        for key in ("A", "Mid", "B", "Map"):
            review.render(scene, cams[key], os.path.join(RENDERS, f"city_{key}.png"))

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(BLENDER_DIR, "city.blend"), check_existing=False)


if __name__ == "__main__":
    main()
