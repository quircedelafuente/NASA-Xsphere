# Role 1 · Data: prepare, classify and choose the data — **Yasen + Sean**

**Mission:** be the team's authority on **what SPHEREx data exists, which of it we use and why**. You turn the 5 test
targets into clean, propagated coordinates (C1), an inventory of every SPHEREx exposure that sees them, grouped into
epochs and marked usable/unusable (C2), a plain-English flag dictionary (C3) and verified science facts (C7). Processing
builds frames from your inventory; Niklas builds the story from your facts. **If a number appears in the app or video, it came from you.**

**You own:** `data/` (targets, inventory, flags, science notes, band windows, scripts that produce them).
**You don't touch:** `processing/`, `web/` (ask Quirce/Giorgi/Niklas).

| | Yasen | Sean |
|---|---|---|
| Owns | **D-1 Targets**, **D-2 Inventory**, D-6~ Archival positions/Gaia, release-update script | **D-3 Flags & quality**, **D-4 Science notes**, **D-5 Band & molecule windows** |
| Later (after ~Sat 23:00) | Tour-card texts (U4 content) with Niklas | Submission texts: *NASA data*, *References*, data part of *Detailed description* |
| Together | **D-7**: QA every bundle against expectations before CP2 (is the star where it should be? right epochs? sane flux?) |

---

## 1. What we already know (measured on 14 Nov — see `research/01-data.md`)

| Target | Why it's in the test | pm (″/yr) → px/yr | Ref position / epoch | SPHEREx images | Epochs (survey passes) |
|---|---|---|---|---|---|
| Barnard's Star | fastest-moving star | 10.39 → **1.69** | Gaia DR3 4472832130942575872 @2016.0 | 358 | Aug–Sep 2025 · Mar–May 2026 · Aug–Sep 2026 (**3**) |
| ε Indi B (Ba/Bb) | brown-dwarf pair orbiting a star | 4.68 → **0.76** | Gaia DR3 6412596012146801152 (G=18.0) @2016.0 | 458 | Apr–Jun 2025 · Sep–Nov 2025 · Apr–May 2026 · Sep–Oct 2026 (**4**) |
| WISE 0855−0714 | coldest known brown dwarf | ~8.15 → **1.33** | *not in Gaia* — AllWISE pos @~2010.5 + literature pm (−8118, +680) mas/yr ⚠️ verify | 258 (DR1 only so far) | May 2025 · Oct–Dec 2025 · Apr–May 2026 (**3**) |
| RW Aurigae | young variable star | ~0 (static) | Gaia DR3 @2016.0 | 335 | Sep 2025 · Feb–Mar 2026 · Sep 2026 (**3**) |
| R Draconis | Mira variable (P ≈ 245 d) | ~0 (static) | Gaia DR3 @2016.0 | **2,493** (north ecliptic deep field) | **~monthly** Apr 2025 → Sep 2026 → a real light curve |

Key facts:
- Everything is **public, no login**: SIA `https://irsa.ipac.caltech.edu/SIA`, TAP `https://irsa.ipac.caltech.edu/TAP`, cutouts, S3 bucket `nasa-irsa-spherex`.
- **Releases:** use **DR1** (Surveys 1+2, reprocessed, pipeline R7) + **QR3** (Surveys 3+4, weekly, R7), wide + deep collections:
  `spherex_dr1, spherex_dr1_deep, spherex_qr3, spherex_qr3_deep`. QR1 retired, QR2 not searchable and **must not be mixed** with R7 data.
- Each exposure = one detector file 2040×2040 @ 6.15″/px, ~65 MB. D1+D4, D2+D5, D3+D6 are taken simultaneously.
- **LVF:** wavelength changes along one detector axis; within one survey pass the target is stepped through the 17 channels of each detector (~1 visit per channel per pass).
- **Motion was measured in real data:** Barnard +9.8″ in Dec over 0.99 yr (expected +10.3″); WISE 0855 −7.4″ in RA over 0.985 yr (expected ~−8″). Real, but only 1–2 px.
- **WISE 0855's catalogue position is ~127″ (~20 px) off today** → always propagate (D6).
- **Saturation:** Barnard is OVERFLOW/BLOOM/TRANSIENT in all 168 D1–D3 frames (NaN cores); RW Aur OVERFLOW in 100/101.
- **WISE 0855 is invisible below ~3.8 µm**, S/N 3–5 per exposure in D5/D6, **10–14 per epoch co-add** → co-adding per detector per epoch is mandatory.
- Cutouts: ~8.5 s each, ~1/s in parallel with HTTP 503s, each carries a 3.8 MB PSF table → never fetch live in the demo.

## 2. Scopes

| ID | Scope | Owner | Must/~ | Appetite | Done looks like |
|---|---|---|---|---|---|
| D-1 | **Target catalogue** `data/targets.json` (C1) — Gaia DR3 astrometry (ref epoch 2016.0) or literature for WISE 0855, aliases for search, `kind`, `default_band`, `expected` (motion px/yr, variability, saturated) — + up to 3 bonus targets | Yasen | must | 2 h | Valid C1 JSON for 5 targets, every number with a source in `data/SOURCES.md`. **Mock at H+1, final at H+2.** |
| D-2 | **Coverage inventory** `data/inventory/<id>.json` (C2) via `data/scripts/inventory.py` — SIA on 4 collections at the propagated position, λ at target pixel, on-chip/edge check, flags at target, epoch grouping (D4), usable + reject reason, S3 key + cutout URL | Yasen | must | 4 h | One command regenerates all 5 inventories; Quirce's frame engine reads them without questions. |
| D-3 | **Flag dictionary & quality rules** `data/flags.json` (C3) — read `MSKN/MSKM/MSKD` keys from a FLAGS header; classify hard / soft / info; plain-English text; per-target notes (saturation) | Sean | must | 3 h | Processing uses it as mask; Niklas uses `plain` texts in the legend. |
| D-4 | **Science notes** `data/science-notes.md` (C7) — per target 3–5 facts with sources: what it is, distance, why it moves/varies, which band shows it, what to look for, caveats; plus mission facts (SPHEREx, 102 bands, Pluto blink, Backyard Worlds numbers) | Sean | must | 3 h | Niklas can write the cards, tour and video from it without googling. |
| D-5 | **Band & molecule windows** `data/bands.json` — D1–D6 ranges + `D56`; molecule windows (H₂O 1.4/1.9/3.0 µm, CH₄ 1.6/2.2/3.3, CO₂ 4.27, CO 4.67) with continuum side-bands and plain labels | Sean | must (molecules ~) | 2 h | Processing builds bands from it; Niklas labels chips and the spectrum from it. |
| D-6 | **Archival positions & Gaia field** — per target, past positions (2MASS ~1999, AllWISE ~2010, Gaia 2016) for a "where it was" overlay showing 1–3′ of motion; Gaia DR3 sources in the field for `gaia.json` | Yasen | must-lite (archival list) / ~ (field) | 2 h | `meta.json` can show "in 1999 it was here" — the most convincing motion visual we have. |
| D-7 | **Release update + bundle QA** — re-run inventory for new weeks; check each bundle: target at predicted pixel (±1 px), epochs match inventory, flux sane, flags shown | Yasen + Sean | must | 2 h | QA checklist ticked per target before CP2 (Sun 11:00). |

## 3. Decisions you must take (with recommendation)

| Decision | Options | Recommendation | Class |
|---|---|---|---|
| **Releases / collections** | DR1 only · DR1+QR3 · +QR2 | DR1 + QR3, wide + deep, list in `config.yaml`; **never QR2** | Team-lock D3 |
| **Astrometry source** | SIMBAD J2000 · Gaia DR3 · literature | Gaia DR3 @2016.0; WISE 0855 from AllWISE + literature pm (cite paper); store `ref_epoch` | Team-lock D6 |
| **Epoch grouping** | per exposure · gap > 20 d · gap > 60 d · by month | **One epoch per survey pass**: split on gap > 60 d; if a group spans > 60 d (deep field: R Dra) split it by calendar month. Label with dates + survey number. | Team-lock D4 |
| **Which exposures are usable** | all · strict | Reject: target off-chip or < 5 px from edge, hard-flag at target, FINAST ≠ 0, MISSING_DATA. Keep saturated ones but mark `saturated` (still useful for position). | Consultative (Processing reviews) |
| **Hard vs soft flags** | mosaic-tool mask · own | Start from IRSA's mosaic reject list (TRANSIENT, SUR_ERROR, NONFUNC, DICHROIC, MISSING_DATA, HOT, COLD, PHANMISS, NONLINEAR, PERSIST, CROSSTALK, GHOST×3, STREAK, BLOOM, SNOWBALL, HALO); **OVERFLOW = warning, SOURCE = info** (not bad), OUTLIER = soft | Consultative |
| **Default band per target** | D1…D6 · D56 | Brown dwarfs (WISE 0855, ε Indi B) → `D56`; Barnard → least-saturated band (check D4–D6); RW Aur / R Dra → `D2` for variability + spectrum | Consultative (Niklas: story) |
| **Bonus targets** | none · 1–3 | Only if they make the demo better: e.g. a fast brown dwarf near an ecliptic pole (many epochs), or a known asteroid crossing a deep field. Max 3, after D-1..D-5 are done. | Autonomous |
| **Handoff format** | Data downloads stamps · Processing reads S3 | **Inventory only (C2)**; Processing reads S3 sections itself. Optional: share a stamp cache if you already downloaded cutouts. | Team-lock C2 |
| **R Dra light curve** | ignore · show | Show it: monthly photometry → light curve is the strongest "variable" demo. Agree with Giorgi (P3) that `spectrum.json` points include `mjd` so the UI can plot flux vs time. | Consultative |

## 4. What to research (time-boxed)

1. **Run the spikes first (30 min):** `spikes/sia_coverage_5targets.py` reproduces the coverage table; `spikes/sia/*.ecsv` already contain the full SIA results for all 5 targets (all metadata columns), so you can start D-2 without querying.
2. **SPHEREx Explanatory Supplement** v2.1 (10 Nov 2026) — §1.4 survey/cadence, §2.1 releases, §3.4.3 flags & mosaic mask, §3.4.4/§4.3.2 the 102 channels, saturation limits: https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf
3. Release overview: https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_qr.html · data products: https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products
4. IRSA tutorials, *Data Overview* + *Spectral Image Cutouts*: https://caltech-ipac.github.io/irsa-tutorials/spherex/
5. **WISE 0855 astrometry** (not in Gaia): find the best published position + pm + parallax (e.g. Luhman 2014; Luhman & Esplin 2016 https://arxiv.org/pdf/1605.08620; CatWISE2020 splits it into several detections). Pick one, cite it, set `ref_epoch` correctly.
6. Gaia DR3 via ESA TAP `https://gea.esac.esa.int/tap-server/tap` or IRSA TAP `gaia_dr3_source` (SIMBAD TAP returned 404 from our server; Sesame name resolver works).
7. Archival positions: IRSA TAP `allwise_p3as_psd`, `catwise_2020` (has pm), 2MASS PSC; unWISE/AllWISE HiPS on CDS for context images.
8. Science facts for C7 (cite each): Barnard's Star (distance ~1.83 pc, fastest pm), ε Indi B (T1+T6 brown-dwarf binary ~3.6 pc), WISE 0855 (~250 K, ~2.3 pc), RW Aur (young T Tauri binary with dimming events), R Dra (Mira, ~245 d). Mission/story: SPHEREx facts (JPL), Pluto 1930 blink (Britannica), Backyard Worlds 3,006 L/T candidates (arXiv 2604.01323), SPHEREx 6,003 ultracool dwarf spectra (arXiv 2604.22012).

## 5. Outputs & deadlines (H0 = kick-off ≈ Sat 15:00)

| When | Output | For |
|---|---|---|
| H+1 | `data/targets.json` (C1) for 5 targets (may be rough) + `config.yaml` collections | Quirce, Niklas |
| H+2 | Inventory C2 for Barnard + WISE 0855; `flags.json` C3 draft | Quirce (frame engine), Niklas (legend) |
| H+3 | Inventory for all 5; `bands.json`; first science notes | Processing, Niklas |
| CP1 (Sat 21:00) | Science notes complete; archival positions; QA of the first Barnard bundle | Niklas (cards/tour), Quirce |
| Sat 23:00 | Tour-card texts (Yasen) + submission data texts (Sean) drafted | Niklas |
| CP2 (Sun 11:00) | QA checklist ticked for all 5 bundles | Team |
| Sun 18:00 | Final *NASA data* + *References* lists | Submission |

## 6. Dependencies & contracts

**You provide:** C1 targets, C2 inventory, C3 flags, C7 science notes, `bands.json`, archival positions → Processing and Product.
**You consume:** almost nothing — you're upstream. You need from Processing: feedback on unusable exposures; from Niklas: the list of facts/numbers he needs (H+3).
**First independent slice:** `targets.json` from Gaia/literature — no waiting on anyone.
**Rule:** if you change a field name in C1–C3, tell Quirce and Niklas first (Team-lock).

## 7. Rabbit holes (avoid)
- Writing your own mosaicking or "proper" photometry (IRSA's Spectrophotometry Tool exists — link to it).
- Downloading full frames (17–165 GB per target). Use the SIA tables you already have + S3 sections.
- Mixing QR2 with DR1/QR3.
- Using J2000/2010 positions for movers (WISE 0855 is 2′ off).
- Treating `SOURCE` as bad (it only means "a known source is here").
- Over-polishing bonus targets before the 5 required ones are QA'd.
- Spending hours on CORS: the browser never calls NASA directly; the backend does (D2: on-demand + cache).
