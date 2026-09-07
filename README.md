# YT-Ambience

Earth above a slowly rotating lunar foreground in `Earth and Moon/`, built with plain HTML, CSS, JavaScript, and Three.js. Vite provides the local server and production build.

## Run

Requires Node.js 22 or newer.

```sh
npm install
npm run dev
```

Open the local URL printed by Vite (normally http://127.0.0.1:5173). Serve through Vite rather than opening the HTML with `file://`, because the page uses JavaScript modules and loaded textures.

```sh
npm run build
npm run preview
```

The production build is written to `dist/`. Textures are included locally; there are no remote asset requests during use.

## Edit

- `Earth and Moon/index.html`: the page and controls.
- `Earth and Moon/style.css`: layout, background UI, and typography.
- `Earth and Moon/src/main.js`: globe, lighting, atmosphere shaders, and interaction. The `SETTINGS` object at the top contains the main visual parameters.
- `Earth and Moon/src/moon.js`: generated seamless lunar albedo/height textures, crater shapes, relief, and lunar material.
- `Earth and Moon/public/textures/`: surface, relief, water, clouds, and night lights.

Drag to rotate Earth; scroll or pinch to resize Earth. Focus the canvas and use arrow keys to rotate Earth, or +/− to resize it. The camera and lunar horizon stay fixed. The toolbar pauses/resumes both rotations, toggles Earth's clouds, adjusts Earth's size, and resets both bodies to their initial orientation. Rotation honors the operating system's reduced-motion setting. Animation pauses while the tab is hidden.

All interface text and controls are hidden on load. While the page has keyboard focus, **Ctrl + Shift + R** reveals them; press it again to hide them. The page intercepts the browser's usual hard-reload shortcut. Independent Earth and Moon sliders run from **0×** (stopped) to **20×** their default speeds, in **0.05×** steps. Speeds remain set when hiding/revealing the interface; reloading restores 1×. The pause button stops both bodies without changing their selected speeds.

The Moon is a large 3D sphere with locally generated, periodic crater textures and shallow geometry displacement. Its silhouette remains fixed as it rotates; relief and bump detail fade at the extreme horizon. The terrain is an artistic approximation of the user's supplied photograph, not a surveyed lunar location. No photographic Moon assets are required. At the default speed, the lunar rotation repeats every approximately 52 minutes; Earth rotates independently at its existing speed. This is an ambience composition, not a physical-scale simulation. Separate lighting passes allow an Earth with approximately 80% of its projected disk in daylight (night tilted toward its lower-right edge to match the lunar shadow gradient) and a readable lunar foreground. The Moon's current material follows the newer close-up reference: neutral gray dust, fine periodic regolith grain, sparse dark flecks, irregular weathered rims, and lightly shaded gray crater interiors. Crater centers and sizes are retained; their profiles are less uniformly smooth. Lunar lighting uses neutral white sunlight and a small white fill. Most crater interiors retain the restrained 6% albedo shading. A deterministic 28% subset has an additional 2.5–6 percentage points of shading concentrated toward the deepest interior, creating slight variation without darkening the general surface. The neutral gray material and crater geometry are preserved. A separate Moon-only shader now adds a smooth, composition-locked sunlight falloff toward the lower right. Crater interiors deepen progressively in that shaded region, while the corner retains a small amount of light rather than clipping to solid black. The far side (the region nearer Earth in the composition) receives up to 2.9 times its previous linear illumination, tapering smoothly to no added light before the dark near side (lower right). This increases contrast without lifting the near-side blacks. Earth derives its sunlight angle from the same gradient direction, correcting for viewport aspect ratio on resize while preserving 80% daylight. The relief texture alpha stores the rotating crater mask; the gradient stays fixed as the terrain moves through it. This is an artistic lighting treatment, not a physical sunlight calculation. This is a procedural visual approximation of the photograph.

## Earth lighting modes

Reveal the interface with Ctrl + Shift + R, then choose **Earth lighting**:

- **Default** preserves the existing 80% daylight, tilted shadow, and night appearance.
- **Day–night cycle** repeats four stages, each lasting one complete automatic Earth rotation: full daylight, gradual nightfall, full night, and gradual dawn. Dawn provides a smooth return to the next daylight rotation. Nightfall follows the existing tilted lighting direction.

The night view uses the existing geographic city-light map for populated areas, with enhanced faint/whiter settlements and stronger light emission to reveal more city networks. A land mask keeps this enhancement off the oceans. The faint blue-gray land contribution has two successive 5% increases (10.25% cumulatively); ocean terrain brightness is unchanged. Coastlines and continents remain subtle, with city lights providing the main definition. Cloud glow and atmosphere dim through nightfall. Moon lighting and rotation are independent of this setting.

Cycle progress advances only with automatic Earth rotation: changing Earth speed changes cycle speed, 0× or Pause holds it, and dragging temporarily holds automatic rotation and the cycle. Manual drag/arrow adjustments change the viewing orientation without skipping cycle stages. Switching into the cycle or choosing Reset view starts its daylight stage again. Selecting Default restores the original lighting immediately. Reloading starts in Default. At 1×, each stage takes about 5 minutes 49 seconds; at 20×, about 17.5 seconds.

The cycle logic is in `Earth and Moon/src/earth-lighting.js`. Run its checks with:

```sh
node --test "Earth and Moon/src/earth-lighting.test.js"
```

## Reference and imagery

Visual reference: [EARTH — The making of home](https://earth.ethanplus.ai/). This project recreates the present-day globe as a standalone scene; its application code is independently authored. It does not include the reference site's historical timeline or other pages. Lighting is artistic, not a live astronomical simulation, and the clouds are a static map with animated drift.

The reference credits NASA-derived photographic textures distributed by these projects. Local copies were downloaded from the upstream repositories on 2026-09-07:

| Local asset | Source |
| --- | --- |
| `earth.jpg` | [WebGL Earth / 2_no_clouds_4k.jpg](https://github.com/turban/webgl-earth/blob/master/images/2_no_clouds_4k.jpg) |
| `earth-bump.jpg` | [WebGL Earth / elev_bump_4k.jpg](https://github.com/turban/webgl-earth/blob/master/images/elev_bump_4k.jpg) |
| `earth-water.png` | [WebGL Earth / water_4k.png](https://github.com/turban/webgl-earth/blob/master/images/water_4k.png) |
| `clouds.png` | [WebGL Earth / fair_clouds_4k.png](https://github.com/turban/webgl-earth/blob/master/images/fair_clouds_4k.png) |
| `earth-night.jpg` | [three-globe / earth-night.jpg](https://github.com/vasturiano/three-globe/blob/master/example/img/earth-night.jpg) |

`Earth and Moon/src/stars.js` adds 1,100 seeded decorative stars behind both bodies, with varied sizes and brightness. Approximately 18% gently vary by 8–16% over independent 8–18 second cycles. Stars stay in position; reduced-motion preferences freeze the twinkle. These are artistic positions, not a measured star catalog. Three.js and Vite are MIT-licensed dependencies; their license notices are included in their installed packages.
