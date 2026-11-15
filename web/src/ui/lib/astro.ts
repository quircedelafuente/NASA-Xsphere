/** Small, dependency-free astronomy helpers for the UI (parsing input, formatting, pixel↔sky). */
import type { Wcs } from './contracts';

const D2R = Math.PI / 180;

/** Parse "08h55m10.831s", "08:55:10.8", "08 55 10.8" (hours) or a decimal number (degrees). */
export function parseRa(s: string): number | null {
  const t = s.trim();
  if (/^[+-]?\d+(\.\d+)?$/.test(t)) {
    const v = Number(t);
    return v >= 0 && v < 360 ? v : null;
  }
  const m = t.match(/^(\d{1,2})[h:\s]+(\d{1,2})[m:\s]+(\d{1,2}(?:\.\d+)?)s?$/i);
  if (!m) return null;
  const v = (Number(m[1]) + Number(m[2]) / 60 + Number(m[3]) / 3600) * 15;
  return v >= 0 && v < 360 ? v : null;
}

/** Parse "-7d14m42.53s", "-07:14:42.5", "-7 14 42.5", "+66°45′18″" or a decimal number. */
export function parseDec(s: string): number | null {
  const t = s.trim().replace(/[°′″'"]/g, ' ').trim();
  if (/^[+-]?\d+(\.\d+)?$/.test(t)) {
    const v = Number(t);
    return v >= -90 && v <= 90 ? v : null;
  }
  const m = t.match(/^([+-−]?)(\d{1,2})[d:\s]+(\d{1,2})[m:\s]+(\d{1,2}(?:\.\d+)?)s?$/i);
  if (!m) return null;
  const sign = m[1] === '-' || m[1] === '−' ? -1 : 1;
  const v = sign * (Number(m[2]) + Number(m[3]) / 60 + Number(m[4]) / 3600);
  return v >= -90 && v <= 90 ? v : null;
}

/**
 * Try to read a free-text box as coordinates. Forgiving about how they are typed:
 *   decimal degrees      "269.45 4.74"  "269.45,+4.74"  "269.45° −4.74°"  "269.45 deg, 4.74 deg"  "(269.45; 4.74)"
 *   with labels          "RA 269.45 Dec 4.74"  "ra=269.45, dec=-4.74"
 *   hours / degrees      "17 57 48.5 +04 41 36"  "17:57:48.5 +04:41:36"  "17h57m48.5s +04d41m36s"  "17h57m48.5s +04°41′36″"
 *   shorter              "17h57m +04d41m"  "17:57 +04:41"  "17h57m48.5s 4.74"
 *   catalogue style      "J175748.5+044136"
 * Any minus sign works (-, −, –). Anything with other letters in it is a name, not coordinates.
 * Mirror of parse_coords in backend/engine/resolve.py: keep the two in sync.
 */
export function parseCoords(input: string): { ra: number; dec: number } | null {
  let t = input.trim().toLowerCase().replace(/[−–—]/g, '-');
  if (!t) return null;
  // J175748.5+044136 → 17 57 48.5 +04 41 36
  const j = t.replace(/\s+/g, '').match(/^j(\d{2})(\d{2})(\d{2}(?:\.\d+)?)([+-])(\d{2})(\d{2})(\d{2}(?:\.\d+)?)$/);
  if (j) t = `${j[1]} ${j[2]} ${j[3]} ${j[4]}${j[5]} ${j[6]} ${j[7]}`;
  t = t
    .replace(/(?:right ascension|declination|\b(?:ra|decl?)\b|[αδ])\s*[:=]?/g, ' ')
    .replace(/degrees?|deg|º/g, '°')
    .replace(/[()[\]=]/g, ' ');
  // numbers with an optional sign and unit; nothing else may be left over
  const tokens: { neg: boolean; signed: boolean; v: number; int: boolean; unit: string }[] = [];
  const rest = t.replace(/([+-]?)\s*(\d+(?:\.\d*)?|\.\d+)\s*([hd°m′'s″":]?)/g, (_, sg: string, num: string, unit: string) => {
    tokens.push({ neg: sg === '-', signed: sg !== '', v: Number(num), int: /^\d+$/.test(num), unit });
    return ' ';
  });
  if (/[^\s,;/]/.test(rest) || tokens.length < 2 || tokens.length > 6) return null;
  // where does the declination start? at a sign, at a degree mark, after the seconds of RA, or half-way
  let k = tokens.findIndex((x, i) => i > 0 && x.signed);
  if (k < 0) k = tokens.findIndex((x, i) => i > 0 && (x.unit === 'd' || x.unit === '°'));
  if (k < 0) { const s = tokens.findIndex((x) => x.unit === 's' || x.unit === '″' || x.unit === '"'); if (s >= 0 && s < tokens.length - 1) k = s + 1; }
  if (k < 0 && tokens.length % 2 === 0) k = tokens.length / 2;
  if (k < 1) return null;
  const UNITS = [['', 'h', 'd', '°', ':'], ['', 'm', '′', "'", ':'], ['', 's', '″', '"']];
  const group = (g: typeof tokens, isRa: boolean): number | null => {
    if (g.length < 1 || g.length > 3) return null;
    if (g.some((x, i) => (i > 0 && (x.signed || x.v >= 60)) || (i < g.length - 1 && !x.int) || !UNITS[i].includes(x.unit))) return null;
    const u = g[0].unit;
    if (g.length === 1 && u === ':') return null;
    if (isRa ? g[0].neg : u === 'h') return null;
    const v = g[0].v + (g[1]?.v ?? 0) / 60 + (g[2]?.v ?? 0) / 3600;
    if (!isRa) return v <= 90 ? (g[0].neg ? -v : v) : null;
    const hours = u === 'h' || (g.length > 1 && u !== 'd' && u !== '°'); // "17 57 48" is hours, "269.45" is degrees
    const deg = hours ? v * 15 : v;
    return deg < 360 ? deg : null;
  };
  const ra = group(tokens.slice(0, k), true);
  const dec = group(tokens.slice(k), false);
  return ra !== null && dec !== null ? { ra, dec } : null;
}

export function formatRa(deg: number): string {
  const t = Math.round((deg / 15) * 36000); // tenths of a second, rounded first so 59.96 s never prints as "60.0s"
  const hh = Math.floor(t / 36000) % 24;
  const mm = Math.floor((t % 36000) / 600);
  const ss = (t % 600) / 10;
  return `${String(hh).padStart(2, '0')}h${String(mm).padStart(2, '0')}m${ss.toFixed(1).padStart(4, '0')}s`;
}

export function formatDec(deg: number): string {
  const sign = deg < 0 ? '−' : '+';
  const t = Math.round(Math.abs(deg) * 3600); // whole arcseconds, rounded first
  const dd = Math.floor(t / 3600);
  const mm = Math.floor((t % 3600) / 60);
  const ss = t % 60;
  return `${sign}${String(dd).padStart(2, '0')}°${String(mm).padStart(2, '0')}′${String(ss).padStart(2, '0')}″`;
}

/**
 * Pixel (top-left origin, as in the .f32 files) → sky, gnomonic (TAN) projection.
 * crpix is FITS 1-based with bottom-left origin, so we convert: fitsY = ny - y.
 */
export function pixelToSky(wcs: Wcs, x: number, y: number, ny: number): { ra: number; dec: number } {
  const fx = x + 1; // 0-based → 1-based
  const fy = ny - y; // top-left → bottom-left, 1-based
  const xi = (fx - wcs.crpix[0]) * wcs.cdelt[0] * D2R;
  const eta = (fy - wcs.crpix[1]) * wcs.cdelt[1] * D2R;
  const ra0 = wcs.crval[0] * D2R;
  const dec0 = wcs.crval[1] * D2R;
  const denom = Math.cos(dec0) - eta * Math.sin(dec0);
  const ra = ra0 + Math.atan2(xi, denom);
  const dec = Math.atan2(Math.sin(dec0) + eta * Math.cos(dec0), Math.sqrt(xi * xi + denom * denom));
  return { ra: ((ra / D2R) % 360 + 360) % 360, dec: dec / D2R };
}

/** MJD → "Aug 2025" style. */
export function mjdToDate(mjd: number): Date {
  return new Date((mjd - 40587) * 86400000);
}
export function formatMjd(mjd: number): string {
  return mjdToDate(mjd).toLocaleDateString('en-GB', { month: 'short', year: 'numeric' });
}
export function formatMjdLong(mjd: number): string {
  return mjdToDate(mjd).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

/** Compass direction for a (dx east, dy north) vector. */
export function compass(dEast: number, dNorth: number): string {
  const ang = (Math.atan2(dEast, dNorth) / D2R + 360) % 360; // 0 = north, 90 = east
  const names = ['north', 'north-east', 'east', 'south-east', 'south', 'south-west', 'west', 'north-west'];
  return names[Math.round(ang / 45) % 8];
}

/** Angular motion in arcsec between two MJDs from proper motion (mas/yr). */
export function pmShiftArcsec(pmra_masyr: number, pmdec_masyr: number, mjdA: number, mjdB: number) {
  const yrs = (mjdB - mjdA) / 365.25;
  return { dEast: (pmra_masyr * yrs) / 1000, dNorth: (pmdec_masyr * yrs) / 1000 };
}
