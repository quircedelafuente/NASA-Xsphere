"""A5 · Align every cut onto one sky grid, merge per band × visit (median), and write the I2 stacks + PNG frames + spectrum points."""
import base64, io, json, math
import numpy as np
from . import config

def grid(ra, dec, fov_arcmin):
    from astropy.wcs import WCS
    n = max(16, int(round(fov_arcmin * 60 / config.GRID_ARCSEC)))
    w = WCS(naxis=2)
    w.wcs.ctype = ['RA---TAN', 'DEC--TAN']; w.wcs.crval = [ra, dec]
    w.wcs.crpix = [n / 2 + 0.5, n / 2 + 0.5]; w.wcs.cdelt = [-config.GRID_ARCSEC / 3600, config.GRID_ARCSEC / 3600]
    return w, n

def _wcs(hdr_text):
    from astropy.io import fits
    from astropy.wcs import WCS
    return WCS(fits.Header.fromstring(hdr_text))

def reproject_cut(cut, out_wcs, n, hard_bits=()):
    from reproject import reproject_interp
    img = cut['img'].astype(float)
    if hard_bits:   # chunk C's hard flags → NaN before merging
        bad = np.zeros(img.shape, bool)
        for b in hard_bits:
            bad |= (cut['flags'] >> int(b)) & 1 == 1
        img[bad] = np.nan
    img = img - np.nanmedian(img)          # per-exposure background (zodiacal light differs per photo)
    rep, _ = reproject_interp((img, _wcs(cut['hdr'])), out_wcs, shape_out=(n, n))
    return rep.astype(np.float32)

def aperture_flux(cut):
    """Quick 3×3 sum at the target pixel (uncalibrated, for spectrum/light-curve previews; chunk B does proper photometry)."""
    xi, yi = int(round(cut['x'])), int(round(cut['y']))
    a = cut['img'][yi - 1:yi + 2, xi - 1:xi + 2].astype(float)
    if a.shape != (3, 3) or not np.isfinite(a).all():
        return None
    bg = np.nanmedian(cut['img'])
    return float((a - bg).sum())

def png(a, lo, hi, linear=False):
    from PIL import Image
    a = np.clip((a - lo) / (hi - lo + 1e-12), 0, 1)
    if not linear:
        a = np.arcsinh(a * 30) / np.arcsinh(30)
    a = np.flipud(np.nan_to_num(a, nan=1.0 if not linear else 0.5))   # FITS row 0 = bottom; NaN core of a saturated star → white
    b = io.BytesIO(); Image.fromarray((a * 255).astype(np.uint8)).save(b, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

def stack(reps):
    reps = [r for r in reps if r is not None]
    return np.nanmedian(reps, axis=0).astype(np.float32) if reps else None

def frames(stacks, bands, visits):
    """PNG frames per band (same stretch across visits so brightness changes are real) + difference frames vs the band's mean."""
    out = {}
    for i, b in enumerate(bands):
        S = [stacks[i, v] for v in range(len(visits))]
        have = [s for s in S if np.isfinite(s).any()]
        if not have:
            continue
        vals = np.concatenate([s[np.isfinite(s)] for s in have])
        lo, hi = np.percentile(vals, 20), np.percentile(vals, 99.5)
        mean = np.nanmean(have, axis=0)
        diffs = [s - mean if np.isfinite(s).any() else None for s in S]
        dv = np.concatenate([d[np.isfinite(d)] for d in diffs if d is not None]); dl = max(np.percentile(np.abs(dv), 99.5), 1e-6)
        out[b] = dict(frames=[png(s, lo, hi) if np.isfinite(s).any() else None for s in S],
                      diffs=[png(d, -dl, dl, linear=True) if d is not None else None for d in diffs])
    return out

def write_stacks(path, stacks, counts, bands, visits, out_wcs, n, extra):
    """I2 contract: stacks.npz (img[band, visit, y, x], n[band, visit]) + stacks.json (same keys as contracts/fixtures)."""
    np.savez_compressed(path.with_suffix('.npz'), img=stacks, n=counts)
    hdr = out_wcs.to_header()
    meta = dict(contract='I2 stacks v0', bands=bands, grid=dict(nx=n, ny=n, pix_arcsec=config.GRID_ARCSEC, wcs={k: hdr[k] for k in hdr}),
                visits=visits, units='MJy/sr, background-subtracted per exposure, median per band x visit',
                nan='no data or saturated core', source='SPHEREx DR1+QR3 via AWS S3 (fallback: IRSA cutouts)', **extra)
    path.with_suffix('.json').write_text(json.dumps(meta, indent=1))
    return meta
