"""Chunk B entry point: I2 stacks -> I3 report.

  python -m processing.discovery.scan contracts/fixtures/barnards-star [--out report.json] [--offline]

From the backend:  from processing.discovery.scan import scan;  report = scan(stacks_dir)
"""
import argparse, json, time

import numpy as np
from astropy.time import Time

from . import classify as C, crossmatch as X, detect as D, link as L, photometry as P, report as R
from .stacks_io import load

DIRS = ["north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west"]


def _sky_motion(stk, t):
    """pixel velocity -> (pm_east, pm_north) in mas/yr using the local WCS; position at t0."""
    w = stk["wcs"]
    c0 = w.pixel_to_world(t["x0"], t["y0"])
    c1 = w.pixel_to_world(t["x0"] + t["vx"], t["y0"] + t["vy"])
    de, dn = c0.spherical_offsets_to(c1)
    pmra, pmdec = de.to_value("mas"), dn.to_value("mas")
    scale = np.hypot(pmra, pmdec) / max(t["speed_px_yr"], 1e-9) if t["speed_px_yr"] > 1e-6 else stk["pix"] * 1000
    ang = (np.degrees(np.arctan2(pmra, pmdec)) + 360) % 360
    return c0, pmra, pmdec, scale, DIRS[int((ang + 22.5) // 45) % 8]


def scan(stacks_dir, network=True, thr=5.0, max_pm_arcsec_yr=12.0, log=print):
    t_start = time.time()
    stk = load(stacks_dir)
    nb, nv, ny, nx = stk["img"].shape
    dets = D.detect_all(stk, thr)
    fwhm = D.psf_fwhm(stk, dets)
    tracks, singles, linfo = L.link(dets, stk["year"], fwhm, stk["pix"], max_pm_arcsec_yr=max_pm_arcsec_yr)
    valid = np.isfinite(np.nanmean(stk["img"], axis=(0, 1))).sum()
    log(f"  B1 detections per visit {[len(d) for d in dets]}, PSF FWHM {fwhm:.1f}px; B2 {len(tracks)} tracks, {len(singles)} one-offs")

    c = stk["wcs"].pixel_to_world((nx - 1) / 2, (ny - 1) / 2)
    ra0, dec0 = float(c.ra.deg), float(c.dec.deg)
    w_arcmin = nx * stk["pix"] / 60
    radius = np.hypot(nx, ny) / 2 * stk["pix"] / 3600 + 0.003

    for t in tracks:
        c0, pmra, pmdec, scale, direction = _sky_motion(stk, t)
        t["ra_deg"], t["dec_deg"], t["epoch_year"] = float(c0.ra.deg), float(c0.dec.deg), t["t0"]
        t["pmra_masyr"], t["pmdec_masyr"] = float(pmra), float(pmdec)
        t["sig_pm_masyr"] = float(t["sig_v_px_yr"] * scale)
        t["direction"] = direction
        t["chance"] = L.chance_lines(t, dets, linfo["n_pairs_moving"], linfo["tol_px"], valid)
    for s in singles:
        cc = stk["wcs"].pixel_to_world(s["x"], s["y"])
        s["ra_deg"], s["dec_deg"] = float(cc.ra.deg), float(cc.dec.deg)

    log("  B3 cross-match")
    xinfo = X.crossmatch(tracks, stk, ra0, dec0, radius, network=network, log=log)
    X.asteroids_for(singles, stk, ra0, dec0, radius, network=network)

    Rr = C.rules()
    sources = []
    for t in tracks:
        pos = {}
        for v in range(nv):
            if v in t["members"]:
                d = dets[v][t["members"][v]]; pos[v] = (d["x"], d["y"])
            else:
                dt = stk["year"][v] - t["t0"]; pos[v] = (t["x0"] + t["vx"] * dt, t["y0"] + t["vy"] * dt)
        flux = P.measure_track(stk, pos)
        positions = []
        for v in range(nv):
            cc = stk["wcs"].pixel_to_world(*pos[v])
            positions.append({"visit": v, "mjd": round(float(stk["mjd"][v]), 4), "ra_deg": round(float(cc.ra.deg), 6),
                              "dec_deg": round(float(cc.dec.deg), 6), "x": round(pos[v][0], 2), "y": round(pos[v][1], 2),
                              "detected": v in t["members"]})
        src = {"kind": "track", "snr": t["snr_max"], "near_mask": t["saturated"], "crossmatch": t["crossmatch"], "flux": flux,
               "motion": {"pmra_masyr": round(t["pmra_masyr"], 1), "pmdec_masyr": round(t["pmdec_masyr"], 1),
                          "sig_pm_masyr": round(t["sig_pm_masyr"], 1),
                          "speed_arcsec_yr": round(float(np.hypot(t["pmra_masyr"], t["pmdec_masyr"])) / 1000, 3),
                          "direction": t["direction"], "sig": round(t["motion_sig"], 1),
                          "chance_lines_expected": round(t["chance"], 4), "fit_rms_px": round(t["rms_px"], 2),
                          "n_visits": t["n_visits"]},
               "positions": positions}
        cls, conf, why = C.classify(src, Rr)
        src.update({"class": cls, "confidence": conf, "reason": why})
        src["appearance_class"] = C.appearance(src, Rr, src.pop("_var", (False, 1, None)))
        src["flags"] = (["saturated-core"] if t["saturated"] else [])
        sources.append(src)
    for s in singles:
        flux = P.measure_track(stk, {s["visit"]: (s["x"], s["y"])})
        src = {"kind": "single", "snr": s["snr"], "near_mask": s.get("near_mask", False), "crossmatch": s.get("crossmatch", []),
               "flux": flux, "positions": [{"visit": s["visit"], "mjd": round(float(stk["mjd"][s["visit"]]), 4),
                                            "ra_deg": round(s["ra_deg"], 6), "dec_deg": round(s["dec_deg"], 6),
                                            "x": round(s["x"], 2), "y": round(s["y"], 2), "detected": True}]}
        cls, conf, why = C.classify(src, Rr)
        src.update({"class": cls, "confidence": conf, "reason": why, "flags": ["single-visit"],
                    "appearance_class": "asteroid" if cls == "known-asteroid" else None})
        sources.append(src)

    # B5/B6: spectrum (per band, per visit, along the path) + light curve
    lam = stk["lam"]
    for s in sources:
        s["spectrum"] = [{"lam_um": round(lam[b], 3), "band": b, "visit": r["visit"], "flux": r["flux"], "err": r["err"],
                          "quality": r["q"]} for b, rows in s["flux"].items() for r in rows if r["flux"] is not None]
        s["light_curve"] = [{"mjd": round(float(stk["mjd"][r["visit"]]), 4), "band": b, "flux": r["flux"], "err": r["err"],
                             "quality": r["q"]} for b, rows in s["flux"].items() for r in rows if r["flux"] is not None]
        s["flux"] = {b: [r["flux"] for r in rows] for b, rows in s["flux"].items()}
    # the per-exposure spectrum that chunk A measured for the requested target, attached to the nearest source
    if stk["spectrum_points"] and sources:
        near = min(sources, key=lambda s: np.hypot(s["positions"][0]["x"] - (nx - 1) / 2, s["positions"][0]["y"] - (ny - 1) / 2))
        near["spectrum_exposures"] = stk["spectrum_points"]

    order = {"candidate-mover": 0, "variable": 1, "known-star": 2, "known-asteroid": 3, "unknown-static": 4, "artefact": 5}
    sources.sort(key=lambda s: (order[s["class"]], -(s.get("motion", {}).get("speed_arcsec_yr") or 0), -s["snr"]))
    for i, s in enumerate(sources):
        s["id"] = f"s{i + 1:03d}"
        for k in ("kind", "snr", "near_mask"):
            s.pop(k, None)
        s.update({k: s[k] for k in ()})
    sources = [{"id": s.pop("id"), **s} for s in sources]

    zone = {"ra_deg": round(ra0, 6), "dec_deg": round(dec0, 6), "w_arcmin": round(w_arcmin, 2), "h_arcmin": round(ny * stk["pix"] / 60, 2)}
    info = {"detection_sigma": thr, "psf_fwhm_px": round(fwhm, 2), "link_tolerance_px": round(linfo["tol_px"], 2),
            "max_motion_arcsec_yr": max_pm_arcsec_yr, "rules": Rr.get("_source"), "names_from": xinfo["name_source"],
            "catalog_counts": xinfo["catalog_counts"], "pixel_arcsec": stk["pix"], "stacks": stk["dir"],
            "runtime_s": round(time.time() - t_start, 1)}
    rep = R.build(zone, stk, sources, info)
    log(f"  B7 {rep['summary']}")
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stacks"); ap.add_argument("--out"); ap.add_argument("--offline", action="store_true")
    ap.add_argument("--thr", type=float, default=5.0)
    a = ap.parse_args()
    rep = scan(a.stacks, network=not a.offline, thr=a.thr)
    txt = json.dumps(rep, indent=1, default=float)
    if a.out:
        open(a.out, "w").write(txt)
    print(rep["summary_text"])


if __name__ == "__main__":
    main()
