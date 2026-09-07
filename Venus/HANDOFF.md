# Venus ambience — session handoff

Last updated: **2026-09-07**, integrated into `main`. This is the starting document for a new session continuing the Venus scene.

## Current state

A working, locally served Three.js Venus ambience scene is implemented in `Venus/`. It began as a direct adaptation of the project's Mercury scene. The user then supplied a detailed Venus image and asked for a closer visual match. The current version uses NASA's original sphere with a generated cloud texture inspired by that reference: fine swirling clouds, blue-gray regions, and cream/pale-gold bands.

The production build passed and the scene was inspected in Chrome at desktop and narrow sizes. The preview was left open with controls hidden, default framing, and 1× rotation. The user may return for visual changes; there is no specific outstanding change request or final visual sign-off. The user subsequently requested committing, merging into main, pushing, and removing the Venus worktree. This document describes the resulting repository layout; use Git to verify the current commit and remote state. No public website deployment is configured.

## Repository and related scenes

| Item | Location or value |
| --- | --- |
| Main checkout | `C:\Projects\ContactEstablished\YouTube\YT-Ambience` |
| Venus implementation, package, and docs | `Venus/` within that checkout |
| Remote | `https://github.com/ContactEstablished/YT-Ambience.git` |
| Integration target | `main` |
| Venus preview | http://127.0.0.1:5176/ |
| Venus build output | `Venus/dist/` |
| Environment | Windows, PowerShell; Node.js 22.14.0 and npm 11.12.1 used |

The original Venus worktree was `C:\Projects\ContactEstablished\YouTube\.chorus\YT-Ambience\wt-e95dc094`, on branch `chorus/YT-Ambience/e95dc094`, based on `0bde42a33282551de86d794ad207fa402fcbb159`. It was designated for removal after the merge and push. Do not use its old paths for assets or preview startup. All required source assets and references are now inside the repository's `Venus/` folder.

The Mercury implementation used as the starting point is in the separate worktree `C:\Projects\ContactEstablished\YouTube\.chorus\YT-Ambience\wt-fe9723e0`. The user requested that other planet scenes and previews remain separate and undisturbed. Do not stop unrelated Node processes. Sun uses 5174, Mercury 5175, and Earth conventionally uses 5173. Recheck current port ownership; no old PID is a durable identifier.

The root package retains Earth's existing scripts. Venus has its own `package.json`, lockfile, dependencies, and build directory. Root convenience commands `dev:venus`, `build:venus`, and `preview:venus` forward to the Venus package. For a fresh checkout install Venus dependencies explicitly with `npm --prefix Venus ci`.

## What happened and why

1. Read the Mercury reference's `README.md`, `package.json`, and all implementation files. Reused its Three.js scene setup, controls, layout, seeded stars, and timing.
2. Started NASA asset research at https://science.nasa.gov/venus/ and found separate cloud-covered Venus and Venus-surface resources. Downloaded and inspected the cloud model's GLB metadata and extracted texture before selecting it.
3. Built the first Venus version with that original NASA model and its soft cream/gold embedded cloud texture. Preserved Mercury's framing and upper-left sunlight; changed automatic rotation to retrograde at the same slow speed.
4. The user supplied `Venus_-_December_23_2016.png` and asked, “can we make Venus look more like this image?” The image shows much finer cloud structure and cooler blue-gray coloring with warm cream/gold areas.
5. Used the built-in imagegen tool to create a flat 2:1 cloud map inspired by the image. Integrated the generated map on NASA's existing mesh/UVs. Preserved the original NASA GLB unchanged on disk.
6. Added shader blending at the longitude wrap and polar tips. During browser review, a thin seam appeared when wrapping UVs with `fract()`. Removing `fract()` and using the original continuous `vMapUv` eliminated the visible line in the inspected rotated view. Do not reintroduce that derivative discontinuity.
7. Updated source credits to distinguish NASA's model from the artistic cloud texture, rebuilt production, and checked desktop/mobile rendering and controls.

The reference's lighting direction was not copied: upper-left illumination remains part of the Mercury-matching scene. Framing and the subdued star field also remain consistent with Mercury.

## Read these files next

| File | Purpose / where to make changes |
| --- | --- |
| [Venus README](README.md) | Run instructions and current behavior |
| [Venus/src/main.js](src/main.js) | `SETTINGS`, renderer/camera/lights, NASA model loading, motion, input, resize, loading/error handling |
| [Venus/src/clouds.js](src/clouds.js) | Current texture loading and material shader; longitude/polar blending |
| [Venus/src/stars.js](src/stars.js) | Mercury's seeded 1,100-star field and gentle twinkle |
| [Venus/index.html](index.html) | Initially hidden interface, accessible canvas, slider/buttons, credits, status |
| [Venus/style.css](style.css) | Fullscreen layout, responsive typography and toolbar |
| [Venus/ASSETS.md](ASSETS.md) | Exact sources, attribution, asset inspection and SHA-256 checksums |
| [Venus/VERIFICATION.md](VERIFICATION.md) | What was actually tested, with limitations |
| [Venus/references/cloud-texture-prompt.md](references/cloud-texture-prompt.md) | Exact imagegen prompt and generation method |

## Assets and provenance

- **NASA geometry:** `Venus/public/models/venus.glb`, from https://science.nasa.gov/resource/venus-3d-model/. Credit: NASA Visualization Technology Applications and Development (VTAD). Contains 3,062 vertices, 6,048 triangles, and an embedded cloud texture. This selected model depicts clouds, not radar terrain.
- **Current rendered clouds:** `Venus/public/textures/venus-clouds-reference.png`. Generated using the built-in imagegen tool from the user's reference. This is artistic visualization, not NASA observation data or a scientific reconstruction of unseen longitudes. It is stored locally and loaded at runtime; no image-generation service is involved during playback.
- **User reference, local copy:** `Venus/references/user-venus-2016.png`. Original path: `C:\Users\matth\Downloads\Venus_-_December_23_2016.png`. Original author/license was not supplied or independently verified; do not invent attribution from the filename. The reference is not bundled as a playback asset.
- **Original NASA texture, extracted for inspection:** `Venus/references/nasa-cloud-atlas.png`. It remains available for comparison or reverting to the softer first appearance.

NASA's standalone texture at https://science.nasa.gov/3d-resources/venus/ is explicitly stitched Magellan RADAR imagery. It was not chosen because the user wanted the visible cloud-covered appearance. The separate Venus-surface model was also not selected.

To return to the original NASA appearance, remove/bypass the `applyCloudAppearance()` call and its import in `main.js`; the GLB loader still supplies the original embedded map. Update documentation and credits if making that change.

## Behavior to preserve

- All interface text and controls hidden on load. **Ctrl + Shift + R** toggles the interface and intercepts the browser hard-reload shortcut while the page has focus. Loading and error status must remain visible when needed.
- Drag and canvas-focused arrow keys rotate the globe. Wheel, two-pointer pinch, +/− keys, and zoom buttons change globe scale; lighting/camera/stars remain fixed.
- Slider range **0–20×**, step **0.05×**, initial **1×**. Rotation speed is `-0.012` radians/second at 1×, about 8 minutes 44 seconds per turn. This is an ambience pace, not astronomical timing.
- Pause/resume stops/starts automatic rotation and star twinkle. Dragging temporarily holds automatic rotation. Reset restores default orientation, scale, speed, and motion-preference behavior.
- Reduced motion starts paused and suppresses twinkle. Resume may explicitly enable globe rotation. Hidden-tab handling prevents time advancement and a catch-up jump; pointer state is cleaned up on visibility changes/blur.
- Responsive orthographic framing and touch handling; clear loading and failure messages.

Current settings: exposure `1.08`, sunlight `3.2`, ambient fill `0.025`, daylight fraction `0.8`, half-frame `1.65`, initial orientation `[0.08, 0.65, -0.025]`, globe zoom bounds `0.55–1.45`, device pixel ratio capped at 2. Material: roughness 1, metallic 0, no bump/displacement or emission.

Cloud-map details: sRGB color space, `flipY = false` for glTF UVs, horizontal repeat, maximum supported anisotropy. The shader blends a 0.035-wide UV strip at the longitude seam and near each pole. It patches Three.js's `map_fragment` shader chunk, so review this integration if upgrading Three.js.

## Resume the local preview

Dependencies are pinned to Three.js `0.185.1` and Vite `6.4.3`; the Venus lockfile is included. `node_modules/`, `dist/`, and `*.log` are ignored at any depth.

From the repository root:

```powershell
npm --prefix Venus ci
npm run build:venus
npm run preview:venus
```

Alternatively, `cd Venus`, then use `npm ci`, `npm run build`, and `npm run preview` there. `npm run preview` from the repository root still belongs to Earth.

Venus preview uses loopback port 5176 with `--strictPort`. If it is already running, reuse it. It serves `Venus/dist/`, so **source edits require a Venus production build followed by a browser reload**. It is not a hot-reloading dev server.

For hot reload, stop only the verified Venus preview process and use `npm run dev:venus` from the root instead. Do not start both Venus servers on 5176. If another application owns the port, choose another available strict port and record it.

The migrated preview runs from the main checkout's `Venus/` directory, with logs `Venus/venus-preview.log` and `Venus/venus-preview-error.log`. Do not assume the tab or server survives a restart. Do not run preview from the deleted worktree.

## Verification and remaining limits

- Production build passed after the final rendering change. Vite emits non-blocking warnings for a >500 kB JS chunk in the original build configuration. The integrated Venus build now stays inside `Venus/dist/`.
- Initial version: browser checks exercised hidden/revealed controls, drag, wheel, arrow and +/− keys, zoom buttons, pause/resume, slider limits/step, and reset. Desktop and 390 × 844 views were inspected.
- Current texture revision: browser inspection covered desktop/mobile appearance, the expanded credits toolbar, accelerated rotation, pause, drag to another hemisphere, reset, and the seam fix. No captured console errors or warnings.
- Physical multitouch and OS reduced-motion emulation were **not** exercised. Those handlers and hidden-tab suspension were preserved and reviewed in source; do not present that as a completed device test.
- No automated test suite was added. The seam was visually checked in sampled orientations, not exhaustively at every angle/mip level. Inspect a full turn and poles if changing the map or UV treatment.
- Website work remains local; the source is integrated into Git main. No website hosting or publishing is configured.

## Suggested next-session workflow

1. Read this document and inspect the current files/Git status. Preserve any new uncommitted edits and check the current main/remote state.
2. Open/restart the local preview and inspect the actual current scene before changing it. Use the saved user reference when discussing visual changes.
3. Apply the user's new request. Appearance work usually belongs in `clouds.js`/the texture, lighting/framing in `main.js`, and interface work in HTML/CSS. Keep the other planet previews isolated.
4. Build, reload the production preview, inspect desktop and narrow views, and check controls/console as appropriate to the change. Reset temporary viewport overrides and leave the preview open if requested.
5. Update this handoff and the asset/verification notes when behavior, sources, port, or validation changes.

Suggested prompt to resume:

> Continue the Venus ambience scene in `C:\Projects\ContactEstablished\YouTube\YT-Ambience\Venus`. Read `Venus/HANDOFF.md` from the repository root first, then inspect the scene and local preview. Preserve any existing edits and do not modify or interrupt the other planet previews. My next requested change is: …
