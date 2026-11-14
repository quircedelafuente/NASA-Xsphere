# SPHEREx Blink: engine (backend/) + processing + app (web/app, web/lib3d) in one container.
FROM python:3.11-slim
WORKDIR /srv
COPY backend/requirements.txt backend-req.txt
COPY processing/requirements.txt processing-req.txt
RUN pip install --no-cache-dir -r backend-req.txt -r processing-req.txt   # cached layer: code changes don't reinstall
COPY . .
ENV PORT=8000 WATCH_WEEKLY=1 SPHEREX_CACHE=/srv/cache
# Pre-load the 5 targets in the background, serve immediately (targets show "fetching" until ready)
CMD sh -c "cd backend && (python -m engine.prewarm > /srv/cache-prewarm.log 2>&1 &) && uvicorn engine.api:app --host 0.0.0.0 --port ${PORT}"
