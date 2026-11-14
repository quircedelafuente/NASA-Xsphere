"""A6 · HTTP API (contract I1). Run: uvicorn engine.api:app --app-dir backend --port 8000"""
import json, pathlib
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from . import config, jobs, resolve as R

app = FastAPI(title='SPHEREx Blink engine', version='0.1')
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['GET', 'POST'], allow_headers=['*'])   # public, read-only data

class ViewReq(BaseModel):
    ra_deg: float = Field(ge=0, lt=360)
    dec_deg: float = Field(ge=-90, le=90)
    fov_arcmin: float = Field(3.0, ge=1, le=10)
    bands: list[str] = Field(default_factory=lambda: list(config.BANDS))
    per_visit: int = Field(6, ge=1, le=20)
    target_id: str | None = None

class Box(BaseModel):
    ra_deg: float = Field(ge=0, lt=360)
    dec_deg: float = Field(ge=-90, le=90)
    w_arcmin: float = Field(gt=0)
    h_arcmin: float = Field(gt=0)

class ScanReq(BaseModel):
    box: Box

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
    bad = [b for b in req.bands if b not in config.BANDS]
    if bad:
        raise HTTPException(422, dict(error='bad-band', message=f'Unknown band(s) {bad}; use D1–D6.'))
    t = _target(req.target_id) if req.target_id else None
    key = jobs.start_view(req.ra_deg, req.dec_deg, req.fov_arcmin, req.bands, req.per_visit, t)
    return {'job': key}

@app.get('/view/{key}')
def view_status(key: str):
    j = jobs.JOBS.get(key) or jobs.cached(key)
    if not j:
        raise HTTPException(404, dict(error='unknown-job', message='This view is not known. Start it with POST /view.'))
    return {k: v for k, v in j.items() if k != 'trace'}

@app.post('/scan')
def scan(req: ScanReq):
    b = req.box
    if max(b.w_arcmin, b.h_arcmin) > config.MAX_ZONE_ARCMIN:
        raise HTTPException(422, dict(error='zone-too-large', message=f'Draw a zone up to {config.MAX_ZONE_ARCMIN}′ wide for now.'))
    try:   # chunk B (processing/) plugs in here; until it is merged, return the merged images so B can be tested against them
        from processing import scan as discover   # noqa: F401
    except ImportError:
        key = jobs.start_view(b.ra_deg, b.dec_deg, max(b.w_arcmin, b.h_arcmin), list(config.BANDS), 4)
        return {'job': key, 'note': 'Discovery engine (chunk B) not merged yet: this job returns the merged images (I2) for the zone.'}
    raise HTTPException(501, dict(error='not-wired', message='processing.scan found; wiring happens at integration (A10).'))

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

@app.get('/files/{key}/{name}')
def files(key: str, name: str):
    if name not in ('stacks.npz', 'stacks.json', 'view.json') or not key.startswith('v_') or '/' in key or '..' in key:
        raise HTTPException(404)
    p = config.CACHE / 'views' / key / name
    if not p.exists():
        raise HTTPException(404)
    return FileResponse(p)

@app.get('/', response_class=HTMLResponse)
def dev_page():
    """Developer test page (not the product UI, which is Niklas's)."""
    return (pathlib.Path(__file__).parent / 'devpage.html').read_text()
