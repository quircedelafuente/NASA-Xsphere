"""Write I2 "stacks" (contracts/README.md) from our frame engine, for any target in data/targets.json.

Chunk A (backend/) is the official producer of I2. This adapter lets chunk B develop and test on all five targets
now, with the same shapes. Extra optional fields: `err` (1-sigma per pixel) in the npz.

  python -m processing.stacks --target wise-0855 --out contracts/fixtures/wise-0855
"""
import argparse, json
from pathlib import Path

import numpy as np
from astropy.time import Time

from .config import ROOT
from .exposures import assign_epochs, list_exposures
from .frames import build_frames, sky_at
from .targets import get_target, load_targets

BANDS = ["D4", "D5", "D6"]
LAM = {"D4": [2.42, 3.82], "D5": [3.83, 4.41], "D6": [4.42, 5.00]}


def make(target, out, nx=112, pix=3.075, log=print):
    exps = []
    for b in BANDS:
        e, _ = list_exposures(target, b)
        exps += e
    exps.sort(key=lambda e: e["mjd"])
    assign_epochs(exps)                                   # visits defined once, across all bands
    nv = max(e["epoch"] for e in exps) + 1
    center = sky_at(target, float(np.mean([e["mjd"] for e in exps])))
    img = np.full((len(BANDS), nv, nx, nx), np.nan, np.float32)
    err = np.full_like(img, np.nan); n = np.zeros((len(BANDS), nv), np.int16)
    grid = None
    for bi, b in enumerate(BANDS):
        sub = [e for e in exps if e["det"] == b]
        grid, _, frames = build_frames(target, sub, center=center, nx=nx, ny=nx, pix_arcsec=pix, renumber=False,
                                       log=lambda *a: None)
        for f in frames:
            img[bi, f["epoch"]] = f["flux"]; err[bi, f["epoch"]] = f["err"]; n[bi, f["epoch"]] = f["n_exposures"]
        log(f"  {b}: {len(sub)} exposures -> visits {[f['epoch'] for f in frames]}")
    visits = []
    for v in range(nv):
        m = [e["mjd"] for e in exps if e["epoch"] == v]
        visits.append({"id": v, "mjd": float(np.mean(m)), "start": Time(min(m), format="mjd").iso[:10],
                       "end": Time(max(m), format="mjd").iso[:10]})
    h = grid.to_header()
    meta = {"contract": "I2 stacks v0", "target": target["id"], "bands": BANDS,
            "grid": {"nx": nx, "ny": nx, "pix_arcsec": pix, "wcs": {k: h[k] for k in h}},
            "visits": visits, "band_lambda_um": LAM,
            "units": "MJy/sr, zodi + background subtracted, inverse-variance mean per band x visit",
            "nan": "no data or masked (hard flags)", "source": "SPHEREx DR1+QR3, S3 sections (processing/stacks.py adapter)",
            "orientation": "FITS order: row 0 = south (same as the chunk A fixture)"}
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out / "stacks.npz", img=img, n=n, err=err)
    (out / "stacks.json").write_text(json.dumps(meta, indent=1))
    log(f"{target['id']}: {nv} visits x {len(BANDS)} bands, {nx}x{nx} @ {pix}\" -> {out}")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--target"); ap.add_argument("--all", action="store_true")
    ap.add_argument("--out"); ap.add_argument("--nx", type=int, default=112)
    a = ap.parse_args()
    for t in (load_targets() if a.all else [get_target(a.target)]):
        make(t, a.out or ROOT / "processing" / "cache" / "stacks" / t["id"], nx=a.nx)


if __name__ == "__main__":
    main()
