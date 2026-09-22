# The Sun

For development history, architecture, debugging notes, and validation, start with [HANDOFF.md](HANDOFF.md). It was written in the original development worktree, so its workspace and Git-state notes describe that setup rather than this folder.

`The Sun/` is a separate Three.js scene: a centered, rotating 3D Sun with a golden-orange procedural surface, evolving dark magnetic regions, luminous magnetic arches, outward flare particles, and a gently breathing corona. This first **Golden plasma** style follows the supplied fiery Sun reference. The surface uses seamless object-space noise, so detail rotates with the sphere. Flares are attached to the sphere and correctly disappear behind it. This is an artistic ambience scene, not a scientific solar simulation.

From the repository root:

```sh
npm install
npm run dev:sun
```

Open the local URL Vite prints. `npm run build:sun` writes to `dist-sun/`; `npm run preview:sun` previews that build. The Sun needs WebGL 2 and makes no external asset requests.

As in Earth and Moon, the interface starts hidden. Press **Ctrl + Shift + R** with the page focused to show or hide it.

| Control | Behavior |
| --- | --- |
| Rotation, 0–20× | Independent spin speed, in 0.05× steps. At 1×, a revolution takes about 5 minutes 49 seconds. At 0×, the surface can still evolve. |
| Surface flow, 0–3× | Speed of the surface's mixing, flowing light/dark texture. At 0× the texture holds still while rotation and flares can continue. |
| Sunspots, 0–3× | Coverage and darkness of magnetic regions, independent of motion. At 0× these spots disappear; the underlying turbulent texture remains. |
| Flare activity, 0–3× | Number and frequency of smaller loops, particles, and large eruptions. At 0× all flares disappear and their clock holds; surface flow and corona continue independently. Higher values enable more event slots and advance flare lifecycles faster. |
| Flare intensity, 0–3× | Scales magnetic arches and outward particles. At 0× they disappear. |
| Corona glow, 0–2× | Adjusts the halo independently; 0× removes the corona (small bloom on the bright surface and flares remains). |
| Pause scene | Holds all automatic animation without changing slider values. |
| Stars | Toggles the warm star field. |
| − / + | Resizes the Sun while keeping it centered. |
| Reset view | Restores initial size and orientation; preserves the selected activity and speed. |

Drag or use arrow keys on the focused canvas to rotate. Scroll, pinch, or use +/− to resize. Settings survive hiding and revealing the interface; reload restores defaults. Reduced-motion preferences start the scene paused, with Resume available. Animation stops while the tab is hidden and resumes without a time jump. Rendering resolution is capped at 1.5 device pixels per CSS pixel to limit GPU load.

The Sun also produces broad, turbulent plasma fans and thick arching prominences with bright roots, twisting strands, and trailing fragments. At 1× flare activity, five independent event slots randomize the location, direction, width, reach, duration, and quiet gap of each eruption; 3× enables fifteen slots. The smaller-loop population similarly grows from 24 at 1× to 72 at 3×, with partial slots fading in between whole counts. Approximately 26% of large events are stronger eruptions, reaching 0.65–1.1 Sun radii before projection and lifetime scaling. Launches rise quickly and dissipate gradually. Each page load seeds a new sequence. Surface flow, flares, and corona use independent clocks; Pause holds all three. Flare intensity controls brightness independently of population and timing. Smaller loops have varied thickness and overlapping modulation periods.

The surface shaders and smaller flares live in `The Sun/src/sun.js`; broad plasma sheets and fragments in `The Sun/src/eruptions.js`; random event scheduling in `The Sun/src/eruption-events.js`; interaction and bloom in `The Sun/src/main.js`; the background in `The Sun/src/stars.js`; and independent animation timing in `The Sun/src/motion.js`. Further visual styles can be developed as additional materials in `sun.js`; this version implements one style.

```sh
node --test "The Sun/src/motion.test.js"
node --test "The Sun/src/eruption-events.test.js"
```

For the GPU regression check, open `/render-check.html` on the Sun's development server. It samples all pixels before and after bloom across 600 frames covering 60 seconds at 7.7× rotation, 1.7× surface flow, and 1.7× flare activity. The original flare shader generated non-finite pixels at frames 298 and 431 on the development GPU, contaminating the entire bloom image. Clamping the ribbon profile before fractional powers prevents that whole-screen blink. The check must finish with **PASS**, zero invalid channels, and no GPU errors. This diagnostic page is separate from the production build.

## Blender and Unreal editions

Two native renditions of the same Golden plasma Sun sit alongside the web scene. Each is self-contained and has its own README:

- [`blender/`](blender/README.md): a Blender 5.2 scene (`solar_observatory.blend`) with a control panel, build and validation scripts, and a preview render.
- [`unreal/`](unreal/README.md): an Unreal Engine 5.8 project (`SolarObservatory.uproject`) with a Sequencer film and a finished 1920 × 1080 render in `unreal/Renders/Sun-Unreal.mp4`.

The two editions' READMEs refer to their folders as `blender/` and `unreal/` at the repository root; they now live inside `The Sun/`. Their launch and render scripts resolve paths relative to their own folder, so they work unchanged. Caches, frame sequences, and logs are excluded by each folder's `.gitignore` and are regenerated by their build/render scripts.
