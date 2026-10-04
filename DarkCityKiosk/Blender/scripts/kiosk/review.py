"""Review renders in Blender (EEVEE): night lighting close to the Unreal scene, the 20 mm
video cameras (A / Mid / B) and close-up cameras. Not exported; for judging geometry.
"""
import math
import os

import bpy
from mathutils import Vector

import kiosk_config as C


def _engine(scene):
    for name in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = name
            return name
        except TypeError:
            continue
    raise RuntimeError("no EEVEE engine found")


def setup_scene(scene, coll, materials):
    _engine(scene)
    ee = scene.eevee
    for k, v in (("taa_render_samples", 64), ("use_raytracing", True), ("use_shadows", True)):
        try:
            setattr(ee, k, v)
        except AttributeError:
            pass
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0.0
    world = bpy.data.worlds.new("ReviewNight")
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.012, 0.02, 0.024, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    scene.world = world
    # Emission tuned for EEVEE review under AgX (the Unreal values live in scene_config.EMISSIVE)
    for name, strength in (("Lightbox_Yellow", 2.2), ("Lightbox_White", 2.0), ("Tube_WarmWhite", 8.0),
                           ("Lantern_Paper", 2.5), ("Interior_Light", 5.0), ("Screen_Multi", 2.0)):
        m = bpy.data.materials.get(name)
        b = m.node_tree.nodes.get("Principled BSDF") if m else None
        if b:
            b.inputs["Emission Strength"].default_value = strength
            if name == "Lightbox_Yellow":
                b.inputs["Emission Color"].default_value = (1.0, 0.6, 0.07, 1.0)
                b.inputs["Base Color"].default_value = (1.0, 0.6, 0.07, 1.0)

    # Wet ground (review only; the export skips objects named Ground)
    me = bpy.data.meshes.new("Ground")
    s = 60.0
    me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
    gm = bpy.data.materials.get("Ground_Wet")
    bsdf = gm.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.12
    me.materials.append(gm)
    ground = bpy.data.objects.new("Ground", me)
    coll.objects.link(ground)

    def area(name, loc, rot_deg, size, size_y, power, color):
        ld = bpy.data.lights.new(name, "AREA")
        ld.shape = "RECTANGLE"
        ld.size, ld.size_y, ld.energy, ld.color = size, size_y, power, color
        ob = bpy.data.objects.new(name, ld)
        ob.location = loc
        ob.rotation_euler = [math.radians(a) for a in rot_deg]
        coll.objects.link(ob)

    def point(name, loc, power, color, radius=0.05):
        ld = bpy.data.lights.new(name, "POINT")
        ld.energy, ld.color, ld.shadow_soft_size = power, color, radius
        ob = bpy.data.objects.new(name, ld)
        ob.location = loc
        coll.objects.link(ob)

    warm = (1.0, 0.82, 0.6)
    for i, (axis, fixed, a, b) in enumerate(C.SOFFIT_TUBES):
        mid = (a + b) / 2
        loc = (mid, fixed, C.CANOPY_BOTTOM - 0.07) if axis == "X" else (fixed, mid, C.CANOPY_BOTTOM - 0.07)
        area(f"L_Soffit_{i}", loc, (0, 0, 0 if axis == "X" else 90), b - a, 0.06, 35, warm)
    mid_z = (C.CANOPY_BOTTOM + C.CANOPY_TOP) / 2
    area("L_Spill_Front", ((C.CANOPY_X0 + C.CANOPY_X1) / 2, C.CANOPY_Y0 - 0.1, mid_z), (115, 0, 0),
         C.CANOPY_X1 - C.CANOPY_X0, 0.4, 260, (1.0, 0.62, 0.18))
    area("L_Spill_Left", (C.CANOPY_X0 - 0.1, (C.CANOPY_Y0 + C.CANOPY_Y1) / 2, mid_z), (115, 0, -90),
         C.CANOPY_Y1 - C.CANOPY_Y0, 0.4, 220, (1.0, 0.62, 0.18))
    point("L_Interior", (-0.82, -1.0, 1.72), 25, (1.0, 0.75, 0.5), 0.15)
    for name, lt in (("L_Lantern_L", C.LANTERN_L), ("L_Lantern_R", C.LANTERN_R)):
        point(name, (lt["x"], lt["y"], lt["z"]), 8, (1.0, 0.7, 0.4), lt["radius"])
    # cool city fill from the camera side + teal rim from behind, so the shapes read
    area("L_Fill", (-9, -9, 7), (55, 0, -45), 8, 8, 450, (0.75, 0.82, 0.88))
    area("L_Rim", (7, 9, 9), (-50, 0, 145), 10, 10, 500, (0.4, 0.75, 0.7))
    area("L_Rake", (-6.5, 0.4, 2.0), (90, 0, -90), 3, 3, 120, (1.0, 0.9, 0.75))  # grazing light on the door wall


def video_camera(coll, name, theta_deg):
    vc, hc = C.VIDEO_CAM, C.HERO_CAM
    px, py = C.ORBIT_PIVOT
    t = math.radians(theta_deg)
    dx, dy = (hc["pos_xy"][0] - px) * vc["distance_scale"], (hc["pos_xy"][1] - py) * vc["distance_scale"]
    cam = bpy.data.cameras.new(name)
    cam.lens, cam.sensor_fit, cam.sensor_width = vc["lens_mm"], "HORIZONTAL", vc["sensor_w_mm"]
    cam.clip_start, cam.clip_end = 0.02, 500
    ob = bpy.data.objects.new(name, cam)
    ob.location = (px + dx * math.cos(t) - dy * math.sin(t), py + dx * math.sin(t) + dy * math.cos(t), vc["height_m"])
    ob.rotation_euler = (math.radians(90 + vc["pitch_deg"]), 0.0, math.radians(hc["heading_deg"] + theta_deg - 90))
    coll.objects.link(ob)
    return ob


def look_camera(coll, name, loc, target, lens):
    cam = bpy.data.cameras.new(name)
    cam.lens, cam.sensor_fit, cam.sensor_width = lens, "HORIZONTAL", 36.0
    cam.clip_start = 0.02
    ob = bpy.data.objects.new(name, cam)
    ob.location = loc
    ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    coll.objects.link(ob)
    return ob


def cameras(coll):
    arc = C.VIDEO_CAM["arc_deg"]
    cams = {
        "A": video_camera(coll, "CAM_Video_A", -arc),
        "Mid": video_camera(coll, "CAM_Video_Mid", 0.0),
        "B": video_camera(coll, "CAM_Video_B", arc),
        "Corner": look_camera(coll, "CAM_Close_Corner", (-5.2, -4.9, 0.9), (-1.6, -1.2, 2.0), 30),
        "Soffit": look_camera(coll, "CAM_Close_Soffit", (-3.4, -3.8, 0.35), (-1.0, -1.6, 2.55), 24),
        "Wall": look_camera(coll, "CAM_Close_Wall", (-4.3, -1.4, 1.3), (-2.15, -0.6, 1.3), 35),
        "Front": look_camera(coll, "CAM_Close_Front", (-0.1, -6.4, 1.15), (-0.1, -1.55, 1.25), 28),
        "Interior": look_camera(coll, "CAM_Close_Interior", (-1.3, -3.4, 1.5), (-0.85, -0.8, 1.35), 32),
        "Door": look_camera(coll, "CAM_Close_Door", (-4.9, -0.6, 1.15), (-2.15, 0.25, 1.15), 32),
        "Roof": look_camera(coll, "CAM_Close_Roof", (-5.4, -5.6, 4.7), (-0.4, -0.8, 3.25), 28),
        "Clutter": look_camera(coll, "CAM_Close_Clutter", (-4.9, -3.0, 1.05), (-2.5, -0.4, 1.05), 30),
        "Right": look_camera(coll, "CAM_Close_Right", (3.9, -4.4, 1.0), (2.2, -1.7, 1.15), 30),
    }
    return cams


def render(scene, cam, path, res=(1600, 900)):
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print(f"rendered {os.path.basename(path)}")
