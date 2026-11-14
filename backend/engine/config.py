"""Shared settings: repo paths, config.yaml values, cache folder. One place so every module agrees."""
import json, os, pathlib, re

try:  # networks that inspect HTTPS break Python's bundled CA list; the OS trust store works (see data/scripts/targets.py)
    import truststore; truststore.inject_into_ssl()
except ImportError:
    pass

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = pathlib.Path(os.environ.get('SPHEREX_CACHE', ROOT / 'cache'))   # git-ignored (cache/ in .gitignore)
CACHE.mkdir(parents=True, exist_ok=True)

def _yaml_list(text, key):
    # config.yaml is tiny and flat; avoid a YAML dependency for two values
    m = re.search(rf'{key}:\s*\[([^\]]*)\]', text)
    return [x.strip() for x in m.group(1).split(',')] if m else []

_cfg = (ROOT / 'config.yaml').read_text()
COLLECTIONS = _yaml_list(_cfg, 'collections') or ['spherex_dr1', 'spherex_dr1_deep', 'spherex_qr3', 'spherex_qr3_deep']
PIX_ARCSEC = 6.15                     # SPHEREx detector pixel
GRID_ARCSEC = 3.075                   # output grid: half a SPHEREx pixel (same as contracts/fixtures)
GAP_DAYS = 60                         # D4: a new visit starts after a 60-day gap
S3_BASE = 'https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/'
IRSA = 'https://irsa.ipac.caltech.edu/'
BANDS = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']
MAX_ZONE_ARCMIN = 30                  # MVP limit for a drawn zone (WORKSPLIT.md)

def targets():
    return json.loads((ROOT / 'data' / 'targets.json').read_text())

def flags_dictionary():
    """Sean's flag dictionary (C3): data/flags.json (or science/flags.json). None → no hard mask, flags only reported."""
    for p in (ROOT / 'data' / 'flags.json', ROOT / 'science' / 'flags.json'):
        if p.exists():
            return json.loads(p.read_text())
    return None

def hard_mask_bits():
    """Hard bits minus saturation bits and TRANSIENT: per data/flags.json saturation_note, those sit on the core of
    saturated targets (Barnard, RW Aur) in every frame, so masking them would erase the target. They become a warning instead."""
    f = flags_dictionary()
    if not f:
        return [], []
    sat = set(f.get('saturation_bits', [])) | {0}
    return sorted(set(f.get('hard_mask_bits', [])) - sat), sorted(sat)
