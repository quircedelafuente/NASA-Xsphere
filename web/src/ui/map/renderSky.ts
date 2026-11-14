/** Draws the simplified sky (Milky Way glow, field stars, bright stars, constellation lines, labels). */
import { CONSTELLATIONS, STARS, STAR_BY_ID } from './skyData';
import { D2R, galToEq, type Projector } from './sphere';

// ---- precomputed layers ----
const MW: { ra: number; dec: number; w: number; a: number }[] = [];
for (let l = 0; l < 360; l += 2.5) {
  const dl = Math.min(l, 360 - l);
  const core = Math.exp(-((dl / 38) ** 2));
  const w = 7 + 9 * core;
  const a = 0.05 + 0.09 * core;
  for (const b of [-0.35, 0, 0.35]) {
    const p = galToEq(l, b * w);
    MW.push({ ...p, w: w * (b === 0 ? 1 : 0.8), a: a * (b === 0 ? 1 : 0.6) });
  }
}
const GC = galToEq(0, -1.5);

function rng(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}
/** Faint field stars, denser towards the galactic plane. Deterministic. */
const FIELD: { ra: number; dec: number; m: number; t: number; c: string }[] = (() => {
  const r = rng(7);
  const out: { ra: number; dec: number; m: number; t: number; c: string }[] = [];
  for (let i = 0; i < 2600; i++) {
    const l = r() * 360;
    const plane = r() < 0.55;
    const b = plane ? (r() + r() + r() - 1.5) * 14 : (Math.asin(2 * r() - 1) / D2R);
    const p = galToEq(l, b);
    const t = r();
    out.push({ ...p, m: r() ** 2.4, t, c: `rgb(${starColor(t)})` });
  }
  return out;
})();

/** The Milky Way glow is rendered at a fraction of CSS resolution: it is blurry anyway and fill cost drops ~10×. */
const MW_SCALE = 0.3;
let mwCanvas: HTMLCanvasElement | null = null;
let mwSoft: HTMLCanvasElement | null = null;
function mwLayer(W: number, H: number) {
  if (!mwCanvas) mwCanvas = document.createElement('canvas');
  if (!mwSoft) mwSoft = document.createElement('canvas');
  const w = Math.max(1, Math.ceil(W * MW_SCALE)), h = Math.max(1, Math.ceil(H * MW_SCALE));
  for (const c of [mwCanvas, mwSoft]) if (c.width !== w || c.height !== h) { c.width = w; c.height = h; }
  return { c: mwCanvas, ctx: mwCanvas.getContext('2d')!, soft: mwSoft, softCtx: mwSoft.getContext('2d')! };
}

export interface SkyLayerAlpha {
  base: number;   // field stars, bright stars, Milky Way
  lines: number;  // constellation lines & labels
}

function starColor(t: number) {
  // subtle temperature tint: bluish ↔ warm (no saturated red/green)
  return t < 0.33 ? '200,220,255' : t < 0.8 ? '240,240,245' : '255,226,190';
}

export function drawSky(ctx: CanvasRenderingContext2D, P: Projector, fov: number, alpha: SkyLayerAlpha, dpr: number) {
  const { W, H } = P;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, W, H);
  if (alpha.base <= 0.01 && alpha.lines <= 0.01) return;

  const onScreen = (x: number, y: number, r: number) => x > -r && x < W + r && y > -r && y < H + r;

  // ---- Milky Way: drawn into a small offscreen layer (it is a soft glow), then scaled up ----
  if (alpha.base > 0.01) {
    const L = mwLayer(W, H);
    const m = L.ctx;
    m.setTransform(1, 0, 0, 1, 0, 0);
    m.clearRect(0, 0, L.c.width, L.c.height);
    m.setTransform(MW_SCALE, 0, 0, MW_SCALE, 0, 0);
    m.globalCompositeOperation = 'lighter';
    const maxR = 2.2 * Math.hypot(W, H);
    for (const p of MW) {
      const q = P.project(p.ra, p.dec);
      if (q.cosc < -0.35) continue;
      const r = Math.min(maxR, p.w * D2R * q.k);
      if (r < 1 || !onScreen(q.x, q.y, r)) continue;
      const a = p.a * alpha.base * ((1 + q.cosc) / 2) ** 1.5; // dim where the projection stretches
      if (a < 0.002) continue;
      const g = m.createRadialGradient(q.x, q.y, 0, q.x, q.y, r);
      g.addColorStop(0, `rgba(150,170,215,${a})`);
      g.addColorStop(0.5, `rgba(120,140,200,${a * 0.45})`);
      g.addColorStop(1, 'rgba(90,110,180,0)');
      m.fillStyle = g;
      m.beginPath();
      m.arc(q.x, q.y, r, 0, Math.PI * 2);
      m.fill();
    }
    const c = P.project(GC.ra, GC.dec);
    if (c.cosc > -0.2) {
      const r = Math.min(maxR, 16 * D2R * c.k);
      if (r > 2 && onScreen(c.x, c.y, r)) {
        const g = m.createRadialGradient(c.x, c.y, 0, c.x, c.y, r);
        g.addColorStop(0, `rgba(255,225,190,${0.16 * alpha.base * ((1 + c.cosc) / 2) ** 1.5})`);
        g.addColorStop(1, 'rgba(255,225,190,0)');
        m.fillStyle = g;
        m.beginPath();
        m.arc(c.x, c.y, r, 0, Math.PI * 2);
        m.fill();
      }
    }
    m.globalCompositeOperation = 'source-over';
    // a 1px blur at low resolution hides the browser's gradient dithering before it is scaled up
    L.softCtx.clearRect(0, 0, L.soft.width, L.soft.height);
    L.softCtx.filter = 'blur(1.2px)';
    L.softCtx.drawImage(L.c, 0, 0);
    L.softCtx.filter = 'none';
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = 'high';
    ctx.globalCompositeOperation = 'lighter';
    ctx.drawImage(L.soft, 0, 0, W, H);
    ctx.globalCompositeOperation = 'source-over';

    // ---- field stars (one colour string per star, alpha via globalAlpha) ----
    const zoomBoost = Math.max(0, Math.min(1.2, Math.log10(180 / Math.max(fov, 1)) * 0.6));
    for (const s of FIELD) {
      const q = P.project(s.ra, s.dec);
      if (q.cosc < -0.4 || !onScreen(q.x, q.y, 2)) continue;
      const r = 0.35 + (1 - s.m) * 0.9 + zoomBoost * 0.5;
      ctx.globalAlpha = (0.25 + (1 - s.m) * 0.55) * alpha.base;
      ctx.fillStyle = s.c;
      ctx.fillRect(q.x - r / 2, q.y - r / 2, r, r);
    }
    ctx.globalAlpha = 1;
  }

  // ---- constellation lines ----
  if (alpha.lines > 0.01) {
    ctx.strokeStyle = `rgba(120,160,210,${0.32 * alpha.lines})`;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (const c of CONSTELLATIONS) {
      for (const [a, b] of c.lines) {
        const sa = STAR_BY_ID[a], sb = STAR_BY_ID[b];
        if (!sa || !sb) continue;
        const pa = P.project(sa.ra, sa.dec), pb = P.project(sb.ra, sb.dec);
        if (pa.cosc < -0.3 || pb.cosc < -0.3) continue;
        if (!onScreen(pa.x, pa.y, 0) && !onScreen(pb.x, pb.y, 0) && Math.hypot(pa.x - pb.x, pa.y - pb.y) < Math.max(W, H)) continue;
        // shorten the line a little at each end so stars sit in a gap
        const dx = pb.x - pa.x, dy = pb.y - pa.y, L = Math.hypot(dx, dy);
        if (L < 8) continue;
        const g = Math.min(5, L / 4);
        ctx.moveTo(pa.x + (dx / L) * g, pa.y + (dy / L) * g);
        ctx.lineTo(pb.x - (dx / L) * g, pb.y - (dy / L) * g);
      }
    }
    ctx.stroke();
  }

  // ---- bright stars ----
  if (alpha.base > 0.01) {
    for (const s of STARS) {
      const q = P.project(s.ra, s.dec);
      if (q.cosc < -0.4 || !onScreen(q.x, q.y, 20)) continue;
      const r = Math.max(0.8, 3.6 - s.mag * 0.62);
      if (s.mag < 1.6) {
        const g = ctx.createRadialGradient(q.x, q.y, 0, q.x, q.y, r * 4);
        g.addColorStop(0, `rgba(220,232,255,${0.35 * alpha.base})`);
        g.addColorStop(1, 'rgba(220,232,255,0)');
        ctx.fillStyle = g;
        ctx.beginPath();
        ctx.arc(q.x, q.y, r * 4, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.fillStyle = `rgba(245,247,255,${Math.min(1, 0.55 + (3 - s.mag) * 0.15) * alpha.base})`;
      ctx.beginPath();
      ctx.arc(q.x, q.y, r, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  // ---- labels ----
  if (alpha.lines > 0.05 && fov < 230) {
    ctx.font = '500 11px Inter, system-ui, sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const la = alpha.lines * Math.min(1, (230 - fov) / 60);
    ctx.fillStyle = `rgba(140,170,210,${0.55 * la})`;
    for (const c of CONSTELLATIONS) {
      let x = 0, y = 0, n = 0;
      const ids = new Set(c.lines.flat());
      let bad = false;
      ids.forEach((id) => {
        const s = STAR_BY_ID[id];
        const q = P.project(s.ra, s.dec);
        if (q.cosc < -0.2) bad = true;
        x += q.x; y += q.y; n++;
      });
      if (bad || !n) continue;
      x /= n; y /= n;
      if (!onScreen(x, y, -10)) continue;
      ctx.fillText(c.name.toUpperCase().split('').join(' '), x, y + 14);
    }
    if (fov < 130) {
      ctx.textAlign = 'left';
      ctx.fillStyle = `rgba(200,210,230,${0.6 * la})`;
      for (const s of STARS) {
        if (!s.name) continue;
        const q = P.project(s.ra, s.dec);
        if (q.cosc < -0.2 || !onScreen(q.x, q.y, -10)) continue;
        ctx.fillText(s.name, q.x + 7, q.y - 7);
      }
    }
  }
}
