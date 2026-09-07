# Earth and Moon — session handoff

## Current task status

The latest request removes the decorative coastal lights: the user felt they looked too intentionally dotted and preferred the previous appearance. The coastal texture generator and shader contribution have been removed, restoring the enhanced geographic city-light map alone. Current land/ocean brightness is preserved. Do not reintroduce decorative coastline dots. The user prefers small, iterative visual adjustments.

## Project and preview

- Workspace: `C:/Projects/ContactEstablished/YouTube/YT-Ambience`.
- Plain HTML/CSS/Three.js app in `Earth and Moon/`; root npm scripts use Vite.
- `npm run dev` starts the local preview, normally http://127.0.0.1:5173/. Check whether the existing server is still running before starting another.
- `npm run build` produces `dist/`. Build has a non-blocking Three.js bundle-size warning.
- Timing checks: `node --test "Earth and Moon/src/earth-lighting.test.js"`.
- Work is not committed; existing additions and README modifications are intentional.

## Accepted visual direction

- Small rotating photographic Earth above a large slowly rotating cratered lunar foreground.
- Fixed lunar silhouette/horizon, sloping upward toward the right; ground rotates through stationary lighting.
- User calls the lunar region nearer Earth in the composition the **far side**, and the lower-right foreground the **near side**. These are compositional labels, not astronomical definitions.
- Moon is neutral gray, with rough regolith, fine dark speckles, irregular crater rims, and varied cavity shading. Do not reintroduce the brown tint or broadly darken all craters.
- Far side is brightly lit; light falls off toward an almost-black lower-right near side. User particularly likes this contrast.
- Subdued stars of varied brightness; a minority gently twinkle.
- Controls and text are hidden on load. **Ctrl + Shift + R** reveals/hides them.
- Independent Earth and Moon speed sliders: **0–20×**, 0.05× increments. Pause stops both rotations; reset restores orientation and restarts the lighting cycle.

## Earth lighting modes

- **Default** preserves roughly 80% daylight with a shadow tilted toward the lower right, aligned with the Moon's gradient. Alignment accounts for viewport aspect ratio.
- **Day–night cycle**: one automatic rotation each of full daylight, gradual nightfall, full night, and gradual dawn, then repeat. Dawn was added for a smooth loop and explained to the user.
- Cycle counts actual automatic Earth rotation. Earth speed changes timing; zero speed, pause, hidden tab, or dragging holds progress. Manual orientation changes do not advance stages.
- At 1× each phase lasts about 349 seconds; at 20× about 17.5 seconds.
- Full night has faint blue-gray terrain and warm geographically mapped city lights. Faint/whiter settlements are enhanced from the existing texture, masked to land.
- Latest tuning: land-only faint terrain multiplier is **1.1025**. City-light calculation remains `pow(cycleCities, 0.65) * 9.5`. Default mode is unaffected by these cycle-only changes.
- Selecting the cycle or resetting starts daylight again; reloading defaults to Default lighting.

## Files

- `Earth and Moon/src/main.js`: scene, Earth materials, city lights, UI, animation, lighting integration. Night terrain adjustment is in `surface.onBeforeCompile`.
- `Earth and Moon/src/earth-lighting.js`: pure four-stage cycle and lighting direction calculations.
- `Earth and Moon/src/earth-lighting.test.js`: phase duration, continuity, speed/rotation coupling, and Default alignment tests.
- `Earth and Moon/src/moon.js`: deterministic seamless crater terrain, neutral material, and composition-locked lighting gradient. Exports shared `LUNAR_SHADOW_DIRECTION`.
- `Earth and Moon/src/stars.js`: procedural star field and gentle twinkling.
- `Earth and Moon/index.html`, `style.css`: hidden UI and presentation.
- `README.md`: run instructions, asset attribution, and current behavior.

## Browser verification notes

The prior local Chrome preview tab was `1557161856` in browser `1`; verify availability before reuse. Browser screenshots can briefly show the previous rendered frame even when the accessibility state has already updated. For night QA, run the cycle at 20× and pause during “Night · Rotation 3 of 4”; restore prior speeds afterward. The user may adjust the live controls during work, so respect newer observed choices. Last observed user Moon speed was 17.65×; this is live state, not a saved default.
