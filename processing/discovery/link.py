"""B2 · link dots across visits and fit straight-line motion.

For anchor pairs of visits (first/last and neighbours) every pair of detections closer than the maximum allowed
motion defines a line; the line predicts where the dot must be at every other visit. A track is kept when it has
a detection within `tol` px at >= min_visits visits. Tracks are chosen greedily (most visits, smallest residual,
slowest motion first) so each detection is used once.

Chance lines: with detection density rho (per px^2) in a visit, a random dot falls inside the tolerance circle with
p = rho * pi * tol^2. A moving track confirmed at k extra visits beyond its two anchors has an expected number of
chance look-alikes ~ n_pairs * prod(p_k). Movers are kept only when that is < 1 (WORKSPLIT B2).
"""
import numpy as np
from scipy.spatial import cKDTree


def _anchor_pairs(nv):
    pairs = [(0, nv - 1)]
    if nv >= 4:
        pairs += [(0, nv - 2), (1, nv - 1)]
    if nv >= 6:
        pairs += [(1, nv - 2)]
    return [p for p in pairs if p[1] - p[0] >= 2 or nv == 2]


def link(dets, years, fwhm, pix_arcsec, max_pm_arcsec_yr=12.0, min_visits=3):
    nv = len(dets)
    tol = max(1.0, 0.45 * fwhm)
    pts = [np.array([[d["x"], d["y"]] for d in ds]) if ds else np.zeros((0, 2)) for ds in dets]
    trees = [cKDTree(p) if len(p) else None for p in pts]
    area = None
    cand = []
    n_pairs_moving = 0
    for i, j in _anchor_pairs(nv):
        if trees[i] is None or trees[j] is None:
            continue
        dt = years[j] - years[i]
        rmax = max_pm_arcsec_yr * dt / pix_arcsec + tol
        for a, pa in enumerate(pts[i]):
            for b in trees[j].query_ball_point(pa, rmax):
                pb = pts[j][b]
                vel = (pb - pa) / dt
                if np.hypot(*vel) * dt > 2 * tol:
                    n_pairs_moving += 1
                members = {i: a, j: b}
                for k in range(nv):
                    if k in members or trees[k] is None:
                        continue
                    pred = pa + vel * (years[k] - years[i])
                    dd, idx = trees[k].query(pred, distance_upper_bound=tol)
                    if np.isfinite(dd):
                        members[k] = idx
                if len(members) >= min(min_visits, nv):
                    cand.append(members)
    # fit every candidate, then pick greedily
    fits = []
    for mem in cand:
        f = fit(mem, dets, years, fwhm)
        fits.append((len(mem), f["rms_px"], f["speed_px_yr"], mem, f))
    fits.sort(key=lambda t: (-t[0], round(t[1], 1), t[2]))
    used = set(); tracks = []
    for nvis, rms, sp, mem, f in fits:
        keys = {(k, i) for k, i in mem.items()}
        if keys & used or rms > tol:
            continue
        used |= keys
        tracks.append(f)
    singles = [{"visit": k, **dets[k][i], "idx": i} for k in range(nv) for i in range(len(dets[k])) if (k, i) not in used]
    return tracks, singles, {"tol_px": tol, "n_pairs_moving": n_pairs_moving}


def fit(members, dets, years, fwhm):
    ks = sorted(members)
    xy = np.array([[dets[k][members[k]]["x"], dets[k][members[k]]["y"]] for k in ks])
    snr = np.array([min(dets[k][members[k]]["snr"], 200) for k in ks])
    t = np.array([years[k] for k in ks])
    sat = any(dets[k][members[k]]["sat"] for k in ks)
    sat_hole_pos = any(dets[k][members[k]]["sat"] and "pos_from" not in dets[k][members[k]] for k in ks)
    # positional error per detection: centroid noise + 0.15 px registration floor (+ more for saturated holes)
    sig = np.sqrt((0.6 * fwhm / snr) ** 2 + 0.15 ** 2 + (0.5 ** 2 if sat_hole_pos else 0))
    t0 = np.average(t, weights=1 / sig ** 2)
    A = np.vstack([np.ones_like(t), t - t0]).T
    W = np.diag(1 / sig ** 2)
    cov = np.linalg.inv(A.T @ W @ A)
    px, py = cov @ A.T @ W @ xy[:, 0], cov @ A.T @ W @ xy[:, 1]
    res = xy - np.vstack([A @ px, A @ py]).T
    rms = float(np.sqrt((res ** 2).sum(1).mean())) if len(ks) > 2 else 0.0
    # scale errors up if residuals say so (only with >= 3 points)
    chi2 = float(((res ** 2).sum(1) / sig ** 2).sum())
    dof = max(2 * len(ks) - 4, 1)
    scale = np.sqrt(max(chi2 / dof, 1.0)) if len(ks) > 2 else 1.0
    sv = np.sqrt(cov[1, 1]) * scale
    v = np.array([px[1], py[1]])
    return {"members": {int(k): int(members[k]) for k in ks}, "t0": float(t0),
            "x0": float(px[0]), "y0": float(py[0]), "vx": float(v[0]), "vy": float(v[1]),
            "sig_v_px_yr": float(sv), "speed_px_yr": float(np.hypot(*v)),
            "motion_sig": float(np.hypot(*v) / sv) if sv > 0 else 0.0,
            "rms_px": rms, "n_visits": len(ks), "saturated": sat,
            "snr_max": float(snr.max())}


def chance_lines(track, dets, n_pairs_moving, tol, area_px2):
    """Expected number of random dot alignments that would look like this mover."""
    extra = [k for k in track["members"]][1:-1]                    # visits beyond the two anchors
    p = 1.0
    for k in extra:
        p *= len(dets[k]) / area_px2 * np.pi * tol ** 2
    return float(n_pairs_moving * p) if extra else float(n_pairs_moving)
