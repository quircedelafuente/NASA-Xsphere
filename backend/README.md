# Chunk A · on-demand engine (Yasen)

NASA data is fetched **only when asked** (name, coordinates, or a zone), aligned, merged per band × visit, and **cached**. See WORKSPLIT.md.

## Run
```bash
python -m venv venv && venv/bin/pip install -r backend/requirements.txt
venv/bin/python -m uvicorn engine.api:app --app-dir backend --port 8000     # API + test page at http://127.0.0.1:8000/
cd backend && ../venv/bin/python -m engine.prewarm                          # pre-load the 5 targets (do before the demo)
claude mcp add spherex -- python -m engine.mcp_server                       # from backend/: Claude gets the engine as tools
python backend/tests/test_resolve.py                                         # name/coordinate tests
```

## Modules (`backend/engine/`)
| File | Task | What |
|---|---|---|
| `resolve.py` | A2 | Name (fuzzy, aliases, typos) or coordinates (decimal / sexagesimal) → RA/Dec; known targets motion-corrected; CDS Sesame fallback |
| `inventory.py` | A3 | Live SIA query on the 4 collections in config.yaml → photos per band, grouped into visits (D4 rule); cached 6 h |
| `fetch.py` | A4 | Only the needed pixels: S3 byte ranges, IRSA cutout fallback, retries; every cut cached on disk |
| `merge.py` | A5 | Reproject onto one TAN grid (3.075″/px), median per band × visit, PNG frames + difference frames, quick spectrum points, **writes I2 stacks** |
| `jobs.py` | A6/A7 | Background jobs, progress, visit-by-visit partial results, result cache (`cache/views/<key>/`) |
| `api.py` | A6 | Contract I1: `/resolve`, `/view`, `/view/{job}`, `/scan` (returns stacks until chunk B is merged), `/object/{id}`, `/targets`, `/files/...` |
| `prewarm.py` | A7 | Pre-load the 5 targets; re-run weekly (only new photos download) |
| `mcp_server.py` | A9 | MCP tools: `resolve_object`, `list_targets`, `view_sky`, `view_status` (mcp ≥ 2) |
| `devpage.html` | – | Developer test page at `/` (not the product UI) |

## Measured (14 Nov, IE Wi-Fi)
- Name → coordinates: instant. Photo list for Barnard: 358 photos, 6.5 s.
- One photo's pixels from S3: ~10 s here; 12 in parallel ≈ 73 s → **the network is the bottleneck**. Barnard, 36 photos: 206 s cold, **instant cached**.
- A server in AWS us-east-1 (next to the data) should be several times faster: the team measured 0.5–2.5 s per read from a server. ⚠ Hosting needs a decision.

## Known gaps
- Flags: no hard mask until `science/flags.json` (chunk C) exists; then it is applied automatically.
- Spectrum points are a quick 3×3 sum (uncalibrated); chunk B does proper photometry.
- `/scan` wiring to `processing.scan` happens at integration (A10).
