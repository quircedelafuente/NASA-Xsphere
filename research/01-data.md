# Research — SPHEREx data (for Yasen + Sean)

*Compiled 14 Nov 2026. **[V]** = run on our server today · **[D]** = documentation · **[U]** = uncertain / not checked.*

## Bottom line
All five targets have plenty of public data (258–2,493 images each), anonymous, via IRSA SIA, the cutout service and a public S3 bucket. Motion of Barnard's Star and WISE 0855 was measured in real SPHEREx data and matches their proper motions. Motion ≈ 1–1.7 px/yr (6.15″ px): subtle in a raw blink; Gaia/WISE/2MASS archival positions (10–25 years ago) + centroid tracking make it obvious. Main risks: cutout speed (~1/s with HTTP 503 → precompute), saturation (Barnard, RW Aur OVERFLOW in every frame), WISE 0855's 2010 coordinates (~2′ off today).

## 1. Products
**Releases** — QR1 (Jul 2025) retired [D]; QR2 not searchable, downloadable until Feb 2027 [D]; **DR1** (Nov 2026) = Surveys 1+2 (Apr 2025 → ~May 2026) reprocessed with pipeline R7 [D]; **QR3** (from Sep 2026) = Surveys 3+4, R7, weekly [D]. DR1 + QR3 are one uniform set; don't mix with QR2. QR3 data from 16 May–19 Jul 2026 to be released "late fall 2026". DR2 (Surveys 1–4) after year 2. Sources: https://irsa.ipac.caltech.edu/data/SPHEREx/docs/overview_qr.html · Explanatory Supplement v2.1 (2026-11-10) §2.1 https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf

**SIA collections** [V]: `spherex_dr1`, `spherex_dr1_deep`, `spherex_dr1_cube`, `spherex_qr3`, `spherex_qr3_deep`.

**Level 2 spectral image** [V] — one MEF FITS per exposure per detector: PRIMARY · IMAGE 2040×2040 float32 MJy/sr (zodi not subtracted) · FLAGS int32 · VARIANCE · ZODI · EPSF (441 PSFs 33×33 oversampled) · WCS-WAVE. 65.7 MB. Exposure 113.58 s; 6.15″/px; PSF_FWHM ≈ 9.0″ (D6). Header: DATE-OBS, MJD-AVG, DETECTOR, **FINAST** (astrometry quality, 0 = good), **L2DQAFLG**, flag counts, **AURORA_CONT / SHUTTLE_GLOW_CONT / HE_AIRGLOW_CONT**, spacecraft position/velocity, OMEGA_MEDIAN (pixel solid angle ≈ 37.9 arcsec²) → ready-made metadata for the UI.

**Detectors & LVF** [D, Supplement Table 2] — a dichroic splits the 3.5°×11.3° field; short-wave D1–D3 and long-wave D4–D6 see the same sky simultaneously (confirmed [V]: each exposure id appears as D1+D4, D2+D5 or D3+D6).

| Det | µm | R |
|---|---|---|
| D1 | 0.75–1.09 | 39 |
| D2 | 1.10–1.62 | 41 |
| D3 | 1.63–2.41 | 41 |
| D4 | 2.42–3.82 | 35 |
| D5 | 3.83–4.41 | 112 |
| D6 | 4.42–5.00 | 128 |

λ varies along one detector axis; per-pixel λ from the `W` alternate WCS + WCS-WAVE (set `spectral_wcs.sip=None`; the SIP warning is harmless).

**102 bands** [D §3.4.4/§4.3.2] — each detector split geometrically into 17 channels (0/18 = corners); 17 × 6 = 102. Channels 51–52 (dichroic edges) blank in the DR1 cube. Planning coordinate, not exact calibrated λ.

**FLAGS** [V] — names in every FLAGS header as `MSKNnnnn` (name), `MSKMnnnn` (mask), `MSKDnnnn` (description) → read from file, don't hard-code.
0 TRANSIENT · 1 OVERFLOW · 2 SUR_ERROR · 6 NONFUNC · 7 DICHROIC · 9 MISSING_DATA · 10 HOT · 11 COLD · 12 FULLSAMPLE · 14 PHANMISS · 15 NONLINEAR · 17 PERSIST · 19 OUTLIER · 20 CROSSTALK · 21 SOURCE (known catalog source; not bad) · 22 GHOST · 23 GHOST_FPA · 24 GHOST_EXT · 25 STREAK · 26 BLOOM · 27 SNOWBALL · 28 HALO.
Mosaic tool rejects [D §3.4.3]: TRANSIENT, SUR_ERROR, NONFUNC, DICHROIC, MISSING_DATA, HOT, COLD, PHANMISS, NONLINEAR, PERSIST, CROSSTALK, GHOST×3, STREAK, BLOOM, SNOWBALL, HALO, SATELLITE_HALO; passes OVERFLOW, SOURCE, OUTLIER.

**Higher-level** — DR1 all-sky cube (`spherex_dr1_cube`, HEALPix order-5 tiles 512×512×102 at 12.9″, zodi-subtracted) [D]; HiPS cube https://irsa.ipac.caltech.edu/data/hips/SPHEREx/spherex_allsky_cube (102 frames PNG, order 5, fixed 0–40 MJy/sr asinh, display only) [V]; CDS HiPS `CDS/P/SPHEREx/QR2/D1..D6` and `/color` [V]. No public L3/L4 catalogs yet (except SPLICES, 3I/ATLAS) [D]. IRSA tools: Spectrophotometry, Mosaic, Data Explorer https://irsa.ipac.caltech.edu/applications/spherex , MOST.

## 2. Access
- **SIA2** [V] `https://irsa.ipac.caltech.edu/SIA?COLLECTION=spherex_dr1&POS=circle+RA+DEC+R` — 2–8 s; returns access_url, cloud_access (S3 key), t_min/t_max (MJD), energy_bandpassname, em_min/em_max, s_region, obs_id, obs_release_date.
- **TAP** [V] `https://irsa.ipac.caltech.edu/TAP` — `spherex.obscore`, `.plane` (metrics_maglimit, quality_flag), `.artifact` (contentlength), `.observation`.
- **Cutouts** [V] `access_url + "?center=RA,DEC&size=DEG"` (0.05° → 29×29 px). Keep all extensions incl. full EPSF (3.96 MB, ~95 % PSF). 8.5 s each. 8 threads: 85/93 ok in 110 s; 5 threads: 101/111 in 177 s; failures = HTTP 503 → ~1 cutout/s with retries. Tutorial: 7–12 workers, `conf.remote_timeout=120`.
- **S3** [V] `nasa-irsa-spherex` (us-east-1), anonymous, listable, prefixes `dr1/ qr2/ qr3/`; key pattern `dr1/level2/<plan>/l2b-v27-<date>/<det>/level2_<obsid>D<det>_spx_l2b-v27-<date>.fits`. Byte-range reads measured by the processing research at 0.5–2.5 s per exposure.
- No auth. CORS from the browser untested [U]. Data reach IRSA within 60 days; SIA lags ingest ~1 day [D].

## 3. Cadence
[D, Supplement §1.4] A "target group" = 17 pointings at the same ecliptic longitude stepped by one channel width → each channel lands on the source once. Surveys 1+2 in year 1 (ascending PA 0°, descending PA 180°), 3+4 in year 2 shifted by half a channel. → ~2 epochs/year ~6 months apart, each a 1–3 week cluster of ~50–60 exposures per detector pair; ~1 hit per wavelength per epoch; ~4 per wavelength over the mission. Deep fields at the ecliptic poles: near-monthly.

**Measured coverage** [V] (DR1 + QR3, wide + deep; clusters with gap > 20 d):

| Target | Position (epoch 2026.0) | Images | Date clusters (images) |
|---|---|---|---|
| Barnard's Star | 269.44627, +4.76820 | 358 | 2025-08-15→09-05 (108); 09-30 (10); 2026-03-11→04-10 (113); 05-04 (8); 08-16→09-02 (117); 09-22 (2) |
| ε Indi B | 331.09665, −56.80066 | 458 | 2025-04-24→06-10 (118); 09-28→11-12 (146); 2026-04-18→05-04 (74); 09-22→10-02 (120) |
| WISE 0855 | 133.75953, −7.24222 | 258 (DR1 only) | 2025-05-05 (30); 10-31→11-14 (110); 12-11→12-13 (18); 2026-04-21→05-14 (100) |
| RW Aur | 76.95609, +30.40112 | 335 | 2025-09-01→09-20 (112); 2026-02-20→03-12 (114); 2026-09-02→09-16 (109) |
| R Dra | 248.16723, +66.75503 | **2,493** (1,954 deep) | ~monthly Apr 2025 → Sep 2026; peaks 500 (Mar 2026), 432 (Aug 2026) |

R Dra is 8.6° from the north ecliptic pole (deep field) → ideal for a Mira light curve (~245 d). Full frames would be 17–165 GB per target → cutouts / S3 sections only.
*Note (plan):* small clusters (e.g. Barnard 09-30, 10 images) belong to the same survey pass → the plan uses gap > 60 d, with month-splitting for deep fields (D4).

## 4. Proper motion vs 6.15″ pixels
- Barnard: Gaia DR3 4472832130942575872, pm (−802, +10362) mas/yr = 10.39″/yr = **1.69 px/yr** [V]
- ε Indi B: Gaia DR3 6412596012146801152, G = 18.0, pm (3982, −2467) = 4.68″/yr = **0.76 px/yr** [V]
- WISE 0855: not in Gaia; CatWISE2020 splits it; literature pm (−8118, +680) mas/yr ≈ 8.15″/yr = **1.33 px/yr** [U]. Given position = AllWISE (~2010.5); propagated to 2026 it's ~127″ (~20 px) west → **must propagate**.
- RW Aur, R Dra: < 0.03″/yr → static; variability tests. Parallax wobble < 0.1 px.

**Measured centroid shifts** (epoch means vs first epoch) [V]: Barnard D1–D3 **+9.8″ Dec over 0.99 yr** (1.6 px, ±0.2″; expected +10.3″) · WISE 0855 D5/D6 **−7.4″ RA over 0.985 yr** (1.2 px, ±0.3–0.9″; expected ~−8″). Measured − predicted ≤ 1.8″ every epoch (astrometry RMS < 0.3″ for bright stars per Supplement).

**Detectability** [V]: WISE 0855 invisible below ~3.8 µm; D5/D6 single-exposure S/N 3–5, per-epoch stack **10–14**, flux ~0.4–0.6 mJy (consistent with W2) → co-add per detector per epoch required.
**Saturation** [V]: Barnard OVERFLOW+BLOOM+TRANSIENT in all 168 D1–D3 frames, NaN cores (centroid still works with NaN→0). RW Aur OVERFLOW 100/101; its D5 (~4 µm) flux fell ~2.2 Jy (Sep 2025) → ~1.2 Jy (Sep 2026) while 1.1–1.6 µm didn't — suggestive of real variability but unreliable (saturation) [U].

## 5. Overlay catalogs
Gaia DR3: ESA TAP https://gea.esac.esa.int/tap-server/tap or IRSA TAP `gaia_dr3_source` [V]; propagate from 2016.0. SIMBAD TAP returned 404 from our server [V]. WISE: IRSA TAP `catwise_2020` (with pm), `allwise_p3as_psd`, `unwise_2019` [V]; HiPS `CDS/P/unWISE/W1`, `/W2`, `/color-W2-W1W2-W1`, `CDS/P/allWISE/*` [V]. WiseView http://byw.tools/wiseview is the UI model.

## 6. Recommendations (from the research; adopted/adjusted in DECISIONS.md)
1. DR1 + QR3 (wide + deep), collection list in config; query live, never hard-code file lists.
2. Demo set = the 5 targets, precomputed.
3. Epochs by time clustering, labelled by survey and date range; deep fields subdivided by month.
4. Movie = inverse-variance co-add per detector per epoch (6 broadband frames/epoch); default D1/D2 for stars, D5/D6 for cold brown dwarfs; keep per-channel data for spectra.
5. Quality: mosaic-tool reject mask; keep SOURCE; OVERFLOW = "saturated" warning; show FINAST, L2DQAFLG, *_CONT per frame.
6. Live cutouts too slow → precompute; arbitrary coordinates = background job + cache (or S3 sections / HiPS preview).
7. Handoff: per target a manifest (obs_id, det, mjd, epoch, λ at target, flags, FINAST, predicted position, access_url/S3 key) — formalised as C2.
8. URL state `?ra=&dec=&pmra=&pmdec=&epoch=&fov=&det=` (Product owns final scheme, C5).

## 7. Risks
Propagate high-pm targets; saturated targets → NaN cores, ghosts/crosstalk at 32/64-px offsets [D]; EPSF bloat in cutouts; each epoch spans 2–3 weeks of different λ (variable star colour ↔ time confusion); don't mix QR2 with R7; HiPS PNGs not for photometry; shallow single exposures; CORS untested; don't write own mosaicking/photometry — link IRSA's Spectrophotometry Tool.

## Snippets that worked [V]
`python3 -m venv venv && venv/bin/pip install astropy pyvo astroquery pandas` (astropy 8.0.2, pyvo 1.10.0, astroquery 0.4.11; no SSL problems).
```python
from astroquery.ipac.irsa import Irsa
from astropy.coordinates import SkyCoord, Distance
from astropy.time import Time
import astropy.units as u
c = SkyCoord(ra=133.7947597*u.deg, dec=-7.2451456*u.deg, pm_ra_cosdec=-8118*u.mas/u.yr,
             pm_dec=680*u.mas/u.yr, distance=Distance(parallax=439*u.mas),
             obstime=Time(2010.5, format='jyear'))
c26 = c.apply_space_motion(new_obstime=Time('2026-01-01'))
r = Irsa.query_sia(pos=(SkyCoord(c26.ra, c26.dec), 1*u.arcsec),
                   collection=['spherex_dr1','spherex_qr3','spherex_dr1_deep','spherex_qr3_deep'])
url = r['access_url'][0] + f"?center={c26.ra.deg},{c26.dec.deg}&size=0.05"   # size in degrees
```
```python
h = fits.open('cut.fits'); H = h['IMAGE'].header
img = h['IMAGE'].data - h['ZODI'].data
flagnames = {int(k[4:]): h['FLAGS'].header[k] for k in h['FLAGS'].header if k.startswith('MSKN')}
sw = WCS(H, fobj=h, key='W'); sw.sip = None
lam_um = sw.pixel_to_world_values(x, y)[0]
# TAP: pyvo.dal.TAPService("https://irsa.ipac.caltech.edu/TAP").search("select ... from spherex.plane ...")
# S3: s3://nasa-irsa-spherex/<cloud_access['aws']['key']>  (anonymous, us-east-1)
```
Scripts are in [`spikes/`](../spikes/).
