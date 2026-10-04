# Kiosk Spec Sheet

The single source of truth for building the hero kiosk. The Blender build script reads its numbers from here (mirrored in `Blender/scripts/kiosk_config.py`), so change a value here first, then in the config.

- **Target look:** `_reference/PrimaryReference.png`. The six other references show the same kiosk from the same corner and are used for detail. None of them show the back or right side, so those are designed by us and kept simple.
- **How the numbers were found:** `Blender/scripts/solve_reference_camera.mjs` solves the reference camera from the kiosk's vanishing lines, then measures features by projecting pixels onto the two wall planes. The pixel readings are in `docs/measure-grid-*.png` and the output is in `docs/reference_camera_solve.json`.
- **Scale assumption:** the side door is **2.00 m** tall. Everything scales with it.
- **Accuracy:** AI images are not perfectly perspective-correct (the left face's lines disagree by about 40 px). Treat the measured values as ±10%. The **Design** column is what we build: measured values rounded, and fixed where they would look wrong for real use.

## Coordinate frame (Blender, metres)

- Origin: centre of the kiosk body's footprint, at ground level.
- **+X** runs along the front face, to the right as seen from the hero camera.
- **+Y** runs from the front face toward the back.
- **+Z** is up.
- The front face (service window) is at Y = −1.55 and faces −Y. The left face (door) is at X = −2.15 and faces −X.

## Hero camera (the reference view = middle of the orbit)

| | Solved | Use |
|---|---|---|
| Horizontal FOV | 58.4° | 58.4° (32 mm on a 36 × 20.25 mm filmback) |
| Pitch | 12.8° up | 12.8° up |
| Height | ≈ 0 m (ground level) | 0.05 m for the overlay match. The video camera height is decided Sunday, starting at 0.35 m. |
| Distance to front-left corner | 10.6 m | 10.6 m |
| Position (kiosk frame) | — | (−9.94, −8.76, h) |
| Heading | Front face runs 35.8° right of the view axis; left face 54.2° left | Blender rotation (102.8°, 0°, −54.2°) |
| Horizon in frame | y = 811 of 941 (86% down) | — |

Distance from the camera to the kiosk centre is 13.25 m; the kiosk centre sits about 5.6° right of frame centre. The orbit pivots on the kiosk centre, with ±45° as the starting arc (to be judged on Sunday's stills).

## Overall dimensions

| Part | Measured | Design | Notes |
|---|---|---|---|
| Body, front face (X) | 4.27 m | **4.30 m** | Converted-container proportions |
| Body, left face (Y) | 3.07 m | **3.10 m** | |
| Body height to canopy underside | 2.43 m | **2.45 m** | |
| Platform (concrete slab) | ~0.07 m (poorly constrained) | **0.12 m**, 1.0 m margin all round | Wet, puddled, chipped edge |
| Canopy band height | 0.49 m | **0.50 m** | Top of canopy = roof deck, at 2.95 m |
| Canopy overhang | front ~0.7, left ~0.7, right ~0.4 | **front 0.70, left 0.70, right 0.40, back 0.40** | Footprint 5.40 × 4.20 m |
| Roof machinery, tallest | 3.93 m | **3.95 m** | Tall cabinet with porthole |
| Antenna mast top | 4.36 m | **4.60 m** | Back-right of the roof |
| Counter lip | 0.83 m | **1.00 m** | Raised: 0.83 m is too low for standing customers |

## Body walls

**Construction (all faces):** painted steel panels about 0.9–1.0 m wide, with vertical seam strips. Rivet rows run along every seam and edge at ~8 cm spacing. Rivets are domed and about 2 cm across. Panels have slight dents. Corners are rounded steel posts about 12 cm square.

### Left face (X = −2.15), the door side

From the front corner toward the back:

1. **Electrical cluster** near the corner, Y ≈ −1.35 to −0.9: a meter box with a dial window (0.35 × 0.50 m, Z 1.30–1.80); a fuse/breaker box with a red-green indicator (0.30 × 0.40 m, Z 1.55–1.95); a small junction box higher up; conduit from all of them running up into the canopy soffit.
2. **"KAZE かぜ" logo**: stencilled on the wall, an A-in-a-circle mark with the word below, about 0.35 m tall at Z ≈ 0.9–1.4.
3. **Sticker poster**: colourful, about 0.30 × 0.45 m at Z ≈ 0.6–1.05, just left of the logo.
4. **Door**: 0.85 × 2.00 m, centred at Y = +0.25, with heavy rounded corners and a raised frame. The upper half has a small window (0.35 × 0.55 m, 2 × 3 panes, dark glass with faint interior glow). The lower half has a riveted kick plate with scratched graffiti. It also has a handle and a lock box.
5. **Conduit and pipes**: two vertical runs and one horizontal run at Z ≈ 2.2 under the canopy.
6. **Back end**: wall ends at Y = +1.55, where the corner post meets the lantern stack (see Props).

### Front face (Y = −1.55), the service side

From the left corner toward the right:

1. **Sticker zone** near the corner: small signs and stickers, plus a small electrical box.
2. **Ticket/vending machine** (retro), mounted on the wall at X ≈ −1.85 to −1.45. Its body spans Z 1.00–1.75 and it projects 0.35 m. It has a lit multi-colour screen, buttons and a coin slot.
3. **Service window**: X −1.50 to −0.15 (1.35 m wide), sill at the counter (1.00 m), top at 1.85 m. It has a real interior about 0.9 m deep:
   - steel shelves with stock and containers
   - stainless equipment and a ramen pot
   - a warm overhead light
   - a pipe across the back

   The orbit looks into it at different angles, so it must be modelled, not painted.
4. **Counter**: a steel shelf projecting 0.40 m, X −1.85 to +0.40, lip at 1.00 m, on two brackets plus a support pipe down to the platform. Condiment bottles (red/orange sauce, soy) and napkin tins stand on it.
5. **Under-counter sign**: a backlit panel, about 0.60 × 0.45 m at X −0.95 to −0.40, Z 0.35–0.80. It reads **HOT RAMEN / COLD BREW / BETTER HUMANS**.
6. **Poster and stickers** on the panel strip between the service window and the glazed window.
7. **Glazed window**: X 0.60–1.86 (1.26 m), Z 0.55–1.60, a steel grid of 4 columns × 5 rows. The glass is frosted and dirty, with dim warm light behind a few panes.
8. **Window lightbox** above it: X 0.65–1.85, Z 1.70–2.20, projecting 0.12 m. The face is white and reads **カフェ・ラーメン / インプラント** in black.
9. **Vent grille** at the base under the glazed window, plus a drain pipe.
10. **Right end**: wall ends at X = +2.15.

### Right face and back (invented, low detail)

These are only seen edge-on at one end of the orbit and through gaps. They get plain riveted panels, a couple of conduit runs, one electrical box and a rear vent. No signs.

## Canopy and lightbox

- **Box**: 5.40 × 4.20 × 0.50 m, underside at 2.45 m. It has a riveted steel frame about 8 cm thick around each lit face, with corner brackets.
- **Lit faces**: front and left only, glowing warm yellow. The right and back faces are dark painted steel.
  - **Left face** reads **珈琲　拉麺　義体** (coffee, ramen, implant), with a steaming ramen-bowl icon near the corner end.
  - **Front face** reads **coffee, ramen, implant** in a rounded sans-serif, with a ⊙ mark after it and a small glyph near the right end.
  - Both faces carry dirt streaks, rust at the rivets and a darker bottom edge where water collects.
- **Soffit** (underside), as dark metal:
  - fluorescent tube fixtures: 2 under the left band, 3 under the front band, angled so they wash the walls
  - conduit and cable runs
  - small junction boxes
- **Corner sign**: a vertical lightbox, about 0.28 × 0.75 m, mounted just past the front-right end of the canopy (X ≈ 2.70, Y ≈ −2.15, Z 2.25–3.00, level with the band and dropping slightly below it) on a bracket with a cable loop. It reads **コーヒー** vertically in red on yellow, with a steaming cup icon at the bottom.
- **Drips**: water runs off the canopy edges, from EasyRain leaks plus a few hero drip streams at the corners.

## Roof machinery (sits on the deck at Z 2.95)

The layout follows the reference from left to right along the front edge, with more stacked behind. All items are boxy and weathered: grey or galvanised steel with rust-red lids, dents and stickers.

| Item | Approx size (W × D × H) | Position |
|---|---|---|
| Small utility unit | 0.6 × 0.5 × 0.45 | Front-left corner |
| AC condenser, fan grille facing −X | 1.0 × 0.7 × 0.75 | Left, behind the small unit |
| Tall cabinet with round porthole, rust-red lid | 0.8 × 0.7 × 1.0 | Left-centre (tallest, top 3.95) |
| Tank cluster: 3 vertical tanks with domed tops, plus a cross pipe | Ø 0.45–0.55, H 0.8–0.9 | Centre |
| Cabinet with a yellow hazard sticker | 0.6 × 0.5 × 0.8 | Centre-right |
| Cable reel lying on its side | Ø 0.9, W 0.4 | Right-centre, near the front edge |
| White box with red label | 0.55 × 0.45 × 0.40 | Right end, near the front |
| Antenna mast with crossbars | 0.15 × 0.15 × 1.65 | Back-right (top 4.60) |
| Pipes, conduit, loose cables | — | Connecting everything; some drape over the canopy edge |

## Free-standing props

- **Ramen lantern (left)**: a paper chōchin, Ø 0.35 × 0.65 m, centre Z ≈ 1.68, at the back-left corner about 0.4 m out from the wall (X ≈ −2.55, Y ≈ +1.30). It sits on a short post on top of stacked wooden boxes, with a cable up to the canopy. It reads **ラーメン** vertically, with a smaller vertical line beside it (proposed: 醤油・味噌, soy/miso).
- **Right lantern**: Ø 0.30 × 0.55 m, centre Z ≈ 1.55, on a thin post at the front-right corner (X ≈ 2.40, Y ≈ −1.85). It reads **24 / 時間 / 営業** (open 24 hours) in black.
- **Two red stools** at the counter: round steel stools with red seats, Ø 0.36 m seat, 0.75 m tall, at X ≈ −1.15 and −0.35, Y ≈ −2.10. They are empty, wet and slightly askew.
- **Stacked boxes/crates** at the back-left: wooden and metal boxes about 1.2 m high, with a red plastic bottle crate in front.
- **Red bottle crate** at the left face, by the door.
- **Green trash bin** at the front-left corner, by the platform.
- **Grey utility cabinet** (about 0.5 × 0.4 × 1.0 m) at the front-right, beside the lantern post, with a second trash bin.
- **Railing**: a short steel rail at the back-left of the platform, from the reference's far left.

## Lights (what actually emits)

| Source | Colour | Role |
|---|---|---|
| Canopy lightbox faces | Warm yellow (≈ 3000 K, saturated) | Key light of the whole kiosk; the main reflection in the puddles |
| Soffit tubes | Warm white ≈ 3500 K | Wash the walls; hard highlights on wet rivets |
| Service-window interior | 2700–3000 K | Depth and life; some light spills onto the counter |
| Lanterns | 2400 K, slight flicker | Accents |
| Window lightbox, under-counter sign | Neutral white / warm | Readable text |
| Ticket machine screen | Multi-colour | Small colour accent |
| Indicator LEDs on electrical boxes | Red/green, a few blink | Tiny moving detail |

## Surface look

- **Paint**: warm ochre-yellow (between RAL 1003 and 1006), satin. Under the yellow light it reads orange-gold.
- **Wear**:
  - paint chipped to dark steel on edges and corners
  - rust blooms at rivets, with rust streaks running down from seams and rivet rows
  - grime gradient over the bottom 40 cm
  - general dirt in recesses
- **Applied**: stickers, posters, graffiti scratches and a stencilled logo, all done as decals.
- **Wet**: everything darker and glossier, with droplets on vertical faces, drip streaks under the canopy edges and puddles on the platform.

## Choices to settle (the references disagree)

Settled by the user on 2026-10-03:

| # | Element | PrimaryReference | Other options seen | Decision |
|---|---|---|---|---|
| 1 | Front-right section | Glazed grid window + lightbox | Menu board (ラーメン 650 / コーヒー 450 / インプラント 1200) + small window (ref 07_18_32) | **Glazed grid window + lightbox** |
| 2 | Corner vertical sign text | Unreadable red glyphs | コーヒー + cup icon (ref 4); 義体 (ref 07_18_32) | **コーヒー + steaming cup icon** |
| 3 | Right lantern text | 24 時間 営業 | 義体 + bowl icon (ref 07_18_32) | **24 時間 営業** |
| 4 | Stools at the counter | None | Two red stools (ref 07_18_32) | **Two red stools** |
| 5 | Left band middle word | 拉麺 | ラーメン (ref 07_18_32) | **拉麺** (matches primary) |

## Out of scope for the kiosk build

The city, train, people, flying cars, ad screens, street furniture beyond the props above, and steam vents. Those are separate phases.
