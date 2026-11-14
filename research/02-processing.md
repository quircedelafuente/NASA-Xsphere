# Research — Processing, algorithm & backend→frontend (for Quirce + Giorgi)

*Compiled 14 Nov 2026. **[DOC]** = from documentation · **[MEASURED]** = checked today with small requests to IRSA / S3 / CDS · **[INFER]** = recommendation.*

## 0. Five measured facts that change the design
1. **~3 epochs, not dozens.** SIA for Barnard's Star: `spherex_dr1` 240 exposures in two seasons (MJD 60903–60949 = Aug–Sep 2025; 61110–61165 = Mar–May 2026); `spherex_qr3` 123 exposures in one more (MJD 61269–61306 = Aug–Sep 2026). All detectors D1–D6, ~40 exposures each. A season spreads over 3–7 weeks because a point is stepped across the LVF ([DOC] https://spherex.caltech.edu/page/survey). Gap > 20 d splits seasons wrongly → use **gap > 60 d**.
2. **Propagate coordinates to the observation date.** Barnard's J2000 position (SIMBAD/Sesame) is **4.4′** from where it is in 2025–26; a 0.05° cutout misses it. Propagating Gaia DR3 to each image's `MJD-AVG` (`SkyCoord.apply_space_motion`) put it within ~1 px in all three epochs.
3. **Motion between epochs is 1–2 px** (6.15″/px): Barnard 10.4″/yr → ~1.7 px DR1→QR3; WISE 0855 8.2″/yr → ~1.3 px; ε Indi B 4.7″/yr → < 1 px. Needs NN upscaling, difference frames, predicted-track overlay; optionally a long-baseline context (unWISE 2010–2024: Barnard moved ~2.6′).
4. **Bright targets are saturated.** Barnard peaks 900–2000 MJy/sr with 3–4 NaN core pixels; core flags 69206023 = TRANSIENT+OVERFLOW+SUR_ERROR+SOURCE+BLOOM (bits in `MSKNnnnn` header keys). R Dra (Mira) and RW Aur likely similar.
5. **IRSA cutout service is slow; S3 byte-range reads ~4× faster.** Cutout (`?center=…&size=0.05`): ~8.6 s/exposure, 3.96 MB of which 3.86 MB is the EPSF table it always includes (image 29×29 px). S3 (`fits.open(url, use_fsspec=True)` + `.section[...]`) on public bucket `nasa-irsa-spherex` (us-east-1, key in SIA `cloud_access` column): 1.25 s open + ~0.25 s/extension ≈ 0.5–2.5 s. Full L2 file ≈ 65 MB. SIA query ≈ 1.9 s; TAP in the notebook ≈ 20 s.

## 1. Pipeline
**1a Resolve** [MEASURED] Sesame `https://cds.unistra.fr/cgi-bin/nph-sesame/-oxp/SNV?<name>` → XML `jradeg, jdedeg, pmRA, pmDE, plx` in 0.1–0.3 s (follow redirects). "WISE 0855-0714" fails; "WISE J085510.83-071442.5" works. Prefer Gaia DR3 (epoch 2016.0).

**1b Query** [DOC] https://caltech-ipac.github.io/irsa-tutorials/spherex-intro/
```python
Irsa.query_sia(pos=(coord, r), collection=['spherex_dr1', 'spherex_qr3'])
```
Also `spherex_dr1_deep`, `spherex_qr3_deep`; QR2 superseded. Columns: `obs_id, t_min, t_max, energy_bandpassname ('SPHEREx-D1'…), em_min, em_max, s_region, access_url, cloud_access`. SIA can lag ingestion by ~1 day. TAP: `spherex.artifact` JOIN `spherex.plane` with `CONTAINS(POINT, p.poly)` (https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts/). Query at the propagated position with radius ≈ FOV.

**1c Cutouts** [DOC] `https://irsa.ipac.caltech.edu/<path>.fits?center=RA,DECd&size=DEG`; notebook: 84 cutouts 2.26 min serial, 13 s with 10 threads, but **16/84 failed** in parallel → retries mandatory. Recommended S3 reading [MEASURED]:
```python
with fits.open(s3_https_url, use_fsspec=True, fsspec_kwargs={"block_size": 512_000}) as h:
    hdr = h['IMAGE'].header; w = WCS(hdr)
    c = target.apply_space_motion(new_obstime=Time(hdr['MJD-AVG'], format='mjd'))
    x, y = map(lambda v: int(round(float(v))), w.world_to_pixel(c))
    sl = np.s_[y-n:y+n, x-n:x+n]   # clip at edges; skip if target off-chip
    img, flg = h['IMAGE'].section[sl], h['FLAGS'].section[sl]
    var, zod = h['VARIANCE'].section[sl], h['ZODI'].section[sl]
    wcs_cut = w[sl]
```

**1d MEF layout** [DOC] IMAGE 2040² float32 MJy/sr (zodi not subtracted) · FLAGS int32 compressed · VARIANCE · ZODI · EPSF (21×21 grid of 33×33 PSFs, ×5 oversampled) · WCS-WAVE (9×9 control grid). Flag bits: 0 TRANSIENT, 1 OVERFLOW, 2 SUR_ERROR, 6 NONFUNC, 7 DICHROIC, 9 MISSING_DATA, 10 HOT, 11 COLD, 15 NONLINEAR, 17 PERSIST, 19 OUTLIER, 20 CROSSTALK, 21 SOURCE, 22–24 GHOST*, 25 STREAK, 26 BLOOM, 27 SNOWBALL, 28 HALO. Headers: `MJD-AVG`, `DATE-OBS`, `DETECTOR`, `PSF_FWHM`. Astropy warns SIP present but CTYPE lacks "-SIP" — handle on purpose.

**1e LVF / band images** [DOC] λ per pixel from alternate WCS `'W'`: `sw = WCS(hdr, fobj=hdul, key="W"); sw.sip=None; wl, bw = sw.pixel_to_world(x, y)`. D1 0.75–1.09 (R39) · D2 1.10–1.62 (R41) · D3 1.63–2.41 (R41) · D4 2.42–3.82 (R35) · D5 3.83–4.41 (R112) · D6 4.42–5.00 (R128). [MEASURED] over a 29-px cutout λ varied 4.983–4.992 µm → a cutout < ~10′ is nearly monochromatic: each exposure = one narrow-band sample at λ(target). For larger FOV mask by per-pixel λ (what the Mosaic tool does: https://caltech-ipac.github.io/irsa-tutorials/spherex-mosaic/).

**1f Epochs** sort by `t_min`, split on gap > 60 d; only compare epochs within the same λ window.

**1g Reprojection** [MEASURED, synthetic TAN, 4-core ARM]: 60² interp 5.7 ms / adaptive 10 / exact 27; 120²: 13 / 32 / 95; 300²: 69 / 178 / 541 ms. Interp fastest, not flux-conserving; exact costly (Source Discovery notebook: 2–3 min) (https://docs.astropy.org/projects/reproject/en/stable/celestial.html). `reproject_and_coadd(..., match_background=True)` (https://docs.astropy.org/projects/reproject/en/stable/mosaicking.html). PSF FWHM ≈ 1–1.5 px (undersampled) → interpolation causes dipoles on static stars in diffs.

**1h Background & co-add** subtract ZODI (changes with solar elongation between epochs); residual background `sep`/`Background2D` (notebook: `sep.Background(bw=64,bh=64,fw=11,fh=11)`, needs native byte order); hard mask → NaN (NONFUNC, MISSING_DATA, HOT, COLD, PERSIST, OUTLIER, STREAK, SNOWBALL, TRANSIENT if not saturated); soft flags → contamination layer (SOURCE, DICHROIC, GHOST*, HALO, CROSSTALK, NONLINEAR, OVERFLOW/SUR_ERROR, BLOOM). Inverse-variance co-add `Σw·I/Σw`, err `1/√Σw`, σ-clip/median if N ≥ 5, keep `nhits`.

**1i Difference** `diff = E2 − E1` same grid & λ; skip PSF matching; show sigma diff `diff/√(err1²+err2²)` with a diverging colormap; expect dipoles on all bright stars → Gaia overlay distinguishes real movers.

**1j Stretch** one stretch per sequence: vmin/vmax from 0.5/99.5 percentiles over all valid pixels, `AsinhStretch(a)`; per-frame normalisation causes flicker. WiseView does the same (asinh, "linear" slider, trim bright).

## 2. WiseView / unTimely lessons
- unTimely (Meisner+2023, https://arxiv.org/abs/2209.14327): one co-add per band per 6-month pass, ~16 epochs/location, 2048² tiles at 2.75″/px; issues: deblending differences fake variability, first pass ~2 % brighter, cosmic rays, nebulosity.
- WiseView internals [MEASURED, http://byw.tools/static/flash3.js]: one request to an AWS Lambda `png-animation` with `ra, dec, band, size, minbright, maxbright, stretch, invert, diff, diff_window, window, outer, unique, scandir, smooth_scan, neowise, shift(pmx,pmy), synth_*`; JSON response with `all_mjds`, per-frame `mjds`, `epochs`, `neg_epochs`, pixel range, WCS, PNG URLs; retries on 504. Gaia overlay drawn client-side, propagated per frame (minor bug: uses DR2 epoch 2015.5 with DR3 positions).
- Lessons: server renders frames + metadata, client animates + overlays; "window" (co-add) and "diff" are the core features; consistent stretch; restart border; shift-and-add at trial pm is cheap and powerful with few epochs.

## 3. Spectrum on the fly
[DOC] Source Discovery notebook: aperture photometry per exposure r = 3/4/5 px, λ from 'W' WCS, MJy/sr → µJy with solid-angle map, ~5 min dominated by downloads. HiPS/Mosaic notebooks: photutils aperture + annulus per cube plane ~20 s. IRSA Spectrophotometry tool: Tractor forced PSF, λ/flux/err/flags/mjd/det per exposure, slow (≥ 5 min), no API → link out for science-grade.
[INFER] Reuse per-exposure cutouts; ~1 ms/exposure; colour points by epoch (shows R Dra / RW Aur variability); small apertures lose λ-dependent flux (aperture correction from EPSF if time).
```python
def phot(img, var, flg, wcs, wcsW, c, r=2.0, rin=5, rout=9):
    x, y = wcs.world_to_pixel(c); lam, bw = wcsW.pixel_to_world(x, y)
    bad = (flg & HARD_MASK) != 0
    ap = CircularAperture((x, y), r); an = CircularAnnulus((x, y), rin, rout)
    bkg = ApertureStats(img, an, mask=bad, sigma_clip=SigmaClip(3)).median
    t = aperture_photometry(img - bkg, ap, error=np.sqrt(var), mask=bad)
    f = (t['aperture_sum'][0] * u.MJy/u.sr * (6.15*u.arcsec)**2).to(u.uJy)
    return dict(wl=lam.to_value(u.um), bw=bw.to_value(u.um), flux=f.value, ...)
```

## 4. Automatic motion detection (optional)
Sigma diff per λ window → ±5σ peaks (`DAOStarFinder`/`sep.extract`) → pair + and − within 1–4 px → direction and pm ≈ |Δ|·6.15″/Δt → cross-match Gaia DR3 propagated per epoch. Dipole with no Gaia counterpart, or red-only (bright D5/D6, absent D1–D3, like WISE 0855) = candidate. Shift-and-add over a pm grid as a "motion search" button. Marginal at 1–2 px → always "candidate".

## 5. Architecture options
| Option | Pros | Cons |
|---|---|---|
| A FastAPI + disk cache | any RA/Dec | 30 s–5 min cold; needs jobs/progress |
| B Precomputed static bundles for 5 targets | instant, robust, CDN | no arbitrary coordinates |
| C Browser-side (JS9/fitsjs) | no server | CORS unknown; LVF + reprojection in JS = rabbit hole |
| D SPHEREx HiPS cube in Aladin Lite | zero processing, 102 channels | **time-averaged: no epochs** |
HiPS [MEASURED] https://irsa.ipac.caltech.edu/data/hips/SPHEREx/spherex_allsky_cube: `hips_cube_depth=102`, png tiles, order 5, 12.9″ pixels, t 60790–61174 (all DR1 averaged), slices 50–51 blank. Aladin Lite v3 has `setSliceNumber()`; maps slice→frequency linearly (labels may be off for SPHEREx). Use D as context map only.
**Recommendation:** B + A hybrid — one Python module writes "target bundles"; `precompute.py` for the 5 targets (committed, static); same module behind FastAPI for live queries with job polling and a cache keyed by `hash(ra, dec, fov, λwindow, release)`. Host near us-east-1. Avoid ~10 s serverless timeouts.

## 6. API sketch
`GET /api/resolve?name=` → `{name, ra, dec, epoch, pmra, pmdec, plx, source}` · `GET /api/epochs?ra&dec` → epochs + exposures (obs_id, det, mjd, lam_um, bw_um, epoch, flags_at_target, url) · `POST /api/frames` → manifest (wcs, shape, units, stretch, frames[{epoch, mjd, lam_range, n, png, f32, mask_png}], target_track, gif) · `GET /api/spectrum` · `GET /api/cube` (uint8 [λ][y][x] + JSON header) · `GET /api/overlay/gaia`. Deliver float32 (64² × 4 B = 16 KB/frame) for client-side stretch + PNG previews; GIF/MP4 only for export. The locked version is in [`CONTRACTS.md`](../CONTRACTS.md).

## 7. 3D cube
64×64×102 float32 = 1.6 MB; uint8 = 418 KB. three.js `Data3DTexture` + raymarch (best, hours of shader work) · vtk.js (heavier) · Plotly `go.Volume` (quick, sluggish > 50³). **Better per hour of work: 2D image + λ slider + click-to-spectrum.** Molecule filters as line/continuum ratio maps: H₂O ice 3.0 µm, CH₄ 3.3 µm (PAH confusion), CO₂ ice 4.27, CO 4.67, H₂O vapour 1.4/1.9, CH₄ 1.6/2.2 (T/Y dwarfs).

## 8. Open questions
CORS on IRSA/S3? Cutout rate limits? Can the cutout service drop EPSF? HiPS weighting/zodi and slice labels? Saturation limits per band (Explanatory Supplement https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp_QR.pdf)? Epoch count for ε Indi B (Dec −57°) and R Dra (+66.8°)?

## Key URLs
Tutorials https://caltech-ipac.github.io/irsa-tutorials/spherex/ · Spectrophotometry help https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html · unTimely https://arxiv.org/abs/2209.14327 · WiseView http://byw.tools/wiseview · reproject https://docs.astropy.org/projects/reproject/en/stable/ · Aladin Lite https://github.com/cds-astro/aladin-lite
