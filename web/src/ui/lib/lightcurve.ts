import type { SpectrumJson, SpectrumPoint } from './contracts';

/** Light-curve points: the detector with the most clean visits. A fixed 1.1–1.6 µm window found nothing (the reports
 *  cover D4–D6). Saturated stars (R Dra) have only flagged points, so those are used and marked `rough`. */
export function lightCurvePoints(spectrum: SpectrumJson): { det: string | undefined; rough: boolean; points: SpectrumPoint[] } {
  const mostVisits = (ps: SpectrumPoint[]) => {
    const n = new Map<string, Set<number>>();
    ps.forEach((p) => n.set(p.det, (n.get(p.det) ?? new Set<number>()).add(p.epoch)));
    return [...n.entries()].sort((a, b) => b[1].size - a[1].size)[0];
  };
  const clean = spectrum.points.filter((p) => !p.flagged);
  const best = mostVisits(clean);
  const rough = !best || best[1].size < 2;
  const det = rough ? mostVisits(spectrum.points)?.[0] : best[0];
  return { det, rough, points: (rough ? spectrum.points : clean).filter((p) => p.det === det) };
}
