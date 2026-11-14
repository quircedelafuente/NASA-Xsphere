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

def test_motion_applied():
    m = first('barnard')      # Barnard at 2026 is ~104″ north of its 2016 Gaia position
    assert 4.766 < m['dec_deg'] < 4.770, m

if __name__ == '__main__':
    test_coordinates(); test_names_fuzzy(); test_motion_applied(); print('resolve: all tests passed')
