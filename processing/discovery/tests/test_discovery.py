"""Offline tests (no network): run with  venv/bin/python -m pytest processing/discovery/tests -q"""
import numpy as np
import pytest

from processing.config import ROOT
from processing.discovery import detect, inject, link
from processing.discovery.scan import scan
from processing.discovery.stacks_io import load

FIX = ROOT / "contracts" / "fixtures" / "barnards-star"


@pytest.mark.skipif(not (FIX / "stacks.npz").exists(), reason="chunk A fixture not present")
def test_barnard_moves_north_on_fixture():
    rep = scan(FIX, network=False, log=lambda *a: None)
    fastest = max(rep["sources"], key=lambda s: s.get("motion", {}).get("speed_arcsec_yr", 0))
    m = fastest["motion"]
    assert 8.0 < m["speed_arcsec_yr"] < 13.0          # Gaia: 10.4"/yr
    assert m["direction"] == "north"
    assert m["sig"] >= 5
    assert "saturated-core" in fastest["flags"]


def test_linker_recovers_a_clean_synthetic_mover():
    rng = np.random.default_rng(0)
    nv, n = 3, 64
    years = np.array([2025.5, 2026.0, 2026.5])
    stk = {"img": rng.normal(0, 1, (3, nv, n, n)).astype(np.float32), "bands": ["D4", "D5", "D6"],
           "year": years, "mjd": (years - 2000) * 365.25 + 51544.5, "pix": 3.075, "err": None}
    yy, xx = np.mgrid[0:n, 0:n]
    for k in range(nv):
        x, y = 20 + 3.0 * (years[k] - years[0]), 30.0
        for b in range(3):
            stk["img"][b, k] += 25 * np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * 1.35 ** 2))
    dets = detect.detect_all(stk)
    tracks, _, _ = link.link(dets, years, 3.15, 3.075)
    best = max(tracks, key=lambda t: t["speed_px_yr"])
    assert abs(best["vx"] - 3.0) < 0.5 and abs(best["vy"]) < 0.5 and best["motion_sig"] > 5
