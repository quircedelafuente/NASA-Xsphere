"""Long-baseline context (owner: Quirce): older images of the same patch from other telescopes.

2MASS (~1998-2001), AllWISE (~2010) and the last NEOWISE visit (~2024), all from NASA/IPAC IRSA, resampled onto
the same kind of north-up grid as SPHEREx (6.15"/px) but wider, so a fast mover stays inside. Followed by the
SPHEREx epochs on that same wide grid. These frames are CONTEXT only: different telescope, resolution and colour,
so they are never subtracted from SPHEREx and each frame has its own stretch.

  python -m processing.context --target wise-0855
  python -m processing.context --all
"""
import argparse, io, json, time, warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import requests
from astropy.io import ascii, fits
from astropy.stats import sigma_clipped_stats
from astropy.time import Time
from astropy.wcs import WCS, FITSFixedWarning
from PIL import Image
from reproject import reproject_interp

from .config import CFG, ROOT
from .exposures import list_exposures
from .export import web_px
from .frames import build_frames, common_grid, sky_at
from .targets import get_target, load_targets

warnings.simplefilter("ignore", FITSFixedWarning)
IBE = "https://irsa.ipac.caltech.edu/ibe"
CACHE = ROOT / CFG["cache_dir"] / "context"
# which archival band is closest in colour to the SPHEREx band we blink
WISE_BAND = {"D4": 1, "D56": 2, "D5": 2, "D6": 2, "D3": 1, "D2": 1, "D1": 1}


def _get(url, timeout=120):
    for k in range(4):
        try:
            r = requests.get(url, timeout=timeout)
            if r.status_code == 200:
                return r
        except requests.RequestException:
            pass
        time.sleep(2 * (k + 1))
    raise RuntimeError(f"IRSA request failed: {url[:120]}")


def _table(url):
    return ascii.read(_get(url).text, format="ipac")


def _cutout(url, ra, dec, size_deg):
    key = CACHE / (str(abs(hash((url, round(ra, 5), round(dec, 5), round(size_deg, 4))))) + ".fits")
    if not key.exists():
        r = _get(f"{url}?center={ra},{dec}&size={size_deg}deg&gzip=false", timeout=180)
        CACHE.mkdir(parents=True, exist_ok=True)
        key.write_bytes(r.content)
    with fits.open(key) as h:
        return h[0].data.astype(np.float32), h[0].header


def _on_grid(items, grid, shape):
    """Reproject a list of (data, header) cutouts and average them (fills gaps between overlapping images)."""
    from scipy.ndimage import gaussian_filter
    from astropy.wcs.utils import proj_plane_pixel_scales
    stack = []
    for data, hdr in items:
        if data is None or data.ndim != 2 or data.size < 100:
            continue
        w = WCS(hdr)
        _, med, _ = sigma_clipped_stats(data, sigma=3)
        data = np.nan_to_num(data - med)
        ratio = CFG["grid"]["pix_arcsec"] / (proj_plane_pixel_scales(w)[0] * 3600)
        if ratio > 1.5:                                       # anti-alias before going to 6.15"/px
            data = gaussian_filter(data, ratio / 2.5)
        a, fp = reproject_interp((data, w), grid, shape_out=shape)
        a[fp == 0] = np.nan
        stack.append(a)
    return np.nanmedian(stack, axis=0) if stack else None


def twomass(ra, dec, size, grid, shape):
    t = _table(f"{IBE}/search/twomass/allsky/allsky?POS={ra},{dec}&SIZE={size / 1.5:.4f}&INTERSECT=OVERLAPS")
    t = t[t["filter"] == "k"][:10]
    urls = [f"{IBE}/data/twomass/allsky/allsky/{r['ordate']}{r['hemisphere']}/s{int(r['scanno']):03d}/image/{r['fname']}"
            for r in t]
    with ThreadPoolExecutor(4) as p:
        items = [x for x in p.map(lambda u: _safe_cutout(u, ra, dec, size), urls) if x is not None]
    dates = [Time(f"20{str(r['ordate'])[:2]}-{str(r['ordate'])[2:4]}-{str(r['ordate'])[4:6]}"
                  if int(str(r['ordate'])[:2]) < 50 else f"19{str(r['ordate'])[:2]}-{str(r['ordate'])[2:4]}-{str(r['ordate'])[4:6]}").mjd
             for r in t]
    return _on_grid(items, grid, shape), float(np.mean(dates)), "2MASS", "Ks 2.2 µm"


def allwise(ra, dec, size, grid, shape, band):
    t = _table(f"{IBE}/search/wise/allwise/p3am_cdd?POS={ra},{dec}")
    t = t[t["band"] == band]
    items, mjds = [], []
    for r in t[:2]:
        c = str(r["coadd_id"])
        items.append(_cutout(f"{IBE}/data/wise/allwise/p3am_cdd/{c[:2]}/{c[:4]}/{c}/{c}-w{band}-int-3.fits", ra, dec, size))
        mjds.append(Time(str(r["mid_obs"]).replace(" ", "T")).mjd)
    lam = {1: "3.4 µm", 2: "4.6 µm"}[band]
    return _on_grid(items, grid, shape), float(np.mean(mjds)), "AllWISE", f"W{band} {lam}"


def neowise_last(ra, dec, size, grid, shape, band, max_frames=12):
    t = _table(f"{IBE}/search/wise/neowiser/p1bm_frm?POS={ra},{dec}&where=band={band}")
    t = t[t["qual_frame"] >= 5]
    if len(t) == 0:
        return None, None, "NEOWISE", ""
    last = t[t["mjd_obs"] > t["mjd_obs"].max() - 5]          # the last visit (a visit lasts ~1-2 days)
    last = last[np.argsort(last["mjd_obs"])][:max_frames]
    urls = [f"{IBE}/data/wise/neowiser/p1bm_frm/{r['scangrp']}/{r['scan_id']}/{int(r['frame_num']):03d}/"
            f"{r['scan_id']}{int(r['frame_num']):03d}-w{band}-int-1b.fits" for r in last]
    with ThreadPoolExecutor(6) as p:
        items = [x for x in p.map(lambda u: _safe_cutout(u, ra, dec, size), urls) if x is not None]
    lam = {1: "3.4 µm", 2: "4.6 µm"}[band]
    return _on_grid(items, grid, shape), float(np.mean(last["mjd_obs"])), "NEOWISE", f"W{band} {lam}"


def _safe_cutout(u, ra, dec, size):
    try:
        return _cutout(u, ra, dec, size)
    except Exception:
        return None


def _stretch_u8(a, p=(1, 99.7), aa=0.1):
    v = a[np.isfinite(a)]
    lo, hi = np.percentile(v, p)
    x = np.clip((a - lo) / (hi - lo), 0, 1)
    return np.where(np.isfinite(a), np.arcsinh(x / aa) / np.arcsinh(1 / aa) * 255, 0).astype(np.uint8)


def run(target, band=None, log=print):
    band = band or target["default_band"]
    t0 = time.time()
    exps, _ = list_exposures(target, band)
    # positions from 2MASS era to the last SPHEREx epoch -> grid wide enough for the whole track
    now = max(e["mjd"] for e in exps)
    p_old, p_new = sky_at(target, Time(1999.0, format="jyear").mjd), sky_at(target, now)
    mid = sky_at(target, (Time(1999.0, format="jyear").mjd + now) / 2)
    span_px = p_old.separation(p_new).arcsec / CFG["grid"]["pix_arcsec"]
    n = int(max(96, np.ceil((span_px + 48) / 16) * 16))
    grid, shape = common_grid(mid, n, n)
    size = n * CFG["grid"]["pix_arcsec"] / 3600 * 1.5
    ra, dec = mid.ra.deg, mid.dec.deg
    log(f"{target['id']}: context grid {n}x{n} px ({n * 6.15 / 60:.1f}'), motion since 1999 = {span_px:.0f} px")
    wb = WISE_BAND.get(band, 1)
    frames = []
    for fn in (lambda: twomass(ra, dec, size, grid, shape),
               lambda: allwise(ra, dec, size, grid, shape, wb),
               lambda: neowise_last(ra, dec, size, grid, shape, wb)):
        try:
            img, mjd, survey, filt = fn()
        except Exception as ex:
            log(f"  {fn.__name__ if hasattr(fn, '__name__') else 'survey'} failed: {ex}")
            continue
        if img is not None and np.isfinite(img).any():
            frames.append({"survey": survey, "filter": filt, "mjd": mjd, "img": img, "kind": "archive"})
            log(f"  {survey} {filt} {Time(mjd, format='mjd').iso[:10]}")
    _, _, sp = build_frames(target, exps, center=mid, nx=n, ny=n, log=lambda *a: None)
    for f in sp:
        frames.append({"survey": "SPHEREx", "filter": band, "mjd": f["mjd"], "img": f["flux"], "kind": "spherex"})
    log(f"  SPHEREx {band}: {len(sp)} epochs on the wide grid")

    out = ROOT / CFG["bundles_dir"] / target["id"] / "context"
    out.mkdir(parents=True, exist_ok=True)
    man = []
    for i, f in enumerate(frames):
        u8 = _stretch_u8(f["img"])[::-1]                          # web orientation: north up, top row first
        Image.fromarray(u8).save(out / f"c{i}.png")
        pos = sky_at(target, f["mjd"])
        x, y = grid.world_to_pixel(pos)
        t = Time(f["mjd"], format="mjd")
        man.append({"survey": f["survey"], "filter": f["filter"], "kind": f["kind"], "mjd": round(f["mjd"], 3),
                    "date": t.iso[:10], "year": round(t.jyear, 2), "png": f"c{i}.png",
                    "target_px": web_px((float(x), float(y)), n)})
    m = {"target_id": target["id"], "band": band, "grid": {"nx": n, "ny": n, "pix_arcsec": CFG["grid"]["pix_arcsec"],
         "center": [round(ra, 6), round(dec, 6)], "origin": "top-left, north up"},
         "note": "Context only: other telescopes, other resolution and colour. Never subtracted from SPHEREx; "
                 "each frame has its own stretch.",
         "frames": man, "track": [{"year": f["year"], "x": f["target_px"][0], "y": f["target_px"][1]} for f in man],
         "credits": ["2MASS: UMass/IPAC-Caltech, NASA/NSF", "WISE/NEOWISE: NASA/JPL-Caltech/UCLA", "Data via NASA/IPAC IRSA"]}
    (out / "manifest.json").write_text(json.dumps(m, indent=1))
    log(f"  -> {out.relative_to(ROOT)} ({time.time() - t0:.0f}s)")
    return m


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--target"); ap.add_argument("--band"); ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    for t in (load_targets() if a.all else [get_target(a.target)]):
        run(t, a.band)


if __name__ == "__main__":
    main()
