"""Zone scan (WORKSPLIT "How we discover unknown objects"): a drawn box → frames on one grid (processing) →
change candidates (processing.change) → grouped into sources → cross-checked with Gaia DR3 + SkyBoT → sorted with a reason.

The sorting rules here are an interim layer owned by chunk A until processing provides `classify(report, ...)`;
when `processing.classify` exists it is used instead (WORKSPLIT B4)."""
import csv, io, json, math, os, time, traceback, urllib.parse, urllib.request
import numpy as np
import astropy.units as u
from astropy.coordinates import SkyCoord
from astropy.time import Time
from . import config, inventory, pipeline

GAIA_MATCH_ARCSEC = 9.0        # ~1.5 SPHEREx pixels
ASTEROID_MATCH_ARCSEC = 20.0   # SkyBoT uses a geocentric observer; SPHEREx orbits Earth, so allow a few arcsec of parallax
FAST_PM_MASYR = 100.0          # Gaia motion counted as a 'mover' (0.1″/yr); slower stars' changes are not motion

def _tap(query):
    url = config.IRSA + 'TAP/sync?' + urllib.parse.urlencode({'QUERY': query, 'FORMAT': 'csv', 'LANG': 'ADQL', 'REQUEST': 'doQuery'})
    for a in range(3):
        try:
            return list(csv.DictReader(io.StringIO(urllib.request.urlopen(url, timeout=120).read().decode())))
        except Exception:
            time.sleep(3 * (a + 1))
    return None

def gaia_in_box(ra, dec, radius_deg):
    rows = _tap(f"SELECT source_id, ra, dec, pmra, pmdec, parallax, phot_g_mean_mag FROM gaia_dr3_source "
                f"WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',{ra},{dec},{radius_deg})) AND phot_g_mean_mag < 21")
    return rows

def skybot(ra, dec, radius_deg, mjd):
    url = ('https://ssp.imcce.fr/webservices/skybot/api/conesearch.php?' +
           urllib.parse.urlencode({'-ep': f'{mjd + 2400000.5:.5f}', '-ra': ra, '-dec': dec, '-rd': radius_deg, '-mime': 'json', '-output': 'object', '-loc': '500'}))
    try:
        data = None
        for a in range(3):   # SkyBoT is slow under load
            try:
                r = urllib.request.urlopen(url, timeout=90)
                body = r.read()
                data = [] if r.status == 204 or not body.strip() else json.loads(body.decode()); break   # 204 = no known object in the field
            except Exception:
                time.sleep(4 * (a + 1))
        if data is None:
            return None
    except Exception:
        return None   # service down: report says "asteroid check unavailable"
    out = []
    for o in data if isinstance(data, list) else []:
        try:
            c = SkyCoord(o['RA (hms)'], o['DEC (dms)'], unit=(u.hourangle, u.deg))
            out.append(dict(name=o.get('Name'), num=o.get('Num'), cls=o.get('Class'), vmag=o.get('VMag (mag)'), ra=c.ra.deg, dec=c.dec.deg))
        except Exception:
            continue
    return out

def _sep(ra1, dec1, ra2, dec2):
    return math.hypot((ra1 - ra2) * math.cos(math.radians(dec1)), dec1 - dec2) * 3600

def group_sources(changes, frames, grid_wcs):
    """Candidates from every epoch pair → one entry per sky position (within 2 px), with every change seen there."""
    srcs = []
    for c in changes:
        for k in c['candidates']:
            ra, dec = (float(v) for v in grid_wcs.pixel_to_world_values(k['x'], k['y']))
            s = next((s for s in srcs if math.hypot(s['x'] - k['x'], s['y'] - k['y']) <= 2), None)
            if s is None:
                s = dict(x=k['x'], y=k['y'], ra_deg=ra, dec_deg=dec, seen=[], kinds=set(), max_sigma=0.0, saturated=False)
                srcs.append(s)
            s['seen'].append(dict(pair=[c['from'], c['to']], kind=k['kind'], sigma=k['sigma'],
                                  mjd=[round(frames[c['from']]['mjd'], 3), round(frames[c['to']]['mjd'], 3)]))
            s['kinds'].add(k['kind']); s['saturated'] |= k['saturated']
            s['max_sigma'] = max(s['max_sigma'], abs(k['sigma']))
    return srcs

def classify(s, gaia, asteroids, mean_year):
    """Interim rules (transparent, one-line reason each). Classes per contracts/report.md."""
    for mjd, objs in asteroids.items():
        for o in objs or []:
            d = _sep(s['ra_deg'], s['dec_deg'], o['ra'], o['dec'])
            if d < ASTEROID_MATCH_ARCSEC:
                s['crossmatch'].append(dict(cat='SkyBoT', id=o['name'], cls=o['cls'], sep_arcsec=round(d, 1), mjd=mjd))
                return 'known-asteroid', 0.9, f"Known asteroid {o['name']} ({o['cls']}) was {d:.0f}″ away on that date."
    dt = mean_year - 2016.0
    near = []   # Gaia stars propagated to the scan's mean date: (separation″, star, motion mas/yr)
    for g in gaia or []:
        gra = float(g['ra']) + float(g['pmra'] or 0) / 3.6e6 * dt / math.cos(math.radians(float(g['dec'])))
        gdec = float(g['dec']) + float(g['pmdec'] or 0) / 3.6e6 * dt
        near.append((_sep(s['ra_deg'], s['dec_deg'], gra, gdec), g, math.hypot(float(g['pmra'] or 0), float(g['pmdec'] or 0))))
    n_pairs = len({tuple(x['pair']) for x in s['seen']})
    # 1) a fast-moving star within 2 matching radii explains a brighter/fainter pair: the blobs sit ahead of / behind it
    movers = sorted((x for x in near if x[2] >= FAST_PM_MASYR and x[0] < 2 * GAIA_MATCH_ARCSEC), key=lambda x: x[0])
    if movers and ('moved' in s['kinds'] or s['kinds'] & {'brighter', 'fainter'}):
        d, g, pm = movers[0]
        s['crossmatch'].append(dict(cat='Gaia DR3', id=g['source_id'], sep_arcsec=round(d, 1), G=round(float(g['phot_g_mean_mag']), 2), pm_masyr=round(pm, 1)))
        return 'known-star', 0.95, f"Moving star: matches Gaia DR3 {g['source_id']} (G={float(g['phot_g_mean_mag']):.1f}), which moves {pm/1000:.2f}″/yr; the change is it shifting between visits."
    if s['saturated']:
        return 'artefact', 0.7, 'Change in the glare of an over-exposed bright star (detector saturated there), not a real change.'
    close = sorted((x for x in near if x[0] < GAIA_MATCH_ARCSEC), key=lambda x: x[0])
    if close:
        d, g, pm = close[0]
        s['crossmatch'].append(dict(cat='Gaia DR3', id=g['source_id'], sep_arcsec=round(d, 1), G=round(float(g['phot_g_mean_mag']), 2), pm_masyr=round(pm, 1)))
        if n_pairs >= 2 and s['kinds'] <= {'brighter', 'fainter'} and len(s['kinds']) == 1:
            return 'variable', 0.6, f"Known star Gaia DR3 {g['source_id']} gets {next(iter(s['kinds']))} in {n_pairs} visit pairs."
        return 'known-star', 0.5, f"Change at a known star (Gaia DR3 {g['source_id']}); likely a colour or image-sharpness difference between visits."
    if n_pairs == 1:
        return 'artefact', 0.6, 'Seen in one visit only and not in any catalogue: likely a cosmic ray or glint.'
    if 'moved' in s['kinds']:
        return 'candidate-mover', 0.5, f"Moves across {n_pairs} visit pairs and matches no Gaia star or known asteroid: worth a closer look."
    return 'candidate-change', 0.4, f"Changes across {n_pairs} visit pairs and matches nothing known: worth a closer look."

def summary_text(report):
    s = report['summary']; parts = [f"{s['sources']} changes found"]
    for k, label in (('known_star', 'known stars'), ('known_asteroid', 'known asteroids'), ('variable', 'variables'),
                     ('artefact', 'artefacts'), ('candidate', 'unexplained candidates')):
        if s.get(k):
            parts.append(f"{s[k]} {label}")
    return ': '.join([parts[0], ', '.join(parts[1:])]) + '.' if len(parts) > 1 else parts[0] + '.'

def llm_summary(report):
    """Optional single call per zone (WORKSPLIT): OpenAI-compatible endpoint from env (e.g. DeepSeek). Off unless SCAN_LLM_URL and SCAN_LLM_KEY are set."""
    url, key, model = os.environ.get('SCAN_LLM_URL'), os.environ.get('SCAN_LLM_KEY'), os.environ.get('SCAN_LLM_MODEL', 'deepseek-chat')
    if not (url and key):
        return None
    facts = [{k: s[k] for k in ('class', 'confidence', 'reason')} for s in report['sources'][:30]]
    body = json.dumps(dict(model=model, max_tokens=250, messages=[
        dict(role='system', content='Explain an astronomy scan result to a curious non-expert in 3 short sentences. Never say "discovery"; say "candidate". Use only the facts given.'),
        dict(role='user', content=json.dumps(dict(summary=report['summary'], sources=facts)))])).encode()
    try:
        req = urllib.request.Request(url, body, {'Content-Type': 'application/json', 'Authorization': f'Bearer {key}'})
        return json.loads(urllib.request.urlopen(req, timeout=60).read())['choices'][0]['message']['content']
    except Exception:
        return None

def run_scan(job, ra, dec, w_arcmin, h_arcmin, band, per_epoch):
    from . import jobs
    try:
        radius = math.hypot(w_arcmin, h_arcmin) / 2 / 60
        job.update(status='listing', progress=0.03)
        rows = inventory.query(ra, dec, radius_deg=radius)
        if not rows:
            raise RuntimeError('outside-coverage: SPHEREx has no photos of this zone yet')
        exps = pipeline.exposures(rows, band, per_epoch)
        grid_px = int(math.ceil(max(w_arcmin, h_arcmin) * 60 / 6.15))
        job.update(status='fetching', progress=0.08, n_photos_total=len(rows), n_photos_band=len(exps), visits=inventory.summary(rows))
        t = pipeline.field_target(ra, dec, name=f'Zone {ra:.3f} {dec:+.3f}')
        out = jobs.LIVE / job['key'] / band
        man, (grid_wcs, shape, frames, changes) = pipeline.build_band(t, band, exps, SkyCoord(ra * u.deg, dec * u.deg), out,
                                                                      grid_px=max(grid_px, 64), log=jobs._log(job))
        if man is None:
            raise RuntimeError('outside-coverage: fewer than 2 visits of this zone in this band, nothing to compare')
        job.update(status='checking catalogues', progress=0.85, bundle=f"/live/{job['key']}/{band}/manifest.json")
        srcs = group_sources(changes, frames, grid_wcs)
        gaia = gaia_in_box(ra, dec, radius)
        asteroids = {round(f['mjd'], 3): skybot(ra, dec, radius, f['mjd']) for f in frames}
        mean_year = Time(np.mean([f['mjd'] for f in frames]), format='mjd').jyear
        try:
            from processing.classify import classify as classify_b   # chunk B, when it exists
        except ImportError:
            classify_b = None
        for s in srcs:
            s['crossmatch'] = []
            s['class'], s['confidence'], s['reason'] = (classify_b or classify)(s, gaia, asteroids, mean_year)
            s['kinds'] = sorted(s['kinds'])
            s['appearance_class'] = {'known-asteroid': 'asteroid', 'candidate-mover': 'brown-dwarf'}.get(s['class'])
        # one moving star leaves several blobs (where it was / where it is, per visit pair): show it once
        merged, by_star = [], {}
        for s in srcs:
            gid = s['crossmatch'][0]['id'] if s['class'] == 'known-star' and s['confidence'] >= 0.9 and s['crossmatch'] else None
            if gid and gid in by_star:
                m = by_star[gid]; m['seen'] += s['seen']; m['max_sigma'] = max(m['max_sigma'], s['max_sigma']); m['blobs'] += 1
                m['kinds'] = sorted(set(m['kinds']) | set(s['kinds'])); continue
            s['blobs'] = 1
            if gid:
                by_star[gid] = s
            merged.append(s)
        srcs = merged
        order = {'candidate-mover': 0, 'candidate-change': 1, 'variable': 2, 'known-asteroid': 3, 'known-star': 4, 'artefact': 5}
        srcs.sort(key=lambda s: (order.get(s['class'], 9), -s['max_sigma']))
        for i, s in enumerate(srcs):
            s['id'] = f's{i + 1:03d}'
        cnt = lambda c: sum(1 for s in srcs if s['class'] == c)
        report = dict(zone=dict(ra_deg=ra, dec_deg=dec, w_arcmin=w_arcmin, h_arcmin=h_arcmin), band=band,
                      generated_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), visits=len(frames),
                      photos_used=len(exps), photos_available=len(rows),
                      checks=dict(gaia='ok' if gaia is not None else 'unavailable',
                                  asteroids='ok' if all(v is not None for v in asteroids.values()) else 'partly unavailable'),
                      summary=dict(sources=len(srcs), known_star=cnt('known-star'), known_asteroid=cnt('known-asteroid'),
                                   variable=cnt('variable'), artefact=cnt('artefact'),
                                   candidate=cnt('candidate-mover') + cnt('candidate-change')),
                      sources=srcs, bundle=job['bundle'],
                      method='processing.change sigma differences (≥5σ) → grouped → Gaia DR3 (propagated) + SkyBoT per visit → interim rules (engine/scan.py)')
        report['summary_text'] = llm_summary(report) or summary_text(report)
        (out.parent / 'report.json').write_text(json.dumps(report, indent=1))
        job.update(status='done', progress=1.0, report=report, report_url=f"/live/{job['key']}/report.json")
        jobs._save(job)
    except Exception as e:
        msg = str(e); code = msg.split(':')[0]
        job.update(status='error', error=code if code in ('outside-coverage', 'nasa-busy') else 'internal', message=msg,
                   trace=traceback.format_exc()[-1500:])
