# YT-Ambience — project handoff

Prepared September 7, 2026. This document captures the work in this conversation, with emphasis on **The Sun**, its accepted appearance, implementation, and important debugging history. It describes a working implementation, not a proposed plan. Read it before changing the scene, then verify the current files and Git state because development may have continued elsewhere.

## 1. Current status and user intent

This repository contains standalone browser-based space ambience scenes using plain HTML, CSS, JavaScript ES modules, Three.js, and Vite. There is no application framework, backend, account system, or shared scene-selection page.

- **Earth and Moon** was already present in the user's main project. Its interaction conventions informed the Sun controls.
- **The Sun** was created during this conversation. It is a centered, rotating 3D Sun with a turbulent golden-orange surface, evolving dark magnetic regions, small magnetic loops, larger random plasma ejections, a breathing corona, and decorative stars.
- The user approved the visual direction, requested stronger and less repetitive flares, and then requested finer control over individual effects. Those requests are implemented.
- The last implementation request was to separate surface mixing, sunspot amount, and flare activity. That separation is complete. The user subsequently said, “This looks great,” and requested this handoff.

The desired result is attractive, living space ambience suitable for the user's YouTube project. It is an artistic rendering inspired by supplied images, not a physical solar simulation. The user expressed interest in multiple styles eventually, but **only the first style, Golden plasma, is implemented**. There is no pending request to redesign it or add a second style.

## 2. Read this before moving or committing files

### Workspace snapshot at handoff

The work in this conversation resides here:

```text
C:\Projects\ContactEstablished\YouTube\.chorus\YT-Ambience\wt-21e886fd
branch: chorus/YT-Ambience/21e886fd
HEAD:   0bde42a (Initial commit)
```

The user's main checkout is separate:

```text
C:\Projects\ContactEstablished\YouTube\YT-Ambience
branch: main
HEAD:   6b67f48 (First Draft), as observed September 7, 2026
```

This task's worktree initially contained only the original minimal README. The Earth and Moon scene, package files, and richer README existed as uncommitted files in the main checkout. They were copied into this worktree so the Sun could use the established setup and both scenes could build here. During development, an additional Earth night-land brightness adjustment appeared in the main folder; that change and its README description were carried into this worktree too.

At handoff, `main` was clean and had advanced to `6b67f48`. Its `The Sun` folder was still empty. **The Sun implementation in this worktree has not been committed, merged, or copied back into main by this conversation.** Multiple other worktrees also exist. Do not assume their files are identical.

Before writing this handoff, this worktree's status was:

```text
 M README.md
?? .gitignore
?? "Earth and Moon/"
?? "The Sun/"
?? package-lock.json
?? package.json
```

This documentation task additionally creates `HANDOFF.md`, archives the Sun references, and adds a README link. The many untracked Earth/package files reflect the initially sparse worktree, not a request to replace newer Earth work. Before integrating, compare against current main and preserve changes from other tasks. Avoid blindly copying the entire old worktree over main. No commit or integration is performed as part of this handoff request.

Useful orientation commands:

```powershell
Get-Location
git status --short --branch
git worktree list
git log -3 --oneline
```

## 3. Run and build

The package is still named `yt-ambience-earth`; that historical name does not mean the Sun is absent. Dependencies are pinned in the package and lockfile:

| Component | Version / requirement |
| --- | --- |
| Node.js | README requires 22 or newer; this session used 22.14.0 |
| Three.js | 0.185.1 |
| Vite | 6.4.3 |
| Browser | WebGL 2 support |

Run commands from the repository/worktree root, not from `The Sun/src`:

```powershell
npm ci
npm run dev:sun
```

Use the URL printed by Vite. The Sun preview used `http://127.0.0.1:5174/` during this session because another server occupied 5173. The port and running process are session details, not permanent configuration. If restarting on a specific port is useful, this direct invocation avoids the npm argument-forwarding issue seen in PowerShell:

```powershell
node node_modules/vite/bin/vite.js "The Sun" --host 127.0.0.1 --port 5174
```

| Scene | Development | Build | Build preview | Output |
| --- | --- | --- | --- | --- |
| Sun | `npm run dev:sun` | `npm run build:sun` | `npm run preview:sun` | `dist-sun/` |
| Earth and Moon | `npm run dev` | `npm run build` | `npm run preview` | `dist/` |

Serve through Vite or a static web server; do not open the source HTML with `file://`. The Sun has no external texture or asset requests. Its reference images are documentation assets, not runtime textures.

Builds pass with two existing Vite warnings: the output folder is outside the selected scene root and will not be emptied automatically, and the bundled Three.js code exceeds the default 500 kB chunk warning threshold. These are warnings, not the cause of the previously observed blink. `node_modules/`, `dist/`, `dist-sun/`, and `*.log` are ignored.

## 4. Visual direction and archived references

The initial request was a centered 3D Sun that rotates, develops dark spots, shoots flares, and feels alive and almost “breathing.” The first supplied image established the orange/gold palette, detailed luminous surface, dark magnetic regions, and star field.

The user then supplied close-up ejection references and specifically asked for some flares to be **much thicker and sometimes more violent**, with randomness to avoid an obviously repeating effect. The references show white-yellow roots, broad plasma sheets, curling strands, and long red-orange trails. Thin, regular hoops alone did not meet that request.

Original user-supplied images have been copied from temporary clipboard storage into the repository for future context:

| Reference | Purpose |
| --- | --- |
| [Golden Sun](The%20Sun/references/01-golden-sun.png) | Initial full-Sun composition and palette |
| [Bright-root ejection](The%20Sun/references/02-bright-root-ejection.png) | Thick, energetic flare emerging from a very bright root |
| [Extended prominence](The%20Sun/references/03-extended-prominence.png) | Broad arcing and trailing material beyond the limb |

The second and third images in the user's later ejection message were byte-identical, so only one copy of that reference is archived. These images describe the target; they are not screenshots of the current implementation.

Preserve the current general appearance unless asked otherwise. In particular, the user liked the surface and wanted more granular controls, not a replacement look. A surface flow adjustment should not silently alter flare behavior again.

## 5. Current controls and their exact semantics

The interface starts **hidden** to provide a clean ambience view. With the page focused, **Ctrl + Shift + R** reveals or hides it. The page intercepts that shortcut instead of letting the browser hard-reload. This matches Earth and Moon.

All sliders default to `1.00×`, with steps of `0.05`. Settings survive hiding/revealing the interface but are **not persisted across reloads**. Values observed during experimentation are not agreed presets or defaults; the user adjusted the live preview repeatedly.

| Label / DOM ID | Range | Behavior |
| --- | --- | --- |
| Rotation / `rotation-speed` | 0–20× | Automatic spin at `0.018 * rotation` radians/second. At 1× a revolution takes about 349 seconds. Zero stops automatic spin only. |
| Surface flow / `surface-flow` | 0–3× | Rate of the mixing/flowing procedural surface. Zero freezes surface evolution while rotation, flares, and corona can continue. This is a speed control, not a fluid-physics amplitude control. |
| Sunspots / `sunspots` | 0–3× | Coverage and strength of dark magnetic regions. Zero removes the explicit spot masks; it does not remove all dark detail from the turbulent base texture. Spot evolution follows surface flow. |
| Flare activity / `flare-activity` | 0–3× | Population and frequency of small loops, particles, and broad eruptions. Higher values enable more slots and advance their lifecycles faster. Zero hides all flares and holds the flare clock. |
| Flare intensity / `flares` | 0–3× | Brightness multiplier for loops, particles, and eruption sheets. Zero makes them invisible, but their scheduling clock can continue if flare activity is nonzero. |
| Corona glow / `corona` | 0–2× | Brightness of the halo. Zero removes that halo mesh's visible contribution; bloom from bright surface/flaring pixels can still remain. |

Other controls:

- **Pause scene** holds all automatic clocks and spin without resetting selected values. It does not lock manual rotation, zoom, or slider changes.
- **Stars** toggles the static warm background stars.
- **− / +**, scroll, pinch, or keyboard `+`/`-` resize the Sun, centered in the frame. Zoom is clamped to 0.55–1.35.
- Drag or focused-canvas arrow keys rotate the Sun. Dragging holds automatic spin but does not pause surface evolution or flares.
- **Reset view** restores initial orientation and zoom, retaining the control values, clocks, and eruption schedule.
- Reduced-motion preference starts the scene paused, with Resume available; preference changes also update pause state.
- Hidden browser tabs stop the render loop. Returning resets the frame timestamp to avoid a jump.

The toolbar now contains six sliders and scrolls vertically if viewport height is too small. Titles on the three granular controls explain their meanings.

## 6. File map

| File | Responsibility |
| --- | --- |
| [README.md](README.md) | User-facing run instructions, scene descriptions, controls, Earth imagery attribution |
| [The Sun/index.html](The%20Sun/index.html) | Canvas, loading/error status, initially hidden controls, labels and slider ranges |
| [The Sun/style.css](The%20Sun/style.css) | Fullscreen layout, warm translucent toolbar, responsive styling |
| [The Sun/src/main.js](The%20Sun/src/main.js) | Renderer, fixed camera, postprocessing, interaction, settings, resize and render loops |
| [The Sun/src/sun.js](The%20Sun/src/sun.js) | Procedural surface, corona, small loops, background flare particles, assembly of eruption system |
| [The Sun/src/eruptions.js](The%20Sun/src/eruptions.js) | Broad plasma sheets, large arches, trailing fragments, per-event transforms/uniforms |
| [The Sun/src/eruption-events.js](The%20Sun/src/eruption-events.js) | Pure seeded random event scheduling, event envelopes, slot participation |
| [The Sun/src/motion.js](The%20Sun/src/motion.js) | Pure independent-clock advancement and spin calculation |
| [The Sun/src/stars.js](The%20Sun/src/stars.js) | 2,600 seeded static warm stars |
| [The Sun/src/motion.test.js](The%20Sun/src/motion.test.js) | Clock independence, pause, dragging, interrupted-frame checks |
| [The Sun/src/eruption-events.test.js](The%20Sun/src/eruption-events.test.js) | Population, event shape/timing, randomness and reproducibility checks |
| [The Sun/render-check.html](The%20Sun/render-check.html) and [src/render-check.js](The%20Sun/src/render-check.js) | Actual GPU regression sweep, separate from normal ambience page and production entry |
| `The Sun/references/` | Archived user-supplied visual references |

## 7. How the rendering works

### Composition and postprocessing

`main.js` creates a WebGL renderer with `antialias: false`, a device-pixel-ratio cap of 1.5, a very dark warm background (`0x050201`), ACES filmic tone mapping, and exposure 1.02.

The camera is orthographic at Z = 8. On resize, its half-height is `1.72 / min(1, aspect)`, so the Sun remains centered and fits narrow viewports. A composition group contains the rotating Sun group and the camera-facing corona. The initial Sun Euler rotation is `(0.15, 0.4, -0.12)` radians. Zoom scales the composition; manual and automatic rotation affect the Sun group, not the halo plane or stars.

The pass chain is:

```text
RenderPass(scene, camera)
  -> UnrealBloomPass(strength 0.23, radius 0.45, threshold 1.35)
  -> OutputPass (tone mapping and output color conversion)
```

Early versions had too much bloom and washed the surface into a pale white-yellow disk. The current bloom threshold, strength, and shader palette were tuned to retain the orange/red texture and dark regions. Raising bloom indiscriminately can erase that detail.

### Surface

The Sun is a unit-radius `SphereGeometry(1, 128, 96)` with an emissive custom shader; it does not depend on scene lighting or photographic Sun textures. Seamless 3D value noise and five-octave fractal noise are evaluated in object space. Therefore detail rotates with the sphere instead of sliding across the screen.

Domain warping produces large-scale flow, with higher-frequency noise for granulation and filaments. Heat is mapped through dark red, orange, and bright gold. Broader magnetic noise fields create the sunspot masks. `sunspots` adjusts mask thresholds and strength without changing time. Limb darkening gives the self-luminous sphere some volume. A small surface brightness pulse follows surface time.

### Corona

A 4.8-by-4.8 plane sits at Z = -1.15 behind the opaque sphere. Its shader uses radial falloff, noisy rays/wisps, and a slow sinusoidal variation in falloff width. Additive blending creates the warm glow. This is a camera-facing procedural halo, not a simulated gaseous volume. It uses its own clock, so changing surface flow or flare activity does not stop the corona.

### Smaller loops and particles

There are 72 prebuilt 3D loop ribbons anchored around the sphere. Their thickness varies, and two overlapping modulation periods control their visibility rather than a single uniform cycle. The current population multiplier is:

```glsl
clamp(flareActivity * 24.0 - loopIndex, 0.0, 1.0)
```

Thus 1× selects 24 loops and 3× selects 72, with partial participation between whole counts. These are eligible loops, not a promise that all are simultaneously bright or visible; their phase and the sphere's occlusion still matter.

The small-flare particle buffer contains 5,400 particles allocated across those anchors, using the same population rule. Motion is calculated in the vertex shader. These elements are attached to the rotating Sun, with depth testing against the surface and no transparent depth writes.

### Larger random eruptions

`createEruptions()` allocates 15 event slots. At 1× activity, five participate; at 2×, ten; at 3×, fifteen. `eruptionParticipation()` smoothly weights the final partial slot. The underlying schedule advances on the flare clock even for currently inactive slots; changing the slider does not recreate the entire scene.

Each live Sun receives a fresh random seed. Event sequences are deterministic for a given seed, allowing repeatable tests. Events randomize location, orientation, shape, length, width, bend, twist, texture seed, power, duration, and subsequent quiet gap.

| Event parameter | Current range / behavior |
| --- | --- |
| Shape | Approximately 40% arches, otherwise jets |
| Stronger-event chance | 26% |
| Duration | 11–28 flare-clock seconds |
| Gap before next event in a slot | 5–29 flare-clock seconds |
| Ordinary length | 0.25–0.60 Sun radii |
| Stronger length | 0.65–1.10 Sun radii |
| Ordinary width parameter | 0.055–0.14 |
| Stronger width parameter | 0.15–0.28 |

Lengths and widths are parameters before projection, shape deformation, and growth; they are not guaranteed on-screen distances. At activity above 1×, durations and gaps occupy less real time because the flare clock runs faster. Two initial events are already underway at startup, avoiding an entirely empty opening.

Each broad plume is three intersecting, warped sheets sharing a geometry with 64 longitudinal and 16 transverse subdivisions. A shader creates a curling arch or a bending, widening fan, with advected noise for strands, broken edges, and bright roots. These are inexpensive layered meshes that suggest volume, not ray-marched volumetric fluid simulation. Each event also has 360 seeded trailing particles, visible for jets. Their brightness and size were reduced after inspection so the effect reads as plasma rather than glitter/fireworks.

The lifecycle rises rapidly, remains active, and then fades gradually. Meshes and buffers are reused; scheduling changes parameters rather than rebuilding geometry every frame. Shader-deformed eruption meshes and particles disable frustum culling because CPU-side placeholder geometry does not describe their actual bounds.

## 8. Independent clocks: preserve this separation

The original implementation had one combined surface activity setting. The user explicitly rejected that coupling because they wanted to adjust the surface's wave-like mixing without changing flares, and wanted independent dark-spot control.

`advanceMotion()` now accepts clock values plus elapsed time and returns:

```text
surfaceTime += delta * settings.surfaceFlow
flareTime   += delta * settings.flareActivity
coronaTime  += delta
rotationStep = delta * 0.018 * settings.rotation
```

`delta` is clamped to 0–0.05 seconds and is zero when paused. Dragging makes only `rotationStep` zero. As a tradeoff, persistently slow rendering slows simulation time instead of making large jumps.

In `main.js`, returned clocks are written to shared uniforms, other slider uniforms are updated, `sun.update()` advances eruption scheduling, and then the composer renders.

Important naming detail: the surface clock is still called **`uniforms.time`** in `sun.js`. Materials for small flares and eruptions alias their shader's `time` uniform to **`uniforms.flareTime`**. The corona aliases its shader's `time` to **`uniforms.coronaTime`**. Do not mistake the repeated GLSL name `time` for shared timing across all effects.

`sunspots` controls appearance only. `flareStrength` controls brightness only. A future preset system should set the independent values, not bring back the old single combined `activity` field.

## 9. The whole-screen blink: reproduced and fixed

This was the main rendering defect encountered. The user saw the whole screen flash or “hiccup” every few seconds. It was not simply the intended breathing pulse, and disabling animation or removing bloom was not necessary.

The small ribbon fragment shader originally calculated:

```glsl
float edge = abs(vUv.y - .5) * 2.0;
float thread = pow(1.0 - edge, 2.5);
```

Interpolation/rounding could put a fragment infinitesimally beyond the ribbon's UV boundary. A fractional power of a negative base produced NaN. A single invalid flare pixel then contaminated the bloom chain across the whole frame.

The actual GPU sweep reproduced this in the earlier implementation at frames 298 and 431: six invalid scene channels total, expanding to 1,036,800 invalid channels after bloom across those two frames. That explains why a tiny edge problem looked like a global flash.

The fix clamps the base before either power:

```glsl
float profile = max(1.0 - edge, 0.0);
float thread = pow(profile, 2.5);
float core = pow(profile, 12.0);
```

The same 600-frame sweep then passed with zero invalid channels. Later eruption shaders also bound fractional-power inputs and guard square roots. **Preserve these protections when editing shaders.** The old exact failure frame numbers describe the earlier geometry/schedule, not a permanent expectation for every future version or GPU.

An earlier startup failure also came from using `active`, a reserved GLSL word, as a variable name. It was renamed to `activeRegion`. A Vite build alone does not compile GLSL on the user's GPU, so browser validation is required after shader changes.

## 10. Validation and how to repeat it

### Last verified implementation results

- Sun production build: passed.
- Sun Node tests: **11 passed** after the granular-controls change.
- GPU sweep: **600 frames, zero invalid scene channels, zero invalid bloom channels, no invalid frames** after that change.
- Browser checks: expanded controls render, sunspots can be removed or increased, flares can be disabled while the surface continues, and independent minimum/maximum settings are selectable.
- Earlier in this conversation, Earth and Moon built successfully and its four existing lighting tests passed after carrying forward the night-land brightness adjustment.

These are session validation results, not a claim of exhaustive cross-browser, mobile, hardware, or hours-long playback testing. This handoff-only task does not repeat rendering/build tests because production code is unchanged.

Run the focused tests:

```powershell
node --test "The Sun/src/motion.test.js" "The Sun/src/eruption-events.test.js"
npm run build:sun
```

If changing shared setup or Earth files, also use:

```powershell
node --test "Earth and Moon/src/earth-lighting.test.js"
npm run build
```

### GPU regression page

With the Sun dev server running, open `/render-check.html` on that server. It creates an independent test scene at 480×270, seeded with `73491`, sampling a 60-second timeline in 0.1-second increments. It sets rotation to 7.7×, surface flow and flare activity to 1.7×, and advances the corona separately. It inspects half-float channels before and after bloom for NaN/infinity, checks GPU readback errors, and reports shader compile errors.

Completion should read `PASS`, `frames: 600`, and zero invalid channels. `maxBrightnessStep` is diagnostic only; it has no pass/fail threshold because real eruptions intentionally change brightness. This low-resolution deterministic test catches the prior defect but does not certify every possible seed or resolution.

`/render-check.html?still=25.8` renders one deterministic sample at 960×540 for visual inspection. A still-page `PASS` is a **one-frame result**, not the full sweep. Other finite times from 0 to 3600 are accepted. Scheduling/population changes can alter which eruption appears at an old saved time.

The diagnostic page omits the normal interface and star field. It is not a production scene or performance benchmark; GPU readback is intentionally expensive. Do not add this readback to the ambience render loop. It is not included in the normal Vite production entry.

## 11. Earth and Moon context

Earth and Moon is a sibling scene with its own entry point and assets. In this worktree it includes an interactive, textured Earth, clouds, atmosphere, night-city lights, a large procedural cratered Moon foreground, decorative stars, independent Earth/Moon rotation sliders, and optional Earth day/night cycling. See the README and Earth-specific source for full implementation details and imagery attribution.

The day/night cycle progresses with automatic Earth rotation through daylight, nightfall, full night, and dawn. Its pure helper and tests live in `Earth and Moon/src/earth-lighting.js` and `.test.js`. Earth night-land brightness in this worktree includes the two successive 5% boosts, giving 10.25% cumulatively; oceans are unaffected by that particular adjustment.

Do not refactor or replace this scene just because its files show as untracked relative to this worktree's old initial commit. Main and other worktrees may contain newer Earth work; compare before integrating.

## 12. Boundaries, limitations, and sensible continuation

No functional request remains unfinished from this conversation. The user is happy with the scene and asked to preserve context for later.

Current boundaries:

- One Sun style only; no style switcher or preset library.
- No saving settings, shareable scene parameters, screenshot export, recording UI, or video export pipeline.
- No production deployment was performed.
- Random events are visually varied but generated from seeded pseudo-random sequences, not a physical magnetic-field model.
- Surface flow changes temporal rate; it is not an independent wave-amplitude slider.
- Sunspots are procedural masks, not individually tracked physical spots.
- Corona is a plane, broad plumes use intersecting sheets, and particles approximate ejected material.
- High flare activity enables more geometry and can increase GPU cost. Large zoom/ejection combinations may extend beyond the viewport. No adaptive quality system is implemented.
- There is no automatic recovery after a lost WebGL context; the visible error asks for reload.

Potential later work, only if requested, includes alternate visual styles, saved presets, independent surface-flow amplitude, quality/performance controls, and capture/export support. These are possibilities, not commitments or an active roadmap.

For the next session:

1. Establish the correct worktree and inspect current main before editing or integrating anything.
2. Read the current README, this handoff, and the relevant files from the map above.
3. Run the Sun and use Ctrl + Shift + R to inspect controls. Do not assume a blank interface means it failed to load.
4. Keep surface, flare, and corona clocks separate and preserve bounded shader math.
5. For shader changes, inspect the actual browser rendering and run the GPU sweep in addition to building.
6. If the user is adjusting their live preview, test in a separate tab instead of repeatedly changing their settings or reloading their view.
7. Preserve the accepted appearance and make the user's next requested adjustment without an unsolicited redesign.
