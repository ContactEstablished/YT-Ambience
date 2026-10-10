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
# Kitchen pass (10/9): L_Interior is now the kitchen's dim rear fill, at the fluorescent batten on the
# rear ceiling (kiosk/kitchen.py room()); the bright work light at the opening is L_Kitchen_Prep
# (KITCHEN_LIGHTS). Was: in the old recess at (-1.075, -1.15, 1.67), 20 cd, 2800 K, 4 m.
INTERIOR = {"pos": (-1.05, -0.905, 2.03),
            "intensity_cd": 15, "temperature": 3200, "radius_m": 2.8, "volumetric": 0.2}
LANTERN_LIGHT = {"intensity_cd": 6, "temperature": 2300, "radius_m": 6}
WINDOW_LIGHTBOX_LIGHT = {"intensity_cd": 7, "temperature": 5200}
CORNER_SIGN_LIGHT = {"intensity_cd": 5, "color": (1.0, 0.8, 0.3), "radius_m": 4}

# Emissive strength for the kiosk's glowing parts (sign faces, tubes, lanterns, screens)
# (was: lightbox yellow 5, white 7, tubes 40, lantern paper 9, interior 20, lit glass 3, screen 6)
EMISSIVE = {
    "Lightbox_Yellow": 2.8,
    "Lightbox_White": 4.0,
    "Tube_WarmWhite": 14.0,
    "Lantern_Paper": 2.3,  # signage pass (10/5): warm paper, a bright secondary sign under the fascia (was 5.0, read white; 3.2 still near white)
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
    "Lantern_Paper": (1.0, 0.50, 0.11),  # signage pass (10/5): warm paper like the reference lantern (was the glTF's pale cream)
}
# Wet paint and steel read glossier (RoughnessFactor on the kiosk's glTF material instances)
KIOSK_ROUGHNESS = {"Kiosk_YellowPaint": 0.32, "Kiosk_YellowPaint_Dark": 0.35, "Steel_Dark": 0.3, "Steel_Grey": 0.35,
                   "Steel_Galvanised": 0.3, "Platform_Concrete": 0.45, "Glass_Dirty": 0.1,
                   # construction pass (2026-10-04): duller layers that separate from the main paint
                   "Kiosk_YellowPaint_Faded": 0.45, "Steel_Charcoal": 0.45, "Steel_Galv_Dull": 0.5,
                   # utility pass (2026-10-04): conduit, cable, hose, copper, lagging, cast drain pipe
                   "Conduit_Painted": 0.42, "Cable_Black": 0.5, "Hose_Grey": 0.7, "Copper_Aged": 0.42,
                   "Insulation_Black": 0.85, "Pipe_Cast": 0.55,
                   # roof pass (2026-10-04): the oldest roof pieces (warm aged metal) and the HVAC housing
                   "Steel_Aged_Warm": 0.5, "Paint_Grey_Faded": 0.55}

# ---- Kiosk weathering (surfacing pass, 2026-10-04) ----------------------------------------------
# kiosk_weather.py builds M_KioskWeathered and one MI_KW_<material> per weathered glTF material, and
# sets them on the kiosk actors' slots. The baked masks (Blender kiosk/weather.py) say WHERE wear,
# rust, grime, streaks, soot, grease, splash and polish physically go; these numbers say HOW MUCH
# each material shows, so every material (and so every roof unit) has its own history.
# A material = a category preset + overrides. PaintColor defaults to the glTF instance's colour;
# the amber / faded / newer-repaint generations are derived from it unless given. Colours linear.
WEATHER_COMMON = {
    "PrimerColor": (0.11, 0.065, 0.04), "RustDark": (0.065, 0.028, 0.012), "RustOrange": (0.22, 0.08, 0.022),
    "RustBlack": (0.02, 0.013, 0.009), "GrimeColor": (0.042, 0.034, 0.024), "MudColor": (0.10, 0.088, 0.07),
    "StreakColor": (0.045, 0.036, 0.025), "GreaseColor": (0.085, 0.048, 0.016), "SootColor": (0.014, 0.013, 0.012),
    "EdgeWear": 0.0, "RustAmount": 0.0, "GrimeAmount": 0.0, "StreakAmount": 0.0, "StreakRustAmount": 0.0,
    "SootAmount": 1.0, "GreaseAmount": 1.0, "TouchAmount": 1.0, "SplashAmount": 0.0, "WetAmount": 1.0,
    "PaintVar": 0.0, "PrimerAmount": 0.0, "ScratchAmount": 0.0, "BaseRough": 0.5, "NewRough": 0.35,
    "BareRough": 0.42, "Metallic": 0.0, "BareMetallic": 0.6, "BareColor": (0.05, 0.047, 0.043),
    "EmissiveStrength": 0.0,
    # brief 5B layers, driven by the fourth mask (zero outside the refined zones, so these are safe
    # defaults): dried spatter, sun fade (to ChalkColor, derived per material), zinc white rust,
    # light scuffs; EmisAge lets the lit diffuser's panel ages tint and dim its glow
    "SpeckAmount": 1.0, "FadeAmount": 1.0, "FadedRough": 0.25, "OxideAmount": 1.0, "ScuffAmount": 1.0, "EmisAge": 0.0,
    "OxideColor": (0.30, 0.30, 0.285),
}
WEATHER_CATEGORIES = {
    # the kiosk's yellow sheets: generations of the same paint over dark steel
    "yellow": {"EdgeWear": 1.0, "RustAmount": 0.85, "GrimeAmount": 0.7, "StreakAmount": 1.25, "StreakRustAmount": 0.9,
               "SplashAmount": 0.6, "PaintVar": 1.0, "PrimerAmount": 0.6, "ScratchAmount": 0.8,
               "BaseRough": 0.42, "NewRough": 0.28},
    # dark painted structure: softened black paint, worn to steel at corners; streaks dry lighter
    "dark_paint": {"EdgeWear": 1.15, "RustAmount": 0.8, "GrimeAmount": 0.6, "StreakAmount": 0.85, "StreakRustAmount": 0.75,
                   "SplashAmount": 0.8, "PaintVar": 0.5, "PrimerAmount": 0.3, "ScratchAmount": 0.8,
                   # on black paint, dried runs and dust read lighter than the paint
                   "StreakColor": (0.17, 0.155, 0.13), "GrimeColor": (0.065, 0.057, 0.045), "MudColor": (0.16, 0.14, 0.11),
                   "BareColor": (0.21, 0.2, 0.19),
                   "BaseRough": 0.46, "NewRough": 0.32, "Metallic": 0.3, "BareMetallic": 0.75},
    # other painted metal (greys, charcoal, machine bodies)
    "paint": {"EdgeWear": 0.8, "RustAmount": 0.7, "GrimeAmount": 0.75, "StreakAmount": 0.85, "StreakRustAmount": 0.7,
              "SplashAmount": 0.7, "PaintVar": 0.3, "PrimerAmount": 0.4, "ScratchAmount": 0.6,
              "BaseRough": 0.52, "NewRough": 0.36, "BareMetallic": 0.7, "BareColor": (0.10, 0.097, 0.092)},
    # bare zinc: rubs brighter, stains dark, rusts only where the zinc is gone
    "galv": {"EdgeWear": 0.5, "RustAmount": 0.45, "GrimeAmount": 0.8, "StreakAmount": 1.0, "StreakRustAmount": 0.5,
             "SplashAmount": 0.7, "PaintVar": 0.4, "ScratchAmount": 0.6, "BaseRough": 0.5, "NewRough": 0.32,
             "BareRough": 0.3, "BareMetallic": 0.9},
    # old oxidised steel and cast iron: heavily stained
    "aged": {"EdgeWear": 0.6, "RustAmount": 1.2, "GrimeAmount": 0.9, "StreakAmount": 1.0, "StreakRustAmount": 1.2,
             "SplashAmount": 0.8, "PaintVar": 0.5, "ScratchAmount": 0.4, "BaseRough": 0.62, "NewRough": 0.5,
             "BareMetallic": 0.5},
    # the lit yellow sign faces: still the cleanest, brightest yellow; seams, joins, edges and runoff age
    # 5B (was grime 0.65, streak 0.35, rust streak 0.12, paint var 0.12): ~20-30% more visible age,
    # per-panel diffuser age (EmisAge) and the runs from the roof, joints and rivets. The sign sits on
    # the tonemapper's shoulder, so its dirt has to dim the glow quite a lot to read on screen.
    "lightbox": {"GrimeAmount": 0.9, "StreakAmount": 1.0, "StreakRustAmount": 0.8, "SootAmount": 0.25, "GreaseAmount": 0.1,
                 "TouchAmount": 0.0, "WetAmount": 0.3, "PaintVar": 0.5, "BaseRough": 0.5, "NewRough": 0.5, "EmisAge": 1.0},
    # the platform slab: dirt, splash, rust stains from the drain and fixings
    "concrete": {"EdgeWear": 0.25, "RustAmount": 0.6, "GrimeAmount": 1.0, "StreakAmount": 0.5, "StreakRustAmount": 0.6,
                 "SplashAmount": 0.6, "PaintVar": 0.5, "BaseRough": 0.7, "NewRough": 0.7, "BareRough": 0.8,
                 "BareMetallic": 0.0, "BareColor": (0.21, 0.205, 0.195), "TouchAmount": 0.0},
}
KIOSK_WEATHER = {
    "Kiosk_YellowPaint": ("yellow", {}),
    "Kiosk_YellowPaint_Dark": ("yellow", {"EdgeWear": 1.15, "RustAmount": 1.0}),  # the older sheets
    "Kiosk_YellowPaint_Faded": ("yellow", {"GrimeAmount": 0.8, "BaseRough": 0.55}),
    "Steel_Dark": ("dark_paint", {}),
    "Conduit_Painted": ("dark_paint", {"EdgeWear": 0.6, "RustAmount": 0.5}),
    "Steel_Charcoal": ("paint", {"EdgeWear": 0.55, "RustAmount": 0.35, "StreakAmount": 0.6, "BaseRough": 0.5}),  # newer retrofit housings
    "Steel_Grey": ("paint", {}),
    "Paint_Grey_Faded": ("paint", {"EdgeWear": 1.0, "RustAmount": 0.9, "StreakAmount": 1.0, "BaseRough": 0.6}),  # HVAC: old, sun-faded
    "Machine_Body": ("paint", {"EdgeWear": 0.7, "RustAmount": 0.5}),
    "Steel_Galvanised": ("galv", {}),
    "Steel_Galv_Dull": ("galv", {"RustAmount": 0.7, "StreakAmount": 1.15, "GrimeAmount": 0.95}),  # oxidised zinc, more stained
    "Steel_Aged_Warm": ("aged", {"BareColor": (0.20, 0.185, 0.17)}),  # 5B: scuffs and chips show lighter steel
    "Rust_Red": ("aged", {"RustAmount": 0.9}),
    "Pipe_Cast": ("aged", {"RustAmount": 1.0, "StreakRustAmount": 1.3}),
    "Copper_Aged": ("galv", {"RustAmount": 0.0, "StreakRustAmount": 0.0, "BareColor": (0.5, 0.26, 0.15)}),
    "Lightbox_Yellow": ("lightbox", {}),
    "Platform_Concrete": ("concrete", {}),
}
# Plain (unweathered) slots aged on one section only, as children of the glTF instance (5B):
# section -> {slot: glTF parameters}. The roof reel's hose: sun-chalked, dusty rubber (the same
# rubber elsewhere on the kiosk stays black).
KIOSK_SLOT_AGED = {"Roof": {"Rubber_Black": {"BaseColorFactor": (0.042, 0.040, 0.037), "RoughnessFactor": 0.9}}}

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
    # Loop seam (prompt 10): LS_Sweep carries tail_s more past its loop end, keyed as the loop's first tail_s (camera,
    # fog, train, traffic, crowd, the loop clock all wrap). The playback range stays the loop; render.py renders the tail
    # when asked (--frames 0-744) and encode_loop.mjs crossfades it over the loop's first frames, so the rain particles
    # (the one thing that can't repeat) flow across the seam instead of jumping.
    "tail_s": 1.0,
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
    "kiosk_zone": (-4.1, 3.9, -3.55, 3.05),  # kiosk, platform, stools, props (10/4: was (-3.6, 3.4, -3.4, 2.9))
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

# ---- Kiosk graphics (signage pass, 2026-10-05, brief 6) -----------------------------------------
# kiosk_graphics.py builds M_KioskGraphic (the cards), M_KioskDecal (marks in the paint) and
# M_KioskLettering (the aged fascia lettering) and applies these numbers. A card picks up the
# weathering of the surface it is stuck to (the kiosk's masks through its UV1), scaled per texel by
# its art's weather response (paper ~1, laminate/vinyl ~0.4, metal ~0.3) and by the amounts below.
GRAPHICS_LOOK = {
    "paper": {"GrimeAmount": 0.9, "StreakAmount": 0.9, "StreakRustAmount": 0.75, "SplashAmount": 0.85, "WetAmount": 0.8,
              "SootAmount": 0.8, "GreaseAmount": 0.9, "SpeckAmount": 0.7, "TouchAmount": 0.8, "AgeTint": 0.45,
              "EmissiveStrength": 0.0, "TileM": 0.0, "DetailScale": 40.0},
    "colors": {"GrimeColor": (0.11, 0.09, 0.06), "StreakColor": (0.17, 0.14, 0.09), "RustStain": (0.33, 0.15, 0.05),
               "MudColor": (0.19, 0.16, 0.12), "SootColor": (0.04, 0.035, 0.03), "GreaseColor": (0.27, 0.18, 0.07),
               "EmissiveTint": (1.0, 1.0, 1.0)},
    # material slot -> (atlas, overrides)
    "slots": {
        "KG_Paper": ("Paper", {}),
        "KG_Labels": ("Labels", {"StreakAmount": 0.75, "GrimeAmount": 0.8}),
        # lit faces: well under the fascia (Lightbox_Yellow 2.8 on (1, 0.6, 0.07)); the faces' own colours tint them
        "KG_Signs": ("Signs", {"EmissiveStrength": 1.25, "StreakAmount": 0.6, "GrimeAmount": 0.6}),  # 1.9 read brighter than the fascia
        "KG_SignFrame": ("Signs", {"TileM": 0.256}),
        # kitchen pass (10/9): the order terminal's screen and displays, tickets, labels (no kiosk weathering:
        # their vertex alpha is 0); lit items glow dimly, a screen in a warm kitchen
        "KG_Kitchen": ("Kitchen", {"EmissiveStrength": 2.0, "AgeTint": 0.3}),
        # exterior pass (10/9): supplier stamps, bin signs, gas labels, tags, stencils, carton print, tape on the
        # ground props (no kiosk weathering: vertex alpha 0); kiosk_exterior.py builds MI_KG_Exterior
        "KG_Exterior": ("Exterior", {"AgeTint": 0.35}),
    },
    "lantern_ink": (0.025, 0.014, 0.008),
    # decal tweaks per item: opacity, tint (multiplies the art)
    "decals": {"ghost_poster": {"opacity": 0.9}, "ghost_dark": {"opacity": 0.9}},
    # decal UV -> atlas: Unreal's decal U runs up the wall and V to the viewer's right here, so swap them and flip V
    "decal_uv": {"SwapUV": 1.0, "FlipU": 0.0, "FlipV": 1.0},
    "decal_order": ["ghost_poster", "ghost_dark", "holes_pair", "holes_row", "residue_a", "residue_b", "residue_c",
                    "stencil_k07", "marker_dates", "marker_breaker"],
    # the fascia lettering: faded vinyl, crazing that leaks the lightbox, the diffuser's streaks and dust
    "lettering_on": True,
    # (first try: dust 0.13, faded ink 0.045, leak 0.6 were invisible past a metre; still subtle, the fascia stays the cleanest sign)
    "lettering": {"FadeOdds": 0.35, "CrackScale": 160.0, "StreakAmount": 1.0, "GrimeAmount": 0.8, "SpeckAmount": 0.8,
                  "LeakStrength": 1.8, "InkColor": (0.012, 0.010, 0.009), "FadedInk": (0.10, 0.08, 0.075),
                  "DustColor": (0.30, 0.26, 0.19), "LeakColor": (1.0, 0.6, 0.07)},
}
# The 24h lightbox's light (L_Lantern_R moved in front of it); dimmer than the fascia's spill
SIGN_24H_LIGHT = {"intensity_cd": 5, "temperature": 3000}

# ---- Kitchen pass (2026-10-09, prompt 7): the working kitchen behind the service opening -------------
# kiosk_kitchen.py builds M_Kitchen and one MI_KK_<material> per kitchen material. A material = a category
# preset + the Blender build's colour / roughness / metal (kitchen.json) + overrides below. Masks: the
# baked vertex colours (R convex edges -> EdgeWear, G occlusion below AOStart + B cavity -> Grime);
# T_KitchenDetail (tiles every detail_tile m) gives smudges / fingerprints (Smudge), brushed grain
# (Scratch) and water spots (Stain); the customer counter's sheet adds its own map (WearAmount, Polish).
# Old but hygienic: grime only in corners and seams, smudges where hands go, no filth.
KITCHEN_LOOK = {
    "detail_tile": 0.5,
    "defaults": {"Roughness": 0.5, "Metallic": 0.0, "EdgeWear": 0.0, "EdgeRough": 0.4, "EdgeMetal": 0.0, "Grime": 0.3, "AOStart": 0.3,
                 "Smudge": 0.2, "Scratch": 0.2, "Stain": 0.1, "WearAmount": 0.0, "EmissiveStrength": 0.0, "Polish": 1.0,
                 "BaseColor": (0.5, 0.5, 0.5), "EdgeColor": (0.6, 0.6, 0.6), "GrimeColor": (0.035, 0.03, 0.022), "Emissive": (0.0, 0.0, 0.0)},
    "categories": {
        "steel": {"Grime": 0.3, "AOStart": 0.25, "Smudge": 0.35, "Scratch": 0.7, "Stain": 0.25},
        "paint": {"EdgeWear": 0.7, "EdgeColor": (0.30, 0.30, 0.29), "EdgeRough": 0.35, "EdgeMetal": 0.85, "Grime": 0.45, "AOStart": 0.35,
                  "Smudge": 0.45, "Scratch": 0.3, "Stain": 0.15},
        "ceramic": {"Grime": 0.15, "Smudge": 0.12, "Scratch": 0.05, "Stain": 0.1},
        "plastic": {"Grime": 0.25, "Smudge": 0.35, "Scratch": 0.2, "Stain": 0.12},
        "paper": {"Grime": 0.3, "Smudge": 0.1, "Scratch": 0.0, "Stain": 0.2},
        "food": {"Grime": 0.0, "Smudge": 0.0, "Scratch": 0.0, "Stain": 0.0},
        "glow": {"Grime": 0.0, "Smudge": 0.0, "Scratch": 0.0, "Stain": 0.0},
    },
    "materials": {
        "KK_Steel": ("steel", {}), "KK_SteelWorn": ("steel", {"Smudge": 0.45, "Stain": 0.4}), "KK_Mesh": ("steel", {"Smudge": 0.2}),
        "KK_Chrome": ("steel", {"Smudge": 0.3, "Scratch": 0.3}),
        # the customer counter: its own wear map (polished pickup zone, scratches along it, faint rings, dark seams)
        "KK_SteelCounter": ("steel", {"WearAmount": 1.0, "Polish": 1.0, "Smudge": 0.2, "Scratch": 0.3, "Stain": 0.12}),
        "KK_POS": ("paint", {"EdgeColor": (0.18, 0.18, 0.17), "EdgeMetal": 0.0, "EdgeRough": 0.3, "Smudge": 0.6}),  # worn corners: darker plastic
        "KK_POSDark": ("paint", {"EdgeColor": (0.28, 0.28, 0.28), "EdgeMetal": 0.9, "Smudge": 0.5}),
        "KK_Cabinet": ("paint", {}), "KK_WallPaint": ("paint", {"EdgeWear": 0.1, "Grime": 0.35, "AOStart": 0.22, "Smudge": 0.15, "BaseColor": (0.58, 0.52, 0.41)}), "KK_Ceiling": ("paint", {"EdgeWear": 0.15, "Smudge": 0.0}), "KK_Floor": ("paint", {"EdgeWear": 0.0}),
        "KK_CeramicWhite": ("ceramic", {}), "KK_CeramicRed": ("ceramic", {}), "KK_CeramicBlack": ("ceramic", {}),
        "KK_Tile": ("ceramic", {"Grime": 0.25, "Stain": 0.2}), "KK_TileOld": ("ceramic", {"Grime": 0.35, "Stain": 0.3}),
        "KK_Rubber": ("plastic", {}), "KK_PlasticBlack": ("plastic", {}), "KK_PlasticGrey": ("plastic", {"Smudge": 0.7}),
        "KK_PlasticRed": ("plastic", {}), "KK_PlasticYellow": ("plastic", {}), "KK_PlasticGreen": ("plastic", {}),
        "KK_PlasticCream": ("plastic", {}), "KK_PlasticBlue": ("plastic", {}), "KK_GlassDark": ("plastic", {"Smudge": 0.5}),
        "KK_PaperCream": ("paper", {}), "KK_Kraft": ("paper", {}), "KK_Cardboard": ("paper", {}), "KK_Cloth": ("paper", {"Stain": 0.35}),
        "KK_ClothBlue": ("paper", {}), "KK_Wood": ("paper", {"Stain": 0.4, "Grime": 0.2}), "KK_WoodDark": ("paper", {}),
        "KK_Soy": ("food", {}), "KK_Broth": ("food", {}), "KK_Water": ("food", {}), "KK_Scallion": ("food", {}), "KK_Chashu": ("food", {}),
        "KK_Menma": ("food", {}), "KK_Egg": ("food", {}), "KK_Nori": ("food", {}), "KK_Onion": ("food", {}), "KK_Beans": ("food", {}),
        "KK_Grout": ("food", {}),
        "KK_Lamp": ("glow", {}), "KK_LampHood": ("glow", {}), "KK_LampShelf": ("glow", {}), "KK_LED_Green": ("glow", {}),
        "KK_LED_Amber": ("glow", {}), "KK_LED_Red": ("glow", {}), "KK_LED_Blue": ("glow", {}),
    },
    # emissive strengths (Emissive = the material's colour); the old interior panel Interior_Light stays at EMISSIVE
    "emissive": {"KK_Lamp": 8.0, "KK_LampHood": 6.0, "KK_LampShelf": 5.0, "KK_LED_Green": 8.0, "KK_LED_Amber": 8.0, "KK_LED_Blue": 6.0},
}
# The kitchen's lights (positions from the Blender build, kitchen.json). First levels (prep 16, rear 9) left the
# opening at 125 (8-bit luma) from the cinematic camera against 188 for the old flat cream recess: too dim for
# "a richer warm glow". Now ~1.4x; the kiosk's own walls and the frame stay as they were. Brighter where the work happens
# (the prep light at the opening, which also spills onto the customer counter), warm pools on the
# cooking line, warmer and dimmer on the shelves, the back corners left to fall off.
KITCHEN_LIGHTS = {
    "L_Kitchen_Prep": {"intensity_cd": 24, "temperature": 3000, "radius_m": 4.0, "barn_deg": 55.0, "barn_cm": 8.0, "volumetric": 0.55},
    "L_Kitchen_Hood_": {"intensity_cd": 6, "temperature": 2600, "radius_m": 1.8, "inner_deg": 25.0, "volumetric": 0.2},
    "L_Kitchen_CeilingR": {"intensity_cd": 12, "temperature": 3200, "radius_m": 2.5, "barn_deg": 80.0, "barn_cm": 3.0, "volumetric": 0.2},
    "L_Kitchen_Shelf_": {"intensity_cd": 3.5, "temperature": 2400, "radius_m": 1.5, "barn_deg": 80.0, "barn_cm": 2.0, "volumetric": 0.1},
    "L_Kitchen_POS": {"intensity_cd": 0.4, "color": (0.45, 0.7, 1.0), "radius_m": 0.7, "volumetric": 0.0, "shadows": False},
}

# ---- Exterior pass (2026-10-09, prompt 8): the ground props round the footprint ---------------------------
# kiosk_exterior.py builds M_Exterior and one MI_KX_<material> per prop material. A material = defaults + a
# category preset + the Blender build's colour / roughness / metal (exterior.json) + overrides below.
# Masks: the baked vertex masks (R edges, G occlusion with the kiosk and the slab, B cavity) and the kitchen's
# tiling detail map at two scales. Rain comes from world position: wet outside the canopy's footprint,
# wind-driven rain reaching Reach x (height below the canopy) under its edges, never onto tops under it, so
# sheltered cartons stay dry and exposed crates, cage and locker read wet like the slab. Splash: dried mud
# specks in a band SplashH cm above the slab (lighter than the dark plastics and paint, as dried mud is). Var: per-instance brightness spread (instanced props only).
# edge_lift (rubbed edges: lighter, greyer) and fade_to (chalky sun fade) derive those colours per material.
EXTERIOR_LOOK = {
    "detail_tile": 0.5, "broad_tile": 2.2,  # metres per repeat of the detail map (UV0 is metre-scale planar)
    "defaults": {"Roughness": 0.5, "Metallic": 0.0, "EdgeWear": 0.0, "EdgeRough": 0.5, "EdgeMetal": 0.0, "Grime": 0.35, "AOStart": 0.4,
                 "Rust": 0.0, "Smudge": 0.2, "Scratch": 0.2, "Fade": 0.0, "Var": 0.0, "Splash": 0.6, "SplashH": 22.0, "Wet": 1.0,
                 "WetDarken": 0.1, "Reach": 0.25, "WetSoft": 18.0, "EmissiveStrength": 0.0,
                 "BaseColor": (0.5, 0.5, 0.5), "EdgeColor": (0.5, 0.5, 0.5), "GrimeColor": (0.035, 0.03, 0.022),
                 "RustColor": (0.13, 0.052, 0.018), "FadeColor": (0.3, 0.3, 0.3), "MudColor": (0.22, 0.19, 0.15), "Emissive": (0.0, 0.0, 0.0)},
    "categories": {
        # moulded plastic: faded colour, corners rubbed paler and matte, handling scuffs
        "plastic": {"edge_lift": 1.7, "fade_to": 0.35, "EdgeWear": 0.75, "EdgeRough": 0.72, "Fade": 0.45, "Grime": 0.3, "Smudge": 0.3,
                    "Scratch": 0.45, "WetDarken": 0.04},
        # enamelled steel: chips to bare steel at edges and handles, oxidation along seams and feet
        "paint": {"EdgeWear": 0.85, "EdgeColor": (0.10, 0.096, 0.09), "EdgeMetal": 0.75, "EdgeRough": 0.38, "Rust": 0.6, "Fade": 0.3,
                  "fade_to": 0.3, "Grime": 0.45, "Smudge": 0.25, "Scratch": 0.5, "WetDarken": 0.06},
        # zinc: rubs brighter, white-rusts in seams, stains in the splash band
        "galv": {"EdgeWear": 0.35, "EdgeColor": (0.46, 0.46, 0.45), "EdgeMetal": 0.95, "EdgeRough": 0.3, "Rust": 0.35,
                 "RustColor": (0.33, 0.32, 0.30), "Grime": 0.5, "Smudge": 0.2, "Scratch": 0.5, "WetDarken": 0.03, "Splash": 0.8},
        # timber: silvered by weather, edges rubbed, soaks up rain
        "wood": {"edge_lift": 1.5, "fade_to": 0.55, "EdgeWear": 0.5, "EdgeRough": 0.85, "Fade": 0.6, "Grime": 0.55, "Smudge": 0.0,
                 "Scratch": 0.3, "WetDarken": 0.3, "Splash": 0.9},
        "paper": {"fade_to": 0.3, "Fade": 0.25, "Grime": 0.3, "Smudge": 0.15, "Scratch": 0.0, "WetDarken": 0.35, "Splash": 0.8},
        "concrete": {"Grime": 0.55, "Smudge": 0.0, "Scratch": 0.1, "WetDarken": 0.3, "Splash": 0.4},
        "rubber": {"fade_to": 0.5, "Fade": 0.4, "Grime": 0.2, "Smudge": 0.2, "Scratch": 0.2, "WetDarken": 0.0, "Splash": 0.7},
        "glass": {"Grime": 0.25, "Smudge": 0.45, "Scratch": 0.15, "WetDarken": 0.0, "Splash": 0.3},
        "metal": {"edge_lift": 1.3, "EdgeWear": 0.4, "EdgeMetal": 1.0, "EdgeRough": 0.25, "Grime": 0.45, "Smudge": 0.35, "Scratch": 0.4,
                  "WetDarken": 0.0},
        "food": {"Grime": 0.0, "Smudge": 0.0, "Scratch": 0.0, "Splash": 0.0, "WetDarken": 0.0},
    },
    "materials": {
        "KX_CrateBlue": ("plastic", {"Var": 0.25}), "KX_CrateGreen": ("plastic", {"Var": 0.25}),
        # the red accent: sun-faded toward a dusty coral, rubbed pink at the corners
        "KX_CrateRed": ("plastic", {"Var": 0.2, "Fade": 0.25}),
        "KX_ToteGrey": ("plastic", {"Var": 0.2, "EdgeWear": 0.5}), "KX_ToteLid": ("plastic", {"Var": 0.2}),
        # the customer bin: handling scuffs, splash marks along its foot. Prompt 10: its broad sun-fade patches, scratch specks
        # and smudges read as mottling at 4K (was Fade 0.45 via the category, Scratch 0.7, Smudge 0.5); the rubbed edges and
        # the splash band at the foot carry the wear now
        "KX_BinBody": ("plastic", {"Scratch": 0.45, "Splash": 1.2, "SplashH": 28.0, "Grime": 0.45, "EdgeWear": 1.0, "Smudge": 0.35, "Fade": 0.3}),
        "KX_BinLid": ("plastic", {"Fade": 0.5, "EdgeWear": 0.9, "Smudge": 0.45}),
        "KX_LockerPaint": ("paint", {"Rust": 0.9, "Fade": 0.45}),
        "KX_CabinetPaint": ("paint", {"Rust": 0.5}),
        "KX_CaseOlive": ("paint", {"Rust": 0.85, "EdgeWear": 1.0}),
        "KX_CylinderGrey": ("paint", {"Var": 0.15, "Rust": 0.45, "EdgeWear": 0.7}),
        "KX_SteelDark": ("paint", {"EdgeColor": (0.16, 0.155, 0.15), "Rust": 0.5, "Fade": 0.0}),
        "KX_GasPipe": ("paint", {"Rust": 0.3}),
        # the cans bin (and the cage): prompt 10: on wet zinc every matte white-rust or grime patch sits next to mirror-like
        # metal reflecting the city, which read as heavy mottling at 4K; white rust kept to the seams, lighter grime
        "KX_Galv": ("galv", {"Rust": 0.12, "Grime": 0.32, "Scratch": 0.3}),
        "KX_Wood": ("wood", {}), "KX_WoodDark": ("wood", {"Fade": 0.35}),
        "KX_Cardboard": ("paper", {}),
        "KX_Concrete": ("concrete", {}),
        "KX_Rubber": ("rubber", {}), "KX_HoseGreen": ("rubber", {"Fade": 0.3}),
        "KX_GlassBrown": ("glass", {"Var": 0.2}), "KX_GlassGreen": ("glass", {"Var": 0.2}),
        "KX_Brass": ("metal", {"Grime": 0.6}), "KX_Copper": ("metal", {}), "KX_Chrome": ("metal", {"Smudge": 0.4}),
        "KX_Cabbage": ("food", {"Var": 0.3}), "KX_Negi": ("food", {}), "KX_NegiWhite": ("food", {}),
    },
    "emissive": {},
}

# ---- Rain contact, drips and steam (2026-10-09, prompt 9; wet_fx.py) --------------------------------------------
# Where the water goes comes from Blender (build_rain_contact.py -> RawContent/rain/T_RainContact.png +
# rain_contact.json: the platform's wet map, drip sources and landing spots, downpipe mouths, steam sources). These
# numbers say how it looks and moves. Every animated effect runs on the MPC_WetFX loop clock (make_sweep.py keys it),
# completes whole cycles per loop and so joins the seam exactly. Water and steam switch separately:
#   node Scripts/ue.mjs Scripts/wet_fx.py --water off|on --steam off|on --contact off|on
WET_FX = {
    # the platform's wet layer (M_KioskWeathered's rain-contact branch, on MI_KW_Platform_Concrete only)
    "contact": {
        "ContactAmount": 1.0,  # master for the platform's wetness (0 = the slab as before)
        "WetDark": 0.52,  # damp concrete darkens
        "WetRough": 0.14, "PoolRough": 0.03, "PoolDark": 0.12,
        "ContactDark": 0.32,  # moist grime round feet, bases and the wall foot
        "DetailAmt": 0.6, "DetailTile": 0.85, "DetailAvg": 0.22,  # concrete texture: tone and roughness variation (world-mapped)
        "RippleAmt": 0.22, "RippleTiling": 1.4, "RippleSpeed": 1.0,  # raindrop rings where rain lands on water / wet concrete
        "RingAmt": 0.35, "RingSpeed": 0.30, "RingDur": 0.55,  # rings where each canopy drip lands
        "EdgeStreak": 1.0,  # wet runoff streaks down the slab's sides below the lip
        "DebugMap": 0.0,  # 1 = show the wet map as colour on the platform (R damp, G standing water, B rain)
    },
    # the street puddles' raindrop rings move to the loop clock too (same look as EasyRain's, now seam-exact)
    "ground_ripples_loop_clock": True,
    # canopy drips (positions from rain_contact.json): period s (divides the loop; slots), skip = share of slots that
    # stay dry (irregular timing), size = drop diameter m, seed. The edge box drips a little faster and larger.
    "drips": {
        "corner_fl": {"period": 1.5, "skip": 0.35, "size": 0.0045, "seed": 1.3},
        "front_joint": {"period": 3.0, "skip": 0.45, "size": 0.0040, "seed": 2.7},
        "edge_box": {"period": 0.75, "skip": 0.18, "size": 0.0062, "seed": 4.1},
        "left_joint": {"period": 2.5, "skip": 0.40, "size": 0.0040, "seed": 5.9},
        "right_edge": {"period": 2.0, "skip": 0.40, "size": 0.0042, "seed": 7.3},
    },
    "drip_look": {"width_m": 0.16, "Streak": 1.0, "SplashDur": 0.16, "SplashV": 1.1, "Grow": 0.45, "Opacity": 1.0,
                  "WaterColor": (0.45, 0.47, 0.5), "Roughness": 0.05, "Specular": 1.0,
                  # a drop refracts a wide patch of its surroundings: it shows the bright fascia it drips from (sampled
                  # RefractUp of the frame above it), so it catches the sign's warm light near the top and dims as it falls
                  "Refract": 1.2, "RefractUp": 0.05},
    # downpipe trickles: shoe mouth onto the splash block (beads streaming at Flow m/s, Skip = gaps)
    "trickles": {"pipe_fr": {"flow": 0.55, "skip": 0.55, "size": 0.005, "seed": 3.3},
                 "pipe_bl": {"flow": 0.45, "skip": 0.7, "size": 0.0045, "seed": 8.8}},
    "trickle_look": {"width_m": 0.10, "Streak": 0.75, "SplashDur": 0.12, "SplashV": 0.6, "Refract": 0.35},
    # steam: cards turned to the camera, density from noise carried upward (whole tiles per loop), lit by the scene's own
    # lights through the translucency volume (no glow of its own). Prompt 10 (M_FX_Steam reworked, wetfx_hlsl.STEAM_HLSL):
    # the noise is laid out in metres (the old card-unit noise stretched eddies into vertical streaks on tall cards), the
    # column meanders, widens and thins as it rises and breaks into wisps higher up, its sides eaten by the noise; cards
    # are wide enough that the plume fades out well inside them. Base / Spread m (half-width at the source / per m of
    # rise), Rise m/s, Sway cycles/s, SwayAmp m of meander per m of rise, Scale eddy frequency (1 = billows ~0.3 m),
    # Thresh / Breakup / Soft: the density threshold at the source, its climb by the top, its softness (the noise's mean
    # is 0.51, sd ~0.08 for the blend read: Thresh 0.40 keeps the core filled, +Breakup by the top leaves only wisps).
    "steam": {
        # kept faint (prompt 10): the stock pot, the prep area and the kitchen's darker depth must stay readable through it
        "pot": {"cards": [{"w": 0.50, "h": 0.40, "seed": 0.21, "yaw_off": 0.0}],
                "Opacity": 0.55, "Rise": 0.18, "Sway": 0.1, "SwayAmp": 0.08, "Base": 0.05, "Spread": 0.25, "Scale": 3.0,
                "Thresh": 0.42, "Breakup": 0.10, "Soft": 0.18, "Lean": 0.0, "Fade": 6.0,
                # the hood lamps shine straight down through it; the translucency lighting volume is too coarse to catch
                # their narrow cones, so their in-scatter is carried here (warm, about the lamps' colour)
                "Ambient": (0.45, 0.36, 0.25)},
        # from the floor camera the corner HVAC hides the fan: the plume shows once it climbs past ~6 m, so the cards are tall
        # and lean toward the street side (kiosk +X) as they thin out
        "roof_fan": {"cards": [{"w": 3.6, "h": 3.4, "seed": 0.63, "dx": 0.0}, {"w": 3.0, "h": 2.8, "seed": 0.11, "dx": 0.15}],
                     "Opacity": 0.34, "Rise": 0.30, "Sway": 1.0 / 15.0, "SwayAmp": 0.06, "Base": 0.25, "Spread": 0.22, "Scale": 1.0,
                     "Thresh": 0.37, "Breakup": 0.12, "Soft": 0.24, "Lean": 0.9, "Fade": 15.0,
                     # nothing lights the roof: what reveals a plume up here is scattered city glow, so it carries an
                     # in-scatter term (grey-blue, like the haze); keep it a soft grey wisp, never a white cloud
                     "Ambient": (0.30, 0.34, 0.38)},
        # the flue's vapour (warm, moist combustion gas condensing in the cold rain): leaves under the rain cap, thin; the
        # plume the cinematic camera sees above the roof
        "flue": {"cards": [{"w": 2.6, "h": 2.8, "seed": 0.37, "dx": 0.0}],
                 "Opacity": 0.50, "Rise": 0.45, "Sway": 1.0 / 10.0, "SwayAmp": 0.06, "Base": 0.10, "Spread": 0.22, "Scale": 1.0,
                 "Thresh": 0.37, "Breakup": 0.12, "Soft": 0.24, "Lean": 0.6, "Fade": 12.0,
                 "Ambient": (0.34, 0.38, 0.42)},
    },
    "steam_look": {"SteamColor": (0.80, 0.80, 0.80), "Ambient": (0.0, 0.0, 0.0), "wind": (0.95, -0.3)},  # the plume drifts toward kiosk +X, a little back (Unreal +X, -Y)
}

# ---- Final polish (prompt 10, 2026-10-10; polish.py) ----------------------------------------------------------------
# Roof light. From the floor camera the roof machinery read as one dark mass against the viaduct's underside (4K
# luma: HVAC faces ~18, condenser ~10, against ~29 behind them). Two soft, shadowed spot lights stand in for light that
# is really there: the city and the wet street behind the camera (cool, broad, from the front-left and ~35 deg up, so
# the faces the orbit sees catch it and the gaps between units stay in shadow) and the SAME CITY screen to the right
# (its own blue: a rim along the right-hand units' sides and tops). Lighting channel 1 only, and only the roof
# machinery's actor joins channel 1, so the fascia, canopy, deck, walls, street and props are untouched; no
# volumetric scattering (no beam in the fog); MegaLights off for these two (the classic path honours channels).
# Positions are the Blender kiosk frame (m).
ROOF_LIGHT = {
    "actors": ["SM_Kiosk_Roof"],
    "lights": {
        "L_Roof_CityBounce": {"pos": (-5.55, -5.20, 8.0), "target": (-0.60, -0.60, 3.45), "cd": 150.0, "color": (0.62, 0.72, 0.86),
                              "outer_deg": 30.0, "inner_deg": 6.0, "source_radius_m": 2.0, "radius_m": 12.0, "specular": 0.5},
        "L_Roof_ScreenRim": {"pos": (6.30, 0.20, 8.0), "target": (0.20, -0.60, 3.60), "cd": 120.0, "color": (0.50, 0.75, 1.00),
                             "outer_deg": 30.0, "inner_deg": 6.0, "source_radius_m": 1.5, "radius_m": 12.0, "specular": 0.6},
    },
}
