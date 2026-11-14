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

/** Try to read a free-text box as coordinates. Accepts "269.45 4.74", "269.45, 4.74", "08h55m10.8s -7d14m42s", "08:55:10.8 -07:14:42". */
export function parseCoords(input: string): { ra: number; dec: number } | null {
  const t = input.trim().replace(/,/g, ' ').replace(/\s+/g, ' ');
  // Two decimal numbers
  let m = t.match(/^([+-]?\d+(?:\.\d+)?)\s([+-]?\d+(?:\.\d+)?)$/);
  if (m) {
    const ra = parseRa(m[1]);
    const dec = parseDec(m[2]);
    return ra !== null && dec !== null ? { ra, dec } : null;
  }
  // Sexagesimal with letters or colons: split where the Dec sign starts or after the "s"/third field
  m = t.match(/^(\d{1,2}[h:\s]\d{1,2}[m:\s]\d{1,2}(?:\.\d+)?s?)\s?([+-−]?\d{1,2}[d:\s°]\d{1,2}[m:\s′']\d{1,2}(?:\.\d+)?[s″"]?)$/i);
  if (m) {
    const ra = parseRa(m[1]);
    const dec = parseDec(m[2]);
    return ra !== null && dec !== null ? { ra, dec } : null;
  }
  // Six space-separated numbers
  const parts = t.split(' ');
  if (parts.length === 6) {
    const ra = parseRa(parts.slice(0, 3).join(' '));
    const dec = parseDec(parts.slice(3).join(' '));
    return ra !== null && dec !== null ? { ra, dec } : null;
  }
  return null;
}

export function formatRa(deg: number): string {
  const h = deg / 15;
  const hh = Math.floor(h);
  const mm = Math.floor((h - hh) * 60);
  const ss = ((h - hh) * 60 - mm) * 60;
  return `${String(hh).padStart(2, '0')}h${String(mm).padStart(2, '0')}m${ss.toFixed(1).padStart(4, '0')}s`;
}

export function formatDec(deg: number): string {
  const sign = deg < 0 ? '−' : '+';
  const a = Math.abs(deg);
  const dd = Math.floor(a);
  const mm = Math.floor((a - dd) * 60);
  const ss = ((a - dd) * 60 - mm) * 60;
  return `${sign}${String(dd).padStart(2, '0')}°${String(mm).padStart(2, '0')}′${ss.toFixed(0).padStart(2, '0')}″`;
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
