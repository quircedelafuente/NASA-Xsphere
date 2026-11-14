/**
 * Tiny inline-SVG chart for the floating card:
 *  - 'lightcurve': mean 1.1–1.6 µm brightness per visit, current visit highlighted (variable stars)
 *  - 'spectrum'  : brightness vs wavelength for one visit, with H₂O / CH₄ / CO₂ / CO bands shaded (brown dwarfs)
 * Clicking it opens the full SpectrumPanel. Colours: Okabe–Ito sky blue + orange, no red–green.
 */
import { useMemo } from 'react';
import type { SpectrumJson } from '../lib/contracts';
import { MOLECULES } from '../copy';

const W = 300, H = 64, PAD = 4;

export function MiniChart({ spectrum, kind, visit, onOpen, flash }: {
  spectrum: SpectrumJson | null; kind: 'lightcurve' | 'spectrum'; visit: number; onOpen: () => void; flash?: boolean;
}) {
  const data = useMemo(() => {
    if (!spectrum || spectrum.points.length === 0) return null;
    if (kind === 'lightcurve') {
      const by = new Map<number, { mjd: number; sum: number; n: number }>();
      for (const p of spectrum.points) {
        if (p.flagged || p.wl_um < 1.1 || p.wl_um > 1.62) continue;
        const e = by.get(p.epoch) ?? { mjd: p.mjd, sum: 0, n: 0 };
        e.sum += p.flux; e.n += 1;
        by.set(p.epoch, e);
      }
      const pts = [...by.entries()].sort((a, b) => a[0] - b[0]).map(([epoch, e]) => ({ epoch, x: e.mjd, y: e.sum / e.n }));
      return pts.length >= 2 ? pts : null;
    }
    const epochs = [...new Set(spectrum.points.map((p) => p.epoch))].sort((a, b) => a - b);
    const ep = epochs.includes(visit) ? visit : epochs[0];
    const pts = spectrum.points.filter((p) => p.epoch === ep && !p.flagged).sort((a, b) => a.wl_um - b.wl_um).map((p) => ({ epoch: ep, x: p.wl_um, y: p.flux }));
    return pts.length >= 3 ? pts : null;
  }, [spectrum, kind, visit]);

  if (!data) return null;
  const xs = data.map((d) => d.x), ys = data.map((d) => d.y);
  const x0 = kind === 'spectrum' ? 0.75 : Math.min(...xs), x1 = kind === 'spectrum' ? 5.0 : Math.max(...xs);
  const y0 = Math.min(...ys), y1 = Math.max(...ys);
  const sx = (x: number) => PAD + ((x - x0) / Math.max(1e-9, x1 - x0)) * (W - 2 * PAD);
  const sy = (y: number) => H - PAD - ((y - y0) / Math.max(1e-9, y1 - y0)) * (H - 2 * PAD - 10);
  const path = data.map((d, i) => `${i ? 'L' : 'M'}${sx(d.x).toFixed(1)},${sy(d.y).toFixed(1)}`).join(' ');
  const title = kind === 'lightcurve' ? 'Brightness at each visit' : 'Brightness by wavelength';
  const desc = kind === 'lightcurve'
    ? `Light curve over ${data.length} visits. Open for the full chart.`
    : 'Spectrum from 0.75 to 5 micrometres with water and methane bands marked. Open for the full chart.';

  return (
    <button className={`minichart ${flash ? 'is-flash' : ''}`} onClick={onOpen} aria-label={`${title}. ${desc}`}>
      <span className="minichart__head"><span>{title}</span><span className="minichart__open">Open ›</span></span>
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-hidden="true">
        {kind === 'spectrum' && MOLECULES.map((m) => (
          <g key={m.id}>
            <rect x={sx(m.um[0])} y={0} width={Math.max(2, sx(m.um[1]) - sx(m.um[0]))} height={H} fill="rgba(230,159,0,.16)" />
            <text x={sx((m.um[0] + m.um[1]) / 2)} y={9} textAnchor="middle" fontSize="8" fill="rgba(230,159,0,.9)">{m.label}</text>
          </g>
        ))}
        <path d={path} fill="none" stroke="var(--accent)" strokeWidth={kind === 'spectrum' ? 1.4 : 1.8} vectorEffect="non-scaling-stroke" />
        {kind === 'lightcurve' && data.map((d) => (
          <circle key={d.epoch} cx={sx(d.x)} cy={sy(d.y)} r={d.epoch === visit ? 4 : 2.2}
            fill={d.epoch === visit ? 'var(--mark)' : 'var(--accent)'} />
        ))}
      </svg>
    </button>
  );
}
