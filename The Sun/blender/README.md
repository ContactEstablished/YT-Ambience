# Solar Observatory — Blender edition

A separate native Blender interpretation of the existing **The Sun** web scene. Built and rendered with the installed **Blender 5.2.1 LTS** on September 8, 2026. The Three.js project remains intact.

The scene contains a rotating orange-gold photosphere, flowing granulation, evolving dark magnetic regions, a gently breathing volumetric corona, magnetic loops, randomly scheduled broad plasma ejections, and a warm star field. It uses editable Blender geometry, shader nodes, and native animation drivers. No downloaded textures, add-ons, simulation caches, or extra assets are required.

This is a Blender scene with timeline playback and adjustable controls. It does not run inside the old web page. The previous page remains available for browser interaction; Blender produces native viewport previews, stills, and rendered animation.

## Open and use

1. Double-click **[Open Sun.cmd](Open%20Sun.cmd)** to open the scene and register its optional control panel. The launcher uses the installed Blender 5.2 path. Alternatively, open **[solar_observatory.blend](solar_observatory.blend)** directly.
2. In the 3D viewport, press **N**, then choose the **Solar** tab. When opening the `.blend` directly, the same settings are available by selecting **SUN CONTROLS** in the Outliner and expanding **Object Properties → Custom Properties**. To enable the sidebar manually, run the embedded `sun_controls.py` once in Blender's Text Editor.
3. Press **Space** to play/pause. The saved composition is at frame 180; **Shift + Left Arrow** returns to the start. The timeline runs from frame 1 to 1800 at 30 fps.
4. Press **Numpad 0** for the camera view. Use normal Blender orbit/pan controls to inspect the model; **Sun size** adjusts its scale within the camera composition.
5. Press **F12** for a final Cycles still. Material Preview is the saved startup mode for easier navigation. **Z, R** switches to rendered viewport shading, which can be slower. The final render is the reference for volume, color, transparency, and glow.
6. Save your chosen settings with **Ctrl + S**. The sidebar is optional UI and must be registered again after restarting Blender, using the launcher or embedded text. The scene renders and animates without registering it.

The PowerShell launcher also accepts a different installation path:

```powershell
.\blender\Open-Sun.ps1 -BlenderExe 'D:\Apps\Blender\blender.exe'
```

## Controls

All numeric controls default to **1.0**; stars default on.

| Setting | Range | What it changes |
| --- | --- | --- |
| Rotation | 0–20 | Rotation multiplier; 1 is approximately one turn every 349 seconds. Zero sets a static orientation. |
| Surface flow | 0–3 | Speed of the surface's warped noise and dark-region evolution. Zero gives a static texture phase. Flares continue independently. |
| Sunspots | 0–3 | Coverage of the dark magnetic masks. Zero removes these masks while retaining the natural light/dark texture of the plasma. |
| Flare activity | 0–3 | Number of active loops and eruption slots, plus eruption timing and plume texture speed. Zero hides all loops and ejections. |
| Flare intensity | 0–3 | Brightness of loops and broad ejections, independently of their frequency. Zero hides the geometry. |
| Corona glow | 0–2 | Emissive volume strength, including its small breathing variation. Zero removes the corona; compositor glow from bright objects can remain. |
| Sun size | 0.55–1.35 | Scales the photosphere, corona, loops, and ejections together within the fixed camera. |
| Stars | On/off | Shows or hides the star field. |

**Play/Pause** holds the timeline and therefore all animation. **Reset view** restores camera view and Sun size to 1; it retains effect settings and the current animation frame. Standard Blender navigation replaces the web page's drag/scroll interactions.

### Timing and randomness

The saved scene has a reproducible random seed of **73491**. Eruption locations, sizes, shapes, start times, durations, and gaps are varied during construction. About 26% of generated events use the stronger size/brightness range. Three crossing turbulent sheets form each broad arch or jet; smooth envelopes fade events in and out. Small loops have separate phases.

Randomness is intentionally repeatable on playback and rendering. Rebuild with another `--seed` for a new arrangement. The `seed` property on SUN CONTROLS is informational; editing it does not regenerate the scene.

Native drivers evaluate time from the frame number. Changing a speed slider at an existing frame **retimes that effect and may change its current pose immediately**. Setting a speed to zero returns it to its static phase; use Pause to hold the current pose. This differs from the web scene's accumulated clocks. Choose speed values before rendering a shot. Although Blender lets you keyframe custom properties, speed ramps are not integrated motion clocks in this version.

The 60-second timeline has eruption schedules covering 180 seconds of internal flare time, accommodating activity up to 3. Extending the timeline requires rebuilding for the new duration. Playback wraps, but the animation is **not a seamless loop**.

## Included output

- [Full HD still, frame 180](renders/preview_0180.png): 1920 × 1080, Cycles, 64 samples, denoised, 16-bit PNG.
- [Animation preview](renders/sun-preview.mp4): eight seconds, 960 × 540, 15 fps, Cycles at 32 samples, default controls. This compact preview samples every second scene frame; the scene itself is configured for 30 fps.
- [Build manifest](build_manifest.json): Blender version, seed, scene length, object/event counts, and initial controls.
- [Validation results](validation.json): independent-control checks and driver evaluation checks.
- [Development handoff](HANDOFF.md): architecture, decisions, limitations, and next-step context.

## Render your own shot

Set the desired controls, resolution, frame range, and render engine in Blender. **Ctrl + F12** renders the timeline to the configured PNG sequence under `blender/renders/frames/`. Rendering to individual images makes an interrupted long render recoverable. The default scene is 1920 × 1080 at 30 fps using Cycles with 64 samples and denoising.

On this machine, the builder selects the NVIDIA RTX 4080 SUPER through OptiX. If moved to a machine without a configured compatible GPU, select **CPU** in Render Properties or configure that machine's Cycles devices. EEVEE is also supported by the builder for quicker iteration, but its volume/transparency result should be reviewed separately; the supplied beauty still uses Cycles.

Encode a completed default 30 fps sequence with FFmpeg from the project root:

```powershell
ffmpeg -framerate 30 -start_number 1 -i 'blender/renders/frames/sun_%04d.png' -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart 'blender/renders/sun-final.mp4'
```

For very fine grain or dim fading plasma, increase Cycles samples if denoising shimmers. The low-resolution preview is for motion review; evaluate delivery quality at the intended output resolution and frame rate.

## Rebuild and verify

Run these commands from the repository root. The builder starts a **new, empty background scene** and overwrites `blender/solar_observatory.blend`, its embedded panel, and the manifest. Save a separate copy of any artistic edits before rebuilding. It does not preserve manual changes inside that generated file.

```powershell
$SolarBlender = 'C:\Program Files\Blender Foundation\Blender 5.2\blender.exe'
& $SolarBlender --background --factory-startup --python-exit-code 1 --python blender/scripts/build_sun.py -- --seconds 60 --seed 73491 --render --frame 180
& $SolarBlender --background blender/solar_observatory.blend --python-exit-code 1 --python blender/scripts/validate_sun.py
```

Builder options: `--seconds 10..1800`, `--seed INTEGER`, `--engine CYCLES|EEVEE`, `--render`, `--frame INTEGER`, and `--preview` (half-resolution still). Longer durations generate more event objects and increase file size and build time.

Regenerate the short preview without changing the saved scene:

```powershell
& $SolarBlender --background blender/solar_observatory.blend --python-exit-code 1 --python blender/scripts/render_preview.py
ffmpeg -framerate 15 -start_number 0 -i 'blender/renders/preview_frames/%04d.png' -frames:v 120 -c:v libx264 -crf 18 -pix_fmt yuv420p -movflags +faststart 'blender/renders/sun-preview.mp4'
```

Intermediate image sequences and logs stay inside `blender/renders/` and are ignored by the local `.gitignore`. The final `.blend`, still, video, scripts, and documentation are deliverables.

## Assets and visual direction

The existing three supplied images are copied into `references/` for future art direction. They are references only, not texture dependencies, and are not embedded into the material. You do not need to obtain anything else to use or develop this version.

Optional footage or close-up references showing a particular prominence's motion would help guide a future realism pass. The current effect is a procedural artistic model: it uses layered mesh plumes and curves, rather than a physically simulated magnetohydrodynamic or fluid system. Thin loops can still read as filaments, and detached particle trails from the web version have not been separately recreated. One orange-gold visual style is implemented.
