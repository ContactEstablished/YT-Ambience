"""Every number the kiosk build uses. Mirrors docs/KIOSK-SPEC.md.

Frame (Blender, metres): origin = centre of the body footprint at ground level.
+X runs along the front face to the right (as seen from the hero camera),
+Y runs from the front face toward the back, +Z is up.
"""

# ---- Body -------------------------------------------------------------------
# Proportion pass (2026-10-04, brief 1B): the kiosk read tall and narrow from the video camera.
# It is now wider than it is tall: the front grows 22% and the side 10%, symmetrically about the
# orbit pivot so the kiosk stays where it was, and the walls are 0.20 m lower. Everything on the
# walls is laid out from X0/X1/Y0/Y1 below, so it follows the walls.
BODY_W = 5.25  # along X (front face); was 4.30
BODY_D = 3.40  # along Y (left face); was 3.10
BODY_TOP = 2.25  # canopy underside; was 2.45
X0, X1 = -BODY_W / 2, BODY_W / 2  # left face at X0, right face at X1
Y0, Y1 = -BODY_D / 2, BODY_D / 2  # front face at Y0, back face at Y1

PLATFORM_H = 0.12
PLATFORM_MARGIN = 1.0

CORNER_POST = 0.12  # square steel posts at the four vertical corners
SEAM_SPACING = 0.95  # vertical seam strips on the walls
SEAM_W = 0.06

# ---- Canopy -----------------------------------------------------------------
# Massing pass (2026-10-04): a heavier canopy that reads as bright yellow fascia / dark
# structural frame / kiosk body. The fascia is a deep box around the edge: a dark edge beam
# that hangs below the soffit, the lit yellow face, and a dark coping on top.
CANOPY_BOTTOM = BODY_TOP  # soffit plate
CANOPY_H = 0.62  # was 0.50
CANOPY_TOP = CANOPY_BOTTOM + CANOPY_H  # roof deck
OVERHANG = {"front": 0.85, "left": 0.85, "right": 0.50, "back": 0.50}  # was 0.70 / 0.70 / 0.40 / 0.40
CANOPY_X0, CANOPY_X1 = X0 - OVERHANG["left"], X1 + OVERHANG["right"]
CANOPY_Y0, CANOPY_Y1 = Y0 - OVERHANG["front"], Y1 + OVERHANG["back"]
LIGHTBOX_FRAME = 0.08  # metal frame around each lit face
FASCIA = {
    "depth": 0.30,  # the fascia box reaches this far in from the canopy edge
    "drop": 0.10,  # the edge beam hangs this far below the soffit
    "beam_h": 0.15,  # dark edge beam at the bottom of the fascia (from the drop up)
    "beam_proud": 0.025,  # edge beam sits proud of the yellow face
    "lip_h": 0.03,  # bottom flange of the edge beam, a little further out
    "lip_proud": 0.045,
    "cap_h": 0.06,  # dark coping along the top (its top sits 1 cm above the deck)
    "cap_proud": 0.05,
    "post": 0.15,  # structural post at each canopy corner
    "post_proud": 0.07,  # proud of the coping too (no coplanar faces)
}
FASCIA_Z0 = CANOPY_BOTTOM - FASCIA["drop"]  # underside of the edge beam
FACE_Z0 = FASCIA_Z0 + FASCIA["beam_h"]  # yellow face, bottom
FACE_Z1 = CANOPY_TOP - FASCIA["cap_h"]  # yellow face, top
SOFFIT_JOIST_H = 0.09  # dark cross beams under the soffit, from the walls to the edge beam

# Soffit tube lights: (axis, fixed coordinate, start, end). They hang on drop rods just inside
# the edge beam, so they show under the fascia from the floor-level camera.
SOFFIT_TUBE_Z = CANOPY_BOTTOM - 0.12
SOFFIT_TUBES = [  # three along the front, two along the left side, spread over the wider canopy
    ("X", CANOPY_Y0 + 0.42, CANOPY_X0 + 0.70, CANOPY_X0 + 2.10),
    ("X", CANOPY_Y0 + 0.42, CANOPY_X0 + 2.625, CANOPY_X0 + 4.025),
    ("X", CANOPY_Y0 + 0.42, CANOPY_X0 + 4.55, CANOPY_X0 + 5.95),
    ("Y", CANOPY_X0 + 0.42, CANOPY_Y0 + 0.70, CANOPY_Y0 + 1.95),
    ("Y", CANOPY_X0 + 0.42, CANOPY_Y0 + 2.45, CANOPY_Y0 + 3.70),
]
# Dark joists under the soffit (between the tube runs): X positions along the front, Y along the left
SOFFIT_JOISTS = {"x": (-1.11, 0.81), "y": (-0.35, 1.40)}
# Junction boxes on the soffit conduit, each with a drop into the header beam: (along-wall coordinate)
SOFFIT_JUNCTIONS = {"front": (-2.30, -0.60, 1.50), "left": (-0.75, 1.05)}

# ---- Left face (X = X0), the door side --------------------------------------
DOOR = {"y": 0.25, "w": 0.85, "h": 1.92, "window": (0.35, 0.50, 1.33)}  # window w, h, bottom Z
# Wall-mounted boxes: (name, y0, y1, z0, z1, depth)
LEFT_WALL_BOXES = [
    ("MeterBox", Y0 + 0.15, Y0 + 0.53, 1.20, 1.80, 0.19),  # massing pass: was 0.32 x 0.50 x 0.15
    ("FuseBox", Y0 + 0.55, Y0 + 0.83, 1.78, 2.08, 0.12),  # top clear of the header beam
    ("JunctionBox", Y0 + 0.10, Y0 + 0.30, 0.95, 1.12, 0.10),
]
# Flat decals (logo, poster): (name, y0, y1, z0, z1). Grey-box only (build_kiosk_blockout.py): the detailed kiosk's
# graphics come from the signage pass (GRAPHICS below, kiosk/graphics.py).
LEFT_WALL_DECALS = [
    ("KazeLogo", Y0 + 0.10, Y0 + 0.45, 0.75, 1.25),
    ("Poster_L", Y0 + 0.68, Y0 + 1.01, 0.60, 1.05),  # clear of the first batten
]

# ---- Front face (Y = Y0), the service side ----------------------------------
# Left to right: ticket machine by the corner, the service window (22% wider than before) over a
# long counter, wall with a poster, then the framed bay with the glazed window and its lightbox.
SERVICE_WINDOW = {"x0": -1.90, "x1": -0.25, "z0": 1.00, "z1": 1.80, "depth": 0.90}  # was 1.35 x 0.85
COUNTER = {"x0": X0 + 0.10, "x1": 0.73, "z": 1.00, "projection": 0.40, "thickness": 0.05}
TICKET_MACHINE = {"x0": X0 + 0.08, "x1": X0 + 0.45, "z0": 1.00, "z1": 1.65, "depth": 0.25}
UNDER_COUNTER_SIGN = {"x0": -1.20, "x1": -0.60, "z0": 0.35, "z1": 0.80}
GLAZED_WINDOW = {"x0": X1 - 1.69, "x1": X1 - 0.29, "z0": 0.55, "z1": 1.58, "cols": 4, "rows": 5}
WINDOW_LIGHTBOX = {"x0": X1 - 1.64, "x1": X1 - 0.30, "z0": 1.66, "z1": 2.04, "depth": 0.12}
VENT_GRILLE = {"x0": X1 - 1.64, "x1": X1 - 0.94, "z0": 0.15, "z1": 0.40}
FRONT_WALL_DECALS = [  # grey-box only, as LEFT_WALL_DECALS
    ("Poster_F", 0.04, 0.38, 1.20, 1.65),
    ("Stickers_F", X0 + 0.05, X0 + 0.25, 1.10, 1.70),
]

# ---- Canopy lettering (fitted to the reference) -----------------------------
# Front band text fills X x0..x1 (starts at the body corner); a ring mark follows it.
# z sits a little under the yellow face's centre (the font's centring includes descenders).
CANOPY_TEXT_FRONT = {"x0": X0, "x1": X0 + 2.77, "ring_x": X0 + 2.95, "z": (FACE_Z0 + FACE_Z1) / 2 - 0.10}
# Left band text runs from the back (y0) toward the front corner (y1); the bowl icon sits near the corner.
CANOPY_TEXT_LEFT = {"y0": 1.10, "y1": -0.92, "bowl_y": -1.45, "z": (FACE_Z0 + FACE_Z1) / 2 - 0.06}

# ---- Corner vertical sign ---------------------------------------------------
# Hangs off the right end of the front fascia, clear of the canopy corner post.
# Signage pass (2026-10-05): moved forward, level with the front of the corner post and dropping
# further below the edge beam, so the cinematic camera sees it beside the fascia's end as in the
# reference (it used to sit 0.25 m behind the fascia line, hidden by the canopy's right end). Its
# printed face is a graphics card (kiosk/graphics.py); the box keeps the lit diffuser behind it.
CORNER_SIGN = {"x": CANOPY_X1 + 0.29, "y": CANOPY_Y0 - 0.02, "w": 0.28, "d": 0.10,
               "z0": FASCIA_Z0 - 0.28, "z1": CANOPY_TOP - 0.05}  # z0 was FASCIA_Z0 - 0.13

# ---- Roof machinery (on the deck at CANOPY_TOP) -----------------------------
# Roof pass (2026-10-04, brief 4): the roof reads as a crowded mechanical ecosystem of equipment
# installed at different times. Four clusters overlap from the camera side (left to right in frame):
#   A  HVAC zone on the front-left corner: the packaged HVAC unit on a roof curb right at the corner
#      (the anchor mass, fan on its front), the louvred condenser behind it along the left edge, and
#      a small unit with a round port behind that;
#   B  a horizontal service vessel along the front, flanged into the HVAC's side, on saddles;
#   C  upright tanks and elbows: a tall banded tank, a squat receiver with a gooseneck into it, and
#      a tiered separator fed from the vessel;
#   D  a swivel hose reel turned toward the street, the control cabinet, a slim sensor mast and the
#      white terminal box on the front-right corner.
# Nothing rises above the earlier tallest point (4.32 m). The HVAC is broader, lower and right at the
# corner: being nearer the camera it reads as the biggest mass, so it is kept low enough that the
# kiosk's silhouette from the hero camera is no taller than before the pass. The floor camera hides about 0.4 m of an item for every metre it sits behind
# the coping, so the clusters keep to the front ~1.2 m of the deck; the back holds a few low units
# that show in the overview. Heights are above whatever the item stands on.
# Supports: everything stands on a skid, a curb, dunnage rails, a stand or a plinth.
# Skids, chequer-plate equipment bases on channel frames: (name, x0, x1, y0, y1, h)
ROOF_SKIDS = [
    ("Skid_C", 0.29, 1.32, -2.24, -1.28, 0.10),  # C: separator, tank, receiver
    ("Skid_D", 1.56, 2.80, -2.22, -0.86, 0.10),  # D: reel, control cabinet, mast, white box
]
# Flashed roof curbs (the HVAC sits on one, its duct and conduits go down through it): (name, x0, x1, y0, y1, h)
ROOF_CURBS = [("Curb_HVAC", -3.06, -1.88, -2.06, -1.09, 0.06)]
# Dunnage: two steel channels along `axis` on short posts or pads: (name, x0, x1, y0, y1, h, axis)
ROOF_RAILS = [
    ("Rails_AC", -3.03, -2.35, -0.96, 0.26, 0.14, "Y"),
    ("Rails_Vessel", -1.36, 0.01, -2.06, -1.50, 0.08, "Y"),  # one channel under each saddle
    ("Rails_BackA", -1.52, -0.58, 0.38, 1.22, 0.10, "X"),
]
# Boxes: (name, cx, cy, w(X), d(Y), h)
ROOF_BOXES = [
    # A
    ("TallCabinet", -2.47, -1.575, 1.26, 1.05, 0.68),  # the packaged HVAC unit (anchor; name kept for older scripts)
    ("ACCondenser", -2.69, -0.35, 0.66, 1.18, 0.55),  # louvre grille on the -X face; set in and a step lower than the HVAC
    ("SmallUnit", -2.86, 0.58, 0.56, 0.60, 0.46),  # round port on the -X face
    # D
    ("ControlCabinet", 2.55, -1.10, 0.52, 0.40, 0.92),  # rain hood, label, hazard sticker
    ("WhiteBox", 2.62, -2.00, 0.36, 0.42, 0.50),
    # back
    ("FanBox", 2.22, -0.28, 0.62, 0.62, 0.44),  # refrigeration condensing unit, fan on top
    ("VentHousing", 0.62, 0.50, 0.90, 0.72, 0.56),
    ("BackBox_A", -1.05, 0.80, 0.90, 0.80, 0.78),
    ("BackBox_B", -2.75, 1.30, 0.70, 0.70, 0.45),
    ("BackBox_C", 1.95, 1.15, 0.60, 0.56, 0.62),
]
ROOF_STACKED = {}  # item -> the box it stands on (none: complexity comes from clustering, not height)
ROOF_LIFT = {"ControlCabinet": 0.08}  # short stands
# B: horizontal service vessel along X: shell x0..x1 (a reducer and a flanged stub run from x0 into the
# HVAC's +X face), axis y and height above the deck (raised on tall saddles so most of it clears the
# coping from the floor camera), radius, bolted joint, saddles (on the Rails_Vessel channels)
ROOF_VESSEL = {"x0": -1.56, "x1": 0.20, "cy": -1.78, "z": 0.58, "r": 0.27, "stub_r": 0.085, "joint_x": -0.68, "saddles": (-1.33, -0.02)}
# C: upright vessels: (name, cx, cy, radius, body height); the tank gets a dome, the separator is tiered
ROOF_TANKS = [
    ("Tank", 1.00, -1.92, 0.27, 0.84),  # front: the tallest rounded form
    ("Receiver", 0.72, -1.50, 0.18, 0.46),  # behind; its gooseneck arches over into the tank
    ("Separator", 0.50, -2.03, 0.17, 1.10),  # front, beside the vessel's dished end
]
# Rectangular supply duct from the HVAC's back to a drop into the deck: (x, y) path, section w x h,
# centre height above the deck
ROOF_DUCT = {"path": [(-1.95, -1.04), (-1.95, -0.42), (0.40, -0.42)], "w": 0.32, "h": 0.26, "z": 0.58}
EXHAUST_STACK = {"cx": -2.15, "cy": 1.55, "r": 0.10, "h": 1.00}  # flue, back-left
EXHAUST_FAN = {"cx": -0.20, "cy": 0.95, "curb": 0.50, "r": 0.32}  # kitchen exhaust: a mushroom fan on its curb, back centre
# D: hose reel on a swivel base, its axis turned `yaw` degrees from -X toward -Y (toward the street)
CABLE_REEL = {"cx": 2.00, "cy": -1.78, "radius": 0.39, "width": 0.34, "yaw": 35.0}
MAST = {"cx": 2.66, "cy": -1.58, "w": 0.06, "h": 1.18}  # slim sensor mast (pipe), red beacon on top

# ---- Free-standing props ----------------------------------------------------
# Placed from the walls (X0/X1/Y0/Y1), so they move out with them.
LANTERN_L = {"x": X0 - 0.40, "y": Y1 - 0.25, "z": 1.68, "radius": 0.175, "h": 0.65}
LANTERN_R = {"x": X1 - 0.15, "y": Y0 - 0.40, "z": 1.45, "radius": 0.15, "h": 0.55}
# Pedestal tiers under the left lantern: (size, height)
LANTERN_L_PEDESTAL = [(0.40, 0.35), (0.32, 0.30), (0.24, 0.25)]
# Boxes on the ground: (name, cx, cy, w, d, h)
GROUND_BOXES = [
    ("CrateStack_A", X0 - 0.55, Y1 + 0.45, 0.60, 0.50, 0.75),
    ("CrateStack_B", X0 - 0.85, Y1 + 0.10, 0.50, 0.50, 1.00),
    ("RedCrate", X0 - 0.25, Y1 - 0.50, 0.40, 0.30, 0.30),
    ("UtilityCabinet", X1 + 0.15, Y0 - 0.20, 0.45, 0.40, 0.85),
]
# Bins: (name, cx, cy, radius, h)
BINS = [
    ("Bin_Green", X0 - 0.32, Y0 + 0.25, 0.22, 0.65),  # clear of the base frame
    ("Bin_Grey", X1 + 0.70, Y0 - 0.45, 0.22, 0.50),
]
STOOLS = [(-1.55, Y0 - 0.55), (-0.25, Y0 - 0.55)]  # Ø 0.36 seat, 0.75 m tall; framing the under-counter sign
RAILING = {"x": X0 - 0.90, "y0": Y1 - 0.35, "y1": Y1 + 0.95, "h": 1.00}

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

# Close-up review cameras for the surfacing passes, shared by Blender checks and Unreal's LS_Review
# (Unreal/Scripts/make_review.py): name -> (location, look-at target, lens mm), kiosk frame metres.
REVIEW_CAMS = {
    "DoorWall": ((X0 - 3.1, -0.35, 1.10), (X0, 0.30, 1.10), 28),
    "ServiceWindow": ((-1.10, Y0 - 3.2, 1.25), (-1.00, Y0, 1.25), 26),
    "FasciaCorner": ((CANOPY_X0 - 1.3, CANOPY_Y0 - 1.5, 1.90), (CANOPY_X0 + 0.45, CANOPY_Y0 + 0.40, 2.55), 26),
    "Roof": ((-4.4, -4.5, 4.30), (-1.1, -1.4, 3.10), 28),
    "UnderCanopy": ((-3.55, -3.85, 0.25), (-1.70, -1.90, 2.35), 22),
    "WearDetail": ((X0 - 1.0, -0.40, 0.70), (X0, -0.42, 0.55), 32),
}
# Signage pass (2026-10-05, brief 6): extra review shots, appended after "Reference" in LS_Review so the
# older shots keep their frame numbers. Kept out of REVIEW_CAMS on purpose: weather.py uses REVIEW_CAMS
# as bake viewpoints, and the weathering is locked.
GRAPHICS_REVIEW_CAMS = {
    "LeftSign": ((X0 - 2.55, -0.55, 1.20), (X0 - 0.35, Y1 - 0.30, 1.62), 30),  # the ramen lantern, back of the door wall
    "RightSign": ((0.80, Y0 - 3.55, 1.05), (X1 + 0.25, Y0 - 0.45, 2.00), 24),  # 24h sign, corner sign, window lightbox
    "DecalCloseup": ((X0 - 1.30, -1.30, 1.05), (X0, -0.72, 0.92), 34),  # door-wall poster cluster and old residue
}
# Kitchen pass (2026-10-09, prompt 7): shots appended after the signage ones (older shots keep their
# frames); make_review.py adds "Cinematic" (the sweep camera at Mid, theta 0) after these.
KITCHEN_REVIEW_CAMS = {
    "KitchenPOS": ((-1.55, Y0 - 1.25, 1.50), (-2.33, Y0 - 0.12, 1.30), 35),  # the order terminal, angled
    "KitchenShelves": ((-1.05, Y0 - 0.60, 1.42), (-0.70, -0.05, 1.45), 24),  # into the opening: back wall + shelving
    "CounterTop": ((-1.45, Y0 - 0.95, 1.50), (-1.15, Y0 - 0.20, 1.00), 28),  # the customer counter's surface
    "UnderCounter": ((-0.75, Y0 - 1.75, 0.50), (-0.75, Y0, 0.52), 20),  # storage under the counter
}
# Exterior pass (2026-10-09, prompt 8): ground props round the footprint. Appended after "Cinematic" (older
# shots keep their frames); make_review.py adds "OrbitA" / "OrbitB" (the sweep camera at its two stops) after these.
EXTERIOR_REVIEW_CAMS = {
    "ExtDoorSide": ((X0 - 3.2, -0.70, 1.00), (X0 - 0.40, 1.20, 0.60), 24),  # the door-side delivery / storage cluster, door at right
    "ExtDoorCorner": ((X0 - 2.0, Y0 - 1.75, 0.80), (X0 - 0.25, Y0 + 0.25, 0.45), 28),  # bins and empties at the front-left corner
    "ExtService": ((1.10, Y0 - 3.0, 0.85), (X1 + 0.25, Y0 - 0.35, 0.55), 26),  # the service cluster at the front-right corner
    "ExtFrontLow": ((-0.85, Y0 - 2.9, 0.42), (-0.85, Y0, 0.50), 18),  # stools, under-counter storage, clearances
}

# Rain contact pass (2026-10-09, prompt 9): appended after OrbitB in LS_Review (older shots keep their frames).
WET_REVIEW_CAMS = {
    "WetFrontLeft": ((X0 - 1.85, Y0 - 1.95, 0.55), (X0 - 0.55, Y0 - 0.55, 0.14), 24),  # the platform's wet/dry transition at the near corner
    "WetDrain": ((1.55, Y0 - 1.95, 0.62), (2.45, Y0 - 0.62, 0.16), 26),  # the front-right downpipe, its splash block and run-off trail
    "WetDripCorner": ((X0 - 2.85, Y0 - 3.15, 1.10), (X0 - 0.90, Y0 - 0.90, 1.10), 22),  # the near corner post's drip
    "WetDrip": ((1.15, Y0 - 3.30, 1.15), (2.62, Y0 - 0.88, 1.12), 22),  # the edge-box drip (after WetDripCorner: its 16 frames catch a drop falling and landing): source under the fascia, fall, landing
    "WetSteamPot": ((-0.62, Y0 - 0.95, 1.55), (-0.17, -0.30, 1.45), 35),  # the stock pot's wisp under the hood
}
# A fixed camera for the motion preview (make_review.py builds LS_WetFX from LS_Sweep with this camera)
WET_MOTION_CAM = ((0.95, Y0 - 3.90, 0.55), (2.35, Y0 - 0.55, 1.45), 20)

# Final polish (prompt 10): longer lenses from the video camera's own positions, so a close look keeps the viewer's
# perspective: name -> (orbit angle deg: 0 = Cinematic, -/+ VIDEO_CAM arc = orbit stops A / B, look-at target, lens mm).
# make_review.py --polish builds LS_Polish: Cinematic, OrbitA, OrbitB, these, then POLISH_DETAIL_SHOTS (existing cams).
POLISH_REVIEW_CAMS = {
    "CineRoof": (0.0, (-0.75, -0.55, 4.05), 50),  # the roof machinery and the flue plume as the cinematic camera sees them
    "OrbitARoof": (-45.0, (-1.10, 0.10, 3.95), 50),
    "OrbitBRoof": (45.0, (0.10, -0.95, 4.00), 50),  # the vessel, tanks, reel and the kitchen fan's plume
}
POLISH_DETAIL_SHOTS = ["CounterTop", "ExtDoorCorner", "DecalCloseup", "WetSteamPot"]

# ---- Detailed shell (build_kiosk.py) -------------------------------------------------
SHELL = {
    "panel_t": 0.025,  # steel panel thickness; outer face sits on the wall plane
    "panel_gap": 0.014,  # gap between neighbouring panels (was 0.008; seams now read from the camera)
    "panel_bevel": 0.004,
    "panel_jitter_out": 0.007,  # replacement sheets stand up to this far proud
    "refit_chance": 0.3,  # chance a sheet is a later replacement
    "panel_jitter_tilt_deg": 0.12,
    "lap_w": 0.035,  # overlap at a lap joint
    "lap_t": 0.008,  # how far a lapping sheet stands out
    "strip_w": 0.11,  # wide bolted reinforcement strip over a joint
    "strip_t": 0.018,
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
    "rail_h": 0.035,  # dark frame rails around each lightbox face (was 0.045)
    "rail_t": 0.035,
    "diffuser_inset": 0.012,  # lit face sits this far behind the frame line
    "mullion_every": 1.25,
    "rail_rivet_pitch": 0.15,
    "soffit_seam_every": 1.2,
}

# ---- Structural massing (kiosk/massing.py -> SM_Kiosk_Structure) ------------------------
# Massing pass (2026-10-04): a heavier, more industrial body without moving the walls or the
# openings fitted to the reference. Mass is added outward from the wall planes.
MASSING = {
    "base_h": 0.26,  # dark steel base frame round the bottom of the walls (over the old skirt)
    "base_proud": 0.055,
    "base_lip_h": 0.03,  # drip ledge along its top
    "base_lip_proud": 0.07,
    "header_h": 0.13,  # dark header beam under the soffit (over the old top beam)
    "header_proud": 0.07,
    "corner_t": 0.075,  # steel angles wrapping the vertical corners, proud of base and header
    # (left/right, front/back) -> (flange width on the front/back wall, on the left/right wall).
    # Front-left flanges stay clear of the ticket machine and the junction box.
    "corners": {("left", "front"): (0.14, 0.18), ("right", "front"): (0.22, 0.22),
                ("left", "back"): (0.22, 0.22), ("right", "back"): (0.22, 0.22)},
    # Proportion pass (1B): the service opening reads as cut through a thick wall: deeper jambs and
    # hood (were 0.10 x 0.09 and 0.20 proud) and a dark reveal lining the first part of the opening.
    "service_jamb_w": 0.13,  # thick jambs either side of the service window
    "service_jamb_proud": 0.20,
    "service_hood": {"x0": SERVICE_WINDOW["x0"] - 0.22, "x1": SERVICE_WINDOW["x1"] + 0.22,
                     "z0": SERVICE_WINDOW["z1"] + SHELL["frame_w"], "z1": 2.10, "proud": 0.30},
    "service_reveal": {"t": 0.035, "depth": 0.16},  # lining inside the opening, back from the wall plane
    "bay": {"x0": X1 - 1.89, "x1": X1 - 0.08, "post_w": 0.13, "proud": 0.10, "sill_z1": 0.50},  # glazed-window box-out
}
# Wall-mounted housings: (name, wall, u0, u1, z0, z1, depth)
WALL_HOUSINGS = [
    ("VentHousing_R", "right", Y0 + 0.15, Y0 + 1.15, 0.40, 2.00, 0.48),
    ("UtilityBox_L", "left", Y0 + 0.60, Y0 + 0.99, 1.12, 1.72, 0.13),
]
# Overlapping repair plates: (wall, u0, u1, z0, z1, proud, tilt_deg, material)
# Construction pass: the door-wall plate moved up beside the fuse box (the electrical cabinet and
# exhaust fan took its old place); construction.py bolts every plate down.
REPAIR_PLATES = [
    ("left", Y0 + 0.08, Y0 + 0.53, 1.84, 2.10, 0.016, 0.5, "Kiosk_YellowPaint_Faded"),
    ("left", Y0 + 0.17, Y0 + 0.57, 0.40, 0.72, 0.016, -0.7, "Kiosk_YellowPaint_Dark"),
    ("right", 0.25, 1.15, 0.55, 1.65, 0.016, -0.4, "Kiosk_YellowPaint_Dark"),
]

# ---- Construction detail (kiosk/construction.py -> SM_Kiosk_Construction) --------------------
# Construction pass (2026-10-04, brief 2): the body should read as an old industrial shell that has
# been repaired, retrofitted, reinforced and rewired for decades, through geometry alone (weathering,
# signage and the cable network come in later passes). The proportions are locked; everything here
# is layered onto the approved walls, in three scales: large (cabinet, vents, the service posts),
# medium (plates, frames, boxes, brackets) and small (bolts, rivets, seams).
# Wall coordinates as in shell.py: u along the wall (front: +X, left: +Y), z height, w outward.

# Panel joints, (u, kind), replacing the even 0.95 m grid. kinds: "seam" a bare gap, "batten" a riveted
# flat bar, "lap" the next sheet laps over this one, "strip" a wide bolted reinforcement strip.
# Deliberately uneven: narrow filler sheets by the door and the service posts, wide sheets elsewhere.
PANEL_JOINTS = {
    "front": [(-2.13, "seam"), (-1.40, "batten"), (-0.50, "lap"), (-0.12, "seam"), (0.44, "strip"),
              (0.98, "seam"), (1.64, "batten"), (2.21, "lap")],
    "left": [(-1.27, "lap"), (-0.655, "batten"), (-0.33, "strip"), (-0.205, "seam"), (0.705, "seam"),
             (0.845, "seam"), (1.36, "lap")],
}
PANEL_WIDTHS = (0.40, 1.10)  # seeded sheet widths on the right and back walls
# Horizontal splits per sheet: chance of one / two splits and their heights; chance the upper part laps
PANEL_SPLITS = {"one": 0.45, "two": 0.2, "z1": (0.70, 1.75), "z2": ((0.55, 0.95), (1.45, 1.85)), "lap": 0.6}
PANEL_PAINT = {"Kiosk_YellowPaint_Faded": 0.18, "Kiosk_YellowPaint_Dark": 0.10}  # odds; the rest Kiosk_YellowPaint

FASTENERS = {"bolt_r": 0.016, "bolt_small_r": 0.012, "rivet_r": 0.010}  # sized to read from the video camera
# (at the Mid pose 1 cm is about 2.5 px of a 4K frame, so nothing smaller than ~2 cm across)

# Service opening, read as layers: wall -> steel posts carrying the hood -> jambs with a bolted steel
# face -> reveal -> an inner steel frame stepping in at the back of the reveal -> interior.
SERVICE_POSTS = {"w": 0.06, "proud": 0.14}  # posts outside each jamb, from the base frame up to the hood
SERVICE_FACE = {"lip": 0.02, "t": 0.014}  # steel facing on the jamb fronts, lapping `lip` over the reveal
SERVICE_INNER_FRAME = {"w": 0.05, "w0": -0.195, "w1": -0.16}  # steps in at the back of the reveal
SERVICE_SWITCH = {"z0": 1.30, "z1": 1.46}  # isolator switch box on the right post's face
# Equipment around the opening: (u0, u1, z0, z1, depth)
FRONT_HOUSING = (0.51, 0.71, 1.06, 1.92, 0.13)  # narrow utility housing between the opening and the window bay
KITCHEN_EXHAUST = (0.03, 0.36, 1.70, 1.94, 0.19)  # hooded extract box beside the hood (louvres face down)
SERVICE_ENTRY = (-2.18, -1.56, 0.47, 0.86, 0.15)  # water/gas service enclosure under the counter
# Inset maintenance doors: (wall, u0, u1, z0, z1)
ACCESS_PANELS = [("front", -0.40, 0.20, 0.46, 0.88), ("left", -0.60, -0.40, 0.46, 1.00)]
# Framed sections (an old opening, blanked off with a plate in an angle frame): (wall, u0, u1, z0, z1)
FRAMED_BLANKS = [("front", -2.545, -2.355, 0.44, 0.88)]  # left of the counter's corner gusset
# Bolted patch plates (on top of REPAIR_PLATES): (wall, u0, u1, z0, z1, tilt_deg, material, fastener)
PATCH_PLATES = [
    ("front", -1.56, -1.25, 0.40, 0.70, -0.8, "Kiosk_YellowPaint_Faded", "rivet"),
    ("front", 0.22, 0.70, 0.40, 0.66, 0.5, "Kiosk_YellowPaint_Dark", "bolt"),
    ("left", 1.30, 1.53, 0.98, 1.66, -0.4, "Kiosk_YellowPaint_Dark", "bolt"),
]
# Horizontal reinforcement strips: (wall, u0, u1, z0, z1)
H_STRIPS = [("left", 0.82, 1.555, 0.92, 0.98)]

# Door wall: electrical cabinet on unistrut rails, an exhaust fan below it, a pull box on a unistrut
# riser beside the door, and a steel channel + gussets reinforcing the door frame.
ELEC_CABINET = {"u0": 0.86, "u1": 1.30, "z0": 1.02, "z1": 1.90, "depth": 0.20, "rail_t": 0.035}
FAN_COVER = {"u": 1.10, "z": 0.68, "r": 0.19, "plate": 0.22}  # plate = half-size of the square mount plate
PULL_BOX = {"u0": -0.60, "u1": -0.40, "z0": 1.50, "z1": 1.74, "depth": 0.10, "riser_u": -0.50}
DOOR_CHANNEL = {"u0": 0.735, "u1": 0.805, "depth": 0.06}  # hinge side, full height

# Under the canopy: purlins parallel to the fascia, unistrut rails carrying the conduits, gussets and
# bolted end plates where the joists meet the edge beam, splice plates on the edge beam, and a few
# shallow housings (tube drivers, the sign power supply strapped to the corner brace, a controller).
SOFFIT_FRAME = {
    "purlin_front_y": -2.01, "purlin_left_x": -2.93, "purlin_h": 0.06, "purlin_w": 0.05,
    "rails_front_x": [-2.48, -1.62, -0.31, 1.18, 2.28], "rails_left_y": [-1.25, 0.35, 0.90],
    "rail_z": (2.175, 2.205),
    "extra_joists": {"x": [2.62], "y": [1.72]},  # beyond the tube runs (joists may not cross a tube)
    "splice_front_x": [-2.85, -1.30, 0.10, 1.40, 2.55], "splice_left_y": [-1.95, -0.50, 0.90],
    # tube drivers hung under the purlins: (side, a0, a1)
    "drivers": [("front", -2.62, -2.32), ("front", 0.08, 0.36), ("front", 1.92, 2.22), ("left", -1.10, -0.80)],
    "psu_along_brace": 0.42,  # metres from the body corner along the diagonal brace
    "controller": (-2.88, -2.72, 0.45, 0.78, 2.08, 2.19),  # x0, x1, y0, y1, z0, z1 (left side, by the wall)
}

# ---- Utility network (kiosk/utilities.py -> SM_Kiosk_Utilities) ------------------------------
# Utility pass (2026-10-04, brief 3): conduit, cable, pipe and drainage runs that tie the equipment of
# the construction pass into one working system. Each run starts and ends at real equipment (a box, a
# gland, a penetration). Three line weights: heavy (the drain, the HVAC suction line, the kitchen vent,
# the soffit trunk), medium (rigid conduit, the water line, bundles) and fine (signal and light wiring).
# Most runs are rigid and clamped; a few flexible ones hang with slack as accents.
# Wall coordinates as in shell.py (u along the wall, z height, w out from the wall plane).
UTILITIES = {
    # door wall: service entrance from the platform (power -> meter box, comms -> data box), with a jog
    "entrance": {"u": (-1.215, -1.13), "w": 0.10, "r": (0.024, 0.014), "jog": (0.93, 1.005, -1.055)},
    "fuse_feed": {"u_drop": -0.66, "z_top": 1.97, "z_in": 1.62, "r": 0.016},  # fuse box -> pull box
    "data_riser": {"u": -0.755, "w": 0.032, "r": 0.011},  # data box -> tee on the old wall conduit
    "card_reader": (-0.345, -0.275, 1.10, 1.245, 0.035),  # u0, u1, z0, z1, depth (fed from the pull box)
    # electrical cabinet -> soffit: three conduits out of its side, nested elbows, up past the header
    "door_bundle": {"u": (1.475, 1.53, 1.585), "z": (1.62, 1.50, 1.38), "r": (0.016, 0.013, 0.014), "w": 0.098},
    # front wall: two conduits from the front housing's side up the yellow strip beside the kitchen extract
    "housing_risers": {"u": (0.455, 0.41), "z": (1.66, 1.46), "r": (0.014, 0.012), "w": 0.10},
    # soffit: galvanised trunk hung under the joists along the front, a run along the left to the
    # controller, and the sign circuit under both fascia edge beams (from the sign power supply)
    "trunk": {"y": -1.95, "z": 2.13, "r": 0.02, "x0": -2.55, "x1": 2.24, "hangers": (-1.95, -0.95, 0.05, 1.00, 1.85)},
    "left_run": {"x": X0 - 0.247, "z": 2.125, "r": 0.018, "y0": -1.55, "hangers": (-1.20, -0.10, 0.25)},
    "fascia_conduit": {"inset": 0.24, "z": 2.13, "r": 0.014, "lantern_box_y": 1.25},
    "driver_bundle": {"y": -2.06, "z": 2.205, "x0": -2.66},  # thin cables feeding the tube drivers
    # roof drain, front-right: outlet under the front edge beam, a run back under the soffit, a cast
    # downpipe on the window bay's corner, and a shoe onto a splash block
    "drain": {"x": X1 - 0.165, "w": 0.165, "r": 0.045, "outlet_y": CANOPY_Y0 + 0.15, "run_z": 2.03,
              "shoe": (0.30, 0.20)},
    # roof: a disconnect switch on the HVAC front face, right of its service door (seen from the floor
    # camera); roof pass: moved with the HVAC, the riser now comes up beside its right end
    "roof_disconnect": {"x0": -2.02, "x1": -1.86, "z0": 3.24, "z1": 3.46, "d": 0.10, "riser": (-1.78, -2.15)},
}

# ---- Weathering (kiosk/weather.py -> Unreal/RawContent/weather/T_KioskWear_*.png) ------------------
# Surfacing pass (2026-10-04, brief 5: materials only, geometry locked). 20-40 years of rain, repairs,
# repainting, cooking and hands. Every mark has a physical driver baked from the geometry: rain-flow
# streaks under fasteners/brackets/ledges (a 2.5D relief of each camera-facing side), chips on exposed
# edges, rust where water sits, grime in recesses, grease and soot at the kitchen openings, polish where
# hands go. The masks are potentials; Unreal's per-material instances decide how much of each shows
# (Unreal/Scripts/scene_config.KIOSK_WEATHER), so each roof unit can have its own history.
WEATHER = {
    "res": 8192,  # atlas size (WeatherUV = TEXCOORD_1); ~2-3 mm texels on the surfaces the cameras see
    # materials that get WeatherUV islands and the weathered master material in Unreal
    "materials": ["Kiosk_YellowPaint", "Kiosk_YellowPaint_Dark", "Kiosk_YellowPaint_Faded", "Steel_Dark", "Steel_Grey",
                  "Steel_Galvanised", "Steel_Charcoal", "Steel_Galv_Dull", "Steel_Aged_Warm", "Paint_Grey_Faded",
                  "Rust_Red", "Machine_Body", "Conduit_Painted", "Pipe_Cast", "Copper_Aged", "Lightbox_Yellow",
                  "Platform_Concrete"],
    "sections": ["Ground", "Body", "Structure", "Construction", "ServiceSide", "DoorSide", "Canopy", "Roof", "Utilities"],
    "hidden_scale": 0.3,  # UV scale of faces no video/review viewpoint sees (back walls, canopy insides)
    "cell": 0.004,  # rain-flow relief cell (m)
    "fastener_diag": 0.065,  # parts smaller than this (bbox diagonal, m) count as bolts / rivets / latches
    "streak_len": (0.12, 0.65),  # random run length range (m) of a streak before it fades
    "rain_angle_deg": 32.0,  # wind-driven rain reaches under the canopy at this angle from vertical
    "splash_top": (0.30, 0.62),  # splash-back band top above the ground (m), varies along the wall
    # paint generations of the yellow sheets: odds of (original, faded, darker amber, newer repaint)
    "paint_odds": (0.52, 0.20, 0.12, 0.16),
}
# Hands: (kind, p0, p1, radius, strength) capsules in the kiosk frame. touch = polished, cleaner;
# abrade = knocks and scrapes (more chips and scratches, no polish).
_DOOR_LATCH_Y = DOOR["y"] - DOOR["w"] / 2
WEATHER_TOUCH = [
    ("touch", (X0 - 0.05, _DOOR_LATCH_Y + 0.08, PLATFORM_H + 1.0), (X0 - 0.05, _DOOR_LATCH_Y + 0.21, PLATFORM_H + 1.0), 0.07, 1.0),  # door lever
    ("touch", (X0 - 0.01, _DOOR_LATCH_Y + 0.02, PLATFORM_H + 0.80), (X0 - 0.01, _DOOR_LATCH_Y + 0.02, PLATFORM_H + 1.45), 0.07, 0.6),  # door edge
    ("touch", (X0, _DOOR_LATCH_Y + 0.10, PLATFORM_H + 1.08), (X0, _DOOR_LATCH_Y + 0.10, PLATFORM_H + 1.30), 0.14, 0.35),  # push marks
    ("abrade", (X0, _DOOR_LATCH_Y + 0.05, PLATFORM_H + 0.05), (X0, DOOR["y"] + DOOR["w"] / 2 - 0.05, PLATFORM_H + 0.05), 0.22, 0.8),  # kicks
    ("touch", (COUNTER["x0"] + 0.1, Y0 - COUNTER["projection"], COUNTER["z"] - 0.012), (COUNTER["x1"] - 0.1, Y0 - COUNTER["projection"], COUNTER["z"] - 0.012), 0.05, 1.0),  # counter nose
    ("touch", (COUNTER["x0"] + 0.2, Y0 - COUNTER["projection"] + 0.1, COUNTER["z"]), (COUNTER["x1"] - 0.2, Y0 - COUNTER["projection"] + 0.1, COUNTER["z"]), 0.11, 0.45),  # forearms
    ("touch", (SERVICE_WINDOW["x0"] - 0.10, Y0 - 0.20, 1.02), (SERVICE_WINDOW["x0"] - 0.10, Y0 - 0.20, 1.50), 0.08, 0.55),  # jamb fronts
    ("touch", (SERVICE_WINDOW["x1"] + 0.10, Y0 - 0.20, 1.02), (SERVICE_WINDOW["x1"] + 0.10, Y0 - 0.20, 1.50), 0.08, 0.55),
    ("touch", (TICKET_MACHINE["x0"] + 0.06, Y0 - TICKET_MACHINE["depth"], 1.22), (TICKET_MACHINE["x1"] - 0.06, Y0 - TICKET_MACHINE["depth"], 1.40), 0.09, 0.7),
    ("touch", (-0.03, Y0 - 0.22, SERVICE_SWITCH["z0"] + 0.05), (-0.03, Y0 - 0.22, SERVICE_SWITCH["z1"]), 0.06, 0.7),  # isolator
    ("touch", (-0.328, Y0 - 0.02, 0.537), (-0.328, Y0 - 0.02, 0.803), 0.045, 0.8),  # front access panel latches
    ("touch", (0.128, Y0 - 0.02, 0.67), (0.128, Y0 - 0.02, 0.67), 0.045, 0.8),
    ("touch", (X0 - 0.02, -0.528, 0.537), (X0 - 0.02, -0.528, 0.923), 0.045, 0.8),  # door-wall access panel latches
    ("touch", (X0 - 0.02, -0.472, 0.73), (X0 - 0.02, -0.472, 0.73), 0.045, 0.8),
    ("touch", (X0 - 0.25, ELEC_CABINET["u0"] + 0.055, 1.37), (X0 - 0.25, ELEC_CABINET["u0"] + 0.055, 1.60), 0.07, 0.8),  # cabinet handle
    ("abrade", (X0 - 0.03, Y0 - 0.03, PLATFORM_H), (X0 - 0.03, Y0 - 0.03, 1.9), 0.13, 0.6),  # the exposed body corner
    ("abrade", (STOOLS[0][0], Y0 - 0.02, 0.62), (STOOLS[1][0], Y0 - 0.02, 0.62), 0.22, 0.5),  # stools knocking the counter front
    ("abrade", (X0 - 0.02, BINS[0][2] - 0.3, 0.45), (X0 - 0.02, BINS[0][2] + 0.3, 0.45), 0.3, 0.5),  # bin by the corner
    ("abrade", (X0 - 0.02, Y1 - 0.9, 0.40), (X0 - 0.02, Y1, 0.40), 0.35, 0.6),  # crates against the door wall
]
# Heat and kitchen: (kind, p0, p1, radius, strength). soot = dark matte film, grease = brown glossy film
# (also drips into the grease streaks), heat = scorched steel near the flue.
_HOOD = MASSING["service_hood"]
WEATHER_HEAT = [
    ("grease", (_HOOD["x0"], Y0 - 0.12, _HOOD["z0"]), (_HOOD["x1"], Y0 - 0.12, _HOOD["z0"]), 0.22, 0.9),  # hood underside + lip
    ("soot", (_HOOD["x0"] + 0.1, Y0 - 0.15, _HOOD["z1"] + 0.06), (_HOOD["x1"] - 0.1, Y0 - 0.15, _HOOD["z1"] + 0.06), 0.30, 0.7),  # above the hood
    ("soot", (_HOOD["x0"] + 0.2, Y0 - 0.55, CANOPY_BOTTOM), (_HOOD["x1"] - 0.2, Y0 - 0.55, CANOPY_BOTTOM), 0.45, 0.55),  # soffit above
    ("grease", (KITCHEN_EXHAUST[0], Y0 - 0.12, KITCHEN_EXHAUST[2]), (KITCHEN_EXHAUST[1], Y0 - 0.12, KITCHEN_EXHAUST[2]), 0.16, 1.0),
    ("soot", (KITCHEN_EXHAUST[0], Y0 - 0.08, KITCHEN_EXHAUST[3] + 0.08), (KITCHEN_EXHAUST[1], Y0 - 0.08, KITCHEN_EXHAUST[3] + 0.2), 0.20, 0.6),
    ("soot", (SERVICE_WINDOW["x1"], Y0, 1.98), (FRONT_HOUSING[1] + 0.3, Y0, 2.0), 0.28, 0.35),  # upper wall by the kitchen
    ("grease", (EXHAUST_FAN["cx"], EXHAUST_FAN["cy"], CANOPY_TOP + EXHAUST_FAN["curb"]), (EXHAUST_FAN["cx"], EXHAUST_FAN["cy"], CANOPY_TOP + EXHAUST_FAN["curb"] + 0.35), 0.55, 0.9),
    ("soot", (EXHAUST_STACK["cx"], EXHAUST_STACK["cy"], CANOPY_TOP + EXHAUST_STACK["h"] - 0.1), (EXHAUST_STACK["cx"], EXHAUST_STACK["cy"], CANOPY_TOP + EXHAUST_STACK["h"] + 0.15), 0.22, 1.0),
    ("heat", (EXHAUST_STACK["cx"], EXHAUST_STACK["cy"], CANOPY_TOP + 0.45), (EXHAUST_STACK["cx"], EXHAUST_STACK["cy"], CANOPY_TOP + EXHAUST_STACK["h"]), 0.14, 0.8),
]
# Water: explicit wet sources with rust (kind, point, radius, strength): the roof drain outlet, the
# shoe on its splash block and the condensate pad.
WEATHER_WATER = [
    ("rust", (X1 - 0.165, CANOPY_Y0 + 0.15, FASCIA_Z0), 0.10, 1.0),
    ("rust", (X1 - 0.165, Y0 - 0.30, PLATFORM_H + 0.05), 0.22, 0.9),
]

# ---- Weathering refinement (2026-10-04, brief 5B: targeted, not another global pass) -----------
# Four areas only; every other texel keeps its 5A masks exactly (kiosk/weather.py refine()).
#  1 the lit fascia: older but still the cleanest, brightest yellow (per-panel ageing of the diffuser
#    and its glow, dirt at joints, lower edges and corner posts, rust runs from the rail rivets, runoff
#    from the roof over the coping, dried rain spatter);
#  2 the service-window frame: grease and heat at the head, grime where sections overlap, worn counter
#    edges, a few runs from under the hood; the working surfaces are kept cleaned;
#  3 the roof units get visibly different ages (WEATHER_ROOF_UNITS);
#  4 the longest runoff stains start at a named source (WEATHER_RUNOFF).
_LIT_TOP = FACE_Z1 - CANOPY_DETAIL["rail_h"]  # top of the lit diffuser, just under the top rail
_HEADER_LOW = BODY_TOP - MASSING["header_h"]  # underside of the header beam along the walls
WEATHER_FASCIA = {
    # diffuser age per panel between the mullions (front left to right, left wall front to back):
    # orig, amber (yellowed: warmer and ~12% dimmer), bleach (sun-paled), new (a newer replacement)
    "panels": {"front": ["orig", "amber", "orig", "bleach", "new"], "left": ["amber", "orig", "bleach", "orig"]},
    "bottom_band": 0.09,  # dirt collects above the bottom rail, up to this high (m)
    "joint_band": 0.045,  # dirt either side of each mullion and at the stiles (m)
    "corner_reach": 0.35,  # extra dirt and rust near the canopy corner posts (m)
    "rivet_rust_odds": 0.35,  # top-rail rivets that weep a rust run down the diffuser
    "chip_boost": 1.6,  # occasional small chips on the frame rails and mullions
}
# Long runs: (side, u, z, width, length, strength, sub-streaks, kind, materials). side "front" (u = x)
# or "left" (u = y); the run starts on the first surface of `materials` just below (u, z) and follows
# the rain-flow relief from there (it drips across small gaps and stops where its surface ends).
# materials: "lit" (the diffuser), "yellow" (the wall sheets) or "any".
_FRONT_RUNOFF = [  # water off the roof units and the deck, over the front coping onto the lit face
    (-3.00, 0.05, 0.44, 0.50, 2), (-2.50, 0.08, 0.40, 0.40, 3), (-1.90, 0.05, 0.44, 0.55, 2),  # HVAC curb + drip edge
    (-1.33, 0.06, 0.34, 0.45, 2), (-0.02, 0.06, 0.34, 0.40, 2),  # vessel saddles
    (0.40, 0.05, 0.40, 0.45, 2), (1.00, 0.10, 0.44, 0.55, 3), (1.40, 0.04, 0.28, 0.35, 1),  # skid C: separator, tank
    (1.58, 0.05, 0.44, 0.70, 2),  # the reel hose lies over the coping here and wicks water down
    (2.20, 0.06, 0.30, 0.35, 2), (2.62, 0.05, 0.30, 0.40, 1),  # reel skid, white box
]
_LEFT_RUNOFF = [  # over the left coping
    (-2.00, 0.05, 0.44, 0.50, 2), (-1.55, 0.08, 0.40, 0.40, 3), (-1.08, 0.05, 0.40, 0.45, 2),  # HVAC
    (-0.90, 0.04, 0.30, 0.30, 1), (0.25, 0.05, 0.34, 0.40, 2),  # condenser rails
    (0.58, 0.06, 0.34, 0.35, 2), (1.30, 0.06, 0.40, 0.40, 2), (1.62, 0.04, 0.44, 0.45, 1),  # small unit, back box, flue
]
_HOOD5 = MASSING["service_hood"]
WEATHER_RUNOFF = (
    [("front", u, _LIT_TOP, w, ln, s, n, "dark", "lit") for u, w, ln, s, n in _FRONT_RUNOFF]
    + [("left", u, _LIT_TOP, w, ln, s, n, "dark", "lit") for u, w, ln, s, n in _LEFT_RUNOFF]
    + [  # yellow walls: a few long, faint runs from canopy joints and utility penetrations
        ("front", -2.30, _HEADER_LOW, 0.05, 0.50, 0.20, 2, "dark", "yellow"),  # soffit junction drop into the header
        ("front", -2.46, _HEADER_LOW, 0.04, 1.10, 0.16, 1, "dark", "yellow"),  # canopy brace joint at the body corner
        ("front", 0.385, _HEADER_LOW, 0.03, 1.20, 0.18, 1, "dark", "yellow"),  # reinforcement-strip joint, both edges
        ("front", 0.495, _HEADER_LOW, 0.03, 1.00, 0.15, 1, "dark", "yellow"),
        ("left", -0.39, _HEADER_LOW, 0.04, 1.30, 0.18, 2, "dark", "yellow"),  # soffit joist meets the wall at the strip joint
        ("left", -0.27, _HEADER_LOW, 0.03, 0.90, 0.14, 1, "dark", "yellow"),
        ("left", 1.40, _HEADER_LOW, 0.05, 1.00, 0.17, 2, "dark", "yellow"),  # joist + lap joint
        ("left", -0.75, _HEADER_LOW, 0.05, 0.40, 0.20, 1, "dark", "yellow"),  # junction drop onto the utility box
        ("left", 1.05, _HEADER_LOW, 0.05, 0.25, 0.20, 1, "dark", "yellow"),  # junction drop onto the electrical cabinet
        ("left", -1.50, _HEADER_LOW, 0.04, 1.00, 0.15, 1, "dark", "yellow"),  # canopy brace joint, door-wall side
        # service window: water creeping under the hood lip runs down the jamb facings and the posts
        ("front", -2.02, _HOOD5["z0"], 0.06, 0.60, 0.45, 2, "dark", "any"),
        ("front", -0.13, _HOOD5["z0"], 0.06, 0.60, 0.45, 2, "dark", "any"),
        ("front", -2.12, _HOOD5["z0"] - 0.22, 0.03, 0.70, 0.35, 1, "dark", "any"),  # knee brackets onto the posts
        ("front", -0.03, _HOOD5["z0"] - 0.22, 0.03, 0.70, 0.35, 1, "dark", "any"),
    ]
)
# Service-window frame: extra grease and heat at the head and the jamb tops (WEATHER_HEAT capsules),
# worn counter edges (WEATHER_TOUCH capsules), and a zone where overlapping sections collect dirt.
_SW5 = SERVICE_WINDOW
WEATHER_SERVICE = {
    "zone": (_HOOD5["x0"] - 0.30, _HOOD5["x1"] + 0.30, COUNTER["z"] - 0.10, BODY_TOP, Y0 + 0.25),  # x0, x1, z0, z1, y max
    "overlap_dirt": 0.55,  # dark runs-channel dirt where sections overlap (the grime layer is already full there)
    "heat": [  # the 5A capsule already covers the hood underside; these reach the faces it missed
        ("grease", (_HOOD5["x0"] + 0.05, Y0 - _HOOD5["proud"] - 0.01, _HOOD5["z0"] + 0.02),
         (_HOOD5["x1"] - 0.05, Y0 - _HOOD5["proud"] - 0.01, _HOOD5["z0"] + 0.02), 0.13, 0.65),  # hood front, its lower lip
        ("grease", (_SW5["x0"], Y0 + 0.10, _SW5["z1"] - 0.02), (_SW5["x1"], Y0 + 0.10, _SW5["z1"] - 0.02), 0.13, 0.65),  # reveal + inner frame head
        ("grease", (-2.02, Y0 - 0.21, 1.50), (-2.02, Y0 - 0.21, _HOOD5["z0"]), 0.12, 0.65),  # jamb-facing tops
        ("grease", (-0.13, Y0 - 0.21, 1.50), (-0.13, Y0 - 0.21, _HOOD5["z0"]), 0.12, 0.65),
        ("soot", (_SW5["x0"] + 0.15, Y0 + 0.08, _SW5["z1"]), (_SW5["x1"] - 0.15, Y0 + 0.08, _SW5["z1"]), 0.12, 0.40),  # reveal head
    ],
    "abrade": [
        ("abrade", (COUNTER["x0"], Y0 - COUNTER["projection"] - 0.004, COUNTER["z"]),
         (COUNTER["x1"], Y0 - COUNTER["projection"] - 0.004, COUNTER["z"]), 0.035, 0.9),  # counter nose edge
        ("abrade", (COUNTER["x0"], Y0 - COUNTER["projection"] - 0.004, COUNTER["z"] - 0.07),
         (COUNTER["x1"], Y0 - COUNTER["projection"] - 0.004, COUNTER["z"] - 0.07), 0.03, 0.5),  # nosing bottom edge
        ("abrade", (COUNTER["x0"], Y0 - COUNTER["projection"], COUNTER["z"] - 0.03),
         (COUNTER["x0"], Y0 - COUNTER["projection"], COUNTER["z"]), 0.09, 1.0),  # counter corners
        ("abrade", (COUNTER["x1"], Y0 - COUNTER["projection"], COUNTER["z"] - 0.03),
         (COUNTER["x1"], Y0 - COUNTER["projection"], COUNTER["z"]), 0.09, 1.0),
    ],
    "clean": 0.4,  # working surfaces (counter top, pass-through sill) are wiped daily: dirt layers x this
}
# Roof units, each with its own history: (name, (x0, x1, y0, y1), changes). grime / streak / rust are
# multipliers inside the box; fade (sun-chalked paint), oxide (white-rust bloom on zinc), scuff (light
# abrasion, rubbed lighter) and base (dark water staining wicking up from the unit's base: strength,
# height) are new layers, each limited to the listed materials; flange_rust: rust round the rims of
# flanges, rings and pads.
WEATHER_ROOF_UNITS = [
    ("HVAC", (-3.14, -1.82, -2.27, -1.02), {"fade": (0.85, ["Paint_Grey_Faded"]), "streak": 1.15}),  # the oldest paint
    ("Condenser", (-3.10, -2.32, -0.99, 0.29), {"oxide": (0.80, ["Steel_Galv_Dull"]), "streak": 1.1}),
    ("Vessel", (-1.86, 0.40, -2.10, -1.46), {"scuff": (0.9, ["Steel_Aged_Warm"]), "flange_rust": 1.0}),
    ("Tank", (0.70, 1.31, -2.25, -1.60), {"oxide": (0.5, ["Steel_Galvanised"]), "grime": 0.75, "streak": 0.8,
                                         "base": (0.80, 0.17, ["Steel_Galvanised", "Steel_Dark"])}),
    ("Receiver", (0.52, 0.93, -1.70, -1.29), {"base": (0.60, 0.12, ["Steel_Charcoal", "Steel_Dark"])}),
    ("Separator", (0.31, 0.69, -2.22, -1.84), {"base": (0.70, 0.15, ["Paint_Grey_Faded", "Steel_Dark"])}),
    ("Reel", (1.50, 2.52, -2.26, -1.30), {"grime": 1.35, "streak": 1.3, "rust": 1.35, "fade": (0.35, ["Steel_Charcoal"]),
                                         "flange_rust": 1.0}),
]
# Dark rings on the skid round the upright vessels' bases: (cx, cy, shell radius, reach, strength)
WEATHER_BASE_RINGS = [(t[1], t[2], t[3], 0.14, 0.6) for t in ROOF_TANKS]

# ---- Signage pass (2026-10-05, brief 6): graphics on the kiosk -----------------------------------
# Posters, notices, labels, stickers, nameplates, lit sign faces (textured cards) and marks in the
# paint (Unreal deferred decals). The art and each item's size come from
# Graphics/make_kiosk_graphics.mjs (Unreal/RawContent/graphics/graphics_manifest.json); this table only
# says where each one goes. build_graphics.py lays every card onto the exported kiosk
# (RawContent/kiosk_detail.glb) by raycasting, so paper bends over battens and laps, sits on proud
# sheets and tucks behind conduits, and gives each card the WeatherUV of the surface under it, so in
# Unreal the wall's rain streaks, grime and wetness carry on across the paper.
# Hierarchy: the fascia stays the cleanest, brightest sign; secondary lit signs (ramen lantern, 24h
# box, corner sign, under-counter LED board) are smaller and dimmer; medium posters and notices; then
# the small layer only found up close (labels, inspection stickers, handwritten notes, residue).
#
# Card: (item, wall, u, z, rotation deg, layer, options)
#   wall    "left" = the door wall (u = y, seen from -X, +y to the viewer's left); "front" (u = x)
#   u, z    centre of the card, kiosk frame metres; rotation counter-clockwise as seen
#   layer   stacking where cards overlap (0 = oldest, against the wall)
#   options depth: where the ray starts in front of the wall plane (small for paper on the wall, so it
#           passes behind conduits; past the face for labels on boxes and cabinets); scale; lift
#           (corner "tl"/"tr"/"bl"/"br", reach m, height m) for a peeling corner; flat (one plane at the
#           proudest point, for sign faces); age (0 new .. 1 old: more grime in Unreal)
_L, _F = "left", "front"
GRAPHICS_CARDS = [
    # -- door wall: the poster cluster under the utility box (oldest -> newest). From the cinematic camera
    # the green bin hides the wall below ~0.85 m between y -1.4 and -0.78, so the cluster sits above that
    # line, the KAZE poster's logo just under the box and the older prints spilling over the batten. --
    ("ramen_ad", _L, -0.765, 0.80, -1.5, 0, {"age": 0.9}),  # faded food ad across the batten, clear of the hatch frame
    ("kaze_poster", _L, -0.88, 0.905, 1.2, 2, {"age": 0.6, "lift": ("bl", 0.07, 0.014)}),  # newest, a season old (prompt 10: was age 0.25, read clean); top just under the box
    ("market_flyer", _L, -0.56, 1.21, -2.5, 1, {"age": 0.7, "lift": ("br", 0.05, 0.010)}),  # torn, behind the pull box riser
    ("tape_scrap_0", _L, -0.615, 1.43, 10, 0, {"age": 0.8}),  # corners of notices ripped off long ago
    ("tape_scrap_1", _L, -0.43, 1.02, -20, 0, {"age": 0.8}),
    ("inspection_notice", _L, -0.95, 1.425, 0.8, 0, {"depth": 0.30, "age": 0.75}),  # taped to the utility box door
    ("st_kaze", _L, -0.655, 1.25, 0, 0, {"age": 0.3}),  # on the batten
    # -- door wall: door, equipment labels ------------------------------------------------------
    ("staff_only", _L, 0.30, 1.225, 0.4, 0, {"depth": 0.15, "age": 0.5}),
    ("knock_note", _L, 0.42, 1.05, -3.0, 0, {"depth": 0.15, "age": 0.35}),
    ("st_band", _L, 0.10, 0.92, 7.0, 0, {"depth": 0.15, "age": 0.6}),
    ("id_db02", _L, -0.79, 1.675, 0, 1, {"depth": 0.30}),  # utility box
    ("haz_bolt_small", _L, -1.045, 1.665, 0, 1, {"depth": 0.30}),
    ("volt_3ph", _L, -1.29, 1.48, 0, 0, {"depth": 0.35}),  # meter box
    ("insp_yellow", _L, -1.47, 1.52, 0, 0, {"depth": 0.35, "age": 0.8}),
    ("qr_log", _L, -1.47, 1.30, 0, 0, {"depth": 0.35}),
    ("volt_200", _L, -0.93, 2.035, 0, 0, {"depth": 0.30}),  # fuse box
    ("haz_bolt_small", _L, -1.50, 1.035, 0, 0, {"depth": 0.30}),  # junction box
    ("id_ml3", _L, -0.50, 1.685, 0, 0, {"depth": 0.25}),  # pull box
    ("plate_cabinet", _L, 1.12, 1.79, 0, 1, {"depth": 0.45}),  # electrical cabinet
    ("haz_shock_jp", _L, 1.17, 1.53, 0, 1, {"depth": 0.45}),
    ("no_open", _L, 0.99, 1.68, 0, 1, {"depth": 0.45}),
    ("insp_green", _L, 1.24, 1.30, 0, 1, {"depth": 0.45, "age": 0.2}),
    ("svc_nagase", _L, 1.09, 1.13, -2.0, 1, {"depth": 0.45, "age": 0.4}),
    ("asset_a", _L, 1.24, 1.08, 0, 1, {"depth": 0.45}),
    # -- front wall: around the service window ---------------------------------------------------
    ("cash_card", _F, -1.965, 1.64, 4.0, 0, {"depth": 0.40, "age": 0.9}),  # left jamb, top to bottom
    ("menu_card", _F, -1.965, 1.43, 1.0, 1, {"depth": 0.40, "scale": 0.75, "age": 0.4}),
    ("soldout_note", _F, -1.97, 1.205, -3.0, 2, {"depth": 0.40, "scale": 0.85, "age": 0.15}),
    ("permit", _F, -0.185, 1.665, 0.0, 0, {"depth": 0.40, "scale": 0.95, "age": 0.6}),  # right jamb
    ("price_note", _F, -0.19, 1.47, 3.0, 0, {"depth": 0.40, "scale": 0.95, "age": 0.3}),
    ("pay_decal", _F, -0.185, 1.22, 0.0, 0, {"depth": 0.40, "age": 0.3, "lift": ("tr", 0.025, 0.004)}),
    # (the ticket machine's ticket_strip and asset_a went with it in the kitchen pass, 10/9: the order
    # terminal that replaces it carries its own labels, kiosk/kitchen.py)
    ("id_sg4", _F, -2.44, 1.88, 0.0, 0, {"depth": 0.30}),  # small box above the machine
    # -- front wall: the strip between the opening and the window bay ---------------------------
    ("clinic_poster", _F, 0.255, 1.33, -1.0, 0, {"age": 0.6}),
    ("torn_remnant", _F, 0.25, 1.60, 1.5, 0, {"age": 0.9}),  # top of an older poster, torn down
    ("st_eye", _F, 0.335, 1.085, 0.0, 1, {"age": 0.8}),
    ("st_circle_red", _F, 0.17, 1.065, 0.0, 1, {"age": 0.7}),
    ("haz_hot", _F, 0.29, 1.83, 0.0, 0, {"depth": 0.35, "scale": 0.8}),  # kitchen extract
    ("id_wt", _F, 0.607, 1.86, 0.0, 0, {"depth": 0.30}),  # front housing
    ("insp_blue", _F, 0.66, 1.70, 0.0, 0, {"depth": 0.30, "age": 0.5}),
    ("gyoza_strip", _F, 0.80, 1.22, 0.5, 0, {"depth": 0.25, "age": 0.5}),  # bay post
    ("st_ramenclub", _F, 1.11, 0.655, -4.0, 0, {"depth": 0.12, "age": 0.6}),  # on a window pane
    # -- under the counter, utility cabinet ----------------------------------------------------
    ("flow_gas", _F, -1.80, 0.80, 0.0, 0, {"depth": 0.30}),  # service entry enclosure
    ("svc_minato", _F, -2.05, 0.64, -1.5, 0, {"depth": 0.30, "age": 0.9}),
    ("next_insp", _F, -1.70, 0.62, 0.0, 0, {"depth": 0.30}),
    ("haz_bolt", _F, 2.70, 0.80, 0.0, 0, {"depth": 0.60}),  # utility cabinet by the 24h pole
    ("svc_nagase", _F, 2.88, 0.55, 1.5, 0, {"depth": 0.60, "age": 0.6}),
    ("id_sg4", _F, 2.86, 0.90, 0.0, 0, {"depth": 0.60}),
    # -- lit sign faces (printed acrylic in front of the diffusers) ------------------------------
    ("corner_face", _F, CORNER_SIGN["x"], (CORNER_SIGN["z0"] + CORNER_SIGN["z1"]) / 2, 0.0, 0, {"depth": 1.2, "flat": True}),
    ("counter_face", _F, (UNDER_COUNTER_SIGN["x0"] + UNDER_COUNTER_SIGN["x1"]) / 2,
     (UNDER_COUNTER_SIGN["z0"] + UNDER_COUNTER_SIGN["z1"]) / 2, 0.0, 0, {"depth": 0.20, "flat": True}),
]
# Decals (marks in the paint, Unreal deferred decals): (item, wall, u, z, rotation deg, width m, height m,
# options). Width/height None = the art's own size. depth = where the ray starts, as for cards.
GRAPHICS_DECALS = [
    ("ghost_poster", _L, -0.79, 0.86, -3.5, None, None, {}),  # an older poster's ghost, its glue corners peeking out
    ("marker_dates", _L, -0.48, 0.70, -1.0, None, None, {"depth": 0.10}),  # on the access hatch
    ("marker_breaker", _L, -1.01, 1.955, 0.0, 0.085, 0.062, {"depth": 0.30}),  # fuse box
    ("residue_a", _L, 0.47, 1.47, 5.0, None, None, {"depth": 0.15}),  # a sticker scraped off the door
    ("stencil_k07", _F, -1.80, 1.985, 0.0, 0.25, 0.118, {"depth": 0.45}),  # service hood (light paint)
    ("ghost_dark", _F, -0.80, 1.985, 0.0, 0.52, 0.17, {"depth": 0.45}),  # a sign once bolted to the hood
    ("holes_pair", _F, 0.80, 1.52, 0.0, None, None, {"depth": 0.25}),  # bay post: a removed bracket
    ("residue_b", _F, 0.80, 0.80, 0.0, None, None, {"depth": 0.25}),
    ("residue_c", _F, -0.185, 1.06, 0.0, None, None, {"depth": 0.40}),  # right jamb
    ("holes_row", _F, -1.97, 1.84, 0.0, 0.16, 0.042, {"depth": 0.40}),  # left jamb, an old sign rail
]
# The 24h sign: a narrow lightbox on the old lantern pole at the front-right (LANTERN_R's pole, which the
# utility pass feeds through its cap), clamped to the pole and wired from a box on it. Faces `yaw` deg
# from -Y toward -X (toward the orbit); centre `z`; housing w x h x d (m).
SIGN_24H = {"pole": (LANTERN_R["x"] + 0.12, LANTERN_R["y"]), "pole_r": 0.02, "pole_top": LANTERN_R["z"] + LANTERN_R["h"] / 2 + 0.16,
            "w": 0.20, "h": 0.52, "d": 0.075, "z": 1.47, "yaw": 22.0, "face_inset": 0.016}
# The ramen lantern's lettering, bent onto the paper: (text, size m, angle round the lantern in rad from
# the camera-facing side (+ = the viewer's right), z offset m)
LANTERN_LETTERING = [("ラ\n｜\nメ\nン", 0.095, 0.0, 0.01), ("醤\n油\n・\n味\n噌", 0.036, -0.62, 0.035)]

# ---- Kitchen pass (2026-10-09, prompt 7): the service opening's working kitchen -------------------
# Built on its own (kiosk/kitchen.py, build_kitchen.py -> Unreal/RawContent/kiosk_kitchen.glb), so the
# kiosk export and its weathering bake stay untouched. Unreal trims the old step-2 interior (stock
# shelves, coffee machine, pots, condiments, the ticket machine) out of copies of SM_Kiosk_ServiceSide
# and SM_Kiosk_Body (kiosk_kitchen.py, GeometryScript), and with it the service cavity's lining, so
# the room can be deeper and taller than the old 0.9 m recess.
# Layering seen through the opening: customer counter -> heavy frame -> pass + prep worktop (front)
# -> cooking line on the back counter under a hood -> shelves on the back wall -> darker back corners.
KITCHEN = {
    "front": Y0 + 0.195,  # the room's front wall face: right behind the inner frame at the back of the reveal
    "x0": -2.35, "x1": 0.62,  # wider than the opening: the orbit looks right-back through it, at the right wall
    "depth": 1.45,  # front wall to back wall (was a 0.9 m recess)
    "ceiling": 2.10,  # rear ceiling; a bulkhead keeps the opening head (and the prep light) at 1.80
    "bulkhead_d": 0.25,
    "front_top": 1.012, "front_d": 0.42,  # pass + prep worktop along the front wall (a step above the customer counter)
    "back_top": 0.98, "back_d": 0.48,  # the cooking line (and the prep sink) along the back wall
    "tile_top": 1.46,  # white subway-tile splashback up to here, stainless above
    "shelves": (1.50, 1.80),  # back-wall shelves: middle (seasonings, ingredients, bowls), top (backup stock, packaging)
    "shelf_d": (0.27, 0.30),
    "hood": (-1.05, 0.05),  # extraction hood over the noodle boiler and the stock pot (x range)
    "boiler": (-0.98, -0.42),  # noodle boiler (tebo wells), built into the back counter
    "burner": (-0.36, 0.02),  # stock-pot burner
    "coffee_x": 0.10,  # coffee from here to the right wall (front worktop and back counter)
}
# The order terminal at the counter's left end, where the reference has its angled payment unit
# (replaces the step-2 ticket machine, same footprint so the wall behind stays covered):
# a wall pedestal, a payment unit with a sloped keypad deck, and a hooded screen pod tilted back.
POS = {"x0": X0 + 0.077, "x1": X0 + 0.453, "z0": COUNTER["z"], "pedestal_d": 0.09, "deck": (0.27, 0.10, 0.17),
       "pod": (1.27, 1.61), "pod_d": (0.25, 0.15), "visor": 0.07}
# Storage under the customer counter (outside, mostly in the canopy's shadow): an under-counter fridge,
# drawers under the terminal end.
# Exterior pass (2026-10-09, prompt 8): the fridge (was a two-door unit at x -0.43..0.21, right behind the
# right stool, filling the sitter's knee space and covering the access panel) is now a narrower single-door
# unit between the right stool and the gusset at 0.53, hinged on its right so the door swings away from the
# stool; the noodle boxes and the spare stock pot that stood in front of the gas / water entry are gone
# (the cartons wait behind the back-left corner instead, EXTERIOR["cartons"]).
UNDER_COUNTER = {
    "fridge": (0.08, 0.50, 0.70),  # x0, x1, top z (base frame front + 1 cm .. counter underside)
    "fridge_hinge": "right",
    "drawers": (X0 + 0.11, X0 + 0.43, 0.61),  # under the left gusset (its strut starts at 0.62)
}

# ---- Exterior pass (2026-10-09, prompt 8): ground props round the footprint ------------------------
# Built on its own (kiosk/exterior.py, build_exterior.py -> Unreal/RawContent/kiosk_exterior.glb); Unreal
# trims the old step-3 ground props (crates, the green cabinet, the red crate, the bins, the utility cabinet,
# the lantern's box pedestal, the flattened cartons, the junction box's floor cable) out of a copy of
# SM_Kiosk_Props (kiosk_exterior.py), so the kiosk export and its weathering bake stay untouched.
# Working zones (kept clear on purpose): the staff door's apron and swing (left wall, y -0.30..0.80 out to
# ~0.9 m), the electrical cabinet and exhaust fan beside it (y 0.80..1.35), the door-wall access panel
# (y -0.70..-0.30), the gas / water entry under the counter, the stools' knee space, the fridge door, the
# utility cabinet's door, both drain splash zones, and every walking route off the platform.
# Positions: centres in the kiosk frame (m), sizes (x, y, z), yaw in degrees.
EXTERIOR = {
    # back-left, inside the railing: the lantern's pedestal rebuilt as a ballasted crate, a steel case and a
    # timber riser under the pole's flange (same top, PH + 0.90, so the pole and lantern stay put)
    "pedestal": {"x": LANTERN_L["x"], "y": LANTERN_L["y"], "tiers": (0.34, 0.30, 0.26)},
    # deliveries waiting against the railing: two stacking crates (long side along y), and on top the red crate of
    # empties going back with the driver (the scene's red accent, beside the lantern as in the reference)
    "crate_stack": {"x": X0 - 0.66, "y": Y1 + 0.25, "yaw": -90.0, "top_yaw": -4.0},  # label panels face the street (-X)
    # the dry-stock locker (was the green equipment cabinet, which overhung the platform edge and the railing
    # ran through it): back of the pen, its door facing the work space behind the kiosk's corner
    "locker": {"x": X0 - 0.595, "y": Y1 + 0.73, "size": (0.46, 0.38, 1.05)},
    # cardboard, kept dry: two cartons on timber bearers behind the back-left corner, under the canopy's back
    # overhang (seen past the corner from the orbit's door-side end)
    "cartons": {"x": X0 + 0.30, "y": Y1 + 0.27, "yaw": 2.0},
    # splash block under the old back-left downpipe's shoe (its water now lands on concrete, not on stock)
    "splash_left": {"x": X0 - 0.346, "y": Y1 + 0.267, "size": (0.22, 0.16, 0.04), "yaw": 146.5},
    # front-left corner, by the counter's end: the customer bin (near the old green bin, whose grime the
    # wall's weathering bake already shows) and a lidded tote of cup stock beside it
    "bin_burnable": {"x": X0 - 0.365, "y": Y0 + 0.26, "size": (0.40, 0.40, 0.62), "yaw": 3.0},  # lid top ~0.80 m, as the old barrel: the KAZE poster above stays readable
    "tote": {"x": X0 - 0.345, "y": Y0 + 0.765, "yaw": -93.0},  # its label side to the street
    # the junction box's floor cable, re-run down the wall to a floor gland clear of the bin
    "jb_cable": {"x": X0 - 0.115, "y": Y0 + 0.25},
    # front-right: the utility cabinet (on a stand, clear of the corner angle, the 24h pole clamped to its side;
    # door on the street side, hinged on the right), the gas cylinders' cage beside it (gate on the platform's
    # edge side, regulator on the back post, the pipe into the right wall's base hidden behind the corner),
    # and the cans bin moved in front of the bay's corner, clear of the vent grille and the drain
    "utility_cabinet": {"x": X1 + 0.22, "y": Y0 - 0.285, "size": (0.43, 0.37, 0.74), "stand": 0.10},
    "cylinder_cage": {"x": X1 + 0.725, "y": Y0 - 0.43, "size": (0.46, 0.60, 0.78)},
    "bin_cans": {"x": X1 - 0.48, "y": Y0 - 0.33, "radius": 0.19, "h": 0.48},
    # canopy footprint for the materials' rain exposure (Unreal: world-space wetness, kiosk_exterior.py)
    "canopy": (CANOPY_X0, CANOPY_X1, CANOPY_Y0, CANOPY_Y1, CANOPY_BOTTOM),
}

# ---- Rain contact pass (2026-10-09, prompt 9) -------------------------------------------------------
# Where rain reaches the platform, where runoff collects and drains, which canopy points drip, and where steam
# rises. build_rain_contact.py (Blender, on kiosk_exterior.blend) traces rain through the finished kiosk and its
# props, paints a top-down wet map of the platform (Unreal/RawContent/rain/T_RainContact.png) and resolves the
# exact sources / landing points below by ray casts (rain/rain_contact.json). Unreal: Scripts/wet_fx.py.
# Everything is in the kiosk frame (metres). Drip and steam timing lives in Unreal's scene_config.WET_FX.
RAIN_CONTACT = {
    "map_half_m": 4.096,  # the map covers +-4.096 m round the kiosk centre...
    "map_px": 2048,  # ...at 4 mm a texel
    "exposure_px": 512,  # rain exposure is traced at 16 mm (40 rays a texel), then filtered up
    "rays": 40,
    # rain direction: falling ~6 deg off vertical toward +X+Y (blown from the street on the camera side, so the
    # front and door-side edges catch wind-driven rain under the canopy), with gusts
    "wind": (0.07, 0.07), "gust": 0.20,
    # the wet/dry line: exposure through smoothstep(lo, hi), broken up by noise (no rectangle under the canopy edge)
    "wet_lo": 0.06, "wet_hi": 0.5, "edge_noise": 0.42,
    "splashback_m": 0.10,  # rain landing on the exposed band spatters this far into the sheltered concrete
    "edge_wick_m": (0.02, 0.06),  # street splash and wicking along the slab's outer edge (min, max width)
    "contact_halo_m": 0.025,  # darkening round anything standing on the slab (feet, bases, the walls)
    # shallow pools: a gentle height field; water stands only where rain or runoff feeds it, never in the
    # customer standing area in front of the counter
    "pool_level": 0.355, "pool_soft": 0.06,
    "lip_pool_m": 0.05,  # behind the steel edge angle (front and door side, 4 mm proud) water dams in a narrow line
    "no_pool": [((-2.20, -2.75), (0.45, -1.65))],  # the counter's standing area (x0, y0), (x1, y1)
    # canopy drips: a few chosen points (not an even row): name -> (x, y) under the fascia's drip edge or a post.
    # Exact source and landing heights come from ray casts. "trail" = a short wet trail from the landing spot.
    "drips": {
        "corner_fl": {"xy": (-3.525, -2.605), "trail": (-0.06, -0.08)},  # the near corner post (front-left), on the camera's side
        "front_joint": {"xy": (1.02, -2.585), "trail": (0.0, -0.10)},  # a fascia panel joint in front of the glazed window bay
        "edge_box": {"xy": (2.63, -2.585), "trail": (-0.04, -0.10)},  # beside the canopy's drain edge box: the slightly stronger one
        "left_joint": {"xy": (-3.505, 1.02), "trail": (-0.10, 0.0)},  # door side, past the door, before the lantern's pedestal
        "right_edge": {"xy": (3.16, -0.62), "trail": (0.30, 0.02)},  # the right fascia (seen from the orbit's service-side end)
    },
    "splash_r_m": 0.12,  # spatter round each drip's landing spot
    # downpipe outlets: water leaves the shoe, lands on its splash block and runs off as a narrow trail
    "outlets": {
        "pipe_fr": {"mouth": (2.46, -2.012, 0.190), "land": (2.455, -2.075), "trail": [(2.45, -2.15), (2.47, -2.32), (2.44, -2.50), (2.46, -2.69)]},
        "pipe_bl": {"mouth": (-2.862, 1.895, 0.155), "land": (-2.93, 1.94), "trail": [(-2.99, 2.02), (-2.93, 2.20), (-2.92, 2.42), (-2.90, 2.69)]},
    },
    "trail_w_m": (0.05, 0.10),
    "grate": {"xy": (-1.33, -2.04), "r_m": 0.10},  # the drain hose's floor grate under the counter (utilities.py: SERVICE_ENTRY)
    # steam: the stock pot's broth (inside, under the hood) and the kitchen's roof exhaust fan (mushroom fan,
    # back centre; the kitchen's duct runs up to it). Never near the gas cage or the electrical cabinet.
    "steam": {
        "pot": {"xy": (-0.17, -0.305), "z": 1.34, "rise_m": 0.34, "w_m": 0.30},
        "roof_fan": {"xy": (EXHAUST_FAN["cx"], EXHAUST_FAN["cy"]), "z": CANOPY_TOP + 0.30, "rise_m": 1.6, "w_m": 0.9},
        # the gas appliances' flue (back-left, rain cap at ~4.0 m): seen past the roof's silhouette from the floor camera
        "flue": {"xy": (EXHAUST_STACK["cx"], EXHAUST_STACK["cy"]), "z": CANOPY_TOP + EXHAUST_STACK["h"] + 0.12, "rise_m": 1.4, "w_m": 0.7},
    },
}
