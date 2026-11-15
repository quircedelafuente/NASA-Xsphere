/**
 * TypeScript mirror of CONTRACTS.md (C1, C3, C4, C6).
 * If Giorgi ships his own types in web/src/data/, re-export those from here instead
 * so the UI keeps a single import point.
 */

// ---------- C1 · targets.json ----------
export type TargetKind = 'mover' | 'variable' | 'companion-mover' | 'custom';

export interface ArchivalPosition {
  survey: string;
  epoch: number;
  ra_deg: number;
  dec_deg: number;
}

export interface Target {
  id: string;
  name: string;
  aliases: string[];
  kind: TargetKind;
  ra_deg: number;
  dec_deg: number;
  ref_epoch: number;
  pmra_masyr?: number;
  pmdec_masyr?: number;
  plx_mas?: number;
  rv_kms?: number;
  astrometry_source?: string;
  default_band: BandId;
  fov_arcsec: number;
  archival_positions?: ArchivalPosition[];
  expected?: {
    motion_px_per_yr?: number;
    variability?: string;
    saturated?: boolean;
    notes?: string;
  };
  bonus?: boolean;
}

// ---------- C3 · flags.json ----------
export interface FlagBit {
  name: string;
  class: 'hard' | 'soft';
  plain: string;
}
export interface FlagsJson {
  hard_mask_bits: number[];
  soft_bits: number[];
  bits: Record<string, FlagBit>;
}

// ---------- C4 · bundle ----------
export type BandId =
  | 'D1' | 'D2' | 'D3' | 'D4' | 'D5' | 'D6'
  | 'D56' | 'ALL' | 'mol-ch4' | 'mol-h2o' | 'mol-co2';

export interface IndexEntry {
  id: string;
  name: string;
  kind: TargetKind;
  bands: BandId[];
  n_epochs: number;
  thumb?: string;
}

export interface Wcs {
  ctype: [string, string];
  crval: [number, number];
  crpix: [number, number];
  cdelt: [number, number];
}

export interface ManifestFrame {
  epoch: number;
  label: string;
  mjd: number;
  n_exposures: number;
  lam_mean_um: number;
  f32: string;
  png?: string;
  mask_png?: string;
  target_px?: [number, number];
  flags_at_target?: string[];
}

export interface Manifest {
  target_id: string;
  band: BandId;
  /** Band window (C4). Its centre picks the false-colour tint. */
  lam_range_um?: [number, number];
  /** Grid size. Not in the C4 example; optional, default 64×64 (D7). */
  nx?: number;
  ny?: number;
  wcs: Wcs;
  units: string;
  stretch: { method: 'asinh' | 'linear'; a: number; vmin: number; vmax: number; scope: string };
  frames: ManifestFrame[];
  diffs?: { from: number; to: number; f32: string; units: string }[];
  target_track?: { mjd: number; x: number; y: number }[];
  warnings?: string[];
}

export interface EpochSummary {
  id: number;
  label: string;
  mjd_start: number;
  mjd_end: number;
  release?: string;
  n?: number;
}

export interface TargetMeta extends Target {
  epochs: EpochSummary[];
  release?: string | string[];
  generated_utc?: string;
}

export interface SpectrumPoint {
  wl_um: number;
  bw_um: number;
  flux: number;
  err: number;
  mjd: number;
  epoch: number;
  det: string;
  flagged: boolean;
}
export interface SpectrumJson {
  target_id: string;
  aperture_px: number;
  units: string;
  points: SpectrumPoint[];
  official_tool?: string;
}

export interface GaiaJson {
  ref_epoch: number;
  sources: { ra_deg: number; dec_deg: number; pmra_masyr: number; pmdec_masyr: number; plx_mas: number; gmag: number }[];
  /** AllWISE sources in the same field, at the positions WISE measured (~2010.5, proper motion 0). */
  wise?: { ra_deg: number; dec_deg: number; pmra_masyr: number; pmdec_masyr: number; w2mag: number }[];
  ref_epoch_wise?: number;
}

// ---------- C6 · viewer component API ----------
export type ViewMode = 'blink' | 'diff' | 'side';

export interface BlinkCanvasProps {
  manifest: Manifest;
  /** Loaded float32 frames, same order as manifest.frames. Optional extension: Giorgi's version may load these itself. */
  frames?: Float32Array[];
  mode: ViewMode;
  frameIndex: number;
  playing: boolean;
  fps: number;
  stretch: { a: number; vmin: number; vmax: number };
  zoom: number;
  overlays: { crosshair: boolean; track: boolean; gaia: GaiaJson | null; flags: boolean; wise?: GaiaJson | null };
  onPixelClick?: (ra: number, dec: number, x: number, y: number) => void;
  /** Optional extension: lets the UI keep its epoch strip in sync while the canvas auto-plays. */
  onFrameChange?: (i: number) => void;
  /** Optional extension: invert greyscale. */
  invert?: boolean;
  /** Optional extension: false colour by wavelength ('infrared', default) or the plain 'grey' frames. See ui/lib/palette.ts. */
  palette?: 'infrared' | 'grey';
  /** Optional extension: smooth the display instead of square pixels (off by default, D7). See ui/lib/smooth.ts. */
  smooth?: boolean;
  /** Optional extension: epochs the user switched off in Advanced. */
  excludeEpochs?: number[];
}

export type MolBand = 'H2O' | 'CH4' | 'CO2' | 'CO';
