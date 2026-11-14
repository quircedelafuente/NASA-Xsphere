"""Band windows (C4 band ids). One sequence = one window, never mixed λ (D5)."""

DETECTOR_UM = {"D1": (0.75, 1.09), "D2": (1.10, 1.62), "D3": (1.63, 2.41),
               "D4": (2.42, 3.82), "D5": (3.83, 4.41), "D6": (4.42, 5.00)}

BANDS = {d: [d] for d in DETECTOR_UM}
BANDS["D56"] = ["D5", "D6"]   # 3.8–5.0 µm, best for cold brown dwarfs


def detectors(band):
    if band not in BANDS:
        raise SystemExit(f"unknown band {band!r}; known: {list(BANDS)}")
    return BANDS[band]


def lam_range(band):
    ds = detectors(band)
    return [DETECTOR_UM[ds[0]][0], DETECTOR_UM[ds[-1]][1]]
