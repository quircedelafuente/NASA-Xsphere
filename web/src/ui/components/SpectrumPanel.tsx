import { useState } from 'react';
import type { MolBand, SpectrumJson } from '../lib/contracts';
import { SpectrumChart } from '../viewer';
import { MOLECULES } from '../copy';
import { formatMjd } from '../lib/astro';

export function SpectrumPanel({ spectrum, defaultView, onClose }: { spectrum: SpectrumJson | null; defaultView: 'spectrum' | 'lightcurve'; onClose: () => void }) {
  const [view, setView] = useState(defaultView);
  const [epoch, setEpoch] = useState(0);
  const [mols, setMols] = useState<MolBand[]>(['H2O', 'CH4', 'CO2', 'CO']);
  const epochs = spectrum ? [...new Map(spectrum.points.map((p) => [p.epoch, p.mjd])).entries()].sort((a, b) => a[0] - b[0]) : [];

  return (
    <section className="spectrum" aria-labelledby="spec-h">
      <div className="spectrum__head">
        <h2 id="spec-h">{view === 'spectrum' ? 'Spectrum' : 'Light curve'}</h2>
        <div className="modes" role="radiogroup" aria-label="Chart type">
          <button role="radio" aria-checked={view === 'spectrum'} className={`mode ${view === 'spectrum' ? 'mode--on' : ''}`} onClick={() => setView('spectrum')}>Spectrum</button>
          <button role="radio" aria-checked={view === 'lightcurve'} className={`mode ${view === 'lightcurve' ? 'mode--on' : ''}`} onClick={() => setView('lightcurve')}>Light curve</button>
        </div>
        <button className="link" onClick={onClose} aria-label="Close spectrum">Close ✕</button>
      </div>
      {!spectrum ? (
        <p className="muted">No spectrum for this target yet.</p>
      ) : (
        <>
          <p className="muted small">
            {view === 'spectrum'
              ? 'Brightness at each of SPHEREx’s wavelengths. Dips in the shaded bands are molecules absorbing light.'
              : 'Brightness over time (1.1–1.6 µm). For variable stars, this is the heartbeat.'}
          </p>
          <SpectrumChart spectrum={spectrum} highlightBands={mols} view={view} epoch={epoch} />
          {view === 'spectrum' && (
            <div className="spectrum__controls">
              {epochs.length > 1 && (
                <label className="select">
                  Visit{' '}
                  <select value={epoch} onChange={(e) => setEpoch(Number(e.target.value))}>
                    {epochs.map(([e, mjd]) => <option key={e} value={e}>{e + 1} · {formatMjd(mjd)}</option>)}
                  </select>
                </label>
              )}
              <div className="mols">
                {MOLECULES.map((m) => (
                  <label key={m.id} className="check">
                    <input type="checkbox" checked={mols.includes(m.id as MolBand)} onChange={(e) => setMols((s) => (e.target.checked ? [...s, m.id as MolBand] : s.filter((x) => x !== m.id)))} />
                    {m.label} <span className="muted">{m.plain}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
          {spectrum.official_tool && <p className="small"><a href={spectrum.official_tool} target="_blank" rel="noreferrer">Science-grade spectra: IRSA SPHEREx spectrophotometry tool ↗</a></p>}
        </>
      )}
    </section>
  );
}
