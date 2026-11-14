"""A6/A7 · Background jobs on the live inventory + processing engine; results cached on disk as C4 bundles.

view: one position (a known target or coordinates) → one C4 bundle per band.
scan: a drawn zone → bundle on a bigger grid → change candidates → cross-check → report (engine/scan.py)."""
import hashlib, json, time, traceback
from concurrent.futures import ThreadPoolExecutor
import astropy.units as u
from astropy.coordinates import SkyCoord
from . import config, inventory, pipeline

JOBS = {}
_pool = ThreadPoolExecutor(2)   # two heavy jobs at once; each reads S3 with its own thread pool
LIVE = config.CACHE / 'live'

def _key(kind, *parts):
    return kind + '_' + hashlib.sha1(json.dumps([*parts, config.COLLECTIONS]).encode()).hexdigest()[:12]

def cached(key):
    p = LIVE / key / 'job.json'
    return json.loads(p.read_text()) if p.exists() else None

def _save(job):
    d = LIVE / job['key']; d.mkdir(parents=True, exist_ok=True)
    (d / 'job.json').write_text(json.dumps({k: v for k, v in job.items() if k != 'trace'}))

def _log(job):
    def log(msg):
        job.setdefault('log', []).append(str(msg).strip())
        job['log'] = job['log'][-30:]
    return log

def default_bands(target):
    if target and target.get('default_band'):
        b = target['default_band']
        return [b] + (['D4'] if b != 'D4' else ['D56'])
    return ['D4', 'D56']   # unknown field: 2.4–3.8 µm and the brown-dwarf window 3.8–5 µm

def run_view(job, ra, dec, bands, per_epoch, target):
    try:
        job.update(status='listing', progress=0.03)
        rows = inventory.query(ra, dec)
        if not rows:
            raise RuntimeError('outside-coverage: SPHEREx has no photos of this position yet')
        t = target or pipeline.field_target(ra, dec)
        center = SkyCoord(ra * u.deg, dec * u.deg)
        job.update(status='fetching', n_photos_total=len(rows), visits=inventory.summary(rows), bands={}, warnings=[])
        for i, band in enumerate(bands):
            exps = pipeline.exposures(rows, band, per_epoch)
            job.update(current_band=band, n_photos_band=len(exps), progress=0.05 + 0.9 * i / len(bands))
            if not exps:
                job['warnings'].append(f'{band}: no photos'); continue
            man = pipeline.build_band(t, band, exps, center, LIVE / job['key'] / band, log=_log(job))
            if man is None:
                job['warnings'].append(f'{band}: fewer than 2 visits, nothing to compare'); continue
            job['bands'][band] = f"/live/{job['key']}/{band}/manifest.json"
            job['warnings'] += [f'{band}: {w}' for w in man['warnings']]
        if not job['bands']:
            raise RuntimeError('outside-coverage: not enough visits of this position in any band yet')
        job.update(status='done', progress=1.0, built_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
        _save(job)
    except Exception as e:
        msg = str(e); code = msg.split(':')[0]
        job.update(status='error', error=code if code in ('outside-coverage', 'nasa-busy') else 'internal', message=msg,
                   trace=traceback.format_exc()[-1500:])

def per_epoch_for(n_visits):
    """~60 photos per detector in total: 12 per visit for 3–5 visits, fewer for monthly deep fields (R Draconis ~18 visits)."""
    return max(3, min(12, 60 // max(n_visits, 1)))

def start_view(ra, dec, bands=None, per_epoch=None, target=None):
    """per_epoch None = automatic: same choice as the pre-warm, so the app hits the pre-warmed cache."""
    bands = bands or default_bands(target)
    if per_epoch is None:
        per_epoch = per_epoch_for(len(inventory.summary(inventory.query(ra, dec))))
    key = _key('v', round(ra, 4), round(dec, 4), bands, per_epoch)
    return _start(key, dict(kind='view', center=dict(ra_deg=ra, dec_deg=dec), target=target, per_epoch=per_epoch),
                  run_view, ra, dec, bands, per_epoch, target)

def start_scan(ra, dec, w_arcmin, h_arcmin, band='D4', per_epoch=6):
    from . import scan
    key = _key('s', round(ra, 4), round(dec, 4), round(w_arcmin, 2), round(h_arcmin, 2), band, per_epoch)
    return _start(key, dict(kind='scan', box=dict(ra_deg=ra, dec_deg=dec, w_arcmin=w_arcmin, h_arcmin=h_arcmin), band=band),
                  scan.run_scan, ra, dec, w_arcmin, h_arcmin, band, per_epoch)

def _start(key, meta, fn, *args):
    hit = cached(key)
    if hit:
        JOBS[key] = hit; return key
    if key in JOBS and JOBS[key].get('status') != 'error':
        return key   # identical request already running: share it
    JOBS[key] = dict(key=key, status='queued', progress=0.0, **meta)
    _pool.submit(fn, JOBS[key], *args)
    return key

def get(key):
    return JOBS.get(key) or cached(key)

def wait(key, timeout=1800):
    t = time.time()
    while time.time() - t < timeout:
        j = get(key)
        if j and j.get('status') in ('done', 'error'):
            return j
        time.sleep(1)
    return get(key)
