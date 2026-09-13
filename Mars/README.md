# Mars — Ambience

A slowly rotating Mars with visibly enlarged Phobos and Deimos in the same quiet star field and upper-left lighting used by this project's Mercury and Venus scenes. All scene resources, code, dependencies, and build output live inside this folder.

## Run

Requires Node.js 22 or newer. From the repository root:

```sh
cd Mars
npm ci
npm run dev
```

Open http://127.0.0.1:5177/. Use the local server rather than opening `index.html` directly. Port 5177 is strict so another planet's server will not be replaced.

```sh
npm run build
npm run preview
```

Stop the dev server before starting preview on the same port. Production files go to `Mars/dist/`, with relative URLs that also work under a subdirectory. Three.js, the Draco decoder, and all textures/models are served locally; playback makes no external requests. Source attribution links open only when clicked.

From the repository root, `npm --prefix Mars run dev` and `npm --prefix Mars run build` also work.

## Controls

- **Ctrl + Shift + R** reveals or hides the controls. The X at the top right also closes them, including while the menu is scrolled. Settings occupy a separate right sidebar on wide screens and a compact panel above the planet viewport on narrow screens. Closing restores the full view.
- **Mars lighting — Static shadow:** choose 0–100% shadow coverage of Mars's visible disk. The default is 20%; 0% is fully lit and 100% shows the night side. An 8% texture-illumination floor keeps Mars and both moons readable even at full night. Coverage stays fixed while the planet rotates. The setting adjusts the sunlight direction, not material opacity.
- **Mars lighting — Day/night loop:** follows Earth's four-rotation sequence: daylight, nightfall, night, dawn. Day and night each hold for one full Mars rotation; transitions each take one rotation and ease smoothly. The phase and current shadow coverage appear in the controls. The saved static shadow returns when switching back to Static shadow.
- **Drag / arrow keys:** freely rotate the system's viewing orientation, with the camera and stars fixed. On load, reset, and location visits, Mars returns to its standard north/south orientation with north leaning 25° to the right. Automatic spin preserves that axis. Dragging temporarily holds automatic spin, orbits, and the lighting loop. Manual rotation does not advance the loop.
- **Scroll / pinch / + / − / zoom buttons:** zoom the camera from 0.15–30×. Camera zoom avoids clipping through an enlarged globe. The fixed star field does not zoom with the bodies.
- **Mars rotation speed:** 0–20×; one rotation at 1× takes about 8 minutes 44 seconds.
- **Moon orbit speed:** 0–20×; at 1× Phobos circles in 3 minutes and Deimos in 12 minutes. Each moon keeps the same local side toward Mars.
- **Moon scale & distance:** choose Illustrated (the original enlarged moons) or True size & distance. True scale uses approximate longest dimensions of 27 km / 15 km and mean orbital center distances of 9,375 km / 23,457 km, relative to a Mars radius of 3,390 km. It fits the complete system when switching, without restarting orbital phases. Motion remains accelerated in both modes.
- **Explore Mars:** the visible button opens the facts explorer without needing the settings shortcut. The **Facts, landings & statistics** setting opens the same explorer. Click a blinking square or a body for details, or use the Mars / Phobos / Deimos buttons for rotation, orbital speed, distances, Earth-hour days, Earth-day years, and temperature information.
- **Browse or search:** filter surface features, nine NASA landing sites, and three notable events. Search by mission, region, year, or mission detail; click a result to open its card. Landing cards include UTC dates, coordinates, mission descriptions, statistics, milestones, and source links. The list reaches locations even when markers are behind Mars or omitted to avoid overlap. **Close explorer** turns off the markers and cards. This is a curated catalog, not an exhaustive mission database.
- **Click / tap a moon:** show it centered in front of a centered, rotating Mars. The selected moon rotates in place at its illustrated viewing size; this presentation intentionally enlarges and repositions it, including when entering from True size & distance. The other moon continues its orbit. **Back to Mars** restores the previous overview zoom, selected scale mode, and the moon's continuing orbital phase. The camera stays centered on Mars. A fact card's Focus button and double-clicking a moon's fact square also open this view.
- **True-scale moon locators:** labeled sonar rings expand from each moon every five seconds, even when facts are off. Click a locator to center its moon. Locators display only moon names, including during occultation. Reduced motion uses steady rings. Locator graphics stay readable in screen pixels while the overview meshes retain their true relative sizes and distances.
- **Show location on Mars:** smoothly restore the standard 25°-tilted north/south orientation and rotate the selected longitude to the front, then zoom in and hold Mars's rotation and day/night cycle for 15 visible seconds. Latitude remains naturally north or south of the tilted equator. A bright ring, location name, and countdown identify the selected point; nearby overlapping markers yield to it. The settings and explorer panels move aside; **Browse locations** reopens the list. Moons continue orbiting. Mars resumes afterward only if animation is enabled and its speed is above zero; a manually paused scene stays paused. Reduced motion skips the flight. Drag and zoom remain available during the hold, and switching locations starts a fresh visit. Markers follow the mapped surface and identify historical landing positions rather than current rover positions. **Escape** closes a fact card.
- **Pause animation:** freezes Mars, both moons, the lighting loop, and star twinkle. Manual view and static-shadow adjustments remain available.
- **Reset view:** restores orientation, zoom, initial moon phases, star phase, both speeds to 1×, Static shadow at 20%, and Illustrated moon scale. It exits moon focus and turns facts off. Animation resumes unless reduced motion is requested.

The loop follows **Mars rotation speed**, independently of moon orbit speed. A full loop takes about 34 minutes 54 seconds at 1×, or 1 minute 45 seconds at 20×. Setting Mars speed to zero holds the lighting phase. Enabling the loop starts at daylight, including when paused; resuming continues from that phase. The shared sunlight illuminates both moons consistently with Mars throughout the cycle.

System reduced motion starts everything paused, disables twinkle, and makes fact squares steady. Resume can explicitly enable spin, orbits, and the lighting loop while twinkle remains off. Hidden tabs stop advancing animation time. Reload restores defaults; settings are not persisted.

## Composition

Mars has scene radius 1. In Illustrated mode, Phobos and Deimos have display diameters of 0.25 and 0.16, at orbital radii of 1.6 and 2.3. True scale uses the sourced size and mean-distance ratios in the overview, with simplified circular equatorial orbits. Moons can be smaller than a pixel there; sonar locators reveal their positions without enlarging the meshes. Centered moon focus displays the selected moon at its illustrated diameter in front of Mars, while preserving orbital time for return. This is not a date-specific astronomical simulation.

The moon meshes retain their irregular shapes and embedded 1024 × 1024 UV textures. Their fixed planet-facing side is geometric, without claiming a scientifically mapped longitude. Normal depth testing provides occultations and transits; cast eclipse shadows are not simulated. Mars now uses an 8192 × 4096 texture derived from the USGS Viking colorized mosaic, with a 4096 × 2048 alternative for devices with smaller texture limits. It is a historical mosaic with baked relief shading, not a live or calibrated true-color view. Extreme magnification is still limited by image resolution; no synthetic surface detail is generated.

The night shader preserves at least 8% of each surface's linear texture color before tone mapping. This is an artistic visibility floor, not 8% sunlit area or a temperature model. Adjust `SETTINGS.nightVisibility` to change it.

Direct sunlight eases out between 99% and 100% shadow and returns smoothly at dawn. This removes the tiny bright highlights along the night-side silhouette while retaining the 8% terrain visibility, in both static and looping lighting modes.

`src/main.js` contains rendering and centered-focus controls. `src/moon-locators.js` projects the true-scale sonar beacons. `src/lighting.js` and `src/orbits.js` contain lighting and geometry math. `src/explorer.js` implements picking, marker projection, and fact cards; `src/facts.js` stores the curated content. `src/stars.js` is copied from Mercury, originally from Earth and Moon. See [ASSETS.md](ASSETS.md) and [FACTS-SOURCES.md](FACTS-SOURCES.md) for provenance and data conventions.

## Verification

```sh
npm test
npx playwright install chromium
npm run test:browser
```

Browser checks build the production page, serve it temporarily at `http://127.0.0.1:5178/Mars/`, and run headless Chromium. They write screenshots and `results.json` to `verification/`, then close their server. They do not control your normal browser. Port 5178 must be available. Playwright is a development dependency only.

See [VERIFICATION.md](VERIFICATION.md) for the latest checks and limitations. The build's Three.js bundle-size warning is non-blocking.
