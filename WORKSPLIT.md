# Work split: three independent chunks → one MVP (14 Nov 2026)

**Goal:** three people build three parts **at the same time, each with their own AI agent, without waiting for each other**. Each part has its own folder, its own input files (already in the repo as real samples), and a fixed output format. When all three are done, we merge, run the end-to-end test, then all work on the frontend together.

| Chunk | Who | Size | Folder (only you write here) | Branch |
|---|---|---|---|---|
| **A · On-demand engine + 3D library** | **Yasen** (Max plan) | **largest** | `backend/`, `data/`, `web/lib3d/` | `a/...` |
| **B · Discovery engine** (find movers, classify) | **Quirce** (Max plan) | **large** | `processing/` | `b/...` |
| **C · Science layer** (flags, molecules, templates, texts) | **Sean** (Pro plan) | **small** | `science/` | `c/...` |

Giorgi and Niklas: Giorgi pairs with Quirce on B (light curves B6 + spectra B5 are a clean split). Niklas starts the frontend design against the API mock (`contracts/api.md`) and owns the frontend phase. *(Assumption: confirm in chat.)*

Shared folder `contracts/` = the formats between chunks. **Change a contract only by telling the other two first.**

---

## How the app gets data (decision D2, now: on-demand)
NASA data is pulled **only when a user asks** for it:
1. **Searches a known object** by name (fuzzy: "barnard" → Barnard's Star) → name resolver → coordinates.
2. **Types coordinates.**
3. **Draws a zone** on the sky map (box, max ~30′ × 30′ for the MVP) → **autonomous scan for movement**.

Before that, the user only sees the **sky map**, made of NASA's all-sky SPHEREx tiles (HiPS, loaded by the browser, no compute on our side). When they zoom in on an area, we **start fetching quietly** (prefetch), so the wait feels shorter.

**After the request** (backend, chunk A):
query SPHEREx image list (SIA/TAP, 1–30 s) → fetch only the pixels needed (S3 byte ranges or cutouts, ≤ 4 at a time, retries) → align all photos to one grid → merge per detector per visit → stream visit 1 to the screen first, then the rest → **cache** the result. The next user asking for the same spot gets it instantly. The weekly NASA release only adds new visits.
**The 5 test targets are pre-warmed in the cache**, so judges never wait (that replaces the old "100 % static" rule).
Typical wait for a new spot: **20–60 s** (measured: list 4 s; one cutout 8–22 s; parallel ≤ 4). During the wait we show progress and the "What am I seeing?" explainer.

## How we discover unknown objects (zone scan, chunk B)
1. **Merge** photos per detector and visit (chunk A delivers this as `stacks`).
2. **Find every dot** in every merged image (source detection).
3. **Link dots across visits.** A dot whose position shifts in a straight line across ≥ 3 visits is a **mover**. Count how many chance lines a random field would give; keep a candidate only if fewer than 1 chance line is expected.
4. **Cross-check catalogues:** Gaia DR3, SIMBAD, AllWISE/CatWISE, 2MASS (each at its own date), and known asteroids at each photo's date (SkyBoT / IRSA Moving Object Search Tool).
5. **Measure its spectrum** (brightness vs wavelength, 0.75–5 µm) and **brightness over time**.
6. **Classify** with rules (chunk C supplies the rules as data): known star ✓ · known asteroid ✓ · **unknown mover → candidate** (brown-dwarf-like if dark at 3.3 µm methane and bright at 4–5 µm) · variable · artefact (seen once, on a flagged pixel).
7. **Report:** "Zone scanned: 41 sources. 33 known stars, 2 known asteroids, 1 variable, 4 artefacts, **1 unknown mover (brown-dwarf-like, 70 %)**", each with a dossier. Always "candidate", never "discovery".

**AI or no AI:** the MVP is **rules only**, which are free, explainable and fast. **Optional: one LLM API**, called **once per zone report** (not per frame), on the numbers, not the pictures. It writes the plain-English summary and gives a second opinion on ambiguous candidates. A teammate's DeepSeek key, or Claude Haiku; the key lives only in the server's environment, never in the repo or browser. Results are cached, so the same zone never costs twice.

---

## Contracts (in `contracts/`)
| Id | From → To | What | Sample in repo |
|---|---|---|---|
| **I1 api.md** | A → frontend, B | HTTP API: `/resolve`, `/view`, `/scan`, `/object/{id}` (shapes below) | mock JSON in `contracts/api.md` |
| **I2 stacks** | A → B | `stacks.npz` (float32 `img[band, visit, y, x]`, `n[band, visit]`) + `stacks.json` (grid WCS, visits with MJD, λ per band, spectrum points) | **`contracts/fixtures/barnards-star/`: real SPHEREx data**, 3 bands × 3 visits, 56×56 px @ 3.075″ |
| **I3 report** | B → A, frontend, 3D | Scan/object report: sources with positions per visit, motion, flux per band, class, confidence, reasons, cross-matches | example in `contracts/report.md` |
| **I4 science** | C → B, frontend, 3D | `science/flags.json`, `science/bands.json` (molecule windows), `science/classes.json` (spectral templates + rules + 3D appearance per class), `science/notes/*.md` | stubs in `contracts/science.md` |
| **I5 lib3d** | A → frontend | `renderObject(el, {cls, temp_K, radius_rsun, ...})` | `data/yasen-proposals/sample-3d/` (Barnard demo) |

### I1 API shapes (MVP)
```
GET  /resolve?q=barnard            → {"matches":[{"name":"Barnard's Star","ra_deg":269.448,"dec_deg":4.739,"source":"targets.json|Sesame"}]}
POST /view   {"ra_deg","dec_deg","fov_arcmin":3,"bands":["D4","D5","D6"]}   → {"job":"v_ab12"}
GET  /view/v_ab12                  → {"status":"fetching|merging|done","progress":0.4,"visits":[...],"frames_png":{...},"stacks_url":"/files/v_ab12/stacks.npz"}
POST /scan   {"box":{"ra_deg","dec_deg","w_arcmin","h_arcmin"}} → {"job":"s_cd34"}
GET  /scan/s_cd34                  → I3 report + {"status","progress"}
GET  /object/barnards-star         → targets.json entry + latest report + science notes
```

---

## Chunk A · Yasen · on-demand engine + 3D library (largest)
**Paste into your agent:** *"Read WORKSPLIT.md, CONTRACTS.md, contracts/, research/01-data.md and spikes/. Build chunk A in `backend/` and `data/` only."*
| # | Task | Done when |
|---|---|---|
| A1 | `data/targets.json` (C1) + `SOURCES.md` + `data/scripts/targets.py` | ✅ done (live Gaia/AllWISE/2MASS queries, self-checked) |
| A2 | **Resolver**: name (fuzzy, aliases, Sesame fallback) or coordinates (decimal or sexagesimal) → ra/dec | `/resolve` passes 20 test strings |
| A3 | **Inventory on demand**: SIA/TAP on the 4 collections (config.yaml) for a point or box; λ at target pixel; usable/reject with Sean's flags | Matches the spike counts for the 5 targets |
| A4 | **Fetcher**: S3 byte-range sections (fallback: cutout service), ≤ 4 parallel, retries on "busy", disk cache keyed by (exposure, box) | Barnard full fetch < 3 min cold, < 1 s warm |
| A5 | **Merger**: reproject to one TAN grid, median per band × visit, masks → **writes I2 stacks** + PNG frames | Output identical in shape to the fixture |
| A6 | **API server** (FastAPI): I1 endpoints, background jobs, progress, streaming visit-by-visit | Frontend mock replaced by real calls |
| A7 | **Cache + pre-warm**: the 5 targets pre-computed at deploy; weekly watcher appends new visits | Second request for a spot is instant |
| A8 | **3D library** (`web/lib3d/`): class-based models (red dwarf, brown dwarf, Mira giant, young star + disk, asteroid, comet), dials from I4 `classes.json` + measured values | 5 targets render; Barnard matches the demo |
| A9 | **MCP server**: same functions as tools (`resolve`, `view`, `scan`, `object`) | Claude can answer "scan around WISE 0855" |
| A10 | **Integration**: merge the three branches, end-to-end on Barnard then the other 4 | One command runs the whole pipeline |

## Chunk B · Quirce · discovery engine (large)
**Paste into your agent:** *"Read WORKSPLIT.md, contracts/, research/02-processing.md and spikes/. Build chunk B in `processing/` only. Develop against `contracts/fixtures/barnards-star/` (real SPHEREx stacks)."*
| # | Task | Done when |
|---|---|---|
| B1 | **Source detection** on each stack (band × visit), with masks | Finds Barnard + field stars in the fixture |
| B2 | **Linking + motion fit** across visits; chance-line estimate; keep < 1 expected | Barnard: ~10″/yr north, measured 9.8″ over 0.98 yr ✓ |
| B3 | **Cross-match**: Gaia DR3, SIMBAD, AllWISE/CatWISE, 2MASS (each at its epoch), SkyBoT asteroids per date | Barnard tagged "known star ✓" |
| B4 | **Classifier** (rules from `science/classes.json`) → class, confidence, one-line reason | 5 targets get the right class |
| B5 | **Spectrum along the path** (flux per band per visit at the moved position) | Matches the fixture's spectrum points |
| B6 | **Light curve** per source (flux per visit); variability flag | R Dra shows its cycle (when A delivers its stacks) |
| B7 | **Zone report** (I3) + optional single LLM summary call (key from env) | Report JSON validates against `contracts/report.md` |
| B8 | Tests on synthetic injected movers (known speed) → recovery rate | Recovers ≥ 1 px/yr movers in the fixture field |

## Chunk C · Sean · science layer (small)
**Paste into your agent:** *"Read WORKSPLIT.md, contracts/science.md, research/01-data.md and the SPHEREx Explanatory Supplement. Build chunk C in `science/` only. Every number needs a citation."*
| # | Task | Done when |
|---|---|---|
| C1 | `science/flags.json`: flag bits → hard / soft / info + plain-English text (C3) | Bits read from a real FLAGS header |
| C2 | `science/bands.json`: molecule windows (water ice ~3.0, CH₄/PAH ~3.3, CO₂ ~4.27, CO ~4.67 µm) with citations | Used by the colour-slider presets |
| C3 | `science/classes.json`: per class: spectral-shape rules (which bands dip or rise), typical temperature/size ranges, and the 3D appearance dials | B4 and A8 read it without questions |
| C4 | `science/notes/<target>.md`: 3–5 cited facts per test target + the numbers still marked "verify" in targets.json (WISE 0855 pm/parallax; Barnard's planets) | Every number in the app has a source |

---

## How we merge
1. Everyone works on their own branch, **only in their folder**. Pull `main` often; never edit another chunk's folder.
2. When a chunk's "done when" boxes are ticked, open a PR. Yasen merges into `integration`, runs `A10`.
3. All green → `main`. Then **everyone switches to the frontend** (Niklas leads) and to fixing gaps found in integration.

**Timeline:** chunks done by **Sun 10:00** → integration by **12:00** → frontend + video until **22:00** (submission).
