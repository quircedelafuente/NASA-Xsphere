/**
 * UI-side data access. Tries the real static bundle (C4, /bundles/...) first and falls back to the
 * in-memory mock if it is missing. When Giorgi's loaders in web/src/data/ land, replace the bodies
 * here with calls to them — the UI only imports from this file.
 */
import type { BandId, IndexEntry, Manifest, SpectrumJson, TargetMeta, GaiaJson, FlagsJson } from './contracts';
import { mock } from '../mock/mockBundle';
import { searchTargets } from './search';

const BASE = '/bundles';
let useMock: boolean | null = null;

async function getJson<T>(path: string): Promise<T> {
  const r = await fetch(`${BASE}/${path}`);
  if (!r.ok) throw new Error(`${r.status} ${path}`);
  const ct = r.headers.get('content-type') ?? '';
  if (!ct.includes('json')) throw new Error(`not json: ${path}`); // Vite dev server returns index.html for 404s
  return r.json() as Promise<T>;
}

export async function isMock(): Promise<boolean> {
  if (useMock !== null) return useMock;
  try {
    await getJson<IndexEntry[]>('index.json');
    useMock = false;
  } catch {
    useMock = true;
  }
  return useMock;
}

export async function loadIndex(): Promise<IndexEntry[]> {
  return (await isMock()) ? mock.index() : getJson<IndexEntry[]>('index.json');
}

export async function loadMeta(id: string): Promise<TargetMeta> {
  return (await isMock()) ? mock.meta(id) : getJson<TargetMeta>(`${id}/meta.json`);
}

export async function loadManifest(id: string, band: BandId): Promise<Manifest> {
  return (await isMock()) ? mock.manifest(id, band) : getJson<Manifest>(`${id}/${band}/manifest.json`);
}

export async function loadFrames(id: string, band: BandId, m: Manifest): Promise<Float32Array[]> {
  if (await isMock()) return mock.frames(id, band);
  return Promise.all(
    m.frames.map(async (f) => {
      const r = await fetch(`${BASE}/${id}/${band}/${f.f32}`);
      if (!r.ok) throw new Error(`${r.status} ${f.f32}`);
      return new Float32Array(await r.arrayBuffer()); // little-endian on every browser we target
    }),
  );
}

export async function loadSpectrum(id: string): Promise<SpectrumJson | null> {
  try {
    return (await isMock()) ? mock.spectrum(id) : await getJson<SpectrumJson>(`${id}/spectrum.json`);
  } catch {
    return null;
  }
}

export async function loadGaia(id: string): Promise<GaiaJson | null> {
  if (await isMock()) return null;
  try {
    return await getJson<GaiaJson>(`${id}/gaia.json`);
  } catch {
    return null;
  }
}

export async function loadFlags(): Promise<FlagsJson | null> {
  try {
    return await getJson<FlagsJson>('flags.json');
  } catch {
    return null;
  }
}

/** Resolve free text against the target index (ids, names, aliases). Forgiving: see ./search.ts. */
export function matchTarget(q: string, index: IndexEntry[], metas: Record<string, { aliases?: string[] }>): IndexEntry | null {
  return searchTargets(q, index, metas)[0] ?? null;
}

/** Find a processed target near given coordinates (within radius, deg). */
export function nearestTarget(ra: number, dec: number, metas: TargetMeta[], radiusDeg = 0.06): TargetMeta | null {
  let best: TargetMeta | null = null;
  let bestD = Infinity;
  for (const m of metas) {
    const dRa = (((ra - m.ra_deg + 540) % 360) - 180) * Math.cos((dec * Math.PI) / 180);
    const d = Math.hypot(dRa, dec - m.dec_deg);
    if (d < bestD) { bestD = d; best = m; }
  }
  return bestD <= radiusDeg ? best : null;
}
