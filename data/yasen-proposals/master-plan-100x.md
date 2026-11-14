# SPHEREx Blink (working name): the plan for a 100× better WiseView
*14 Nov 2026 · Data role draft for the team · numbers marked ⚠ are unverified*

## 0. In one sentence
WiseView answers **"does it move?"**. We answer **"does it move, what is it, what is it made of, how hot is it, how far is it, has anyone seen it before, and what does it look like?"** We do it in seconds, for anyone, on data that grows every week.

## 1. What "100×" means: ten axes, each measurable
| # | Axis | WiseView today | Ours | Factor |
|---|---|---|---|---|
| 1 | Colours per object | 2 (W1, W2) | **102** (0.75–5 µm) | ~50× |
| 2 | What you learn | It moves | Moves **+ type + molecules + temperature + distance + known/unknown** | 6 answers vs 1 |
| 3 | Time scales | Yearly stacks | **Hours–days** (photos inside one visit) → **months** (deep fields) → **15 years** (WISE + SPHEREx) | 3 scales vs 1 |
| 4 | Freshness | Archive (WISE ended 2024) | **Weekly** new data, automatic | live vs frozen |
| 5 | Who can use it | Trained volunteers | **Anyone**: plain language, guided tours, phone | audience ×10+ |
| 6 | Time to a verdict | Minutes of manual checking in other tools | **Seconds**: auto cross-check (Gaia, WISE, SIMBAD, asteroids) | ~20× faster |
| 7 | Seeing the object | Grey dots | Dots + **3D model from measured values** + 3D map | new |
| 8 | Solar System | Not a focus | **Asteroid and comet mode** with known-object overlay and comet spectra | new |
| 9 | Asking questions | Clicks only | **Plain-English questions** through Claude + our MCP server | new |
| 10 | Sharing and teaching | Link | **Embeddable link**, guided story per object, classroom mode | new |

"100×" is the pitch line. The table is the proof behind it. Judges can check each row.

## 2. The data: every piece we use, and for what
### SPHEREx (IRSA, public, no login)
| Product | What it is | Our use |
|---|---|---|
| **Spectral images** DR1 + QR3, wide + deep | Every exposure, 6 detectors, each pixel at its own wavelength (LVF) | Blink, difference, photometry, spectra, fast movers |
| **Deep fields** (ecliptic poles) | Visited about monthly | Light curves, many-epoch motion (R Draconis: 2,493 images) |
| **All-sky cube (HiPS, 102 layers)** | Whole-sky map, one layer per colour | The 3D/2D sky map background, the "colour slider" anywhere |
| **Spectrophotometry Tool** | Calibrated spectrum of a point | Precise spectra (instead of our quick sums) for the 5 targets |
| **Source Discovery Tool** | Finds sources in a region from SPHEREx alone | Seeds for "Find everything" |
| **SPLICES** (ice sources catalogue) | Targets rich in ices | "Ice explorer" showcase |
| **Moving Object Search Tool** | Photos where a named asteroid/comet should be | Solar System mode |
| **Comet 3I/ATLAS spectral images** | Interstellar comet | Showcase: "what an interstellar visitor is made of" |
| **AWS S3 copy** | Same files, byte-range reads | Fast fetching for the engine (0.5–2.5 s vs 8+ s) |

### Companions
| Source | Use |
|---|---|
| **Gaia DR3** | Exact positions, motions, distances: predicted track, "known star ✓", 3D map |
| **AllWISE / unWISE / CatWISE2020 / NEOWISE** | 2010–2024 images and positions: the **15-year blink**, slow-mover proof |
| **2MASS** | 1998–2001 positions: "where it was 25 years ago" |
| **SIMBAD / Sesame** | Names → coordinates, known object types |
| **SkyBoT / JPL Horizons** | Known asteroids and comets at each photo's date |

## 3. The product: ten pillars
Each pillar: **what the user does → what SPHEREx unlocks → how we build it → hackathon tier** (A = must, B = should, C = after).

### P1 · Blink, done right (WiseView parity, then past it) · **A**
- User types a name, coordinates or clicks the map. It auto-plays at ≤ 2 Hz (safe for photosensitivity).
- Photos are merged **per detector, per visit** (each SPHEREx photo is a different colour, so a raw blink flickers from colour, not motion).
- Modes: **Blink · Changes only** (difference) **· Side by side · Trail** (brightest value per pixel: a mover draws a dotted path).
- Overlays: Gaia-predicted crosshair and path, archival positions (2MASS, WISE), scale bar, north arrow.
- Field of view presets (2′ / 5′ / 10′), contrast slider, zoom ×8 nearest-neighbour.
- URL holds the state (`?ra=&dec=&band=&mode=`): embeddable.
- *Status:* our sample already does merge, blink, difference, side by side, track, bands, link.

### P2 · The colour slider: 102 colours as a movie · **A**
- On a still patch of sky, slide through wavelength 0.75 → 5 µm. Objects that change brightness with colour pop out.
- **Molecule presets:** water ice ~3.0 µm, methane / PAH ~3.3 µm, CO₂ ~4.27 µm, CO ~4.67 µm. One click jumps to "with vs without this molecule" and shows the difference.
- **Make-your-own-colour picture:** pick any 3 wavelengths for red/green/blue.
- Built from the all-sky cube (anywhere) or our merged frames (5 targets).

### P3 · "What is it?": the spectrum classifier · **A (rules) / C (model)**
- Each source's spectrum compared with simple templates: **ordinary star** (smooth, temperature from slope), **brown dwarf** (dark at 3.3 µm methane, bright at 4–5 µm), **asteroid** (sunlight + heat rise at long wavelengths), **galaxy**, **ice-rich**.
- Output: **label + confidence + the reason in one sentence** ("dark at 3.3 µm, a sign of methane, typical of cold brown dwarfs").
- Combined with motion: *moves + brown-dwarf spectrum + not in Gaia* = **top candidate**.
- Hackathon: rules on 3–4 features. Later: a small model trained on thousands of SIMBAD-labelled objects.

### P4 · Time machine: 15 years in one blink · **B**
- Frames: 2MASS (≈2000) → WISE (2010) → NEOWISE years → SPHEREx 2025–26, all on one grid.
- Slow movers become obvious (Barnard's Star moved ≈ 2.7′ since 2010 ⚠ my estimate).
- Uses archival images on CDS HiPS (2MASS, AllWISE): same "cutout around a point" pattern.

### P5 · Light curves: things that change · **B**
- Per-visit brightness at a fixed colour, drawn over time. Deep-field targets get monthly points.
- R Draconis: a full brightening/fading cycle (period ≈ 245 days). RW Aurigae: dimming events.
- Flags "variable" in the classifier when change > noise.

### P6 · Solar System mode · **B**
- Blink **inside one visit** (photos hours–days apart): asteroids streak; stars don't.
- Known asteroids/comets drawn at each photo's date (SkyBoT); a candidate sitting on one says so.
- Comet showcase: 3I/ATLAS spectra → "what an interstellar comet is made of".

### P7 · 3D: the object and its neighbourhood · **B (object) / C (map)**
- **Object view:** class-based 3D model whose dials come from data (temperature → colour, size from temperature + brightness + distance). **Human eye ↔ SPHEREx infrared** switch. Flares, spots, bands, disks, pulsation by class. *Sample done: Barnard's Star.*
- **3D neighbourhood map:** Gaia distances place every nearby star in 3D. Fly from the Sun to the object, with its motion arrow.
- Every model labelled "Illustration based on measured values", each number tagged measured / calculated / estimated.

### P8 · Discover and contribute · **C**
- "Flag a candidate" button → candidate inbox with a **dossier** (frames, motion, spectrum, cross-matches, what to check next).
- Community confirmations (Backyard Worlds-style voting). Later, a hand-off to the Backyard Worlds / Zooniverse teams.
- Language rule: always **"candidate"**, never "discovery".

### P9 · For everyone: access and learning · **A**
- **"What am I seeing?"** panel in plain language, on every view.
- **Guided tours** of the 5 targets (≈ 60 s each): the story, then "now you try".
- Accessibility: blink ≤ 2 Hz, reduced-motion = paused side-by-side, colour-blind-safe ramps, keyboard use, text alternative for motion, phone layout.
- Languages: English first. Spanish and Bulgarian later (our team speaks them).

### P10 · Ask the sky (Claude + MCP) · **C (demo in pitch if time)**
- A small MCP server exposes the engine: `find_images`, `get_frames`, `spectrum`, `classify`, `gaia_nearby`.
- "Show me brown-dwarf-like movers within 2° of Orion" → Claude runs the tools and answers with frames.
- Same functions power the website: one engine, two doors.

## 4. How it runs (architecture)
```
Weekly watcher ─► Fetcher (S3 byte ranges, ≤4 parallel, cache) ─► Processor (merge, diff, photometry, spectra)
      │                                                                    │
  new photos?                                           Classifier (rules → later model)
      ▼                                                                    ▼
  Inventory (C2, append-only)                      Bundles (C4): PNG frames + JSON, ~60 KB per object
                                                                           │
                                       Static site on CDN (Vercel)  ◄──────┘
                                       + on-demand server for any typed position (cache: 2nd visitor instant)
                                       + MCP server (same functions)
```
- **Data budget:** raw photos 17–165 GB per object → cutouts ~400 MB → **what the browser loads ≈ 60 KB** (our sample: 58 KB from 108 cutouts).
- **All-sky browsing** uses NASA's HiPS cube directly (⚠ check that IRSA's HiPS server allows other websites to load it; if not, proxy it).
- **Demo safety:** the 5 targets are precomputed. Judging never waits on NASA's servers.

## 5. Proving it works (science checks, the "Validity" score)
| Target | What must be true | Check |
|---|---|---|
| Barnard's Star | Moves ~10.4″/yr (~1.7 px), mostly north | ✅ sample: 9.8″ over 0.98 yr vs 10.2″ expected |
| WISE 0855 | Only visible at 3.8–5 µm after merging; moves ~8″/yr; brown-dwarf spectrum | Merge D5/D6 per visit; classifier says "brown-dwarf-like" |
| ε Indi Ba/Bb | Pair moving together, ~0.8 px/yr; brown-dwarf spectra | Co-moving check; classifier |
| RW Aurigae | Static, varies | Light curve shows change > noise |
| R Draconis | Static, ~245-day cycle | Monthly light curve shows the cycle |
| Any known asteroid in a field | Matches SkyBoT at each date | Overlay agrees |

Every number shown to users traces to a source (Data role, `SOURCES.md`).

## 6. Roadmap
### Hackathon (now → Sun 22:00), in the team's existing roles
| When | Data (Yasen, Sean) | Processing (Quirce, Giorgi) | Product (Niklas) |
|---|---|---|---|
| Sat → CP1 21:00 | targets.json, inventories, flags, science notes | Merge + blink + difference bundles for 5 targets | Viewer shell, P9 panel, tours outline |
| Sat night | Spectrum-classifier rules (P3), tour texts | Spectra per target, colour slider frames (P2) | Colour slider UI, 3D object view (reuse sample) |
| Sun → CP2 11:00 | QA all 5 bundles against §5 | Light curve R Dra (P5), WISE frames (P4) if green | Polish, accessibility, phone |
| Sun → 22:00 | NASA data + references texts | Freeze | 30-s video, submission page |
**Cut order if late:** P4 → P5 → 3D object → colour slider presets. Never cut: P1, P9, the 5 targets.

### After the hackathon
- **Weeks:** any-position on-demand server, weekly watcher live, P6 Solar System mode, 3D neighbourhood map, Spanish/Bulgarian.
- **Months:** trained classifier, candidate inbox + community voting (P8), MCP "ask the sky" public, partnership pitch to Backyard Worlds.

## 7. How we know it's working
- Time from typing a name to the first moving frame: **< 3 s** (precomputed), **< 30 s** (new position).
- A non-expert explains what they saw after 60 s: test on 5 classmates.
- Classifier on known objects: correct type on ≥ 80 % of a labelled test set ⚠ target, not yet measured.
- All 5 test targets pass §5.

## 8. Risks and answers
| Risk | Answer |
|---|---|
| NASA servers slow or busy | Precompute; ≤ 4 parallel requests; S3 reads; cache |
| Prior art (SPHEREx-Blink-3.0, MIT, built before the event) | Our edge is P2, P3, P7, P9 + story. Check Space Apps rules before reusing any of its code |
| Overclaiming ("discovery", fake-precise 3D) | "Candidate" wording; measured / calculated / estimated tags on every number |
| Saturated bright stars (Barnard, RW Aur) | Use D4–D6, white-fill cores, rely on position more than brightness |
| Few visits (3–4) | Design sparse states; intra-visit blink; deep fields; WISE time machine |
| Scope creep | The cut order above; tiers A/B/C |

## 9. Decisions for the team (each with a recommendation) · Yasen: yes to all four, 14 Nov; team to confirm
1. Adopt tiers A/B/C as above. **Recommend yes.**
2. Hackathon extras = P2 colour slider + P3 "What is it?" + P7 3D object. **Recommend yes** (the three things WiseView can't do).
3. P4 time machine only if CP2 is green. **Recommend yes.**
4. Product name: Niklas's call by H+2 (working name "SPHEREx Blink").

## 10. Added from the team discussion (14 Nov, kick-off)
| Idea from the discussion | Where it goes | Note |
|---|---|---|
| **Map first:** the user sees a sky map, zooms in, and only then does the tool download from NASA | D2 → on-demand (WORKSPLIT.md), P1 | Sky map = NASA's all-sky tiles, no compute on our side |
| **Start downloading while the user zooms in** (prefetch) | Chunk A (A4/A6) | Cuts the 20–60 s wait |
| **Use the 20–30 s wait** (progress, explainer, fun facts) | P9 | Was joked as "ads"; use it for learning instead |
| **Draw a square → autonomous movement scan → report** ("33 stars, 12 comets, 1 unknown") | P3 + zone scan (chunk B) | Max ~30′ × 30′ for the MVP |
| **Fuzzy name search** ("closest match to what you typed") | Chunk A2 resolver | Aliases + Sesame fallback |
| **Like the forest-health tool:** select an area → pull past images → heat map | Zone scan output can include a **change heat map** | Cheap add-on to the difference image |
| **One cheap LLM API** (teammate has a DeepSeek key), not called in real time per view | Zone report (B7) | Once per zone, cached; key only on the server |
| **3D model library by class**, picked by what the object is likely to be | Chunk A8 + C3 `classes.json` | Not generated from the image itself |
| **Comet: render from data** (size guessed from brightness) | A8 class "comet" | Labelled illustration |
| **AI photo enhancement** (e.g. upscaling) | **Not on science images.** Only in the 3D/illustration layer, watermarked | Enhancement invents detail; judges score Validity, and Space Apps requires AI images to be watermarked |
| **Package as a tool others can plug in:** own API + MCP, deploy-ready | A6 API + A9 MCP; embeddable view by URL | Deploy-ready without paying to host everyone's compute |
| **Keep up to date weekly** | A7 watcher | Appends new visits only |
| **Don't store raw data**, only processed results | A4/A7 cache | Matches the data-budget numbers in §4 |
| **Start with one part, test, then grow** | WORKSPLIT: fixture-first, Barnard end-to-end first | |
| **Align all photos to the same orientation** before comparing | A5 merger (reprojection) | Done in our sample |
| **Object type: known objects from catalogues, unknown ones inferred** | B3 cross-match + B4 classifier | |
| **Python for data + AI** | D10 already | |
| **Cloud credits are limited** | Work split by plan size (WORKSPLIT.md) | |
