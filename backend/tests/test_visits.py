import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from engine.inventory import _visits

def test_gap_rule():
    v = _visits([60900, 60901, 60950, 61100, 61101])        # 60900–60950 one visit (gap 49 d), then a >60 d gap
    assert v[60900] == v[60950] == 0 and v[61100] == v[61101] == 1

def test_deep_field_split_by_month():
    days = list(range(61000, 61200, 10))                     # 200 d with 10-d gaps: one group, longer than 60 d → monthly visits
    v = _visits(days)
    assert len(set(v.values())) >= 6

if __name__ == '__main__':
    test_gap_rule(); test_deep_field_split_by_month(); print('visits: all tests passed')
