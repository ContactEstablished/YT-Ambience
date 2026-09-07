# Asset sources and inspection

Research started at https://science.nasa.gov/venus/, then followed its Resources and 3D Resources collections to the Venus model resources. Retrieved 2026-09-07.

## NASA model: cloud-covered Venus

- Resource: https://science.nasa.gov/resource/venus-3d-model/
- Credit: **NASA Visualization Technology Applications and Development (VTAD)**, as credited on the resource page.
- Download: https://assets.science.nasa.gov/content/dam/science/psd/solar/2023/09/v/Venus_1_12103.glb
- Local original: `public/models/venus.glb` (unmodified, including its embedded texture).
- SHA-256: `6aa26809feeb74fee371c43e9904112a76ebb3df15696e6e75297c0fce063bf9`.
- Contents: one mesh, 3,062 vertices, 6,048 triangles, one embedded 1,440 × 720 PNG named `color_2016_04_26.jpg`, no embedded animation. Original material: metallic 0, roughness approximately 0.9. Runtime material: roughness 1, metallic 0.

Before selecting the asset, the GLB JSON and embedded image were extracted and inspected. The image shows soft pale gold and cream cloud bands with white polar areas, without radar terrain or rocky surface features. The byte-for-byte extracted image is retained as `references/nasa-cloud-atlas.png` for review. The first version used the original embedded texture. The reference-inspired revision retains the original mesh/UVs but replaces the material's map at runtime; the original GLB remains unmodified. The model was also visually inspected in the running browser scene.

This selected NASA model represents the **cloud-covered appearance**, not radar-mapped terrain. The resource page does not identify the embedded texture's mission or spectral provenance; do not describe it as a calibrated visible-light photo mosaic.

## Reference-inspired cloud texture (current appearance)

- Local asset: `public/textures/venus-clouds-reference.png`.
- SHA-256: `b6f9ff9b80ba6cf6a55f8c9ae29545751381179963304baa77b85c72150bfeba`.
- Generated 2026-09-07 using the built-in imagegen tool, with the user's supplied `Venus_-_December_23_2016.png` as the visual reference. A local reference copy is retained at `references/user-venus-2016.png`; its original author/license was not supplied or independently verified. It is not served as a playback asset.
- This new artwork is an artistic interpretation of the reference's blue-gray, cream, and pale-gold cloud patterns. It is **not NASA imagery, a scientific cloud map, or a reconstruction of unseen observed longitudes**.
- The exact generation prompt is recorded in `references/cloud-texture-prompt.md`.
- The generated file is stored unchanged. The rendering shader blends its left/right edges and fades its polar tips to prevent distracting seams during rotation. Real-time scene lighting supplies the upper-left illumination.
- On-screen credits distinguish NASA's model from the reference-inspired cloud artwork.

## Surface resources considered but not used

- https://science.nasa.gov/resource/venus-surface-3d-model/ explicitly describes a model of Venus's surface, with a separate `Venussurface_1_12103.glb` download.
- https://science.nasa.gov/3d-resources/venus/ explicitly identifies its standalone Venus texture as stitched **Magellan RADAR imagery**, with gaps filled using global texture, from JPL/Caltech planetary maps. This would show terrain below the clouds and was not selected for the initial scene.

## Other credits

Scene implementation and visual style adapted from this project's Mercury scene (`../wt-fe9723e0`). The seeded star field originated in the existing Earth and Moon scene via Mercury. Three.js and Vite are MIT-licensed; their installed packages contain their notices.

NASA media usage guidance: https://www.nasa.gov/nasa-brand-center/images-and-media/. NASA credit does not imply endorsement.
