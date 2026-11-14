"""A6/A7 · Background jobs: view a spot (fetch → merge, visit by visit) and cache the result so the next request is instant."""
import hashlib, json, logging, math, time, traceback
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from . import config, inventory, fetch, merge
from .resolve import propagate

import astropy; astropy.log.setLevel('ERROR')   # SPHEREx headers trigger harmless SIP notices
JOBS = {}                       # job id → state dict (in memory; results also on disk under cache/views/)
_pool = ThreadPoolExecutor(2)   # at most 2 views at once; each uses its own fetch pool
FETCH_PARALLEL = 12             # S3 has no "busy" throttle like the IRSA cutout service

def view_key(ra, dec, fov_arcmin, bands, per_visit):
    return 'v_' + hashlib.sha1(json.dumps([round(ra, 4), round(dec, 4), fov_arcmin, sorted(bands), per_visit, config.COLLECTIONS]).encode()).hexdigest()[:12]

def _dir(key):
    d = config.CACHE / 'views' / key; d.mkdir(parents=True, exist_ok=True); return d

def cached(key):
    p = config.CACHE / 'views' / key / 'view.json'
    return json.loads(p.read_text()) if p.exists() else None

def run_view(job, ra, dec, fov_arcmin, bands, per_visit, target=None):
    """Fills job dict progressively: status, progress, visits, frames per band, spectrum points, stacks file."""
    try:
        job.update(status='listing', progress=0.02)
        half = int(math.ceil(fov_arcmin * 60 / config.PIX_ARCSEC / 2)) + 3
        rows = inventory.query(ra, dec)
        if not rows:
            raise RuntimeError('outside-coverage: SPHEREx has no photos of this position yet')
        sel = inventory.pick(rows, bands, per_visit)
        vis = inventory.summary(rows)
        job.update(status='fetching', progress=0.05, visits=vis, n_photos_total=len(rows), n_photos_used=len(sel))
        out_wcs, n = merge.grid(ra, dec, fov_arcmin)
        fl = config.flags_dictionary(); hard = fl.get('hard_mask_bits', []) if fl else []
        pos = (lambda mjd: _target_pos(target, mjd)) if target else (lambda mjd: (ra, dec))
        V = len(vis); stacks = np.full((len(bands), V, n, n), np.nan, np.float32); counts = np.zeros((len(bands), V), np.int16)
        spectrum, done = [], 0
        with ThreadPoolExecutor(FETCH_PARALLEL) as ex:
            for v in range(V):                      # visit by visit, oldest first: the UI can show visit 1 early
                vrows = [r for r in sel if r['visit'] == v]
                cuts = list(ex.map(lambda r: (r, _safe_get(r, *pos(r['mjd']), half)), vrows))
                for bi, b in enumerate(bands):
                    reps = [merge.reproject_cut(c, out_wcs, n, hard) for r, c in cuts if c is not None and r['band'] == b]
                    s = merge.stack(reps)
                    if s is not None:
                        stacks[bi, v] = s; counts[bi, v] = len(reps)
                for r, c in cuts:
                    if c is not None:
                        f = merge.aperture_flux(c)
                        if f is not None and np.isfinite(c['lam']):
                            spectrum.append(dict(lam=round(c['lam'], 4), flux=round(f, 3), det=r['band'], ep=v, mjd=round(c['mjd'], 4)))
                done += len(vrows)
                job.update(progress=0.05 + 0.9 * done / max(len(sel), 1), visits_ready=v + 1,
                           bands={b: f for b, f in merge.frames(stacks, bands, vis).items()})
        key = job['key']; d = _dir(key)
        meta = merge.write_stacks(d / 'stacks', stacks, counts, bands, vis, out_wcs, n,
                                  dict(center=dict(ra_deg=ra, dec_deg=dec), target=target['id'] if target else None, spectrum_points=spectrum))
        result = dict(status='done', progress=1.0, key=key, center=dict(ra_deg=ra, dec_deg=dec), fov_arcmin=fov_arcmin, grid_px=n,
                      grid_arcsec=config.GRID_ARCSEC, visits=vis, n_photos_total=len(rows), n_photos_used=len(sel),
                      counts={b: counts[i].tolist() for i, b in enumerate(bands)},
                      bands=merge.frames(stacks, bands, vis), spectrum=spectrum, target=target,
                      tracks=[dict(visit=x['id'], **dict(zip(('ra_deg', 'dec_deg'), pos(_mid_mjd(rows, x['id']))))) for x in vis],
                      stacks_url=f'/files/{key}/stacks.npz', stacks_meta_url=f'/files/{key}/stacks.json', built_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
        (d / 'view.json').write_text(json.dumps(result))
        job.update(result)
    except Exception as e:
        msg = str(e)
        code = msg.split(':')[0] if msg.split(':')[0] in ('outside-coverage', 'nasa-busy') else 'internal'
        job.update(status='error', error=code, message=msg, trace=traceback.format_exc()[-1500:])

def _target_pos(t, mjd):
    return propagate(t, 2000.0 + (mjd + 2400000.5 - 2451545.0) / 365.25)

def _mid_mjd(rows, v):
    m = sorted(r['mjd'] for r in rows if r['visit'] == v); return m[len(m) // 2]

def _safe_get(r, ra, dec, half):
    try:
        return fetch.get(r, ra, dec, half)
    except Exception:
        return None   # one bad photo must not sink the whole view; counts show what was merged

def start_view(ra, dec, fov_arcmin=3.0, bands=None, per_visit=6, target=None):
    bands = bands or config.BANDS
    key = view_key(ra, dec, fov_arcmin, bands, per_visit)
    hit = cached(key)
    if hit:
        JOBS[key] = hit; return key
    if key in JOBS and JOBS[key].get('status') not in ('error',):
        return key   # same request already running: share it
    JOBS[key] = dict(key=key, status='queued', progress=0.0)
    _pool.submit(run_view, JOBS[key], ra, dec, fov_arcmin, bands, per_visit, target)
    return key

def wait(key, timeout=900):
    t = time.time()
    while time.time() - t < timeout:
        j = JOBS.get(key) or cached(key)
        if j and j.get('status') in ('done', 'error'):
            return j
        time.sleep(1)
    return JOBS.get(key)
