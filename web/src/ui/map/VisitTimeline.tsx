/**
 * Visits as dots on a real time axis: you see at a glance how many visits there are, when they were taken and
 * which one is on screen. Tapping a dot pauses and shows that visit. In Difference mode the two visits being
 * subtracted are both highlighted.
 */
import type { ManifestFrame, ViewMode } from '../lib/contracts';
import { formatMjd, formatMjdLong } from '../lib/astro';

export function VisitTimeline({ frames, current, excluded, mode, onPick }: {
  frames: ManifestFrame[]; current: number; excluded: number[]; mode: ViewMode; onPick: (i: number) => void;
}) {
  if (frames.length === 0) return null;
  const t0 = frames[0].mjd, t1 = frames[frames.length - 1].mjd;
  const span = Math.max(1, t1 - t0);
  const pos = (mjd: number) => (frames.length === 1 ? 50 : 4 + ((mjd - t0) / span) * 92);
  const pair = mode === 'diff' ? [current === 0 ? 1 : current, current === 0 ? 0 : current - 1] : [current];

  return (
    <div className="vtl" role="group" aria-label={`${frames.length} SPHEREx visits`}>
      <div className="vtl__track">
        <span className="vtl__line" aria-hidden="true" />
        {frames.map((f, i) => (
          <button
            key={i}
            className={`vtl__dot ${pair.includes(i) ? 'is-on' : ''} ${excluded.includes(i) ? 'is-off' : ''}`}
            style={{ left: `${pos(f.mjd)}%` }}
            onClick={() => onPick(i)}
            aria-label={`Visit ${i + 1}: ${formatMjdLong(f.mjd)}`}
            aria-current={i === current ? 'true' : undefined}
            title={formatMjdLong(f.mjd)}
          />
        ))}
      </div>
      <div className="vtl__labels small">
        <span>{formatMjd(t0)}</span>
        <span className="vtl__now mono">
          {mode === 'diff' && frames.length > 1
            ? `Visit ${pair[0] + 1} − ${pair[1] + 1}`
            : `Visit ${current + 1} of ${frames.length} · ${formatMjdLong(frames[current]?.mjd ?? t0)}`}
        </span>
        {frames.length > 1 && <span>{formatMjd(t1)}</span>}
      </div>
    </div>
  );
}
