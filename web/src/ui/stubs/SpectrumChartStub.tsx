/**
 * STUB of Giorgi's <SpectrumChart> (C6). Plain SVG, no chart library.
 * Two views: spectrum (flux vs wavelength, one epoch) and light curve (flux vs time in a wavelength window).
 */
import { useMemo, useState } from 'react';
import type { MolBand, SpectrumJson } from '../lib/contracts';
import { MOLECULES } from '../copy';
import { formatMjd } from '../lib/astro';
import { lightCurvePoints } from '../lib/lightcurve';

interface Props {
  spectrum: SpectrumJson;
  highlightBands: MolBand[];
  view?: 'spectrum' | 'lightcurve';
  epoch?: number;
}

const W = 560, H = 260, PAD = { l: 52, r: 14, t: 16, b: 38 };

export function SpectrumChartStub({ spectrum, highlightBands, view = 'spectrum', epoch = 0 }: Props) {
  const [hover, setHover] = useState<string | null>(null);
  const pts = useMemo(() => spectrum.points.filter((p) => !p.flagged), [spectrum]);

  if (view === 'lightcurve') {
    const { det, rough, points } = lightCurvePoints(spectrum);
    const byEpoch = new Map<number, { mjd: number; f: number[] }>();
    points.forEach((p) => {
      const e = byEpoch.get(p.epoch) ?? { mjd: p.mjd, f: [] };
      e.f.push(p.flux);
      byEpoch.set(p.epoch, e);
    });
    const series = [...byEpoch.values()].map((e) => ({ mjd: e.mjd, f: e.f.sort((a, b) => a - b)[Math.floor(e.f.length / 2)] })).sort((a, b) => a.mjd - b.mjd);
    if (series.length < 2) return <p className="muted">Only one visit — no light curve yet.</p>;
    const x0 = series[0].mjd, x1 = series[series.length - 1].mjd;
    const y1 = Math.max(...series.map((s) => s.f)) * 1.1;
    const X = (m: number) => PAD.l + ((m - x0) / (x1 - x0 || 1)) * (W - PAD.l - PAD.r);
    const Y = (f: number) => H - PAD.b - (f / y1) * (H - PAD.t - PAD.b);
    return (
      <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img" aria-label="Light curve: brightness over time">
        <Axes yLabel={`Brightness (${spectrum.units})`} xLabel="Date" />
        <polyline fill="none" stroke="var(--accent)" strokeWidth={2} points={series.map((s) => `${X(s.mjd)},${Y(s.f)}`).join(' ')} />
        {series.map((s) => (
          <circle key={s.mjd} cx={X(s.mjd)} cy={Y(s.f)} r={4} fill="var(--accent)">
            <title>{`${formatMjd(s.mjd)}: ${s.f.toFixed(0)}`}</title>
          </circle>
        ))}
        <text x={W - PAD.r} y={PAD.t + 10} className="tick" textAnchor="end">{`${det}${rough ? ' · saturated, rough' : ''}`}</text>
        <text x={PAD.l} y={H - 8} className="tick">{formatMjd(x0)}</text>
        <text x={W - PAD.r} y={H - 8} className="tick" textAnchor="end">{formatMjd(x1)}</text>
      </svg>
    );
  }

  const ep = pts.filter((p) => p.epoch === epoch).sort((a, b) => a.wl_um - b.wl_um);
  const yMax = Math.max(1, ...ep.map((p) => p.flux + p.err)) * 1.08;
  const X = (wl: number) => PAD.l + ((wl - 0.7) / (5.05 - 0.7)) * (W - PAD.l - PAD.r);
  const Y = (f: number) => H - PAD.b - (Math.max(0, f) / yMax) * (H - PAD.t - PAD.b);

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart" role="img" aria-label="Spectrum: brightness at each of SPHEREx’s wavelengths">
      {MOLECULES.filter((m) => highlightBands.includes(m.id as MolBand)).map((m) => (
        <g key={m.id} onMouseEnter={() => setHover(m.id)} onMouseLeave={() => setHover(null)}>
          <rect x={X(m.um[0])} y={PAD.t} width={X(m.um[1]) - X(m.um[0])} height={H - PAD.t - PAD.b} fill="var(--mol)" opacity={hover === m.id ? 0.35 : 0.18} />
          <text x={(X(m.um[0]) + X(m.um[1])) / 2} y={PAD.t + 12} textAnchor="middle" className="mol-label">{m.label}</text>
          <title>{`${m.plain} absorbs light here`}</title>
        </g>
      ))}
      <Axes yLabel={`Brightness (${spectrum.units})`} xLabel="Wavelength (µm)" />
      {[1, 2, 3, 4, 5].map((t) => (
        <text key={t} x={X(t)} y={H - PAD.b + 14} textAnchor="middle" className="tick">{t}</text>
      ))}
      {ep.map((p, i) => (
        <line key={`e${i}`} x1={X(p.wl_um)} x2={X(p.wl_um)} y1={Y(p.flux - p.err)} y2={Y(p.flux + p.err)} stroke="var(--fg-dim)" strokeWidth={1} />
      ))}
      <polyline fill="none" stroke="var(--accent)" strokeWidth={1.6} points={ep.map((p) => `${X(p.wl_um)},${Y(p.flux)}`).join(' ')} />
      {ep.map((p, i) => <circle key={i} cx={X(p.wl_um)} cy={Y(p.flux)} r={1.8} fill="var(--accent)" />)}
    </svg>
  );
}

function Axes({ xLabel, yLabel }: { xLabel: string; yLabel: string }) {
  return (
    <g className="axes">
      <line x1={PAD.l} x2={W - PAD.r} y1={H - PAD.b} y2={H - PAD.b} />
      <line x1={PAD.l} x2={PAD.l} y1={PAD.t} y2={H - PAD.b} />
      <text x={(PAD.l + W - PAD.r) / 2} y={H - 4} textAnchor="middle" className="axis-label">{xLabel}</text>
      <text x={14} y={(PAD.t + H - PAD.b) / 2} textAnchor="middle" className="axis-label" transform={`rotate(-90 14 ${(PAD.t + H - PAD.b) / 2})`}>{yLabel}</text>
    </g>
  );
}
