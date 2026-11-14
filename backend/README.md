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
| File | What |
|---|---|
| `resolve.py` | Name (fuzzy, aliases, typos) or coordinates → RA/Dec; known targets motion-corrected; CDS Sesame fallback |
| `inventory.py` | Live SIA query (4 collections) → photos per detector, grouped into visits; cached 6 h |
| `pipeline.py` | **Bridge to Quirce's engine**: live photos → `processing.frames.build_frames` (S3 sections, zodi + background, Sean's flags via config, inverse-variance co-add, outlier clipping) → `processing.change` (σ differences, candidates) → `processing.export` (C4 bundle). Live and pre-built bundles share one format |
| `scan.py` | Zone scan: bundle on a zone-sized grid → candidates grouped into sources → Gaia DR3 (propagated) + SkyBoT (per visit) → sorted with a one-line reason; optional single LLM summary (env `SCAN_LLM_URL/KEY`) |
| `jobs.py` | Background jobs, progress, cache (`cache/live/<job>/`) |
| `api.py` | I1: `/resolve`, `/view`, `/scan`, `/view|scan/{job}`, `/object/{id}`, `/targets`; static `/live/…` (live bundles + reports), `/bundles/…` (pre-built), `/` (app) |
| `prewarm.py` | Pre-load the 5 targets with all photos |
| `mcp_server.py` | MCP tools: `resolve_object`, `list_targets`, `view_sky`, `scan_zone`, `job_status` |

## Measured (14 Nov, IE Wi-Fi)
- Name → coordinates: instant. Photo list for Barnard: 358 photos, 6.5 s.
- One photo's pixels from S3: ~10 s here; 12 in parallel ≈ 73 s → **the network is the bottleneck**. Barnard, 36 photos: 206 s cold, **instant cached**.
- A server in AWS us-east-1 (next to the data) should be several times faster: the team measured 0.5–2.5 s per read from a server. ⚠ Hosting needs a decision.

## Known gaps
- Masking uses processing's flag list in config.yaml (Quirce); Sean's data/flags.json should replace it there.
- Zone grids > 64 px swap processing's CFG grid size under a lock (shortcut; better: a grid-size parameter in build_frames).
- No spectrum yet (was a quick sum in the removed merge.py); belongs to processing (B5).
- Sorting rules are interim in scan.py; `processing.classify` replaces them automatically when it exists.
