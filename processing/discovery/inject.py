"""B8 · recovery test: inject fake movers of known speed and brightness into real stacks, run B1+B2, count hits.

  python -m processing.discovery.inject processing/cache/stacks/barnards-star --trials 6
"""
import argparse, copy, json

import numpy as np

from . import detect as D, link as L
from .stacks_io import load


def _gain(stk, fwhm, rng, tries=6):
    """Detection-map S/N produced by a source whose per-band peak is 1 x that band's pixel noise.
    Calibrates injected brightness against the real (confusion-limited) detection noise, not white noise."""
    from . import detect as D
    nb, nv, ny, nx = stk["img"].shape
    sig = fwhm / 2.355; yy, xx = np.mgrid[0:ny, 0:nx]; g = []
    for _ in range(tries):
        k = int(rng.integers(nv)); x, y = rng.uniform(10, nx - 10), rng.uniform(10, ny - 10)
        s = copy.copy(stk); s["img"] = stk["img"].copy()
        for b in range(nb):
            im = s["img"][b, k]
            if np.isfinite(im).any():
                noise = D._robust_sigma(D.background_sub(im))
                s["img"][b, k] = im + 20 * noise * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * sig ** 2))
        d0, _ = D.detection_image(stk, k); d1, _ = D.detection_image(s, k)
        xi, yi = int(round(x)), int(round(y))
        g.append(float((d1 - d0)[yi - 1:yi + 2, xi - 1:xi + 2].max()) / 20)
    return float(np.median(g))


def inject(stk, rng, n, speed_arcsec_yr, snr, fwhm, gain=None):
    """snr = signal-to-noise in the detection map (what the detector actually sees)."""
    nb, nv, ny, nx = stk["img"].shape
    s = copy.copy(stk); s["img"] = stk["img"].copy()
    sig = fwhm / 2.355
    yy, xx = np.mgrid[0:ny, 0:nx]
    t0 = float(np.mean(stk["year"]))
    truth = []
    for _ in range(n):
        ang = rng.uniform(0, 2 * np.pi)
        v = speed_arcsec_yr / stk["pix"] * np.array([np.cos(ang), np.sin(ang)])
        span = np.abs(v) * (stk["year"].max() - stk["year"].min())
        x0 = rng.uniform(8 + span[0], nx - 8 - span[0]); y0 = rng.uniform(8 + span[1], ny - 8 - span[1])
        for b in range(nb):
            for k in range(nv):
                im = s["img"][b, k]
                if not np.isfinite(im).any():
                    continue
                noise = D._robust_sigma(D.background_sub(im))
                amp = snr / gain * noise
                x = x0 + v[0] * (stk["year"][k] - t0); y = y0 + v[1] * (stk["year"][k] - t0)
                s["img"][b, k] = im + amp * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * sig ** 2))
        truth.append((x0, y0, v))
    return s, truth, t0


def run(stacks_dir, trials=6, per=6, speeds=(1, 2, 4, 6, 8, 10), snrs=(7, 10, 20), seed=1):
    stk = load(stacks_dir)
    base = D.detect_all(stk); fwhm = D.psf_fwhm(stk, base)
    rng = np.random.default_rng(seed)
    gain = _gain(stk, fwhm, rng)
    table = {}
    for sp in speeds:
        for sn in snrs:
            hit = tot = 0
            for _ in range(trials):
                s, truth, t0 = inject(stk, rng, per, sp, sn, fwhm, gain)
                dets = D.detect_all(s)
                tracks, _, _ = L.link(dets, s["year"], fwhm, s["pix"])
                for x0, y0, v in truth:
                    tot += 1
                    for t in tracks:
                        dt = t["t0"] - t0
                        if (np.hypot(t["x0"] - (x0 + v[0] * dt), t["y0"] - (y0 + v[1] * dt)) < 1.5
                                and abs(t["speed_px_yr"] - np.hypot(*v)) < 0.3 * np.hypot(*v) + 0.3 and t["motion_sig"] >= 5):
                            hit += 1; break
            table[f"{sp}″/yr S/N{sn}"] = round(hit / tot, 2)
    return {"stacks": stacks_dir, "pix_arcsec": stk["pix"], "fwhm_px": round(fwhm, 2), "baseline_years": round(float(np.ptp(stk["year"])), 2),
            "spherex_px_arcsec": 6.15, "snr_meaning": "peak S/N in the detection map (threshold 5)",
            "recovery": table}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("stacks"); ap.add_argument("--trials", type=int, default=6)
    a = ap.parse_args()
    print(json.dumps(run(a.stacks, a.trials), indent=1))


if __name__ == "__main__":
    main()
