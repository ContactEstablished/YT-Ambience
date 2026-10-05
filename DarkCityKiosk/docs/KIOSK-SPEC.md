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
