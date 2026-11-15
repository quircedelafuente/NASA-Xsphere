"""A2 · Turn what the user typed into sky coordinates: known target names (fuzzy), coordinates, or any name via CDS Sesame."""
import difflib, math, re, time, urllib.parse, urllib.request
from . import config

def _norm(s):
    s = s.lower().replace('ε', 'eps').replace('epsilon', 'eps').replace('−', '-').replace("'", '').replace('’', '')
    return re.sub(r'[^a-z0-9+\-.]', '', s)

def propagate(t, year):
    """Position of a targets.json entry at a decimal year (linear proper motion)."""
    dt = year - t['ref_epoch']
    return (t['ra_deg'] + t['pmra_masyr'] / 3.6e6 * dt / math.cos(math.radians(t['dec_deg'])),
            t['dec_deg'] + t['pmdec_masyr'] / 3.6e6 * dt)

_UNITS = [('', 'h', 'd', '°', ':'), ('', 'm', '′', "'", ':'), ('', 's', '″', '"')]

def _group(g, is_ra):
    """1-3 numbers (sign, signed, value, is_integer, unit) -> degrees, or None."""
    if not 1 <= len(g) <= 3:
        return None
    for i, (neg, signed, v, integer, unit) in enumerate(g):
        if (i > 0 and (signed or v >= 60)) or (i < len(g) - 1 and not integer) or unit not in _UNITS[i]:
            return None
    neg, u = g[0][0], g[0][4]
    if (len(g) == 1 and u == ':') or (neg if is_ra else u == 'h'):
        return None
    v = sum(x[2] / 60 ** i for i, x in enumerate(g))
    if not is_ra:
        return (-v if neg else v) if v <= 90 else None
    hours = u == 'h' or (len(g) > 1 and u not in ('d', '°'))   # "17 57 48" is hours, "269.45" is degrees
    deg = v * 15 if hours else v
    return deg if deg < 360 else None

def parse_coords(q):
    """Coordinates typed in any usual way -> (ra, dec) in degrees; None if not coordinates (a name).
    Decimal ('269.45 4.74', '269.45,+4.74', '269.45° −4.74°', 'RA 269.45 Dec 4.74'), sexagesimal ('17 57 48.5 +04 41 36',
    '17:57:48.5 +04:41:36', '17h57m48.5s +04d41m36s', '17h57m +04d41m') or catalogue style ('J175748.5+044136').
    Mirror of parseCoords in web/src/ui/lib/astro.ts: keep the two in sync."""
    t = re.sub(r'[−–—]', '-', q.strip().lower())
    if not t:
        return None
    j = re.match(r'^j(\d{2})(\d{2})(\d{2}(?:\.\d+)?)([+-])(\d{2})(\d{2})(\d{2}(?:\.\d+)?)$', re.sub(r'\s+', '', t))
    if j:
        t = '{} {} {} {}{} {} {}'.format(*j.groups())
    t = re.sub(r'(?:right ascension|declination|\b(?:ra|decl?)\b|[αδ])\s*[:=]?', ' ', t)
    t = re.sub(r'degrees?|deg|º', '°', t)
    t = re.sub(r'[()\[\]=]', ' ', t)
    tokens = []
    def take(m):   # numbers with an optional sign and unit; nothing else may be left over
        tokens.append((m.group(1) == '-', m.group(1) != '', float(m.group(2)), m.group(2).isdigit(), m.group(3)))
        return ' '
    rest = re.sub(r'([+-]?)\s*(\d+(?:\.\d*)?|\.\d+)\s*([hd°m′\'s″":]?)', take, t)
    if re.search(r'[^\s,;/]', rest) or not 2 <= len(tokens) <= 6:
        return None
    # where does the declination start? at a sign, at a degree mark, after the seconds of RA, or half-way
    k = next((i for i, x in enumerate(tokens) if i > 0 and x[1]), -1)
    if k < 0:
        k = next((i for i, x in enumerate(tokens) if i > 0 and x[4] in ('d', '°')), -1)
    if k < 0:
        s = next((i for i, x in enumerate(tokens) if x[4] in ('s', '″', '"')), -1)
        if 0 <= s < len(tokens) - 1:
            k = s + 1
    if k < 0 and len(tokens) % 2 == 0:
        k = len(tokens) // 2
    if k < 1:
        return None
    ra, dec = _group(tokens[:k], True), _group(tokens[k:], False)
    return (ra, dec) if ra is not None and dec is not None else None

SESAME = ['https://cds.unistra.fr/cgi-bin/nph-sesame/-oI/SNV?',            # CDS Strasbourg
          'https://vizier.cfa.harvard.edu/viz-bin/nph-sesame/-oI/SNV?']    # same service, Harvard mirror (used when CDS is unreachable)

_down = {}   # mirror -> time of its last failure

def sesame(name):
    """CDS name resolver (SIMBAD, NED, VizieR). Returns (ra, dec) or None. Tries the mirrors in turn; a clear
    'nothing found' from one of them is final."""
    now = time.time()
    for base in sorted(SESAME, key=lambda b: now - _down.get(b, 0) < 600):   # a mirror that just failed goes last for 10 min
        try:
            txt = urllib.request.urlopen(base + urllib.parse.quote(name), timeout=6).read().decode('utf-8', 'replace')
        except Exception:
            _down[base] = now
            continue   # this mirror is down or slow: try the next
        m = re.search(r'%J\s+([\d.]+)\s+([+\-][\d.]+)', txt)
        if m:
            return float(m.group(1)), float(m.group(2))
        if 'othing found' in txt:
            return None
    return None

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
