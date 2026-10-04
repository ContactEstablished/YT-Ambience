"""City layout: every number the scripted city uses (build_city.py).

Kiosk frame, metres: kiosk at the origin, +X along its front face, +Y toward its back.
The video camera orbits on the -X/-Y side and looks toward +X/+Y, so the city fills the
sector between azimuth ~-60 deg and ~150 deg (azimuth = heading from +X toward +Y).

Towers stand on a ring around the plaza and turn to face the kiosk (their front face looks
back at it). Overlaps are resolved by pushing a tower outward along its azimuth.
"""

SEED = 2077

# Floor heights and window bays (shared with the Unreal window shader through material params)
FLOOR_H = {"glass": 3.6, "slab": 3.2, "terraced": 3.6}
PODIUM_H = 7.0  # shop floors at street level

# Hero towers: (name, azimuth_deg, distance_m, width_m (along the front), depth_m, height_m, style, screens)
# screens: (kind, offset along the front face from its centre, bottom z, width, height, colour)
#   kind "face" = big portrait ad, "neon" = vertical neon sign, "ad" = landscape ad
# Layout: near towers form the left and right canyon walls; the centre opens into a vista of
# receding towers toward the landmark (like the reference).
HERO_TOWERS = [
    ("LeftA", 112, 56, 36, 26, 190, "slab", [("face", 2.0, 22, 16, 30, (0.35, 0.70, 1.00))]),
    ("LeftB", 136, 48, 24, 22, 120, "glass", [("neon", -6.0, 12, 3, 16, (0.30, 1.00, 0.85))]),
    ("FarLeft", 152, 70, 30, 28, 160, "terraced", []),
    ("CenterLeft", 86, 100, 30, 28, 230, "terraced", [("face", 4.0, 34, 10, 20, (0.85, 0.92, 1.00))]),
    ("Center", 60, 150, 30, 30, 170, "glass", [("neon", -8.0, 20, 3, 22, (1.00, 0.30, 0.65)),
                                               ("neon", 8.0, 26, 3, 18, (0.30, 0.90, 1.00))]),
    ("CenterRight", 22, 125, 28, 30, 200, "slab", [("ad", 0.0, 18, 14, 8, (1.00, 0.60, 0.20))]),
    ("RightA", 2, 58, 32, 24, 210, "glass", [("face", 3.0, 20, 15, 28, (0.50, 0.75, 1.00))]),
    ("RightB", -24, 52, 24, 22, 150, "slab", [("neon", -4.0, 12, 5, 22, (1.00, 0.15, 0.10))]),
    ("RightC", -48, 58, 26, 24, 120, "terraced", [("ad", 0.0, 10, 10, 6, (1.00, 0.75, 0.30))]),
]

# The MIRAI landmark: a slender ringed tower far behind the kiosk
LANDMARK = {"azimuth": 40, "distance": 230, "radius": 16, "height": 320, "ring_every": 22, "spire": 45,
            "halo_z": 285, "halo_r": (19, 24), "halo_h": 3.5}

# Procedural fill: (count, min_dist, max_dist, min_h, max_h, min_size, max_size)
MID_FIELD = (18, 95, 170, 70, 200, 18, 34)
FAR_FIELD = (95, 170, 450, 50, 280, 18, 46)
FILL_AZIMUTH = (-75, 160)
STYLE_WEIGHTS = {"glass": 0.4, "slab": 0.4, "terraced": 0.2}
BEACON_CHANCE = 0.55  # red aircraft-warning beacon on top

# Keep-out zones: the plaza around the kiosk and the elevated railway corridor
PLAZA_RADIUS = 40.0
VIADUCT = {"x0": -80.0, "x1": 32.0, "y0": 11.5, "y1": 15.5, "deck_z": 14.0}  # train runs along +X into RightA; deck raised to 14 m (user, 10/3)
LANDMARK_SIGHTLINE_DEG = 7.0  # no fill towers within this azimuth of the landmark (closer than it)

# Commuter train (build_train.py): three cars, lead car at local x = 0 facing +X, rail top at z = 0
TRAIN = {
    "cars": 3, "car_len": 18.0, "gap": 0.8, "width": 2.9, "floor_z": 0.9, "roof_z": 4.0,
    "window_w": 1.3, "window_every": 1.75, "lit_fraction": 0.85, "silhouette_chance": 0.3, "seed": 11,
}
