"""B5/B6 · aperture photometry per band per visit at the source position of that visit (along its path)."""
import numpy as np


def aperture(img, err, x, y, r=3.0, r_in=6.0, r_out=10.0):
    ny, nx = img.shape
    yy, xx = np.mgrid[0:ny, 0:nx]
    d = np.hypot(xx - x, yy - y)
    ap = d <= r
    an = (d >= r_in) & (d <= r_out) & np.isfinite(img)
    if an.sum() < 10:
        return np.nan, np.nan, "no-annulus"
    sky = np.median(img[an])
    sky_sig = 1.4826 * np.median(np.abs(img[an] - sky))
    vals = img[ap]
    if (~np.isfinite(vals)).any():
        # saturated / masked core: report the halo (r..2r) as a relative brightness proxy, flagged
        halo = (d > r) & (d <= 2 * r) & np.isfinite(img)
        if halo.sum() < 5:
            return np.nan, np.nan, "masked"
        f = (img[halo] - sky).sum()
        e = sky_sig * np.sqrt(halo.sum())
        return float(f), float(e), "halo-only"
    f = (vals - sky).sum()
    # empirical noise from the annulus scatter (captures what the pipeline variance misses: lambda mix, residuals)
    e = sky_sig * np.sqrt(ap.sum() * (1 + ap.sum() / max(an.sum(), 1)))
    if err is not None and np.isfinite(err[ap]).all():
        e = max(e, float(np.sqrt((err[ap] ** 2).sum())))
    return float(f), float(e), "ok"


def measure_track(stk, positions, r=3.0):
    """positions: {visit: (x, y)} -> flux table [band][visit] in microJy with errors and quality."""
    out = {}
    for bi, b in enumerate(stk["bands"]):
        row = []
        for v, (x, y) in sorted(positions.items()):
            img = stk["img"][bi, v]
            err = None if stk["err"] is None else stk["err"][bi, v]
            if not np.isfinite(img).any():
                row.append({"visit": v, "flux": None, "err": None, "q": "no-data"}); continue
            f, e, q = aperture(img, err, x, y, r)
            k = stk["pix_to_ujy"]
            row.append({"visit": v, "flux": None if not np.isfinite(f) else round(f * k, 2),
                        "err": None if not np.isfinite(e) else round(e * k, 2), "q": q})
        out[b] = row
    return out
