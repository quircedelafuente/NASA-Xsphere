# Role 2 · Processing, algorithm & bridge to the frontend — **Quirce + Giorgi**

**Mission:** turn the list of SPHEREx exposures that Data hands you (C2) into **wavelength-matched, aligned, consistently
stretched frames per epoch** (plus difference images, a predicted track, Gaia overlay and a spectrum), packaged as
**bundles (C4)** — and make them render in the browser through the **viewer component (C6)** that Niklas builds the UI around.

**You own:** `processing/`, `web/public/bundles/`, `web/src/viewer/`, `web/src/data/`, `config.yaml` (Quirce).
**You don't touch:** `data/` (ask Yasen/Sean), `web/src/ui|pages|styles/` (ask Niklas).

| | Quirce | Giorgi |
|---|---|---|
| Owns | **P1 Frame engine**, **P4 Precompute & publish**, decider for the team | **P2 Diff + track + Gaia**, **P3 Spectrum**, **P5 Viewer component** |
| Buddy for | Giorgi on P2 (same grid code) | Quirce on P1 (reviews stretch/flicker) |

---

## 1. Scopes (what "done" looks like)

| ID | Scope | Owner | Must/~ | Appetite | Done looks like |
|---|---|---|---|---|---|
| P0 | **Spike / thin slice** — Barnard's Star, band `D56`, 3 epochs → 3 PNG frames you can blink locally | Quirce | must | 3 h (H0–H3) | 3 PNGs where the star sits at the predicted pixel each epoch and visibly shifts ~1–2 px. Uses `spikes/` scripts. |
| P1 | **Frame engine** `processing/frames.py`: exposures (C2) → per-epoch co-add per band window on the common grid (D7) → `.f32` + `.png` + mask + manifest (C4) | Quirce | must | 6 h | `python -m processing.frames --target barnards-star --band D56` writes a valid C4 folder; all frames same grid & stretch. |
| P2 | **Difference, track & Gaia** `processing/motion.py`: sigma-difference frames, `target_track` from pm, `gaia.json` for the field; `~` shift-and-add at the target pm | Giorgi | must (`~` shift-add) | 4 h | Diff frame of Barnard shows a dipole at the track; Gaia sources line up with stars. |
| P3 | **Spectrum + light curve** `processing/spectrum.py`: aperture photometry per exposure at the propagated position → `spectrum.json` (points carry `mjd`/`epoch`, so the same file gives a light curve) | Giorgi | must | 3 h | R Dra / WISE 0855 spectrum plotted 0.75–5 µm, points coloured by epoch, flagged points marked; R Dra light curve shows the Mira cycle. |
| P4 | **Precompute & publish** `processing/precompute.py`: runs P1–P3 for every target in C1 × bands → `web/public/bundles/` + `index.json`; re-runnable for a new release | Quirce | must | 2 h | One command rebuilds all bundles; committed; site loads them from Vercel. |
| P5 | **Viewer component** (C6) `web/src/viewer/BlinkCanvas.tsx` + `web/src/data/load.ts`: load `.f32`, client-side asinh stretch, nearest-neighbour zoom, blink/diff/side modes, crosshair, track, Gaia & flag overlays, pixel→RA/Dec on click | Giorgi | must | 6 h | Niklas can drop `<BlinkCanvas>` into his page with a real manifest and it works at 60 fps on a laptop. |
| P6 | `~` **Live API** `processing/api.py` (FastAPI): same JSON as C4 for arbitrary RA/Dec, job + polling, disk cache | Quirce | ~ | 4 h | `/api/frames?ra&dec` returns a C4 manifest for a new position in < 2 min. |
| P7 | `~` **Spectral cube / λ slider**: `cube.json` + `cube_u8.bin` (64×64×N λ, uint8) and a `<CubeSlider>` (2D image + λ slider). 3D volume only if everything else is done. | Giorgi | ~ | 4 h | Sliding through λ on WISE 0855 shows it appear only at > 3.8 µm. |
| P8 | `~` **Molecule filters**: line/continuum maps (CH₄ 3.3, H₂O 3.0, CO₂ 4.27, CO 4.67 µm…) as extra band ids | Quirce | ~ | 3 h | `mol-ch4` band renders with a meaningful contrast on a brown dwarf. |

Appetite = the maximum time we're willing to spend; if a scope hits it, cut or simplify, don't extend.

## 2. The pipeline (reference design — you may change details, not the contracts)

```
C1 target (ref_epoch, pm) ─┐
C2 exposures (S3 url, det, mjd, lam_um, usable) ─┴─►
 for each usable exposure in band window:
   1. open S3 with fsspec, read only a section around the target  (astropy fits.open(url, use_fsspec=True).section)
   2. position = target.apply_space_motion(MJD-AVG)  → pixel via IMAGE WCS (watch the SIP "-SIP" ctype warning)
   3. IMAGE - ZODI ; residual background (sep / photutils Background2D, bw 16–32 px)
   4. hard-mask bits (C3) → NaN ; soft bits → mask layer
   5. reproject_interp (bilinear) onto the common grid (D7)
 group by epoch (C2 epoch id) → inverse-variance co-add (w = 1/VAR, 0 where masked; clipped mean if N≥5) + nhits
 sequence stretch: vmin/vmax = 0.5/99.5 percentile over ALL frames → asinh(a)          (D8)
 diff(Ej−Ei) / sqrt(err_i²+err_j²)  → sigma units, diverging colormap in the viewer
 export: .f32 (north-up, top row first), .png, mask.png, manifest.json                (C4)
```
Measured numbers to plan with (see `research/01-data.md` and `research/02-processing.md`): 3–4 epochs per target (R Dra ~monthly, deep field); WISE 0855 needs the per-epoch co-add (S/N 3–5 per exposure → 10–14 per epoch, only in D5/D6); S3 section read 0.5–2.5 s
per exposure vs 8.6 s via the cutout service; `reproject_interp` 64² ≈ 10 ms; Barnard moves ~1.7 px DR1→QR3,
WISE 0855 ~1.3 px, ε Indi B < 1 px; bright targets are saturated (NaN cores, OVERFLOW/BLOOM flags).

## 3. Decisions you must take

| Decision | Options | Recommendation | Class |
|---|---|---|---|
| Band windows per target | per detector / D56 / per channel | `D56` default for brown dwarfs, per-detector chips for all; **never mixed λ** | Team-lock D5 |
| Epoch grouping | per exposure / per pass | per pass (gap > 60 d) + optional raw mode | Team-lock D4 |
| Data access | IRSA cutout / S3 section / full download | S3 section + retry/backoff, cutout as fallback | Consultative D11 |
| Grid & pixel size | native 6.15″ / 3″ supersampled | native 6.15″, 64×64, NN upscale in the browser | Team-lock D7 |
| Reprojection | interp / adaptive / exact | `reproject_interp(order='bilinear')` for display; photometry in native pixels | Autonomous |
| Co-add | mean / median / inverse-variance | inverse-variance + σ-clip when N ≥ 5 | Autonomous |
| Which flags are hard vs soft | — | take C3 from Data; propose changes to them | Consultative |
| Stretch | per frame / per sequence | per sequence asinh, client re-stretch | Team-lock D8 |
| Diff method | plain / sigma / PSF-matched | sigma diff; **no PSF matching** (D14) | Autonomous |
| Spectrum method | aperture / PSF forced | aperture r≈2 px + annulus, per exposure; link to IRSA's tool for science-grade | Autonomous |
| Delivery format | PNG only / float32 + PNG | float32 for viewer + PNG previews | Team-lock C4 |
| Saturated targets | show anyway / warn / switch band | show + `warnings:["saturated core"]` + suggest D56/diff | Consultative with Niklas |
| Live mode | none / FastAPI on VPS | only after all 5 bundles are done (`~`) | Team-lock D2 |
| Viewer rendering | canvas 2D / WebGL | canvas 2D `ImageData` (64² px is tiny); WebGL only for the cube | Autonomous (Giorgi) |

## 4. What to research (in this order, time-boxed)

1. **Run the spikes first** (`trash/spikes/README.md`, moved 14 Nov): `s3.py` (S3 section read), `pm.py` (propagation check), `bench.py` (reproject speed). 30 min.
2. IRSA tutorial notebooks — read the code, not the prose: *Spectral Image Cutouts*, *Source Discovery Tool* (background with `sep`, aperture photometry, MJy/sr → µJy), *Mosaic Cube* (how they keep similar-λ pixels). https://caltech-ipac.github.io/irsa-tutorials/spherex/
3. The LVF / spectral WCS: alternate WCS key `"W"` gives λ per pixel (`WCS(hdr, fobj=hdul, key="W")`, set `.sip=None`). Confirm on one cutout that λ varies < 0.01 µm across 64 px (measured 4.983→4.992 µm over 29 px).
4. FLAGS bit meanings: header keys `MSKNnnnn`; SPHEREx Explanatory Supplement https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp_QR.pdf (saturation limits per band).
5. How WiseView does it (copy the good ideas): one request → server-rendered frames + metadata; client draws Gaia overlay propagated per frame; `+/−/.` epoch legend; dashed border on frame 0 so you see the loop restart; shift-and-add with `pmx/pmy`. JS: http://byw.tools/static/flash3.js. Paper on unTimely co-adds: https://arxiv.org/abs/2209.14327
6. Gaia DR3 cone search via `astroquery.gaia` (ADQL `CONTAINS(POINT…, CIRCLE…)`), propagate with `SkyCoord.apply_space_motion`.
7. (`~`) SPHEREx HiPS cube (102 slices, time-averaged — context only, not for blinking): https://irsa.ipac.caltech.edu/data/hips/SPHEREx/spherex_allsky_cube ; Aladin Lite `setSliceNumber()`.
8. (`~`) Open question to check if you build live mode: is S3 / IRSA CORS open (could the browser fetch directly)? Rate limits on the cutout service?

## 5. Outputs & deadlines (H0 = kick-off)

| When | Output | For |
|---|---|---|
| H+1 | **Mock bundle** for `barnards-star/D56` committed (fake numbers, correct shapes) + `BlinkCanvas` props stub | Niklas starts UI immediately |
| H+3 | P0 thin slice: 3 real PNG frames of Barnard | Team confidence, video material |
| H+6 (**CP1, Sat ~20:00**) | First **real** bundle (Barnard D56) rendering in Niklas' page via `<BlinkCanvas>` | Integration checkpoint |
| Sun 10:00 (**CP2**) | Bundles for all 5 targets × (D1–D6, D56), diffs, gaia.json, spectrum.json; viewer with all modes | Product polish, demo recording |
| Sun 16:00 (**freeze**) | `~` items only if green; otherwise cut | — |
| Sun 18:00 | Technical description for the submission page (pipeline, NASA data used, references) | Niklas (submission) |

## 6. Dependencies & contracts

**You consume:**
- C1 `targets.json` and C2 `inventory/<id>.json` from Data. **While waiting** (first ~3 h): use the `spikes/` scripts which already query SIA for Barnard and WISE 0855; switch to C2 as soon as it lands.
- C3 `flags.json` from Data. **While waiting:** hard mask = NONFUNC, MISSING_DATA, HOT, COLD, PERSIST, OUTLIER, STREAK, SNOWBALL.
- C5 URL scheme/states from Niklas (so your loader exposes `n_epochs`, warnings, etc.).

**You provide:**
- C4 bundles (Quirce) and C6 viewer component (Giorgi) to Niklas.
- Feedback to Data: which exposures were unusable and why (they refine `usable`).
- Technical text + figures for the submission.

**Strictly sequential pairs:** C2 → P1 (mitigated by the spike scripts) · P1 grid → P2/P3/P5 (mitigated by the mock bundle at H+1).

## 7. Rabbit holes (avoid)
- Mixing wavelengths in one blink (fake variability). **D5.**
- Using J2000 positions (Barnard is 4′ away). **D6.**
- PSF matching for difference images; residual dipoles on bright static stars are expected — Gaia overlay explains them.
- `reproject_exact` (2–3 min); downloading full 65 MB files; parallel cutout requests without retries (16/84 failed in IRSA's own notebook).
- Polishing photometry on saturated cores (Barnard, R Dra, RW Aur): just flag it.
- Building the 3D volume renderer before CP2.
