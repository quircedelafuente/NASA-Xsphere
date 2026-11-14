"""One command: target (or RA/Dec) + band -> C4 bundle with frames, diffs and change candidates.

  python -m processing.build --target barnards-star --band D4
  python -m processing.build --ra 133.7595 --dec -7.2422 --band D56 --name my-field   # fixed patch
  python -m processing.build --all                                                    # 5 targets, default band
"""
import argparse
import json
import time

import astropy.units as u
import numpy as np
from astropy.coordinates import SkyCoord

from .bands import detectors
from .change import compute_changes
from .config import CFG, ROOT
from .exposures import list_exposures
from .export import export_bundle
from .frames import build_frames
from .targets import get_target, load_targets


def run(target, band, center=None):
    t0 = time.time()
    exps, source = list_exposures(target, band)
    if not exps:
        print(f"{target['id']} {band}: no exposures"); return None
    grid_wcs, shape, frames = build_frames(target, exps, center=center)
    if len(frames) < 2:
        print(f"{target['id']} {band}: only {len(frames)} epoch(s), nothing to compare"); return None
    changes = compute_changes(frames)
    warn = []
    if any(f["sat"][int(round(f['target_fits_px'][1])) % shape[0], int(round(f['target_fits_px'][0])) % shape[1]]
           for f in frames):
        warn.append("saturated core: brightness at the target is not reliable; use the difference view / a redder band")
    out = ROOT / CFG["bundles_dir"] / target["id"] / band
    man = export_bundle(out, target, band, grid_wcs, shape, frames, changes, source, warn)
    n_c = sum(len(d["candidates"]) for d in man["diffs"] if d["from"] == 0)
    print(f"{target['id']} {band}: {len(frames)} epochs, {n_c} change candidates vs epoch 0 -> {out.relative_to(ROOT)} "
          f"({time.time() - t0:.0f}s)")
    return man


def update_index():
    root = ROOT / CFG["bundles_dir"]
    idx = []
    for t in load_targets():
        d = root / t["id"]
        bands = sorted(p.parent.name for p in d.glob("*/manifest.json")) if d.exists() else []
        if bands:
            m = json.loads((d / bands[0] / "manifest.json").read_text())
            idx.append({"id": t["id"], "name": t["name"], "kind": t.get("kind"), "bands": bands,
                        "default_band": t.get("default_band"), "n_epochs": len(m["frames"]),
                        "thumb": f"{t['id']}/{bands[0]}/e0.png"})
    (root / "index.json").write_text(json.dumps(idx, indent=1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target"); ap.add_argument("--band")
    ap.add_argument("--ra", type=float); ap.add_argument("--dec", type=float); ap.add_argument("--name")
    ap.add_argument("--sia", help="SIA table for a custom position (ecsv)")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    if a.all:
        for t in load_targets():
            run(t, a.band or t["default_band"])
    elif a.ra is not None:
        if not a.sia:
            raise SystemExit("--ra/--dec needs --sia <table.ecsv> until the live SIA query is wired (P6)")
        t = {"id": a.name or f"field-{a.ra:.4f}{a.dec:+.4f}", "name": a.name or "custom field",
             "ra_deg": a.ra, "dec_deg": a.dec, "ref_epoch": 2016.0, "sia": a.sia}
        run(t, a.band or "D4", center=SkyCoord(a.ra * u.deg, a.dec * u.deg))
    else:
        t = get_target(a.target)
        detectors(a.band or t["default_band"])
        run(t, a.band or t["default_band"])
    update_index()


if __name__ == "__main__":
    main()
