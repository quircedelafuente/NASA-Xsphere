"""A4 · Get only the pixels we need from one SPHEREx photo. Amazon S3 byte-range reads first, IRSA cutout service as fallback.
Each result is cached on disk as a small .npz, so a spot is never downloaded twice."""
import hashlib, io, math, time, urllib.request, warnings
import numpy as np
from . import config

warnings.simplefilter('ignore')   # SPHEREx headers trigger harmless astropy WCS/SIP notices

def _key(row, ra, dec, half_px):
    return hashlib.sha1(f"{row['obs_id']}{row['band']}{ra:.5f}{dec:.5f}{half_px}".encode()).hexdigest()[:20]

def _extract(hdul, ra, dec, half_px):
    from astropy.wcs import WCS
    hd = hdul['IMAGE'].header
    w = WCS(hd)
    x, y = (float(v) for v in w.all_world2pix(ra, dec, 0))
    ny, nx = hd['NAXIS2'], hd['NAXIS1']
    xi, yi = int(round(x)), int(round(y))
    x0, x1, y0, y1 = max(xi - half_px, 0), min(xi + half_px + 1, nx), max(yi - half_px, 0), min(yi + half_px + 1, ny)
    if x1 - x0 < 3 or y1 - y0 < 3:
        return None   # position falls off this detector
    img = np.asarray(hdul['IMAGE'].section[y0:y1, x0:x1], dtype=np.float32)
    flg = np.asarray(hdul['FLAGS'].section[y0:y1, x0:x1], dtype=np.int32)
    try:   # wavelength at the target pixel: LVF, so it depends on position (needs the WCS-WAVE table)
        sw = WCS(hd, fobj=hdul, key='W'); sw.sip = None
        lam, bw = (float(v) for v in sw.pixel_to_world_values(x, y))
    except Exception:
        lam = bw = float('nan')
    # sub-image WCS: shift the reference pixel to the cut box
    from astropy.io import fits
    sub = fits.Header([c for c in hd.cards if c.keyword and not c.keyword.endswith('W') and c.keyword not in ('COMMENT', 'HISTORY')])
    sub['CRPIX1'] = hd['CRPIX1'] - x0; sub['CRPIX2'] = hd['CRPIX2'] - y0
    sub['NAXIS1'], sub['NAXIS2'] = x1 - x0, y1 - y0
    return dict(img=img, flags=flg, lam=lam, bw=bw, mjd=float(hd.get('MJD-AVG') or hd.get('MJD-OBS')), x=x - x0, y=y - y0,
                hdr=sub.tostring())   # spatial WCS of the cut, as FITS header text

def _s3(row, ra, dec, half_px):
    from astropy.io import fits
    with fits.open(row['s3'], use_fsspec=True, fsspec_kwargs={'block_size': 256_000}) as h:
        return _extract(h, ra, dec, half_px)

def _cutout(row, ra, dec, half_px):
    from astropy.io import fits
    size = (2 * half_px + 1) * config.PIX_ARCSEC / 3600
    url = f"{row['https']}?center={ra},{dec}&size={size:.4f}"
    data = urllib.request.urlopen(url, timeout=120).read()
    if len(data) < 5000:
        raise RuntimeError(data[:80].decode('latin1'))   # "Server busy, retry later."
    with fits.open(io.BytesIO(data)) as h:
        return _extract(h, ra, dec, half_px)

def get(row, ra, dec, half_px):
    """Returns the cut dict (or None if the position is off-chip). Raises only if both routes fail."""
    p = config.CACHE / 'cuts' / f'{_key(row, ra, dec, half_px)}.npz'
    if p.exists():
        z = np.load(p, allow_pickle=False)
        if z['img'].size == 0:
            return None
        return dict(img=z['img'], flags=z['flags'], lam=float(z['lam']), bw=float(z['bw']), mjd=float(z['mjd']), x=float(z['x']), y=float(z['y']), hdr=str(z['hdr']))
    err = None
    for fn, tries in ((_s3, 2), (_cutout, 3)):
        for a in range(tries):
            try:
                cut = fn(row, ra, dec, half_px); break
            except Exception as e:
                err = e; time.sleep(2 * (a + 1))
        else:
            continue
        break
    else:
        raise RuntimeError(f"fetch failed for {row['obs_id']}: {err}")
    p.parent.mkdir(parents=True, exist_ok=True)
    if cut is None:
        np.savez(p, img=np.zeros(0, np.float32)); return None
    np.savez(p, **{k: (np.asarray(v) if k in ('img', 'flags') else v) for k, v in cut.items()})
    return cut
