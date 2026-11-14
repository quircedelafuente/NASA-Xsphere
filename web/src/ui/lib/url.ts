/**
 * C5 · URL scheme (owner: Product). Single source of truth for parsing and writing view state.
 *
 *   /                                   landing
 *   /?target=barnards-star              named target
 *   /?ra=133.795&dec=-7.245&fov=394     arbitrary coordinates (live mode)
 *     &band=D56&mode=blink|diff|side&speed=1.0&frame=0&stretch=asinh:0.1&overlay=gaia,flags
 *     &zoom=8&tour=1&palette=grey       (UI-only extras, optional; palette: frames are false colour unless 'grey')
 *     &view=269.4486,4.7398,0.32         (UI-only: sky-map centre RA,Dec and horizontal field in deg)
 *   /embed?...                          same params, minimal chrome
 */
import type { BandId, ViewMode } from './contracts';
import { PALETTES, type PaletteId } from './palette';

export const MAX_FPS = 2; // WCAG 2.3.1 — never more than 3 flashes/s; we cap at 2

export type Overlay = 'gaia' | 'flags' | 'track' | 'crosshair';

export interface ViewState {
  embed: boolean;
  target?: string;
  ra?: number;
  dec?: number;
  fov?: number;
  band?: BandId;
  mode: ViewMode;
  speed: number;
  frame: number;
  stretchA?: number;
  overlays: Overlay[];
  zoom?: number;
  tour?: boolean;
  /** False colour by wavelength (default, omitted from the URL) or 'grey'. */
  palette?: PaletteId;
  /** Sky-map camera (UI extra): centre RA/Dec and horizontal field of view, all in degrees. */
  view?: MapView;
}

export interface MapView { ra: number; dec: number; fov: number }

function parseView(v: string | null): MapView | undefined {
  if (!v) return undefined;
  const [ra, dec, fov] = v.split(',').map((x) => Number(x));
  if (![ra, dec, fov].every(Number.isFinite)) return undefined;
  if (dec < -90 || dec > 90 || fov <= 0) return undefined;
  return { ra: ((ra % 360) + 360) % 360, dec, fov };
}

const BANDS: BandId[] = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D56', 'ALL', 'mol-ch4', 'mol-h2o', 'mol-co2'];
const MODES: ViewMode[] = ['blink', 'diff', 'side'];
const OVERLAYS: Overlay[] = ['gaia', 'flags', 'track', 'crosshair'];
export const DEFAULT_OVERLAYS: Overlay[] = ['crosshair', 'track', 'flags'];

function num(v: string | null): number | undefined {
  if (v === null || v.trim() === '') return undefined;
  const n = Number(v);
  return Number.isFinite(n) ? n : undefined;
}

export function parseUrl(loc: { pathname: string; search: string }): ViewState {
  const p = new URLSearchParams(loc.search);
  const band = p.get('band') as BandId | null;
  const mode = p.get('mode') as ViewMode | null;
  const stretch = p.get('stretch'); // "asinh:0.1"
  const overlayParam = p.get('overlay');
  const overlays = overlayParam === null
    ? DEFAULT_OVERLAYS
    : (overlayParam.split(',').filter((o) => OVERLAYS.includes(o as Overlay)) as Overlay[]);
  const speed = num(p.get('speed')) ?? 1;
  return {
    embed: loc.pathname.replace(/\/+$/, '').endsWith('/embed'),
    target: p.get('target') ?? undefined,
    ra: num(p.get('ra')),
    dec: num(p.get('dec')),
    fov: num(p.get('fov')),
    band: band && BANDS.includes(band) ? band : undefined,
    mode: mode && MODES.includes(mode) ? mode : 'blink',
    speed: Math.min(MAX_FPS, Math.max(0.25, speed)),
    frame: Math.max(0, Math.floor(num(p.get('frame')) ?? 0)),
    stretchA: stretch ? num(stretch.split(':')[1] ?? null) : undefined,
    overlays,
    zoom: num(p.get('zoom')),
    tour: p.get('tour') === '1',
    palette: PALETTES.find((x) => x === p.get('palette')),
    view: parseView(p.get('view')),
  };
}

export function buildSearch(s: Partial<ViewState>): string {
  const p = new URLSearchParams();
  if (s.target) p.set('target', s.target);
  else if (s.ra !== undefined && s.dec !== undefined) {
    p.set('ra', s.ra.toFixed(5));
    p.set('dec', s.dec.toFixed(5));
  }
  if (s.fov) p.set('fov', String(Math.round(s.fov)));
  if (s.band) p.set('band', s.band);
  if (s.mode && s.mode !== 'blink') p.set('mode', s.mode);
  if (s.speed !== undefined && s.speed !== 1) p.set('speed', String(s.speed));
  if (s.frame) p.set('frame', String(s.frame));
  if (s.stretchA !== undefined) p.set('stretch', `asinh:${s.stretchA}`);
  if (s.overlays && s.overlays.join(',') !== DEFAULT_OVERLAYS.join(',')) p.set('overlay', s.overlays.join(','));
  if (s.zoom !== undefined) p.set('zoom', String(s.zoom));
  if (s.tour) p.set('tour', '1');
  if (s.palette && s.palette !== 'infrared') p.set('palette', s.palette);
  if (s.view) p.set('view', `${s.view.ra.toFixed(4)},${s.view.dec.toFixed(4)},${Number(s.view.fov.toPrecision(3))}`);
  const q = p.toString().replace(/%2C/gi, ','); // commas are safe in a query string and easier to read
  return q ? `?${q}` : '';
}

export function viewUrl(s: Partial<ViewState>, opts: { embed?: boolean; absolute?: boolean } = {}): string {
  const path = opts.embed ? '/embed' : '/';
  const rel = path + buildSearch(s);
  return opts.absolute ? `${window.location.origin}${rel}` : rel;
}
