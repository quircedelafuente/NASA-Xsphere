"""A3 · Which SPHEREx photos cover a point or a zone, grouped into visits. Live query to IRSA SIA, cached per position."""
import datetime, hashlib, json, math, time
from . import config

def _visits(mjds):
    """D4 rule: new visit after a 60-day gap; a group longer than 60 days (deep fields) is split by calendar month."""
    order = sorted(set(mjds)); groups = []
    for m in order:
        if not groups or m - groups[-1][-1] > config.GAP_DAYS:
            groups.append([m])
        else:
            groups[-1].append(m)
    out = []
    for g in groups:
        if g[-1] - g[0] <= config.GAP_DAYS:
            out.append(g); continue
        by_month = {}
        for m in g:
            d = datetime.datetime(1858, 11, 17) + datetime.timedelta(days=m)
            by_month.setdefault((d.year, d.month), []).append(m)
        out.extend(by_month[k] for k in sorted(by_month))
    return {m: i for i, g in enumerate(out) for m in g}

def query(ra, dec, radius_deg=0.0003, collections=None):
    """Returns list of exposures: obs_id, band, mjd, visit, collection, https (IRSA) and s3 urls. Cached 6 h per position."""
    collections = collections or config.COLLECTIONS
    key = hashlib.sha1(json.dumps([round(ra, 4), round(dec, 4), round(radius_deg, 4), collections]).encode()).hexdigest()[:16]
    cache = config.CACHE / 'inventory' / f'{key}.json'
    if cache.exists() and time.time() - cache.stat().st_mtime < 6 * 3600:   # weekly releases: 6 h is fresh enough
        return json.loads(cache.read_text())
    import pyvo   # imported here so resolve/tests don't need it
    rows, res, err = [], None, None
    from . import s3index
    for attempt in range(3):
        try:   # the service object reads IRSA's capabilities, so it fails too when IRSA is down
            res = pyvo.dal.SIA2Service(config.IRSA + 'SIA').search(pos=(ra, dec, max(radius_deg, 0.0003)), collection=collections).to_table()
            break
        except Exception as e:
            err = e
            if s3index.available():   # our own index of the S3 photos answers at once: don't keep IRSA retrying
                break
            time.sleep(3 * (attempt + 1))
    if res is None:
        if cache.exists():   # IRSA down: an older photo list beats no answer (it only misses photos added since)
            return json.loads(cache.read_text())
        if not s3index.available():
            raise RuntimeError(f'nasa-busy: NASA\'s photo index (IRSA) is not answering, try again in a few minutes ({str(err)[:120]})')
        rows = s3index.query(ra, dec, radius_deg)   # same photos, found from their headers on NASA's S3 copy
        res = []
    for r in res:
        if 'dataproduct_subtype' in res.colnames and r['dataproduct_subtype'] != 'science':
            continue
        url = str(r['access_url'])
        rows.append(dict(obs_id=str(r['obs_id']), band=str(r['energy_bandpassname'])[-2:], mjd=float(0.5 * (r['t_min'] + r['t_max'])),   # mid-exposure, as processing/
                         collection=str(r['obs_collection']), https=url,
                         s3=url.replace(config.IRSA + 'ibe/data/spherex/', config.S3_BASE)))
    vmap = _visits([r['mjd'] for r in rows])
    for r in rows:
        r['visit'] = vmap[r['mjd']]
    rows.sort(key=lambda r: (r['visit'], r['band'], r['mjd']))
    cache.parent.mkdir(parents=True, exist_ok=True); cache.write_text(json.dumps(rows))
    return rows

def pick(rows, bands, per_visit):
    """Up to `per_visit` photos per band per visit, spread evenly in time (enough for a clean median, keeps the fetch fast)."""
    out = []
    for v in sorted({r['visit'] for r in rows}):
        for b in bands:
            g = [r for r in rows if r['visit'] == v and r['band'] == b]
            if len(g) > per_visit:
                step = len(g) / per_visit
                g = [g[int(i * step)] for i in range(per_visit)]
            out.extend(g)
    return out

def summary(rows):
    vs = sorted({r['visit'] for r in rows})
    def iso(m): return (datetime.datetime(1858, 11, 17) + datetime.timedelta(days=m)).date().isoformat()
    return [dict(id=v, start=iso(min(r['mjd'] for r in rows if r['visit'] == v)), end=iso(max(r['mjd'] for r in rows if r['visit'] == v)),
                 n={b: sum(1 for r in rows if r['visit'] == v and r['band'] == b) for b in config.BANDS}) for v in vs]
