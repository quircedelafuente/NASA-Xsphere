"""Read I2 stacks (contracts/README.md)."""
import json
from pathlib import Path

import numpy as np
from astropy.time import Time
from astropy.wcs import WCS

PIX_SR_PER_ARCSEC2 = (1 / 206264.806) ** 2


def load(stacks_dir):
    d = Path(stacks_dir)
    z = np.load(d / "stacks.npz")
    m = json.loads((d / "stacks.json").read_text())
    img = z["img"].astype(np.float32)
    w = WCS(m["grid"]["wcs"])
    pix = float(m["grid"]["pix_arcsec"])
    mjd = np.array([v["mjd"] for v in m["visits"]])
    return {
        "dir": str(d), "meta": m, "img": img, "n": z["n"],
        "err": z["err"].astype(np.float32) if "err" in z.files else None,
        "wcs": w, "pix": pix, "bands": list(m["bands"]), "mjd": mjd,
        "year": Time(mjd, format="mjd").jyear,
        "lam": {b: float(np.mean(m["band_lambda_um"][b])) for b in m["bands"]},
        # MJy/sr in one pixel -> microJy
        "pix_to_ujy": 1e6 * 1e6 * pix ** 2 * PIX_SR_PER_ARCSEC2,
        "spectrum_points": m.get("spectrum_points", []),
        "target": m.get("target"),
    }
