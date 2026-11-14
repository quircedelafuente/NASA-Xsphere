import { useState } from 'react';
import { SkyRegionSelector, type SkyRegion } from '../ui/sky-region/SkyRegionSelector';
import { scanRegion, type ScanProgress, type ScanReport } from '../api/client';

const LABEL: Record<string, string> = { 'known-star': 'known star', 'known-asteroid': 'known asteroid', variable: 'variable', artefact: 'artefact',
  'candidate-mover': 'candidate mover', 'candidate-change': 'candidate change' };

export function SkyRegionDemo() {
  const [submitted, setSubmitted] = useState<SkyRegion | null>(null);
  const [progress, setProgress] = useState<ScanProgress | null>(null);
  const [report, setReport] = useState<ScanReport | null>(null);

  async function handleRegionSelected(region: SkyRegion) {
    // BACKEND CONNECTION: the engine fetches the SPHEREx photos of this square from NASA, compares the visits and
    // checks every change against Gaia and known asteroids. Returning the Promise lets the selector lock and show errors.
    setSubmitted(region); setReport(null); setProgress({ status: 'queued', progress: 0 });
    try {
      setReport(await scanRegion(region, setProgress));
    } finally {
      setProgress(null);
    }
  }

  return (
    <main className="demo">
      <header>
        <p className="demo__eyebrow">XSPHERE / REGION SELECTOR</p>
        <h1>Choose your patch of sky.</h1>
        <p>Explore, select a square, then confirm it. The engine checks it for anything that moved or changed between SPHEREx visits.</p>
      </header>
      <SkyRegionSelector onRegionSelected={handleRegionSelected} />
      <section className="demo__payload" aria-labelledby="payload-title" aria-live="polite">
        <div><h2 id="payload-title">Scan</h2><span>{submitted ? `RA ${submitted.ra_deg.toFixed(4)}° · Dec ${submitted.dec_deg.toFixed(4)}°` : ''}</span></div>
        {progress && <p>{progress.status} · {Math.round(progress.progress * 100)}%{progress.step ? ` · ${progress.step}` : ''}<br />
          <small>A new patch takes a few minutes: the engine reads the photos from NASA. Patches already scanned return instantly.</small></p>}
        {report ? (<>
          <p><strong>{report.summary_text}</strong></p>
          <ol className="demo__sources">{report.sources.map((s) => (
            <li key={s.id}><b>{LABEL[s.class] ?? s.class}</b> · {Math.round(s.max_sigma)}σ · {s.reason}</li>))}</ol>
          <p><small>{report.photos_used} of {report.photos_available} photos · {report.visits} visits · Gaia {report.checks.gaia} · asteroids {report.checks.asteroids}. "Candidate" means unexplained so far, not a discovery.</small></p>
        </>) : !progress && <pre>{submitted ? 'Waiting…' : 'No region submitted yet.'}</pre>}
      </section>
      <footer>Sky background: SPHEREx all-sky (NASA/IRSA), DSS2 and 2MASS mirrors at IRSA, shown with <a href="https://aladin.cds.unistra.fr/AladinLite/">CDS Aladin Lite</a>. Scan results come from the SPHEREx photos themselves.</footer>
    </main>
  );
}
