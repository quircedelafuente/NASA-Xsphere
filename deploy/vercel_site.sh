#!/usr/bin/env bash
# Publish the product UI to Vercel as a static site, with the live-engine paths proxied to ENGINE_URL.
#   deploy/vercel_site.sh https://<engine-host>          (needs: npm, the repo venv, `npx vercel` logged in)
# The 5 challenge targets are served as static files (they work even if the engine is down); name search,
# "Select an area" scans and /explore views go to the engine through Vercel rewrites (filesystem first).
# SITE_DIR keeps the Vercel project link (.vercel/) between runs; VERCEL_PROJECT / VERCEL_SCOPE pick the project.
set -euo pipefail
ENGINE_URL="${1:?usage: $0 https://engine-host}"; ENGINE_URL="${ENGINE_URL%/}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SITE_DIR="${SITE_DIR:-$HOME/xsphere-site}"
PROJECT="${VERCEL_PROJECT:-nasa-xsphere}"; SCOPE="${VERCEL_SCOPE:-quirces-projects}"
PY="${PYTHON:-$ROOT/venv/bin/python}"

if [ "${SKIP_BUILD:-0}" != 1 ]; then
  (cd "$ROOT/web" && npm ci --silent && npm run build)
  (cd "$ROOT" && "$PY" deploy/export_static.py)
fi

mkdir -p "$SITE_DIR"
find "$SITE_DIR" -mindepth 1 -maxdepth 1 ! -name .vercel -exec rm -rf {} +
cp -r "$ROOT/web/dist/." "$SITE_DIR/"

"$PY" - "$ENGINE_URL" "$SITE_DIR/vercel.json" <<'EOF'
import json, sys
engine, out = sys.argv[1], sys.argv[2]
live = ['/resolve', '/view', '/view/:key', '/scan', '/scan/:key', '/targets', '/object/:id',
        '/live/:path*', '/reports/:path*', '/lib3d/:path*', '/bundles/:path*']
cfg = {
    'cleanUrls': False,
    'rewrites': [{'source': '/embed', 'destination': '/index.html'},
                 {'source': '/explore', 'destination': '/explore/index.html'}]
                + [{'source': s, 'destination': engine + s} for s in live],
    'headers': [
        {'source': '/(.*)', 'headers': [
            {'key': 'X-Content-Type-Options', 'value': 'nosniff'},
            {'key': 'Referrer-Policy', 'value': 'strict-origin-when-cross-origin'},
            {'key': 'Permissions-Policy', 'value': 'camera=(), microphone=(), geolocation=()'},
            {'key': 'Strict-Transport-Security', 'value': 'max-age=31536000'}]},
        {'source': '/assets/(.*)', 'headers': [{'key': 'Cache-Control', 'value': 'public, max-age=31536000, immutable'}]},
        {'source': '/sw.js', 'headers': [{'key': 'Cache-Control', 'value': 'no-cache'}]},
    ],
}
json.dump(cfg, open(out, 'w'), indent=1)
EOF

cd "$SITE_DIR"
[ -d .vercel ] || npx --yes vercel@latest link --yes --project "$PROJECT" --scope "$SCOPE" >/dev/null
npx --yes vercel@latest deploy --prod --yes --scope "$SCOPE"
