"""B3 · cross-check every track against catalogues, each at its own epoch.

Gaia DR3 (2016.0, with proper motion: propagated to every visit), CatWISE2020 (~2015.4, pm), AllWISE (~2010.5, pm),
2MASS (~1997-2001, no pm: our measured motion is extrapolated back), SIMBAD for names (falls back to the team's
data/targets.json when CDS is unreachable), SkyBoT for known asteroids at every visit date.
All catalogue queries go through NASA/IPAC IRSA TAP and are cached on disk.
"""
import hashlib, json, time
from pathlib import Path

import numpy as np
import requests
from astropy.time import Time

from ..config import CFG, ROOT

CACHE = ROOT / CFG["cache_dir"] / "catalogs"

CATS = {
    "Gaia DR3": ("gaia_dr3_source", "source_id,ra,dec,pmra,pmdec,parallax,phot_g_mean_mag,bp_rp",
                 "phot_g_mean_mag < 19.5", 2016.0),
    "CatWISE2020": ("catwise_2020", "source_name,ra,dec,pmra,pmdec,w1mpro,w2mpro,meanobsmjd", "w2mpro < 16", None),
    "AllWISE": ("allwise_p3as_psd", "designation,ra,dec,pmra,pmdec,w1mpro,w2mpro", "w2mpro < 16", 2010.5),
    "2MASS": ("fp_psc", "designation,ra,dec,k_m,jdate", "k_m < 15", None),
}


def _cached(key, fn):
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / (hashlib.md5(key.encode()).hexdigest() + ".json")
    if f.exists():
        return json.loads(f.read_text())
    val = fn()
    if val is not None:
        f.write_text(json.dumps(val))
    return val


def query_irsa(name, ra, dec, radius_deg):
    from astroquery.ipac.irsa import Irsa
    tab, cols, cut, _ = CATS[name]
    q = (f"SELECT {cols} FROM {tab} WHERE CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',{ra:.6f},{dec:.6f},{radius_deg:.5f}))=1"
         f" AND {cut}")

    def run():
        for k in range(3):
            try:
                t = Irsa.query_tap(q).to_table()
                rows = []
                for r in t:
                    rows.append({c: (None if np.ma.is_masked(r[c]) else (r[c].item() if hasattr(r[c], "item") else str(r[c])))
                                 for c in t.colnames})
                return rows
            except Exception:
                time.sleep(3 * (k + 1))
        return None
    return _cached(f"{name}|{ra:.5f}|{dec:.5f}|{radius_deg:.4f}", run) or []


def skybot(ra, dec, radius_deg, mjd):
    url = (f"https://ssp.imcce.fr/webservices/skybot/api/conesearch.php?-ep={mjd + 2400000.5:.5f}&-ra={ra:.5f}"
           f"&-dec={dec:.5f}&-rd={radius_deg:.4f}&-mime=json&-output=basic&-loc=500&-filter=0")

    def run():
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 204 or not r.text.strip():
                return []
            data = r.json()
            data = data.get("data", data) if isinstance(data, dict) else data
            out = []
            for a in data:
                ra_ = a.get("RA") or a.get("ra"); de_ = a.get("DEC") or a.get("dec")
                if ra_ is None:
                    continue
                if isinstance(ra_, str) and ":" in ra_:
                    from astropy.coordinates import SkyCoord
                    import astropy.units as u
                    c = SkyCoord(ra_, de_, unit=(u.hourangle, u.deg)); ra_, de_ = c.ra.deg, c.dec.deg
                out.append({"name": a.get("Name") or a.get("name"), "num": a.get("Num") or a.get("num"),
                            "ra": float(ra_), "dec": float(de_), "V": a.get("V") or a.get("vmag"),
                            "class": a.get("Class") or a.get("class")})
            return out
        except Exception:
            return None
    return _cached(f"skybot|{ra:.4f}|{dec:.4f}|{radius_deg:.3f}|{mjd:.2f}", run) or []


def simbad_names(ra, dec, radius_deg):
    q = ("SELECT main_id, ra, dec, otype, pmra, pmdec FROM basic WHERE CONTAINS(POINT('ICRS',ra,dec),"
         f"CIRCLE('ICRS',{ra:.6f},{dec:.6f},{radius_deg:.5f}))=1")

    def run():
        try:
            r = requests.get("https://simbad.cds.unistra.fr/simbad/sim-tap/sync",
                             params={"request": "doQuery", "lang": "adql", "format": "json", "query": q}, timeout=40)
            if r.status_code != 200:
                return None
            d = r.json()
            cols = [c["name"] for c in d["metadata"]]
            return [dict(zip(cols, row)) for row in d["data"]]
        except Exception:
            return None
    return _cached(f"simbad|{ra:.5f}|{dec:.5f}|{radius_deg:.4f}", run)


def team_targets():
    f = ROOT / "data" / "targets.json"
    return json.loads(f.read_text()) if f.exists() else []


def _tangent(ra, dec, ra0, dec0):
    """arcsec offsets (east, north) of ra/dec from ra0/dec0 (small field)."""
    return ((np.asarray(ra) - ra0) * np.cos(np.radians(dec0)) * 3600, (np.asarray(dec) - dec0) * 3600)


def _propagate(ra, dec, pmra, pmdec, ep0, ep1):
    """Linear proper-motion propagation (mas/yr, pmra includes cos dec). Good to << 1" for decades here."""
    dt = ep1 - ep0
    return (ra + (pmra or 0) / 3.6e6 * dt / np.cos(np.radians(dec)), dec + (pmdec or 0) / 3.6e6 * dt)


def crossmatch(tracks, stk, ra0, dec0, radius_deg, network=True, log=print):
    """Adds t['crossmatch'] (list) and t['cat_pm'] (best catalogue pm) to each track (tracks carry sky motion)."""
    years = stk["year"]
    cats = {}
    if network:
        for name in CATS:
            t0 = time.time()
            cats[name] = query_irsa(name, ra0, dec0, radius_deg)
            log(f"    {name}: {len(cats[name])} sources ({time.time() - t0:.0f}s)")
    simbad = simbad_names(ra0, dec0, radius_deg) if network else None
    names = simbad if simbad is not None else []
    name_source = "SIMBAD" if simbad is not None else "team targets.json (SIMBAD unreachable)"
    team = team_targets()
    tol = max(2.0, 0.8 * stk["pix"])                                  # arcsec

    for t in tracks:
        xm = []
        e, n = _tangent(t["ra_deg"], t["dec_deg"], ra0, dec0)         # at t["epoch_year"]
        pm_e, pm_n = t["pmra_masyr"] / 1000, t["pmdec_masyr"] / 1000   # arcsec/yr
        spm = t["sig_pm_masyr"] / 1000
        for name, rows in cats.items():
            if not rows:
                continue
            ep_fixed = CATS[name][3]
            best = None
            for r in rows:
                if name == "Gaia DR3" or name == "AllWISE" or name == "CatWISE2020":
                    pmra = r.get("pmra"); pmdec = r.get("pmdec")
                    if name == "CatWISE2020" and pmra is not None:
                        pmra, pmdec = pmra * 1000, pmdec * 1000          # catalogue gives arcsec/yr
                    ep = ep_fixed if ep_fixed else Time(r["meanobsmjd"], format="mjd").jyear
                    if pmra is not None and np.isfinite(pmra):
                        rr, dd = _propagate(r["ra"], r["dec"], pmra, pmdec, ep, t["epoch_year"])
                        ce, cn = _tangent(rr, dd, ra0, dec0)
                        lim = tol + (2.0 if name != "Gaia DR3" else 0)
                    else:
                        # no catalogue pm: move OUR track back to the catalogue epoch
                        ce, cn = _tangent(r["ra"], r["dec"], ra0, dec0)
                        dt = ep - t["epoch_year"]; ce, cn = ce - pm_e * dt, cn - pm_n * dt
                        lim = tol + 3 * spm * abs(dt) + 2
                else:                                                  # 2MASS: no pm, its own date
                    ep = Time(r["jdate"], format="jd").jyear if r.get("jdate") else 1999.0
                    ce, cn = _tangent(r["ra"], r["dec"], ra0, dec0)
                    dt = ep - t["epoch_year"]; ce, cn = ce - pm_e * dt, cn - pm_n * dt
                    lim = min(tol + 3 * spm * abs(dt) + 2, 60)
                    pmra = pmdec = None
                sep = float(np.hypot(ce - e, cn - n))
                if sep <= lim and (best is None or sep < best["sep_arcsec"]):
                    best = {"cat": name, "id": str(r.get("source_id") or r.get("designation") or r.get("source_name")),
                            "sep_arcsec": round(sep, 2), "epoch": round(float(ep), 2)}
                    if pmra is not None and np.isfinite(pmra):
                        best["pmra_masyr"] = round(float(pmra), 1); best["pmdec_masyr"] = round(float(pmdec), 1)
                    for k in ("phot_g_mean_mag", "bp_rp", "w1mpro", "w2mpro", "k_m", "parallax"):
                        if r.get(k) is not None:
                            best[k] = round(float(r[k]), 3)
            if best:
                xm.append(best)
        # names: SIMBAD (or team list), compared at the track epoch with their pm
        for r in names:
            rr, dd = _propagate(float(r["ra"]), float(r["dec"]), r.get("pmra") or 0, r.get("pmdec") or 0, 2000.0, t["epoch_year"])
            ce, cn = _tangent(rr, dd, ra0, dec0)
            sep = float(np.hypot(ce - e, cn - n))
            if sep <= tol + 2:
                xm.append({"cat": "SIMBAD", "id": r["main_id"], "otype": r.get("otype"), "sep_arcsec": round(sep, 2)})
                break
        for tg in team:
            rr, dd = _propagate(tg["ra_deg"], tg["dec_deg"], tg.get("pmra_masyr", 0), tg.get("pmdec_masyr", 0),
                                tg.get("ref_epoch", 2016.0), t["epoch_year"])
            ce, cn = _tangent(rr, dd, ra0, dec0)
            sep = float(np.hypot(ce - e, cn - n))
            if sep <= tol + 4:
                xm.append({"cat": "team targets.json", "id": tg["name"], "kind": tg.get("kind"),
                           "sep_arcsec": round(sep, 2), "pmra_masyr": tg.get("pmra_masyr"),
                           "pmdec_masyr": tg.get("pmdec_masyr")})
        t["crossmatch"] = xm
    return {"name_source": name_source, "catalog_counts": {k: len(v) for k, v in cats.items()}}


def asteroids_for(singles, stk, ra0, dec0, radius_deg, network=True):
    """Known asteroids near single-visit detections: one SkyBoT query per visit date for the whole field."""
    if not network:
        return
    by_visit = {}
    for s in singles:
        by_visit.setdefault(s["visit"], []).append(s)
    for v, group in by_visit.items():
        rows = skybot(ra0, dec0, radius_deg + 0.01, float(stk["mjd"][v]))
        for s in group:
            best = None
            for a in rows:
                sep = float(np.hypot((a["ra"] - s["ra_deg"]) * np.cos(np.radians(s["dec_deg"])), a["dec"] - s["dec_deg"]) * 3600)
                if sep < 20 and (best is None or sep < best["sep_arcsec"]):
                    best = {"cat": "SkyBoT", "id": f"{a.get('num') or ''} {a.get('name') or ''}".strip(),
                            "sep_arcsec": round(sep, 1), "V": a.get("V")}
            s["crossmatch"] = [best] if best else []
