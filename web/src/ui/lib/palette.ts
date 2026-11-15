/**
 * False colour for the SPHEREx frames. Mirror of processing/palette.py (PNG/GIF previews): keep the two in sync.
 *
 * One band = one colour, picked from its wavelength: shorter wavelengths bluer, longer redder (the "representative
 * colour" convention NASA uses for infrared pictures). The colour only replaces grey: every channel rises with
 * brightness, so brighter pixels stay brighter and all visits in a loop share one table (nothing is faked by the colour).
 * Costs nothing: no extra data, one 256-entry lookup per band, applied while drawing.
 * The Difference view stays grey on purpose: its text and tour describe a dark–bright pair on grey, and in a test the
 * tinted version made plain noise look blotchy.
 */
import type { Manifest } from './contracts';

export type PaletteId = 'infrared' | 'grey';
export const PALETTES: PaletteId[] = ['infrared', 'grey'];
type Rgb = [number, number, number];

/** wavelength (µm) → tint (0..1 per channel), linear in between */
const STOPS: [number, Rgb][] = [
  [0.9, [0.25, 0.45, 1.0]], // blue
  [1.35, [0.1, 0.75, 1.0]], // cyan
  [2.0, [0.15, 1.0, 0.75]], // teal
  [3.1, [1.0, 0.72, 0.15]], // amber
  [4.1, [1.0, 0.45, 0.1]], // orange
  [4.7, [1.0, 0.2, 0.12]], // red
];

export function tint(lamUm: number): Rgb {
  if (!(lamUm > STOPS[0][0])) return STOPS[0][1];
  for (let i = 1; i < STOPS.length; i++) {
    const [l1, c1] = STOPS[i];
    if (lamUm <= l1) {
      const [l0, c0] = STOPS[i - 1];
      const f = (lamUm - l0) / (l1 - l0);
      return [c0[0] + f * (c1[0] - c0[0]), c0[1] + f * (c1[1] - c0[1]), c0[2] + f * (c1[2] - c0[2])];
    }
  }
  return STOPS[STOPS.length - 1][1];
}

/**
 * One wavelength for the whole sequence (never per frame: a tint that changed between visits would look like a real change).
 * Band window centre when the manifest has it, else the mean over the frames.
 */
export function sequenceLambda(m: Manifest): number {
  if (m.lam_range_um) return (m.lam_range_um[0] + m.lam_range_um[1]) / 2;
  const l = m.frames.map((f) => f.lam_mean_um).filter((v) => Number.isFinite(v));
  return l.length ? l.reduce((a, b) => a + b, 0) / l.length : 3.1;
}

const cache = new Map<string, Uint8ClampedArray>();
function cached(key: string, make: (g: number) => Rgb): Uint8ClampedArray {
  let t = cache.get(key);
  if (!t) {
    t = new Uint8ClampedArray(256 * 3);
    for (let i = 0; i < 256; i++) t.set(make(i / 255), i * 3);
    cache.set(key, t);
  }
  return t;
}

/** 256 × RGB table for the frames: black stays black, white stays white, the tint fills the middle. */
export function frameLut(palette: PaletteId, lamUm: number): Uint8ClampedArray {
  if (palette === 'grey') return cached('grey', (g) => [g * 255, g * 255, g * 255]);
  const key = lamUm.toFixed(2);
  return cached(`ir${key}`, (g) => tint(Number(key)).map((t) => 255 * g ** (0.9 + 1.5 * (1 - t))) as Rgb);
}

/**
 * Colour of "problem pixels" (no usable data). Orange on grey and on the blue/green tints; sky blue on the warm tints,
 * where orange would pass for a bright star. Both are from the colour-blind-safe Okabe–Ito set.
 */
export function maskRgb(palette: PaletteId, lamUm: number): Rgb {
  if (palette === 'grey') return [230, 159, 0];
  const t = tint(lamUm);
  return t[0] > t[2] ? [86, 180, 233] : [230, 159, 0];
}
export const maskCss = (palette: PaletteId, lamUm: number) => `rgb(${maskRgb(palette, lamUm).join(',')})`;
