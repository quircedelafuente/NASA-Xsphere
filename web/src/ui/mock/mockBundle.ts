/**
 * In-memory MOCK of the C1 + C4 contracts, so the UI works before Data/Processing ship real files.
 * Used only when /bundles/index.json is missing. Numbers are ILLUSTRATIVE (rough literature values),
 * not science — the real values come from data/targets.json and the bundles.
 * Lives in web/src/ui/ so it never collides with Processing's web/public/bundles/ (D16).
 */
import type { BandId, IndexEntry, Manifest, SpectrumJson, TargetMeta } from '../lib/contracts';

const N = 64;
const PX_ARCSEC = 6.15;

interface MockTarget {
  meta: Omit<TargetMeta, 'epochs'>;
  epochMjds: number[];
  bands: BandId[];
  /** brightness multiplier per epoch (variables) */
  amp?: (i: number, mjd: number) => number;
  peak: number;
  /** visible only at long wavelengths */
  coldOnly?: boolean;
}

const months = (start: number, n: number) => Array.from({ length: n }, (_, i) => start + i * 30.4);

const MOCK: MockTarget[] = [
  {
    meta: {
      id: 'barnards-star', name: "Barnard's Star", aliases: ["Barnard's Star", 'Barnard', 'GJ 699', 'HIP 87937'],
      kind: 'mover', ra_deg: 269.4486, dec_deg: 4.7398, ref_epoch: 2016.0, pmra_masyr: -801.55, pmdec_masyr: 10362.39,
      plx_mas: 546.98, astrometry_source: 'Gaia DR3', default_band: 'D6', fov_arcsec: 394,
      archival_positions: [
        { survey: '2MASS', epoch: 1999.4, ra_deg: 269.452, dec_deg: 4.668 },
        { survey: 'AllWISE', epoch: 2010.5, ra_deg: 269.4507, dec_deg: 4.6996 },
      ],
      expected: { motion_px_per_yr: 1.69, variability: 'none', saturated: true, notes: 'Bright: core saturated.' },
    },
    epochMjds: [60920.1, 61105.4, 61290.2], bands: ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D56'], peak: 60,
  },
  {
    meta: {
      id: 'eps-indi-b', name: 'ε Indi B', aliases: ['eps Indi B', 'Epsilon Indi B', 'ε Indi Ba', 'eps Ind B', 'Epsilon Indi'],
      kind: 'companion-mover', ra_deg: 330.876, dec_deg: -56.797, ref_epoch: 2016.0, pmra_masyr: 3982, pmdec_masyr: -2470,
      plx_mas: 270.6, astrometry_source: 'Gaia DR3', default_band: 'D56', fov_arcsec: 394,
      expected: { motion_px_per_yr: 0.76, variability: 'none', saturated: false },
    },
    epochMjds: [60840.3, 61020.8, 61205.5, 61388.1], bands: ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D56'], peak: 6,
  },
  {
    meta: {
      id: 'wise-0855', name: 'WISE 0855−0714', aliases: ['WISE 0855', 'WISE J085510.83-071442.5', 'WISE 0855-0714', 'W0855'],
      kind: 'mover', ra_deg: 133.79513, dec_deg: -7.24515, ref_epoch: 2010.5, pmra_masyr: -8118, pmdec_masyr: 680,
      plx_mas: 439, astrometry_source: 'AllWISE + literature pm', default_band: 'D56', fov_arcsec: 394,
      expected: { motion_px_per_yr: 1.32, variability: 'none', saturated: false, notes: 'Only visible at 3.8–5 µm after co-adding.' },
    },
    epochMjds: [60975.6, 61160.2, 61342.9], bands: ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D56'], peak: 2.2, coldOnly: true,
  },
  {
    meta: {
      id: 'rw-aurigae', name: 'RW Aurigae', aliases: ['RW Aur', 'RW Aurigae', 'HD 240764'],
      kind: 'variable', ra_deg: 76.9563, dec_deg: 30.4011, ref_epoch: 2016.0, pmra_masyr: 3.6, pmdec_masyr: -24.5,
      astrometry_source: 'Gaia DR3', default_band: 'D2', fov_arcsec: 394,
      expected: { variability: 'irregular dimming', saturated: true },
    },
    epochMjds: [60950.3, 61133.7, 61318.4], bands: ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D56'], peak: 40,
    amp: (i) => [1, 0.45, 0.8][i] ?? 1,
  },
  {
    meta: {
      id: 'r-draconis', name: 'R Draconis', aliases: ['R Dra', 'R Draconis', 'HD 148206'],
      kind: 'variable', ra_deg: 248.1645, dec_deg: 66.7531, ref_epoch: 2016.0, pmra_masyr: -11.5, pmdec_masyr: 38.0,
      astrometry_source: 'Gaia DR3', default_band: 'D2', fov_arcsec: 394,
      expected: { variability: 'Mira, ~245 d', saturated: true },
    },
    epochMjds: months(60830, 14), bands: ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D56'], peak: 30,
    amp: (_i, mjd) => 0.55 + 0.45 * Math.sin(((mjd - 60830) / 245) * 2 * Math.PI),
  },
];

const BAND_LAM: Record<string, number> = { D1: 0.92, D2: 1.36, D3: 2.02, D4: 3.12, D5: 4.12, D6: 4.71, D56: 4.4, ALL: 2.5 };

function rng(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}
function gauss(r: () => number) {
  return Math.sqrt(-2 * Math.log(r() + 1e-12)) * Math.cos(2 * Math.PI * r());
}
function hash(s: string) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
}

function mjdLabel(mjd: number) {
  return new Date((mjd - 40587) * 86400000).toLocaleDateString('en-GB', { month: 'short', year: 'numeric' });
}

function trackFor(t: MockTarget) {
  const m0 = t.epochMjds[0];
  const c = N / 2 - 0.5;
  return t.epochMjds.map((mjd) => {
    const yrs = (mjd - m0) / 365.25;
    const dE = ((t.meta.pmra_masyr ?? 0) * yrs) / 1000 / PX_ARCSEC;
    const dN = ((t.meta.pmdec_masyr ?? 0) * yrs) / 1000 / PX_ARCSEC;
    // east is left on the sky (RA increases to the left with north up); north is up (y decreases)
    return { mjd, x: c - dE, y: c - dN };
  });
}

function renderFrame(t: MockTarget, band: BandId, i: number): Float32Array {
  const img = new Float32Array(N * N);
  const fieldR = rng(hash(t.meta.id)); // same background stars every epoch
  const noiseR = rng(hash(`${t.meta.id}/${band}/${i}`));
  const lam = BAND_LAM[band] ?? 2;
  const stars: [number, number, number][] = [];
  for (let k = 0; k < 28; k++) stars.push([fieldR() * N, fieldR() * N, 0.4 + 6 * fieldR() ** 3]);
  const tr = trackFor(t)[i];
  const amp = t.amp ? t.amp(i, t.epochMjds[i]) : 1;
  const coldFactor = t.coldOnly ? (lam > 3.7 ? 1 : 0.02) : 1;
  const tgt: [number, number, number] = [tr.x, tr.y, t.peak * amp * coldFactor];
  const sigma = 0.9 + lam * 0.12; // PSF grows with wavelength
  const all = [...stars.map(([x, y, f]) => [x, y, f / (0.6 + lam * 0.25)] as [number, number, number]), tgt];
  const noise = band === 'D56' ? 0.06 : 0.12;
  for (let y = 0; y < N; y++) {
    for (let x = 0; x < N; x++) {
      let v = 0.05 + noise * gauss(noiseR);
      for (const [sx, sy, f] of all) {
        const dx = x - sx, dy = y - sy;
        const d2 = dx * dx + dy * dy;
        if (d2 < 49) v += f * Math.exp(-d2 / (2 * sigma * sigma));
      }
      img[y * N + x] = v;
    }
  }
  // saturation: NaN core for very bright targets
  if (t.meta.expected?.saturated && tgt[2] > 20 && lam < 4.5) {
    for (let y = -1; y <= 1; y++) for (let x = -1; x <= 1; x++) {
      const px = Math.round(tgt[0]) + x, py = Math.round(tgt[1]) + y;
      if (px >= 0 && px < N && py >= 0 && py < N) img[py * N + px] = NaN;
    }
  }
  return img;
}

function get(id: string) {
  const t = MOCK.find((m) => m.meta.id === id);
  if (!t) throw new Error(`no mock target ${id}`);
  return t;
}

export const mock = {
  index(): IndexEntry[] {
    return MOCK.map((t) => ({ id: t.meta.id, name: t.meta.name, kind: t.meta.kind, bands: t.bands, n_epochs: t.epochMjds.length }));
  },
  meta(id: string): TargetMeta {
    const t = get(id);
    return {
      ...t.meta,
      epochs: t.epochMjds.map((mjd, i) => ({ id: i, label: mjdLabel(mjd), mjd_start: mjd - 10, mjd_end: mjd + 10, release: 'mock' })),
      release: 'MOCK — illustrative only',
      generated_utc: new Date().toISOString(),
    };
  },
  manifest(id: string, band: BandId): Manifest {
    const t = get(id);
    const track = trackFor(t);
    const lam = BAND_LAM[band] ?? 2;
    const sat = t.meta.expected?.saturated && t.peak > 20 && lam < 4.5;
    return {
      target_id: id,
      band,
      nx: N,
      ny: N,
      wcs: { ctype: ['RA---TAN', 'DEC--TAN'], crval: [t.meta.ra_deg, t.meta.dec_deg], crpix: [32.5, 32.5], cdelt: [-PX_ARCSEC / 3600, PX_ARCSEC / 3600] },
      units: 'MJy/sr (mock)',
      stretch: { method: 'asinh', a: 0.1, vmin: -0.1, vmax: Math.max(3, t.peak * 0.6), scope: 'sequence' },
      frames: t.epochMjds.map((mjd, i) => ({
        epoch: i, label: mjdLabel(mjd), mjd, n_exposures: 18 + (i % 4), lam_mean_um: lam,
        f32: `e${i}.f32`, target_px: [track[i].x, track[i].y], flags_at_target: sat ? ['OVERFLOW', 'SOURCE'] : [],
      })),
      target_track: track,
      warnings: sat ? ['saturated core'] : [],
    };
  },
  frames(id: string, band: BandId): Float32Array[] {
    const t = get(id);
    return t.epochMjds.map((_, i) => renderFrame(t, band, i));
  },
  spectrum(id: string): SpectrumJson {
    const t = get(id);
    const r = rng(hash(`${id}/spec`));
    const points = [] as SpectrumJson['points'];
    t.epochMjds.forEach((mjd, e) => {
      const amp = t.amp ? t.amp(e, mjd) : 1;
      for (let k = 0; k < 102; k++) {
        const wl = 0.75 + (k / 101) * 4.25;
        let f: number;
        if (t.coldOnly) {
          // Y-dwarf-like: almost nothing blueward, peak ~4.5 µm, CH4 dip ~3.3, H2O dip ~2.8
          f = 40 * Math.exp(-((wl - 4.5) ** 2) / 0.25) + 2;
          f *= 1 - 0.7 * Math.exp(-((wl - 3.3) ** 2) / 0.02) - 0.4 * Math.exp(-((wl - 2.8) ** 2) / 0.02);
        } else {
          f = 1500 * Math.exp(-((wl - 1.3) ** 2) / 1.2) + 120;
          f *= 1 - 0.25 * Math.exp(-((wl - 2.8) ** 2) / 0.04) - 0.15 * Math.exp(-((wl - 4.6) ** 2) / 0.03);
        }
        f *= amp;
        points.push({ wl_um: wl, bw_um: wl / 40, flux: f * (1 + 0.04 * gauss(r)), err: f * 0.05, mjd, epoch: e, det: `D${Math.min(6, 1 + Math.floor((wl - 0.75) / 0.71))}`, flagged: false });
      }
    });
    return { target_id: id, aperture_px: 2, units: 'uJy (mock)', points, official_tool: 'https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html' };
  },
};
