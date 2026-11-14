import type { SkyRegion } from '../ui/sky-region/geometry';

/** Zone scan report (contracts/report.md, I3), the fields the page shows. */
export interface ScanSource { id: string; class: string; confidence: number; reason: string; ra_deg: number; dec_deg: number; max_sigma: number }
export interface ScanReport { summary: Record<string, number>; summary_text: string; sources: ScanSource[]; visits: number; photos_used: number; photos_available: number; checks: Record<string, string> }
export interface ScanProgress { status: string; progress: number; step?: string }

const API = import.meta.env.VITE_API_URL ?? '';   // dev: Vite proxies /scan to the engine on :8000 (vite.config.ts)

async function json<T>(res: Response): Promise<T> {
  const body = await res.json().catch(() => null);
  if (!res.ok) throw new Error(body?.detail?.message ?? `The engine answered ${res.status}. Is it running (uvicorn engine.api:app)?`);
  return body as T;
}

/** POST /scan, then poll until the report is ready. Region width is the full side of the square (geometry.ts). */
export async function scanRegion(region: SkyRegion, onProgress?: (p: ScanProgress) => void, signal?: AbortSignal): Promise<ScanReport> {
  const side = region.width_deg * 60;
  const { job } = await json<{ job: string }>(await fetch(`${API}/scan`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, signal,
    body: JSON.stringify({ box: { ra_deg: region.ra_deg, dec_deg: region.dec_deg, w_arcmin: side, h_arcmin: side }, band: 'D4' }),
  }));
  for (;;) {
    const j = await json<{ status: string; progress?: number; log?: string[]; message?: string; report?: ScanReport }>(await fetch(`${API}/scan/${job}`, { signal }));
    onProgress?.({ status: j.status, progress: j.progress ?? 0, step: j.log?.at(-1) });
    if (j.status === 'done' && j.report) return j.report;
    if (j.status === 'error') throw new Error(j.message ?? 'The scan failed.');
    await new Promise((r) => setTimeout(r, 1500));
  }
}
