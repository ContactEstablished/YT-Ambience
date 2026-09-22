# Unreal Sun — development handoff

Prepared September 8, 2026. This folder is an independent Unreal interpretation of the accepted Three.js Sun. The user disliked the Blender result and asked for a short MP4 from Unreal with the web scene's styling and techniques. Preserve the Three.js and Blender projects. All task-authored files are under `unreal/`; Unreal also manages its normal machine-wide engine caches.

## Delivered state

`Renders/Sun-Unreal.mp4` is a 12-second H.264 movie, 1920 × 1080, 30 fps, with 360 native Movie Render Queue frames. `Renders/Sun-Unreal.png` is frame 180. See `Renders/render_result.json` for the successful render request and `Renders/output_validation.json` for sequence/video checks.

The engine installation reports Unreal **5.8.2**, changelist **56702186**, compatible changelist 55116800. The Windows engine is at `C:\Program Files\Epic Games\UE_5.8`. Rendering uses DirectX 11 / SM5 on the installed NVIDIA GPU. No C++ build toolchain, external Unreal bridge, Twinmotion scene, downloaded texture, or Blender renderer is involved.

Twinmotion 2026.1 is present on the machine, but its scene-import workflow does not contribute to the procedural Sun. The project enables PythonScriptPlugin, EditorScriptingUtilities, and MovieRenderPipeline. It uses native Custom HLSL materials and mesh effects rather than Niagara because this provides a close, deterministic port of the existing web techniques.

## Architecture

The map contains **six StaticMeshActors and one CameraActor**:

1. Photosphere: Unreal's built-in sphere, scaled to radius 100 cm. An opaque unlit material uses seamless 3D domain-warped noise, fine granulation, filament detail, dark magnetic masks, active regions, limb darkening, and a small breathing multiplier.
2. Magnetic loops: one imported mesh with 72 ribbon strips. Native WPO reconstructs each loop from a normal, tangent, height, width, phase, and rate. A soft cross-section and flowing hot core replace the solid wire-like curves of the Blender attempt.
3. Broad ejections: one imported mesh containing three crossing sheets per event, each 65 × 17 vertices. WPO computes growth, twist, bend, ripple, and local-to-solar orientation. Pixel shading adds ragged billows, veins, bright roots, jet tip taper, and a smooth life envelope.
4. Plasma particles: 5,400 small-loop particles plus 360 detached-fragment quads for each of 34 precomputed events, totaling 17,640 billboard quads. Shader-generated seeds drive the motion. The sprite math follows the web implementation, adapted to mesh quads.
5. Corona: camera-facing additive plane behind the opaque sphere. Its radial falloff, directional noisy wisps, and gentle breathing come from the Three.js halo shader.
6. Stars: 1,800 soft additive disk quads, combined into one mesh.

The camera is at `(700, 0, 0)`, looking toward −X, with a 50-degree horizontal field of view and 16:9 aspect ratio. Solar shader coordinates follow the web convention `(x, y, z)`, with z toward the camera, and map to Unreal `(z, x, y) × 100`. Static OBJ coordinates are authored in Unreal axes; Interchange preserves them.

The sphere's shader coordinates rotate through the inverse of the same transform used to move loops, plumes, and particles. A geometrically symmetric sphere does not need an actor transform animation to appear to spin; its material features supply visible rotation. The geometry remains three dimensional and the opaque sphere occludes far-side effects.

## How the port stays close to Three.js

`References/ThreeJS/` preserves `sun.js`, `eruptions.js`, and `eruption-events.js` from the web project. `Scripts/prepare_assets.py` translates the original surface/corona/plume GLSL into HLSL, converting types and functions while retaining the original procedural formulas. Shared functions are packaged in a local `SolarMath` struct, which is valid inside Unreal Custom node functions.

The script reproduces the loop-anchor LCG with seed 73491. Broad eruptions use seed 29173 and the same event distributions: varied start times, durations, quiet gaps, orientations, widths, lengths, bends, twists, and about 26% stronger eruptions. The schedule is precomputed for 60 internal seconds and contains 34 events. It is repeatable, unlike a fresh random seed on each web-page load.

FlareActivity is 1.5 for the delivered clip to show more development within twelve seconds; the other effect multipliers are 1. At this activity, 36 loop slots and 7.5 broad-event slots participate. The movie's later frames show a stronger broad ejection growing near the left limb. An event may be occluded by the sphere depending on its randomized anchor and the current rotation.

All materials reference `SolarControls`, a native Material Parameter Collection. The `SolarFilm` Level Sequence animates only SolarTime from 0 to 12. Display rate is 30 fps and tick resolution is 30,000 ticks/second; the final time key is at tick 360,000. SurfaceFlow, RotationSpeed, FlareActivity, Sunspots, FlareIntensity, CoronaGlow, SunSize, and Stars remain independent material parameters. See README for ranges and time-retiming behavior.

## Rendering decisions

The scene uses unlit emission and additive effects, so dynamic global illumination, reflections, static lighting, Nanite, and virtual shadow maps are unnecessary. Final rendering uses Unreal's deferred raster pipeline with eight spatial samples and one temporal sample, fixed manual exposure, bloom intensity 0.23 / threshold 1.35, no motion blur, and no vignette. This keeps the granular detail readable and prevents exposure adaptation from creating global breathing or flashes.

Movie Render Queue writes PNGs to `Renders/Frames/Sun_0000.png` through `Sun_0359.png`. FFmpeg encodes H.264, CRF 17, slow preset, yuv420p, fast-start metadata. The PNGs retain the source images for re-encoding. The delivered shot is not a seamless loop and has no audio.

`Render-Sun.ps1` runs the hidden rendering process and waits for the completion report before encoding. `Scripts/Run-Unreal.ps1` returns a process ID; it does not wait itself. `Scripts/render_movie.py` uses MoviePipelineQueueSubsystem and MoviePipelinePIEExecutor, with global references and completion/error delegates. The saved `.uproject` contains native assets; scripts are needed to rebuild or automate rendering, not to evaluate material animation in Sequencer.

## Important integration fixes

- **Asynchronous Python lifetime:** `unreal.EditorPythonScripting.set_keep_python_script_alive(True)` is essential when launching MRQ with `-ExecutePythonScript`. Without it, Unreal closes as soon as the top-level script returns and cancels the render. Only the completion callback should quit the editor.
- **5.8 struct initialization:** CollectionScalarParameter and CustomInput did not accept keyword constructor arguments in the installed build. Create the struct, then assign editor properties.
- **Material node wiring:** ComponentMask's unnamed input must be connected using an empty input name. Passing `Input` silently failed and produced a default material. The builder now asserts input connections.
- **MRQ console variables:** use `add_or_update_console_variable`; the old writable `console_variables` property is not exposed by this version.
- **UV precision:** loop/event/particle IDs share a UV component with local ribbon coordinates. Imported half-precision UVs destroy this information, especially at particle IDs in the thousands. All authored meshes have full-precision UVs enabled. Do not revert this optimization setting.
- **Import cost:** identical placeholder quads caused excessive overlapping-vertex work. Tiny offsets give each placeholder grid distinct source positions. WPO replaces these positions, so the offsets have no visible effect. This greatly shortened import time.
- **Rebuild cleanup:** `new_level` does not overwrite an existing map. The builder loads its own map and removes its generated mesh/camera/sequence actors before rebuilding, preventing duplicate additive layers. It does not operate on other project levels.
- **Finite shader math:** fractional powers retain nonnegative bases from the web blink fix. Keep the clamps around ribbon-edge profiles and plume terms; NaN values can contaminate bloom across the frame.

Useful primary sources are Epic's installed MoviePipelineEditorExample.py and engine headers, plus the [Movie Render Queue Python API](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/MoviePipelineQueueSubsystem) and [Twinmotion-to-Unreal workflow](https://dev.epicgames.com/documentation/en-us/twinmotion/overview-of-the-twinmotion-to-unreal-engine-workflow). Local execution against the installed 5.8.2 build resolved API details.

## Verification and future editing

Representative first, middle, and last native frames were inspected. The final render log contains no shader compilation failures or rendering errors. The MP4 was probed for resolution/frame rate/frame count/duration and decoded successfully. `Scripts/verify_output.py` checks the complete PNG numbering, unique frames, dimensions, and adjacent global brightness changes; it does not claim to detect all local temporal aliasing.

`Scripts/validate_scene.py` performs read-only native checks on the saved actor count, camera count, material output links, unlit shading, full-precision mesh UVs, defaults, and sequence range. Its report is `Assets/validation.json`. Desktop GUI operation is not covered by these checks.

For art changes, edit the HLSL or preparer, regenerate sources as appropriate, and run `Render-Sun.ps1 -Rebuild`. The builder overwrites generated assets and initial controls, so preserve manual artistic edits separately. For longer movies, extend the event generation horizon and sequence duration/timing keys together. Merely expanding the MRQ frame range does not create more animation.

Potential future refinements should be guided by user feedback on this MP4: alternate color treatments, denser prominence detail, volumetric plasma experiments, a seamless loop, or easier dedicated controls. No separate custom control widget, browser renderer, or physical solar simulation has been implemented in this version.
