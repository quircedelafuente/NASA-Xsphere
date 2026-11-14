import { useCallback, useEffect, useMemo, useState } from 'react';
import type { BandId, FlagsJson, GaiaJson, Manifest, SpectrumJson, TargetMeta, ViewMode } from '../ui/lib/contracts';
import { BlinkCanvas } from '../ui/viewer';
import { useCatalog } from '../ui/lib/useCatalog';
import { loadFlags, loadFrames, loadGaia, loadManifest, loadSpectrum, matchTarget, nearestTarget } from '../ui/lib/data';
import { navigate } from '../ui/lib/router';
import { MAX_FPS, viewUrl, type Overlay, type ViewState } from '../ui/lib/url';
import { maskCss, sequenceLambda, type PaletteId } from '../ui/lib/palette';
import { formatDec, formatMjdLong, formatRa } from '../ui/lib/astro';
import { Header, MockBanner, Footer, BlinkMark } from '../ui/components/Chrome';
import { SearchBox } from '../ui/components/SearchBox';
import { TargetChips } from '../ui/components/TargetChips';
import { AdvancedDrawer, BandChips, EpochStrip, ModeToggle, PlayBar, StateCard } from '../ui/components/Controls';
import { ExplainPanel, motionSentence } from '../ui/components/ExplainPanel';
import { TourCard } from '../ui/components/Tour';
import { SpectrumPanel } from '../ui/components/SpectrumPanel';
import { CandidatePanel, SharePanel } from '../ui/components/SharePanel';
import { BANDS, MODES, PRODUCT, STATES } from '../ui/copy';

type Panel = 'none' | 'spectrum' | 'share' | 'candidate';
const TOUR_ORDER = ['barnards-star', 'wise-0855', 'eps-indi-b', 'rw-aurigae', 'r-draconis'];

function prefersReducedMotion() {
  return typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}

export function Viewer({ state, embed }: { state: ViewState; embed?: boolean }) {
  const catalog = useCatalog();
  const reduced = useMemo(prefersReducedMotion, []);

  // ---- resolve which target this URL means ----
  const resolved: { meta: TargetMeta | null; status: 'resolving' | 'ok' | 'name-not-found' | 'live-not-available' } = useMemo(() => {
    if (!catalog) return { meta: null, status: 'resolving' };
    if (state.target) {
      const hit = catalog.metas[state.target] ? catalog.index.find((e) => e.id === state.target) : matchTarget(state.target, catalog.index, catalog.metas);
      return hit ? { meta: catalog.metas[hit.id], status: 'ok' } : { meta: null, status: 'name-not-found' };
    }
    if (state.ra !== undefined && state.dec !== undefined) {
      const near = nearestTarget(state.ra, state.dec, Object.values(catalog.metas));
      return near ? { meta: near, status: 'ok' } : { meta: null, status: 'live-not-available' };
    }
    return { meta: null, status: 'name-not-found' };
  }, [catalog, state.target, state.ra, state.dec]);
  const meta = resolved.meta;
  const entry = meta && catalog ? catalog.index.find((e) => e.id === meta.id) : undefined;

  // ---- view state (initialised from the URL, C5) ----
  const [band, setBand] = useState<BandId | undefined>(state.band);
  const [mode, setMode] = useState<ViewMode>(reduced && !state.mode ? 'side' : state.mode);
  const [speed, setSpeed] = useState(Math.min(MAX_FPS, state.speed));
  const [frame, setFrame] = useState(state.frame);
  const [playing, setPlaying] = useState(!reduced);
  const [zoom, setZoom] = useState(state.zoom ?? 8);
  const [stretchA, setStretchA] = useState<number | undefined>(state.stretchA);
  const [vmax, setVmax] = useState<number | undefined>(undefined);
  const [invert, setInvert] = useState(false);
  const [palette, setPalette] = useState<PaletteId>(state.palette ?? 'infrared');
  const [overlays, setOverlays] = useState<Overlay[]>(state.overlays);
  const [excluded, setExcluded] = useState<number[]>([]);
  const [advOpen, setAdvOpen] = useState(false);
  const [panel, setPanel] = useState<Panel>('none');
  const [tour, setTour] = useState(Boolean(state.tour));
  const [tourStep, setTourStep] = useState(0);
  const [picked, setPicked] = useState<{ ra: number; dec: number } | null>(null);

  const [manifest, setManifest] = useState<Manifest | null>(null);
  const [frames, setFrames] = useState<Float32Array[] | null>(null);
  const [load, setLoad] = useState<'idle' | 'loading' | 'ok' | 'error'>('idle');
  const [spectrum, setSpectrum] = useState<SpectrumJson | null>(null);
  const [flags, setFlags] = useState<FlagsJson | null>(null);
  const [gaia, setGaia] = useState<GaiaJson | null>(null);

  const activeBand: BandId | undefined = meta
    ? band && entry?.bands.includes(band) ? band : entry?.bands.includes(meta.default_band) ? meta.default_band : entry?.bands[0]
    : undefined;

  // ---- load bundle ----
  useEffect(() => {
    if (!meta || !activeBand) return;
    let alive = true;
    setLoad('loading');
    (async () => {
      try {
        const m = await loadManifest(meta.id, activeBand);
        const f = await loadFrames(meta.id, activeBand, m);
        if (!alive) return;
        setManifest(m);
        setFrames(f);
        setFrame((i) => Math.min(i, m.frames.length - 1));
        setExcluded([]);
        setVmax(undefined);
        setLoad('ok');
      } catch {
        if (alive) setLoad('error');
      }
    })();
    return () => { alive = false; };
  }, [meta, activeBand]);

  useEffect(() => {
    if (!meta) return;
    loadSpectrum(meta.id).then(setSpectrum);
    loadGaia(meta.id).then(setGaia);
    loadFlags().then(setFlags);
  }, [meta]);

  // ---- keep the URL in sync (shareable state) ----
  const shareState: ViewState = useMemo(() => ({
    embed: Boolean(embed), target: meta?.id, mode, speed, frame: playing ? 0 : frame,
    band: band, stretchA, overlays, zoom: zoom !== 8 ? zoom : undefined, tour, palette,
    ...(meta ? {} : { ra: state.ra, dec: state.dec }),
  }), [embed, meta, mode, speed, frame, playing, band, stretchA, overlays, zoom, tour, palette, state.ra, state.dec]);

  useEffect(() => {
    if (resolved.status !== 'ok') return;
    navigate(viewUrl(shareState, { embed }), { replace: true });
  }, [shareState, embed, resolved.status]);

  // ---- actions ----
  const n = manifest?.frames.length ?? 0;
  const activeFrames = useMemo(() => Array.from({ length: n }, (_, i) => i).filter((i) => !excluded.includes(i)), [n, excluded]);
  const step = useCallback((d: number) => {
    setPlaying(false);
    setFrame((i) => {
      const pos = activeFrames.indexOf(i);
      return activeFrames[(pos + d + activeFrames.length) % activeFrames.length] ?? 0;
    });
  }, [activeFrames]);
  const toggleOverlay = (o: Overlay, on: boolean) => setOverlays((s) => (on ? [...new Set([...s, o])] : s.filter((x) => x !== o)));
  const goTarget = (id: string, extra: Partial<ViewState> = {}) => navigate(viewUrl({ target: id, ...extra }, { embed }));

  // ---- keyboard (Space, ←/→, B/D/S, +/−) ----
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      const el = e.target as HTMLElement;
      if (el && (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.tagName === 'SELECT' || el.isContentEditable)) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === ' ') { e.preventDefault(); setPlaying((p) => !p); }
      else if (e.key === 'ArrowRight') { e.preventDefault(); step(1); }
      else if (e.key === 'ArrowLeft') { e.preventDefault(); step(-1); }
      else if (e.key === 'd' || e.key === 'D') setMode((m) => (m === 'diff' ? 'blink' : 'diff'));
      else if (e.key === 'b' || e.key === 'B') setMode('blink');
      else if (e.key === 's' || e.key === 'S') setMode('side');
      else if (e.key === '+' || e.key === '=') setZoom((z) => Math.min(14, z + 1));
      else if (e.key === '-') setZoom((z) => Math.max(2, z - 1));
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [step]);

  // ---- non-OK resolution states ----
  if (resolved.status === 'resolving') return <Shell embed={embed} catalog={catalog}><StateCard {...STATES.loading} /></Shell>;
  if (resolved.status === 'name-not-found') {
    return (
      <Shell embed={embed} catalog={catalog}>
        <StateCard title={STATES['name-not-found'].title} body={`“${state.target ?? ''}” — ${STATES['name-not-found'].body}`} tone="warn" />
        <TargetChips catalog={catalog} embed={embed} />
      </Shell>
    );
  }
  if (resolved.status === 'live-not-available' || !meta) {
    return (
      <Shell embed={embed} catalog={catalog}>
        <StateCard {...STATES['live-not-available']}>
          <p className="mono small">{formatRa(state.ra ?? 0)} {formatDec(state.dec ?? 0)}</p>
          <p className="small"><a href="https://irsa.ipac.caltech.edu/Missions/spherex.html" target="_blank" rel="noreferrer">SPHEREx at IRSA ↗</a></p>
        </StateCard>
        <TargetChips catalog={catalog} embed={embed} />
      </Shell>
    );
  }

  const nEpochs = manifest?.frames.length ?? 0;
  const fr = manifest?.frames[frame];
  const saturated = Boolean(meta.expected?.saturated && (manifest?.warnings?.some((w) => w.includes('saturat')) || fr?.flags_at_target?.includes('OVERFLOW')));
  const stretch = manifest ? { a: stretchA ?? manifest.stretch.a, vmin: manifest.stretch.vmin, vmax: vmax ?? manifest.stretch.vmax } : { a: 0.1, vmin: 0, vmax: 1 };
  const bandCopy = BANDS.find((b) => b.id === activeBand);
  const motion = manifest ? motionSentence(manifest) : null;

  const canvas = manifest && frames && load === 'ok' ? (
    <div className="stage__canvas">
      <BlinkCanvas
        manifest={manifest}
        frames={frames}
        mode={mode}
        frameIndex={frame}
        playing={playing && nEpochs > 1}
        fps={speed}
        stretch={stretch}
        zoom={zoom}
        invert={invert}
        palette={palette}
        excludeEpochs={excluded}
        overlays={{ crosshair: overlays.includes('crosshair'), track: overlays.includes('track'), gaia: overlays.includes('gaia') ? gaia : null, flags: overlays.includes('flags') }}
        onFrameChange={setFrame}
        onPixelClick={(ra, dec) => { setPicked({ ra, dec }); }}
      />
      {mode !== 'side' && fr && (
        <div className="stage__label mono" aria-live={playing ? 'off' : 'polite'}>
          <span>{mode === 'diff' ? `Visit ${frame === 0 ? 2 : frame + 1} − visit ${frame === 0 ? 1 : frame}` : `Visit ${frame + 1}/${nEpochs}`}</span>
          <span>{formatMjdLong(fr.mjd)}</span>
          <span>{fr.lam_mean_um.toFixed(2)} µm</span>
        </div>
      )}
      {mode === 'side' && manifest && (
        <div className="stage__sidelabels mono small">{manifest.frames.filter((_, i) => !excluded.includes(i)).map((f) => <span key={f.epoch}>{f.label}</span>)}</div>
      )}
      <p className="sr-only">{motion ?? ''}</p>
    </div>
  ) : load === 'error' ? (
    <StateCard {...STATES.error} tone="warn" />
  ) : (
    <div className="stage__canvas stage__canvas--loading" style={{ width: 64 * zoom, height: 64 * zoom }}><span>{STATES.loading.title}</span></div>
  );

  // ---- embed: minimal chrome ----
  if (embed) {
    return (
      <div className="page page--embed">
        {canvas}
        <div className="embed__bar">
          <button className="icon-btn" onClick={() => setPlaying((p) => !p)} aria-label={playing ? 'Pause' : 'Play'}>{playing ? '❚❚' : '▶'}</button>
          <ModeToggle value={mode} onChange={setMode} disabledDiff={nEpochs < 2} />
          <a className="embed__open" href={viewUrl({ ...shareState, embed: false }, { absolute: true })} target="_blank" rel="noreferrer">
            <BlinkMark /> {meta.name} · Open in {PRODUCT.name} ↗
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="page page--viewer">
      <Header>
        <SearchBox catalog={catalog} compact />
      </Header>
      {catalog?.mock && <MockBanner />}
      <nav className="viewer__targets" aria-label="Demo targets"><TargetChips catalog={catalog} current={meta.id} variant="pills" /></nav>

      <main id="main" className="viewer">
        <section className="stage" aria-label={`${meta.name} — SPHEREx images`}>
          <div className="stage__title">
            <h1>{meta.name}</h1>
            <span className="mono small muted">{formatRa(meta.ra_deg)} {formatDec(meta.dec_deg)}</span>
            {!tour && <button className="link small" onClick={() => { setTour(true); setTourStep(0); }}>Guided tour</button>}
          </div>

          {tour && (
            <TourCard
              targetId={meta.id} kind={meta.kind} step={tourStep} onStep={setTourStep} order={TOUR_ORDER.filter((id) => catalog?.metas[id])}
              onTarget={(id) => goTarget(id, { tour: true })} onClose={() => setTour(false)}
              onSuggest={(s) => { if (s.mode) setMode(s.mode); if (s.band) setBand(s.band); if (s.spectrum) setPanel('spectrum'); setPlaying(true); }}
            />
          )}

          {nEpochs === 1 && <StateCard {...STATES['one-epoch']} />}
          {nEpochs === 2 && <StateCard {...STATES['two-epochs']} />}
          {saturated && mode !== 'diff' && <StateCard {...STATES['saturated-target']} />}

          {canvas}

          {manifest && (
            <>
              <EpochStrip frames={manifest.frames} current={frame} excluded={excluded} onPick={(i) => { setPlaying(false); setFrame(i); }} />
              <PlayBar
                playing={playing} onToggle={() => setPlaying((p) => !p)} onPrev={() => step(-1)} onNext={() => step(1)}
                speed={speed} onSpeed={setSpeed} zoom={zoom} onZoom={setZoom} disabled={nEpochs < 2 || mode === 'side'}
              />
              <div className="stage__row">
                <ModeToggle value={mode} onChange={setMode} disabledDiff={nEpochs < 2} />
                <p className="mode-help small muted">{MODES[mode].help}</p>
              </div>
              <div className="stage__row stage__row--bands">
                <BandChips available={entry?.bands ?? []} value={activeBand!} onChange={setBand} />
                {bandCopy && <p className="small muted">Showing <strong>{bandCopy.range}</strong> — {bandCopy.plain.charAt(0).toLowerCase() + bandCopy.plain.slice(1)}. Every visit in the loop is the same colour.</p>}
              </div>
              <div className="actions">
                <button className={`btn ${panel === 'spectrum' ? '' : 'btn--ghost'}`} onClick={() => setPanel(panel === 'spectrum' ? 'none' : 'spectrum')}>Spectrum</button>
                <button className={`btn ${panel === 'share' ? '' : 'btn--ghost'}`} onClick={() => setPanel(panel === 'share' ? 'none' : 'share')}>Share / embed</button>
                <button className={`btn ${panel === 'candidate' ? '' : 'btn--ghost'}`} onClick={() => setPanel(panel === 'candidate' ? 'none' : 'candidate')}>Flag a candidate</button>
              </div>
              {panel === 'spectrum' && <SpectrumPanel spectrum={spectrum} defaultView={meta.kind === 'variable' && nEpochs > 3 ? 'lightcurve' : 'spectrum'} onClose={() => setPanel('none')} />}
              {panel === 'share' && <SharePanel state={shareState} meta={meta} onClose={() => setPanel('none')} />}
              {panel === 'candidate' && <CandidatePanel state={shareState} meta={meta} manifest={manifest} picked={picked} onClose={() => setPanel('none')} />}
              <AdvancedDrawer
                open={advOpen} onToggle={() => setAdvOpen((o) => !o)}
                stretchA={stretchA ?? manifest.stretch.a} onStretchA={setStretchA}
                vmax={vmax ?? manifest.stretch.vmax} vmaxDefault={manifest.stretch.vmax} onVmax={setVmax}
                invert={invert} onInvert={setInvert}
                palette={palette} onPalette={setPalette}
                flags={overlays.includes('flags')} onFlags={(v) => toggleOverlay('flags', v)}
                crosshair={overlays.includes('crosshair')} onCrosshair={(v) => toggleOverlay('crosshair', v)}
                track={overlays.includes('track')} onTrack={(v) => toggleOverlay('track', v)}
                frames={manifest.frames} excluded={excluded}
                onExclude={(i) => setExcluded((s) => (s.includes(i) ? s.filter((x) => x !== i) : [...s, i]))}
              />
              <p className="kbd-help small muted">Keys: <kbd>Space</kbd> play/pause · <kbd>←</kbd>/<kbd>→</kbd> visit · <kbd>D</kbd> difference · <kbd>S</kbd> side by side · <kbd>+</kbd>/<kbd>−</kbd> zoom</p>
            </>
          )}
        </section>

        {manifest && <ExplainPanel meta={meta} manifest={manifest} frameIndex={frame} flags={flags} mock={Boolean(catalog?.mock)} flagColour={maskCss(palette, sequenceLambda(manifest))} />}
      </main>
      <Footer />
    </div>
  );
}

function Shell({ embed, catalog, children }: { embed?: boolean; catalog: ReturnType<typeof useCatalog>; children: React.ReactNode }) {
  return (
    <div className={`page ${embed ? 'page--embed' : 'page--viewer'}`}>
      {!embed && <Header><SearchBox catalog={catalog} compact /></Header>}
      <main id="main" className="viewer viewer--state">{children}</main>
      {!embed && <Footer />}
    </div>
  );
}
