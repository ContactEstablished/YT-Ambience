# YT-Ambience — Venus

A cloud-covered Venus ambience scene, adapted directly from the Mercury implementation in the original Mercury worktree (`wt-fe9723e0/Mercury/`). Implementation: `Venus/`.

**Returning in a new session? Start with [HANDOFF.md](HANDOFF.md)** for project history, current state, asset provenance, implementation guidance, and verification limits.

## Run

Requires Node.js 22 or newer. From the repository root, enter `Venus/` first:

```sh
cd Venus
npm ci
npm run build
npm run preview
```

Open http://127.0.0.1:5176/. This strict, loopback-only port is separate from Earth (5173), Sun (5174), and Mercury (5175). The production build is in `Venus/dist/` with relative asset URLs. The first-review preview serves that build. For development, stop only the Venus preview and use `npm run dev` on the same port. Three.js and its GLTF loader produce a non-blocking Vite bundle-size warning.

## Appearance and controls

- Text and controls start hidden. **Ctrl + Shift + R** toggles them while the page has focus. Loading and error messages remain visible when needed.
- Drag or focus the canvas and use arrow keys to rotate. Scroll, pinch, +/− keys, or the zoom buttons change the globe size while the camera, lighting, and stars stay fixed.
- The rotation-speed slider spans **0–20×**, in 0.05× steps. At 1×, one turn takes about 8 minutes 44 seconds, matching Mercury's pace but rotating retrograde. This is an ambience composition, not physical planetary timing.
- Pause/Resume controls automatic rotation and star twinkle. Dragging temporarily holds automatic rotation. Reset restores initial orientation, zoom, 1× speed, and the motion preference defaults.
- Reduced motion starts rotation paused and disables star twinkle; Resume explicitly enables rotation. Hidden tabs stop advancing animation and resume without a time jump.

`Venus/src/main.js` retains Mercury's orthographic framing, initial orientation, upper-left white sunlight, faint night-side fill, dark background, and zoom bounds. `Venus/src/stars.js` and `Venus/style.css` reuse Mercury's seeded 1,100-star field and responsive controls. NASA's sphere now uses a reference-inspired blue-gray, cream, and pale-gold cloud texture with fine swirling detail, applied by `Venus/src/clouds.js`. The fully rough, nonmetallic material has no terrain bump map or emission. Runtime blending softens the longitude seam and polar tips.

The detailed cloud artwork was generated with the built-in imagegen tool from the user's supplied `Venus_-_December_23_2016.png` reference. It is an artistic interpretation, not NASA observation data. NASA's original model and embedded soft cloud texture remain stored unmodified. Sources, inspection details, asset checksum, and the generation prompt are in [ASSETS.md](ASSETS.md) and [references/cloud-texture-prompt.md](references/cloud-texture-prompt.md).
