"""A2 · Turn what the user typed into sky coordinates: known target names (fuzzy), coordinates, or any name via CDS Sesame."""
import difflib, math, re, urllib.parse, urllib.request
from . import config

def _norm(s):
    s = s.lower().replace('ε', 'eps').replace('epsilon', 'eps').replace('−', '-').replace("'", '').replace('’', '')
    return re.sub(r'[^a-z0-9+\-.]', '', s)

def propagate(t, year):
    """Position of a targets.json entry at a decimal year (linear proper motion)."""
    dt = year - t['ref_epoch']
    return (t['ra_deg'] + t['pmra_masyr'] / 3.6e6 * dt / math.cos(math.radians(t['dec_deg'])),
            t['dec_deg'] + t['pmdec_masyr'] / 3.6e6 * dt)

def parse_coords(q):
    """Decimal ('269.45 4.74', '269.45,+4.74') or sexagesimal ('17 57 48.5 +04 41 36', '17h57m48.5s +04d41m36s'). None if not coordinates."""
    s = q.strip().replace(',', ' ')
    raw = re.findall(r'[+\-−]?\d+(?:\.\d+)?', s)
    if not raw or re.search(r'[a-z]', re.sub(r'[hmsd]', '', s.lower())):
        return None
    nums = [float(n.replace('−', '-')) for n in raw]
    if len(nums) == 2:
        ra, dec = nums
    elif len(nums) == 6:
        sign = -1 if raw[3].startswith(('-', '−')) else 1   # keep the sign of "-00 30 ..." declinations
        ra = 15 * (nums[0] + nums[1] / 60 + nums[2] / 3600)
        dec = sign * (abs(nums[3]) + nums[4] / 60 + nums[5] / 3600)
    else:
        return None
    if not (0 <= ra < 360 and -90 <= dec <= 90):
        return None
    return ra, dec

def sesame(name):
    """CDS name resolver (SIMBAD, NED, VizieR). Returns (ra, dec) or None."""
    url = 'https://cds.unistra.fr/cgi-bin/nph-sesame/-oI/SNV?' + urllib.parse.quote(name)
    try:
        txt = urllib.request.urlopen(url, timeout=20).read().decode('utf-8', 'replace')
    except Exception:
        return None
    m = re.search(r'%J\s+([\d.]+)\s+([+\-][\d.]+)', txt)
    return (float(m.group(1)), float(m.group(2))) if m else None

def resolve(q, year=2026.0):
    """Returns {'matches': [...]}: best first. Each match: name, id (if a known target), ra_deg, dec_deg, source."""
    q = (q or '').strip()
    if not q:
        return {'matches': []}
    c = parse_coords(q)
    if c:
        return {'matches': [dict(name=f'{c[0]:.5f}, {c[1]:+.5f}', ra_deg=c[0], dec_deg=c[1], source='coordinates')]}
    nq, scored = _norm(q), []
    for t in config.targets():
        for a in [t['name'], t['id']] + t['aliases']:
            na = _norm(a)
            score = 1.0 if na == nq else (0.95 if nq and (nq in na or na in nq) else difflib.SequenceMatcher(None, nq, na).ratio())
            scored.append((score, t))
    scored.sort(key=lambda x: -x[0])
    out, seen = [], set()
    for score, t in scored:
        if score >= 0.6 and t['id'] not in seen:
            seen.add(t['id']); ra, dec = propagate(t, year)
            out.append(dict(name=t['name'], id=t['id'], ra_deg=ra, dec_deg=dec, source='targets.json', score=round(score, 2)))
    if not out or out[0]['score'] < 0.9:
        s = sesame(q)
        if s:
            out.insert(0, dict(name=q, ra_deg=s[0], dec_deg=s[1], source='CDS Sesame (J2000 catalogue position; no proper motion applied)'))
    return {'matches': out[:5]}
