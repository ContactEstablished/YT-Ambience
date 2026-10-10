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
| Body, front face (X) | 4.27 m | **5.25 m** (proportion pass 10/4; was 4.30) | Wider than measured on purpose: from the 20 mm floor camera the measured kiosk read tall and narrow. Widened symmetrically about the orbit pivot |
| Body, left face (Y) | 3.07 m | **3.40 m** (was 3.10) | |
| Body height to canopy underside | 2.43 m | **2.25 m** (was 2.45) | |
| Platform (concrete slab) | ~0.07 m (poorly constrained) | **0.12 m**, 1.0 m margin all round | Wet, puddled, chipped edge |
| Canopy band height | 0.49 m | **0.73 m** fascia (massing pass, 10/4; was 0.50) | Dark edge beam 2.15–2.30 (hangs 0.10 below the soffit), yellow face 2.30–2.81, dark coping to 2.88. Roof deck at 2.87 m |
| Canopy overhang | front ~0.7, left ~0.7, right ~0.4 | **front 0.85, left 0.85, right 0.50, back 0.50** (was 0.70 / 0.70 / 0.40 / 0.40) | Footprint 6.60 × 4.75 m (was 5.65 × 4.45); heavy posts cap the four corners |
| Roof machinery, tallest | 3.93 m | **4.15 m** (roof pass 10/4; was 4.32) | The banded tank in the front-right cluster. The HVAC anchor on the front-left corner is broad and low (top 3.81 m with its lid hood): nearest the camera, it sets the silhouette's top, which from the hero, A and B cameras is within ±0.6% of its height before the roof pass |
| Antenna mast top | 4.36 m | **4.24 m** (roof pass; was 4.27) | A slim pipe mast behind the white box, front-right, red beacon on top |
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

- **Box**: 6.60 × 4.75 m, soffit at 2.25 m (proportion pass 10/4; was 5.65 × 4.45 m at 2.45 m). Massing pass (10/4): the fascia is a 0.30 m deep box that reads, from below, as bright yellow face / dark structure: a dark edge beam with a bottom flange hangs 0.10 m below the soffit, the lit face sits in its rail frame, a dark coping runs along the top, and 0.15 m posts cap the corners. Dark joists and a diagonal corner brace cross the soffit; the tube lights hang on drop rods just inside the edge beam.
- **Lit faces**: front and left only, glowing warm yellow. The right and back faces are dark painted steel.
  - **Left face** reads **珈琲　拉麺　義体** (coffee, ramen, implant), with a steaming ramen-bowl icon near the corner end.
  - **Front face** reads **coffee, ramen, implant** in a rounded sans-serif, with a ⊙ mark after it and a small glyph near the right end.
  - Both faces carry dirt streaks, rust at the rivets and a darker bottom edge where water collects.
- **Soffit** (underside), as dark metal:
  - fluorescent tube fixtures: 2 under the left band, 3 under the front band, angled so they wash the walls
  - conduit and cable runs
  - small junction boxes
- **Corner sign**: a vertical lightbox, 0.28 × 0.95 m, hung beside the front-right end of the canopy, level with the front of the corner post (signage pass 10/5: moved forward and down so the cinematic camera sees it; X ≈ 3.42, Y ≈ −2.57, Z 1.87–2.82), on two brackets with a cable drip loop. Its printed face reads **コーヒー** vertically in red on cream, with a steaming cup icon at the bottom.
- **Drips**: water runs off the canopy edges, from EasyRain leaks plus a few hero drip streams at the corners.

## Roof machinery (sits on the deck at Z 2.95)

> **Roof pass (10/4, brief 4):** the deck is at Z 2.87. The layout is `kiosk_config.ROOF_*` (built by `kiosk/roof.py`): four overlapping clusters instead of rows, read left to right from the camera side as box mass, box mass, horizontal cylinder, upright rounded forms, reel, small terminal equipment. Earlier layouts (a front row plus a second row on stands; before that, the reference-measured list) are superseded.

| Cluster | Item | Size (W × D × H, m) | Position, support |
|---|---|---|---|
| A, HVAC zone | Packaged HVAC unit (the anchor): fan in a square bezel and a service door on the front, porthole and filter panel on the left side, heavy lid with a drip edge, exhaust hood on the lid's front-right; faded grey with a charcoal lid | 1.26 × 1.05 × 0.68 (+0.05 lid) | Front-left corner, on a flashed roof curb (0.06) |
| | Condenser with a deep louvre grille facing −X; dull galvanised | 0.66 × 1.18 × 0.55 | Behind the HVAC along the left edge, set in 0.12 m, on dunnage (0.14) |
| | Small unit with a round port; rust-red lid | 0.56 × 0.60 × 0.46 | Behind the condenser |
| B, vessel | Horizontal service vessel (warm aged metal): two courses with a bolted flanged joint, a reducer and a flanged stub into the HVAC's side, a dished end with a blind-flanged nozzle, a gate valve, a relief valve, a sight glass, a nameplate | Ø 0.54, shell 1.76 long (2.2 overall) | Along the front from the HVAC to cluster C, axis 0.58 above the deck, on two saddles bolted to dunnage channels |
| C, tanks | Tiered separator (drum, domed shoulder, flanged neck, upper drum, capped nozzle); a line from the vessel dips into its upper drum | Ø 0.34, H 1.10 | Front, beside the vessel's dished end, on a chequer-plate skid |
| | Banded tank (galvanised): domed head, bolted manway, gauge, relief valve, back valve, pressure switch | Ø 0.54, H 0.84 + dome | Front, right of the separator, same skid (the tallest rounded form) |
| | Squat receiver on three legs; a gooseneck arches from its bolted top into the tank | Ø 0.36, H 0.46 | Behind them |
| D, reel and service | Hose reel on a swivel turntable, turned 35° toward the street: A-frame sides, solid rust-red rear flange, open front ring on three spokes so the coiled black hose shows, crank, roller fairlead; the hose runs over the front edge to a nozzle | Ø 0.78, W 0.34 | Front-right, on a skid |
| | Control cabinet under a sloped rain hood: label, hazard sticker, two lamps, louvres; conduits down into the skid | 0.52 × 0.40 × 0.92 | Behind the reel, on a short stand |
| | Sensor mast: pipe on a gusseted base plate, instrument box, crossarm with an anemometer and a louvred sensor shield, whip antenna, red beacon | Ø 0.06, 1.18 + beacon | Behind the white box |
| | White terminal box with a red label | 0.36 × 0.42 × 0.50 | Front-right corner |
| Back (seen from above only) | Supply duct from the HVAC's back to a drop into the deck; a mushroom kitchen-exhaust fan on its curb; the flue stack; vent housing; a refrigeration condensing unit with a top fan; three back boxes | — | Back half of the deck |

## Free-standing props

- **Ramen lantern (left)**: a paper chōchin, Ø 0.35 × 0.65 m, centre Z ≈ 1.68, at the back-left corner about 0.4 m out from the wall (X ≈ −2.55, Y ≈ +1.30). It sits on a short post on top of stacked wooden boxes, with a cable up to the canopy. It reads **ラーメン** vertically, with a smaller vertical line beside it (proposed: 醤油・味噌, soy/miso).
- **Right lantern**: Ø 0.30 × 0.55 m, centre Z ≈ 1.55, on a thin post at the front-right corner (X ≈ 2.40, Y ≈ −1.85). It reads **24 / 時間 / 営業** (open 24 hours) in black. Signage pass (10/5): now a narrow 0.20 × 0.52 m lightbox clamped to the same post, after the reference (`SIGN_24H`).
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

## Construction pass (2026-10-04, brief 2)

Geometry only, proportions locked. The walls read as an old steel shell that has been repaired, retrofitted and rewired:

- **Sheets:** uneven joints (`kiosk_config.PANEL_JOINTS`): bare seams, riveted battens, laps (the next sheet overlaps, riveted) and wide bolted strips. Sheets split at uneven heights, often lapping; about 30% are replacement sheets standing a few mm proud, some in faded or dark yellow.
- **Service opening, as layers:** wall → charcoal H-posts carrying the hood (with knee brackets) → jambs with a bolted galvanised facing → reveal → an inner steel frame stepping in at the back of the reveal → interior. Around it: an isolator switch on the right post, a hooded kitchen extract, a narrow utility housing with a perforated grille, and a service-entry enclosure with pipe stubs under the counter.
- **Door wall:** an electrical cabinet on unistrut rails (rain hood, conduit risers into the canopy), a round exhaust fan below it, a pull box on a unistrut riser, an inset access hatch, a steel channel up the hinge side, gussets at the top corners of the frame, strap hinges and border rivets on the leaf.
- **Under the canopy:** purlins parallel to the fascia, I-section joists with bolted end plates and header cleats, gussets under the edge beam, splice plates on its face, unistrut rails carrying the conduits on hanger rods, tube drivers, the sign power supply strapped to the corner brace (red pilot lamp), and a controller box.
- **Fasteners:** hex bolts (3.2 cm) and rivets (2 cm), sized to read from the video camera; concentrated on panel edges, frames, equipment and supports.
- **For the cable pass:** gland stubs, LB fittings, risers, pull and junction boxes and unistrut rails are the anchors; no cable network yet.


## Utility pass (2026-10-04, brief 3)

Geometry only, proportions and construction locked. Conduit, cable, pipe and drainage runs connect the equipment so the kiosk reads as one working machine: about 75% organised and clamped, 25% later improvisation. Every run starts and ends at real equipment. Built by `kiosk/utilities.py` (numbers in `kiosk_config.UTILITIES`) into SM_Kiosk_Utilities, as static swept tubes with rounded bends (rigid) or splines (flexible). No simulated cables.

- **Door wall:** the service entrance rises from the platform as a 2-conduit group (power into the meter box; comms jogs over into the data box). The fuse box feeds the pull box through an LB body and an elbow. The data box's riser runs up behind that feed and tees into the old wall conduit. Armoured flex runs from the pull box to a card reader by the door. Liquid-tight flex runs from the fan into the cabinet's gland. Three conduits leave the cabinet's side with nested elbows, run up past the header (crossing in front of the old conduit) and enter a sealed soffit penetration.
- **Service opening:** the ticket machine feeds two conduits up into the corner soffit junction box. The isolator offsets round the hood bracket into the kitchen extract. The extract vents through a gooseneck. A copper water line with a red-lever valve enters the wall under the counter. A grey drain hose runs from the service-entry enclosure to a floor grate. A retrofit cable is tied along the old conduit, lifted over the bay post and dropped into the window lightbox.
- **Under the canopy:** a galvanised trunk hangs under the joists on clevis hangers, with couplings, a tee onto the hood and an end box. A left run goes to the controller. The sign circuit runs from the sign power supply to a corner box, then along conduits under both fascia edge beams with feed bodies, a lantern box and an end box. Three thin cables hang on J-hooks to the tube drivers.
- **Loose accents:** the corner-sign drip loop, a twice-coiled slack cable tied under the right junction box, the 24h lantern feed draped over the drain, and the two roof cables brought down the blank ends of the lit faces into the sign circuit. Older step-3 cables that sagged along the front wall were replaced by the tied cable. The fuse-box cable and the left lantern feed now end on sign-circuit boxes.
- **Drainage (front-right):** the canopy's edge box drains through an outlet under the front edge beam. A short run goes back under the soffit, then a cast downpipe with socket joints and a cleanout runs down the window bay's corner, ending in a shoe over a splash block. The older back-left downpipe gained a soffit collar and a cleanout.
- **Roof:** a disconnect switch sits on the HVAC front (seen from the floor camera), fed by conduit from a roof boot, with a flex whip into the unit. An insulated suction line and a copper liquid line arch from the condenser into the HVAC. A condensate line runs to a splash pad. Coax runs down a mast leg to the white box. Not every unit is connected. (The roof pass re-anchored these on the regrouped equipment; see below.)
- **Line weights:** heavy (drain Ø9 cm, vent Ø8.4 cm, lagged suction Ø5.6 cm, trunk Ø4 cm); medium (conduit Ø2.2–4.8 cm, copper, hose); fine (signal and light wiring Ø0.9–1.4 cm).
- **New materials:** Conduit_Painted, Cable_Black, Hose_Grey, Copper_Aged, Insulation_Black, Pipe_Cast. All are clean; grime comes with the weathering pass.

## Roof pass (2026-10-04, brief 4)

Geometry only, on top of the locked proportions, construction and utilities. The target was the reference roof's character: dense, layered, asymmetrical, retrofitted equipment of different generations, memorable in silhouette, while the kiosk stays low and squat. Built by `kiosk/roof.py` into SM_Kiosk_Roof; the numbers are in `kiosk_config.ROOF_*`.

- **Four clusters, not rows** (see the roof machinery table). Seen from the camera they overlap: the condenser steps up to the HVAC, the vessel runs out of the HVAC's side to the tanks, the separator and tank stand at the vessel's end, the cabinet shows between the tank and the reel, and the mast stands behind the white box.
- **Height rule:** the HVAC moved to the corner, nearest the camera, so it reads as the biggest mass while staying low; the tank cluster and cabinet, farther away, carry more height instead. Measured on silhouette renders, the kiosk's height from the hero/Mid camera is +0.6% (reference camera −0.5%, A 0%, B +0.6%). The roof's tallest point (mast aside) dropped from 4.27 to 4.15 m.
- **Support logic:** a flashed curb under the HVAC; dunnage I-sections on posts or pads under the condenser, the vessel's saddles and a back box; chequer-plate skids for clusters C and D; a stand under the control cabinet; a gusseted base plate for the mast; a swivel turntable for the reel; rubber boots where lines go into the deck.
- **Connections:** the vessel's flanged stub into the HVAC; the vessel's line into the separator; the receiver's gooseneck into the tank; the tank's pressure-switch cable across the platforms to the control cabinet; the separator's drain into the deck. The utility pass's roof runs were re-anchored on the moved equipment: the disconnect sits right of the HVAC's door; the refrigerant pair leaves the condenser's side into the HVAC's back; the condensate runs to a pad beside the vessel's saddle; the mast coax runs down the pole into the white box. The corner drape cable now leaves the HVAC's curb (the corner box was removed); its drop down the fascia and the pull elbow are unchanged.
- **New materials:** Steel_Aged_Warm (the vessel, warm aged metal) and Paint_Grey_Faded (the HVAC housing and the separator). Existing paints mark the other generations: dull galvanised, charcoal, rust-red reel flanges. All clean; grime comes with the weathering pass.
- **Removed:** the front-row corner box, the top box with its cowl, and the four-leg lattice mast (now a slim pipe mast).

## Surfacing pass (2026-10-04, brief 5)

Materials only; geometry, utilities, roof, lighting, camera, city and crowd untouched. Target: 20–40 years of rain, repairs, repainting, cooking and hands, still in daily use (not abandoned). The yellow stays the warm hero against the cool city: measured on the lit door wall the yellow lost ~5% luma (the cinematic Mid frame ~7%) and no saturation. Review renders: `Renders/frames/wx_before` vs `wx_after2` (LS_Review), `kiosk_roof_final2` vs `wx_after2_sweep` (Mid, frame 180, fog clear); sheets `Renders/stills/kiosk_weather_*.png`.

**How it works.** Blender bakes WHERE the kiosk ages from its own geometry; Unreal decides HOW MUCH each material shows.
- `kiosk/weather.py` (run by `export_kiosk_glb.py`): faces of the weathered materials get a second UV channel, `WeatherUV` (TEXCOORD_1); faces no video/review viewpoint can see are packed at 0.3 scale. Cycles bakes per-texel position, normal, part/material ids, cavity (3.5 cm AO), edges (bevel vs flat normal) and recess (45 cm AO) into `Blender/weather_cache/` (git-ignored, ~2 GB). numpy then writes three 8K masks to `Unreal/RawContent/weather/`: A = edge wear, rust, grime, dark streaks; B = rust streaks, soot, touch, wetness; C = paint variation, newness, splash, grease. `T_WearDetail.png` is a tiling 0.5 m detail (chip noise, scratches, water spots, mottling) on the metre-scale UVMap.
- Iterating the look needs no re-bake: `blender -b --factory-startup -P weather_masks.py` (~5 min), then `node Scripts/ue.mjs Scripts/kiosk_weather.py --textures`. Any geometry change needs the full export (the cache matches one UV layout; bake ~7 min + masks ~5 min).
- `Unreal/Scripts/kiosk_weather.py`: imports the masks (BC7, linear), builds `M_KioskWeathered` (one custom-HLSL layer stack: paint generations → chips to primer and steel → rust → grime → splash → rain streaks → grease/soot → hands → wetness, with roughness and metallic following every layer), makes `MI_KW_<material>` from `scene_config.KIOSK_WEATHER` (category preset + overrides; base colour from the glTF instance) and sets them as overrides on the SM_Kiosk_* actors. `--instances` re-applies the numbers only; `--off` restores the clean glTF materials for A/B checks. `kiosk_refresh.py` re-applies them after a re-import; `kiosk_look.py` also drives the lit sign faces' emissive.

**Physical drivers (all baked, nothing is a global grunge overlay).**
- *Rain-flow streaks:* the two camera-facing sides (−Y front, −X door wall) become a 2.5D relief (4 mm cells, up to three surface layers per cell). Water runs down each surface; where a surface ends (a rivet, bolt, bracket, lap, sill, box bottom), it drips onto the surface below if that lies within 3 cm (otherwise only a weak wicked stain). Drip edges add dirt, in coherent clusters rather than an even curtain; fasteners always do, and rusty fasteners run orange. Some face tops start a dirt run below the edge. Runs fade over 12–65 cm, meander and are intermittent. The roof drain outlet and shoe feed rust.
- *Rust:* fastener heads (about half of them rusty) and a halo round them, seams (cavity, more when low or wet), the bottom 3.5 cm of every sheet, the lowest 32 cm of the walls, the deck under roof equipment, the bottoms of roof units, the drain, and old chips.
- *Edge wear:* convex edges × a per-part history (most parts lightly chipped, a few heavily) × abrasion: up to 2.4× in the bottom 60 cm, more at the exposed corner, the door bottom, the counter front by the stools, by the bin and the crates (`kiosk_config.WEATHER_TOUCH`, "abrade"). Bolt heads are rubbed. Small dings low down.
- *Grime:* cavities and recesses, undersides and the soffit, ledges (dirt collects), a dirt line along every sheet's bottom, the low walls; rubbed clean on convex edges and touch points.
- *Heat/kitchen* (`WEATHER_HEAT`): grease on the service hood's underside and lip and round the kitchen extract (it also feeds grease drips), soot above the hood, on the soffit above the opening and on the upper wall by the kitchen, grease round the roof exhaust fan, soot and scorching at the flue top.
- *Hands* (`WEATHER_TOUCH`, "touch"): the door lever and leading edge, push marks, the counter nose and forearm band, the service jambs, the ticket-machine keypad, the isolator, access-panel latches, the cabinet handle. Cleaner, polished, worn to bright steel on edges.
- *Splash-back:* a band whose top wanders between 30 and 62 cm above the platform, with mud speckles and dried spots.
- *Wetness:* wind-driven rain (32° from vertical) reaches only the low walls under the canopy; the fascia, roof and exposed faces are wet. Wet areas get lower roughness; porous layers darken slightly.
- *Paint generations* on the yellow sheets, per sheet: original 52%, faded/chalky 20%, darker amber 12%, newer repaint 16% (glossier, less worn, fewer rust spots), plus broad soft fading blotches. Other paints vary only slightly in value.

**Per-material histories** (`scene_config.KIOSK_WEATHER`). Yellow sheets (the dark-yellow ones older and more chipped); dark structure (softened black paint worn to steel; on black, dried runs and dust read lighter); greys/charcoal (charcoal = newer retrofit housings, least worn; the HVAC's faded grey = old, sun-faded, streaky); galvanised (rubs brighter, stains dark; the dull galvanised more oxidised and stained); aged warm steel, rust-red, cast pipe (heavily stained); the lit sign faces (only seams, joins and edges age; dirt dims the glow locally); the platform slab (dirt, splash, rust under the drain).

**Not yet** (later passes): stickers, posters, ads, graffiti, warning labels, menus, counter clutter, steam, animated drips. Possible later additions: a height/normal response for the chips.

### Targeted refinement (2026-10-04, brief 5B)

A selective pass on four areas, not another global one. Target feeling: heavily used + old + maintained + continuously wet (not abandoned). Verified with a texel diff of the old and new masks: outside the four zones, only the dark-run channel (and the wetness that follows it) changed, along the named source columns on the two yellow walls. The door wall and lower kiosk are otherwise identical. Numbers live in `kiosk_config.WEATHER_FASCIA / WEATHER_RUNOFF / WEATHER_SERVICE / WEATHER_ROOF_UNITS / WEATHER_BASE_RINGS`; the code is `kiosk/weather.py` `refine()` and `_source_runs()`.

- **A fourth mask, `T_KioskWear_D`** (4K, zero outside the zones): R dried rain spatter, G sun fade (to a per-material `ChalkColor`, rougher by `FadedRough`), B zinc white rust (`OxideColor`, matte), A light scuffs (rubbed lighter, slightly metallic, fine scratches). In `M_KioskWeathered`, spatter uses the coarse detail sample's water spots (about 4 mm to 1.5 cm).
- **Lit fascia:** each diffuser panel between the mullions has an age (`WEATHER_FASCIA["panels"]`: orig / amber / bleach / new). The shader's `EmisAge` tints and dims the glow per panel: amber panels are warmer and about 25% lower in emission, bleached ones paler, the new one a touch brighter. Dirt collects above the bottom rail (irregular line), along each mullion and stile, under the top rail and toward the corner posts. Frame rails get about 1.6× chips. A third of the top-rail rivets weep a faint rust run down the diffuser. Runs come down from the coping under every roof unit, saddle, skid and the hose. The sign sits on the tonemapper's shoulder, so its dirt amounts are high (lightbox streak 1.0, grime 0.9, rust streak 0.8). Measured: the lit sign lost 2.2% luma in the cinematic frame (3.5% in the close-up), with about 2–4% of its pixels (the runs, spatter and edges) more than 15% darker.
- **Service window:** grease and heat on the faces 5A missed: the hood's front lower lip, the reveal and inner-frame head, and the tops of the jamb facings (patchy upward plumes). Overlaps get dark accumulation through the runs channel, because the grime layer was already full in those cavities. The counter nose, nosing and corners get more chips. Runs come down the jamb facings and posts from under the hood. The working surfaces (counter top, pass-through sill) are wiped (dirt × 0.4). The kitchen interior is unweathered material and stays clean.
- **Roof units (each its own age):**
  - HVAC housing: sun-faded, chalky paint with streaky chalking, rougher; its charcoal lid stays darker (newer).
  - Condenser: white-rust bloom on its galvanised casing and louvres.
  - Vessel: light scuffs along its crown, lighter steel in its chips (`Steel_Aged_Warm` BareColor 0.20).
  - Tank: cleaner galvanised with a few oxidised patches.
  - Tank, receiver and separator: dark water staining wicking up 12–17 cm from their bases, plus dark rings on the skid round them.
  - Reel: grime, runs and rust × 1.3, its frame slightly faded. The hose has its own sun-chalked rubber, only on the roof actor (`scene_config.KIOSK_SLOT_AGED` → `MI_KW_Rubber_Black_Roof`).
  - Flanges, rings and pads get rim rust. A faint 3D rust halo (about 4 cm) surrounds every roof fastener.
  - The roof is barely lit, so these read as restrained tonal and roughness differences. They will separate more once the lighting pass adds a soft roof light.
- **Rain history:** the longest runs start at named sources (`WEATHER_RUNOFF`):
  - the roof units over the coping, onto the lit faces;
  - on the yellow walls, a few long faint runs (0.4–1.3 m) from the soffit joists meeting the header, the strip and lap joints, the junction-box drops into the header, and the canopy brace at the body corner;
  - the hood onto the jambs and posts.

  Each run starts on the first matching surface below its source and then follows the rain-flow relief: it drips across small gaps and stops where its surface ends.
- Stills: `Renders/stills/kiosk_weather5b_{fascia,service_window,roof,doorwall,cinematic,cinematic_crop}.png`. The renders are `Renders/frames/wx5b_review2` (LS_Review) and `wx5b_sweep` (Mid frame 180, fog clear), against `wx_after2` and `wx_after2_sweep`.
- **The user's brief closes the weathering/material pass with 5B.** Next: signage and decals.

## Signage pass (2026-10-05, brief 6)

Graphics only: geometry, rooftop machinery, utilities and weathering stay locked. Target: the kiosk has
operated for years and collected layers of practical communication, maintenance markings, advertising
and owner-made notes, at roughly the reference's density (busy enough to have a history, not covered
edge to edge). No counter clutter, food equipment, steam, animated water or ground props yet.

**Hierarchy.**
- The fascia stays the cleanest and brightest sign; its lettering only ages (below).
- Secondary lit signs are smaller and dimmer: the ramen lantern (warm), the 24h lightbox, the
  corner コーヒー sign and the under-counter LED board.
- Medium: posters, notices, the menu, plates.
- Small, found up close: labels, inspection stickers, handwritten notes, residue.

**How it is built.**
- **Art:** `Graphics/make_kiosk_graphics.mjs` (headless Chromium via Playwright, Windows system
  fonts) draws every item as vector art (`Graphics/art/*.js`), then ages it per pixel:
  - sun fade (yellow and magenta inks go first, so old prints drift cyan);
  - paper yellowing, water stains with tide lines, edge dirt, creases and wrinkles;
  - tears with fibrous edges, tape, scratches, rust spots.
- **Atlases:** four, each with three maps in `Unreal/RawContent/graphics/`:
  - Paper (2 px/mm), Labels (5 px/mm), Signs (2 px/mm), Decals (2 px/mm);
  - maps: C = albedo + opacity, N = normal, S = roughness / metallic / emissive / weather response.
  - `graphics_manifest.json` gives each item's cell and real size. Small labels are reused across
    parts (one cell, many cards).
- **Cards:** `Blender/scripts/build_graphics.py` + `kiosk/graphics.py` lay each card from
  `kiosk_config.GRAPHICS_CARDS` onto the exported kiosk (`kiosk_detail.glb`) by raycasting:
  - paper bridges over battens, laps and rivets, sits on proud sheets, slips behind conduits and
    tucks under newer equipment;
  - stacking layers are 0.9 mm apart, so there is no z-fighting;
  - a corner can peel.
  - UV1 is the WeatherUV of the surface under each triangle, so in Unreal the card samples the
    wall's own weathering masks. Rain streaks, rust runs, grime, splash, kitchen grease and wetness
    carry on across the paper, scaled by how much each material soaks up (paper > vinyl > metal).
  - Output: `RawContent/kiosk_graphics.glb` (SM_Kiosk_Graphics, SM_Kiosk_Signs) and
    `graphics/kiosk_decals.json`, exported on its own. Iterating on signage never touches the kiosk
    export or its bake.
- **Unreal:** `Unreal/Scripts/kiosk_graphics.py`:
  - M_KioskGraphic (masked, two-sided, the weathering transfer);
  - M_KioskDecal (deferred decals, one instance per item; the cards don't receive decals);
  - M_KioskLettering on the canopy's Sign_Text_Black slot;
  - moves L_Lantern_R to the 24h box.
  - Tunables: `scene_config.GRAPHICS_LOOK`. `kiosk_refresh.py` re-applies it after a kiosk re-import.

**What is where** (`kiosk_config.GRAPHICS_CARDS` / `GRAPHICS_DECALS`).

*Door wall:*
- **Poster cluster** under the utility box, oldest to newest. It sits above the line where the green
  bin hides the wall from the cinematic camera (below ~0.85 m, y −1.4..−0.78); a first layout lower
  down was almost entirely behind the bin.
  - a sun-faded tonkotsu ramen ad (drifting cyan, water-stained), across the batten and onto the
    access hatch's frame;
  - the KAZE poster (blue/cyan with a red band) on top, its logo just under the utility box, one
    corner peeling;
  - a torn night-market flyer above them, behind the pull box's riser.
  - Around them: an older poster's adhesive ghost with tape-glue corners peeking out, and scraps of
    tape from notices ripped off long ago.
- **Notices and stickers:** the utility company's inspection notice (stained edges) taped to the
  utility box; a KAZE sticker on the batten.
- **Equipment labels:**
  - utility box: DB-02, a hazard sticker;
  - meter box: 3φ 200V, a faded old inspection sticker, a QR service log;
  - fuse box: 200V and circuit numbers in white paint marker;
  - junction box: a hazard sticker; pull box: ML-3;
  - electrical cabinet: nameplate, 感電注意, 通電中 開放厳禁, an inspection sticker, a service company,
    an asset barcode.
- **Access hatch:** inspection dates in marker.
- **Door:** STAFF ONLY plate, a handwritten "please knock" note, a band sticker, scraped sticker
  residue.

*Service side:*
- **Left jamb:** the old CASH ONLY card crossed out by hand; the laminated menu with the owner's
  price corrections; a handwritten "miso sold out" note.
- **Right jamb:** the food-business permit, a coffee price-rise note on kraft card, the cashless
  payment decal (one corner lifting), scraped residue.
- **Ticket machine:** a 食券 strip, an asset label. **The box above it:** SG-4.
- **Strip between the opening and the window bay:** the implant-clinic poster, the torn top strip
  of an older poster above it, two round street stickers.
- **Small equipment labels:**
  - kitchen extract: 高温注意; front housing: WT-1 and an inspection sticker;
  - window pane: a RAMEN CLUB sticker;
  - service entry: GAS, an old service sticker, the next inspection date;
  - utility cabinet: hazard, service company, SG-4.
- **Bay post:** a gyoza tanzaku, and the screw holes and residue of a removed bracket.
- **Service hood:** the stall number K-07 stencilled in light paint, and the ghost of a sign once
  bolted there (four holes with rust runs). An old sign rail's holes at the top of the left jamb.

**Lit signs.** All are smaller and dimmer than the fascia (`GRAPHICS_LOOK` KG_Signs emissive 1.9
against the fascia's 2.8).
- **Corner sign:** moved forward (`CORNER_SIGN`), hanging beside the fascia's right end level with
  the corner post, so the cinematic camera sees it as in the reference. It has a printed face:
  cream, red border, コーヒー, a steaming cup. Its old 3D lettering stays behind the print, so the
  canopy keeps its part list and therefore its weathering.
- **24h sign:** the round 24h lantern became a narrow lightbox (`SIGN_24H`): 24 / 時間 / 営業 on
  the old pole, on galvanised clamps, wired from a box on the pole. L_Lantern_R now lights it
  (`SIGN_24H_LIGHT`).
- **Under-counter sign:** an LED-dot board (smoked acrylic, warm dots, a few dead ones).
- **Ramen lantern:** warm paper (`EMISSIVE_COLOR` Lantern_Paper, strength 3.2) with ラーメン and
  a small 醤油・味噌 line.

**Fascia.** The lettering stays the identity; only the vinyl ages.
- M_KioskLettering: a few letters faded, fine crazing that leaks the light behind, and the
  diffuser's own rain runs, dust and spatter carried over the letters (lighter than the black
  vinyl).
- It finds the diffuser's WeatherUV from world position through an affine fit that build_graphics.py
  writes (`kiosk_decals.json` fascia_uv1). The front diffuser has 6 UV islands; the fit uses the one
  under the lettering, x −3.44..0.64.

**Weathering check.** Moving the corner sign and removing the props' placeholder stickers needed one
re-export and re-bake. The masks were compared with the previous ones by world position (4 mm
cells): the mean change per channel is 0.000–0.013. The larger differences sit on the roof deck's
wetness (not seen from the cameras), the service hood's streak relief, and the wall strip where the
placeholder stickers used to make drip edges.

Gotcha: weather.py keys each part's random history on its part number, so adding or removing parts
in a weathered section reshuffles every later part's paint generation. A first attempt that dropped
the corner sign's 3D text and added two bolts changed 37% of cells. Keep part lists identical.

## Kitchen pass (2026-10-09, prompt 7)

The service opening and the working kitchen behind it. Geometry, walls, utilities, roof, weathering and
signage stay locked. Target: a real, actively used ramen / coffee counter at 11 PM in a quiet moment
between customers. Compact, practical, dense and warm, but readable: the opening still says "order
here" from the cinematic camera. No worker, no steam, smoke, boiling or drips yet (later passes).

**How it is built (no re-bake).** The old step-2 interior (stock shelves, coffee machine, pots,
condiments, the ticket machine, the 0.9 m recess's lining) lived inside the weathered ServiceSide and
Body meshes. Re-exporting them would have re-baked the locked weathering, so instead:
- **Blender:** `build_kitchen.py` + `kiosk/kitchen.py` build the kitchen on its own:
  `Unreal/RawContent/kiosk_kitchen.glb` + `kitchen/kitchen.json`. Numbers: `kiosk_config.KITCHEN`,
  `POS`, `UNDER_COUNTER`; small props are sized in `kiosk/kitchen.py`.
  - SM_Kiosk_Kitchen: the room, worktops, cabinets, sink, hood, boiler, stock pot, shelves, rails,
    brewer, grinder, the order terminal, the fridge and drawers.
  - SM_Kiosk_KitchenCounter: a stainless top sheet on the customer counter, with UV1 = 0..1 over
    the counter for its own wear map.
  - SM_Kiosk_KitchenCards: printed things from the new Kitchen atlas.
  - 40 prototypes SM_KP_* (bowls, cups, bottles, tubs, inserts, tools, boxes), placed in Unreal as
    instances (99 placements; 97 since the exterior pass cleared the under-counter boxes).
  - Vertex masks as on the kiosk (`kiosk/masks.py`: R edges, G occlusion, B cavity).
  - The script also trims the context kiosk with the same rules Unreal uses, so its check renders
    match.
- **Unreal:** `Unreal/Scripts/kiosk_kitchen.py`:
  - **Trim.** GeometryScript deletes the old interior from COPIES (`/Game/DarkCity/Kiosk/Kitchen/Trim/
    SM_Kiosk_ServiceSide_K`, `SM_Kiosk_Body_K`) and puts them on those actors. The rules are in
    kitchen.json "trim": whole material slots, boxes for parts that share a kept material (the old
    grout strips, jar lids, coffee spouts), and the service recess's Interior_Recess faces. Every
    kept triangle keeps its WeatherUV, so the weathering is unchanged. It removes 9166 of 23150
    ServiceSide triangles and 1024 of the Body's (the same counts as the Blender trim).
  - **Material.** M_Kitchen is one master with per-material instances MI_KK_* (`scene_config.
    KITCHEN_LOOK`): category preset + the Blender colour + overrides.
    - Worn edges and grime come from the vertex masks.
    - T_KitchenDetail (tiling) gives smudges and fingerprints, brushed grain and water spots.
    - The counter sheet adds T_CounterWear through UV1.
  - **Props.** One InstancedStaticMesh component per prototype on SM_Kiosk_KitchenProps.
  - **Lights.** KITCHEN_LIGHTS, plus L_Interior, which is now the rear fill (`scene_config.INTERIOR`).
  - `kiosk_refresh.py` re-runs it after a kiosk re-import (step 2 puts the untrimmed meshes back).
    `kiosk_look.py` re-applies its light levels. `--off` restores the old interior for A/B.
- **Art:** `Graphics/art/kitchen.js` makes the Kitchen atlas (4 px/mm; big prints lower). It holds the
  terminal's screen, LCD, key legends, tap pad, maintenance sticker, asset tag and NO CASH sticker;
  six order tickets and a translucent ticket back; masking-tape labels; noodle and cup box prints; the
  bean bag and tare labels; the calendar, temperature log, menu and hood note. The cards use the
  signage pass's M_KioskGraphic through MI_KG_Kitchen (vertex alpha 0 means no wall weathering, and
  displays glow at EmissiveStrength 2).
  - Item names are global across atlases: the kitchen menu is `k_menu`, because `menu_card` already
    belonged to the Paper atlas.
- **Wear textures:** `Blender/scripts/make_kitchen_textures.py` (numpy, Blender's python) writes
  `RawContent/kitchen/T_CounterWear.png` and `T_KitchenDetail.png`.

**The room.** It runs 2.97 m wide (x −2.35..0.62) and 1.45 m deep behind the opening. That is wider and
deeper than the old recess, because the orbit looks right-back through the opening, mostly at the
right wall. A bulkhead keeps the opening head (and the old prep-light fixture) at 1.80 m. Behind it the
ceiling rises to 2.10 m, so the floor camera sees the upper shelves. From the camera inward:
- **Pass + prep worktop** along the front wall:
  - stacked ramen bowls (white with a red band; black with a red inside);
  - a cutting board with a knife and sliced scallions;
  - a topping rail of four inserts (scallion, chashu, menma, egg);
  - two bowls set out with tare in them, a ladle resting on a dish;
  - squeeze bottles and seasoning tubs.
- **Coffee corner** (right): cup stacks, lids, a sugar / creamer caddy, the grinder with a bean hopper.
  On the back counter below the right shelf: a batch brewer over an airpot (green BREW display) and a
  second airpot labelled HOT.
- **Cooking line** under a stainless hood (baffle filters, two warm lamps, a "clean filters Mondays"
  sticker):
  - a six-well noodle boiler with four tebo baskets in use;
  - the stock pot on its burner, a ladle in the broth, the lid leaning on the upstand;
  - a red kitchen timer on the wall;
  - slim tools (strainer, ladles, tongs) hanging from the hood's rail.
- **Prep side** (left): a rice cooker, the sink with a gooseneck faucet, tare bottles with tape
  labels, a tools rail (ladles, a yukihira pan) and a knife strip.
- **Back wall:** white subway-tile splashback (one or two replaced tiles a shade off), cream-painted
  steel above (the warm glow from the street), stainless behind the cooking line.
  - Middle shelf: seasonings, ingredients, bowls.
  - Top shelf: backup stock and packaging (blue noodle boxes, takeout containers, tub stacks, cup
    sleeves, a cup box, coffee beans).
  - A warm LED strip under the top shelf lights the middle one.
- **Right wall** (the surface the orbit sees most): tiles, a wire rack with bowls and stock over the
  aisle, the noodle supplier's calendar, the temperature log on a clipboard, a towel on a hook.
- **Order tickets** hang on a rail just inside the opening. The customer sees their backs glowing
  faintly in the prep light.

**The order terminal** (replaces the step-2 ticket machine, same footprint, so the wall behind stays
covered; the signage pass's two labels on the old machine went with it). Its parts:
- a charcoal pedestal bolted to the wall, with a flex conduit into it;
- a warm-grey payment unit with a sloped keypad deck: 12 rubber keys with legends, red / yellow / green
  function keys, an amber LCD, and a glossy contactless pad with its LED row;
- a card slot, and a receipt slot with a curled receipt;
- a hooded screen pod tilted back 17°: a deep charcoal bezel, a dim order-summary screen, rubber
  corner bumpers, and three status LEDs on the visor;
- the maintenance sticker on the pod's side, an asset tag, and a NO CASH sticker.
Worn corners, smudged keys and scratches come from M_Kitchen.

**The customer counter.** A stainless top sheet in pieces round the jambs, posts and terminal. Its seams
(x −1.15, −0.62) run where sheets meet; it has a rolled nose over the old edge.
- T_CounterWear marks:
  - polish where forearms, trays and bowls slide (the band along the edge, the pickup spot by the
    opening, in front of the terminal);
  - scratches mostly along the counter;
  - faint cup and bowl rings, soy specks round the condiments;
  - dark grime only in the seams and along the wall.
  Old but hygienic.
- On it, about 20–30% of the area:
  - napkins and a chopstick pot by the left jamb;
  - a condiment caddy (chili oil, two soy, shichimi, pepper);
  - the pickup tray with a lidded coffee and a covered black bowl;
  - a ticket spike with receipts by the terminal;
  - a tray stack and a menu stand at the right end.

**Under the counter** (outside, mostly in the canopy's shadow):
- a slim under-counter fridge (green 3.2 °C display), with a crate of onions on it;
- a three-drawer steel unit under the terminal, below the gusset strut.
The darker lower band contrasts with the bright working area above. The exterior pass (below) moved
the fridge and cleared the boxes and stock pot from the gas entry.

**Lighting** (`scene_config.KITCHEN_LIGHTS`, `INTERIOR`):
- L_Kitchen_Prep: a rect light under the bulkhead, aimed down and a little toward the customer. The
  pass and counter are brightest; it spills onto the counter.
- L_Kitchen_Hood_0/1: warm spots on the cooking line.
- L_Kitchen_Shelf_0/1: warmer, dimmer strips.
- L_Kitchen_CeilingR: over the coffee corner and the right wall.
- L_Interior: the rear batten's dim fill (was 20 cd in the old recess).
- L_Kitchen_POS: a faint cool screen glow.
- The back corners fall off.

**Review shots:** `kiosk_config.KITCHEN_REVIEW_CAMS` (KitchenPOS, KitchenShelves, CounterTop,
UnderCounter), plus "Cinematic" (the sweep camera at Mid), are appended to LS_Review after the signage
shots. They are frames 175, 191, 207, 223 and 239. Stills: `Renders/stills/kiosk_kitchen_*.png`.


## Exterior pass (2026-10-09, prompt 8)

The kiosk's immediate footprint: crates, bins, delivery containers, small service equipment, and how
they meet the platform. Everything from prompts 1–7 stays locked (structure, fascia, posters, kitchen,
terminal, roof, lighting, cameras, city, train, crowd). Target: the stall looks settled into its street,
with things accumulated through deliveries, cleaning, storage and maintenance, in a few purposeful
clusters with open ground between them. No worker, no new patrons, signs, roof equipment, steam,
smoke, drips or rain effects.

**How it is built (no re-bake).** The old step-3 ground props lived in SM_Kiosk_Props, part of the kiosk
export (whose bake used them as occluders), so:
- **Blender:** `build_exterior.py` + `kiosk/exterior.py` → `Unreal/RawContent/kiosk_exterior.glb` +
  `exterior/exterior.json`. Placement: `kiosk_config.EXTERIOR`; standard sizes (crates, tote, bottle crate,
  bottles, cylinders) in `kiosk/exterior.py`.
  - SM_Kiosk_Exterior: the one-off parts in place. SM_Kiosk_ExteriorCards: the printed marks.
  - 7 prototypes SM_XP_* (two crates with produce, the tote, the bottle crate, two bottles, the gas
    cylinder), 20 placements, instanced in Unreal.
  - Vertex masks as on the kiosk; the in-place parts bake their occlusion with the kiosk and the slab
    visible, so feet and wall sides collect grime.
  - The script trims the context with the Unreal rules and prints a residue check (no face of an old
    prop's own material may survive).
- **Unreal:** `Unreal/Scripts/kiosk_exterior.py`:
  - **Trim.** GeometryScript deletes the old ground props from a COPY of SM_Kiosk_Props
    (`/Game/DarkCity/Kiosk/Exterior/Trim/SM_Kiosk_Props_X`): the slatted crates, the green cabinet, the
    red crate, both bins, the utility cabinet, the lantern's box pedestal, the flattened cartons and the
    junction box's floor cable (9660 of 16904 triangles; Blender's check trims 9656). The railing, the
    stools, the lantern and both poles, the downpipe and the electrical cluster stay.
  - **Material.** M_Exterior, one master with MI_KX_* per material (`scene_config.EXTERIOR_LOOK`):
    category preset (plastic, paint, galv, wood, paper, concrete, rubber, glass, metal) + the Blender
    colour + overrides. Grime from occlusion and cavity, oxidation in seams, rubbed (plastic, wood) or
    chipped (paint) edges, sun fade, smudges and scratches from the kitchen's tiling detail map at two
    scales, dried mud specks in a band above the slab, and **rain exposure from world position**: wet
    and glossy outside the canopy's footprint, wind-driven rain reaching `Reach` × (height below the
    canopy) under its edges, never onto tops under it. Sheltered things stay dry; exposed ones read as
    wet as the slab.
  - Printed marks: `Graphics/art/exterior.js` (the Exterior atlas, 4 px/mm, the cartons 2) through
    MI_KG_Exterior on M_KioskGraphic (no wall weathering).
  - `kiosk_refresh.py` re-runs it after a kiosk re-import. `--apply` numbers only, `--off` the old
    props back for A/B.

**Working zones kept clear** (open ground is part of the layout):
- the staff door's apron and outward swing (hinged at its back edge; about 0.9 m out);
- the electrical cabinet and the exhaust fan beside the door (the old red crate stood below them);
- the door wall's access panel, the gas / water entry under the counter, the stools' knee space;
- the fridge door, the utility cabinet's door and the cage's gate;
- both drain splash zones, and all walking routes: every prop stands on the platform.

**Door side, back-left (inside the railing), the main cluster** (the reference's left accumulation):
- **The lantern's pedestal**, same footprint and top (so the pole and lantern stay put):
  - a slatted timber crate on skids, weighted with two concrete blocks seen through the slats,
    stencilled 天地無用;
  - an olive steel tool case (lid, latches, folding end handles, swages, TOOLS No.3 stencil), turned 4°;
  - a crossed timber riser with the pole's flange plate, socket and gussets.
- **This morning's delivery** against the railing: a faded blue stacking crate of cabbages and a green
  one of spring onions. Each has a stacking lip, ribs, hand holes, an inset foot that sits inside the rim
  below, and a supplier stamp (丸三青果, KAZE 物流); a delivery slip is tucked under the green crate's
  grip. On top sits **the red crate of empties** going back with the driver: 14 brown and green
  returnable bottles, six cells empty, the MIRAI logo panel, an EMPTIES tag. That keeps the scene's red
  accent beside the lantern, where the reference has its red crate.
- **The dry-stock locker** (the old green cabinet, which overhung the platform edge with the railing
  running through it): olive steel on feet, a rain hood with a drip edge, louvres, swages, the K-07 STOCK
  stencil. Its door and padlocked hasp face the work space behind the corner.
- A splash block under the old back-left downpipe's shoe.
- Two cartons (noodles, cups) on timber bearers behind the back corner, under the canopy's back
  overhang. The orbit never sees them; they keep the dry cardboard where the story needs it.

**Front-left corner, by the counter's end:**
- **The customer bin**, about where the old green bin stood (the wall's baked grime already expects it):
  a moulded, tapered grey-green body with corner ribs and hoops, a skirt on rubber feet, side grips, a
  rim lip, and a teal lid with a push flap toward the counter. A 燃えるゴミ BURNABLE sign on the front,
  a half-scraped collection-day sticker on the side, scuffs and splash specks low down. Its lid tops out
  at about 0.80 m, like the old barrel: any taller and the cinematic camera loses the KAZE poster's
  lower line behind it.
- A lidded tote of cup stock beside it (masking-tape label, a note taped to the lid).
- The junction box's floor cable, re-run straight down the wall (two saddle clips) into a floor gland
  box, clear of the bin.

**Front-right corner, the service cluster** (kept under counter height):
- **The utility cabinet** (refined, and moved clear of the corner angle it used to overlap): a grey
  enamelled box on a galvanised channel stand bolted down, a sloped rain hood, the door on the street
  side hinged on the right (louvres, T-handle lock, padlocked hasp), and flexible conduit from its gland
  plate into the slab. A shock-hazard sign, an owner's plate, an inspection card on the side. **The 24h
  sign's pole is clamped to it** with two U-bolt brackets.
- **The gas cylinders' cage**: two grey 10 kg LPG cylinders (foot ring, collar with hand holes, brass
  valve) chained into a galvanised angle-and-bar cage with a sloped roof over the valves. The gate is on
  the platform-edge side, for deliveries from the street. Copper pigtails run to a regulator on the back
  post; the supply pipe drops behind the corner and runs along the right wall's foot into its base,
  unseen from the street. 火気厳禁 plate, LPG labels, a filling tag. A green wash-down hose with a brass
  nozzle hangs coiled on the front.
- **The cans bin** (the old grey bin, moved in front of the bay's corner, clear of the vent grille and
  the drain): galvanised, corrugated, dented, with a rolled rim, side handles, a can-hole lid and a
  カン・ビン sign.

**Under the counter:** the fridge moved from behind the right stool (where it filled the sitter's knee
space and covered the access panel) to between that stool and the gusset at x 0.53, with one door
hinged away from the stool. Nothing stands in front of the gas / water entry or under the left stool.
The drawers stay. The two stools, the counter supports and the lit lower sign are untouched.

**Checks:** a BVH overlap test of every new part against the kiosk, the kitchen and each other leaves
only intended contacts (the clamps round the 24h pole, the socket round the lantern pole, the gas pipe's
wall sleeve, the pigtails on the valves).

**Review shots:** `kiosk_config.EXTERIOR_REVIEW_CAMS` (ExtDoorSide, ExtDoorCorner, ExtService,
ExtFrontLow) plus OrbitA / OrbitB (the sweep camera at its two stops) are appended to LS_Review after
"Cinematic": frames 255, 271, 287, 303, 319 and 335. Stills: `Renders/stills/kiosk_exterior_*.png`.

## Rain contact pass (2026-10-09, prompt 9)

How rain, runoff, drips and a little steam meet the finished kiosk. Geometry, props, signage, kitchen, weathering,
lighting, camera, city, crowd, rain density and fog are untouched. Target: the platform and props feel connected to
the rainy street, runoff has sources and destinations, sheltered areas stay sheltered, steam adds gentle life, and
everything joins the loop seam exactly.

**Where the water goes (Blender, `build_rain_contact.py`, numbers in `kiosk_config.RAIN_CONTACT`).** It runs on
`kiosk_exterior.blend` (the kiosk, kitchen and props as they stand in Unreal) and rebuilds nothing:
- *Exposure:* from every 16 mm texel of the slab, 40 rays go up against the rain (falling ~6 deg off vertical toward
  +X+Y, with gusts); the share that escapes is how much rain lands there. The canopy, walls, counter, stools and props
  shelter it, so the wet/dry line follows the geometry. Noise (2.5–55 cm) breaks the line into ragged damp tongues
  10–20 cm under the front and door-side canopy edges; the open right and back margins are wet.
- *Damp:* exposure through a soft threshold, spatter a few cm into the shelter, street splash and wicking along the
  slab's outer edge, drip spatter, runoff trails, the grate's wet ring. *Standing water:* only where rain or runoff
  feeds a low spot of a gentle height field, in short stretches behind the steel edge angle (front and door side),
  never in the counter's standing area. *Contact:* anything standing on the slab (feet, bases, the walls) found by short
  upward rays, with a soft halo.
- *Points:* the drip sources (the underside above each chosen point) and landing spots, the downpipe mouths and
  landings, the grate, the steam bases, all ray-cast.
- Writes `Unreal/RawContent/rain/T_RainContact.png` (2048 px over ±4.096 m, 4 mm: R damp, G standing water, B rain
  exposure, A 1 − contact; the alpha is never 0) and `rain/rain_contact.json`; preview `Blender/renders/rain_contact_map.png`.

**Canopy drips (5, not an even row):** the near front-left corner post; a fascia joint in front of the glazed window
bay; beside the canopy's drain edge box at the front-right (the slightly stronger one: every 0.75 s slot, 82% drip);
a door-side fascia joint past the door; the right fascia. All land on the platform (15 cm front/door-side band, 50 cm
right band), never on a prop or in front of the service opening. Periods 0.75–3 s; some slots stay dry, so timing is
irregular.

**Downpipes and drains:** the front-right shoe trickles (broken beads, a few splash droplets) onto its splash block;
a narrow trail meanders from the block to the slab's front edge between the cans bin and the utility cabinet and fans
out where it leaves. The back-left shoe does the same onto the exterior pass's splash block, its trail running to the
back edge clear of the locker and the cartons. The under-counter drain hose's grate has a damp ring. Nothing leaks from
the electrical cabinet or the gas equipment.

**Unreal (`Scripts/wet_fx.py`, look in `scene_config.WET_FX`, shader code in `Scripts/wetfx_hlsl.py`):**
- *Loop clock:* `MPC_WetFX` LoopTime, keyed linearly 0 → loop length over LS_Sweep by `make_sweep.py` (LS_Review and
  LS_WetFX copy it). Every effect completes whole cycles per loop (rates rounded to LoopLength) and hashes its random
  choices on the slot index modulo the slots per loop, with an exact integer hash (a `sin()` hash is not reproducible
  in fp32 and would desync shaders). The last frame leads into the first exactly, whatever range a render covers.
- *Platform:* `M_KioskWeathered` gained a `UseRainContact` static switch, on only for `MI_KW_Platform_Concrete`, so
  every other kiosk material compiles as before. Damp concrete darkens and turns glossy; standing water is mirror-smooth;
  moist grime collects round feet and the wall foot; world-mapped concrete tone/roughness variation; raindrop rings
  (EasyRain's ripple textures and maths, on the loop clock) where rain lands on water or wet concrete; rings where each
  canopy drip lands, synced to the drops; the slab's sides soaked a few cm up from the street with wet runoff streaks.
  `DebugMap` 1 shows the map as colour (R damp, G water, B rain).
- *Street:* the puddles' raindrop rings moved to the loop clock (same look as EasyRain's MF_EasyRain_ripplesRain).
- *Drips and trickles:* `M_FX_Water` on camera-facing strips (SM_FX_Quad = the engine plane with its bounds pushed out
  of plane). A falling streak as long as half a frame's travel, never thinner than a pixel (no shimmer), the next drop
  swelling at the source, a few droplets thrown up on landing. Lit per pixel with a rounded normal, plus a refraction
  pickup of the scene just above the drop, so it catches the fascia's warm light near the top and dims as it falls.
- *Steam:* `M_FX_Steam` on camera-facing cards, scrolling noise (whole tiles per loop), a slow sway, widening and
  thinning with height, soft where it meets geometry, lit through the translucency volume. Sources: the stock pot (a
  faint wisp under the hood; warm in-scatter for the hood lamps, whose narrow cones the volume can't resolve), the
  kitchen's roof exhaust fan, and the gas appliances' flue (both carry a grey-blue in-scatter for the city glow, since
  nothing lights the roof). From the floor camera the corner HVAC hides the fan below ~6 m, so its cards are tall and
  lean toward the street side; the flue plume shows above the roof in the cinematic view, the fan plume at orbit end B.
- *Exterior props:* `M_Exterior` picks up the slab's damp a few cm up their feet, beads on wet exposed tops and narrow
  runoff paths down wet exposed sides (world-mapped). Sheltered crates, cartons and the kitchen stay dry.
- Switches: `wet_fx.py --water off|on`, `--steam off|on`, `--contact off|on` (also the MPC's WaterAmount/SteamAmount).

**Review:** `kiosk_config.WET_REVIEW_CAMS` (WetFrontLeft, WetDrain, WetDripCorner, WetDrip, WetSteamPot) appended to
LS_Review after OrbitB (frames 351, 367, 383, 399, 415); LS_WetFX (`make_review.py --wetfx`) is LS_Sweep seen from
`WET_MOTION_CAM` at the front-right corner. Stills `Renders/stills/kiosk_wet_*.png`, clips `Renders/kiosk_wet_*.mp4`.
Measured: 192 LS_Review frames at 1080p rendered in 40.0 s with the effects vs 39.8 s without.

## Final polish pass (2026-10-10, prompt 10)

A restrained finishing pass on the approved kiosk: roof readability, steam, three material distractions, and the loop
seam. Geometry, props, camera compositions, warm kiosk lighting, exposure, fog and the city are untouched; measured
on the 4K cinematic frame, the whole-frame mean, fascia, service window, walls and street are unchanged (56.1 / 119.5 /
122.0 / 80.3 / 73.9 before, 56.2 / 119.7 / 122.0 / 80.6 / 74.0 after).

**Roof light (`Scripts/polish.py`, `scene_config.ROOF_LIGHT`).** From the floor camera the roof machinery read as one
dark mass against the viaduct's underside. Two soft, shadowed spot lights stand in for light that is really there:
`L_Roof_CityBounce`, the cool city glow and wet street behind the camera (front-left, ~35 deg up, 150 cd, 2 m source),
and `L_Roof_ScreenRim`, the SAME CITY screen's blue from the right (120 cd). They shine on lighting channel 1 only, and
only SM_Kiosk_Roof joins channel 1, so the fascia, canopy, deck, walls, props, street and fog get nothing (no volumetric
scattering; MegaLights off for these two, the classic path honours channels). Shadowed, so the gaps between units stay
dark. 4K luma, cinematic: HVAC faces 18 -> 29, condenser 10 -> 20, vessel 37 -> 44, tanks 35 -> 48 (the fascia stays
~120). Orbit A gains least (its camera-facing units were already lit by the soffit glow), orbit B most.

**Steam (`wetfx_hlsl.STEAM_HLSL`, `wet_fx.py`, `scene_config.WET_FX["steam"]`).** The old noise was laid out in card
units, so a 2.2 m tall card stretched every eddy ~4x into vertical streaks. Now: noise in metres (the card size comes
from its scaled axes), read at fixed low mips (5-6 of StarterContent T_Perlin_Noise_M, whose finest octaves are ~1 mm
here and read as grain; a mip bias would make the wide and tele views differ), carried up at Rise m/s with the fine
eddies 1.35x faster than the billows and the warp 0.7x (it churns rather than scrolls), a meander of two slow waves
climbing the column, a half-width growing by Spread per metre, density thinning as sqrt(Base / width), the threshold
climbing by Breakup toward the top so it ends in wisps, its sides eaten by the noise, and a fade well inside the card's
sides and top (cards widened: flue 2.6 x 2.8 m, fan 3.6 x 3.4 + 3.0 x 2.8 m). Same sources and restrained density; the
stock pot's wisp is fainter (Opacity 0.8 -> 0.55, higher threshold) so the pot and prep area read through it.

**Materials (only what still showed at 4K).**
- *KAZE poster* (`Graphics/art/paper.js` age, `GRAPHICS_CARDS` age 0.25 -> 0.6): a season old, sun-faded toward cyan
  with a paler red band, blacks lifted, water-stained up from the bottom, streaks from the box's drip line, grimy edges,
  a small tear at the lower right. Paper atlas regenerated in full (all 15 items keep their rects; only the poster's
  pixels changed, checked against git). Never use `make_kiosk_graphics.mjs --only`: it repacks the atlas with just the
  named items (the other posters' pixels vanish while the manifest keeps their old rects).
- *Cans bin* (KX_Galv: Rust 0.35 -> 0.12, Grime 0.5 -> 0.32, Scratch 0.5 -> 0.3): on wet zinc each matte white-rust or
  grime patch sat beside mirror-like metal reflecting the city, which read as heavy mottling. *Customer bin*
  (KX_BinBody: Fade 0.45 -> 0.3, Scratch 0.7 -> 0.45, Smudge 0.5 -> 0.35): calmer panels; rubbed edges and the splash
  band carry the wear.
- *Counter* (`make_kitchen_textures.py`, `kiosk_kitchen.py --textures`): scratches were laid at >= 35% strength
  everywhere plus 900 random strays at 50% (an even bright haze); now their strength follows the polish map's use zones
  (pickup spot, forearm band, terminal) as polish^1.6, 300 faint strays, patchy. The counter top is below every video
  camera's eye line (only its nose shows), so this mostly matters in close views.

**Loop (all of the sequence's moving parts now repeat exactly; the rain is crossfaded).**
- The big billboard's NEXUS (719) -> SAME CITY (0) in the prompt-9 seam sheet was an unintended reset, not an ad
  change: M_LEDScreen, M_NeonSign, M_CityBG_Light (beacons, neon pulse) and M_Vehicle_NavBlink ran on engine Time, which
  starts wherever each render process starts (so every chunk of a long render would also have jumped). They now read
  `wetfx_hlsl.loop_time` = fmod(MPC_WetFX LoopTime, LoopLength); `setup_screens.py / setup_city_bg.py /
  setup_traffic.py --materials` rebuild just those materials. Slide changes are kept clear of the seam (LeftA_0 offset
  0 -> 1.5 s: its changes were ending exactly on the seam); RightA_0 shows SAME CITY across it, its changes at 3, 11,
  18, 26 s. A scan of every material in /Game/DarkCity found no other engine-time node (EasyRain's puddle-wind
  function has Time but its intensity is 0).
- The rain (EasyRain's GPU particles, splashes and puddle ring sprites) can never repeat: a hard cut at the seam
  changes the frame 2-2.5x more than the steps around it. `make_sweep.py` now keys every track for `SWEEP["tail_s"]`
  (1 s) past the loop end as the loop's own first second (camera, fog waves, train, traffic runs that start in the first
  second, crowd runs and clips, the loop clock), the playback range stays the loop, `render.py` renders past it when
  asked (`--frames 0-744`, playback range extended for that render and restored), and `encode_loop.mjs <tag>` crossfades
  the tail over the loop's first second: the wrap then plays frame 719 -> 720 of one continuous simulation. It also
  writes a labelled repeat of the boundary (crossfaded, then hard cut) and a frame-difference report.
- Frame 720 vs frame 0 (the same loop moment from the two passes) differ only in rain, splashes and sub-pixel
  anti-aliasing jitter: walkers, vehicles, screens, steam, drips and camera match. The whole crossfaded loop played
  twice has no step above 2.5x its neighbourhood in any region (frame, sky, kiosk, ground).
- For the 5-minute final rendered in chunks, overlap each chunk by the same second and crossfade the joins the same way
  (the loop clock already makes the chunks agree).

**Review:** `make_review.py --polish` builds LS_Polish (Cinematic, OrbitA, OrbitB, then 50 mm views from those same
positions, `kiosk_config.POLISH_REVIEW_CAMS`, then CounterTop, ExtDoorCorner, DecalCloseup, WetSteamPot; last frames
15, 31, 47 ... 159); `--motion` builds LS_CineMotion (LS_Sweep from a camera held at the Cinematic pose, mist waves on).
Stills `Renders/stills/kiosk_polish_*.png`; clips `Renders/kiosk_polish_motion.mp4`, `kiosk_polish_loop_30s.mp4`,
`kiosk_polish_loop_seam.mp4` (+ `_seam_diff.txt`). Timing: 4K MRQ ~1 s a frame with a free GPU, but with the editor's
VRAM grown (15.2 of 16 GB in use) the same render ran ~7x slower; 744 frames at 1080p took about a minute.
