"""A7 · Pre-warm the cache with the 5 official targets so judges never wait. Run: python -m engine.prewarm  (from backend/)
Re-run weekly (or after a new release in config.yaml): only new photos are downloaded, everything else comes from cache/."""
import sys, time
from . import config, jobs
from .resolve import propagate

PER_EPOCH = None   # all photos for the official targets (best quality; done once, before the demo)

def main(ids=None):
    for t in config.targets():
        if ids and t['id'] not in ids:
            continue
        ra, dec = propagate(t, 2026.0)
        t0 = time.time(); key = jobs.start_view(ra, dec, None, PER_EPOCH, t); j = jobs.wait(key, timeout=7200)
        print(f"{t['id']:14s} {j.get('status')} {time.time()-t0:5.0f}s bands {list((j.get('bands') or {}).keys())} photos {j.get('n_photos_total')} key {key} {j.get('message') or ''}", flush=True)

if __name__ == '__main__':
    main(sys.argv[1:] or None)
