"""B1 · find every dot in every merged image (per visit, all bands combined), with masks.

Detection image per visit = mean over bands of (image - local background) / noise. Peaks above `thr` sigma
are sources. Saturated stars have NaN cores: a NaN hole ringed by bright pixels is reported as a source with the
flag `saturated-core` (its position = centre of the hole).
"""
import numpy as np
from scipy import ndimage


def _robust_sigma(a):
    v = a[np.isfinite(a)]
    if v.size < 20:
        return np.nan
    return 1.4826 * np.median(np.abs(v - np.median(v)))


def background_sub(img, box=15):
    fill = np.where(np.isfinite(img), img, np.nanmedian(img))
    bkg = ndimage.median_filter(fill, size=box)
    return img - bkg


def snr_image(stk, b, v):
    im = stk["img"][b, v]
    if not np.isfinite(im).any():
        return None
    r = background_sub(im)
    s = _robust_sigma(r)
    return r / s if s and np.isfinite(s) and s > 0 else None


def detection_image(stk, v, smooth=1.0, bands=None):
    idx = range(len(stk["bands"])) if bands is None else [stk["bands"].index(b) for b in bands if b in stk["bands"]]
    maps = [m for m in (snr_image(stk, b, v) for b in idx) if m is not None]
    if not maps:
        return None, None
    nanany = np.any([~np.isfinite(m) for m in maps], axis=0)
    stack = np.nanmean(np.stack(maps), axis=0) * np.sqrt(len(maps))
    sm = ndimage.gaussian_filter(np.nan_to_num(stack), smooth)
    s = _robust_sigma(sm[~nanany])
    return sm / s, nanany


def _saturated_holes(stk, v, det):
    """NaN regions inside the field whose surrounding ring is very bright."""
    out = []
    for b in range(len(stk["bands"])):
        im = stk["img"][b, v]
        if not np.isfinite(im).any():
            continue
        lab, n = ndimage.label(~np.isfinite(im))
        for k in range(1, n + 1):
            ys, xs = np.nonzero(lab == k)
            if len(ys) > 400 or ys.min() == 0 or xs.min() == 0 or ys.max() == im.shape[0] - 1 or xs.max() == im.shape[1] - 1:
                continue                                          # edge / no-coverage areas
            ring = ndimage.binary_dilation(lab == k, iterations=2) & ~(lab == k)
            if np.nanmedian(det[ring]) > 15:
                out.append((float(xs.mean()), float(ys.mean()), int(len(ys)), stk["bands"][b]))
    merged = []
    for x, y, npx, b in sorted(out, key=lambda t: -t[2]):
        if all(np.hypot(x - m["x"], y - m["y"]) > 3 for m in merged):
            merged.append({"x": x, "y": y, "snr": 999.0, "sat": True, "hole_px": npx, "bands_sat": [b]})
        else:
            for m in merged:
                if np.hypot(x - m["x"], y - m["y"]) <= 3 and b not in m["bands_sat"]:
                    m["bands_sat"].append(b)
    return merged


RED = ["D5", "D6"]          # 3.8-5 um: where cold brown dwarfs are brightest (and nearly invisible bluer)


def _peaks(det, nanany, sat, thr, edge):
    ny, nx = det.shape
    pk = (det == ndimage.maximum_filter(det, size=5)) & (det > thr)
    ys, xs = np.nonzero(pk)
    near_nan = ndimage.binary_dilation(nanany, iterations=1)
    out = []
    for y, x in zip(ys, xs):
        if x < edge or y < edge or x >= nx - edge or y >= ny - edge:
            continue
        if any(np.hypot(x - s["x"], y - s["y"]) < 2.5 + np.sqrt(s["hole_px"] / np.pi) for s in sat):
            continue
        sub = det[y - 2:y + 3, x - 2:x + 3].clip(0)
        yy, xx = np.mgrid[-2:3, -2:3]
        out.append({"x": float(x + (sub * xx).sum() / sub.sum()), "y": float(y + (sub * yy).sum() / sub.sum()),
                    "snr": float(det[y, x]), "sat": False, "near_mask": bool(near_nan[y, x])})
    return out


def detect_visit(stk, v, thr=5.0, edge=3):
    det, nanany = detection_image(stk, v)
    if det is None:
        return []
    sat = _saturated_holes(stk, v, det)
    srcs = _peaks(det, nanany, sat, thr, edge)
    # second pass on the red bands only: finds objects that only shine at 3.8-5 um (cold brown dwarfs)
    if len([b for b in RED if b in stk["bands"]]) and len(stk["bands"]) > 2:
        rdet, rnan = detection_image(stk, v, bands=RED)
        if rdet is not None:
            for r in _peaks(rdet, rnan, sat, thr, edge):
                if all(np.hypot(r["x"] - s["x"], r["y"] - s["y"]) > 1.5 for s in srcs):
                    r["red_only"] = True
                    srcs.append(r)
    ny, nx = det.shape
    for s in sat:
        s["near_mask"] = True
    return _finish_sat(stk, v, srcs, sat, nx, ny)


def _finish_sat(stk, v, srcs, sat, nx, ny):
    for s in sat:
        s["near_mask"] = True
        # better position for a saturated star: the peak in the bands that are NOT saturated there
        ok = [b for b in range(len(stk["bands"])) if stk["bands"][b] not in s["bands_sat"]]
        maps = [m for m in (snr_image(stk, b, v) for b in ok) if m is not None]
        if maps:
            m = ndimage.gaussian_filter(np.nan_to_num(np.nanmean(np.stack(maps), 0)), 1.0)
            x0, y0 = int(round(s["x"])), int(round(s["y"]))
            r = int(np.ceil(np.sqrt(s["hole_px"] / np.pi))) + 2
            ys0, ys1, xs0, xs1 = max(y0 - r, 0), y0 + r + 1, max(x0 - r, 0), x0 + r + 1
            sub = m[ys0:ys1, xs0:xs1]
            if sub.size and np.isfinite(sub).all():
                py, px = np.unravel_index(np.argmax(sub), sub.shape)
                py += ys0; px += xs0
                if 2 <= px < nx - 2 and 2 <= py < ny - 2:
                    w = m[py - 2:py + 3, px - 2:px + 3].clip(0)
                    yy, xx = np.mgrid[-2:3, -2:3]
                    if w.sum() > 0:
                        s["x"] = float(px + (w * xx).sum() / w.sum()); s["y"] = float(py + (w * yy).sum() / w.sum())
                        s["pos_from"] = "unsaturated bands"
    return srcs + sat


def detect_all(stk, thr=5.0):
    return [detect_visit(stk, v, thr) for v in range(len(stk["mjd"]))]


def psf_fwhm(stk, dets):
    """Median FWHM (px) of bright isolated unsaturated detections, from second moments."""
    vals = []
    for v, ds in enumerate(dets):
        det, _ = detection_image(stk, v, smooth=0.01)
        if det is None:
            continue
        for d in ds:
            if d["sat"] or not (15 < d["snr"] < 200):
                continue
            x, y = int(round(d["x"])), int(round(d["y"]))
            if x < 4 or y < 4 or x >= det.shape[1] - 4 or y >= det.shape[0] - 4:
                continue
            sub = det[y - 3:y + 4, x - 3:x + 4].clip(0)
            yy, xx = np.mgrid[-3:4, -3:4]
            m0 = sub.sum()
            sx = (sub * (xx - (sub * xx).sum() / m0) ** 2).sum() / m0
            sy = (sub * (yy - (sub * yy).sum() / m0) ** 2).sum() / m0
            vals.append(2.355 * np.sqrt(max((sx + sy) / 2, 0.1)))
    return float(np.median(vals)) if vals else 3.0
