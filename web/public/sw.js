// Keeps sky tiles and SPHEREx frames in the browser so zooming back in never re-downloads them.
// Sky tiles (HiPS, never change) → cache first, works even when IRSA is down.
// SPHEREx frames (/bundles/…/*.f32|png) → show cached copy at once, refresh it in the background (bands get rebuilt).
const TILES = 'hips-v1', FRAMES = 'frames-v1';
const isTile = (u) => /\/hips\/|alasky\.cds\.unistra\.fr\/DSS\//.test(u.href) && !u.pathname.includes('AladinLiteLogger');
const isFrame = (u) => u.origin === self.location.origin && /^\/(bundles|live)\/.+\.(f32|png)$/.test(u.pathname);

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => e.waitUntil(self.clients.claim()));

self.addEventListener('fetch', (e) => {
  if (e.request.method !== 'GET') return;
  const u = new URL(e.request.url);
  if (isTile(u)) e.respondWith(cacheFirst(e.request));
  else if (isFrame(u)) e.respondWith(staleWhileRevalidate(e.request, e));
});

async function cacheFirst(req) {
  const c = await caches.open(TILES);
  const hit = await c.match(req, { ignoreVary: true });
  if (hit) return hit;
  const r = await fetch(req);
  if (r.ok) c.put(req, r.clone());   // only good tiles; a 502 from IRSA is never stored
  return r;
}

async function staleWhileRevalidate(req, e) {
  const c = await caches.open(FRAMES);
  const hit = await c.match(req);
  const fresh = fetch(req).then((r) => { if (r.ok) c.put(req, r.clone()); return r; });
  if (hit) { e.waitUntil(fresh.catch(() => {})); return hit; }
  return fresh;
}
