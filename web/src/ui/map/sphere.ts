/**
 * Camera + stereographic projection for the sky map.
 * Orientation matches the sky as seen from Earth and the SPHEREx cut-outs: north up, east LEFT.
 * Camera fov = horizontal field of view in degrees.
 */
export const D2R = Math.PI / 180;

export interface Camera {
  ra: number;  // deg
  dec: number; // deg
  fov: number; // deg, horizontal
}

export const MIN_FOV = 0.06;
export const MAX_FOV = 330;

/** The map draws the sky only up to ~100° from the centre, so zooming out further leaves a disc in a black frame.
 *  Cap the zoom-out so the screen corners stay ≤ CORNER_DEG from the centre: the sky always fills the screen. */
const CORNER_DEG = 138;   // renderSky draws stars out to ~150° (cosc −0.87), so corners at 125° are always filled
/** Zoom-in limit: the shorter screen side always shows at least this much sky, so an open patch (6.6′) never
 *  swallows the screen and the controls around it stay usable. */
const MIN_SPAN_ARCMIN = 10;
let screenMaxFov = MAX_FOV;
let screenMinFov = MIN_FOV;
export function setViewport(W: number, H: number) {
  if (W <= 0 || H <= 0) return;
  const k = Math.tan((CORNER_DEG * D2R) / 2) * (W / 2) / Math.hypot(W / 2, H / 2);
  screenMaxFov = Math.min(MAX_FOV, (4 * Math.atan(k)) / D2R);
  screenMinFov = Math.max(MIN_FOV, (MIN_SPAN_ARCMIN / 60) * W / Math.min(W, H));
}

export function clampFov(f: number) {
  return Math.min(screenMaxFov, Math.max(screenMinFov, f));
}

export function normRa(ra: number) {
  return ((ra % 360) + 360) % 360;
}

/** Pixels per projection unit (stereographic r = 2·tan(c/2)). */
export function scaleFor(cam: Camera, W: number) {
  return W / 2 / (2 * Math.tan((Math.min(cam.fov, 340) * D2R) / 4));
}

/** Inverse of scaleFor: horizontal fov for a given scale. */
export function fovForScale(s: number, W: number) {
  return (4 * Math.atan(W / (4 * s))) / D2R;
}

export interface Projected {
  x: number;
  y: number;
  /** cos of angular distance from the centre (−1…1) */
  cosc: number;
  /** local linear magnification (px per radian at that point) */
  k: number;
}

export function makeProjector(cam: Camera, W: number, H: number) {
  const s = scaleFor(cam, W);
  const a0 = cam.ra * D2R;
  const d0 = cam.dec * D2R;
  const sd0 = Math.sin(d0), cd0 = Math.cos(d0);
  const cx = W / 2, cy = H / 2;

  function project(raDeg: number, decDeg: number): Projected {
    const a = raDeg * D2R, d = decDeg * D2R;
    const sd = Math.sin(d), cd = Math.cos(d);
    const da = a - a0;
    const cda = Math.cos(da);
    const cosc = sd0 * sd + cd0 * cd * cda;
    const k = 2 / Math.max(1e-6, 1 + cosc);
    const xe = k * cd * Math.sin(da);
    const yn = k * (cd0 * sd - sd0 * cd * cda);
    return { x: cx - s * xe, y: cy - s * yn, cosc, k: s * k };
  }

  function unproject(x: number, y: number): { ra: number; dec: number } {
    const xe = -(x - cx) / s;
    const yn = -(y - cy) / s;
    const rho = Math.hypot(xe, yn);
    if (rho < 1e-12) return { ra: cam.ra, dec: cam.dec };
    const c = 2 * Math.atan(rho / 2);
    const sc = Math.sin(c), cc = Math.cos(c);
    const dec = Math.asin(Math.max(-1, Math.min(1, cc * sd0 + (yn * sc * cd0) / rho)));
    const ra = a0 + Math.atan2(xe * sc, rho * cd0 * cc - yn * sd0 * sc);
    return { ra: normRa(ra / D2R), dec: dec / D2R };
  }

  return { project, unproject, scale: s, W, H };
}

export type Projector = ReturnType<typeof makeProjector>;

/** Angular distance in degrees. */
export function angDist(ra1: number, dec1: number, ra2: number, dec2: number) {
  const a = Math.sin(dec1 * D2R) * Math.sin(dec2 * D2R) + Math.cos(dec1 * D2R) * Math.cos(dec2 * D2R) * Math.cos((ra1 - ra2) * D2R);
  return Math.acos(Math.max(-1, Math.min(1, a))) / D2R;
}

function toVec(ra: number, dec: number): [number, number, number] {
  const a = ra * D2R, d = dec * D2R;
  return [Math.cos(d) * Math.cos(a), Math.cos(d) * Math.sin(a), Math.sin(d)];
}
function fromVec(v: [number, number, number]) {
  const n = Math.hypot(v[0], v[1], v[2]) || 1;
  return { ra: normRa(Math.atan2(v[1], v[0]) / D2R), dec: Math.asin(v[2] / n) / D2R };
}

/** Great-circle interpolation between two positions. */
export function slerp(a: { ra: number; dec: number }, b: { ra: number; dec: number }, t: number) {
  const va = toVec(a.ra, a.dec), vb = toVec(b.ra, b.dec);
  const dot = Math.max(-1, Math.min(1, va[0] * vb[0] + va[1] * vb[1] + va[2] * vb[2]));
  const om = Math.acos(dot);
  if (om < 1e-9) return { ra: b.ra, dec: b.dec };
  const sa = Math.sin((1 - t) * om) / Math.sin(om), sb = Math.sin(t * om) / Math.sin(om);
  return fromVec([va[0] * sa + vb[0] * sb, va[1] * sa + vb[1] * sb, va[2] * sa + vb[2] * sb]);
}

/** Mean direction of a set of points. */
export function centroid(pts: { ra: number; dec: number }[]) {
  const v: [number, number, number] = [0, 0, 0];
  pts.forEach((p) => { const u = toVec(p.ra, p.dec); v[0] += u[0]; v[1] += u[1]; v[2] += u[2]; });
  return fromVec(v);
}

export interface FitArea { left: number; right: number; top: number; bottom: number }

/**
 * Camera that shows all points inside the free part of a W×H viewport (insets in px: room for the search bar,
 * labels to the right of markers, etc.). Centre = direction minimising the largest distance to any point.
 */
export function fitCamera(pts: { ra: number; dec: number }[], W: number, H: number, inset: FitArea): Camera {
  const worst = (ra: number, dec: number) => Math.max(...pts.map((p) => angDist(ra, dec, p.ra, p.dec)));
  let c = centroid(pts);
  let best = worst(c.ra, c.dec);
  for (let dec = -85; dec <= 85; dec += 5) {
    for (let ra = 0; ra < 360; ra += 5) {
      const w = worst(ra, dec);
      if (w < best) { best = w; c = { ra, dec }; }
    }
  }
  for (let step = 2.5; step > 0.2; step /= 2) {
    for (const [dr, dd] of [[step, 0], [-step, 0], [0, step], [0, -step]]) {
      const ra = normRa(c.ra + dr), dec = Math.max(-89, Math.min(89, c.dec + dd));
      const w = worst(ra, dec);
      if (w < best) { best = w; c = { ra, dec }; }
    }
  }
  // project at a reference scale, then pick the largest scale at which every point stays inside the
  // free area (each side has its own inset, e.g. extra room on the right for marker labels)
  const ref = makeProjector({ ...c, fov: 90 }, W, H);
  let k = Infinity;
  for (const p of pts) {
    const q = ref.project(p.ra, p.dec);
    const dx = q.x - W / 2, dy = q.y - H / 2;
    const roomX = dx >= 0 ? W / 2 - inset.right : W / 2 - inset.left;
    const roomY = dy >= 0 ? H / 2 - inset.bottom : H / 2 - inset.top;
    if (Math.abs(dx) > 1e-6) k = Math.min(k, Math.max(20, roomX) / Math.abs(dx));
    if (Math.abs(dy) > 1e-6) k = Math.min(k, Math.max(20, roomY) / Math.abs(dy));
  }
  if (!Number.isFinite(k)) k = 1;
  return { ...c, fov: clampFov(fovForScale(ref.scale * k, W)) };
}

/** Horizontal fov at which a patch of `deg` degrees fills `frac` of the shorter screen side. */
export function fovForPatch(deg: number, W: number, H: number, frac = 0.55) {
  return clampFov((deg * W) / (frac * Math.min(W, H)));
}

// ---------- galactic → equatorial (J2000) ----------
const RA_NGP = 192.85948 * D2R;
const DEC_NGP = 27.12825 * D2R;
const L_NCP = 122.93192 * D2R;

export function galToEq(lDeg: number, bDeg: number) {
  const l = lDeg * D2R, b = bDeg * D2R;
  const sd = Math.sin(b) * Math.sin(DEC_NGP) + Math.cos(b) * Math.cos(DEC_NGP) * Math.cos(L_NCP - l);
  const dec = Math.asin(sd);
  const y = Math.cos(b) * Math.sin(L_NCP - l);
  const x = Math.sin(b) * Math.cos(DEC_NGP) - Math.cos(b) * Math.sin(DEC_NGP) * Math.cos(L_NCP - l);
  const ra = RA_NGP + Math.atan2(y, x);
  return { ra: normRa(ra / D2R), dec: dec / D2R };
}

/** Smooth 0→1 ramp between two fov values on a log scale (1 at `full`, 0 at `none`). */
export function fovRamp(fov: number, full: number, none: number) {
  const t = (Math.log(fov) - Math.log(none)) / (Math.log(full) - Math.log(none));
  const c = Math.max(0, Math.min(1, t));
  return c * c * (3 - 2 * c);
}
