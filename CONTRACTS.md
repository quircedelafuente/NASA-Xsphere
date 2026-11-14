# Contracts between roles

> These are the interfaces that let the three roles work **in parallel without waiting for each other**.
> They are **Team-locks** (see [DECISIONS.md](DECISIONS.md)): once locked at kick-off, nobody changes a field
> on their own. Adding an optional field is fine; renaming/removing one needs the decider (Quirce) and a
> message to the consumers.
>
> Every contract has a **mock file committed in Phase 0** so the consumer can build against it from minute one.

```
 DATA (Yasen, Sean)            PROCESSING (Quirce, Giorgi)            PRODUCT (Niklas)
 ───────────────────           ──────────────────────────            ────────────────
 C1 targets.json      ───────►  reads targets, pm, band  ──────────►  object cards, chips
 C2 inventory/<id>.json ─────►  which exposures to fetch
 C3 flags.json        ───────►  hard/soft mask           ──────────►  "problem pixels" legend
 C7 science notes     ──────────────────────────────────────────────►  copy, tour, video facts
                                C4 bundle (static files)  ──────────►  viewer renders it
                                C6 viewer component API  ◄─────────►  UI shell uses it
                       ◄──────────────── C5 URL scheme / states ─────  (owned by Niklas)
```

All files are JSON, UTF-8, numbers in SI-ish astro units stated in the field name
(`_deg`, `_arcsec`, `_um`, `_masyr`, `mjd`). Coordinates are ICRS.

---

## C1 · `data/targets.json` — the target catalogue (owner: **Data**, consumers: Processing, Product)

*(Numbers in the examples are illustrative — the real values come from Data.)*

```json
[
  {
    "id": "barnards-star",
    "name": "Barnard's Star",
    "aliases": ["Barnard's Star", "GJ 699", "Gaia DR3 4472832130942575872"],
    "kind": "mover",                       // mover | variable | companion-mover | custom
    "ra_deg": 269.4486,                     // at ref_epoch
    "dec_deg": 4.7398,
    "ref_epoch": 2016.0,                    // Gaia DR3 epoch (J2000 positions are 4' off for Barnard!)
    "pmra_masyr": -801.55,
    "pmdec_masyr": 10362.39,
    "plx_mas": 546.98,
    "rv_kms": -110.6,                       // optional
    "astrometry_source": "Gaia DR3",
    "default_band": "D6",                  // see C4 band ids
    "fov_arcsec": 394,                      // 64 px * 6.15"
    "archival_positions": [               // "where it was" overlay (motion of 1–3′ over 10–25 yr)
      {"survey": "2MASS", "epoch": 1999.4, "ra_deg": 269.4520, "dec_deg": 4.6680},
      {"survey": "AllWISE", "epoch": 2010.5, "ra_deg": 269.4507, "dec_deg": 4.6996}
    ],
    "expected": {
      "motion_px_per_yr": 1.69,
      "variability": "none",
      "saturated": true,
      "notes": "Bright: core saturated/NaN in most bands; use D5/D6 or diff mode."
    }
  }
]
```

Rules:
- Positions are **always** at `ref_epoch` with proper motion; processing propagates to each exposure's `MJD-AVG`.
- `id` is URL-safe and permanent (used in URLs and bundle paths).
- The 5 official targets are required. Data may add up to 3 bonus showcase targets (`"bonus": true`).

## C2 · `data/inventory/<id>.json` — what SPHEREx has for a target (owner: **Data**, consumer: Processing)

```json
{
  "target_id": "barnards-star",
  "generated_utc": "2026-11-14T15:00:00Z",
  "collections": ["spherex_dr1", "spherex_qr3"],
  "epoch_rule": "split when gap > 60 d; groups spanning > 60 d split by calendar month",
  "epochs": [
    {"id": 0, "label": "Aug–Sep 2025", "mjd_start": 60903.0, "mjd_end": 60949.3,
     "release": "spherex_dr1", "n": 120, "per_detector": {"D1": 20, "D2": 19, "D3": 21, "D4": 20, "D5": 19, "D6": 21}}
  ],
  "exposures": [
    {"obs_id": "2025W33_2C_0321_1", "release": "spherex_dr1", "epoch": 0, "det": "D6",
     "mjd": 60902.87, "lam_um": 4.987, "bw_um": 0.039,
     "x_pix": 1012.4, "y_pix": 344.0, "on_chip": true, "edge_margin_px": 312,
     "flags_at_target": 69206023, "saturated": true, "finast": 0, "contamination": [],   // AURORA/SHUTTLE_GLOW/HE_AIRGLOW _CONT
     "usable": true, "reject_reason": null,
     "s3_url": "s3://nasa-irsa-spherex/...", "https_url": "https://nasa-irsa-spherex.s3.amazonaws.com/...",
     "cutout_url": "https://irsa.ipac.caltech.edu/....fits"}
  ]
}
```

Rules:
- `lam_um` is the wavelength **at the target's pixel** (LVF: it changes with position on the detector).
- `usable=false` exposures stay in the file with a `reject_reason` (transparency + debugging).
- Re-generating for a new release must only append; ids stay stable.

## C3 · `data/flags.json` — flag dictionary (owner: **Data**, consumers: Processing, Product)

```json
{
  "hard_mask_bits": [6, 9, 10, 11, 17, 19, 25, 27],
  "soft_bits": [0, 1, 2, 7, 15, 20, 21, 22, 23, 24, 26, 28],
  "bits": {
    "1":  {"name": "OVERFLOW",  "class": "soft", "plain": "Too bright: the detector saturated here."},
    "21": {"name": "SOURCE",    "class": "soft", "plain": "A known star or galaxy sits on this pixel."},
    "26": {"name": "BLOOM",     "class": "soft", "plain": "Light bleeding from a very bright star."}
  }
}
```
`plain` text is written for the public (Niklas reviews wording).

## C4 · Bundle — processed output the website reads (owner: **Processing**, consumer: Product)

Static files under `web/public/bundles/` (served as-is by the frontend host). The live API (if built)
returns **exactly the same JSON shapes**, so the frontend doesn't care where data comes from.

```
web/public/bundles/
  index.json                         # [{id, name, kind, bands:[...], n_epochs, thumb}]
  <target-id>/
    meta.json                        # C1 entry + epochs summary (from C2) + release + generated_utc
    <band>/manifest.json             # see below
    <band>/e0.f32  e1.f32  e2.f32    # float32 little-endian, row-major [y][x], NaN = masked
    <band>/e0.png  ...               # pre-stretched 8-bit previews (OG cards, embeds, fallback)
    <band>/e0_mask.png ...           # RGBA overlay of soft flags (transparent where clean)
    <band>/diff_1_0.f32 ...          # epoch1 - epoch0 in sigma units (optional)
    spectrum.json
    gaia.json
    cube.json + cube_u8.bin          # ~ optional (λ slider / 3D)
```

**Band ids:** `D1`…`D6` (one detector each), `D56` (3.8–5.0 µm, best for cold brown dwarfs),
`ALL` (all detectors, only for "pretty" context — never blink across mixed λ), `mol-ch4`, `mol-h2o`, `mol-co2` (~).

**`<band>/manifest.json`:**
```json
{
  "target_id": "barnards-star",
  "band": "D6",
  "lam_range_um": [4.42, 5.00],
  "grid": {"nx": 64, "ny": 64, "pix_arcsec": 6.15,
           "wcs": {"ctype": ["RA---TAN", "DEC--TAN"], "crval": [269.4521, 4.7452],
                   "crpix": [32.5, 32.5], "cdelt": [-0.001708, 0.001708]}},
  "units": "MJy/sr (zodi-subtracted)",
  "stretch": {"method": "asinh", "a": 0.1, "vmin": -0.05, "vmax": 12.3, "scope": "sequence"},
  "frames": [
    {"epoch": 0, "label": "Aug–Sep 2025", "mjd": 60920.1, "n_exposures": 21,
     "lam_mean_um": 4.71,
     "f32": "e0.f32", "png": "e0.png", "mask_png": "e0_mask.png",
     "target_px": [31.2, 34.0], "flags_at_target": ["OVERFLOW", "SOURCE"]}
  ],
  "diffs": [{"from": 0, "to": 1, "f32": "diff_1_0.f32", "units": "sigma"}],
  "target_track": [{"mjd": 60920.1, "x": 31.2, "y": 34.0}],
  "warnings": ["saturated core"]
}
```

Rules (Team-lock D7, D8):
- All frames of one manifest share **the same grid** (same WCS, same nx/ny) and **the same stretch**.
- Frames in one manifest are **wavelength-matched** (same band window) — never mix λ in a blink.
- Pixel (0,0) is the bottom-left in FITS; **the `.f32` files are written top-row-first** (north up, ready for canvas). Write this once in `processing/export.py` and nowhere else.
- `target_px` / `target_track` are in the same top-left-origin pixel coordinates as the `.f32`.

**`spectrum.json`:**
```json
{"target_id": "r-draconis", "aperture_px": 2.0, "units": "uJy",
 "points": [{"wl_um": 1.23, "bw_um": 0.03, "flux": 1520.0, "err": 40.0,
             "mjd": 60920.4, "epoch": 0, "det": "D2", "flagged": false}],
 "official_tool": "https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html"}
```

`spectrum.json` points carry `mjd` + `epoch`, so the UI can also plot a **light curve** (flux vs time per band) — the key view for R Dra (~monthly data).

**`gaia.json`:** `{"ref_epoch": 2016.0, "sources": [{"ra_deg","dec_deg","pmra_masyr","pmdec_masyr","plx_mas","gmag"}]}` —
the viewer propagates them per frame (WiseView-style).

## C5 · URL scheme & UI states (owner: **Product**, consumers: everyone)

```
/                                   landing
/?target=barnards-star              named target (alias resolved from index.json)
/?ra=133.795&dec=-7.245&fov=394     arbitrary coordinates (live mode, may say "not processed yet")
   &band=D56&mode=blink|diff|side&speed=1.0&frame=0&stretch=asinh:0.1&overlay=gaia,flags
/embed?...                          same params, minimal chrome for iframes
```

States the data must make possible (processing must expose the signal, product designs the screen):
`loading` · `ok` · `one-epoch` ("come back in 6 months") · `two-epochs` · `no-coverage` ·
`saturated-target` · `name-not-found` · `live-not-available` (static-only deploy).

## C6 · Viewer component API (owners: **Giorgi** builds it, **Niklas** uses it)

```ts
<BlinkCanvas
  manifest={Manifest}          // C4
  mode="blink" | "diff" | "side"
  frameIndex={number}          // controlled by the UI
  playing={boolean} fps={1}    // ≤ 2 fps (WCAG 2.3.1), paused if prefers-reduced-motion
  stretch={{ a, vmin, vmax }}  // client-side re-stretch of the .f32
  zoom={8}                     // nearest-neighbour upscale (pixels stay square)
  overlays={{ crosshair: true, track: true, gaia: GaiaJson | null, flags: boolean }}
  onPixelClick={(ra, dec, x, y) => void}
/>
<SpectrumChart spectrum={SpectrumJson} highlightBands={MolBand[]} />
<CubeSlider cube={CubeJson} />            // ~
```
Giorgi owns rendering and data loading (`web/src/viewer/`, `web/src/data/`); Niklas owns layout, controls,
copy, styling (`web/src/ui/`, `web/src/pages/`). Props can gain optional fields; changing existing ones = message Niklas.

## C7 · Science notes (owner: **Data**, consumer: Product)

`data/science-notes.md`: per target, 3–5 plain-English facts with a source link
(what it is, distance, why it moves or varies, what to look for, which band shows it best, caveats).
Niklas turns them into cards, the guided tour and the 30-second video. **Every number in the UI or video
must trace back to this file.**
