# Dark City Kiosk: session handoff (2026-10-03)

Read this first, then `PLAN.md` in this folder: phases, rebuild commands, and how each system
works. Every number lives in two config files:
- `Unreal/Scripts/scene_config.py`
- `Blender/scripts/kiosk_config.py` and `Blender/scripts/city_config.py`

## The project

The target is a seamless, looping 4K rain ambience for YouTube, built around the yellow cyberpunk
kiosk in `_reference/PrimaryReference.png`. The camera does a slow ping-pong orbit (A → B → A,
±45°) at 24 fps. Test loops are 30 s; the final loop will be 5 min. Unreal Engine 5.8 renders
with MRQ. Blender 5.2 builds every asset, all scripted. The Unreal editor is driven from the
terminal with `node Scripts/ue.mjs Scripts/<script>.py`, run from `Unreal/`. In Git Bash, run
`export MSYS_NO_PATHCONV=1` first.

**Latest preview:** `Renders/preview_v25_fog.mp4`: low-lying fog, a softer NEXUS glow and shinier puddles, on top of the flying vehicles and the toned-down kiosk (`Renders/stills/fog_puddles_before_after.png`, `kiosk_brightness_before_after.png`). Stills (`hero_glow_before_after.png` is the glow change):
- `Renders/stills/traffic_v22_types.png` and `traffic_v22_hero.png`: the vehicles and the hero pass in the render.
- `vehicles_blender_v1.png`: the vehicle models.
- `mirai_sign.png`: the landmark sign.
- City background comparisons: `bg_mid_before_after_ref.png`, `bg_AB_before_after.png`, `bg_passes_mid.png`.

## Decisions the user has locked (don't re-litigate)

- **Tools:** UE 5.8 is the main tool, rendered with MRQ. The kiosk and all props come from Blender, all scripted.
- **Imports:** nothing comes from the old Night Kiosk project. Fab purchases are fine.
  - Owned: EasyRain, NPC Animation Pack, Female NPC pack Vol.2, Ultra Dynamic Sky (unused so far).
- **Camera:** `kiosk_config.VIDEO_CAM` holds a 20 mm lens, 10 cm off the floor, distance_scale 0.807, pitch 15.8°, arc ±45°.
- **Mist:** "fine snow-like mist drops and breathing haze". Fog waves twice per loop.
  - Changed 10/4 at the user's request ("so much fog that it's really washing out everything"): the fog now hugs the ground (height falloff 0.32), and the luminous air glow (VolumetricFogEmissive) is cut to about a third, since it is uniform over the first 120 m and veiled everything.
- **Ground:** concrete with puddles, **not** a flooded pool ("more street, a little less water"). Keep the kiosk's reflection in the foreground puddles.
- **Viaduct:** deck at 14 m. The train passes once per loop.
- **Crowd:**
  - Coated silhouettes; about 20% without umbrellas.
  - **No one standing front-right of the kiosk.** The user removed that figure as distracting.
  - Moving lights must never shine through the viaduct deck; the user spotted that once.
- **Deferred:** the rust/grime surfacing pass, possibly as an overnight 4K render.

## How the user likes to work

- **Fewer renders.** Each Unreal render launches a separate process that crashes on exit (EasyRain GPU particles; frames are already written by then). Render only at milestones.
  - For checks, render a single frame (`--frames N-N+1`), or preview offline (Blender/numpy) first.
  - A full 30 s 1080p preview takes about 15 min.
- **Communication:**
  - Report results plainly, with the mp4 path and a stills sheet.
  - The user is learning Unreal, so explain choices briefly.
  - They give feedback as annotated screenshots (red arrows).
- **Commits:** don't commit unless asked. The whole `DarkCityKiosk/` folder is still untracked in git; nothing has been committed yet.

## What's built (all re-runnable)

| System | Where |
|---|---|
| Kiosk (detailed, scripted) | `Blender/scripts/build_kiosk.py` + `kiosk/` → `export_kiosk_glb.py` → `Unreal/Scripts/import_kiosk.py` |
| Scene: fog, lights, rain, post | `setup_scene.py`; `kiosk_look.py` re-applies the kiosk light levels, fog glow and emissive strengths from scene_config without a rebuild |
| Street ground, own puddle layer | `ground.py` |
| City: hero towers, viaduct, ad screens (Blender) | `build_city.py --export` → `setup_city.py` |
| City background: ~430 instanced towers in 4 depth bands, the MIRAI landmark, the 3 vista ad towers rebuilt (their screens re-hosted), skybridges, neon, blinking beacons | `city_bg_layout.py` (pure Python, also runs in Blender's python) → `setup_city_bg.py`; tunables `scene_config.CITY_BG`; `--show old` / `--show new` flips to the hidden Blender fill for comparison |
| Fog + sky light (night-sky cubemap) | `atmosphere.py` (setup_scene.py calls it too) |
| LED ad screens and neon (the user's art in `_ads/`, all 7 in) | `make_screens.ps1` / `setup_screens.py` (`screens.json`) |
| Train | `build_train.py` → `setup_train.py` |
| Flying vehicles (6 types, docs/FlyingVehicles): courier, air taxi, commuter pod, aerial transit, cargo lifter (+ swinging container), hero | `build_flying_vehicles.py` → `setup_traffic.py`; corridors + schedule + baked motion from `traffic_plan.py` (pure Python; corridors cached in `RawContent/traffic_routes.json`) |
| Crowd: 16 walkers + 1 standing | see the crowd pipeline below |
| Sequence: camera, fog waves, train, cars, crowd | `make_sweep.py` (**re-run after any setup_* that respawns actors**) |
| Render / encode | `render.py --tag <name> [--frames a-b] [--res WxH] [--fog-clear]`, then `node Scripts/encode.mjs <tag>`. `--fog-clear` switches the mist-wave keys off for that render (the Mid pose sits on a mist peak) and back on afterwards |

**Crowd pipeline:**
1. `build_umbrella.py` (Blender) builds the umbrellas.
2. `export_bodies.py` exports the mannequin bodies.
3. `build_outfits.py` (Blender) builds the coats, hoods and hats.
4. `setup_outfits.py` skins the garments onto the bodies.
5. `crowd_paths.py` plans the walks. Run it offline with Blender's python; it takes about 3 min.
6. `setup_crowd.py` spawns the people.

## Gotchas worth knowing before touching things

- **Python:** `python` on this machine is the Windows Store stub and hangs. Use Blender's interpreter: `"C:/Program Files/Blender Foundation/Blender 5.2/5.2/python/bin/python.exe"` (it has numpy).
- **Don't run editor scripts during a render.** The render process is separate; `render.py` handles saving.
- **Coordinates:** Blender kiosk frame (m) → Unreal (x·100, −y·100, z·100).
  - glTF via Interchange imports a single-mesh file named after the FILE.
  - The mannequins face +Y in component space, so actor yaw = heading − 90.
- **Sequencer, UE 5.8:**
  - A skeletal anim section's play rate is a `MovieSceneTimeWarpVariant` (`set_fixed_play_rate`).
  - Setting a section's params resizes it, so call `set_range` afterwards.
- **Loop safety:** everything periodic completes whole cycles per loop. Cars and walkers appear and disappear only where the camera can't see them at that moment, and wait 400 m underground between runs. Check the frames either side of the loop point after changes.
- **Ground:** from a 10 cm-high lens, small puddles and coarse normal maps read as choppy water. The kiosk mirrors only in water within ~1.5 m of the lens.
- **City background (10/3):** the Blender fill towers (City_Mid*, City_Far_*), City_Landmark, the three vista ad towers and the fill towers' shop lights are hidden, not deleted.
  - `setup_city.py` respawns its L_Shop_* lights visible, so run `setup_city_bg.py --show new` after it.
  - From the 10 cm lens the frame top is 42.6° up and the viaduct top 16–23° up: a tower D m away clears the rail only above ~0.42·D, and keeps its top in frame only below ~0.92·D. The layout picks heights by elevation for that reason (the vista "V" of visible crowns and sky).
  - Flying traffic shares the city through **air corridors**. The corridors are planned ignoring bands 1–2 and the skybridges, and the whole background is then laid out clear of them (`keepout.avoid_traffic`). `setup_city_bg.py` ends by refreshing each corridor's visibility in the finished city (`traffic_plan.remask`).
  - After changing CITY_BG: `setup_city_bg.py` → `setup_traffic.py` → `make_sweep.py`.
  - To search new corridors: `traffic_plan.py --replan` (offline, several minutes) → `setup_city_bg.py` → `setup_traffic.py` → `make_sweep.py`.
- **Loop variants (final render):** `scene_config.VARIANT` holds the traffic seed, train on/off, hero on/off and density.
  - No traffic run crosses the loop seam, so every variant starts and ends with the same empty sky and they splice in any order.
  - Per variant: edit VARIANT → `setup_traffic.py` → `make_sweep.py` → render.
- **Traffic behaviour:** vehicles appear and disappear only where the camera can't see at that moment. Corridor visibility is cached for every 2° of the sweep.
  - Motion is baked per run: overshoot-and-settle stops, pod station waits with a slow turn, lagged banking, acceleration pitch, hover bob, and the cargo container's pendulum sway.
  - The hero crosses a static spotlight shaft (`L_HeroShaft`, inside the 120 m volumetric-fog range) while on screen.
  - EasyRain only spawns rain near the camera, so the "rain displacement" under the lift rings is faked: a soft additive glow card (`M_Vehicle_LiftMist`) plus a shadowed under-light. Red nav lights blink at 1.5 s with a per-vehicle phase (custom primitive data).
  - Window shader: instance sizes go in per-instance custom data (10 floats), windows are world metres, and the grid fades to its average below ~3 px (no shimmer).

## Open items, the user's list

1. Whatever the user brings to the new session (fixes/changes first).
2. Blinking red beacons on tower tops (`city_manifest.json` lists them under `beacons`) and gently pulsing lights.
3. Steam around the kiosk base (the reference has it).
4. The 5-minute loop timing, a seam crossfade if needed, final 4K renders, encode.
5. The rust/grime surfacing pass on the kiosk (vertex-colour masks are already baked into `kiosk_detail.glb`).

**Known minor points:**
- Small points at the coat shoulders; they don't show at crowd distance.
- The male walk uses the female pack's clip; the male pack's umbrella clip doesn't loop.
- Previews render at 1 sample, so finals need temporal samples (`--temporal`).
