# What the data tells us about an object, and the 3D library (14 Nov 2026)

## What each source actually measures
| Question | SPHEREx alone | With Gaia / catalogues | Verdict |
|---|---|---|---|
| **Where is it on the sky** | Yes: position in every photo (to ~1″ after averaging; pixel = 6.15″) | Gaia: to a millionth of that | ✅ measured |
| **Is it moving, how fast** | Yes: shift between visits (Barnard ~10″/yr = 1.7 px) | Gaia: exact motion | ✅ measured |
| **How far away** | No (its yearly wobble is ~0.1 px, too small) | Gaia parallax → distance | ✅ from Gaia; ❌ for objects Gaia doesn't have |
| **Colour / temperature** | **Yes, this is SPHEREx's strength**: brightness at 102 infrared wavelengths (0.75–5 µm) = a spectrum. Its shape gives temperature | — | ✅ measured (infrared), visible colour is **inferred** from temperature |
| **What it's made of** | Yes, roughly: dips in the spectrum = methane, water, CO, CO₂, ices | — | ✅ measured, coarse (R≈40–130) |
| **Does it change brightness** | Yes: compare visits (R Draconis gets monthly points → light curve) | — | ✅ measured |
| **Size** | **No**: stars are single dots | Brightness + distance + temperature → radius (physics formula). Brown dwarfs are all about Jupiter's size, whatever their mass | 🟡 calculated, not seen |
| **Shape / surface** | **No** for stars, brown dwarfs, asteroids (all dots). **Yes, coarsely** for galaxies, nebulae and comet comas/tails | — | ❌ for our 5 targets |

**One-line answer:** we measure *where*, *how it moves*, *its infrared colour* and *what it's made of*. We **calculate** size and visible colour. We **never see** its shape: every 3D model is an informed illustration, not a picture.

## What that means for the 3D library
Build **one model per class of object, driven by measured numbers**, not a hand-made model per star. The data sets the dials; the class sets the look.

| Class (from the classifier) | Model | Dials set by data | Our targets |
|---|---|---|---|
| Red dwarf | Glowing sphere, darker edge, starspots, occasional flare | radius, temperature → colour | Barnard's Star |
| Brown dwarf | Jupiter-size ball with cloud bands, very dim | temperature → colour (L: dark red; T: dull magenta; Y: almost black, visible only in infrared) | ε Indi Ba + Bb (as an orbiting pair), WISE 0855 |
| Pulsating giant (Mira) | Huge, lumpy, breathing sphere | period → animation speed, brightness change → swelling | R Draconis |
| Young star (T Tauri) | Star + dusty disk + jets, flickering dimming | dimming events from light curve | RW Aurigae |
| Asteroid | Irregular rock | size (calculated), rotation if known | bonus / "candidate" |
| Comet | Nucleus + coma + tail away from the Sun | tail direction from Sun position | 3I/ATLAS (bonus) |
| Galaxy / nebula | The real SPHEREx image on a plane, or a particle cloud | real shape from the image | background objects |

**Toggle "infrared view ↔ human-eye view":** infrared = SPHEREx's real colours mapped to visible; human eye = colour from temperature. WISE 0855 at ~250 K would be nearly black to the eye. That contrast is a strong pitch moment.

## Rules so we stay honest (judges score "Validity")
- Label every model **"Illustration based on measured values"**, and list which dials are measured, calculated or assumed.
- A brand-new "candidate" gets the class model with a **confidence badge** ("brown-dwarf-like, 70 %"), never a confident portrait.
- If any model or texture is AI-generated: visible watermark (hackathon rule). Code-drawn (procedural) models avoid that.

## How it connects to the Data role
Add an optional `appearance` block to each target in `targets.json` (C1; adding optional fields is allowed). It needs Quirce's OK and a heads-up to Niklas:
```json
"appearance": {"class": "red-dwarf", "temp_K": null, "radius_rsun": null, "visible_hex": null,
  "features": ["starspots", "flares"], "source": {"temp_K": "...", "radius_rsun": "..."}, "confidence": "measured|calculated|assumed"}
```
Values stay `null` until Sean's science notes (D-4) give them with a source. No numbers invented.

## Effort
3D viewer with Three.js and 6 procedural classes: about 6–8 hours for one person. That is an **after-CP2 extra** (Sunday afternoon), unless the team swaps it for something on the cut list. Recommendation: do 3 classes (red dwarf, brown dwarf, Mira) for the 5 targets, and the rest after the hackathon.
