# Builds the sample-site data for one target from downloaded SPHEREx cutouts:
# per detector x epoch median co-add (reprojected to one grid) -> PNG, plus per-exposure photometry -> spectrum.
import glob, json, base64, io, sys, warnings
import numpy as np
from astropy.io import fits
from astropy.wcs import WCS, FITSFixedWarning
from astropy.time import Time
from reproject import reproject_interp
from PIL import Image
warnings.simplefilter('ignore', FITSFixedWarning)
warnings.simplefilter('ignore', RuntimeWarning)

name = sys.argv[1]
P = json.load(open('targets2026.json'))[name]
RA0, DEC0 = P['ra'], P['dec']               # position at 2026.0
PMRA, PMDEC = -801.55, 10362.39              # mas/yr, Gaia DR3 (from team CONTRACTS.md example; verify)
N, SCALE = 56, 3.075 / 3600                  # output grid: 40 px of half a SPHEREx pixel = 2.05'

def pred(mjd):                               # proper-motion position at a date
    dt = Time(mjd, format='mjd').decimalyear - 2026.0
    return RA0 + PMRA / 3.6e6 * dt / np.cos(np.radians(DEC0)), DEC0 + PMDEC / 3.6e6 * dt

out = WCS(naxis=2)
out.wcs.ctype = ['RA---TAN', 'DEC--TAN']; out.wcs.crval = [RA0, DEC0]
out.wcs.crpix = [N / 2 + 0.5, N / 2 + 0.5]; out.wcs.cdelt = [-SCALE, SCALE]

rows = []
for fn in sorted(glob.glob(f'dl/{name}/*.fits')):
    try:
        h = fits.open(fn)
        im, hd = h['IMAGE'].data.astype(float), h['IMAGE'].header
        fl = h['FLAGS'].data
        mjd = hd.get('MJD-AVG') or hd.get('MJD-OBS')
        w = WCS(hd)
        ra, dec = pred(mjd)
        x, y = w.all_world2pix(ra, dec, 0)
        sw = WCS(hd, fobj=h, key='W'); sw.sip = None
        lam, bw = sw.pixel_to_world_values(x, y)
        im = im - np.nanmedian(im)
        xi, yi = int(round(float(x))), int(round(float(y)))
        ap = im[yi-1:yi+2, xi-1:xi+2]
        flag = int(np.bitwise_or.reduce(fl[yi-1:yi+2, xi-1:xi+2].ravel())) if ap.size == 9 else -1
        flux = float(np.nansum(ap)) if ap.size == 9 and np.isfinite(ap).all() else None
        rep, _ = reproject_interp((im, w), out, shape_out=(N, N))
        rows.append(dict(det=hd.get('DETECTOR') or fn[-7:-5], mjd=mjd, lam=float(lam), flux=flux, flag=flag, img=rep))
    except Exception as e:
        print('skip', fn, e)
print('read', len(rows))

# epochs: split when gap > 60 days
mj = sorted(r['mjd'] for r in rows); edges = [mj[0]]
for a, b in zip(mj, mj[1:]):
    if b - a > 60: edges.append(b)
def ep(m): return sum(m >= e for e in edges) - 1
for r in rows: r['ep'] = ep(r['mjd'])

YY, XX = np.mgrid[0:N, 0:N]; CORE = np.hypot(XX - N/2, YY - N/2) < 6
def png(a, lo, hi, core=1.0, linear=False):
    a = np.clip((a - lo) / (hi - lo), 0, 1)
    if not linear: a = np.arcsinh(a * 30) / np.arcsinh(30)
    a = np.where(np.isnan(a) & CORE, core, a)   # saturated star core comes back as NaN: show it as brightest
    a = np.flipud(np.nan_to_num(a, nan=0))   # FITS row 0 is the bottom; PNG row 0 is the top (north up)
    b = io.BytesIO(); Image.fromarray((a * 255).astype(np.uint8)).resize((N * 8, N * 8), Image.NEAREST).save(b, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

dets = sorted(set(str(r['det']) for r in rows))
res = dict(name=name, ra=RA0, dec=DEC0, grid_px=N, grid_arcsec=3.075, bands={}, epochs=[], spectrum=[])
for e in range(len(edges)):
    m = [r['mjd'] for r in rows if r['ep'] == e]
    px, py = out.all_world2pix(*pred(np.mean(m)), 0)
    res['epochs'].append(dict(id=e, mjd=float(np.mean(m)), start=Time(min(m), format='mjd').iso[:10],
                              end=Time(max(m), format='mjd').iso[:10], n=len(m), px=float(px), py=float(N - 1 - py)))
for d in dets:
    stacks = []
    for e in range(len(edges)):
        s = [r['img'] for r in rows if str(r['det']) == d and r['ep'] == e]
        stacks.append(np.nanmedian(s, axis=0) if s else np.full((N, N), np.nan))
    allv = np.concatenate([s[np.isfinite(s)] for s in stacks])
    lo, hi = np.percentile(allv, 20), np.percentile(allv, 99.5)
    mean = np.nanmean(stacks, axis=0)
    diffs = [s - mean for s in stacks]
    dv = np.concatenate([x[np.isfinite(x)] for x in diffs]); dl = np.percentile(np.abs(dv), 99.5)
    lams = [r['lam'] for r in rows if str(r['det']) == d]
    res['bands'][d] = dict(lam_min=min(lams), lam_max=max(lams), n=[sum(1 for r in rows if str(r['det']) == d and r['ep'] == e) for e in range(len(edges))],
                           frames=[png(s, lo, hi) for s in stacks], diffs=[png(x, -dl, dl, core=0.5, linear=True) for x in diffs])
    # centroid per epoch (flux-weighted, 5x5 around predicted) for the measured-shift readout
    res['bands'][d]['_stacks'] = stacks

# measured shift: flux-weighted centroid around the predicted spot, first vs last visit, in the band with most visits
def centroid(a, px, py):
    x0, y0 = int(round(px)), int(round(py)); w = np.nan_to_num(a[y0-3:y0+4, x0-3:x0+4]); w = np.clip(w - np.median(w), 0, None)
    yy, xx = np.mgrid[y0-3:y0+4, x0-3:x0+4]; return (w*xx).sum()/w.sum(), (w*yy).sum()/w.sum()
best = max(dets, key=lambda d: (sum(1 for n in res['bands'][d]['n'] if n), sum(res['bands'][d]['n'])))
res['default_band'] = best
use = [e for e, n in enumerate(res['bands'][best]['n']) if n]
if len(use) >= 2:
    a, b = use[0], use[-1]; E = res['epochs']
    fy = lambda e: N - 1 - E[e]['py']          # back to FITS row order
    ca = centroid(res['bands'][best]['_stacks'][a], E[a]['px'], fy(a)); cb = centroid(res['bands'][best]['_stacks'][b], E[b]['px'], fy(b))
    yrs = (E[b]['mjd'] - E[a]['mjd']) / 365.25
    res['measured'] = dict(band=best, years=yrs, shift_arcsec=float(np.hypot(cb[0]-ca[0], cb[1]-ca[1]) * 3.075),
                           expected_arcsec=float(np.hypot(PMRA, PMDEC) / 1000 * yrs),
                           diff_arcsec=float(np.hypot((cb[0]-ca[0]) - (E[b]['px']-E[a]['px']), (cb[1]-ca[1]) - (fy(b)-fy(a))) * 3.075))
for d in dets: res['bands'][d].pop('_stacks')
res['total'] = len(rows); res['built'] = Time.now().iso[:10]
for r in rows:
    if r['flux'] is not None:
        res['spectrum'].append(dict(lam=round(r['lam'], 4), flux=round(r['flux'], 3), det=str(r['det']), ep=r['ep'], flag=r['flag']))
json.dump(res, open(f'sample_{name}.json', 'w'))
print('bands', {d: (round(v['lam_min'], 2), round(v['lam_max'], 2), v['n']) for d, v in res['bands'].items()})
print('epochs', [(x['start'], x['end'], x['n']) for x in res['epochs']])
print('spectrum points', len(res['spectrum']))
