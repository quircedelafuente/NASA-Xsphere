"""Spectrum on the fly: one point per exposure, at the wavelength that exposure saw the target (all 6 detectors).

SPHEREx's filters change across each detector, so every photo measures the target at its own wavelength. The
per-pixel wavelength comes from the file's WCS-WAVE table (alternate WCS 'W'). Output: the same points schema as
/bundles/<id>/spectrum.json, written to web/public/bundles/<id>/spectrum_full.json (the engine serves it first).

    venv/bin/python -m processing.spectrum barnards-star [more ids ...]
"""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from astropy.io import fits
from astropy.wcs import WCS
from astropy.wcs.utils import proj_plane_pixel_area

from .bands import DETECTOR_UM
from .config import CFG
from .exposures import assign_epochs, list_exposures
from .frames import sky_at
from .targets import get_target

ROOT = Path(__file__).resolve().parents[1]
R_AP, R_IN, R_OUT = 2.0, 4.0, 7.0          # native 6.15″ pixels; PSF FWHM ≈ 1.5 px


def aperture(img, var, x, y):
    """(flux, err) in image units × pixels: sum inside R_AP minus the annulus median. NaN if the aperture is bad."""
    yy, xx = np.indices(img.shape)
    r = np.hypot(xx - x, yy - y)
    ap, an = r <= R_AP, (r >= R_IN) & (r <= R_OUT)
    if not np.isfinite(img[ap]).all() or np.isfinite(img[an]).sum() < 10:
        return np.nan, np.nan
    bg = np.nanmedian(img[an])
    return float(np.sum(img[ap] - bg)), float(np.sqrt(np.sum(var[ap])))


def measure(target, exp):
    with fits.open(exp["url"], use_fsspec=True, fsspec_kwargs={"block_size": 512_000}) as h:
        hdr = h["IMAGE"].header
        w = WCS(hdr)
        x, y = (float(v) for v in w.world_to_pixel(sky_at(target, exp["mjd"])))
        xi, yi, n = int(round(x)), int(round(y)), int(R_OUT) + 2
        if not (n <= xi < hdr["NAXIS1"] - n and n <= yi < hdr["NAXIS2"] - n):
            return None
        sl = (slice(yi - n, yi + n + 1), slice(xi - n, xi + n + 1))
        img = h["IMAGE"].section[sl].astype(float) - h["ZODI"].section[sl].astype(float)
        var = h["VARIANCE"].section[sl].astype(float)
        flg = h["FLAGS"].section[sl].astype(np.int64)
        lam, bw = WCS(hdr, fobj=h, key="W").pixel_to_world_values(x, y)
    hard = sum(1 << b for b in CFG["flags"]["hard_mask_bits"])
    sat = sum(1 << b for b in CFG["flags"]["saturation_bits"])
    img = np.where((flg & hard) != 0, np.nan, img)
    f, e = aperture(img, var, x - (xi - n), y - (yi - n))
    if not np.isfinite(f):
        return None
    to_ujy = proj_plane_pixel_area(w) * (np.pi / 180) ** 2 * 1e12    # MJy/sr × pixel solid angle → µJy
    near = flg[n - 2:n + 3, n - 2:n + 3]
    return dict(wl_um=round(float(lam), 4), bw_um=round(float(bw), 4), flux=round(f * to_ujy, 2), err=round(e * to_ujy, 2),
                mjd=round(exp["mjd"], 4), det=exp["det"], flagged=bool((near & sat).any()))


def build(tid, workers=16, log=print):
    t = get_target(tid)
    exps = [e for d in DETECTOR_UM for e in list_exposures(t, d)[0]]
    exps.sort(key=lambda e: e["mjd"])
    for e in exps:
        e["epoch"] = None
    assign_epochs(exps)                                             # one visit numbering across all detectors
    log(f"{tid}: {len(exps)} exposures over 6 detectors")
    pts = []
    with ThreadPoolExecutor(workers) as pool:
        for e, fu in [(e, pool.submit(measure, t, e)) for e in exps]:
            try:
                p = fu.result()
            except Exception as ex:                                  # one bad file never kills the run
                log(f"  skip {e['obs_id']} {e['det']}: {ex.__class__.__name__}")
                continue
            if p:
                pts.append(p | {"epoch": e["epoch"]})
    pts.sort(key=lambda p: (p["epoch"], p["wl_um"]))
    out = ROOT / "web" / "public" / "bundles" / tid / "spectrum_full.json"
    out.write_text(json.dumps(dict(target_id=tid, aperture_px=R_AP, units="µJy (per-exposure aperture photometry, processing/spectrum.py)",
                                   points=pts, official_tool="https://irsa.ipac.caltech.edu/applications/spherex/tool-spectrophotometry")))
    log(f"{tid}: {len(pts)} points → {out.relative_to(ROOT)}")
    return pts


if __name__ == "__main__":
    for tid in sys.argv[1:]:
        build(tid)
