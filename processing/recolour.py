"""Repaint the preview images (e<N>.png, blink.gif) of bundles that already exist, in false colour.

Reads only what is in the bundle (the .f32 frames and the stretch in manifest.json): no download, a second per bundle.
New bundles get the colour directly from processing/export.py.

  python -m processing.recolour                     # every bundle under web/public/bundles
  python -m processing.recolour cache/live/v_ab12   # one bundle folder, or a folder of bundles
"""
import json
import sys
from pathlib import Path

import numpy as np

from .config import CFG, ROOT
from .export import asinh_u8, save_previews


def recolour(band_dir):
    band_dir = Path(band_dir)
    m = json.loads((band_dir / "manifest.json").read_text())
    if "lam_range_um" not in m or "stretch" not in m:      # e.g. context/ (other surveys): left as it is
        return False
    g, s = m["grid"], m["stretch"]
    items = []
    for f in m["frames"]:
        a = np.fromfile(band_dir / f["f32"], "<f4").reshape(g["ny"], g["nx"])      # already north-up (web order)
        date = f.get("label") or f.get("date", "")
        items.append((f["epoch"], asinh_u8(a, s["vmin"], s["vmax"], s["a"]), f["target_px"], date))
    save_previews(band_dir, m.get("name", m["target_id"]), m["band"], items)
    return True


def main():
    roots = [Path(p) for p in sys.argv[1:]] or [ROOT / CFG["bundles_dir"]]
    for root in roots:
        for man in sorted(root.rglob("manifest.json")):
            done = recolour(man.parent)
            print(("recoloured " if done else "skipped    ") + str(man.parent))


if __name__ == "__main__":
    main()
