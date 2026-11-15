"""False colour for the preview images (PNG, GIF). Mirror of web/src/ui/lib/palette.ts: keep the two in sync.

One band = one colour, picked from its wavelength: shorter wavelengths bluer, longer redder (the "representative colour"
convention NASA uses for infrared pictures). The colour only replaces grey: every channel rises with brightness, so
brighter pixels stay brighter and the frames of one sequence are still directly comparable (D5, D8).
"""
import numpy as np

# wavelength (µm) -> tint (r, g, b in 0..1), linear in between
STOPS = [(0.90, (0.25, 0.45, 1.00)),   # blue
         (1.35, (0.10, 0.75, 1.00)),   # cyan
         (2.00, (0.15, 1.00, 0.75)),   # teal
         (3.10, (1.00, 0.72, 0.15)),   # amber
         (4.10, (1.00, 0.45, 0.10)),   # orange
         (4.70, (1.00, 0.20, 0.12))]   # red


def tint(lam_um):
    lams = [s[0] for s in STOPS]
    return tuple(float(np.interp(lam_um, lams, [s[1][i] for s in STOPS])) for i in range(3))


def lut(lam_um):
    """256x3 uint8 table: grey level -> colour. Black stays black, white stays white, the tint fills the middle."""
    g = np.linspace(0, 1, 256)
    return np.stack([np.round(255 * g ** (0.9 + 1.5 * (1 - t))) for t in tint(lam_um)], -1).astype(np.uint8)


def colourise(u8, lam_um):
    """Grey uint8 image (ny, nx) -> RGB uint8 (ny, nx, 3)."""
    return lut(lam_um)[u8]
