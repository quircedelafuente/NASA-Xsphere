# Putting SPHEREx Blink online

## Current setup (27 Nov 2026) · https://nasa-xsphere.vercel.app
- **Front end on Vercel** (project `nasa-xsphere`, static): the product UI plus the 5 challenge targets exported as static
  files (`deploy/export_static.py`), so the targets open instantly and keep working even if the engine is down.
- **Live engine** (name lookup, "Load SPHEREx photos here", "Select an area", `/explore`) runs on a small server and is reached
  through Vercel rewrites. Vercel serves its own files first and forwards only the engine paths
  (`/resolve`, `/view`, `/scan`, `/targets`, `/object`, `/live`, `/reports`, `/lib3d`, and `/bundles` that are not static).
- Publish / update: `deploy/vercel_site.sh https://<engine-url>` (builds the UI, exports the bundles, writes the rewrites into
  the site's `vercel.json`, deploys to production). `SKIP_BUILD=1` reuses the last build.
- The engine host runs the engine as an unprivileged, sandboxed service that only listens on a unix socket and can only
  open connections to the public internet (NASA/IRSA, S3, CDS); a Cloudflare tunnel is its only public entry.

---

**Why a host near NASA's data matters:** the engine reads small pieces of each SPHEREx photo from NASA's public copy on Amazon S3 in **us-east-1 (Virginia)**. From the IE Wi-Fi one photo takes ~10 s; from a server in Virginia the team measured 0.5–2.5 s. Pick a host region in or next to us-east-1.

## Option A · Render (simplest, free tier exists) ⚠ needs an account (Yasen's yes)
1. render.com → sign up (GitHub login) → New → Blueprint → pick this repo. It reads `render.yaml` (Docker, region Virginia).
2. Wait for the build (~5 min). The URL looks like `https://spherex-blink.onrender.com`.
3. Free plan: sleeps after 15 min idle (first visit ~1 min to wake) and forgets the cache on restart → the 5 targets re-load in the background after each wake. For judging, a paid "Starter" plan + a 1 GB disk at `/srv/cache` keeps everything warm (costs money: needs a yes).

## Option B · AWS App Runner / Lightsail in us-east-1 (fastest data, needs an AWS account + card)
Build the `Dockerfile`, push to ECR, create an App Runner service in us-east-1 on port 8000.

## Option C · this laptop (no account)
`uvicorn engine.api:app --app-dir backend --port 8000`, pre-load with `python -m engine.prewarm` before the demo. Only the 5 targets are instant; new spots take minutes on slow Wi-Fi.

## Optional AI summary (one call per zone scan)
Set `SCAN_LLM_URL` (e.g. `https://api.deepseek.com/chat/completions`), `SCAN_LLM_KEY`, `SCAN_LLM_MODEL` as host environment variables. Never put the key in the repo.
