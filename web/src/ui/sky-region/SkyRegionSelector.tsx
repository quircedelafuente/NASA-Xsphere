import { useEffect, useId, useRef, useState, type PointerEvent } from 'react';
import { createSkyViewer, SURVEYS, type SkyViewer, type SurveyKey } from './aladin';
import { regionAt, type SkyRegion } from './geometry';
import './sky-region.css';

export type { SkyRegion } from './geometry';
export interface SkyRegionSelectorProps {
  onRegionSelected: (region: SkyRegion) => void | Promise<void>;
}

type Gesture = { id: number; x: number; y: number; moved: boolean };

export function SkyRegionSelector({ onRegionSelected }: SkyRegionSelectorProps) {
  const mount = useRef<HTMLDivElement>(null);
  const viewer = useRef<SkyViewer | null>(null);
  const gesture = useRef<Gesture | null>(null);
  const submissionLock = useRef(false);
  const mounted = useRef(false);
  const [ready, setReady] = useState(false);
  const [selecting, setSelecting] = useState(false);
  const [selection, setSelection] = useState<SkyRegion | null>(null);
  const [submission, setSubmission] = useState<'idle' | 'pending' | 'done'>('idle');
  const [error, setError] = useState('');
  const [survey, setSurvey] = useState<SurveyKey>('dss');
  const helpId = useId();

  useEffect(() => {
    mounted.current = true;
    let cancelled = false;
    let instance: SkyViewer | undefined;
    const host = document.createElement('div');
    host.className = 'sky-region__viewer';
    mount.current!.append(host);
    createSkyViewer(host).then((result) => {
      if (cancelled) { result.dispose(); return; }
      instance = result;
      viewer.current = result;
      setReady(true);
    }).catch((cause: unknown) => {
      if (!cancelled) setError(`Could not load the sky map. Check your internet connection and WebGL support, then reload. ${cause instanceof Error ? cause.message : ''}`);
    });
    return () => {
      cancelled = true;
      mounted.current = false;
      gesture.current = null;
      viewer.current = null;
      instance?.dispose();
      host.remove();
    };
  }, []);

  function startGesture(event: PointerEvent<HTMLDivElement>) {
    // UI controls inside Aladin must never become sky selections.
    if (!event.isPrimary || event.button !== 0) { gesture.current = null; return; }
    if (!selecting || submissionLock.current || !(event.target instanceof HTMLCanvasElement)) return;
    gesture.current = { id: event.pointerId, x: event.clientX, y: event.clientY, moved: false };
  }

  function trackGesture(event: PointerEvent<HTMLDivElement>) {
    const current = gesture.current;
    if (current?.id === event.pointerId && Math.hypot(event.clientX - current.x, event.clientY - current.y) > 4) {
      current.moved = true; // Stays true even if the drag returns to its start.
    }
  }

  function finishGesture(event: PointerEvent<HTMLDivElement>) {
    trackGesture(event);
    const current = gesture.current;
    gesture.current = null;
    if (!current || current.id !== event.pointerId || current.moved || !selecting || submissionLock.current || !viewer.current) return;
    if (!(event.target instanceof HTMLCanvasElement)) return;
    try {
      const rect = mount.current!.getBoundingClientRect();
      const position = viewer.current.pixelToSky(event.clientX - rect.left, event.clientY - rect.top);
      if (!position) throw new Error('This click is outside the sky projection. Try another point.');
      const next = regionAt(...position);
      viewer.current.drawRegion(next);
      setSelection(next);
      setSubmission('idle');
      setError('');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to select this sky position.');
    }
  }

  async function submitRegion() {
    if (!selection || submissionLock.current || submission === 'done') return;
    submissionLock.current = true;
    setSubmission('pending');
    setError('');
    try {
      // The ONLY handoff. No rounding, fetching, or automatic submission on pan.
      await onRegionSelected({ ...selection });
      if (mounted.current) setSubmission('done');
    } catch (cause) {
      if (mounted.current) {
        setSubmission('idle');
        setError(cause instanceof Error ? cause.message : 'Submission failed. Please try again.');
      }
    } finally {
      submissionLock.current = false;
    }
  }

  return (
    <section className="sky-region" aria-label="Sky region selector">
      <div className="sky-region__toolbar">
        <button type="button" disabled={!ready || submission === 'pending'} aria-pressed={selecting}
          onClick={() => { setSelecting(!selecting); gesture.current = null; }}>
          {selecting ? 'Stop selecting' : 'Select region'}
        </button>
        <label className="sky-region__survey">Background{' '}
          <select value={survey} disabled={!ready} onChange={(e) => { const k = e.target.value as SurveyKey; setSurvey(k); viewer.current?.setSurvey(k); }}>
            {(Object.keys(SURVEYS) as SurveyKey[]).map((k) => <option key={k} value={k}>{SURVEYS[k].name}</option>)}
          </select>
        </label>
        <span>ICRS · Fixed square · 0.1° × 0.1°</span>
      </div>
      <p id={helpId} className="sky-region__help">
        {!ready ? 'Loading Aladin Lite…' : selecting
          ? 'Click the sky to place or replace the square. Drag to pan; scroll to zoom.'
          : 'Explore the sky by dragging and scrolling. Choose Select region when you are ready.'}
      </p>
      <div ref={mount} className={`sky-region__map${selecting ? ' sky-region__map--selecting' : ''}`}
        aria-label="Interactive Aladin sky map" aria-describedby={helpId}
        onPointerDownCapture={startGesture} onPointerMoveCapture={trackGesture}
        onPointerUpCapture={finishGesture} onPointerCancelCapture={() => { gesture.current = null; }}
        onPointerLeave={() => { gesture.current = null; }}
        onWheelCapture={() => { gesture.current = null; }} />
      <div className="sky-region__footer">
        <dl aria-live="polite">
          <div><dt>Right ascension</dt><dd>{selection ? `${selection.ra_deg.toFixed(7)}°` : '—'}</dd></div>
          <div><dt>Declination</dt><dd>{selection ? `${selection.dec_deg.toFixed(7)}°` : '—'}</dd></div>
          <div><dt>Width</dt><dd>0.1° <small>(6 arcmin)</small></dd></div>
        </dl>
        <button type="button" className="sky-region__submit" onClick={submitRegion}
          disabled={!selection || submission !== 'idle'}>
          {submission === 'pending' ? 'Submitting…' : submission === 'done' ? 'Region submitted' : 'Use this region'}
        </button>
      </div>
      <p className="sky-region__status" role="status">
        {submission === 'done' ? 'Region submitted. Click another sky position to select again.'
          : selection ? 'Selection ready. Use this region to confirm.' : 'No region selected.'}
      </p>
      {error && <p className="sky-region__error" role="alert">{error}</p>}
    </section>
  );
}
