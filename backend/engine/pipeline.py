"""Chunk A ↔ chunk B bridge: live inventory (A3) → Quirce's engine (processing/: frames, change, export, discovery).
Live results use the SAME formats as the pre-built ones: C4 bundles for viewing, I2 stacks for the discovery scan."""
import json, sys
from pathlib import Path
import numpy as np
from astropy.time import Time

from . import config

sys.path.insert(0, str(config.ROOT))          # `processing` is a top-level package in the repo
from processing import frames as P_frames      # noqa: E402  (Quirce)
from processing.bands import detectors, lam_range   # noqa: E402
from processing.change import compute_changes  # noqa: E402
from processing.exposures import assign_epochs  # noqa: E402
from processing.export import export_bundle    # noqa: E402

STACK_BANDS = ['D4', 'D5', 'D6']   # what the discovery scan uses (processing/stacks.py)
STACK_PIX = 3.075                  # half a SPHEREx pixel, as processing/stacks.py

def exposures(rows, band, per_epoch=None):
    """Our live SIA rows → processing's exposure dicts, epochs by processing's own D4 rule; optionally capped per epoch × detector."""
    dets = detectors(band)
    exps = sorted((dict(obs_id=r['obs_id'], det=r['band'], mjd=r['mjd'], release=r['collection'], url=r['s3'], epoch=None)
                   for r in rows if r['band'] in dets), key=lambda e: e['mjd'])
    if not exps:
        return []
    assign_epochs(exps)
    return _cap(exps, dets, per_epoch)

def _cap(exps, dets, per_epoch):
    if not per_epoch:
        return exps
    keep = []
    for ep in sorted({e['epoch'] for e in exps}):
        for d in dets:
            g = [e for e in exps if e['epoch'] == ep and e['det'] == d]
            step = max(len(g) / per_epoch, 1)
            keep += [g[int(i * step)] for i in range(min(per_epoch, len(g)))]
    return sorted(keep, key=lambda e: e['mjd'])

def field_target(ra, dec, name=None):
    """A position without catalogue motion, shaped like a C1 target so processing can use it."""
    return dict(id=f'field-{ra:.4f}{dec:+.4f}', name=name or f'Field {ra:.4f} {dec:+.4f}', ra_deg=ra, dec_deg=dec,
                ref_epoch=2016.0, pmra_masyr=0.0, pmdec_masyr=0.0, plx_mas=0.1, kind='field')

def _bundle(target, band, grid_wcs, shape, frames, out_dir, pix):
    if len(frames) < 2:
        return None
    changes = compute_changes(frames)
    warn = []
    ty, tx = (int(round(frames[0]['target_fits_px'][1])), int(round(frames[0]['target_fits_px'][0])))
    if any(f['sat'][ty % shape[0], tx % shape[1]] for f in frames):
        warn.append('saturated core: brightness at the target is not reliable; use the difference view or a redder band')
    man = export_bundle(out_dir, target, band, grid_wcs, shape, frames, changes, 'live SIA query (engine)', warn)
    if man['grid']['pix_arcsec'] != pix:          # export_bundle writes the config grid size; ours may differ
        man['grid']['pix_arcsec'] = pix
        (Path(out_dir) / 'manifest.json').write_text(json.dumps(man, indent=1))
    return man

def build_band(target, band, exps, center, out_dir, log=print, workers=12):
    """One band → frames + changes → C4 bundle (64×64 @ 6.15″, processing's default grid)."""
    grid_wcs, shape, frames = P_frames.build_frames(target, exps, center=center, workers=workers, log=log)
    return _bundle(target, band, grid_wcs, shape, frames, out_dir, P_frames.CFG['grid']['pix_arcsec'])

def build_zone(target, rows, center, out_dir, nx, per_epoch=None, log=print, workers=12):
    """A zone → I2 stacks (D4/D5/D6, visits shared across bands) for the discovery scan + a C4 bundle (D4) for viewing.
    Mirrors processing/stacks.py make(), but with live exposures."""
    exps = []
    for b in STACK_BANDS:
        exps += [dict(obs_id=r['obs_id'], det=r['band'], mjd=r['mjd'], release=r['collection'], url=r['s3'], epoch=None)
                 for r in rows if r['band'] == b]
    exps.sort(key=lambda e: e['mjd'])
    if not exps:
        return None
    assign_epochs(exps)                                    # visits defined once, across all bands
    exps = _cap(exps, STACK_BANDS, per_epoch)
    nv = max(e['epoch'] for e in exps) + 1
    img = np.full((len(STACK_BANDS), nv, nx, nx), np.nan, np.float32); err = np.full_like(img, np.nan)
    n = np.zeros((len(STACK_BANDS), nv), np.int16); grid = None; d4 = None
    for bi, b in enumerate(STACK_BANDS):
        sub = [e for e in exps if e['det'] == b]
        if not sub:
            continue
        grid, shape, frames = P_frames.build_frames(target, sub, center=center, nx=nx, ny=nx, pix_arcsec=STACK_PIX,
                                                    renumber=False, workers=workers, log=log)
        for f in frames:
            img[bi, f['epoch']] = f['flux']; err[bi, f['epoch']] = f['err']; n[bi, f['epoch']] = f['n_exposures']
        if b == 'D4':
            d4 = (grid, shape, [dict(f) for f in frames])
    visits = []
    for v in range(nv):
        m = [e['mjd'] for e in exps if e['epoch'] == v]
        visits.append(dict(id=v, mjd=float(np.mean(m)), start=Time(min(m), format='mjd').iso[:10], end=Time(max(m), format='mjd').iso[:10]))
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    h = grid.to_header()
    np.savez_compressed(out / 'stacks.npz', img=img, n=n, err=err)
    (out / 'stacks.json').write_text(json.dumps(dict(
        contract='I2 stacks v0', target=target['id'], bands=STACK_BANDS,
        grid=dict(nx=nx, ny=nx, pix_arcsec=STACK_PIX, wcs={k: h[k] for k in h}), visits=visits,
        band_lambda_um={b: lam_range(b) for b in STACK_BANDS},
        units='MJy/sr, zodi + background subtracted, inverse-variance mean per band x visit', nan='no data or masked (hard flags)',
        source='SPHEREx DR1+QR3, S3 sections, live (backend/engine)', orientation='FITS order: row 0 = south'), indent=1))
    man = None
    if d4:   # viewer bundle: renumber epochs that have D4 data so the C4 frames are 0..N-1
        g, shp, fr = d4
        for k, f in enumerate(fr):
            f['epoch'] = k
        man = _bundle(target, 'D4', g, shp, fr, out / 'D4', STACK_PIX)
    return dict(stacks_dir=str(out), n_exposures=len(exps), visits=visits, manifest=man)
