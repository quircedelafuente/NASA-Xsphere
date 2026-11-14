"""Chunk A ↔ chunk B bridge: live inventory (A3) → Quirce's frame engine (processing/frames.py, change.py, export.py).
Live results are written in the SAME C4 bundle format as the pre-built ones, so the frontend has one reader."""
import sys, threading
from . import config, inventory

sys.path.insert(0, str(config.ROOT))          # `processing` is a top-level package in the repo
from processing import frames as P_frames      # noqa: E402  (Quirce)
from processing.bands import detectors         # noqa: E402
from processing.change import compute_changes  # noqa: E402
from processing.config import CFG              # noqa: E402
from processing.exposures import assign_epochs  # noqa: E402
from processing.export import export_bundle    # noqa: E402

_grid_lock = threading.Lock()

def exposures(rows, band, per_epoch=None):
    """Our live SIA rows → processing's exposure dicts, epochs by processing's own D4 rule; optionally capped per epoch × detector."""
    dets = detectors(band)
    exps = [dict(obs_id=r['obs_id'], det=r['band'], mjd=r['mjd'], release=r['collection'], url=r['s3'], epoch=None)
            for r in rows if r['band'] in dets]
    exps.sort(key=lambda e: e['mjd'])
    if not exps:
        return []
    assign_epochs(exps)
    if per_epoch:
        keep = []
        for ep in sorted({e['epoch'] for e in exps}):
            for d in dets:
                g = [e for e in exps if e['epoch'] == ep and e['det'] == d]
                step = max(len(g) / per_epoch, 1)
                keep += [g[int(i * step)] for i in range(min(per_epoch, len(g)))]
        exps = sorted(keep, key=lambda e: e['mjd'])
    return exps

def field_target(ra, dec, name=None):
    """A position without catalogue motion, shaped like a C1 target so processing can use it."""
    return dict(id=f'field-{ra:.4f}{dec:+.4f}', name=name or f'Field {ra:.4f} {dec:+.4f}', ra_deg=ra, dec_deg=dec,
                ref_epoch=2016.0, pmra_masyr=0.0, pmdec_masyr=0.0, plx_mas=0.1, kind='field')

def build_band(target, band, exps, center, out_dir, grid_px=None, log=print, workers=12):
    """Frames + changes + C4 export for one band. grid_px > 64 for zones (processing's grid is fixed in config.yaml)."""
    if grid_px and grid_px != CFG['grid']['nx']:
        # shortcut: processing.common_grid reads nx/ny from the shared CFG dict; we swap it under a lock.
        # Upgrade: ask Quirce to add an optional grid size parameter to build_frames.
        with _grid_lock:
            old = (CFG['grid']['nx'], CFG['grid']['ny'])
            CFG['grid']['nx'] = CFG['grid']['ny'] = int(grid_px)
            try:
                grid_wcs, shape, frames = P_frames.build_frames(target, exps, center=center, workers=workers, log=log)
            finally:
                CFG['grid']['nx'], CFG['grid']['ny'] = old
    else:
        grid_wcs, shape, frames = P_frames.build_frames(target, exps, center=center, workers=workers, log=log)
    if len(frames) < 2:
        return None, (grid_wcs, shape, frames, [])
    changes = compute_changes(frames)
    warn = []
    ty, tx = (int(round(frames[0]['target_fits_px'][1])), int(round(frames[0]['target_fits_px'][0])))
    if any(f['sat'][ty % shape[0], tx % shape[1]] for f in frames):
        warn.append('saturated core: brightness at the target is not reliable; use the difference view or a redder band')
    man = export_bundle(out_dir, target, band, grid_wcs, shape, frames, changes, 'live SIA query (engine)', warn)
    return man, (grid_wcs, shape, frames, changes)
