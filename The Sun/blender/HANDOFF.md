# Blender Sun — implementation handoff

Prepared September 8, 2026. Read this alongside [README.md](README.md), the scripts, and the parent project's [original handoff](../HANDOFF.md). This document describes the Blender edition only.

## User intent and scope

The user approved the existing Three.js Sun and asked to retain it while exploring Blender 5.2 for more vibrant, attractive output. Preserve the separate controls for surface mixing, sunspot coverage, flare population/frequency, and flare brightness. Large eruptions should vary and occasionally become much wider and stronger. Keep the Sun centered, rotating, and alive, with gentle corona breathing.

All new scene files, scripts, copied references, generated images, and documents were placed in the root `blender/` folder. No Three.js implementation was changed for this task. The root worktree already had extensive uncommitted files from earlier work; do not assume those are Blender changes or reset them.

This deliverable is a native Blender scene, not a replacement HTML renderer. Standard Blender navigation, timeline playback, custom properties, and an optional sidebar provide the controls. Browser embedding, a live local control server, and automatic web-to-Blender conversion were not implemented.

## Working deliverable

- `solar_observatory.blend`: self-contained native scene, saved at frame 180, 60 seconds/1800 frames, 30 fps.
- `Open Sun.cmd` / `Open-Sun.ps1`: open Blender with the optional sidebar registered for that session.
- `scripts/build_sun.py`: deterministic builder; uses a new factory-startup process and overwrites the generated scene.
- `scripts/sun_controls.py`: lightweight Solar panel and Reset View operator, also embedded as a Blender Text block.
- `scripts/render_preview.py`: renders 120 half-resolution preview frames without saving changes to the scene.
- `scripts/validate_sun.py`: independent-control, native-driver, dependency, and sidebar-registration checks.
- `scripts/probe_api.py`: small record of local API probing used during initial implementation.
- `build_manifest.json`, `validation.json`, `renders/preview_settings.json`: generated machine-readable provenance.
- `renders/preview_0180.png`, `renders/sun-preview.mp4`: still and short motion preview.

No external textures, third-party add-ons, simulations, frame-change handlers, or custom Python driver namespace are needed to render the saved file. Native simple-expression drivers execute after a fresh reopen without automatic script execution being enabled. The optional UI is separate and requires registration when Blender restarts.

## Scene organization

| Collection | Implementation |
| --- | --- |
| 00 · Camera & controls | SUN CONTROLS empty, Solar rotation parent, orthographic camera. |
| 01 · Photosphere | Smooth unit sphere, 192 segments × 128 rings; fully procedural emissive shader. |
| 02 · Corona volume | Radius-1.55 sphere containing emissive procedural volume. |
| 03 · Magnetic loops | 72 independently phased curve objects, three strands each. Activity 1 enables 24. |
| 04 · Random eruptions | 77 scheduled events for the default seed/duration, each with an empty and a three-sheet mesh. |
| 05 · Star field | 1,400 soft disk quads combined into one mesh. |

The default build contains 232 scene objects and 845 native drivers. Counts are implementation details, not fixed interfaces; see the generated manifest/validation after rebuilding.

All solar geometry descends from **Solar rotation**, which receives the size driver and the Y-axis spin driver. The camera at `(0, 0, 8)` looks down local −Z, uses orthographic scale 6.1, and frames the Sun centrally with room for eruptions. Stars sit behind the Sun and do not inherit its rotation or scale.

## Surface and corona

The surface shader uses object coordinates for a seamless material. A slowly changing 4D noise warps the coordinates before a scale-24 noise and scale-140 fine noise create the granulation. Their weighted mixture feeds an orange/gold temperature palette. A separate scale-4.5 magnetic noise produces dark-region masks, with thresholds and strength controlled by Sunspots. Surface flow independently drives all four noise W phases. There are no UV seam textures to download.

The corona is actual volume emission, with exponential radial falloff, a smooth outer fade, spatial noise, and a small sinusoidal strength variation. Its clock is independent of the surface and flare settings. The first volume had a visible outer boundary; a squared smooth radial cutoff removes that hard ring. Density is zero; appearance comes from emission, not smoke scattering.

Initial AgX output looked pale/pink. The selected setup uses Standard color management, no look, exposure −0.8, stronger orange/gold emissive ramps, and restrained compositor Fog Glow. This is a deliberate artistic choice. Changing view transform, exposure, emission power, or glow together can wash out the surface and erase the dark regions; review the supplied still when adjusting them.

## Flare system

Small loops are native poly curves with three slightly irregular strands, randomized orientation/height/span, and animated emission. The geometry itself is static relative to the rotating Sun. Population fades with activity; both viewport and render visibility disable inactive loops.

Broad eruptions use 15 potential slots. At activity 1, five slots are enabled; at 3, all 15 are enabled. Event schedules cover `seconds × 3` of internal flare time. The default seed produces 77 total scheduled events, most hidden at any one frame. Two slots begin with events already underway so the initial scene is not empty.

For each event, random construction chooses an arch or jet, location, duration (11–28 internal seconds), gap (5–29), width, length, bend, twist, and phase. Roughly 26% draw from a stronger range: reach 0.65–1.1 Sun radii and width 0.15–0.28, versus reach 0.25–0.6 and width 0.055–0.14. These are model-space pre-projection parameters, not guaranteed on-screen silhouettes.

Each plume contains three crossing warped sheets, each 49 × 13 vertices. UV-driven turbulent emission mixes with transparency. Bright roots, softer edges, jet tip tapering, and two-root treatment for arches help the sheets read as plasma. A native driver scales the plume's vertical growth; an event envelope smoothly rises over the first 12% of its lifetime and fades over the final 52%. Hide drivers act at fully faded endpoints. There is no periodic full-screen clearing or exposure pulse.

The earlier web project had a serious bloom blink caused by fractional powers of negative UV-edge values producing NaNs. The Blender plume edge is clamped before its fractional power as well. Keep that constraint when translating or revising shader math. Cycles sample noise/denoising variation is a different possible artifact; assess it separately from deterministic shader discontinuities.

## Animation semantics and limitations

Native driver clocks use `(frame - 1) / 30` multiplied by the associated speed property. This provides deterministic scrubbing/rendering and avoids runtime handlers, but speed changes retime existing animation. Speed zero selects the initial phase, not the currently displayed phase. Pause holds the current frame. Do not claim that slider changes preserve the same accumulated phase as the web scene.

The fps is embedded as 30 in driver expressions. Changing the scene's output fps alone changes playback speed. Rebuild/update the timing expressions if supporting a different native timebase; exporting an image sequence at another playback rate is also a conscious retiming operation.

Other practical boundaries:

- The scene is finite and does not make a seamless loop. Rebuild for longer shots; extending only `frame_end` eventually exhausts the eruption schedule.
- A changed seed property does not regenerate geometry; pass a new `--seed` to the builder.
- Existing flares use sheets and curves, not fluid simulation. Small loops may look wire-like; denser broken filament shading is a possible art refinement.
- Detached particle trails from the Three.js version are not yet a separate Blender feature.
- Material Preview/EEVEE can differ from the Cycles reference. Real-time 30 fps playback is not guaranteed.
- Reset View restores camera view and Sun size, retaining the current timeline frame; it does not reset the animation's rotation angle to frame 1.
- No browser settings persistence/reduced-motion media-query behavior is relevant to this native UI. Saving the `.blend` persists selected controls.

## Blender 5.2 API findings

The locally installed executable reports **5.2.1 LTS**, build `9e2066aef7ef` (August 25, 2026). The script was executed against that installation, not assumed compatible from an earlier release.

- The EEVEE engine identifier is `BLENDER_EEVEE`.
- Scene compositing is assigned through `scene.compositing_node_group`. Create a CompositorNodeTree, expose an Image output socket through its interface, and connect a NodeGroupOutput.
- The Glare node uses input sockets for Type, Quality, Threshold, Strength, and Size. The builder sets Type to `Fog Glow`; old `glare_type` property assumptions fail here.
- Transparent flare materials use `surface_render_method = 'DITHERED'`.
- `World.use_nodes` and `Material.use_nodes` still work but produce deprecation notices for Blender 6.0; update the builder when targeting 6.x.
- This machine uses an NVIDIA RTX 4080 SUPER with OptiX for Cycles. The builder chooses CPU when it finds no OptiX device. Review device setup when moving to another machine; the saved scene is configured for GPU.

Useful official references: [Blender 5.2 rendering manual](https://docs.blender.org/manual/en/5.2/render/index.html), [Blender 5.2 Python API](https://docs.blender.org/api/5.2/), and [5.0 Python API changes](https://developer.blender.org/docs/release_notes/5.0/python_api/) for the EEVEE identifier migration. Local API probes and actual renders were the decisive compatibility checks.

## Validation performed

The generated scene was reopened in a fresh background Blender process and rendered successfully with `autoexec_fail = False`. A full-HD beauty still was reviewed for color, dark-region visibility, flare roots, and the corona edge. The eight-second preview uses the same default controls at lower resolution/sample count.

The encoded H.264 preview was verified as 960 × 540, 15 fps, 120 frames, eight seconds, and decoded without errors. Across its 120 source images, the largest adjacent-frame change in global mean RGB brightness was approximately 0.243%; no global brightness dropout was detected by that check. See `renders/preview_continuity.json`. This measurement does not establish absence of local flicker or denoising shimmer.

The automated validation passes 4,626 assertions, including 4,225 driver validity evaluations across frames 1, 180, 500, 1200, and 1800. It verifies static surface phases with continuing flares, unaffected surface clocks when flare activity changes, all 72 loops at maximum activity, complete flare hiding at zero activity/intensity, zero magnetic masks, zero corona emission, star visibility, uniform size, static rotation, finite event state, no unpacked external images, and repeatable sidebar registration. These checks evaluate Blender data and dependencies; they do not automate or visually inspect the desktop GUI.

Run `validate_sun.py` after changing controls, drivers, materials, or visibility. Render representative frames after changing art parameters. For larger structural changes, update this handoff and rebuild the manifest/preview so the scene and documentation remain consistent.

## Reasonable future work

The next useful step is user art feedback on the native Blender output. Candidate refinements include more ragged and volumetric plume silhouettes, detached ejecta, less uniform small-loop filaments, a seamless ambience loop, or an integrated clock system if smooth live speed changes matter. These are future options, not features delivered by this first version. Preserve the user's granular controls while exploring them.
