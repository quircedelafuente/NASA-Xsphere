"""A7 · Pre-warm the cache with the 5 official targets so judges never wait. Run: python -m engine.prewarm  (from backend/)
Re-run weekly (or after a new release in config.yaml): only new photos are downloaded, everything else comes from cache/."""
import sys, time
from . import config, jobs
from .resolve import propagate

BANDS = ['D2', 'D4', 'D5', 'D6']   # D2 for the variables' light curves; D4–D6 for movers and brown dwarfs (D1–D3 saturate on bright stars)
PER_VISIT = 3

def main(ids=None):
    for t in config.targets():
        if ids and t['id'] not in ids:
            continue
        ra, dec = propagate(t, 2026.0)
        t0 = time.time(); key = jobs.start_view(ra, dec, 3.0, BANDS, PER_VISIT, t); j = jobs.wait(key, timeout=3600)
        print(f"{t['id']:14s} {j.get('status')} {time.time()-t0:5.0f}s photos {j.get('n_photos_used')}/{j.get('n_photos_total')} key {key} {j.get('message') or ''}", flush=True)

if __name__ == '__main__':
    main(sys.argv[1:] or None)
