# Mercury — session handoff

Updated: 2026-09-08 for main-branch integration. This document records the first implemented Mercury scene and the user's latest intent. Read it before changing the scene or starting another server.

## Current status and user intent

The user requested a rotating Mercury in space, similar to the Earth and Moon and Sun ambience projects, using NASA's model if practical. We researched NASA's Mercury resources, inspected the downloadable GLB, and implemented a working Three.js scene with that original asset.

The first version is complete and available for visual review. The user may return to add elements to the background or otherwise change the scene. **No specific background addition, visual treatment, or next implementation has been chosen.** Preserve the current version as the starting point and discuss the new request when it arrives. Do not interpret possible background work as an instruction to add a nebula, spacecraft, Sun, or other object now.

The user also requested and received a copyable prompt for a separate Venus session. Venus work is separate from this Mercury implementation.

## Exact workspace and repository state

**Continue Mercury development from this folder in the main checkout:**

```text
C:\Projects\ContactEstablished\YouTube\YT-Ambience\Mercury
```

- Integration target: `main` in `C:\Projects\ContactEstablished\YouTube\YT-Ambience`, remote `origin` at `https://github.com/ContactEstablished/YT-Ambience.git`.
- On 2026-09-08 the user explicitly requested committing, merging, pushing, and removing Mercury's worktree. All Mercury-specific files were consolidated under `Mercury/`, including package/lock files, `.gitignore`, README, and this handoff. The repository root's existing Earth/Venus package and documentation are retained.
- Original development location (historical, not the continuation path): `C:\Projects\ContactEstablished\YouTube\.chorus\YT-Ambience\wt-fe9723e0`, branch `chorus/YT-Ambience/fe9723e0`, originally based on `0bde42a`. The user requested removal of that worktree after the push; do not depend on it being present.
- Use `git status`, `git log`, and `git worktree list` to verify the current integration state rather than relying on old worktree IDs or historical uncommitted-file lists.
- Earth and Moon's source used as a reference was in the main checkout's `Earth and Moon/`. The star-field module was copied into Mercury, so Mercury has no runtime dependency on the other checkout.
- The Sun preview runs from a separate worktree, `wt-21e886fd`.
- Mercury is now independently runnable with its own package. It does not replace the repository root's package. There is no public website deployment.

## Preview, commands, and runtime

**Mercury preview: http://127.0.0.1:5175/**

The original server was Node PID `57208`, serving the old worktree. After integration, run the preview from the main checkout's `Mercury/` folder. PIDs and browser tabs are temporary observations: verify ownership and the served content before stopping or reusing anything.

Other observed listeners: Sun on `5174`, Venus production preview on `5176`. The earlier Earth preview used `5173`, but no listener was observed there at handoff. Do not stop sibling previews to free a port.

From the repository root:

```powershell
cd Mercury
npm ci
npm run dev
```

- Node.js 22 or newer is the documented prerequisite.
- Dependencies are pinned: `three` **0.185.1**, `vite` **6.4.3**. A generated lockfile and installed `node_modules/` are present.
- Run all Mercury npm commands inside `Mercury/`; from the repository root, the equivalent is `npm --prefix Mercury run dev` (or `build` / `preview`). `npm run dev` serves the current Mercury folder on localhost port 5175 with `--strictPort`. Check for the existing server first; a port-in-use error is not a reason to kill an unidentified process.
- Background servers are launched with `Start-Process ... -WindowStyle Hidden`. Local `*.log` files are ignored by Git.
- `npm run build` writes `Mercury/dist/` and uses relative asset URLs (`--base ./`).
- `npm run preview` serves that build on 5175; dev and production preview cannot occupy that port simultaneously.
- `.gitignore` excludes `node_modules/`, `dist/`, and `*.log`.
- Serve the app through Vite or a static HTTP server, not `file://`. All imagery is local; clicking the NASA credit is an explicit external navigation.

The browser preview was left open in Chrome. The previously observed tab ID was `1557161960`; rediscover the matching URL rather than assuming this ID is still valid. Live speed/orientation/visibility may have been adjusted by the user. Do not reset the user's live view merely to inspect it.

## Files and responsibilities

| File | Responsibility |
| --- | --- |
| `Mercury/src/main.js` | Settings, renderer, camera, lighting, GLB loading and normalization, animation, input, resizing, loading/errors |
| `Mercury/src/stars.js` | Deterministic star positions, size/brightness variation, and twinkle shaders |
| `Mercury/index.html` | Fullscreen canvas, initially hidden interface, loading status, controls, NASA credit |
| `Mercury/style.css` | Fullscreen layout, warm neutral control styling, focus states, narrow-screen layout |
| `Mercury/public/models/mercury.glb` | Unmodified NASA model with embedded texture |
| `Mercury/package.json`, `Mercury/package-lock.json` | Reproducible dependencies and Mercury-specific run/build commands |
| `Mercury/README.md`, `Mercury/SESSION-HANDOFF.md` | Run instructions, attribution, and continuation context |

There is no React framework, backend, database, external scene engine, video exporter, or automated Mercury test suite. This is plain HTML/CSS/ES-module JavaScript using Three.js and Vite.

## NASA asset: already acquired and inspected

- Starting resource: https://science.nasa.gov/mercury/
- Model page: https://science.nasa.gov/resource/mercury-3d-model/
- Download: https://assets.science.nasa.gov/content/dam/science/psd/solar/2023/09/m/Mercury_1_4878.glb
- Credit: **NASA Visualization Technology Applications and Development (VTAD)**.
- Downloaded 2026-09-07; size **3,048,920 bytes** (about 2.91 MiB).
- SHA-256, rechecked at handoff: `0222fa976a5bb3ae3222eeddaaa7150656837a97c515f065eb855e0b1dd2ab94`.
- glTF 2.0, generated with the Khronos Blender exporter; one mesh, **2,034 vertices**, **3,072 triangles**.
- One embedded PNG color texture, **2048 × 1536**, named `mercury_diff.jpg` internally despite its PNG encoding.
- Matte nonmetallic material: metallic factor 0, roughness approximately 0.9. No separate normal/height map and no embedded animation.
- Preserve the mesh and its UV atlas together. The texture is not a standard 2:1 latitude/longitude map suitable for simply wrapping onto a replacement sphere.
- The app recenters the model using its bounding box and normalizes its largest dimension to diameter 2. It retains NASA's material and uses the renderer's maximum supported texture anisotropy.

The NASA page also offered USDZ, but only the GLB was needed and saved. Close-up detail remains limited by the supplied mesh and texture. No synthetic crater relief or generated imagery has been added.

## Current appearance and key settings

A centered gray cratered globe fills about 61% of the viewport's shorter dimension at default zoom. It rotates slowly against near-black space with small subdued stars. White sunlight comes from the upper left; the lower-right side falls into deep shadow. No atmosphere glow, clouds, halo, bloom, or planet emission is implemented.

Values in `SETTINGS` at the top of `main.js`:

| Setting | Current value / effect |
| --- | --- |
| `rotationSpeed` | 0.012 radians/second; one rotation in about 8 minutes 44 seconds at 1× |
| `exposure` | 1.08 |
| `sunlight` | Directional light intensity 3.2, neutral white |
| `fill` | Ambient light intensity 0.025, neutral white |
| `daylightFraction` | 0.8; nominally 80% of the projected globe illuminated |
| `halfFrame` | 1.65; orthographic framing adapted to aspect ratio |
| `initialOrientation` | Euler angles `[0.08, 0.65, -0.025]`, in radians |

Renderer: antialiasing, sRGB output, ACES filmic tone mapping, device pixel ratio capped at 2, clear color `#020305`. The orthographic camera is at `(0, 0, 8)`, looking down -Z, with clipping planes 0.1 and 500. The directional light position is `(-0.64, 0.48, 0.6)`. The camera and light do not orbit with the globe.

This is an artistic ambience composition; the speed is not Mercury's physical rotation rate. The user has not yet requested a separate lighting cycle, orbital motion, or a revised composition.

## Interaction and animation behavior

- Text and controls are hidden on load. **Ctrl + Shift + R** toggles them and intercepts the browser's hard-reload shortcut while this page has focus.
- Drag rotates the globe around world X/Y axes. Automatic rotation temporarily stops while pointers are held; sunlight and background stay fixed.
- Scroll, pinch, toolbar +/−, or focused-canvas +/− resize the globe. Zoom scales the globe only, clamped to 0.55–1.45. Toolbar zoom steps multiply/divide by 1.1.
- Focused-canvas arrow keys rotate the globe by 0.06 radians per press.
- The speed slider spans 0–20× in 0.05× steps; default 1×. Automatic rotation uses `globe.rotateY(...)` about its local Y axis.
- Pause stops both globe rotation and star twinkle. Setting speed to zero stops only the globe: twinkle still advances if the scene is not paused. Dragging also leaves twinkle running.
- Reset restores initial orientation, zoom 1, speed 1×, and rotation according to the current reduced-motion preference. It does not reset star twinkle time or hide the interface.
- Reduced motion starts rotation paused and freezes twinkle; Resume explicitly enables rotation. A change to the OS preference updates rotation state.
- Hidden tabs suspend animation advancement; returning does not catch up elapsed background time. Frame delta is capped at 0.1 seconds.
- Pointer cancellation, lost capture, window blur, and visibility changes clear held-pointer state.
- Preferences are in memory only; there is no persistence across reloads.
- Loading/error status lives outside the hidden interface. Controls stay disabled until initialization completes. WebGL context loss stops the loop and displays a reload message; automatic restoration is not implemented.

## Background implementation and future editing points

The background consists of the renderer's clear color and a `THREE.Points` object returned by `createStars()`. It is a plane of decorative points, not a star catalog or a spherical skybox.

- Seed `7021` produces 1,100 repeatable positions, initially X/Y in `[-0.5, 0.5)` and Z = -300.
- `resize()` scales the points' X/Y extents to the orthographic viewport. They remain behind Mercury and are not children of the rotating globe.
- Point sizes range from 1 to 2.5 times the capped device pixel ratio. Brightness ranges from 0.16 to 0.64, biased toward dim stars.
- Roughly 18% twinkle with amplitudes of 8–16% and independent 8–18-second periods.
- Shader color is `(0.88, 0.93, 1.0)` with soft circular alpha. Material is transparent, `depthWrite: false`, `depthTest: true`; Mercury occludes the stars.
- The returned interface is `{ points, material }`; `main.js` updates the `time` and `pixelRatio` uniforms.

For density, size, color, or twinkle adjustments, start in `stars.js`. For clear color, framing, or background attachment, start in `main.js`. A CSS body background alone will not replace the opaque WebGL background.

If the user requests an additional background object, add it to the scene or a separate background group so rotating/zooming Mercury does not move it unless that behavior is requested. Keep it within the camera clipping range. Extend the existing resize and animation paths as needed, and explicitly decide how its animation should respond to Pause, zero speed, and reduced motion. Transparent layers need a visual check for depth/occlusion and draw order. These are extension points, not a selected design.

## Verification completed and remaining limits

Completed during implementation:

- The initial `npm run build` passed and included the local GLB in the then-current `dist/mercury/models/` output. After folder consolidation the output is `Mercury/dist/models/`.
- Vite emitted a non-blocking warning for a JavaScript chunk around 612 kB. The initial outside-source-root output warning is no longer applicable with the self-contained `Mercury/dist/` layout.
- `git diff --check` passed for tracked edits, with a Windows line-ending notice.
- Chrome rendered the textured globe and star field; screenshots were inspected at desktop size and 390 × 844. The temporary viewport override was reset afterward.
- The hidden-interface shortcut, pause state, speed slider's 20× endpoint, zoom button, and reset were exercised. Reset visibly restored 1× and running state.
- Browser warning/error logs were empty after the checks.

Verification limits: touch pinch, every keyboard path, reduced-motion changes, context loss, and frame-by-frame pause/rotation timing were not exhaustively tested. A browser automation attempt to send the named key `plus` was unsupported by the tool; that is not evidence of an application failure. No formal Mercury tests or video capture/export were created.

At the original documentation handoff, the source files and asset hash were rechecked and the existing preview returned HTTP 200. No scene code or live user controls were changed for that handoff. The 2026-09-08 integration changes package location, build paths, and documentation; the scene code and NASA asset remain the same.

Integration validation on 2026-09-08: a clean `npm --prefix Mercury ci` and `npm --prefix Mercury run build` passed with the self-contained package. The output GLB retained the documented SHA-256. The resulting JavaScript/CSS output hashes matched the first version (`index-C5AQwSQr.js` / `index-FHSrmyYM.css`), confirming no scene-code change. Only the expected Three.js bundle-size warning remains.

## How to resume

1. Start in the main checkout's `Mercury/` folder above and read this handoff plus the current source. Check Git status to preserve any newer user changes.
2. Check whether http://127.0.0.1:5175/ is already serving Mercury. Reuse it if available; otherwise run `npm run dev` from `Mercury/`.
3. Inspect the current rendered scene before making visual edits. Ask only for the missing creative direction in the user's new request; the technical setup and NASA asset are already established.
4. Make the requested change, build, and visually check the affected behavior at desktop and narrow sizes. Keep sibling previews intact and update this handoff with new decisions and validation.

Suggested next-session opener:

> Read `C:\Projects\ContactEstablished\YouTube\YT-Ambience\Mercury\SESSION-HANDOFF.md` and continue the existing Mercury scene. I want to change: [describe the background or scene adjustment]. Preserve the existing model and controls unless the request requires changing them.
