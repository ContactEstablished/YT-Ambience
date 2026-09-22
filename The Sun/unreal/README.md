# Solar Observatory — Unreal Engine edition

Start with **[Sun-Unreal.mp4](Renders/Sun-Unreal.mp4)**: a 12-second native Unreal render, **1920 × 1080 at 30 fps**. A [full-resolution still](Renders/Sun-Unreal.png) is included too.

Created with the locally installed **Unreal Engine 5.8.2**. This is a separate project; the existing Three.js and Blender versions were not changed. Everything authored for this version is inside `unreal/`.

## What this version does

The original Three.js solar math was translated into Unreal's Custom HLSL material nodes. The scene contains an actual 3D sphere, animated magnetic ribbons, broad layered ejections, detached plasma particles, a breathing corona, and warm stars. Unreal renders the image sequence through Movie Render Queue; FFmpeg encodes that sequence into the MP4.

The film uses the web scene's golden plasma palette, warped 3D noise, magnetic dark masks, limb darkening, randomized eruption parameters, soft additive flare shading, bright roots, and restrained bloom. The shader coordinates rotate with the Sun, and the ribbon/plume geometry rotates through native World Position Offset. The camera stays centered.

No texture downloads or additional assets are required. The supplied visual references and snapshots of the original Three.js shaders are retained under `References/`. These images are art references, not render textures.

Twinmotion was not needed. Its [Datasmith workflow](https://dev.epicgames.com/documentation/en-us/twinmotion/overview-of-the-twinmotion-to-unreal-engine-workflow) transfers Twinmotion scenes into Unreal. The custom solar shaders and animated plasma geometry are built directly in Unreal here.

## Open the editable project

1. Double-click **[Open Unreal Sun.cmd](Open%20Unreal%20Sun.cmd)**. It opens the project and its `SolarFilm` sequence.
2. In Sequencer, press **Space** or click Play to preview the animation. Enable the camera-cut lock if you want the viewport to follow the film camera.
3. In the Content Browser, open **Content → Solar → SolarControls**. Expand **Scalar Parameters** to adjust the effect values listed below. Save the asset to retain changes.

Alternatively, open **[SolarObservatory.uproject](SolarObservatory.uproject)** directly, then open `Content/Solar/SolarFilm` in Sequencer. The map is `Content/Solar/SolarScene`. Ordinary Play-in-Editor is not configured to start this film automatically; use Sequencer.

The viewport may look different from the finished Movie Render Queue output. The included MP4 is the quickest way to judge the final result. First-time opening may require shader compilation.

## Independent controls

| Parameter | Intended range | Delivered value | Behavior |
| --- | --- | --- | --- |
| RotationSpeed | 0–20 | 1 | Spin rate; one turn is approximately 349 seconds at 1. |
| SurfaceFlow | 0–3 | 1 | Speed of the flowing photosphere texture and magnetic-region evolution. |
| Sunspots | 0–3 | 1 | Coverage and strength of the dark magnetic masks. |
| FlareActivity | 0–3 | **1.5** | Loop population, eruption-slot participation, and flare clock speed. Slightly raised for this short showcase. |
| FlareIntensity | 0–3 | 1 | Brightness of ribbons, ejections, and particles. |
| CoronaGlow | 0–2 | 1 | Halo and breathing-corona strength. |
| SunSize | 0.55–1.35 | 1 | Size of the solar geometry within the camera composition. |
| Stars | 0 or 1 | 1 | Star visibility. |
| SolarTime | Seconds | Sequencer driven | Shared base time. `SolarFilm` animates this from 0 to 12; leave its track in control during playback. |

Material Parameter Collection fields do not enforce slider ranges; use the intended ranges above. Surface flow, flare activity, rotation, and corona motion use separate expressions derived from SolarTime. Pause Sequencer to hold everything. Setting a speed to zero gives its static phase; changing a speed at an existing frame retimes that effect immediately. It does not preserve an accumulated live clock as the web page does.

## Render again

The scene and sequence are already built. From PowerShell, run:

```powershell
.\unreal\Render-Sun.ps1
```

This launches a hidden Unreal rendering process, waits for Movie Render Queue to finish, and encodes `Renders/Sun-Unreal.mp4`. It overwrites that preview and the requested image frames. FFmpeg must be available on PATH; it is installed on the development machine.

`render_request.json` controls output resolution, frame range, spatial samples, and the frame subfolder. The delivered request is frames 0–359, 1920 × 1080, eight spatial samples, one temporal sample, 30 fps. The scene uses fixed manual exposure and disables motion blur to retain plasma detail.

For direct editor rendering, add `SolarFilm` to Movie Render Queue, select `SolarScene`, add the Deferred Rendering and PNG outputs, and set the desired resolution and sampling. The exact reproducible configuration lives in `Scripts/render_movie.py`.

## Rebuild from source

Rebuilding regenerates the authored `/Game/Solar` materials, level actors, controls, and sequence. Save any manual art changes in a separate project copy first.

```powershell
python .\unreal\Scripts\prepare_assets.py
.\unreal\Render-Sun.ps1 -Rebuild
```

The preparer uses the local shader snapshots under `References/ThreeJS`; it does not require the parent web project. It writes HLSL, OBJ source meshes, and seeded event descriptions. The Unreal builder imports the meshes, creates the native materials, and saves the project assets. Mesh imports are reused while their source file is older than the saved asset; regenerate sources to force imports after changing geometry.

## Files and practical limits

- `Content/Solar/`: native materials, meshes, controls, map, and sequence.
- `Shaders/`: editable HLSL bodies; the builder embeds them into materials, so the saved project has no runtime shader-file dependency.
- `Assets/`: mesh sources, event descriptions, manifest, and native validation report.
- `Renders/`: MP4, still, output report, and intermediate images/logs.
- [HANDOFF.md](HANDOFF.md): technical details and the fixes that made the build work.

This is one artistic golden-plasma style, using procedural mesh/shader effects rather than fluid or magnetohydrodynamic simulation. It is not a browser renderer. The 12-second shot is not a seamless loop, and identical settings reproduce the same seeded events. The schedule is generated over 60 seconds of internal flare time; longer shots require extending that schedule and the sequence, not just the render range. Fine particles remain an artistic approximation, with shader-generated random seeds rather than identical browser point-sprite sampling.

Native asset checks and full MP4/PNG validation reports are included. Desktop UI interaction was not automated during validation.
