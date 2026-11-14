"""Targets (C1). Reads data/targets.json when Data has written it; until then uses these built-ins.

Positions are at ref_epoch with proper motion; never use them directly for cutouts (D6).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BUILTIN = [
    {"id": "barnards-star", "name": "Barnard's Star", "kind": "high-proper-motion star",
     "ra_deg": 269.44850252, "dec_deg": 4.73942045, "ref_epoch": 2016.0,
     "pmra_masyr": -801.551, "pmdec_masyr": 10362.394, "plx_mas": 546.98,
     "default_band": "D4", "sia": "spikes/sia/sia_Barnard.ecsv"},
    {"id": "eps-indi-b", "name": "Epsilon Indi B", "kind": "brown dwarf binary",
     "ra_deg": 331.07645, "dec_deg": -56.79381, "ref_epoch": 2016.0,
     "pmra_masyr": 3982.0, "pmdec_masyr": -2467.0, "plx_mas": 274.8,
     "default_band": "D56", "sia": "spikes/sia/sia_EpsIndB.ecsv"},
    {"id": "wise-0855", "name": "WISE 0855-0714", "kind": "coldest known brown dwarf",
     "ra_deg": 133.7947597, "dec_deg": -7.2451456, "ref_epoch": 2010.5,
     "pmra_masyr": -8118.0, "pmdec_masyr": 680.0, "plx_mas": 439.0,
     "default_band": "D56", "sia": "spikes/sia/sia_WISE0855.ecsv"},
    {"id": "rw-aurigae", "name": "RW Aurigae", "kind": "variable young star",
     "ra_deg": 76.95608, "dec_deg": 30.4012, "ref_epoch": 2016.0,
     "pmra_masyr": 3.0, "pmdec_masyr": -27.0, "plx_mas": 6.4,
     "default_band": "D4", "sia": "spikes/sia/sia_RWAur.ecsv"},
    {"id": "r-draconis", "name": "R Draconis", "kind": "Mira variable",
     "ra_deg": 248.16738, "dec_deg": 66.75501, "ref_epoch": 2016.0,
     "pmra_masyr": -21.0, "pmdec_masyr": 6.0, "plx_mas": 1.2,
     "default_band": "D4", "sia": "spikes/sia/sia_RDra.ecsv"},
]


def load_targets():
    f = ROOT / "data" / "targets.json"
    if f.exists():
        data = json.loads(f.read_text())
        by_id = {t["id"]: t for t in BUILTIN}
        # keep our SIA fallback paths for targets Data also lists
        for t in data:
            t.setdefault("sia", by_id.get(t["id"], {}).get("sia"))
        return data
    return BUILTIN


def get_target(tid):
    for t in load_targets():
        if t["id"] == tid:
            return t
    raise SystemExit(f"unknown target {tid!r}; known: {[t['id'] for t in load_targets()]}")
