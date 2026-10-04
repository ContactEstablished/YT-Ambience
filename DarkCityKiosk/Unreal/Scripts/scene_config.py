"""Every tunable for the Unreal scene: look, lights, rain, placeholder city, sweep.
Positions are in the Blender kiosk frame (metres; +X along the front face, +Y toward
the back), converted with dck.to_ue(). Kiosk dimensions live in kiosk_config.py.
"""

# ---- Exposure / post ----------------------------------------------------------
EXPOSURE_BIAS = -1.5  # manual exposure, EV; raise to brighten the whole frame
BLOOM = 0.7
VIGNETTE = 0.45

# ---- Fog (ExponentialHeightFog + volumetric fog) ------------------------------
FOG = {
    "density": 0.04,  # = the mist waves clear phase (LS_Sweep keys it; renders with --fog-clear see this)
    # 10/4 (user: the fog washed everything out; in the reference it stays near the ground and fills the
    # distance between towers): main layer halves every ~31 m of height (was 0.12, ~83 m)
    "height_falloff": 0.32,
    # Beyond the volumetric range (120 m) the plain height fog takes over; blue-gray there (the near
    # mist stays the luminous teal of the volumetric emissive), so the air cools with distance.
    "inscatter": (0.32, 0.42, 0.50),
    # Second, thin and nearly height-uniform layer: fades the far city bands at every height.
    # Not keyed by the mist waves (they key the main layer's density only).
    "second": {"density": 0.018, "height_falloff": 0.01, "height_offset": 0.0},
    # Glow of the air itself (volumetric fog emissive). This is what makes the haze luminous; the
    # inscatter colour above is ignored inside the volumetric range. Clear-phase value; waves key it.
    "volumetric_emissive": (0.03, 0.045, 0.05),  # was (0.08, 0.12, 0.13): this glow is uniform in the first 120 m and veiled everything
    "volumetric_distribution": 0.75,  # forward scattering: glows around lights
    "volumetric_albedo": (0.85, 0.9, 0.95),
    "volumetric_extinction": 1.0,
    "volumetric_view_distance_m": 120,
}
SKYLIGHT_INTENSITY = 1.0
# Sky light source: a small generated night-sky cubemap (atmosphere.py writes RawContent/sky/
# T_NightSky.hdr). Real-time capture had no sky to capture (no SkyAtmosphere, clouds or IsSky
# mesh), so it lit everything black and printed a warning. Colours are linear radiance.
SKY = {
    "hdr_size": (512, 256),  # lat-long
    "zenith": (0.010, 0.013, 0.022),
    "horizon": (0.10, 0.12, 0.15),  # city light pollution glow just above the horizon
    "glow_falloff_deg": 14.0,
}

# ---- Kiosk lights --------------------------------------------------------------
# 10/4 (user: the kiosk felt too bright): walls averaged 167 (8-bit) with a third clipped, against
# ~66 in the reference (58 with every kiosk light off: bounce from the glowing parts, the city and the
# haze), so every kiosk light and glow was turned down. kiosk_look.py re-applies these
# to the existing lights and materials without rebuilding the scene. (Was: soffit 45, spill 120,
# interior 45, lanterns 14, window lightbox 18, corner sign 10; volumetric scattering 1.0.)
LIGHT_SCALE = 1.0  # multiplies every kiosk light below
KIOSK_LIGHT_VOLUMETRIC = 0.55  # how much the kiosk lights glow in the fog (the halo round the kiosk)
SOFFIT = {"intensity_cd": 8, "temperature": 3100, "tilt_to_wall_deg": 35, "height_cm": 6}
CANOPY_SPILL = {"intensity_cd": 28, "color": (1.0, 0.62, 0.18), "down_deg": 25}
INTERIOR = {"pos": (-0.82, -1.00, 1.72), "intensity_cd": 20, "temperature": 2800, "radius_m": 4}
LANTERN_LIGHT = {"intensity_cd": 6, "temperature": 2300, "radius_m": 6}
WINDOW_LIGHTBOX_LIGHT = {"intensity_cd": 7, "temperature": 5200}
CORNER_SIGN_LIGHT = {"intensity_cd": 5, "color": (1.0, 0.8, 0.3), "radius_m": 4}

# Emissive strength for the kiosk's glowing parts (sign faces, tubes, lanterns, screens)
# (was: lightbox yellow 5, white 7, tubes 40, lantern paper 9, interior 20, lit glass 3, screen 6)
EMISSIVE = {
    "Lightbox_Yellow": 2.8,
    "Lightbox_White": 4.0,
    "Tube_WarmWhite": 14.0,
    "Lantern_Paper": 5.0,
    "Interior_Light": 10.0,
    "Interior_Warm": 1.5,
    "Glass_Lit": 1.8,
    "Screen_Multi": 4.5,
    "Button_Lit_Red": 5.0,
    "Button_Lit_Green": 5.0,
    "Button_Lit_Yellow": 5.0,
}

# Colour overrides (emissive + base colour) for glowing parts: saturated yellow-orange like the reference
EMISSIVE_COLOR = {
    "Lightbox_Yellow": (1.0, 0.60, 0.07),
}

# ---- Rain (BP_EasyRain) --------------------------------------------------------
# Fine, slow, snow-like mist drops (user's look: like the reference clip; mostly visible where lit).
RAIN = {
    "Camera-Centric": True,  # spawn around the camera so drops fill the foreground too
    "spawnRadius": 1600.0,  # cm; around the camera, reaching toward the kiosk
    "Primary Spawn Rate": 2500,
    "Rain Size": 1.2,  # default 2.5; 0.8 was invisible
    "rainfallSpeed": 0.4,  # slow, drifting
    "motionScaling": 0.25,  # shorter streaks
    "rainLifetime": 3.0,  # slow drops need longer to reach the ground
    "rainAmount": 100.0,
    "rainAlpha": 0.55,
    "rainBacklighting": 1.5,  # drops show where the sign and lamps light them
    "rainGlimmerIntensity": 1.0,
    "enableRainCurtains": True,
    "windStrength": 0.15,
    "gustAmount": 0.3,
    "splashAmount": 0.3,
    # (puddles are ground.py's own now; EasyRain's world puddle settings are unused)
    "rainRipplesAmount": 1.0,
    # patchy rain: a drifting 3D mask thins the rain in places, so it comes and goes in waves
    "volumetricMaskingAmount": 0.35,
    "VolumetricMaskTiling": 2500.0,
    "volumetricMaskSpeed": 0.3,
}

# Mist waves, keyed into LS_Sweep: the fog thickens and clears a whole number of times per loop
# (loop-safe). w(t) = (0.5 - 0.5 cos(2 pi cycles t / T)) ** power; 0 at the loop start.
MIST_WAVES = {
    "cycles": 2,
    "power": 1.5,  # >1 = longer clear spells, shorter thick peaks
    "fog_density": (0.04, 0.15),  # clear phase was 0.05: the mid-distance city stays darker (city background, 10/3)
    "volumetric_extinction": (1.0, 2.2),
    # clear phase = PrimaryReference (darker blue-teal), thick phase = the user's green-fog clip
    "volumetric_emissive": ((0.03, 0.045, 0.05), (0.10, 0.17, 0.14)),  # 10/4: about a third of ((0.08, 0.12, 0.13), (0.32, 0.55, 0.45))
}

# ---- Ground ------------------------------------------------------------------------
# Poured-concrete slabs (StarterContent textures, world-aligned) with our own puddles: ground.py.
GROUND = {
    "size_m": 240,
    "concrete_tile_cm": 260, "grime_tile_cm": 750, "macro_tile_cm": 4200, "noise_a_tile_cm": 1600, "noise_b_tile_cm": 350,
    "macro_mip": 6, "noise_a_mip": 5, "noise_b_mip": 3,  # blurred: smooth puddle shapes (2048 px textures)
    "detail_tile_cm": 12,  # fine grit; at 45 cm its bumps bent reflections into swells
    "tint": (0.26, 0.28, 0.33),  # times the light-grey concrete texture (it is warm; cool it)
    "grime": 0.5,
    "slab_cm": 300, "joint_cm": 1.2, "joint_dark": 0.45, "slab_variation": 0.12,
    "roughness": 0.72, "roughness_joint": 0.9,
    "normal_flatness": 1.0, "detail_flatness": 0.8,  # big concrete normal off: from 10 cm up it bent reflections into waves
    # puddle height mask: joints sit lower; a dip between the camera orbit and the kiosk keeps
    # its reflection in the foreground (the user's favourite part of the shot)
    "joint_dip": 0.08,
    # the kiosk is mirrored only in water within ~1.5 m of the lens (camera 10 cm up), so the dip
    # is a band in front of the lens along the orbit (radius 10.7 m): about half of it is puddle
    "foreground_dip": 0.075, "foreground_band_m": (8.4, 9.0, 10.8, 11.2),
    # height ~0.49 +- 0.07 with the blurred mips: coverage 0.42 -> ~14% puddles, ~50% in the band.
    # Few, large puddles: small ones squash into streaks from 10 cm up and read as chop.
    "puddle_coverage": 0.45, "puddle_edge": 0.015,  # 10/4: a little more water (was 0.42)
    "damp_band": 0.1, "wetness": 0.48,  # damp ring round each puddle; wet (not glossy) between them
    "wet_darkening": 0.4, "wet_roughness": 0.24,  # 10/4: shinier (was wetness 0.4, roughness 0.3)  # ~0.3 stretches lights into vertical streaks, like the reference
    "puddle_darkening": 0.35, "puddle_roughness": 0.03,
    # EasyRain ripple functions (raindrop rings in the puddles, a little wind)
    "ripples": {"speed": 1.0, "normal": 0.15, "tiling": 0.5, "amount": 1.0, "wind_speed": 0.3, "wind_normal": 0.0, "wind_tiling": 1.0},  # from 10 cm up any more reads as chop
}

# ---- Placeholder city (blockout only; replaced by the real city later) -----------
# Towers on a ring around the kiosk: (heading_deg from +X toward +Y, distance_m, width_m, depth_m, height_m)
TOWERS = [
    (-55, 42, 16, 16, 90), (-30, 38, 14, 14, 70), (-8, 46, 18, 16, 115), (12, 33, 12, 12, 55),
    (30, 56, 20, 20, 145), (48, 41, 14, 18, 85), (66, 60, 22, 18, 165), (84, 37, 12, 14, 62),
    (102, 49, 16, 16, 125), (122, 41, 14, 14, 78), (142, 52, 18, 18, 105), (162, 44, 16, 16, 88),
]
# Billboards on the tower faces that look at the kiosk: (tower index, width_m, height_m, base_z_m, colour, nits)
BILLBOARDS = [
    (1, 9, 16, 14, (0.25, 0.75, 1.0), 25), (2, 11, 20, 22, (0.9, 0.25, 0.65), 20),
    (4, 12, 22, 30, (0.35, 0.55, 1.0), 22), (5, 8, 18, 12, (1.0, 0.12, 0.08), 30),
    (6, 13, 26, 38, (0.3, 0.9, 0.85), 18), (8, 9, 18, 20, (1.0, 0.55, 0.2), 22),
    (9, 8, 15, 10, (0.6, 0.35, 1.0), 25), (10, 10, 20, 26, (0.25, 0.75, 1.0), 20),
]
BILLBOARD_SCALE = 0.12  # multiplies every billboard's nits
# Each billboard also gets a matching rect light (intensity = nits x area, physically consistent) so the
# fog and wet ground pick up its colour; emissive surfaces alone don't light volumetric fog.
BILLBOARD_LIGHT = {"enabled": True, "radius_m": 70, "volumetric_scattering": 4.0}
BUILDING_COLOR = (0.024, 0.027, 0.032)
# Elevated railway behind the kiosk, parallel to the front face (the train runs here later)
VIADUCT = {"x0": -80, "x1": 45.56, "y0": 11.5, "y1": 15.5, "deck_z": 14.0, "deck_h": 1.1, "pillar_every_m": 16, "pillar_w": 1.3}  # ends inside tower RightA (city_manifest.json)

# ---- Camera sweep (preview) -----------------------------------------------------
# Timing only; the camera itself (lens, distance, height, tilt, arc) is kiosk_config.VIDEO_CAM.
SWEEP = {
    "seconds": 30,
    "key_every_s": 0.5,
}

# ---- City (scripted, from Blender build_city.py -> RawContent/city.glb + city_manifest.json) ----
PLACEHOLDER_CITY = False  # the old slab towers/billboards; setup_scene removes them when False
CITY = {
    # procedural windows (M_Windows): metres; lit = fraction of rooms lit
    "glass": {"FloorH": 3.6, "BayW": 1.3, "WinW": 0.85, "WinH": 0.7, "LitFraction": 0.14, "WarmFraction": 0.55,
              "Intensity": 1.6, "GlassRough": 0.08, "WallRough": 0.5},
    "slab": {"FloorH": 3.2, "BayW": 1.8, "WinW": 0.45, "WinH": 0.5, "LitFraction": 0.2, "WarmFraction": 0.7,
             "Intensity": 1.5, "GlassRough": 0.12, "WallRough": 0.75},
    "shop": {"FloorH": 3.5, "BayW": 4.5, "WinW": 0.88, "WinH": 0.8, "LitFraction": 0.7, "WarmFraction": 0.75,
             "Intensity": 3.0, "GlassRough": 0.1, "WallRough": 0.6},
    # emissive strength of the glTF materials by name prefix
    "emissive": {"City_Screen_": 3.5, "City_Sign_": 5.0, "Landmark_Ring": 12.0, "Beacon_Red": 20.0, "Viaduct_Strip": 6.0, "Viaduct_Lamp": 10.0},
    "screen_light": {"nits_scale": 0.5, "radius_m": 110, "volumetric_scattering": 3.0,
                     "volumetric_per_screen": {"RightA_0": 0.8}},  # NEXUS: less glow in the fog round it (user, 10/4)
    "shop_light": {"intensity_cd": 600, "radius_m": 28, "volumetric_scattering": 1.5, "max_distance_m": 200},
}

# ---- City background (setup_city_bg.py): instanced towers in depth bands --------------------
# Replaces the Blender fill towers (City_Mid*, City_Far_*), the old landmark, and the three ad
# towers in the vista (rebuilt in place; their screens stay exactly where they were). The old
# actors are hidden, not deleted: `setup_city_bg.py --show old` flips back for comparison.
# Distances are from the kiosk (the orbit centre; the camera is within 11 m of it). Elevations are
# degrees up from the Mid-pose camera. From the 10 cm lens the frame top is ~42.6 deg up and the
# viaduct top 16-23 deg up: a tower D m away clears the rail only if taller than ~0.42 D, and its
# top stays in frame only if it is shorter than ~0.92 D.
CITY_BG = {
    "seed": 2077,
    "folder": "City_Background",
    "azimuth_deg": (-70, 148),  # from the kiosk; the sweep sees about -51..123 deg
    "grid_share": 0.7,  # towers on the street grid; the rest turn to face the kiosk
    "yaw_jitter_deg": 5.0,
    "floor_h_m": (3.4, 4.2),  # per tower (window rows)
    "bay_w_m": (1.4, 2.4),  # per tower (window columns)
    "brightness": (0.7, 1.3),  # per tower window brightness
    "podium_h_m": 7.0,
    "archetypes": {"stepped": 0.42, "crown": 0.24, "twin": 0.12, "round": 0.07, "slab": 0.15},
    # The hero view (Mid pose): inside the vista the skyline drops into a V, so crowns, masts and a
    # strip of sky show between the flanks; azimuth seen from the Mid camera.
    "vista": {"axis_deg": 34.0, "halfwidth_deg": 34.0, "core_deg": 14.0},
    # Bands, near to far. height_m: towers that run off the top. A share of towers outside the
    # vista get a visible top instead (top_elev_deg); inside the vista every top lands in
    # vista_elev_deg, rising with depth so each band shows above the one in front of it. vista_extra:
    # more towers placed inside the vista only (it shows the most sky). bay_w_m / floor_h_m override
    # the window sizes below for a band.
    # min_top_elev_deg keeps far towers tall enough to clear the viaduct. lit = lit-window share.
    "bands": {
        "Band1": {"count": 14, "dist_m": (100, 185), "height_m": (150, 320), "width_m": (16, 30), "tiers": (2, 4),
                  "vista_elev_deg": (21, 30), "top_elev_deg": (26, 38), "visible_top_share": 0.35, "min_top_elev_deg": 0,
                  "setback_chance": 0.75, "antenna_chance": 0.6, "beacon_chance": 0.8, "neon_chance": 0.6,
                  "lit": 0.20, "lit_spread": 0.07, "warm_share": 0.80, "podium": True, "shadows": True, "pad_m": 3.0,
                  "shop_lights": True, "bay_w_m": (1.2, 2.0), "floor_h_m": (3.3, 3.9)},
        "Band2": {"count": 40, "dist_m": (190, 380), "height_m": (200, 450), "width_m": (18, 40), "tiers": (3, 5),
                  "vista_elev_deg": (25, 36), "top_elev_deg": (26, 39), "visible_top_share": 0.35, "min_top_elev_deg": 18,
                  "setback_chance": 0.7, "antenna_chance": 0.55, "beacon_chance": 0.7, "neon_chance": 0.5,
                  "lit": 0.28, "lit_spread": 0.08, "warm_share": 0.80, "podium": True, "shadows": True, "pad_m": 3.0,
                  "bay_w_m": (1.2, 2.0), "floor_h_m": (3.3, 3.9), "vista_extra": 8},
        "Band3": {"count": 90, "dist_m": (390, 850), "height_m": (300, 700), "width_m": (25, 60), "tiers": (2, 4),
                  "vista_elev_deg": (28, 41), "top_elev_deg": (26, 40), "visible_top_share": 0.4, "min_top_elev_deg": 20,
                  "setback_chance": 0.65, "antenna_chance": 0.5, "beacon_chance": 0.55, "neon_chance": 0.2,
                  "lit": 0.36, "lit_spread": 0.10, "warm_share": 0.80, "podium": False, "shadows": False, "pad_m": 2.0,
                  "vista_extra": 30},
        "Band4": {"count": 200, "dist_m": (900, 2000), "height_m": (450, 1100), "width_m": (40, 120), "tiers": (1, 3),
                  "vista_elev_deg": (24, 38), "top_elev_deg": (22, 36), "visible_top_share": 0.5, "min_top_elev_deg": 20,
                  "setback_chance": 0.5, "antenna_chance": 0.35, "beacon_chance": 0.4, "neon_chance": 0.0,
                  "lit": 0.44, "lit_spread": 0.10, "warm_share": 0.80, "podium": False, "shadows": False, "pad_m": 1.0,
                  "vista_extra": 40},
    },
    # Window shader (M_CityBG_Facade) per band: metres; Lod* = window cells per pixel where the grid
    # starts / finishes blending into its average glow (no shimmer when windows get sub-pixel).
    "windows": {
        "common": {"PaneW": 0.6, "PaneH": 0.62, "ClusterX": 4, "ClusterY": 3, "UnlitGlow": 0.008, "LodStart": 0.3,
                   "LodEnd": 0.6, "TealShare": 0.05, "WallRough": 0.55, "GlassRough": 0.12},
        "Band1": {"Intensity": 2.2, "PaneW": 0.52}, "Band2": {"Intensity": 2.4, "PaneW": 0.52}, "Band3": {"Intensity": 2.8}, "Band4": {"Intensity": 3.0},
        "Shop": {"FloorH": 3.5, "BayW": 4.5, "PaneW": 0.88, "PaneH": 0.78, "ClusterX": 2, "ClusterY": 1, "Intensity": 2.6,
                 "UnlitGlow": 0.05},
        "Plain": {"Windows": 0.0},
    },
    "colors": {"warm": (1.0, 0.58, 0.28), "cool": (0.72, 0.84, 1.0), "teal": (0.35, 1.0, 0.85),
               "wall": (0.035, 0.04, 0.05), "glass": (0.015, 0.02, 0.028)},
    "shop_lit": 0.65,
    # Lights (M_CityBG_Light, emissive): beacons blink every 1.5 s, neon pulses every 7.5 s (both
    # divide the 30 s and 300 s loops). Beacon cubes grow with distance so far ones stay a few pixels.
    "beacon": {"color": (1.0, 0.06, 0.03), "intensity": 40.0, "size_per_m": 1 / 350, "min_size_m": 0.9, "blink_share": 0.75},
    "neon": {"colors": [(0.3, 0.95, 1.0), (1.0, 0.25, 0.65), (1.0, 0.6, 0.2), (1.0, 0.15, 0.1), (0.4, 1.0, 0.75), (0.65, 0.45, 1.0)],
             "intensity": 8.0, "width_m": (1.6, 3.5), "height_m": (10, 30), "pulse": (0.0, 0.3), "band_sign_intensity": 5.0,
             "min_elev_deg": 17.0},  # mounted high enough to show above the viaduct from the Mid pose
    "mast_width_per_m": 1 / 700,
    "skybridges": {"count": 7, "pair_dist_m": (14, 80), "min_elev_deg": 12.0, "frame_deg": 50.0, "width_m": 5.0, "height_m": 4.0, "glaze_color": (1.0, 0.72, 0.45),
                   "glaze_intensity": 2.5, "strip_color": (0.3, 0.9, 1.0), "strip_intensity": 6.0},
    "shop_light": {"intensity_cd": 500, "radius_m": 26, "volumetric_scattering": 1.5, "max_distance_m": 200},
    # The MIRAI landmark, deeper and slimmer than the Blender one: at the Mid pose it stands just
    # right of the kiosk's centre with its crown under the frame top.
    "landmark": {"azimuth_deg": 33.5, "distance_m": 470, "radius_m": 14.0, "height_m": 345, "spire_m": 45, "ring_every_m": 22,
                 "ring_color": (1.0, 0.68, 0.32), "ring_intensity": 7.0, "ring_out_m": 1.2,  # warm amber, not blown to white
                 # floating halos: (height fraction, radius x shaft radius)
                 "halos": [(0.86, 1.9), (0.93, 1.5), (0.5, 1.45)], "halo_segments": 32,
                 "strip_color": (1.0, 0.8, 0.5), "strip_intensity": 8.0,
                 # the MIRAI / 未来 sign (make_landmark_sign.ps1): centre height (fraction), width (x local shaft radius);
                 # at 0.74 h it sits between the top halo and the viaduct in the Mid frame
                 "sign": {"name": "MIRAI", "texture": "T_Sign_MIRAI", "z": 0.74, "width_r": 2.0, "aspect": 0.75, "intensity": 10.0},
                 "lit": 0.35},
    # Ad towers in the vista: rebuilt on their old footprints; their screens are re-hosted unchanged
    "anchors": ["CenterLeft", "Center", "CenterRight"],
    "anchor_clearance_m": 18,  # tower rises at least this far above its highest screen
    # Hero towers kept from the Blender city (keep-outs for the layout)
    "heroes": ["LeftA", "LeftB", "FarLeft", "RightA", "RightB", "RightC"],
    # avoid_traffic: every tower and skybridge keeps clear of the flying-traffic air corridors
    # (traffic_routes.json). The corridors are planned ignoring bands 1-2 and the bridges
    # (TRAFFIC["plan_ignore_groups"]), so the near city is laid out round them; after a re-plan, rebuild
    # this layout (it also refreshes the corridors' visibility).
    "keepout": {"hero_pad_m": 6.0, "viaduct_pad_m": 4.0, "car_clear_m": 8.0, "avoid_traffic": True,
                "sightline_margin_deg": 1.0, "sightline_max_elev_deg": 21.0,  # towers in front of the landmark stay low
                "behind_max_elev_deg": 24.0, "behind_width": 1.4},  # and those right behind it too, so it reads against the sky
}

# ---- Railway + train --------------------------------------------------------------
PLACEHOLDER_VIADUCT = False  # the old box viaduct; the scripted one comes with the city (City_Viaduct)
VIADUCT_LAMP = {"every": 2, "intensity_cd": 900, "radius_m": 22, "cone_deg": 55, "volumetric_scattering": 2.5}
# The train runs along +X (Blender frame) into tower RightA once per loop. (time_s, x_m) keys,
# linear in between: in from off-screen left at ~15 m/s, slowing to ~9 m/s into the portal.
# x is the nose position; the portal is at city_manifest railway.portal_x (~45.6 m).
TRAIN = {
    "keys": [(0.0, -110.0), (8.0, -110.0), (14.0, -20.0), (18.0, 28.0), (24.5, 85.0), (30.0, 85.0)],
    "head_cd": 4000, "head_radius_m": 70,  # no interior lights: unshadowed, they lit the deck's underside
}

# ---- Loop variants ------------------------------------------------------------------
# The final render splices several loops that are identical except for the flying traffic and
# whether the train runs. No traffic run crosses the loop seam, so every variant starts and ends
# with the same (empty) sky and any variant can follow any other.
VARIANT = {
    "name": "v1",
    "traffic_seed": 101,  # a different seed = a different schedule on the same corridors
    "train": True,
    "hero": True,  # the hero vehicle's one pass this loop
    "density": 1.0,  # scales every layer's traffic rate
}

# ---- Flying traffic ---------------------------------------------------------------
# traffic_plan.py: corridors in three altitude layers (auto-planned, cached in
# RawContent/traffic_routes.json; --replan searches again) and, per VARIANT, a schedule of runs
# with their motion baked (RawContent/traffic.json). setup_traffic.py spawns the vehicles,
# make_sweep.py keys them. Vehicles appear and disappear only where the camera cannot see them
# (behind towers, off frame, in the haze), fading in scale and light over fade_s.
TRAFFIC = {
    # traffic_lanes.py route search (shared settings; each layer below overrides some)
    "routes": {
        "seed": 404,
        "tries": 20000,
        "routes": 8,
        "turns_deg": (0, -20, 20, -40, 40, -60, 60, -80, 80, -100, 100),
        "turn_radius_m": 45,
        "pass_distance_m": (25, 300),
        "pass_azimuth_deg": (-55, 125),
        "pass_elevation_deg": (6, 44),  # angle up from the floor camera (frame top is ~42 deg)
        "min_altitude_m": 16,  # the railway solid keeps them clear of the viaduct and catenary
        "max_climb_deg": 4,
        "collision_pad_m": 8,  # route centrelines; the per-vehicle offsets below stay inside it
        "car_clearance_m": 3,  # a vehicle's own (offset) path
        "camera_samples_deg": (-45, -22.5, 0, 22.5, 45),
        "frame_margin": 0.02,
        "fog_hide_m": 280,  # this far from the camera a vehicle counts as lost in the haze
        "full_weight_within_m": 90,
        "hide_margin_m": 20,
        "max_reach_m": 600,
        "min_visible_m": 40,
        "route_separation_m": 12,
    },
    # Corridor layers: low = couriers (+ the odd pod), mid = taxis and pods, high = transit and cargo
    "layers": {
        "low": {"seed": 411, "routes": 4, "tries": 7000, "pass_distance_m": (25, 140), "pass_elevation_deg": (8, 26),
                "min_altitude_m": 18, "fog_hide_m": 220, "max_reach_m": 420},
        "mid": {"seed": 412, "routes": 5, "tries": 7000, "pass_distance_m": (60, 230), "pass_elevation_deg": (14, 34),
                "min_altitude_m": 35, "fog_hide_m": 300, "max_reach_m": 650},
        "high": {"seed": 413, "routes": 3, "tries": 5000, "pass_distance_m": (140, 380), "pass_elevation_deg": (20, 38),
                 "min_altitude_m": 90, "fog_hide_m": 560, "max_reach_m": 950, "hide_margin_m": 30, "min_visible_m": 60},
    },
    # Vehicle types (docs/FlyingVehicles). layers: share of that layer's runs. speed m/s; accel m/s^2;
    # bank: (max degrees, lag s); hover: ((amplitude m), (period s)); yaw_drift: degrees.
    # stop: chance per run, hold seconds, overshoot (m) before settling back; station = stop beside a
    # building; wait_yaw = slow turn while waiting. light: under-glow point light (+ headlight).
    "types": {
        "Courier": {"mesh": "SM_Veh_Courier", "scale": 1.6, "layers": {"low": 1.0, "mid": 0.12}, "speed": (16, 22), "accel": 6.0,
                    "bank": (22, 0.35), "hover": ((0.04, 0.08), (3, 6)), "yaw_drift": 1.5, "pitch_per_accel": 1.0,
                    "stop": {"chance": 0.3, "hold_s": (1.5, 4.0), "overshoot_m": (0.4, 0.8)}, "min_gap_m": 10, "light": None},
        "Taxi": {"mesh": "SM_Veh_Taxi", "scale": 1.4, "layers": {"mid": 1.0, "low": 0.08}, "speed": (13, 17), "accel": 2.4,
                 "bank": (12, 1.0), "hover": ((0.03, 0.05), (4, 7)), "yaw_drift": 0.3, "pitch_per_accel": 0.8,
                 "stop": {"chance": 0.12, "hold_s": (2.0, 5.0), "overshoot_m": (0.9, 1.5)}, "min_gap_m": 22,
                 "light": {"color": (0.45, 0.85, 1.0), "cd": 500, "radius_m": 30, "head_cd": 1200}},
        "Pod": {"mesh": "SM_Veh_Pod", "scale": 1.4, "layers": {"mid": 0.45, "low": 0.2}, "speed": (11, 15), "accel": 3.0,
                "bank": (18, 0.7), "hover": ((0.05, 0.1), (3, 5)), "yaw_drift": 0.6, "pitch_per_accel": 1.2,
                "stop": {"chance": 0.5, "hold_s": (5.0, 20.0), "overshoot_m": (0.5, 1.0), "station": True, "wait_yaw_deg": 7},
                "min_gap_m": 15, "light": {"color": (0.45, 0.9, 1.0), "cd": 350, "radius_m": 24}},
        "Transit": {"mesh": "SM_Veh_Transit", "scale": 1.25, "layers": {"high": 1.0}, "speed": (9, 12), "accel": 0.8,
                    "bank": (3, 2.5), "hover": ((0.02, 0.03), (6, 9)), "yaw_drift": 0.0, "pitch_per_accel": 0.3,
                    "stop": None, "min_gap_m": 60, "light": {"color": (0.45, 0.85, 1.0), "cd": 1200, "radius_m": 50, "head_cd": 1500}},
        "Cargo": {"mesh": "SM_Veh_Cargo", "scale": 1.25, "layers": {"high": 0.8}, "speed": (5.5, 7.5), "accel": 0.5,
                  "bank": (4, 3.0), "hover": ((0.04, 0.06), (5, 8)), "yaw_drift": 0.0, "pitch_per_accel": 0.4,
                  "stop": None, "min_gap_m": 60, "cable_m": 6.3, "sway_damping": 0.25, "compensate": 0.15,
                  "light": {"color": (0.6, 0.85, 1.0), "cd": 1000, "radius_m": 50}},
    },
    # runs per minute per lane direction; quiet spells; spacing
    "schedule": {"rate_per_min": {"low": 3.0, "mid": 3.0, "high": 1.8}, "lull_chance": 0.25, "lull_s": (5, 18),
                 "min_headway_s": 1.5, "loop_margin_s": 0.5, "pass_clearance_m": 6.0, "key_dt_s": 1 / 12,
                 "offset_jitter_m": (0.8, 1.5)},  # random extra (sideways, up) on top of the slot
    # The hero: one slow pass a loop (VARIANT["hero"]), emerging from the haze, crossing a shaft of
    # light inside the volumetric-fog range, passing behind the viaduct and fading away again
    "hero": {"mesh": "SM_Veh_Hero", "scale": 1.5, "speed": 7.5, "slow_at_shaft": 0.3, "bank": (8, 2.0), "hover": ((0.08, 0.08), (5, 5)),
             "pitch_per_accel": 0.5, "min_visible_s": 6, "max_visible_s": 15,
             "plan_loop_s": 300,  # the route and its shaft of light are chosen for the final 5-min loop (slow pan)
             "train_clearance_m": 12.0,  # from the hero's centre to the train's body: it never passes over the train
             "lift_mist": 0.25, "light_volumetric": 1.2,  # a softer glow under the hero than the other craft
             "search": {"seed": 421, "routes": 10, "tries": 12000, "pass_distance_m": (45, 110), "pass_elevation_deg": (8, 30),
                        "min_altitude_m": 20, "fog_hide_m": 320, "max_reach_m": 600, "hide_margin_m": 25,
                        "turns_deg": (0, -20, 20, -40, 40)},
             "light": {"color": (0.6, 0.9, 1.0), "cd": 250, "radius_m": 40},
             "shaft": {"cd": 1500, "cone_deg": 9, "height_m": 70, "volumetric_scattering": 2.2, "color": (0.85, 0.92, 1.0)}},
    "fade_s": 1.5,  # scale and lights ramp at both ends of a run
    "plan_ignore_groups": ["Band1", "Band2", "Details"],  # corridors are planned through these; the layout then avoids them
    # (side, up) offsets from the corridor centreline, metres; side < 0 = right of travel, so the two
    # directions keep apart
    "slots": ((-4.0, 0.0), (-4.0, 4.0), (-8.0, 2.0), (-4.0, -3.0), (-8.0, -2.0)),
    "scale": 1.0,
    # emissive strengths for the vehicle materials (glTF names) in Unreal
    "emissive": {"Veh_Lift_Cyan": 35.0, "Veh_Lift_Hero": 8.0, "Veh_Nav_White": 40.0, "Veh_Accent_Cyan": 12.0,
                 "Veh_Window_Warm": 4.0, "Veh_Window_Dim": 1.5, "Veh_Glass_Lit": 1.2, "Veh_Marking_Amber": 3.0},
    "nav_blink": {"color": (1.0, 0.05, 0.03), "intensity": 60.0, "period_s": 1.5, "duty": 0.3},  # divides 30 s and 300 s
    "lift_mist": {"color": (0.45, 0.85, 1.0), "intensity": 1.2},  # the faint glow card under each lift ring
}

# ---- Umbrella crowd -------------------------------------------------------------------
# crowd_paths.py (offline, numpy) plans the walks; setup_crowd.py spawns the people;
# make_sweep.py keys them. Every walker appears/disappears where the camera can't see them at
# that moment (dark figures stay visible against the glowing mist, so the haze can't hide them).
CROWD = {
    "seed": 77,
    "walkers": 16,
    "tries": 700,
    "pass_distance_m": (5, 50),
    "pass_azimuth_deg": (-70, 140),
    "turns_deg": (0, 0, -35, 35, -70, 70, -90, 90),
    "leg_max_m": 35, "max_radius_m": 70, "corner_radius_m": 2.5,
    "tower_pad_m": 1.0, "pier_pad_m": 0.5,
    "kiosk_zone": (-3.6, 3.4, -3.4, 2.9),  # kiosk, platform, stools, props
    "camera_keepout_m": 3.5,  # nobody walks into the lens
    "heights_m": (0.3, 1.0, 1.75, 2.15),  # feet, body, head, umbrella top: hidden = all hidden
    "frame_margin": 0.04,
    "weight_band_m": (6, 30),  # on-screen time counts fully between these distances
    "walk_speed": 1.328,  # m/s at play rate 1 (AS_Quinn_NPC_32_Walking_Umbrella root motion)
    "rate_range": (0.92, 1.08),
    "min_visible_s": 4, "max_run_s": 29,
    "min_gap_m": 1.0,
    # people standing all loop (umbrella idle): Blender (x, y), facing heading in degrees
    "standing": [
        # (a figure front-right of the kiosk at (3.0, -5.8) was removed 10/3: the user found it distracting)
        {"pos": (11.5, 10.6), "facing_deg": 245},  # waiting by a viaduct pier, behind the kiosk
    ],
}

# Who the crowd are (setup_crowd.py): bodies, clips, coats, umbrellas.
CROWD_LOOK = {
    "seed": 2049,
    "walk_anim": "/Game/FemaleNPCpack_2/UE5_Animation/Animations/AS_Quinn_NPC_32_Walking_Umbrella",  # clean 13.6 s loop
    "stand_anim": "/Game/FemaleNPCpack_2/UE5_Animation/Animations/AS_Quinn_NPC_28_Standing_Umbrella",  # 18.8 s
    "walk_no_umbrella_anim": "/Game/FemaleNPCpack_2/UE5_Animation/Animations/AS_Quinn_NPC_32_Walking_Crossed_arms",  # same 13.6 s, 1.328 m/s
    "bodies": {"Quinn": "/Game/FemaleNPCpack_2/DEMO/Characters/Mannequins/Meshes/SKM_Quinn",
               "Manny": "/Game/NPC_Animation_Pack/Characters/Mannequins/Meshes/SKM_Manny"},
    "quinn_skeleton": "/Game/FemaleNPCpack_2/DEMO/Characters/Mannequins/Meshes/SK_Quinn",
    "manny_skeleton": "/Game/NPC_Animation_Pack/Characters/Mannequins/Meshes/SK_Mannequin",
    "manny_share": 0.5,
    "scale_range": (0.95, 1.07),
    # measured from the clips: in hand_r space the fist closes ~7 cm along the fingers (-X), 2.5 cm
    # toward the palm (+Y), and world-up is (-0.40, -0.10, 0.91) all through the walk and the idle
    "grip": {"socket": "hand_r", "offset_cm": (-7.0, 2.5, 0.0), "shaft_dir": (-0.40, -0.10, 0.91)},
    "coats": [  # (base colour, roughness): near-black and fairly matte, so people read as silhouettes like
        # the reference (glossier coats caught the kiosk light as a plastic sheen on the mannequins)
        ((0.010, 0.010, 0.012), 0.7), ((0.014, 0.012, 0.010), 0.72), ((0.009, 0.011, 0.017), 0.7),
        ((0.015, 0.015, 0.016), 0.75), ((0.018, 0.015, 0.012), 0.72), ((0.011, 0.013, 0.010), 0.7),
    ],
    # the user (10/3): not everyone needs an umbrella, about 20% without (coat and a hat or a hood)
    "no_umbrella_share": 0.2,
    "hood_share_with_umbrella": 0.3,
    "headwear_without_umbrella": {"Hat_Fedora": 3, "Hat_Cap": 2, "Hat_Beanie": 2, "Hood": 2},
    "trousers": ((0.008, 0.008, 0.009), 0.75),
    "belt": ((0.006, 0.006, 0.007), 0.4),
    "umbrella_weights": {"SM_Umbrella_Black": 8, "SM_Umbrella_Navy": 2, "SM_Umbrella_Red": 1, "SM_Umbrella_Clear": 2.5, "SM_Umbrella_LED": 1.5},
    # outfits (setup_outfits.py): garments from Blender build_outfits.py merged onto each body
    "outfits": {"Coat": ["Coat"], "CoatHood": ["Coat", "Hood"]},
    "skirt_weights": {"thigh_at_hem": 0.85, "curve": 1.2, "side_blend_cm": 9.0},
    "led_emissive": 12.0, "led_light_cd": 40, "led_light_radius_m": 4,
}
