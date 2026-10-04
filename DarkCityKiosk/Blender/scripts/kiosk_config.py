"""Every number the kiosk build uses. Mirrors docs/KIOSK-SPEC.md.

Frame (Blender, metres): origin = centre of the body footprint at ground level.
+X runs along the front face to the right (as seen from the hero camera),
+Y runs from the front face toward the back, +Z is up.
"""

# ---- Body -------------------------------------------------------------------
BODY_W = 4.30  # along X (front face)
BODY_D = 3.10  # along Y (left face)
BODY_TOP = 2.45  # canopy underside
X0, X1 = -BODY_W / 2, BODY_W / 2  # left face at X0, right face at X1
Y0, Y1 = -BODY_D / 2, BODY_D / 2  # front face at Y0, back face at Y1

PLATFORM_H = 0.12
PLATFORM_MARGIN = 1.0

CORNER_POST = 0.12  # square steel posts at the four vertical corners
SEAM_SPACING = 0.95  # vertical seam strips on the walls
SEAM_W = 0.06

# ---- Canopy -----------------------------------------------------------------
CANOPY_BOTTOM = BODY_TOP
CANOPY_H = 0.50
CANOPY_TOP = CANOPY_BOTTOM + CANOPY_H  # roof deck
OVERHANG = {"front": 0.70, "left": 0.70, "right": 0.40, "back": 0.40}
CANOPY_X0, CANOPY_X1 = X0 - OVERHANG["left"], X1 + OVERHANG["right"]
CANOPY_Y0, CANOPY_Y1 = Y0 - OVERHANG["front"], Y1 + OVERHANG["back"]
LIGHTBOX_FRAME = 0.08  # metal frame around each lit face

# Soffit tube lights: (axis, fixed coordinate, start, end); all at Z just under the canopy
SOFFIT_TUBES = [
    ("X", CANOPY_Y0 + 0.30, -2.30, -1.10),
    ("X", CANOPY_Y0 + 0.30, -0.80, 0.40),
    ("X", CANOPY_Y0 + 0.30, 0.80, 2.00),
    ("Y", CANOPY_X0 + 0.30, -1.70, -0.60),
    ("Y", CANOPY_X0 + 0.30, -0.10, 1.00),
]

# ---- Left face (X = X0), the door side --------------------------------------
DOOR = {"y": 0.25, "w": 0.85, "h": 2.00, "window": (0.35, 0.55, 1.35)}  # window w, h, bottom Z
# Wall-mounted boxes: (name, y0, y1, z0, z1, depth)
LEFT_WALL_BOXES = [
    ("MeterBox", -1.40, -1.08, 1.25, 1.75, 0.15),
    ("FuseBox", -1.00, -0.72, 1.85, 2.20, 0.12),
    ("JunctionBox", -1.45, -1.25, 0.95, 1.12, 0.10),
]
# Flat decals (logo, poster): (name, y0, y1, z0, z1)
LEFT_WALL_DECALS = [
    ("KazeLogo", -1.45, -1.10, 0.75, 1.25),
    ("Poster_L", -0.95, -0.62, 0.60, 1.05),  # clear of the batten at y -0.497
]

# ---- Front face (Y = Y0), the service side ----------------------------------
SERVICE_WINDOW = {"x0": -1.50, "x1": -0.15, "z0": 1.00, "z1": 1.85, "depth": 0.90}
COUNTER = {"x0": -2.05, "x1": 0.40, "z": 1.00, "projection": 0.40, "thickness": 0.05}
TICKET_MACHINE = {"x0": -2.07, "x1": -1.70, "z0": 1.00, "z1": 1.65, "depth": 0.25}
UNDER_COUNTER_SIGN = {"x0": -0.95, "x1": -0.40, "z0": 0.35, "z1": 0.80}
GLAZED_WINDOW = {"x0": 0.60, "x1": 1.86, "z0": 0.55, "z1": 1.60, "cols": 4, "rows": 5}
WINDOW_LIGHTBOX = {"x0": 0.65, "x1": 1.85, "z0": 1.70, "z1": 2.20, "depth": 0.12}
VENT_GRILLE = {"x0": 0.65, "x1": 1.35, "z0": 0.15, "z1": 0.40}
FRONT_WALL_DECALS = [
    ("Poster_F", 0.05, 0.35, 1.20, 1.65),
    ("Stickers_F", -2.10, -1.90, 1.10, 1.70),
]

# ---- Canopy lettering (fitted to the reference) -----------------------------
# Front band text fills X x0..x1 (starts at the body corner); a ring mark follows it.
CANOPY_TEXT_FRONT = {"x0": -2.15, "x1": 0.32, "ring_x": 0.50, "z": 2.60}
# Left band text runs from the back (y0) toward the front corner (y1); the bowl icon sits near the corner.
CANOPY_TEXT_LEFT = {"y0": 0.99, "y1": -0.83, "bowl_y": -1.34, "z": 2.64}

# ---- Corner vertical sign ---------------------------------------------------
CORNER_SIGN = {"x": 2.70, "y": -2.15, "w": 0.28, "d": 0.10, "z0": 2.25, "z1": 3.00}

# ---- Roof machinery (on the deck at CANOPY_TOP) -----------------------------
# Boxes: (name, cx, cy, w(X), d(Y), h)
# Positions fitted to the reference with fit_to_reference.mjs (machinery runs
# diagonally from the back-left toward the front-centre; the right third is nearly bare).
ROOF_BOXES = [
    ("SmallUnit", -2.50, 0.55, 0.60, 0.50, 0.45),
    ("ACCondenser", -2.10, -0.25, 0.70, 1.00, 0.75),
    ("TallCabinet", -1.35, -0.60, 0.80, 0.70, 1.00),
    ("StickerCabinet", -0.40, -1.80, 0.60, 0.50, 0.80),
    ("WhiteBox", 0.42, -1.93, 0.55, 0.45, 0.40),
    ("BackBox_A", -1.60, 0.80, 0.90, 0.80, 0.60),
    ("BackBox_B", 0.40, 0.50, 1.00, 0.80, 0.50),
    ("BackBox_C", -0.60, 1.20, 0.60, 0.60, 0.70),
]
# Tanks: (name, cx, cy, radius, height) — vertical cylinders with domed tops
ROOF_TANKS = [
    ("Tank_A", -0.95, -1.20, 0.25, 0.85),
    ("Tank_B", -0.45, -1.25, 0.275, 0.90),
    ("Tank_C", -0.20, -0.85, 0.225, 0.80),
]
CABLE_REEL = {"cx": 1.30, "cy": -0.70, "radius": 0.45, "width": 0.40}
MAST = {"cx": 1.32, "cy": -1.28, "w": 0.15, "h": 1.65}

# ---- Free-standing props ----------------------------------------------------
LANTERN_L = {"x": -2.55, "y": 1.30, "z": 1.68, "radius": 0.175, "h": 0.65}
LANTERN_R = {"x": 2.00, "y": -1.95, "z": 1.45, "radius": 0.15, "h": 0.55}
# Pedestal tiers under the left lantern: (size, height)
LANTERN_L_PEDESTAL = [(0.40, 0.35), (0.32, 0.30), (0.24, 0.25)]
# Boxes on the ground: (name, cx, cy, w, d, h)
GROUND_BOXES = [
    ("CrateStack_A", -2.70, 2.00, 0.60, 0.50, 0.75),
    ("CrateStack_B", -3.00, 1.65, 0.50, 0.50, 1.00),
    ("RedCrate", -2.40, 1.05, 0.40, 0.30, 0.30),
    ("UtilityCabinet", 2.30, -1.75, 0.45, 0.40, 0.85),
]
# Bins: (name, cx, cy, radius, h)
BINS = [
    ("Bin_Green", -2.40, -1.30, 0.22, 0.65),
    ("Bin_Grey", 2.85, -2.00, 0.22, 0.50),
]
STOOLS = [(-1.30, -2.10), (-0.05, -2.10)]  # Ø 0.36 seat, 0.75 m tall; framing the under-counter sign
RAILING = {"x": -3.05, "y0": 1.20, "y1": 2.50, "h": 1.00}

# ---- Cameras ----------------------------------------------------------------
# Hero camera, solved from PrimaryReference.png (docs/reference_camera_solve.json).
HERO_CAM = {
    "pos_xy": (-9.94, -8.76),
    "height_overlay": 0.05,  # matches the reference (camera at ground level)
    "height_video": 0.35,  # starting point for the video camera, decided Sunday
    "pitch_up_deg": 12.8,
    "heading_deg": 35.8,  # view direction, measured from +X toward +Y
    "lens_mm": 32.23,
    "sensor_w_mm": 36.0,
}
ORBIT_PIVOT = (0.0, 0.0)
ORBIT_ARC_DEG = (-45.0, 45.0)  # negative = toward the door side, positive = toward the service window

# The video camera (chosen by the user 2026-10-03), shared by Blender review renders and Unreal.
# It orbits the pivot along the hero camera's line; distance_scale 1.0 = hero distance (13.25 m).
# 20 mm wide-angle: kiosk large in the foreground, tower tops visible, slight wide-angle stretch.
VIDEO_CAM = {
    "lens_mm": 20.0,
    "sensor_w_mm": 36.0,  # 16:9 full-frame filmback (36 x 20.25)
    "distance_scale": 0.807,  # same kiosk size in frame as 32 mm at 1.3x
    "pitch_deg": 15.8,  # horizon ~78% down the frame: wet foreground below, towers above
    "height_m": 0.10,  # practically on the floor; the kiosk towers over the viewer
    "arc_deg": 45.0,  # ping-pong orbit A (-arc) -> B (+arc) -> A around the reference angle
}

# ---- Detailed shell (build_kiosk.py) -------------------------------------------------
SHELL = {
    "panel_t": 0.025,  # steel panel thickness; outer face sits on the wall plane
    "panel_gap": 0.008,  # gap between neighbouring panels
    "panel_bevel": 0.004,
    "panel_jitter_out": 0.003,  # some panels sit a few mm proud (old, refitted)
    "panel_jitter_tilt_deg": 0.12,
    "split_chance": 0.35,  # chance a panel is split horizontally
    "split_z": (1.05, 1.45),
    "batten_w": 0.07,  # flat bar over each panel joint
    "batten_t": 0.012,
    "rivet_r": 0.009,
    "rivet_pitch": 0.08,  # spacing along battens
    "skirt_h": 0.15,  # dark steel plinth band at the base
    "skirt_t": 0.03,
    "topbeam_h": 0.12,  # riveted beam under the canopy
    "topbeam_t": 0.045,
    "post_bevel": 0.015,
    "frame_w": 0.06,  # service-window frame
    "frame_t": 0.04,
}
CANOPY_DETAIL = {
    "plate_t": 0.022,  # soffit and deck plates
    "rail_h": 0.045,  # dark frame rails around each lightbox face
    "rail_t": 0.035,
    "diffuser_inset": 0.012,  # lit face sits this far behind the frame line
    "mullion_every": 1.25,
    "rail_rivet_pitch": 0.15,
    "soffit_seam_every": 1.2,
}
