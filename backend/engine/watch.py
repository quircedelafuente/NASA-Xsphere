"""A7 · Weekly update: NASA adds SPHEREx photos every week. For every finished view in the cache, ask NASA again;
if a spot has new photos, rebuild it (only the new photos are downloaded: older sections stay cached).

Run by hand:      cd backend && python -m engine.watch
Run weekly:       the API starts this every 7 days when WATCH_WEEKLY=1 (see api.py), or cron/launchd on the server."""
import json, time
from . import config, inventory, jobs

def refresh(dry_run=False, log=print):
    changed = []
    for p in sorted((config.CACHE / 'live').glob('v_*/job.json')):
        j = json.loads(p.read_text())
        c = j.get('center') or {}
        if j.get('status') != 'done' or 'ra_deg' not in c:
            continue
        old = j.get('n_photos_total') or 0
        q = config.CACHE / 'inventory'
        for f in q.glob('*.json'):          # force a fresh NASA query (the 6-hour list cache would hide new photos)
            if f.stat().st_mtime < time.time() - 3600:
                f.unlink()
        rows = inventory.query(c['ra_deg'], c['dec_deg'])
        if len(rows) > old:
            changed.append((j['key'], old, len(rows)))
            log(f"{j['key']}: {old} → {len(rows)} photos, rebuilding")
            if not dry_run:
                p.unlink()                  # drop the cached result; the next request (or below) rebuilds it
                jobs.wait(jobs.start_view(c['ra_deg'], c['dec_deg'], list((j.get('bands') or {}).keys()) or None, j.get('per_epoch'), j.get('target')))
    log(f'weekly check done: {len(changed)} spot(s) had new photos')
    return changed

if __name__ == '__main__':
    import sys
    refresh(dry_run='--dry-run' in sys.argv)
