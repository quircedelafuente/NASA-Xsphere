# processing/ — from SPHEREx files to comparable frames (owner: Quirce)

```
python -m venv venv && venv/bin/pip install -r processing/requirements.txt
venv/bin/python -m processing.build --target barnards-star --band D4   # one target
venv/bin/python -m processing.build --all                              # the 5 targets, default band
```
Output → `web/public/bundles/<target>/<band>/` (contract C4) + `web/public/bundles/index.json`.
Quick look without the web app: open `blink.gif` (the little video) and `changes.png` (what changed vs the first epoch).

## What happens, in plain words
1. **Which photos** (`exposures.py`): all SPHEREx exposures of that sky patch in one band (DR1 + QR3). Uses Data's
   `data/inventory/<id>.json` when it exists, otherwise the SIA tables in `spikes/sia/`. Groups them into epochs (D4).
2. **Cut + clean** (`frames.py`): reads only a ~100×100 px piece of each 65 MB file straight from NASA's public S3
   (no download, no account), subtracts the zodiacal light and the residual background, masks bad pixels.
3. **Align** (`frames.py`): puts every piece on the same 64×64 north-up grid (6.15″/px), centred on the target.
4. **Stack per epoch** (`frames.py`): averages the ~10–60 photos of each pass (inverse-variance, outliers clipped)
   → one clean image per epoch. Where the target should be at that date (proper motion) → crosshair.
5. **What changed** (`change.py`): epoch − first epoch (and consecutive pairs), in **sigma** units: 0 = no change,
   ±5 = clearly changed. Lists the strongest spots as **candidates**: `brighter`, `fainter` or `moved`
   (a brighter blob next to a fainter one = something that moved).
6. **Export** (`export.py`): float32 frames for the viewer, PNG previews, one stretch for the whole sequence, manifest.

## Knobs (`config.yaml`)
`change.reference` (first | consecutive), `change.candidate_sigma` (5), `change.sys_frac` (0.1 = 10 % error floor
because each epoch mixes slightly different wavelengths inside a band), `grid.nx/ny`, `stretch.*`, `flags.*`.

## Known limits (first version)
- Saturated stars (Barnard, R Dra, RW Aur in D1–D4) have masked/unreliable cores → the difference view and the
  saturation mask are the honest way to show them.
- Inside one detector the wavelength still varies per exposure (LVF); averaging per epoch evens it out but bright
  stars leave small residuals in the difference images. That is why there is a 10 % error floor.
- Custom RA/Dec needs an SIA table for now (`--sia`); the live query belongs to P6.

## Preview colour (added by Sean, 14 Nov)
`e<N>.png` and `blink.gif` are in false colour: one tint per band, picked from the band's wavelength (shorter bluer,
longer redder), in `palette.py`. Brightness order is kept and one sequence uses one table, so frames stay comparable.
The `.f32` data, the masks and the difference images are unchanged. Bundles made before this:
`python -m processing.recolour` repaints their previews from the `.f32` files (no download). The web viewer uses the
same table in `web/src/ui/lib/palette.ts`: change both together.
