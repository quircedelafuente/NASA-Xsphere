import type { BandId, ManifestFrame, ViewMode } from '../lib/contracts';
import type { PaletteId } from '../lib/palette';
import { BANDS, MODES } from '../copy';
import { MAX_FPS } from '../lib/url';
import { formatMjdLong } from '../lib/astro';

export function PlayBar(p: {
  playing: boolean; onToggle: () => void; onPrev: () => void; onNext: () => void;
  speed: number; onSpeed: (s: number) => void; zoom: number; onZoom: (z: number) => void; disabled?: boolean;
}) {
  return (
    <div className="playbar" role="group" aria-label="Playback">
      <button className="icon-btn" onClick={p.onPrev} aria-label="Previous visit (←)" title="Previous visit (←)" disabled={p.disabled}>‹</button>
      <button className="icon-btn icon-btn--primary" onClick={p.onToggle} aria-label={p.playing ? 'Pause (Space)' : 'Play (Space)'} title={p.playing ? 'Pause (Space)' : 'Play (Space)'} disabled={p.disabled}>
        {p.playing ? '❚❚' : '▶'}
      </button>
      <button className="icon-btn" onClick={p.onNext} aria-label="Next visit (→)" title="Next visit (→)" disabled={p.disabled}>›</button>
      <label className="slider">
        <span>Speed</span>
        <input type="range" min={0.25} max={MAX_FPS} step={0.25} value={p.speed} onChange={(e) => p.onSpeed(Number(e.target.value))} aria-valuetext={`${p.speed} frames per second`} />
        <span className="mono">{p.speed.toFixed(2)}/s</span>
      </label>
      <label className="slider">
        <span>Zoom</span>
        <input type="range" min={2} max={14} step={1} value={p.zoom} onChange={(e) => p.onZoom(Number(e.target.value))} />
        <span className="mono">×{p.zoom}</span>
      </label>
    </div>
  );
}

export function EpochStrip({ frames, current, excluded, onPick }: { frames: ManifestFrame[]; current: number; excluded: number[]; onPick: (i: number) => void }) {
  return (
    <ol className="epochs" aria-label={`${frames.length} SPHEREx visits`}>
      {frames.map((f, i) => (
        <li key={i}>
          <button
            className={`epoch ${i === current ? 'epoch--on' : ''} ${excluded.includes(i) ? 'epoch--off' : ''}`}
            onClick={() => onPick(i)}
            aria-current={i === current ? 'true' : undefined}
            title={`${formatMjdLong(f.mjd)} · ${f.n_exposures} exposures · ${f.lam_mean_um.toFixed(2)} µm`}
          >
            <span className="epoch__n mono">{i + 1}</span>
            <span className="epoch__label">{f.label}</span>
          </button>
        </li>
      ))}
    </ol>
  );
}

export function BandChips({ available, value, onChange }: { available: BandId[]; value: BandId; onChange: (b: BandId) => void }) {
  return (
    <div className="bands" role="radiogroup" aria-label="Infrared colour (wavelength band)">
      {BANDS.filter((b) => available.includes(b.id)).map((b) => (
        <button
          key={b.id}
          role="radio"
          aria-checked={value === b.id}
          className={`band ${value === b.id ? 'band--on' : ''} ${b.id === 'D56' ? 'band--wide' : ''}`}
          onClick={() => onChange(b.id)}
          title={`${b.range} — ${b.plain}`}
        >
          <span className="band__label">{b.label}</span>
          <span className="band__plain">{b.id === 'D56' ? b.plain : b.range}</span>
        </button>
      ))}
    </div>
  );
}

export function ModeToggle({ value, onChange, disabledDiff }: { value: ViewMode; onChange: (m: ViewMode) => void; disabledDiff?: boolean }) {
  const keys: Record<ViewMode, string> = { blink: 'B', diff: 'D', side: 'S' };
  return (
    <div className="modes" role="radiogroup" aria-label="View mode">
      {(Object.keys(MODES) as ViewMode[]).map((m) => (
        <button
          key={m}
          role="radio"
          aria-checked={value === m}
          className={`mode ${value === m ? 'mode--on' : ''}`}
          onClick={() => onChange(m)}
          disabled={m === 'diff' && disabledDiff}
          aria-label={MODES[m].label}
          title={`${MODES[m].help} (${keys[m]})`}
        >
          {MODES[m].label}
        </button>
      ))}
    </div>
  );
}

export function AdvancedDrawer(p: {
  open: boolean; onToggle: () => void;
  stretchA: number; onStretchA: (a: number) => void;
  vmax: number; vmaxDefault: number; onVmax: (v: number) => void;
  invert: boolean; onInvert: (v: boolean) => void;
  palette?: PaletteId; onPalette?: (p: PaletteId) => void;
  smooth?: boolean; onSmooth?: (v: boolean) => void;
  flags: boolean; onFlags: (v: boolean) => void;
  crosshair: boolean; onCrosshair: (v: boolean) => void;
  track: boolean; onTrack: (v: boolean) => void;
  frames: ManifestFrame[]; excluded: number[]; onExclude: (i: number) => void;
}) {
  return (
    <details className="advanced" open={p.open} onToggle={(e) => { if ((e.target as HTMLDetailsElement).open !== p.open) p.onToggle(); }}>
      <summary>Advanced</summary>
      <div className="advanced__grid">
        <label className="slider">
          <span>Stretch (asinh)</span>
          <input type="range" min={0.01} max={1} step={0.01} value={p.stretchA} onChange={(e) => p.onStretchA(Number(e.target.value))} />
          <span className="mono">{p.stretchA.toFixed(2)}</span>
        </label>
        <label className="slider">
          <span>Brightness limit</span>
          <input type="range" min={p.vmaxDefault * 0.05} max={p.vmaxDefault * 2} step={p.vmaxDefault / 100} value={p.vmax} onChange={(e) => p.onVmax(Number(e.target.value))} />
          <span className="mono">{p.vmax.toFixed(1)}</span>
        </label>
        {p.onPalette && (
          <label className="check" title="The tint follows the wavelength: shorter is bluer, longer is redder. Brightness is unchanged.">
            <input type="checkbox" checked={(p.palette ?? 'infrared') === 'infrared'} onChange={(e) => p.onPalette!(e.target.checked ? 'infrared' : 'grey')} /> Colour by wavelength
          </label>
        )}
        {p.onSmooth && (
          <label className="check" title="Draws a smooth surface through SPHEREx's 6″ pixels. Easier on the eye; it adds no real detail.">
            <input type="checkbox" checked={Boolean(p.smooth)} onChange={(e) => p.onSmooth!(e.target.checked)} /> Smooth pixels (display only)
          </label>
        )}
        <label className="check"><input type="checkbox" checked={p.invert} onChange={(e) => p.onInvert(e.target.checked)} /> Invert (dark stars)</label>
        <label className="check"><input type="checkbox" checked={p.flags} onChange={(e) => p.onFlags(e.target.checked)} /> Show problem pixels</label>
        <label className="check"><input type="checkbox" checked={p.crosshair} onChange={(e) => p.onCrosshair(e.target.checked)} /> Crosshair</label>
        <label className="check"><input type="checkbox" checked={p.track} onChange={(e) => p.onTrack(e.target.checked)} /> Predicted track</label>
        <fieldset className="advanced__epochs">
          <legend>Visits in the loop</legend>
          {p.frames.map((f, i) => (
            <label key={i} className="check">
              <input type="checkbox" checked={!p.excluded.includes(i)} onChange={() => p.onExclude(i)} disabled={!p.excluded.includes(i) && p.frames.length - p.excluded.length <= 1} />
              {f.label}
            </label>
          ))}
        </fieldset>
      </div>
    </details>
  );
}

export function StateCard({ title, body, children, tone = 'info' }: { title: string; body: string; children?: React.ReactNode; tone?: 'info' | 'warn' }) {
  return (
    <div className={`state state--${tone}`} role={tone === 'warn' ? 'alert' : 'status'}>
      <strong>{title}</strong>
      <p>{body}</p>
      {children}
    </div>
  );
}
