# Asset sources and inspection

Retrieved 2026-09-12. Every playback asset is stored locally. Files below are unchanged from the cited download unless stated otherwise.

## Mars surface

### Current close-up texture: USGS Viking colorized mosaic

- Resource: https://astrogeology.usgs.gov/search/map/mars_viking_colorized_global_mosaic_232m
- Downloaded the resource page's 1 km cylindrical JPEG: https://astrogeology.usgs.gov/ckan/dataset/7131d503-cdc9-45a5-8f83-5126c0fd397e/resource/5ea881c6-01b3-41fa-a7af-42d2131b54f1/download/mars_viking_mdim21_clrmosaic_1km.jpg
- Original preserved at `references/mars-usgs-1km.jpg`: 21,339 × 10,670, 36,708,552 bytes. SHA-256: `fdfcd335559c3dc67052b7e8a9565d850e336ac0d1f3ea7f5eb7826ffb44ecb2`.
- Runtime `public/textures/mars-detail.jpg`: 8192 × 4096, 10,490,488 bytes. SHA-256: `5081effd7ebd6ea8caceb47b436d1bd2bec2520d0eae7d5f8244aff8894e24f8`.
- Smaller-device alternative `public/textures/mars-detail-4k.jpg`: 4096 × 2048, 2,825,732 bytes. SHA-256: `86eb2a10af171c7976162a24c8ded9c9d4c8a35fe71df04d7ffd5b0841bee78e`.
- The derivatives are deterministic Lanczos downsampling, saved at JPEG quality 92 with optimization; no content generation, recoloring, or sharpening was applied. A 1440 × 720 inspection preview is stored in `references/`.
- The full global mosaic was visually inspected before use. It is north-up with longitude running from −180° to +180° east, compatible with the location conversion in `surfacePosition()`. Olympus Mons was additionally checked at its marker position on the rendered globe. Surface relief is represented by the mosaic shading, not displaced geometry.
- Selects the 8K file when WebGL reports a maximum texture size of at least 8192, otherwise the 4K derivative; Three.js can resize further for smaller hardware limits.
- Credits: NASA Viking imagery / USGS Astrogeology processing. The mosaic's red-brown color differs from the older golden NASA texture. This is historical colorized mapping imagery, not calibrated true-color photography.

### Original texture retained for reference (not loaded by the scene)

- Resource: https://science.nasa.gov/3d-resources/mars/
- Source: NASA/JPL-Caltech planetary map, from Viking imagery processed at USGS, according to NASA's resource page.
- Download: https://raw.githubusercontent.com/nasa/NASA-3D-Resources/11ebb4ee043715aefbba6aeec8a61746fad67fa7/Images%20and%20Textures/Mars/Mars.jpg
- Local: `public/textures/mars.jpg` (972,896 bytes; 1440 × 720 JPEG).
- SHA-256: `12ec6bf02ebd42a246edc778cb2ce8c595b4d9f0892badf0bfff8abb2303c780`.
- Applied to Three.js sphere geometry with sRGB color handling and a matte material. The texture was visually inspected both flat and on the rendered globe. It includes relief shading and visible polar regions; no separate normal or height map is included. Do not describe its colors as a calibrated true-color reconstruction.

## Phobos and Deimos

The older NASA resource pages returned 404 responses during research. These models were instead obtained from earth-pulse's public mirror. Its [source documentation](https://github.com/Buggy1111/earth-pulse/blob/9063c6b60dfb12268931833855f3774526fdcf06/docs/DATOVE-ZDROJE.md) identifies them as NASA VTAD shape models, optimized with Draco/WebP. This is the mirror author's provenance claim; no byte-for-byte comparison against the original NASA downloads was possible.

Original NASA viewer references supplied by the mirror:

- Phobos: https://solarsystem.nasa.gov/gltf_embed/2358/
- Deimos: https://solarsystem.nasa.gov/gltf_embed/2434/

### Phobos

- Download: https://raw.githubusercontent.com/Buggy1111/earth-pulse/9063c6b60dfb12268931833855f3774526fdcf06/public/models/moons/phobos.glb
- Local: `public/models/phobos.glb` (132,008 bytes).
- SHA-256: `286de52c0924deb471a201ee2616f683096cbe4035582f31bf1e18ed0e971e70`.
- One mesh; 16,449 vertices; 32,040 triangles; embedded 1024 × 1024 WebP color texture named `phobos_tex_01.jpg`.

### Deimos

- Download: https://raw.githubusercontent.com/Buggy1111/earth-pulse/9063c6b60dfb12268931833855f3774526fdcf06/public/models/moons/deimos.glb
- Local: `public/models/deimos.glb` (131,352 bytes).
- SHA-256: `29df46fb772837cc35b213264a2011fca36a9015903df0f6788efe0eec3ea25a`.
- One mesh; 16,641 vertices; 32,512 triangles; embedded 1024 × 1024 WebP color texture named `deimos_tex_01.jpg`.

Both GLBs identify `glTF-Transform v4.4.1` as their generator and require `KHR_draco_mesh_compression` and `EXT_texture_webp`. Their textures are embedded, with no external image URI. Both were decoded and visually inspected in Chromium. Runtime transforms center and uniformly scale the models; geometry, UVs, and source files remain intact. Materials use roughness 1 and metallic 0. The models' detailed irregular shapes are retained even though their display sizes are exaggerated.

## Decoder and dependencies

- `public/draco/draco_decoder.js`, `draco_decoder.wasm`, and `draco_wasm_wrapper.js` were copied from Three.js 0.185.1's `examples/jsm/libs/draco/gltf/`. The accompanying README and Apache 2.0 license are stored alongside them. The decoder is loaded locally with a maximum of two workers.
- Draco license source: https://github.com/google/draco/blob/main/LICENSE
- Three.js 0.185.1 and Vite 6.4.3 match Mercury's versions and are MIT-licensed. Their installed packages retain their license notices.
- Playwright 1.62.1 is used only for development verification and is Apache 2.0 licensed; its installed package retains its notice.
- Scene code, layout, and seeded star field are adapted from the existing Mercury project. The star field originally came from Earth and Moon.

NASA media guidance: https://www.nasa.gov/nasa-brand-center/images-and-media/. The mirror describes the NASA moon assets as public domain. Credits identify NASA/JPL-Caltech for Mars and NASA VTAD via earth-pulse for the moons; they do not imply endorsement.
