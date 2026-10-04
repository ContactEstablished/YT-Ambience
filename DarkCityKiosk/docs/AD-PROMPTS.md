# Ad artwork prompts (ChatGPT image generation)

Generate each picture with ChatGPT and save it as PNG in `DarkCityKiosk/_ads/` under the exact filename shown.

- **No text in the images.** Claude adds the headlines, Japanese lettering and logos afterwards, in clean exact type. The LED-screen effect (pixel grid, scanlines, flicker, slide changes) is added in Unreal.
- **If a result contains any letters,** reply to ChatGPT with "remove all text and letters" or regenerate.
- **Use the largest size ChatGPT offers.** Portrait ads should be tall (2:3) and landscape ads wide (3:2). The images are cropped slightly to fit each screen, so keep subjects centred.

## Style line: paste it after every prompt

```
Style: cinematic cyberpunk advertisement for a giant LED billboard on a skyscraper in a rainy megacity at night. Photorealistic, high contrast, soft holographic glow, subtle film grain, Blade Runner 2049 mood. Full-bleed image with no border or frame. Absolutely no text, letters, numbers, logos or watermarks anywhere in the image.
```

## The ads

| File | Screen | Headline Claude will add |
|---|---|---|
| `ad_humanity.png` | Left canyon tower, tall face screen (slide 1) | HUMANITY UPGRADED / より高く |
| `ad_humanity_2.png` | Same screen (slide 2) | MORE THAN HUMAN / それ以上 |
| `ad_samecity.png` | Right canyon tower, tall face screen (slide 1) | SAME CITY. DIFFERENT YOU. / 同じ街、違う、あなた |
| `ad_nexus.png` | Same screen (slide 2) | NEXUS 新世界へ / A BRIGHTER HUMAN TOMORROW |
| `ad_kaze.png` | Centre-left tower, tall brand screen | KAZE かぜ logo / A BRIGHTER HUMAN TOMORROW |
| `ad_daisenka.png` | Centre-right tower, wide screen | DAISENKA 大深化 |
| `ad_people.png` | Right tower, wide screen | PEOPLE. A HIGHER TOMORROW. |

Neon signs that Claude makes from type (no images needed): 生き続ける (teal), 新世界へ (pink), 未来 MIRAI (cyan), 未来は、まだ書き換えられる (red).

### 1. `ad_humanity.png` (portrait)

```
Extreme close-up beauty portrait of a young woman looking straight at the viewer, rain-wet skin, faint glowing cybernetic seam lines tracing her cheekbone and jaw like fine circuitry, calm and confident expression. Cool cyan and electric-blue lighting with deep shadows, dark navy background. Her face fills the upper two-thirds of the frame; the bottom third is dark empty space. Keep her face centred with margin on both sides, because the image will be cropped to a taller, narrower shape.
```

### 2. `ad_humanity_2.png` (portrait)

```
Portrait of an elegant android woman in three-quarter view: half of her face smooth porcelain skin, the other half revealing intricate glowing blue-violet circuitry beneath translucent panels, eyes looking slightly upward. Violet, magenta and blue light on a black background. Subject in the upper two-thirds, bottom third dark and empty. Centred with margin on both sides (the image will be cropped taller).
```

### 3. `ad_samecity.png` (portrait)

```
Side profile of a woman facing left, short dark hair, a delicate glowing neural implant running from her temple to behind her ear, fine raindrops on her face, serene expression. Soft cold blue light from the left, dark blue-grey background with a faint blurred city skyline behind her. Her profile occupies the upper two-thirds; the bottom third stays dark and empty. Centred with margin on both sides (the image will be cropped taller).
```

### 4. `ad_nexus.png` (portrait)

```
A human head-and-shoulders silhouette made entirely of thousands of tiny glowing particles and threads of light, dissolving upward into the air, against a deep black-blue void. Cyan and white light with a hint of warm gold at the core. Silhouette centred in the upper part of the frame, lower third dark. Margin on both sides (the image will be cropped taller).
```

### 5. `ad_kaze.png` (portrait)

```
Minimalist luxury brand advertisement: a pale figure seen from behind, standing with arms slightly open as long flowing ribbons of white and pale-blue light swirl around them like wind. Mostly dark charcoal background, clean and elegant, with plenty of empty space at the top and bottom. Centred; the image will be cropped to a tall 1:2 shape.
```

### 6. `ad_daisenka.png` (landscape)

```
Product advertisement for a sleek futuristic neural-interface headset, matte black with a thin glowing amber light line, floating at an angle above a dark reflective surface, warm amber and orange rim light, deep black background, smoky haze. Product centred in the middle horizontal band, with the left third darker and emptier. Keep the top and bottom quarters plain, because the image will be cropped to a wider shape.
```

### 7. `ad_people.png` (landscape)

```
Wide cinematic shot of a crowd of silhouetted people on a rooftop, looking up at a vast warm amber sunrise glowing through layers of haze between distant skyscrapers, hopeful mood, golden light rays. Main content in the middle horizontal band (the image will be cropped wider); the upper sky stays simple and uncluttered.
```
