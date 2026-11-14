# Chunk B · discovery engine (`processing/discovery/`)

Input: **I2 stacks** (`stacks.npz` + `stacks.json`, see `contracts/README.md`). Output: **I3 report** (`contracts/report.md`).

```
venv/bin/python -m processing.discovery.scan contracts/fixtures/barnards-star --out report.json   # one zone
venv/bin/python -m processing.discovery.scan <stacks_dir> --offline                              # no catalogue calls
venv/bin/python -m processing.discovery.inject <stacks_dir> --trials 4                           # B8 recovery test
venv/bin/python -m pytest processing/discovery/tests -q                                          # offline tests
```
From the backend (chunk A): `from processing.discovery.scan import scan; report = scan(stacks_dir)`.

Until chunk A serves stacks for every target, `python -m processing.stacks --all` writes I2 stacks for the five
targets from our own frame engine (112×112 px @ 3.075″, D4/D5/D6, visits defined once across bands).

| Task | File | What it does |
|---|---|---|
| B1 | `detect.py` | Background-subtract each band, S/N maps, one detection map per visit (all bands) **plus a red-only pass (D5+D6)** so cold brown dwarfs are not diluted. Saturated cores (NaN holes ringed by bright pixels) become sources flagged `saturated-core`, positioned from the unsaturated bands. |
| B2 | `link.py` | Every pair of detections between anchor visits defines a line; a track needs a detection within tolerance (0.45 FWHM) at ≥ 3 visits. Weighted straight-line fit → motion, error, significance. **Chance lines**: n_pairs × Π(ρ π tol²) over the confirming visits; movers need < 1. |
| B3 | `crossmatch.py` | IRSA TAP: Gaia DR3 (propagated to each epoch), CatWISE2020, AllWISE (with pm), 2MASS (our motion extrapolated back to its date). Names from SIMBAD, or `data/targets.json` when CDS is unreachable. SkyBoT asteroids per visit date for one-off detections. Cached under `processing/cache/catalogs/`. |
| B4 | `classify.py` | Rules (overridable from `science/classes.json` → `discovery_rules`): known-star · known-asteroid · candidate-mover · variable · artefact · unknown-static, with confidence and a one-line reason. `appearance_class` for the 3D library: brown-dwarf (F_ν 4.7 µm / 3.1 µm ≥ 1.5), mira, young-star, red-dwarf (Gaia BP−RP ≥ 2), star, asteroid. |
| B5/B6 | `photometry.py` | Aperture photometry (r = 3 px, annulus 6–10) per band per visit **at the source's position in that visit**, in µJy, empirical errors. Saturated cores fall back to halo light (flagged). Gives `spectrum` and `light_curve`. |
| B7 | `report.py` | I3 JSON + summary text from a rules template; optional **one** Claude call per zone on the numbers only (needs `ANTHROPIC_API_KEY` in the server env; model `claude-opus-5-5`, override with `DISCOVERY_LLM_MODEL`; `DISCOVERY_NO_LLM=1` disables it). |
| B8 | `inject.py` | Injects fake movers (speed, brightness calibrated to the real detection noise) into real stacks and measures recovery. |

## Results on the five targets (`reports/*.json`)
| Target | Class | Appearance | Measured motion | Matched |
|---|---|---|---|---|
| Barnard's Star | known-star | red-dwarf | 10.2″/yr north | Gaia DR3 (10.4″/yr) |
| ε Indi B | known-star | brown-dwarf | 4.0″/yr south-east | Gaia DR3 (4.7″/yr) |
| WISE 0855−0714 | known-star | brown-dwarf | 8.4″/yr west | CatWISE2020 (7.9″/yr) |
| RW Aurigae | variable | young-star | static | ×1.9 in D5 |
| R Draconis | variable | mira | static | ×17 (halo light, saturated core) |

## Known limits (honest list)
- **Baseline ~1 year**: recovery (Barnard field, `reports/recovery-barnards-field.json`) is ~60–80 % for movers ≥ 6″/yr
  (≥ 1 SPHEREx pixel/yr) and low below 4″/yr. Slow movers need the next SPHEREx releases; the context frames
  (2MASS/WISE/NEOWISE, `processing/context.py`) show them by eye meanwhile.
- One-off detections are many in deep fields (R Dra: 18 monthly visits); they are labelled artefact unless SkyBoT
  knows an asteroid there.
- A few faint stars get `variable` from one noisy band next to a bright halo (1 per field in WISE 0855's); the rule
  needs ≥ 2 bands to agree, tune `variable_min_bands` / `variable_min_ratio` in `science/classes.json`.
- Photometry of saturated stars is halo-only and relative.
