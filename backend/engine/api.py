"""A6 · HTTP API (contract I1). Run: uvicorn engine.api:app --app-dir backend --port 8000"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from . import config, jobs, resolve as R

app = FastAPI(title='SPHEREx Blink engine', version='0.2')

@app.on_event('startup')
def _weekly():
    import os, threading, time
    if os.environ.get('WATCH_WEEKLY') != '1':
        return
    def loop():
        from . import watch
        while True:
            time.sleep(7 * 24 * 3600)
            try:
                watch.refresh()
            except Exception as e:   # never take the API down because NASA was busy
                print('weekly check failed:', e)
    threading.Thread(target=loop, daemon=True).start()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['GET', 'POST'], allow_headers=['*'])   # public, read-only data

class ViewReq(BaseModel):
    ra_deg: float = Field(ge=0, lt=360)
    dec_deg: float = Field(ge=-90, le=90)
    bands: list[str] | None = None          # C4 band ids: D1..D6, D56. Default: the target's band + one more
    per_epoch: int | None = Field(None, ge=1, le=60)   # photos per detector per visit; None = automatic (matches the pre-warm cache)
    target_id: str | None = None

class Box(BaseModel):
    ra_deg: float = Field(ge=0, lt=360)
    dec_deg: float = Field(ge=-90, le=90)
    w_arcmin: float = Field(gt=0)
    h_arcmin: float = Field(gt=0)

class ScanReq(BaseModel):
    box: Box
    band: str = 'D4'
    per_epoch: int = Field(6, ge=1, le=30)

def _target(tid):
    for t in config.targets():
        if t['id'] == tid:
            return t
    return None

@app.get('/resolve')
def resolve(q: str):
    m = R.resolve(q)
    if not m['matches']:
        raise HTTPException(404, dict(error='name-not-found', message=f'No object or coordinates found for "{q}". Try a name like "Barnard\'s Star" or coordinates like "269.45 4.77".'))
    return m

@app.post('/view')
def view(req: ViewReq):
    from processing.bands import BANDS
    bad = [b for b in (req.bands or []) if b not in BANDS]
    if bad:
        raise HTTPException(422, dict(error='bad-band', message=f'Unknown band(s) {bad}; use {list(BANDS)}.'))
    t = _target(req.target_id) if req.target_id else None
    return {'job': jobs.start_view(req.ra_deg, req.dec_deg, req.bands, req.per_epoch, t)}

@app.get('/view/{key}')
@app.get('/scan/{key}')
def job_status(key: str):
    j = jobs.get(key)
    if not j:
        raise HTTPException(404, dict(error='unknown-job', message='This job is not known. Start it with POST /view or /scan.'))
    return {k: v for k, v in j.items() if k != 'trace'}

@app.post('/scan')
def scan(req: ScanReq):
    b = req.box
    if max(b.w_arcmin, b.h_arcmin) > config.MAX_ZONE_ARCMIN:
        raise HTTPException(422, dict(error='zone-too-large', message=f'Draw a zone up to {config.MAX_ZONE_ARCMIN}′ wide for now.'))
    return {'job': jobs.start_scan(b.ra_deg, b.dec_deg, b.w_arcmin, b.h_arcmin, req.band, req.per_epoch)}

@app.get('/object/{tid}')
def obj(tid: str):
    t = _target(tid)
    if not t:
        raise HTTPException(404, dict(error='name-not-found', message=f'No target "{tid}".'))
    notes = config.ROOT / 'science' / 'notes' / f'{tid}.md'
    return dict(target=t, notes=notes.read_text() if notes.exists() else None)

@app.get('/targets')
def targets():
    return [dict(id=t['id'], name=t['name'], kind=t['kind'], default_band=t['default_band']) for t in config.targets()]

# results: live bundles + reports (engine cache) and the pre-built bundles (processing) — same C4 format
(config.CACHE / 'live').mkdir(parents=True, exist_ok=True)
app.mount('/live', StaticFiles(directory=config.CACHE / 'live'), name='live')
_prebuilt = config.ROOT / 'web' / 'public' / 'bundles'
if _prebuilt.exists():
    app.mount('/bundles', StaticFiles(directory=_prebuilt), name='bundles')
_lib3d = config.ROOT / 'web' / 'lib3d'
if _lib3d.exists():
    app.mount('/lib3d', StaticFiles(directory=_lib3d), name='lib3d')
_appdir = config.ROOT / 'web' / 'app'
if _appdir.exists():
    app.mount('/', StaticFiles(directory=_appdir, html=True), name='app')   # the app screen (mounted last: catches /)
