import type { FlagsJson, Manifest, TargetMeta } from '../lib/contracts';
import { BANDS, FLAG_LEGEND_FALLBACK, KIND_LABEL, TARGET_COPY } from '../copy';
import { compass, formatDec, formatMjd, formatRa } from '../lib/astro';

const PX = 6.15;

/** Plain-language sentence for the motion over the loaded sequence (text alternative to the animation). */
export function motionSentence(m: Manifest): string | null {
  const t = m.target_track;
  if (!t || t.length < 2) return null;
  const a = t[0], b = t[t.length - 1];
  const dEast = -(b.x - a.x) * PX; // x grows to the west (east is left, north up)
  const dNorth = -(b.y - a.y) * PX;
  const dist = Math.hypot(dEast, dNorth);
  const px = dist / PX;
  if (dist < 1.5) return `It stays put: no measurable motion between ${formatMjd(a.mjd)} and ${formatMjd(b.mjd)}.`;
  return `It moved ${dist.toFixed(0)}″ ${compass(dEast, dNorth)} between ${formatMjd(a.mjd)} and ${formatMjd(b.mjd)} — about ${px.toFixed(1)} pixel${px.toFixed(1) === '1.0' ? '' : 's'}.`;
}

export function ExplainPanel({ meta, manifest, frameIndex, flags, mock }: { meta: TargetMeta; manifest: Manifest; frameIndex: number; flags: FlagsJson | null; mock: boolean }) {
  const copy = TARGET_COPY[meta.id];
  const frame = manifest.frames[frameIndex];
  const band = BANDS.find((b) => b.id === manifest.band);
  const motion = motionSentence(manifest);
  const flagNames = frame?.flags_at_target ?? [];
  const legend = flags
    ? Object.values(flags.bits).filter((b) => b.class === 'soft' && (flagNames.length === 0 || flagNames.includes(b.name)))
    : FLAG_LEGEND_FALLBACK.filter((b) => flagNames.length === 0 || flagNames.includes(b.name));

  return (
    <aside className="explain" aria-labelledby="explain-h">
      <p className="eyebrow">{KIND_LABEL[meta.kind]}</p>
      <h2 id="explain-h">What am I seeing?</h2>
      {copy ? <p className="explain__lede">{copy.oneLiner}</p> : <p className="explain__lede">A patch of sky at {formatRa(meta.ra_deg)} {formatDec(meta.dec_deg)}.</p>}

      <div className="explain__now">
        <p className="mono small">
          Visit {frameIndex + 1} of {manifest.frames.length} · {frame?.label} · {frame?.lam_mean_um.toFixed(2)} µm{band ? ` (${band.plain.charAt(0).toLowerCase() + band.plain.slice(1)})` : ''}
        </p>
        {motion && <p className="explain__motion">{motion}</p>}
      </div>

      {copy && (
        <>
          <h3>Look for</h3>
          <p>{copy.lookFor}</p>
          <h3>Best view</h3>
          <p>{copy.bestBand}</p>
          <h3>About it</h3>
          <ul className="facts">
            {copy.facts.map((f, i) => (
              <li key={i}>{f.text}{mock && f.verify && <span className="draft-tag" title="Placeholder until Data's science notes (C7) are in">draft</span>}</li>
            ))}
          </ul>
        </>
      )}

      {meta.archival_positions && meta.archival_positions.length > 0 && (
        <>
          <h3>Where it used to be</h3>
          <ul className="archival mono small">
            {meta.archival_positions.map((p) => (
              <li key={p.survey}>{p.survey} {p.epoch.toFixed(1)}: {formatRa(p.ra_deg)} {formatDec(p.dec_deg)}</li>
            ))}
          </ul>
        </>
      )}

      {(flagNames.length > 0 || manifest.warnings?.length) ? (
        <>
          <h3>Problem pixels</h3>
          <ul className="legend">
            {legend.map((b) => <li key={b.name}><span className="swatch swatch--flag" aria-hidden="true" />{b.plain}</li>)}
          </ul>
        </>
      ) : null}

      <details className="explain__data">
        <summary>About this data</summary>
        <ul className="small">
          <li>Position: <span className="mono">{formatRa(meta.ra_deg)} {formatDec(meta.dec_deg)}</span> ({meta.astrometry_source ?? 'catalogue'}, epoch {meta.ref_epoch})</li>
          <li>Frames are matched in wavelength: every visit in this loop is the same infrared colour.</li>
          <li>Each frame co-adds {frame?.n_exposures ?? '—'} SPHEREx exposures. Pixel size 6.15″.</li>
          <li>Data release: {Array.isArray(meta.release) ? meta.release.join(', ') : meta.release ?? '—'}</li>
        </ul>
      </details>
    </aside>
  );
}
