# Verification — 2026-09-13

## Passed

- The requested home view now uses a 25° right-leaning north axis on load, reset, and location visits. Browser checks compare projected surface positions for the initial view, manual rotation, reset, Olympus Mons, southern Hellas Planitia, and northern Phoenix. The 15-second hold and resumed spin preserve that tilted axis. Current screenshots are `tilted-hellas.png`, `tilted-phoenix.png`, and `location-highlight.png`; older `north-up-*` captures document the previous vertical-axis view.
- Verified plain moon names/tooltips without an occultation suffix. Verified the top-right settings X after scrolling, desktop sidebar separation, and full viewport restoration on close. A focused follow-up checks non-overlapping desktop, portrait, and landscape settings layouts against the final build; screenshots use the `*-side-settings.png` names.
- `npm test`: nine numerical tests covering static shadow percentages, smooth four-phase lighting, full-night sunlight suppression and dawn recovery, rotation-linked cycle timing, complete moon orbits, planet/moon separation, synchronous facing, true-scale dimensions/distances and phase continuity, latitude/longitude conversion, and full-orbit framing at five viewport aspect ratios.
- `npm run build`: production output generated successfully with relative asset URLs.
- Production build and `node tests/browser-check.mjs`: all fourteen browser check groups passed using Playwright 1.62.1 and headless Chromium 151.0.7922.34. The test loaded the production output under `/Mars/`, with external HTTP requests blocked for the local-resource check.
- Verified the visible Explore Mars launcher, synchronized settings toggle, all nine expanded landing cards, search by region/year, empty results, event filtering, body statistics, close, and reset. On mobile, opened the launcher and a searched Perseverance card through touch input. Desktop and mobile landing-detail screenshots are in `verification/`.
- Verified a smooth location flight followed by a full 15-second Mars rotation hold, continued moon orbits, automatic rotation resumption, and preservation of a manually paused scene. The selected event takes priority over a landing marker at the same coordinates. Its bright ring and named countdown remain after the card closes; reset clears the highlight. See `verification/location-highlight.png` and `verification/mobile-location-highlight.png`.
- Verified sourced Phobos cards, clickable marker squares, body navigation, location/category indexing, all nine landing entries, and Olympus Mons placement at the center of the mapped feature.
- Verified moon focus by marker double-click, direct mesh single-click with facts off, and a true-scale locator click. The selected moon remains centered in front of Mars during continued rotation and a switch to true scale. Rendered terrain samples at all four sides of Mars verify that the planet also stays centered. Pause, return, and reset work; the settings and explorer panels clear the centered view.
- Verified both true-scale locators with facts off, steady rings under reduced motion, and the normal sonar animation's visible/faded phases and five-second repetition. Screenshots include `moon-sonar.png`, `true-scale-locators.png`, `phobos-true-focus.png`, and `deimos-centered.png`.
- Verified the 30× Mars zoom limit without sphere/camera clipping. The true-scale overview uses the actual approximate size and mean-distance ratios, with fixed-size UI locators.
- Verified distinct rendered shadow coverage at 0%, 50%, 75%, and 100%; switching from the loop restores the saved static percentage, and reset restores Static shadow at 20%.
- Advanced the full lighting loop through daylight, nightfall, night, dawn, and back to daylight. Verified phase/percentage text, pause, and zero Mars speed holding the phase. Moon speed remains independent.
- Verified independent spin/orbit speed controls, stationary pause and reduced motion, reset reproducibility, keyboard shortcuts, drag, wheel, plus/minus keys, zoom buttons, and a two-finger touch pinch.
- Verified motion preference changes and visibility-change suspension/resumption with controlled animation time.
- Verified local Mars texture, both GLBs, and Draco WASM loaded without application console errors.
- Verified individual missing assets, unavailable WebGL, and actual `WEBGL_lose_context` context loss produce visible recovery messages with disabled controls.

## Visual review

Reproduced the white silhouette speckles at 2.45× zoom and 100% shadow. They persisted with stars hidden and disappeared with direct sunlight disabled. After adding the final 1% sunlight fade, visually checked the clean night edge with stars present; the starless full-night render also exactly matched a render with direct sunlight disabled. Comparison captures: [before](verification/edge-before.png) and [after](verification/edge-after.png).

Inspected the desktop scene, 30× terrain close-up, 8K surface mapping, true-scale overview, Phobos cards/focus, Olympus Mons marker alignment, and 390 × 844 mobile Deimos focus. At full night, Mars and both moons retain surface detail through the 8% linear-color floor; a sampled Mars terrain patch contains visibly varying pixel values rather than a black silhouette. Additional orbital snapshots show a moon occluded behind Mars and both moons crossing the foreground. Settings use separate space beside the viewer on wide screens and above it on narrow screens; they hide automatically for moon focus.

Evidence is in [verification/results.json](verification/results.json), with desktop, mobile, control-panel, and orbital screenshots alongside it. Tests use reduced motion for stable initial screenshots; the normal page starts animated unless the system requests reduced motion.

## Limits

- Browser checks used Chromium software rendering. They do not establish a frame-rate guarantee on physical mobile devices or verify Safari/Firefox. Mobile pinch is emulated through Chromium touch input; hidden-tab behavior is tested by emulating the document visibility lifecycle.
- Vite reports the same kind of non-blocking large Three.js bundle warning as the existing planet projects. Decoder assets remain local, including additional decoder files bundled by Three.js.
- Mars detail is limited to the 8K mosaic (4K on devices with smaller reported texture limits); moon textures are 1K. The 4K hardware-selection branch was inspected in code but not exercised on separate physical hardware. Close-up detail remains finite. Depth occlusion is implemented; cast eclipse shadows are not.
- True-scale overview uses sourced approximate dimensions and mean distances, with simplified circular equatorial orbits and accelerated timing. Centered focus is a presentation view: the selected moon is enlarged and positioned in front of Mars; returning restores the physical overview and continuing orbital phase. The other moon may be outside the close-up. The fact catalog is curated historical/reference information, not live telemetry; Deimos's cited thermal report does not provide a global numerical temperature range.
