"""Builds data/flags.json (C3) and data/bands.json (D-5). Run: python data/scripts/build_flags_bands.py [cutout.fits]
If a SPHEREx cutout/L2 file is given, bit names are checked against its FLAGS header (MSKN keys)."""
import json, sys, pathlib
OUT = pathlib.Path(__file__).resolve().parents[1]

# bit: (name, class, plain)   class: hard = masked out | soft = kept, warn | info = harmless
F = {
 0: ("TRANSIENT", "hard", "Something flashed here during the exposure (cosmic ray or a bright transient), so this pixel can't be trusted."),
 1: ("OVERFLOW", "soft", "Too bright: the detector saturated here, so the real brightness is higher than shown."),
 2: ("SUR_ERROR", "hard", "The on-board computer made an error while reading this pixel."),
 6: ("NONFUNC", "hard", "Dead pixel: it never works."),
 7: ("DICHROIC", "hard", "Edge of the detector where the beam splitter blocks most of the light."),
 9: ("MISSING_DATA", "hard", "Data for this pixel was lost on its way down from the satellite."),
 10: ("HOT", "hard", "Hot pixel: reads brighter than it should."),
 11: ("COLD", "hard", "Cold pixel: reads fainter than it should."),
 12: ("FULLSAMPLE", "info", "Detailed read-out history exists for this pixel (technical note, nothing wrong)."),
 14: ("PHANMISS", "hard", "A small detector-glow correction could not be applied here."),
 15: ("NONLINEAR", "hard", "Bright enough that the brightness correction is unreliable."),
 17: ("PERSIST", "hard", "Afterimage: left-over charge from an earlier bright source."),
 19: ("OUTLIER", "soft", "This pixel looks odd compared with its neighbours; kept, but treat with care."),
 20: ("CROSSTALK", "hard", "Faint copy of a bright object leaking in from elsewhere on the detector."),
 21: ("SOURCE", "info", "A known star or galaxy sits on this pixel. Not a defect: this is the thing we want to see."),
 22: ("GHOST", "hard", "Faint reflection of a bright source in the same image."),
 23: ("GHOST_FPA", "hard", "Faint reflection of a bright source seen by another detector."),
 24: ("GHOST_EXT", "hard", "Faint reflection of a bright source just outside the field of view."),
 25: ("STREAK", "hard", "A line across the image, e.g. a satellite or asteroid trail."),
 26: ("BLOOM", "hard", "Light bleeding out of a very bright star along the detector."),
 27: ("SNOWBALL", "hard", "Round blob left by a cosmic-ray hit."),
 28: ("HALO", "hard", "Glow around a transient hit."),
}
flags = {
 "source": "SPHEREx L2 FLAGS header MSKN/MSKM/MSKD (checked 14 Nov 2026 on 2026W33_2A_0594_4D3, R7); hard list = IRSA mosaic reject list (Explanatory Supplement v2.1 §3.4.3). OVERFLOW, SOURCE, OUTLIER pass the mosaic tool.",
 "hard_mask_bits": [b for b, v in F.items() if v[1] == "hard"],
 "soft_bits": [b for b, v in F.items() if v[1] == "soft"],
 "info_bits": [b for b, v in F.items() if v[1] == "info"],
 "saturation_bits": [1, 26],
 "saturation_note": "OVERFLOW+BLOOM mean 'bright star': processing may mask them in the image but must raise the saturated warning/overlay rather than silently drop the target. For saturated targets (Barnard, RW Aur) BLOOM/TRANSIENT are set on the core in every frame, so a pure hard mask would blank the target; see per_target_notes.",
 "bits": {str(b): {"name": n, "class": c, "plain": p} for b, (n, c, p) in F.items()},
 "per_target_notes": {
  "barnards-star": "OVERFLOW/BLOOM/TRANSIENT on the core in all 168 D1-D3 frames; core is NaN. Use D5/D6 or difference mode; position still measurable from the wings.",
  "rw-aurigae": "OVERFLOW in 100/101 frames: bright (about Jy level). Flux values are lower limits.",
  "epsilon-indi-b": "Faint (Gaia G=18) next to the bright star eps Indi A (~4.7 mag): watch GHOST/CROSSTALK/BLOOM near the target; check in QA.",
  "wise-0855": "Faint, no saturation expected. Only visible above ~3.8 um (D5/D6); SOURCE may mark the AllWISE position, not today's.",
  "r-draconis": "Mira at maximum can be bright in D1-D3; check OVERFLOW per epoch since flux changes by orders of magnitude over a cycle."
 },
 "header_keys": {"finast": "FINAST != 0 = poor astrometry -> reject exposure", "contamination": ["AURORA_CONT", "SHUTTLE_GLOW_CONT", "HE_AIRGLOW_CONT"]},
}
if len(sys.argv) > 1:
    from astropy.io import fits
    H = fits.open(sys.argv[1])["FLAGS"].header
    names = {int(k[4:]): H[k] for k in H if k.startswith("MSKN")}
    bad = {b: (names.get(b), F[b][0]) for b in F if names.get(b) != F[b][0]}
    unk = sorted(set(names) - set(F))
    print("header check:", "OK" if not bad and not unk else f"MISMATCH {bad} unknown {unk}")
(OUT / "flags.json").write_text(json.dumps(flags, indent=1) + "\n")

# ---- bands ----
DET = {"D1": (0.75, 1.09, 39), "D2": (1.10, 1.62, 41), "D3": (1.63, 2.41, 41),
       "D4": (2.42, 3.82, 35), "D5": (3.83, 4.41, 112), "D6": (4.42, 5.00, 128)}
def channels(lo, hi, n=17):
    r = (hi / lo) ** (1 / n)
    return [[round(lo * r ** i, 4), round(lo * r ** (i + 1), 4)] for i in range(n)]
dets = {d: {"lam_um": [lo, hi], "R": R, "channels_um": channels(lo, hi),
            "note": "17 geometric channels; planning approximation, true per-pixel lambda comes from the WCS-WAVE (alt WCS 'W')"}
        for d, (lo, hi, R) in DET.items()}
# molecule windows: [band_lo, band_hi] absorption window, continuum side-bands either side (um). Approximate, from standard spectroscopy.
def mol(id, label, plain, det, win, left, right, sources):
    return {"id": id, "label": label, "plain": plain, "detector": det, "window_um": win, "continuum_um": [left, right], "sources": sources}
M = [
 mol("h2o-1.4", "Water 1.4 um", "Water vapour/ice absorbs here", "D2", [1.33, 1.50], [1.22, 1.30], [1.55, 1.62], "NIR water band; Explanatory Supplement; verify"),
 mol("h2o-1.9", "Water 1.9 um", "Water vapour/ice absorbs here", "D3", [1.80, 2.00], [1.65, 1.75], [2.05, 2.20], "NIR water band; verify"),
 mol("h2o-3.05", "Water ice 3.05 um", "Water ice absorbs strongly here", "D4", [2.85, 3.20], [2.50, 2.75], [3.35, 3.60], "verified: feature at 3.05 um, spherex.caltech.edu/page/the-origin-of-water-in-planetary-systems; window edges approximate"),
 mol("ch4-1.6", "Methane 1.6 um", "Methane in cold brown dwarfs and planets", "D2", [1.58, 1.72], [1.50, 1.56], [1.74, 1.80], "T dwarf CH4 band; verify"),
 mol("ch4-2.2", "Methane 2.2 um", "Methane in cold brown dwarfs", "D3", [2.15, 2.40], [2.05, 2.12], [2.42, 2.50], "T dwarf CH4 band; verify"),
 mol("ch4-3.3", "Methane 3.3 um", "Strongest methane band; cold brown dwarfs are dark here", "D4", [3.20, 3.45], [2.90, 3.10], [3.55, 3.75], "T/Y dwarf CH4 fundamental; verify"),
 mol("co2-4.27", "Carbon dioxide 4.27 um", "CO2 ice and gas absorb here", "D5", [4.20, 4.34], [4.05, 4.15], [4.40, 4.50], "verified: feature at 4.27 um (same page); window edges approximate"),
 mol("co-4.67", "Carbon monoxide 4.67 um", "CO ice and gas absorb here", "D6", [4.60, 4.75], [4.45, 4.55], [4.80, 4.95], "verified: feature at 4.67 um (same page); window edges approximate"),
]
bands = {"detectors": dets,
 "bands": {**{d: {"detectors": [d], "lam_um": dets[d]["lam_um"], "plain": f"{dets[d]['lam_um'][0]}-{dets[d]['lam_um'][1]} um"} for d in DET},
           "D56": {"detectors": ["D5", "D6"], "lam_um": [3.83, 5.00], "plain": "3.8-5.0 um: best for cold brown dwarfs (they glow here)"}},
 "rule": "Never blink across bands; ALL is for pretty context only.",
 "molecules": M, "status": "ice features H2O 3.05, CO2 4.27, CO 4.67 um confirmed from SPHEREx site (JWST-based); window/continuum edges and the NIR water and methane bands are approximate (standard spectroscopy, not yet checked against cube channels). Check before showing in the UI."}
(OUT / "bands.json").write_text(json.dumps(bands, indent=1) + "\n")
print("ok", len(F), "flags;", len(M), "molecule windows")
