# YT-Ambience — Mercury

A rotating Mercury globe in a subdued star field, built with Three.js and NASA's locally stored GLB model. The scene, package files, documentation, and assets are self-contained in `Mercury/`. Other planet previews run separately.

For continuation context, implementation details, and future background editing points, read [SESSION-HANDOFF.md](SESSION-HANDOFF.md).

## Run

Requires Node.js 22 or newer. From the repository root:

```sh
cd Mercury
npm ci
npm run dev
```

Open http://127.0.0.1:5175. Use the local server rather than opening `index.html` directly. The strict port keeps Mercury separate from the Earth and Moon preview on 5173 and the Sun preview on 5174.

```sh
npm run build
npm run preview
```

The build is written to `Mercury/dist/` with relative asset URLs. Run these commands from `Mercury/`. Alternatively, from the repository root use `npm --prefix Mercury run dev`, `npm --prefix Mercury run build`, or `npm --prefix Mercury run preview`. Stop the dev server before starting the production preview on the same port. The model and its texture are bundled locally; no external imagery requests are required during playback. Vite may report a non-blocking bundle-size warning for Three.js and its GLTF loader.

## Controls and appearance

- Controls are hidden on load. **Ctrl + Shift + R** reveals or hides them, overriding the browser hard-reload shortcut while this page has focus.
- Drag or use arrow keys with the canvas focused to rotate Mercury. Scroll, pinch, press +/−, or use the zoom buttons to change its size. The camera, lighting, and star field stay fixed.
- Rotation speed ranges from 0–20× in 0.05× steps. One turn at 1× takes about 8 minutes 44 seconds. Pause holds the rotation and star twinkle; dragging temporarily holds automatic rotation.
- Reset restores the initial orientation, zoom, and 1× speed, and resumes rotation unless reduced motion is requested. Reload also restores defaults.
- The scene starts paused under the system's reduced-motion preference, and star twinkle stays off. Rotation can be enabled explicitly with Resume. Hidden tabs stop advancing animation.

`Mercury/src/main.js` contains the `SETTINGS` values for rotation, framing, exposure, and lighting. Upper-left white sunlight illuminates roughly 80% of the projected globe with a faint neutral fill on the night side. There is no atmosphere glow, cloud layer, or emission. Timing and lighting are an ambience composition, not a physical-time simulation.

NASA's mesh and its UV atlas are retained together. The texture is 2048 × 1536; it is not a standard equirectangular map for an arbitrary sphere. No separate height or normal map is included. Very close views are limited by the original texture and geometry resolution. `Mercury/src/stars.js` reuses the existing Earth and Moon scene's seeded star-field implementation, with 1,100 stars and gentle twinkling on a minority of them.

## NASA asset credit

Model: **NASA Visualization Technology Applications and Development (VTAD)**.

- Resource: https://science.nasa.gov/resource/mercury-3d-model/
- Original file: https://assets.science.nasa.gov/content/dam/science/psd/solar/2023/09/m/Mercury_1_4878.glb
- Local file: `Mercury/public/models/mercury.glb`, downloaded 2026-09-07, unmodified.
- SHA-256: `0222fa976a5bb3ae3222eeddaaa7150656837a97c515f065eb855e0b1dd2ab94`.
- Contents: 2,034 vertices, 3,072 triangles, one embedded color texture, matte nonmetallic material, no embedded animation.

Three.js and Vite are MIT-licensed; their notices are included in their installed packages.
