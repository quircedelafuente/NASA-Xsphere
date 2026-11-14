"""Which exposures to use. Prefers Data's C2 inventory; falls back to the SIA tables in spikes/sia/."""
import json
from pathlib import Path

import numpy as np
from astropy.table import Table

from .bands import detectors
from .config import CFG

ROOT = Path(__file__).resolve().parents[1]


def _from_inventory(tid, dets):
    f = ROOT / "data" / "inventory" / f"{tid}.json"
    if not f.exists():
        return None
    inv = json.loads(f.read_text())
    out = []
    for e in inv["exposures"]:
        if e["det"] in dets and e.get("usable", True) and e.get("on_chip", True):
            out.append({"obs_id": e["obs_id"], "det": e["det"], "mjd": e["mjd"],
                        "release": e["release"], "url": e["https_url"],
                        "epoch": e.get("epoch")})
    return sorted(out, key=lambda e: e["mjd"])


def _from_sia(target, dets):
    t = Table.read(ROOT / target["sia"])
    out = []
    for r in t:
        det = str(r["energy_bandpassname"]).replace("SPHEREx-", "")
        if det not in dets or r["obs_collection"] not in CFG["spherex"]["collections"]:
            continue
        aws = json.loads(str(r["cloud_access"]))["aws"]
        url = f"https://{aws['bucket_name']}.s3.{aws['region']}.amazonaws.com/{aws['key']}"
        out.append({"obs_id": str(r["obs_id"]), "det": det,
                    "mjd": float(0.5 * (r["t_min"] + r["t_max"])),
                    "release": str(r["obs_collection"]), "url": url, "epoch": None})
    return sorted(out, key=lambda e: e["mjd"])


def list_exposures(target, band):
    dets = detectors(band)
    exps = _from_inventory(target["id"], dets)
    source = "C2 inventory"
    if exps is None:
        exps = _from_sia(target, dets)
        source = "SIA table (spikes/sia)"
    if any(e["epoch"] is None for e in exps):
        assign_epochs(exps)
    return exps, source


def assign_epochs(exps, gap_days=None, month_split=None):
    """D4: split when the time gap > gap_days; groups longer than gap_days are split by calendar month."""
    from astropy.time import Time
    gap_days = gap_days or CFG["epochs"]["gap_days"]
    month_split = CFG["epochs"]["split_long_groups_by_month"] if month_split is None else month_split
    mjd = np.array([e["mjd"] for e in exps])
    groups, cur = [], [0]
    for i in range(1, len(exps)):
        if mjd[i] - mjd[i - 1] > gap_days:
            groups.append(cur); cur = []
        cur.append(i)
    groups.append(cur)
    final = []
    for g in groups:
        if month_split and mjd[g[-1]] - mjd[g[0]] > gap_days:
            months = {}
            for i in g:
                months.setdefault(Time(mjd[i], format="mjd").datetime.strftime("%Y-%m"), []).append(i)
            final += list(months.values())
        else:
            final.append(g)
    for k, g in enumerate(final):
        for i in g:
            exps[i]["epoch"] = k
    return exps
