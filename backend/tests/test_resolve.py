"""Run: python -m pytest backend/tests -q   (or python backend/tests/test_resolve.py)"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from engine.resolve import resolve, parse_coords

def first(q):
    m = resolve(q)['matches']
    return m[0] if m else None

def test_names_fuzzy():
    for q, want in [("Barnard's Star", 'barnards-star'), ('barnard', 'barnards-star'), ('BARNARDS STAR', 'barnards-star'), ('GJ 699', 'barnards-star'),
                    ('eps indi b', 'eps-indi-b'), ('ε Indi B', 'eps-indi-b'), ('epsilon indi B', 'eps-indi-b'),
                    ('WISE 0855', 'wise-0855'), ('wise0855', 'wise-0855'), ('WISE J085510.83-071442.5', 'wise-0855'),
                    ('RW Aur', 'rw-aurigae'), ('rw aurigae', 'rw-aurigae'), ('R Dra', 'r-draconis'), ('r draconis', 'r-draconis'),
                    ('barnad', 'barnards-star'), ('R Draconsi', 'r-draconis')]:
        assert first(q) and first(q).get('id') == want, (q, first(q))

def test_coordinates():
    assert parse_coords('269.448 4.739') == (269.448, 4.739)
    assert parse_coords('269.448, -4.739') == (269.448, -4.739)
    ra, dec = parse_coords('08 55 10.831 -07 14 42.53')
    assert abs(ra - 133.79513) < 1e-4 and abs(dec + 7.24515) < 1e-4
    ra, dec = parse_coords('08h55m10.831s -07d14m42.53s')
    assert abs(ra - 133.79513) < 1e-4 and abs(dec + 7.24515) < 1e-4
    ra, dec = parse_coords('17 57 48.5 +04 41 36')
    assert dec > 0
    assert parse_coords('400 10') is None and parse_coords('hello') is None

def test_coordinates_forgiving():
    near = lambda got, want: got is not None and abs(got[0] - want[0]) < 2e-3 and abs(got[1] - want[1]) < 2e-3
    for q in ['269.45 −4.74', '269.45° -4.74°', '269.45 deg, -4.74 deg', '(269.45; -4.74)', 'RA 269.45 Dec -4.74', 'ra=269.45, dec=-4.74', 'RA: 269.45 DEC: -4.74']:
        assert near(parse_coords(q), (269.45, -4.74)), q
    for q in ['17:57:48.5 +04:41:36', '17h57m48.5s+04d41m36s', '17h 57m 48.5s, +04° 41′ 36″', 'J175748.5+044136', 'RA 17h57m48.5s Dec +04d41m36s']:
        assert near(parse_coords(q), (269.4521, 4.6933)), q
    assert near(parse_coords('17h57m +04d41m'), (269.25, 4.6833)) and near(parse_coords('00 00 00 -00 30 00'), (0, -0.5))
    for q in ['wise 0855-0714', 'WISE J085510.83-071442.5', 'gj 699', 'hd 209458', '51 peg', '0855', '269.45', '17 57 61 +04 41 36', '100 95', '12:30', '2026-11-15']:
        assert parse_coords(q) is None, q

def test_name_variants():
    from engine.resolve import name_variants
    assert 'trappist-1' in [v.lower() for v in name_variants('trappist 1')] and 'trappist-1' in [v.lower() for v in name_variants('trappist1')]
    assert 'GJ 1214' in name_variants('gj1214') and 'HIP 87937' in name_variants('hip 87937')
    assert 'gj 1214' in name_variants('gj1214') and 'trappist-1 b' in name_variants('trappist 1 b')
    assert name_variants('alphacentauri') == ['alphacentauri', 'alpha centauri'] and 'tau ceti' in name_variants('tauceti')
    assert 'alpha ursae majoris' in name_variants('AlphaUrsaeMajoris') and 'proxima centauri' in name_variants('proximacentauri')
    assert 'orion nebula' in name_variants('orionnebula') and name_variants('betelgeuse') == ['betelgeuse']
    assert name_variants('Vega') == ['Vega'] and name_variants('J175748.5+044136') == ['J175748.5+044136']
    assert name_variants('TRAPPIST-1')[0] == 'TRAPPIST-1'   # as typed is always tried first

def test_wrong_number_is_not_a_target(monkeypatch=None):
    import engine.resolve as R
    keep, R.sesame = R.sesame, (lambda name: None)   # offline: only our own matching
    try:
        for q in ['hip 57367', 'gj 698', 'wise 0856']:
            assert first(q) is None, (q, first(q))
        assert first('wise 855')['id'] == 'wise-0855' and first('GJ699')['id'] == 'barnards-star'
    finally:
        R.sesame = keep

def test_motion_applied():
    m = first('barnard')      # Barnard at 2026 is ~104″ north of its 2016 Gaia position
    assert 4.766 < m['dec_deg'] < 4.770, m

if __name__ == '__main__':
    test_coordinates(); test_coordinates_forgiving(); test_names_fuzzy(); test_name_variants(); test_wrong_number_is_not_a_target(); test_motion_applied(); print('resolve: all tests passed')
