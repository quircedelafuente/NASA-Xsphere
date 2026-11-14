import { useEffect } from 'react';
import type { ViewMode, BandId, TargetKind } from '../lib/contracts';
import { TARGET_COPY } from '../copy';

/** Demo / recording mode: seconds each tour step stays on screen before advancing by itself. */
export const DEMO_STEP_MS = 4000;

/** Guided tour: 3 cards per target (what it is → what to look for → did you see it?). The tour IS the demo script. */
export function TourCard(p: {
  targetId: string; kind: TargetKind; step: number; onStep: (s: number) => void;
  order: string[]; onTarget: (id: string) => void; onClose: () => void;
  onSuggest: (s: { mode?: ViewMode; band?: BandId; spectrum?: boolean }) => void;
  /** Called after the last step of the last object (defaults to onClose). */
  onFinish?: () => void;
  /** Demo mode: advance automatically every DEMO_STEP_MS while not paused. */
  auto?: boolean;
  paused?: boolean;
}) {
  const copy = TARGET_COPY[p.targetId];
  const pos = p.order.indexOf(p.targetId);
  const next = p.order[pos + 1];
  const suggestion = suggestionFor(p.targetId, p.kind, p.step);
  const finish = p.onFinish ?? p.onClose;

  const advance = () => {
    if (p.step < 2) { p.onStep(p.step + 1); if (suggestion) p.onSuggest(suggestion.action); }
    else if (next) p.onTarget(next);
    else finish();
  };

  useEffect(() => {
    if (!p.auto || p.paused) return;
    const id = window.setTimeout(advance, DEMO_STEP_MS);
    return () => window.clearTimeout(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [p.auto, p.paused, p.step, p.targetId]);

  if (!copy) return null;

  return (
    <section className="tour" aria-live="polite" aria-label="Guided tour">
      <div className="tour__head">
        <span className="tour__progress" aria-label={`Object ${pos + 1} of ${p.order.length}, step ${p.step + 1} of 3`}>
          {p.order.map((id, i) => <span key={id} className={i < pos ? 'done' : i === pos ? 'on' : ''} aria-hidden="true" />)}
          <span className="mono small">{pos + 1}/{p.order.length}</span>
        </span>
        <button className="link" onClick={p.onClose} aria-label="Close tour">Close ✕</button>
      </div>
      <p className="tour__text">{copy.tour[p.step]}</p>
      <div className="tour__actions">
        {suggestion && <button className="btn btn--ghost" onClick={() => p.onSuggest(suggestion.action)}>{suggestion.label}</button>}
        {p.step > 0 && <button className="btn btn--ghost" onClick={() => p.onStep(p.step - 1)}>Back</button>}
        <button className="btn" onClick={advance}>{p.step < 2 ? 'Next' : next ? 'Next object →' : 'Finish'}</button>
      </div>
      <div className="tour__dots" aria-hidden="true">{[0, 1, 2].map((i) => <span key={i} className={i === p.step ? 'on' : ''} />)}</div>
    </section>
  );
}

function suggestionFor(id: string, kind: TargetKind, step: number): { label: string; action: { mode?: ViewMode; band?: BandId; spectrum?: boolean } } | null {
  if (step === 1) {
    if (id === 'wise-0855') return { label: 'Switch to 3.8–5 µm', action: { band: 'D56', mode: 'blink' } };
    if (kind === 'mover' || kind === 'companion-mover') return { label: 'Show Difference', action: { mode: 'diff' } };
    return { label: 'Play the blink', action: { mode: 'blink' } };
  }
  if (step === 2 && (id === 'wise-0855' || id === 'r-draconis')) return { label: id === 'r-draconis' ? 'Open light curve' : 'Open spectrum', action: { spectrum: true } };
  return null;
}
