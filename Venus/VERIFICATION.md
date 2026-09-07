# First-version verification — 2026-09-07

## Reference-inspired cloud revision

- Rebuilt production successfully after replacing the runtime cloud map; original NASA model file preserved.
- Inspected detailed blue-gray/cream cloud appearance in Chrome on desktop and at 390 × 844, including the expanded credits toolbar.
- Exercised 20× rotation, pause, drag to a different hemisphere, and reset. Removed a texture derivative discontinuity at the wrap; the rotated globe then showed no visible hard seam in the inspected view.
- Browser console remained free of captured errors/warnings. Controls were hidden and viewport restored for handoff at 1× rotation.
- Earth/Sun/Mercury process IDs remained unchanged.

## Initial version

- `npm ci`: passed, zero reported vulnerabilities.
- `npm run build`: passed; production output in `dist/venus/`. Non-blocking Vite warnings for bundle size and output directory outside the Venus source root.
- Production preview: http://127.0.0.1:5176/, bound to loopback with strict port selection.
- Chrome: visually inspected at the normal 2079 × 1082 viewport and at 390 × 844. Centered cloud-covered globe, upper-left sunlight, dark night side, and subdued stars. Narrow layout has no horizontal overflow; revealed text and toolbar remain readable and within the viewport.
- Browser controls exercised: Ctrl + Shift + R both directions, initial/reload hidden state, mouse drag, wheel zoom, arrow-key rotation, keyboard +/− zoom, zoom buttons, pause and resume, 0× and 20× slider limits, 0.05× step, and reset to 1×/default framing/resumed rotation.
- Browser console: no captured errors or warnings.
- Source review confirms Mercury's two-pointer pinch handler, reduced-motion behavior, hidden-tab suspension, pointer cleanup, and visible loading/WebGL/error messages were retained. Physical multitouch and OS reduced-motion emulation were not exercised in this desktop browser session.
- Ports 5173/5174/5175 retained their original process IDs; no Earth, Sun, or Mercury files or servers were changed. Venus preview process: 75932 at verification time.
- Temporary viewport override was reset. Preview left open at default framing, 1× rotation, controls hidden.
