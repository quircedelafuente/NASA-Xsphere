// SPHEREx Blink app (first version by chunk A, for Niklas to take over). Talks only to our API (contract I1);
// reads results in the C4 bundle format (processing/export.py), the same for live and pre-built data.
import A from 'https://cdn.jsdelivr.net/npm/aladin-lite@3.8.2/dist/aladin.js';   // ES module build
const $ = s => document.querySelector(s);
const show = (id, on = true) => { $(id).hidden = !on; };
const API = '';
// a catalogue nobody could reach means "not checked", not "no known star here"
const catalogWarnings = rep => Object.entries(rep?.method?.catalog_sources || {}).filter(([, s]) => s === 'unavailable')
  .map(([c]) => `${c} could not be reached, so objects were not checked against it: "unknown" may be a known star.`);                                  // same origin as the engine (uvicorn serves this folder)
const SURVEYS = {
  spherex: 'https://irsa.ipac.caltech.edu/data/hips/SPHEREx/spherex_allsky_cube',   // NASA SPHEREx all-sky (DR1)
  // by URL from IRSA mirrors: CDS's own tile server (alasky) answered 404 on the IE network
  wise: 'https://irsa.ipac.caltech.edu/data/hips/CDS/2MASS/Color', dss: 'https://irsa.ipac.caltech.edu/data/hips/CDS/DSS2/color',
};
let APPEAR = {};   // web/lib3d/appearance.json: 3D dials per target, each tagged with how we know it
const EXPLAIN = [
  'SPHEREx photographs the whole sky every six months, so most spots have 3–4 visits so far.',
  'Each photo is about 65 MB. We read only a small square around your spot, straight from NASA\'s public cloud copy.',
  'Every SPHEREx photo sees the sky in one infrared colour, so we merge photos of the same colour range before comparing visits.',
  'Stars far away stay put. Nearby stars, brown dwarfs and asteroids shift between visits: that is what the blink reveals.',
  'A change only counts if it is at least 5 times bigger than the photo noise (5σ).',
  'Pluto was found in 1930 by blinking two photos of the same patch of sky. This is the same idea, in infrared.',
];
const CLASS_LABEL = { 'known-star': 'known star', 'known-asteroid': 'known asteroid', variable: 'variable', artefact: 'artefact',
  'candidate-mover': 'candidate mover', 'candidate-change': 'candidate change', 'unknown-static': 'unidentified static' };
// chunk B report (processing/discovery): position per visit, motion significance
const srcXY = (s, v) => { const p = s.positions?.find(q => q.visit === v) || s.positions?.[0] || s; return [p.x, p.y]; };
const srcSig = s => s.max_sigma ?? s.motion?.sig ?? null;

let aladin = null, overlay = null, cat = null, targets = [];
let V = null;            // current result: {kind, title, bands:{band: {base, man, imgs, diffs}}, band, report, target}
let ep = 0, mode = 'blink', playing = !matchMedia('(prefers-reduced-motion: reduce)').matches, timer = null, picked = null, three = null;

async function api(path, opts) {
  const r = await fetch(API + path, opts); let j = null;
  try { j = await r.json(); } catch { /* non-JSON error */ }
  // no JSON 404 = the engine isn't behind this site (static hosting), not a NASA problem
  if (r.status === 404 && !j) throw Object.assign(new Error('The search engine is not connected to this website yet, so only the 5 featured targets work here.'), { noEngine: true });
  if (!r.ok) throw new Error(j?.detail?.message || j?.message || `${r.status} ${r.statusText}`);
  return j;
}
const post = (p, body) => api(p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });

// ---------- sky map ----------
async function initMap() {
  try {
    await A.init;
    aladin = A.aladin('#map', { log: false, fov: 2, target: '269.45 4.77', cooFrame: 'ICRSd', showReticle: false, showCooGridControl: true,
      showProjectionControl: false, showFullscreenControl: false, showLayersControl: false, showSimbadPointerControl: false });
    setSurvey('dss');   // SPHEREx cube tiles render near-black with the default stretch
    overlay = A.graphicOverlay({ color: '#f0a43a', lineWidth: 2 }); aladin.addOverlay(overlay);
    cat = A.catalog({ name: 'Scan', sourceSize: 16, color: '#c792ff', shape: 'circle' }); aladin.addCatalog(cat);
  } catch (e) { $('#maphint').textContent = 'The sky map could not load (check the internet connection). Search still works.'; }
}
function setSurvey(k) {
  if (!aladin) return;
  try { aladin.setBaseImageLayer(A.imageHiPS(SURVEYS[k], { name: k })); } catch { /* keep current */ }
  document.querySelectorAll('#surveys button').forEach(b => b.setAttribute('aria-pressed', b.dataset.s === k));
}
$('#surveys').onclick = e => { const b = e.target.closest('button'); if (b) setSurvey(b.dataset.s); };
function mapGo(ra, dec, fovDeg = 0.2) { if (aladin) { aladin.gotoRaDec(ra, dec); aladin.setFoV(fovDeg); } }

// ---------- search ----------
let sugTimer = null;
$('#q').oninput = () => { clearTimeout(sugTimer); sugTimer = setTimeout(suggest, 250); };
async function suggest() {
  const q = $('#q').value.trim(); if (q.length < 2) return show('#suggest', false);
  try {
    const m = (await api('/resolve?q=' + encodeURIComponent(q))).matches;
    $('#suggest').innerHTML = m.map((x, i) => `<li data-i="${i}">${x.name}<small>${x.source === 'coordinates' ? 'coordinates' : x.id ? 'test target' : 'from SIMBAD'}</small></li>`).join('');
    $('#suggest').onclick = e => { const li = e.target.closest('li'); if (li) { show('#suggest', false); openPosition(m[+li.dataset.i]); } };
    show('#suggest', m.length > 0);
  } catch { show('#suggest', false); }
}
$('#search').onsubmit = async e => {
  e.preventDefault(); show('#suggest', false);
  try { const m = (await api('/resolve?q=' + encodeURIComponent($('#q').value))).matches; openPosition(m[0]); }
  catch (err) { fail(err.message, err.noEngine); }
};
document.addEventListener('click', e => { if (!e.target.closest('.search')) show('#suggest', false); });

// ---------- jobs ----------
let pollId = 0;
async function runJob(startPromise, onDone) {
  const my = ++pollId; let tick = 0;
  show('#intro', false); show('#result', false); show('#error', false); show('#wait');
  $('#bar').style.width = '2%'; $('#waitTitle').textContent = 'Asking NASA which photos cover this spot…';
  try {
    const { job } = await startPromise;
    while (my === pollId) {
      const j = await api('/view/' + job);
      $('#bar').style.width = Math.max(2, 100 * (j.progress || 0)) + '%';
      $('#waitTitle').textContent = { queued: 'Waiting for a free slot…', listing: 'Asking NASA which photos cover this spot…', fetching: 'Reading the photos from NASA and lining them up…',
        'checking catalogues': 'Checking every change against known stars and asteroids…', done: 'Done', error: 'Something went wrong' }[j.status] || j.status;
      $('#waitStep').textContent = [j.n_photos_total ? `${j.n_photos_total} photos of this spot exist` : '', j.current_band ? `band ${j.current_band}` : '', (j.log || []).slice(-1)[0] || ''].filter(Boolean).join(' · ');
      if (tick++ % 4 === 0) $('#explain').textContent = EXPLAIN[(tick / 4 | 0) % EXPLAIN.length];
      if (j.status === 'done') return onDone(j);
      if (j.status === 'error') throw new Error(j.message || 'The job failed.');
      await new Promise(r => setTimeout(r, 1500));
    }
  } catch (err) { if (my === pollId) fail(err.message, err.noEngine); }
}
function fail(msg, noEngine) { show('#wait', false); show('#error'); $('#error').innerHTML = `<h2>Could not finish</h2><p>${msg}</p>${noEngine ? '' : '<p class="note">NASA\'s servers can be busy; trying again in a minute usually works.</p>'}`; }

async function openPosition(m) {
  if (!m) return fail('No object or coordinates found. Try a name like "Barnard\'s Star" or coordinates like "269.45 4.77".');
  $('#q').value = m.name; setUrl({ q: m.name });
  mapGo(m.ra_deg, m.dec_deg); overlay?.removeAll(); cat?.removeAll();
  const t = targets.find(x => x.id === m.id) || null;
  runJob(post('/view', { ra_deg: m.ra_deg, dec_deg: m.dec_deg, target_id: m.id || null }), async j => {
    const bands = {}; for (const [b, url] of Object.entries(j.bands)) bands[b] = await loadBundle(url);
    const full = t ? (await api('/object/' + t.id)).target : null;
    present({ kind: 'view', title: m.name, target: full, bands, warnings: j.warnings || [], center: j.center });
  });
}

// ---------- zone drawing ----------
$('#drawBtn').onclick = () => { const on = $('#drawLayer').hidden; show('#drawLayer', on); $('#drawBtn').setAttribute('aria-pressed', on);
  $('#maphint').innerHTML = on ? 'Drag a box on the map (up to 30′ wide). Everything that changed inside it will be listed.' : 'Search a star, pick a test target, or <b>Draw a zone</b>.'; };
(() => {
  const L = $('#drawLayer'), R = $('#rect'); let s = null;
  L.onpointerdown = e => { const b = L.getBoundingClientRect(); s = [e.clientX - b.left, e.clientY - b.top]; L.setPointerCapture(e.pointerId); Object.assign(R.style, { left: s[0] + 'px', top: s[1] + 'px', width: 0, height: 0 }); show('#rect'); };
  L.onpointermove = e => { if (!s) return; const b = L.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top;
    Object.assign(R.style, { left: Math.min(s[0], x) + 'px', top: Math.min(s[1], y) + 'px', width: Math.abs(x - s[0]) + 'px', height: Math.abs(y - s[1]) + 'px' }); };
  L.onpointerup = e => {
    if (!s || !aladin) return; const b = L.getBoundingClientRect(), x = e.clientX - b.left, y = e.clientY - b.top, a = s; s = null;
    show('#rect', false); show('#drawLayer', false); $('#drawBtn').setAttribute('aria-pressed', false);
    if (Math.abs(x - a[0]) < 8 || Math.abs(y - a[1]) < 8) return;
    const c = [[a[0], a[1]], [x, a[1]], [x, y], [a[0], y]].map(p => aladin.pix2world(p[0], p[1]));
    if (c.some(p => !p)) return fail('Draw the box inside the sky.');
    startScan(c);
  };
})();
function sepArcmin(p, q) { const r = Math.PI / 180, d = Math.sin(p[1] * r) * Math.sin(q[1] * r) + Math.cos(p[1] * r) * Math.cos(q[1] * r) * Math.cos((p[0] - q[0]) * r); return Math.acos(Math.min(1, d)) / r * 60; }
function startScan(c) {
  const ra = c.reduce((s, p) => s + p[0], 0) / 4, dec = c.reduce((s, p) => s + p[1], 0) / 4;   // fine for zones ≤ 30′ away from RA = 0
  const w = Math.min(30, sepArcmin(c[0], c[1])), h = Math.min(30, sepArcmin(c[1], c[2]));
  scanZone(ra, dec, w, h);
}
function scanZone(ra, dec, w, h) {
  setUrl({ zone: [ra, dec, w, h].map(v => v.toFixed(4)).join(',') });
  overlay?.removeAll(); cat?.removeAll();
  const dra = w / 120 / Math.cos(dec * Math.PI / 180), ddec = h / 120;
  overlay?.add(A.polygon([[ra - dra, dec - ddec], [ra + dra, dec - ddec], [ra + dra, dec + ddec], [ra - dra, dec + ddec]]));
  runJob(post('/scan', { box: { ra_deg: ra, dec_deg: dec, w_arcmin: w, h_arcmin: h }, band: 'D4' }), async j => {
    const bands = j.report.bundle ? { D4: await loadBundle(j.report.bundle) } : {};
    cat?.addSources(j.report.sources.filter(s => s.class !== 'artefact').map(s => { const p = s.positions?.[0] || s; return A.source(p.ra_deg, p.dec_deg, { name: s.id }); }));
    present({ kind: 'scan', title: `Zone ${w.toFixed(1)}′ × ${h.toFixed(1)}′`, bands, report: j.report, warnings: catalogWarnings(j.report), center: { ra_deg: ra, dec_deg: dec } });
  });
}

// ---------- bundles (C4) ----------
async function loadBundle(url) {
  const base = url.replace(/manifest\.json$/, ''); const man = await (await fetch(url)).json();
  const load = src => new Promise(r => { const im = new Image(); im.onload = () => r(im); im.onerror = () => r(null); im.src = base + src; });
  const imgs = await Promise.all(man.frames.map(f => load(f.png)));
  const diffs = await Promise.all(man.frames.map((f, i) => { const d = man.diffs.find(x => x.from === 0 && x.to === i); return d ? load(d.png) : null; }));
  return { base, man, imgs, diffs };
}

// ---------- result ----------
function present(r) {
  V = r; V.band = Object.keys(r.bands)[0]; ep = 0; picked = null;
  show('#wait', false); show('#result');
  const t = r.target;
  $('#kind').textContent = r.kind === 'scan' ? 'zone scan' : (t?.kind || 'sky position');
  $('#where').textContent = `RA ${r.center.ra_deg.toFixed(4)}° · Dec ${r.center.dec_deg.toFixed(4)}°`;
  $('#title').textContent = t?.name || r.title;
  $('#blurb').textContent = r.kind === 'scan' ? (r.report.summary_text || '') : (t?.expected?.notes ||
    'Each frame is the same patch of sky on a different SPHEREx visit. Watch for anything that jumps between frames, or switch to Changes only.');
  const warns = [...(r.warnings || []), ...Object.values(r.bands).flatMap(b => b.man.warnings || [])];
  $('#warnings').innerHTML = [...new Set(warns)].map(w => `<p class="warn">${w.replace(/^D\d+6?: /, '')}</p>`).join('');
  $('#bands').innerHTML = Object.entries(r.bands).map(([b, x]) => `<button data-b="${b}" aria-pressed="${b === V.band}">${b} · ${x.man.lam_range_um[0].toFixed(1)}–${x.man.lam_range_um[1].toFixed(1)} µm</button>`).join('');
  renderScan(); render3D(t); strip(); draw(); loop();
}
function cur() { return V.bands[V.band]; }
function strip() {
  const m = cur().man;
  $('#strip').innerHTML = m.frames.map((f, i) => `<button data-e="${i}" aria-current="${i === ep}">Visit ${i + 1}<small>${f.date} · ${f.n_exposures} photos</small></button>`).join('');
}
function draw() {
  const c = $('#stage'), g = c.getContext('2d'), b = cur(), m = b.man, N = m.grid.nx, S = c.width / N;
  g.imageSmoothingEnabled = false; g.fillStyle = '#000'; g.fillRect(0, 0, c.width, c.height);
  const f = m.frames[ep];
  if (mode === 'pair') {
    const last = m.frames.length - 1;
    if (b.imgs[0]) g.drawImage(b.imgs[0], 0, 0, N, N, 0, c.height / 4, c.width / 2, c.height / 2);
    if (b.imgs[last]) g.drawImage(b.imgs[last], 0, 0, N, N, c.width / 2, c.height / 4, c.width / 2, c.height / 2);
    $('#hud').innerHTML = `Left <b>${m.frames[0].date}</b> · Right <b>${m.frames[last].date}</b>`;
  } else {
    const im = mode === 'diff' ? (b.diffs[ep] || null) : b.imgs[ep];
    if (im) g.drawImage(im, 0, 0, c.width, c.height);
    else { g.fillStyle = '#8d9ab0'; g.font = '16px Inter'; g.fillText('Visit 1 is the reference: changes are measured against it.', 20, c.height / 2); }
    if ($('#cross').checked && V.kind === 'view') {
      g.strokeStyle = '#f0a43a'; g.lineWidth = 2; const [x, y] = f.target_px.map(v => (v + .5) * S);
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { g.beginPath(); g.moveTo(x + dx * 10, y + dy * 10); g.lineTo(x + dx * 26, y + dy * 26); g.stroke(); }
      g.strokeStyle = 'rgba(127,178,255,.8)'; g.setLineDash([4, 4]); g.beginPath();
      m.target_track.forEach((p, i) => { const X = (p.x + .5) * S, Y = (p.y + .5) * S; i ? g.lineTo(X, Y) : g.moveTo(X, Y); }); g.stroke(); g.setLineDash([]);
    }
    if (V.report) for (const s of V.report.sources) {
      if (s.class === 'artefact' && picked !== s.id) continue;
      const [sx, sy] = srcXY(s, ep); const k = N / (V.report.zone ? Math.round(V.report.zone.w_arcmin * 60 / 3.075) : N);
      const X = (sx * k + .5) * S, Y = (N - 1 - sy * k + .5) * S;
      g.strokeStyle = picked === s.id ? '#f0a43a' : (s.class.startsWith('candidate') ? '#c792ff' : 'rgba(92,196,137,.8)');
      g.lineWidth = picked === s.id ? 3 : 1.5; g.beginPath(); g.arc(X, Y, 14, 0, 7); g.stroke();
    }
    $('#hud').innerHTML = `Visit <b>${ep + 1}/${m.frames.length}</b> · ${f.date}<br>${V.band} · <b>${m.lam_range_um[0].toFixed(2)}–${m.lam_range_um[1].toFixed(2)} µm</b>`;
  }
  $('#legend').textContent = mode === 'diff' ? 'red = brighter now · blue = fainter now (σ)' : `${(N * m.grid.pix_arcsec / 60).toFixed(1)}′ across · north up`;
  document.querySelectorAll('#strip button').forEach(x => x.setAttribute('aria-current', +x.dataset.e === ep));
  $('#modeHelp').textContent = { blink: 'Blink: the same patch at each visit, oldest first. Things that move jump; distant stars stay put.',
    diff: 'Changes only: each visit minus visit 1, measured against the photo noise. A mover leaves a red spot where it is now next to a blue spot where it was.',
    pair: 'First vs last: the first and latest visit side by side, for anyone who prefers no motion.' }[mode];
  setUrl();
}
function loop() { clearInterval(timer); if (playing && mode !== 'pair') timer = setInterval(() => { ep = (ep + 1) % cur().man.frames.length; draw(); }, 1000 / +$('#speed').value);
  $('#play').textContent = playing ? 'Pause' : 'Play'; }
$('#play').onclick = () => { playing = !playing; loop(); };
$('#speed').oninput = loop; $('#cross').onchange = draw;
$('#modes').onclick = e => { const b = e.target.closest('button'); if (!b) return; mode = b.dataset.m; document.querySelectorAll('#modes button').forEach(x => x.setAttribute('aria-pressed', x === b)); draw(); loop(); };
$('#bands').onclick = e => { const b = e.target.closest('button'); if (!b) return; V.band = b.dataset.b; ep = 0; document.querySelectorAll('#bands button').forEach(x => x.setAttribute('aria-pressed', x === b)); strip(); draw(); sync3D(); };
$('#strip').onclick = e => { const b = e.target.closest('button'); if (!b) return; ep = +b.dataset.e; playing = false; loop(); draw(); };

function renderScan() {
  show('#scanCard', V.kind === 'scan'); if (V.kind !== 'scan') return;
  const r = V.report, s = r.summary;
  $('#scanText').textContent = r.summary_text;
  $('#counts').innerHTML = [['known-star', s.known_star], ['known-asteroid', s.known_asteroid], ['variable', s.variable], ['candidate', s.candidate], ['unknown-static', s.unknown_static], ['artefact', s.artefact]]
    .filter(x => x[1]).map(([k, n]) => `<span class="pill p-${k}">${n} ${CLASS_LABEL[k] || 'candidates'}</span>`).join('');
  $('#sources').innerHTML = r.sources.map(x => `<li data-id="${x.id}"><span><span class="pill p-${x.class}">${CLASS_LABEL[x.class] || x.class}</span> <span class="mono note">${srcSig(x) != null ? Math.round(srcSig(x)) + 'σ · ' : ''}${Math.round(x.confidence * 100)}%${x.motion?.speed_arcsec_yr ? ' · ' + x.motion.speed_arcsec_yr.toFixed(2) + '″/yr ' + (x.motion.direction || '') : ''}</span></span><span class="why">${x.reason}</span></li>`).join('');
  $('#scanMethod').textContent = `Checked against Gaia DR3, CatWISE, AllWISE, 2MASS and known asteroids. ${r.photos_used ?? '?'} of ${r.photos_available ?? '?'} photos, ${Array.isArray(r.visits) ? r.visits.length : r.visits} visits${r.first_date ? ` (${r.first_date} to ${r.last_date})` : ''}. "Candidate" means unexplained so far, not a discovery.`;
}
$('#sources').onclick = e => { const li = e.target.closest('li'); if (!li) return; picked = li.dataset.id; const s0 = V.report.sources.find(x => x.id === picked); const s = s0.positions?.[0] || s0;
  document.querySelectorAll('#sources li').forEach(x => x.setAttribute('aria-current', x === li)); mapGo(s.ra_deg, s.dec_deg, 0.05); mode = 'diff';
  document.querySelectorAll('#modes button').forEach(x => x.setAttribute('aria-pressed', x.dataset.m === 'diff')); draw(); };

async function render3D(t) {
  three?.dispose(); three = null;
  const a = t && APPEAR[t.id]; show('#threeCard', !!a); if (!a) return;
  const p = { cls: a.cls, binary: a.binary };
  for (const [k, v] of Object.entries(a)) if (v && typeof v === 'object' && 'value' in v) p[k] = v.value;
  const { renderObject } = await import('/lib3d/lib3d.js');
  three = renderObject($('#three'), p);
  sync3D();
  $('#threeDials').innerHTML = Object.entries(a).filter(([, v]) => v && typeof v === 'object' && 'value' in v)
    .map(([k, v]) => `<span class="pill" title="${v.note || ''}">${k.replace('_K', ' (K)').replace('temp2', 'companion temp').replace('temp', 'temperature').replace('_days', ' (days)')}: ${v.value} · ${v.how}</span>`).join('');
}
// The 3D "SPHEREx infrared" view takes the tint of the band on screen (same false colour as the photos).
let threeView = 'eye';
function sync3D() { const r = V && V.bands && V.bands[V.band]?.man?.lam_range_um; three?.setView(threeView, r ? (r[0] + r[1]) / 2 : undefined); }
document.querySelector('#threeCard .seg').onclick = e => { const b = e.target.closest('button'); if (!b || !three) return; threeView = b.dataset.v; sync3D();
  document.querySelectorAll('#threeCard .seg button').forEach(x => x.setAttribute('aria-pressed', x === b)); };

// ---------- share / URL ----------
let urlState = {};
function setUrl(s) { if (s) urlState = s; const u = new URL(location.href); u.search = new URLSearchParams({ ...urlState, ...(V ? { band: V.band, mode } : {}) }).toString();
  history.replaceState(null, '', u); $('#link').textContent = u.href; }
$('#copy').onclick = async () => { try { await navigator.clipboard.writeText($('#link').textContent); $('#copy').textContent = 'Copied'; } catch { getSelection().selectAllChildren($('#link')); } };

// ---------- start ----------
(async () => {
  initMap();
  try { targets = await api('/targets'); } catch { targets = []; }
  try { APPEAR = await (await fetch('/lib3d/appearance.json')).json(); } catch { APPEAR = {}; }
  $('#chips').innerHTML = targets.map(t => `<button data-id="${t.id}">${t.name}</button>`).join('');
  $('#chips').onclick = async e => { const b = e.target.closest('button'); if (!b) return;
    const m = (await api('/resolve?q=' + encodeURIComponent(b.dataset.id))).matches.find(x => x.id === b.dataset.id); openPosition(m); };
  const p = new URLSearchParams(location.search);
  if (p.get('band')) mode = p.get('mode') || mode;
  if (p.get('zone')) { const [ra, dec, w, h] = p.get('zone').split(',').map(Number); mapGo(ra, dec, Math.max(w, h) / 60 * 2); scanZone(ra, dec, w, h); }
  else if (p.get('q')) { $('#q').value = p.get('q'); $('#search').requestSubmit(); }
})();
