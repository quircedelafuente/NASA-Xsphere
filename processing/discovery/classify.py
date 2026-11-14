"""B4 · rule-based classifier. Rules are data: science/classes.json (chunk C) overrides the defaults below.

Classes (I3): known-star · known-asteroid · candidate-mover · variable · artefact · unknown-static.
appearance_class (for the 3D library): red-dwarf · brown-dwarf · mira · young-star · star · asteroid.
"""
import json

import numpy as np

from ..config import ROOT

DEFAULT_RULES = {
    "mover_min_sig": 5.0,              # motion / its error
    "mover_min_arcsec_yr": 1.0,        # slower than this is not called a mover in ~1 yr of SPHEREx
    "max_chance_lines": 1.0,
    "pm_agree_sigma": 3.0,             # measured vs catalogue pm
    "pm_agree_frac": 0.3,
    "variable_min_ratio": 1.25,        # max/min flux across visits
    "variable_max_p": 1e-3,            # chi2 probability that it is constant
    "variable_sys_frac": 0.05,
    "mira_min_ratio": 2.5,             # Miras swing by > 1 mag in the infrared; young stars usually less
    "saturated_var_min_ratio": 1.5,
    "variable_min_bands": 2,           # the change must show in at least this many bands (or be >= mira_min_ratio)
    "brown_dwarf_d6_over_d4": 1.5,     # F_nu(4.7um)/F_nu(3.1um); a hot star is ~0.5, T/Y dwarfs >> 1
    "red_dwarf_min_bp_rp": 2.0,
}


def rules():
    r = dict(DEFAULT_RULES)
    for p in (ROOT / "science" / "classes.json", ROOT / "data" / "classes.json"):
        if p.exists():
            try:
                c = json.loads(p.read_text())
                r.update(c.get("discovery_rules", {}))
                r["_source"] = str(p.relative_to(ROOT))
            except Exception:
                pass
    r.setdefault("_source", "built-in defaults (science/classes.json not delivered yet)")
    return r


def _chi2_p(chi2, dof):
    from scipy.stats import chi2 as c2
    return float(c2.sf(chi2, dof))


def variability(flux, R, saturated=False):
    """flux: {band: [{visit, flux, err, q}]} -> (is_variable, best_ratio, detail).

    Variable = not constant (chi2) AND max/min >= variable_min_ratio in >= variable_min_bands bands (one noisy band,
    e.g. next to a bright star's halo, is not enough). Saturated stars need >= mira_min_ratio in two bands (their photometry is rough).
    """
    best = (False, 1.0, None)
    hits = []
    for b, rows in flux.items():
        pts = [(r["flux"], r["err"]) for r in rows if r["flux"] is not None and r["err"] and r["q"] in ("ok", "halo-only")]
        if len(pts) < 3:
            continue
        f = np.array([p[0] for p in pts]); e = np.array([p[1] for p in pts])
        if np.median(f) <= 0:
            continue
        e = np.sqrt(e ** 2 + (R["variable_sys_frac"] * np.abs(f)) ** 2)
        mean = np.average(f, weights=1 / e ** 2)
        chi2 = float((((f - mean) / e) ** 2).sum())
        p = _chi2_p(chi2, len(f) - 1)
        ratio = float(f.max() / max(f.min(), 1e-9)) if f.min() > 0 else float("inf")
        halo = any(r["q"] == "halo-only" for r in rows)
        if p < R["variable_max_p"] and ratio >= R["variable_min_ratio"]:
            hits.append((ratio, {"band": b, "chi2_p": p, "ratio": round(ratio, 2), "halo_only": halo}))
    if not hits:
        return best
    hits.sort(key=lambda h: -h[0])
    big = [h for h in hits if h[0] >= R["saturated_var_min_ratio"]]
    if saturated:
        ok = len(big) >= 2
    else:
        ok = len(hits) >= R["variable_min_bands"]
    return (ok, hits[0][0], hits[0][1] | {"bands": [h[1]["band"] for h in hits]}) if ok else best


def band_means(flux):
    out = {}
    for b, rows in flux.items():
        v = [r["flux"] for r in rows if r["flux"] is not None and r["q"] == "ok"]
        if v:
            out[b] = float(np.median(v))
    return out


def appearance(src, R, var):
    fl = band_means(src["flux"])
    gaia = next((x for x in src["crossmatch"] if x["cat"] == "Gaia DR3"), None)
    d4, d6 = fl.get("D4"), fl.get("D6")
    if src["class"] == "known-asteroid":
        return "asteroid"
    if d4 and d6 and d4 > 0 and d6 / d4 >= R["brown_dwarf_d6_over_d4"]:
        return "brown-dwarf"
    if var[0]:
        return "mira" if var[1] >= R["mira_min_ratio"] else "young-star"
    if gaia and gaia.get("bp_rp") is not None and gaia["bp_rp"] >= R["red_dwarf_min_bp_rp"]:
        return "red-dwarf"
    return "star"


def classify(src, R):
    xm = src.get("crossmatch", [])
    named = next((x for x in xm if x["cat"] in ("SIMBAD", "team targets.json")), None)
    catalogue = [x for x in xm if x["cat"] in ("Gaia DR3", "CatWISE2020", "AllWISE", "2MASS")]
    nm = f" ({named['id']})" if named else ""

    if src["kind"] == "single":
        ast = next((x for x in xm if x["cat"] == "SkyBoT"), None)
        if ast:
            return "known-asteroid", 0.9, f"Seen once, where the known asteroid {ast['id']} was on that date ({ast['sep_arcsec']}″ away)."
        if src.get("near_mask") or src["snr"] < 8:
            return "artefact", 0.8, f"Seen in only one visit, faint (S/N {src['snr']:.0f}) or next to masked pixels: most likely a detector artefact."
        return "artefact", 0.55, (f"Seen in only one visit (S/N {src['snr']:.0f}) and no known asteroid there: a transient, "
                                   "an uncatalogued asteroid or an artefact. Worth a look in the single exposures.")

    m = src["motion"]
    moving = (m["sig"] >= R["mover_min_sig"] and m["speed_arcsec_yr"] >= R["mover_min_arcsec_yr"]
              and m["chance_lines_expected"] < R["max_chance_lines"])
    var = variability(src["flux"], R, saturated="saturated-core" in src.get("flags", []) or src.get("near_mask", False))
    src["_var"] = var

    if moving:
        agree = None
        for x in catalogue:
            if x.get("pmra_masyr") is None:
                continue
            d = np.hypot(m["pmra_masyr"] - x["pmra_masyr"], m["pmdec_masyr"] - x["pmdec_masyr"])
            tol = R["pm_agree_sigma"] * m["sig_pm_masyr"] + R["pm_agree_frac"] * np.hypot(x["pmra_masyr"], x["pmdec_masyr"])
            if d <= tol:
                agree = x; break
        if agree:
            return "known-star", 0.95, (f"Moves {m['speed_arcsec_yr']:.1f}″/yr toward {m['direction']}, matching {agree['cat']} "
                                         f"{agree['id']}{nm} (catalogue {np.hypot(agree['pmra_masyr'], agree['pmdec_masyr']) / 1000:.1f}″/yr).")
        if named or catalogue:
            x = named or catalogue[0]
            return "known-star", 0.8, (f"Moves {m['speed_arcsec_yr']:.1f}″/yr toward {m['direction']}; found in {x['cat']} "
                                        f"{x['id']} at the position its motion predicts for that catalogue's date.")
        return "candidate-mover", round(min(0.95, 0.5 + 0.05 * m["sig"]), 2), (
            f"Moves {m['speed_arcsec_yr']:.1f}″/yr toward {m['direction']} ({m['sig']:.0f}σ, {m['chance_lines_expected']:.2g} "
            "chance alignments expected) and no catalogue lists an object there. Candidate, not a discovery: check it by eye.")

    if var[0]:
        d = var[2]
        extra = " (halo light: the core is saturated)" if d["halo_only"] else ""
        return "variable", 0.85 if not d["halo_only"] else 0.65, (
            f"Static, but its {d['band']} brightness changed by a factor {d['ratio']} across visits{extra}" + (f"; known as{nm}." if nm else "."))
    if catalogue or named:
        x = named or catalogue[0]
        slow = f" Motion {m['speed_arcsec_yr']:.1f}±{m['sig_pm_masyr'] / 1000:.1f}″/yr (not significant)." if m["sig"] < R["mover_min_sig"] else ""
        return "known-star", 0.9, f"Static and steady; matches {x['cat']} {x['id']} ({x['sep_arcsec']}″).{slow}"
    return "unknown-static", 0.5, "Static, steady and not in Gaia, CatWISE, AllWISE or 2MASS at our depth: probably a faint galaxy or a blend."
