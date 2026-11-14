import { useState } from 'react';
import type { ViewState } from '../lib/url';
import { viewUrl } from '../lib/url';
import type { Manifest, TargetMeta } from '../lib/contracts';
import { formatDec, formatRa } from '../lib/astro';

function useCopy() {
  const [copied, setCopied] = useState<string | null>(null);
  const copy = async (key: string, text: string) => {
    try { await navigator.clipboard.writeText(text); } catch { /* clipboard blocked: user can still select the field */ }
    setCopied(key);
    window.setTimeout(() => setCopied(null), 1600);
  };
  return { copied, copy };
}

export function SharePanel({ state, meta, onClose }: { state: ViewState; meta: TargetMeta; onClose: () => void }) {
  const { copied, copy } = useCopy();
  const link = viewUrl(state, { absolute: true });
  const embed = `<iframe src="${viewUrl(state, { embed: true, absolute: true })}" width="640" height="520" style="border:0" title="${meta.name} — SPHEREx blink" loading="lazy"></iframe>`;
  const fovArcmin = (meta.fov_arcsec / 60).toFixed(1);
  // WiseView hash params per role file research (ra, dec, size, band, speed, zoom) — verify on the live site
  const wiseview = `http://byw.tools/wiseview#ra=${meta.ra_deg}&dec=${meta.dec_deg}&size=176&band=3&speed=164&zoom=9`;
  const irsa = 'https://irsa.ipac.caltech.edu/Missions/spherex.html';

  return (
    <section className="share" aria-labelledby="share-h">
      <div className="spectrum__head">
        <h2 id="share-h">Share this view</h2>
        <button className="link" onClick={onClose} aria-label="Close share">Close ✕</button>
      </div>
      <label className="field">
        <span>Link (opens exactly this view)</span>
        <div className="field__row">
          <input readOnly value={link} onFocus={(e) => e.target.select()} />
          <button className="btn" onClick={() => copy('link', link)}>{copied === 'link' ? 'Copied ✓' : 'Copy'}</button>
        </div>
      </label>
      <label className="field">
        <span>Embed in a website</span>
        <div className="field__row">
          <textarea readOnly rows={3} value={embed} onFocus={(e) => e.target.select()} />
          <button className="btn" onClick={() => copy('embed', embed)}>{copied === 'embed' ? 'Copied ✓' : 'Copy'}</button>
        </div>
      </label>
      <p className="small">
        Same position elsewhere: <a href={wiseview} target="_blank" rel="noreferrer">WiseView (WISE, 10+ years) ↗</a> ·{' '}
        <a href={irsa} target="_blank" rel="noreferrer">IRSA SPHEREx archive ↗</a>
      </p>
      <p className="muted small mono">{formatRa(meta.ra_deg)} {formatDec(meta.dec_deg)} · field {fovArcmin}′</p>
    </section>
  );
}

/** U7 (nice-to-have): prefilled "flag a candidate" report. Never says "discovery" (D13). */
export function CandidatePanel({ state, meta, manifest, picked, onClose }: {
  state: ViewState; meta: TargetMeta; manifest: Manifest; picked: { ra: number; dec: number } | null; onClose: () => void;
}) {
  const [note, setNote] = useState('');
  const [checks, setChecks] = useState({ notArtifact: false, multiEpoch: false, notCatalogued: false });
  const ra = picked?.ra ?? meta.ra_deg;
  const dec = picked?.dec ?? meta.dec_deg;
  const report = {
    type: 'candidate',
    ra_deg: Number(ra.toFixed(6)),
    dec_deg: Number(dec.toFixed(6)),
    near_target: meta.id,
    band: manifest.band,
    epochs: manifest.frames.map((f) => ({ label: f.label, mjd: f.mjd })),
    permalink: viewUrl({ ...state, ra, dec, target: undefined }, { absolute: true }),
    checklist: checks,
    note,
    created_utc: new Date().toISOString(),
  };
  const download = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `candidate_${report.ra_deg}_${report.dec_deg}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  return (
    <section className="share" aria-labelledby="cand-h">
      <div className="spectrum__head">
        <h2 id="cand-h">Flag a candidate</h2>
        <button className="link" onClick={onClose} aria-label="Close">Close ✕</button>
      </div>
      <p className="small">Spotted something that moves or changes? Click it in the image to set the position, then save a report. A candidate is a lead, not a confirmed object — experts check it against other surveys.</p>
      <p className="mono small">{formatRa(ra)} {formatDec(dec)} {picked ? '' : '(click the image to change)'}</p>
      <fieldset className="checks">
        <legend className="small">Before you flag it</legend>
        <label className="check"><input type="checkbox" checked={checks.multiEpoch} onChange={(e) => setChecks({ ...checks, multiEpoch: e.target.checked })} /> It shifts or changes across more than two visits</label>
        <label className="check"><input type="checkbox" checked={checks.notArtifact} onChange={(e) => setChecks({ ...checks, notArtifact: e.target.checked })} /> It is not on “problem pixels” or next to a very bright star</label>
        <label className="check"><input type="checkbox" checked={checks.notCatalogued} onChange={(e) => setChecks({ ...checks, notCatalogued: e.target.checked })} /> I checked WiseView / SIMBAD and it isn’t a known object</label>
      </fieldset>
      <label className="field"><span>Note (optional)</span><textarea rows={2} value={note} onChange={(e) => setNote(e.target.value)} /></label>
      <button className="btn" onClick={download}>Download candidate report (JSON)</button>
    </section>
  );
}
