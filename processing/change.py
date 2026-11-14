"""What changed between epochs (P2 core, owner Quirce): sigma-difference images + change candidates.

The tool does not decide what an object is: it marks pixels whose brightness changed more than the noise
allows. A mover leaves a dipole (negative where it was, positive where it is); a variable star leaves a
single-sign blob. Everything listed here is a *candidate* (D13).
"""
import numpy as np
from scipy import ndimage

from .config import CFG


def sigma_diff(a, b):
    """(b - a) / sqrt(err_a^2 + err_b^2), NaN where either frame is masked.

    The pipeline VARIANCE ignores systematics (each epoch mixes slightly different wavelengths inside the
    band, PSF changes, calibration), so each error gets a fractional floor `sys_frac * |flux|`, and the
    result is rescaled so the median background pixel has a scatter of exactly 1 sigma.
    """
    k = CFG["change"].get("sys_frac", 0.1)
    ea = np.sqrt(a["err"] ** 2 + (k * np.abs(a["flux"])) ** 2)
    eb = np.sqrt(b["err"] ** 2 + (k * np.abs(b["flux"])) ** 2)
    d = (b["flux"] - a["flux"]) / np.sqrt(ea ** 2 + eb ** 2)
    v = d[np.isfinite(d)]
    if v.size > 50:
        mad = 1.4826 * np.median(np.abs(v - np.median(v)))
        if mad > 0:
            d = (d - np.median(v)) / mad
    return d.astype(np.float32)


def diff_pairs(n, reference=None):
    reference = reference or CFG["change"]["reference"]
    pairs = [(0, j) for j in range(1, n)]                       # vs first epoch
    pairs += [(i, i + 1) for i in range(1, n - 1)]              # consecutive (0->1 already there)
    if reference == "consecutive":
        pairs = [(i, i + 1) for i in range(n - 1)]
    return pairs


def find_candidates(d, sat_mask=None, thr=None, max_n=None):
    thr = thr or CFG["change"]["candidate_sigma"]
    max_n = max_n or CFG["change"]["max_candidates"]
    dd = np.nan_to_num(d)
    out = []
    for sign in (+1, -1):
        lab, n = ndimage.label(sign * dd >= thr)
        for k in range(1, n + 1):
            ys, xs = np.nonzero(lab == k)
            i = np.argmax(sign * dd[ys, xs])
            y, x = int(ys[i]), int(xs[i])
            out.append({"x": x, "y": y, "sigma": round(float(dd[y, x]), 1), "npix": int(len(ys)),
                        "kind": "brighter" if sign > 0 else "fainter",
                        "saturated": bool(sat_mask is not None and sat_mask[y, x])})
    # a brighter blob next to a fainter one (<= 4 px) = something that moved
    for c in out:
        for o in out:
            if c["kind"] != o["kind"] and np.hypot(c["x"] - o["x"], c["y"] - o["y"]) <= 4:
                c["kind"] = "moved"
    out.sort(key=lambda c: -abs(c["sigma"]))
    return out[:max_n]


def compute_changes(frames):
    """Returns list of {from,to,diff,candidates} with arrays in FITS orientation."""
    res = []
    for i, j in diff_pairs(len(frames)):
        d = sigma_diff(frames[i], frames[j])
        sat = frames[i]["sat"] | frames[j]["sat"]
        res.append({"from": i, "to": j, "diff": d, "candidates": find_candidates(d, sat)})
    return res
