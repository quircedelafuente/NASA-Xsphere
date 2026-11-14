"""Build data/targets.json (contract C1) from live catalogue queries.

Run from the repo root:  python data/scripts/targets.py
Every number comes from a query recorded in data/SOURCES.md, except values marked LITERATURE below.
"""
import csv, io, json, math, sys, urllib.parse, urllib.request
from datetime import datetime, timezone

try:  # networks that inspect HTTPS (e.g. university Wi-Fi) break Python's own CA list; the OS trust store works
    import truststore; truststore.inject_into_ssl()
except ImportError:
    pass

TAP = 'https://irsa.ipac.caltech.edu/TAP/sync'
PIX = 6.15  # SPHEREx arcsec per pixel (config.yaml)

# One entry per target. gaia = DR3 source_id, or None to pick the brightest Gaia source within `cone` arcsec.
TARGETS = [
    dict(id='barnards-star', name="Barnard's Star", kind='mover', gaia=4472832130942575872,
         aliases=["Barnard's Star", 'GJ 699', 'HIP 87937'], default_band='D4', saturated=True, variability='none',
         notes='Fastest proper motion of any star. Core saturated (NaN) in D1–D3 and in our D4 sample; position still measurable. Sample build measured 9.8″ shift over 0.98 yr (expected 10.2″).'),
    dict(id='eps-indi-b', name='ε Indi B', kind='companion-mover', gaia=6412596012146801152,
         aliases=['eps Indi B', 'epsilon Indi B', 'ε Indi Ba/Bb', 'eps Ind B'], default_band='D56', saturated=False, variability='none',
         notes='Pair of brown dwarfs (Ba + Bb) orbiting the star ε Indi A; unresolved at 6.15″ pixels. Gaia DR3 entry is the combined light.'),
    dict(id='wise-0855', name='WISE 0855−0714', kind='mover', gaia=None, cone=None,
         aliases=['WISE 0855', 'WISE J085510.83-071442.5', 'WISE 0855-0714'], default_band='D56', saturated=False, variability='none',
         # LITERATURE: not in Gaia. pm from team research (research/01-data.md), marked [U] there: verify against Luhman & Esplin 2016 before launch.
         literature=dict(pmra_masyr=-8118.0, pmdec_masyr=680.0, plx_mas=None, source='research/01-data.md [U]; check Luhman & Esplin 2016 (arXiv:1605.08620)'),
         seed_2026=(133.75952610878713, -7.242216467013144),
         notes='Coldest known brown dwarf. Invisible below ~3.8 µm; needs per-visit co-adds in D5/D6. Catalogue (2010) position is ~2′ off today: always propagate.'),
    dict(id='rw-aurigae', name='RW Aurigae', kind='variable', gaia=None, cone=5.0, seed=(76.95608966179606, 30.401124999983193),
         aliases=['RW Aur', 'RW Aurigae'], default_band='D2', saturated=True, variability='irregular (young T Tauri binary, dimming events)',
         notes='Saturated (OVERFLOW) in ~all D1–D3 frames per research; use for variability with care.'),
    dict(id='r-draconis', name='R Draconis', kind='variable', gaia=None, cone=5.0, seed=(248.16723219463307, 66.75502666660118),
         aliases=['R Dra', 'R Draconis'], default_band='D2', saturated=None, variability='Mira, period ≈ 245 d',
         notes='In the north ecliptic deep field: ~monthly visits, enough for a light curve. Saturation not yet checked.'),
]

log = []  # (target, field, source) rows for SOURCES.md

def tap(query):
    url = TAP + '?' + urllib.parse.urlencode({'QUERY': query, 'FORMAT': 'csv', 'LANG': 'ADQL', 'REQUEST': 'doQuery'})
    for attempt in range(3):
        try:
            rows = list(csv.DictReader(io.StringIO(urllib.request.urlopen(url, timeout=180).read().decode())))
            return rows
        except Exception as e:
            err = e
    sys.exit(f'TAP query failed: {err}\n{query}')

def f(x):
    return None if x in (None, '') else float(x)

def propagate(ra, dec, pmra, pmdec, dt_yr):
    """Linear proper-motion propagation (good to <0.1″ over decades for these targets)."""
    return ra + pmra / 3.6e6 * dt_yr / math.cos(math.radians(dec)), dec + pmdec / 3.6e6 * dt_yr

def cone(table, cols, ra, dec, r_arcsec, order):
    return tap(f"SELECT {cols} FROM {table} WHERE 1=CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',{ra},{dec},{r_arcsec/3600})) ORDER BY {order}")

def jd_to_year(jd):
    return 2000.0 + (jd - 2451545.0) / 365.25

def mjd_to_year(mjd):
    return jd_to_year(mjd + 2400000.5)

out = []
for t in TARGETS:
    e = dict(id=t['id'], name=t['name'], aliases=t['aliases'], kind=t['kind'])
    gcols = 'source_id, ra, dec, pmra, pmdec, parallax, phot_g_mean_mag, ref_epoch'
    if t['gaia']:
        g = tap(f"SELECT {gcols} FROM gaia_dr3_source WHERE source_id = {t['gaia']}")[0]
    elif t.get('cone'):
        g = cone('gaia_dr3_source', gcols, *t['seed'], t['cone'], 'phot_g_mean_mag ASC')[0]
    else:
        g = None
    if g:
        e.update(ra_deg=f(g['ra']), dec_deg=f(g['dec']), ref_epoch=f(g['ref_epoch']), pmra_masyr=f(g['pmra']) or 0.0,
                 pmdec_masyr=f(g['pmdec']) or 0.0, plx_mas=f(g['parallax']), astrometry_source=f"Gaia DR3 {g['source_id']}")
        e['aliases'] = e['aliases'] + [f"Gaia DR3 {g['source_id']}"]
        log.append((t['id'], 'ra, dec, pm, parallax, ref_epoch', f"Gaia DR3 {g['source_id']} (G={float(g['phot_g_mean_mag']):.2f}) via IRSA TAP gaia_dr3_source"))
    else:  # WISE 0855: AllWISE position as reference, literature proper motion
        L = t['literature']
        ra26, dec26 = t['seed_2026']
        ra10, dec10 = propagate(ra26, dec26, L['pmra_masyr'], L['pmdec_masyr'], 2010.5 - 2026.0)
        w = cone('allwise_p3as_psd', 'designation, ra, dec, w1mpro, w2mpro, w1mjdmean', ra10, dec10, 15, 'w2mpro ASC')[0]
        e.update(ra_deg=f(w['ra']), dec_deg=f(w['dec']), ref_epoch=round(mjd_to_year(f(w['w1mjdmean'])), 3),
                 pmra_masyr=L['pmra_masyr'], pmdec_masyr=L['pmdec_masyr'], plx_mas=L['plx_mas'],
                 astrometry_source=f"AllWISE {w['designation']} position + literature proper motion")
        log.append((t['id'], 'ra, dec, ref_epoch', f"AllWISE {w['designation']} (W2={w['w2mpro']}) via IRSA TAP allwise_p3as_psd; epoch = w1mjdmean"))
        log.append((t['id'], 'pmra, pmdec', f"LITERATURE, unverified: {L['source']}"))
        log.append((t['id'], 'plx_mas', 'not set: needs a literature value with citation'))

    # archival positions: where it was in 2MASS (~2000) and AllWISE (~2010)
    arch = []
    for survey, table, cols, order, epoch_col, conv, guess in [
        ('2MASS', 'fp_psc', 'designation, ra, dec, k_m, jdate', 'k_m ASC', 'jdate', jd_to_year, 2000.0),
        ('AllWISE', 'allwise_p3as_psd', 'designation, ra, dec, w2mpro, w1mjdmean', 'w2mpro ASC', 'w1mjdmean', mjd_to_year, 2010.5)]:
        if survey == 'AllWISE' and t['id'] == 'wise-0855':
            arch.append(dict(survey='AllWISE', epoch=e['ref_epoch'], ra_deg=e['ra_deg'], dec_deg=e['dec_deg'])); continue
        ra_g, dec_g = propagate(e['ra_deg'], e['dec_deg'], e['pmra_masyr'], e['pmdec_masyr'], guess - e['ref_epoch'])
        rows = cone(table, cols, ra_g, dec_g, 40, order)   # wide cone: the survey's real epoch can differ from the guess by >1 yr
        def sep(r):  # arcsec from the position propagated to THAT row's own epoch
            ra_p, dec_p = propagate(e['ra_deg'], e['dec_deg'], e['pmra_masyr'], e['pmdec_masyr'], conv(f(r[epoch_col])) - e['ref_epoch'])
            return math.hypot((f(r['ra']) - ra_p) * math.cos(math.radians(dec_p)), f(r['dec']) - dec_p) * 3600
        rows = [r for r in rows if sep(r) < 3.0]   # nearest real counterpart only; a faint target may be undetected
        rows.sort(key=sep)
        if rows:
            r = rows[0]
            arch.append(dict(survey=survey, epoch=round(conv(f(r[epoch_col])), 3), ra_deg=f(r['ra']), dec_deg=f(r['dec'])))
            log.append((t['id'], f'archival {survey}', f"{r['designation']} via IRSA TAP {table} (nearest within 3″ of the propagated position)"))
        else:
            log.append((t['id'], f'archival {survey}', 'not detected (no source within 3″ of the propagated position)'))
    e['archival_positions'] = arch

    pm = math.hypot(e['pmra_masyr'], e['pmdec_masyr']) / 1000
    e['default_band'] = t['default_band']
    e['fov_arcsec'] = 64 * PIX
    e['expected'] = dict(motion_arcsec_per_yr=round(pm, 3), motion_px_per_yr=round(pm / PIX, 3),
                         variability=t['variability'], saturated=t['saturated'], notes=t['notes'])
    out.append(e)
    print(f"{t['id']:14s} ra={e['ra_deg']:.6f} dec={e['dec_deg']:.6f} @{e['ref_epoch']}  pm={pm:.3f}″/yr ({pm/PIX:.2f} px/yr)  archival={[a['survey'] for a in arch]}")

# self-check: propagated archival epochs should land near the catalogue positions (validates pm sign/units)
for e in out:
    for a in e['archival_positions']:
        ra_p, dec_p = propagate(e['ra_deg'], e['dec_deg'], e['pmra_masyr'], e['pmdec_masyr'], a['epoch'] - e['ref_epoch'])
        sep = math.hypot((a['ra_deg'] - ra_p) * math.cos(math.radians(dec_p)), a['dec_deg'] - dec_p) * 3600
        a['offset_from_prediction_arcsec'] = round(sep, 2)
        assert sep < 3.0, f"{e['id']} {a['survey']} is {sep:.1f}″ from the propagated position: check proper motion"

stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
json.dump(out, open('data/targets.json', 'w'), indent=2, ensure_ascii=False)
with open('data/SOURCES.md', 'w') as s:
    s.write(f"# Sources for data/targets.json\n\nGenerated {stamp} by `data/scripts/targets.py` (live queries to IRSA TAP, https://irsa.ipac.caltech.edu/TAP).\n"
            "Re-run to regenerate. Values marked LITERATURE must be checked against the cited paper before launch.\n\n"
            "| Target | Field | Source |\n|---|---|---|\n")
    for row in log:
        s.write('| ' + ' | '.join(row) + ' |\n')
    s.write('\nArchival positions are checked automatically: each must lie within 3″ of the position propagated with the proper motion '
            '(column `offset_from_prediction_arcsec`). Text fields (kind, variability, notes) come from the team research (research/01-data.md) and need the science notes (D-4) for citations.\n')
print('wrote data/targets.json and data/SOURCES.md')
