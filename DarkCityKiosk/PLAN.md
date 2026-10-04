# Dark City Kiosk — Plan

A seamless, looping 4K rain ambience built around the kiosk in `_reference/PrimaryReference.png`. The camera orbits very slowly about 90° around the kiosk and back. Around it there is rain, puddle drops, fog, umbrella crowds, flying cars, flashing LED ads, pulsing lights, blinking tower beacons, and a train that passes once per loop.

## Locked decisions (2026-10-03)

- **Tools:** Unreal Engine 5.8 is the main tool, rendered with Movie Render Queue. The hero kiosk is built in Blender 5.2.
- **Camera:** a ping-pong orbit (A → B → A) with eased stops, so it loops seamlessly. The reference view sits at the middle of the arc; the arc is ±45°. The video camera is kiosk_config.VIDEO_CAM (shared by Blender and Unreal): a 20 mm wide-angle lens, 10 cm off the floor, 0.807x the reference distance, tilted up 15.8°. The kiosk towers over the viewer, with puddle reflections in front and tower tops visible above.
- **Format:** 24 fps, 4K final. Tests are 30 s loops; the final loop is 5 min. Everything that moves repeats a whole number of times per loop. Particle seams are hidden with a short crossfade at a camera stop.
- **Fresh start:** nothing is imported from the Night Kiosk project. Fab assets are bought where they save time; EasyRain (rain, puddles, droplets) is already in.
- **Kiosk choices:** see `docs/KIOSK-SPEC.md` → "Choices to settle". Glazed window, a コーヒー corner sign, the 24時間営業 lantern, two red stools.

## Phases

| # | Phase | Status |
|---|---|---|
| 0 | Spec sheet, reference camera solve, Unreal project, EasyRain | done (Sat 10/3) |
| 1 | Grey-box kiosk in Blender, matched to the reference | done (Sat 10/3) |
| 2 | Grey-box in Unreal: wet ground, rain, fog, placeholder lights and city, camera sweep, preview render | done (Sat 10/3): previews v1-v3 in Renders/ |
| 2b | Mist look: "on again, off again" dense mist with fine rain (first pass: fog waves + patchy rain) | iterating with the user |
| 3 | Kiosk detail modelling, all scripted (build_kiosk.py + kiosk/ modules): 1 shell+canopy, 2 openings+interior, 3 wall clutter+lanterns+signs, 4 roof machinery, 5 texture prep (vertex-colour edge/AO masks) | steps 1-4 done (10/3; step 4 not yet exported to Unreal); Unreal uses kiosk_detail.glb (dck.KIOSK_GLB) |
| 4 | Kiosk surfacing: paint, wear, rust, grime, decals, wetness/drips; sign art | |
| 5 | City: towers, viaduct, bridges, ad screens with animated content, beacons | towers + landmark + procedural windows (v9); LED screens + neon (setup_screens); viaduct + train running into RightA once per loop (v10, 10/3); instanced city background in 4 depth bands + deeper MIRAI landmark + blue-gray far fog + night-sky cubemap sky light (10/3, setup_city_bg / atmosphere; preview_v18) |
| 6 | Life: umbrella crowds, flying cars, train, steam, pulsing lights | six flying-vehicle types in altitude-layered air corridors with baked motion, per-variant schedules, a hero pass through a light shaft (10/4, preview_v22_traffic); flying cars (v12, 10/3); crowd: 16 walkers + 1 standing in scripted coats, hoods and hats, ~20% without umbrellas (v17, 10/3) |
| 7 | Loop timing (5 min), seam crossfade, final 4K renders, encode, long-form assembly | |

## Where things are

```
DarkCityKiosk/
  _reference/            reference images (PrimaryReference.png is the target)
  docs/KIOSK-SPEC.md     kiosk spec: dimensions, parts, signs, lights, choices
  docs/reference_camera_solve.json, measure-grid-*.png
  Blender/scripts/       kiosk_config.py (all kiosk numbers), build_kiosk_blockout.py,
                         export_kiosk_glb.py, solve_reference_camera.mjs, fit_to_reference.mjs
  Blender/kiosk_blockout.blend, Blender/renders/
  Unreal/                DarkCityKiosk.uproject; Scripts/ (see below); RawContent/ (imports)
  Renders/               stills/, frames/<tag>/ (ignored by git), <tag>.mp4
```

## Rebuild commands

Blender (from `Blender/scripts`):

```
blender -b --factory-startup -P build_kiosk_blockout.py -- --render   # .blend + check renders
blender -b ../kiosk_blockout.blend --factory-startup -P export_kiosk_glb.py   # grey box -> RawContent/kiosk_blockout.glb
blender -b ../kiosk_detail.blend --factory-startup -P export_kiosk_glb.py     # detailed -> RawContent/kiosk_detail.glb (what Unreal uses)
blender -b --factory-startup -P build_kiosk.py -- --render --tag d2   # detailed kiosk -> kiosk_detail.blend + review renders
blender -b --factory-startup -P build_city.py -- --export              # city + viaduct -> RawContent/city.glb + city_manifest.json (city_config.py)
blender -b --factory-startup -P build_train.py                           # train -> RawContent/train.glb
blender -b --factory-startup -P build_flying_vehicles.py -- --render     # the six vehicle types + cargo container -> RawContent/flying_vehicles.glb (+ renders/veh_*.png)
blender -b --factory-startup -P build_umbrella.py -- --render            # umbrella variants -> RawContent/umbrellas.glb
blender -b --factory-startup -P build_outfits.py -- --render             # coats, hoods, hats fitted to the bodies -> RawContent/outfits.glb
```

Unreal (from `Unreal/`, with the editor open; in Git Bash run `export MSYS_NO_PATHCONV=1` first):

```
node Scripts/ue.mjs Scripts/import_kiosk.py      # re-import the kiosk GLB in place
node Scripts/ue.mjs Scripts/setup_scene.py       # ground, fog, lights, city, rain (scene_config.py)
node Scripts/ue.mjs Scripts/ground.py            # just the street: concrete slabs + puddle height mask + EasyRain puddle settings
node Scripts/ue.mjs Scripts/setup_city.py       # city meshes, window shader, screen/shop glow lights
node Scripts/ue.mjs Scripts/setup_city_bg.py    # instanced city background (scene_config.CITY_BG); --show old|new to compare
node Scripts/ue.mjs Scripts/atmosphere.py       # height fog + night-sky cubemap sky light (scene_config.FOG / SKY)
node Scripts/ue.mjs Scripts/kiosk_look.py       # kiosk light levels, their fog glow, glowing materials (scene_config kiosk section)
node Scripts/ue.mjs Scripts/setup_screens.py    # ad screens + neon signs (re-composes _ads/ art via make_screens.ps1)
node Scripts/ue.mjs Scripts/setup_train.py      # train actor + its lights (after: blender build_train.py)
"C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe" Scripts/traffic_plan.py --replan        # air corridors (offline, ~20 min) -> RawContent/traffic_routes.json; then setup_city_bg.py
"C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe" Scripts/traffic_plan.py --replan-hero   # only the hero route (~1 min)
node Scripts/ue.mjs Scripts/setup_traffic.py    # vehicles + lights + hero light shaft; schedule for scene_config.VARIANT -> RawContent/traffic.json (then make_sweep)
"C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe" Scripts/crowd_paths.py   # walker plan (offline, ~3 min) -> RawContent/crowd_plan.json
node Scripts/ue.mjs Scripts/export_bodies.py    # mannequin bodies (ref pose, dominant bones, joints) -> RawContent/bodies/ for build_outfits.py
node Scripts/ue.mjs Scripts/setup_outfits.py    # skin the coats/hoods with the bodies' weights -> SKM_<Body>_Coat / _CoatHood
node Scripts/ue.mjs Scripts/setup_crowd.py      # the crowd -> RawContent/crowd.json (then make_sweep)
node Scripts/ue.mjs Scripts/make_sweep.py        # CAM_Sweep + LS_Sweep (+ fog waves, train, cars, crowd). Re-run after any setup_* that respawns actors
node Scripts/ue.mjs Scripts/capture_stills.py --tag test        # quick editor stills
node Scripts/ue.mjs Scripts/render.py --tag preview --temporal 4 # MRQ, full 30 s at 1080p (A = frame 0, Mid = 180, B = 360)
node Scripts/ue.mjs Scripts/render.py --tag still_mid --frames 180-181 --temporal 8   # one still; one range per call
node Scripts/encode.mjs preview                                 # -> Renders/preview.mp4
```

## Flying traffic

The street is a canyon: from the floor camera the near towers fill nearly the whole frame, so cars
can only be seen in front of facades and in the vista gap above the kiosk. `traffic_lanes.py` (pure
Python; try it with Blender's `5.2/python/bin/python.exe Scripts/traffic_lanes.py`) searches for
routes made of two straight legs and one smooth turn. A route is kept only if:

- the whole route clears every tower, the landmark and the viaduct;
- both ends are hidden from every camera pose on the orbit, whether behind a tower, off frame, or
  in the haze past 280 m.

Routes are ranked by how many metres a car spends on screen. `setup_traffic.py` puts each car on a
route, offset to the right of travel so the two directions pass apart. It gives each car the
shortest period (10, 15 or 30 s) that fits its run, and writes the paths with their bank angles to
`RawContent/traffic.json`. `make_sweep.py` keys every car linearly, every 0.25 s. Scale and light
intensity ramp over 1.5 s at both ends of a run, and between runs the car waits 400 m underground.
Tunables: `scene_config.TRAFFIC`.

## Street and puddles

The user's note (10/3): the old ground read as a flooded pool, but the reference is concrete with
puddles ("more street, a little less water"). The cause: EasyRain's puddle function tiles one
puddle texture every 150 m, so around the kiosk it was a single puddle. `ground.py` now builds
M_Ground_Wet with its own puddle layer:

- **Concrete:** poured-concrete slabs, 3 m, using StarterContent textures mapped in world space,
  with grime, large-scale variation, darker joints and a fine 12 cm grit normal. The big concrete
  normal is off: from 10 cm up it bent reflections into waves.
- **Height mask:** macro noise plus two Perlin octaves, sampled from blurred mips. Full-resolution
  grain made hundreds of tiny puddles that read as choppy water. Slabs settle unevenly, and the
  joints sit lower.
- **Puddles** form where height < coverage (~14%). They are dark mirrors with EasyRain's raindrop
  ripples (normal 0.15; wind ripples off). A damp ring surrounds each puddle, and the concrete
  between puddles is only slightly wet, at roughness ~0.3, which stretches lights into vertical
  streaks.
- **Foreground band:** with the lens 10 cm up, the kiosk is mirrored only in water within ~1.5 m of
  the camera. So a dip in a band just inside the orbit (radius 8.4–11.2 m) makes about half of
  that band puddle. The kiosk's reflection slides in and out of puddles as the camera moves.

Tunables: `scene_config.GROUND`. EasyRain's world puddle settings are no longer used.

## Moving lights

Every light that moves (train headlight, car lights) casts shadows. MegaLights makes that cheap.
An unshadowed light shines through the viaduct deck and towers. The train's interior lights did
exactly that, lighting the deck's underside, so they were removed (10/3).

## Umbrella crowd

The crowd uses the user's packs: Female NPC pack Vol.2 (Quinn body and its umbrella walk and idle)
and the NPC Animation Pack (Manny body).

- **Animation:** both bodies play the Female pack's clips. Manny's skeleton lists Quinn's as
  compatible. The male umbrella clip is a start-walk-stop and doesn't loop. `setup_crowd.py`
  makes root-locked copies of the clips (`/Game/DarkCity/Crowd/Anims`), and the actor carries the
  walker along its path at clip speed × play rate (1.328 m/s at rate 1).
- **Umbrella:** `build_umbrella.py` puts the grip at the origin with the shaft on +Z. It attaches
  to hand_r at (-7, 2.5, 0) cm, with the shaft along (-0.40, -0.10, 0.91) in hand space. Both
  values were measured from the clips.
- **Paths:** `crowd_paths.py` (offline, numpy) plans them. A dark figure against glowing mist is
  visible even 60 m away, so the haze can't hide anyone appearing. Every walker appears and
  disappears where the camera can't see them at that moment of the sweep: behind the kiosk, a
  pier or a tower, or off frame. Path, direction and start time are searched together; walkers
  stay 1 m apart and keep 3.5 m from the camera's path.
- **Standing:** two people stand all loop. The front-right spot (3.0, -5.8) is the only place in
  frame for the whole sweep that never covers the kiosk.
- **Keys:** `make_sweep.py` keys transforms every 0.5 s and restarts the walk clip at each run. A
  run crossing the loop seam is split, with the clip offset carried over. Idles play a whole
  number of cycles per loop.

Tunables: `scene_config.CROWD` (paths) and `CROWD_LOOK` (bodies, coats, umbrella mix, grip).

### Coats, hoods and hats

The user's notes (10/3):
- The bare mannequins read as mannequins.
- The figure front-right of the kiosk was distracting, so it was removed.
- Not everyone needs an umbrella: about 20% go without (coat plus a hat or a hood).

**Pipeline:**
- `export_bodies.py` writes each body (Quinn, Manny) in its reference pose, with every vertex's
  dominant bone and the mesh's own joints.
- `build_outfits.py` (Blender) builds the garments around each body:
  - **Coat body:** horizontal slices of the torso, each wrapped by its convex hull plus 2.8 cm and
    smoothed. The coat hangs from the widest points, so no anatomy shows.
  - **Sleeves:** tubes along the shoulder → elbow → wrist, sized from the arm.
  - **Collar, belt, and skirt:** the skirt flares to below the knee, with a front slit, and is
    widened wherever the A-pose legs would poke through.
  - **Hood:** the head and neck, smoothed and pushed out, with the face cut open.
  - **Rigid hats:** fedora, flat cap, beanie.
  - A custom shell thickener replaces bmesh.ops.solidify, which spiked at the head's tight folds.
- `setup_outfits.py` gives the garments the body's own weights (GeometryScript
  transfer_bone_weights_from_mesh). The skirt is weighted by hand, pelvis into the same-side
  thigh, so it swings with the stride. Everything is merged into SKM_<Body>_Coat / _CoatHood on
  the same skeletons.
- `setup_crowd.py` places the people:
  - Hats go on the head bone at the inverse of the head's reference transform.
  - People without umbrellas play the Female pack's crossed-arms walk, which has the same 13.6 s
    loop and 1.328 m/s as the umbrella walk.
