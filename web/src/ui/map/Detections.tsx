/**
 * Detections layer for the patch popup.
 *  - Change engine (processing/change.py, in every manifest): blobs ≥ 5σ between visit 1 and the visit on screen,
 *    labelled brighter / fainter / moved (a "moved" pair is drawn as one vector from where it was to where it is).
 *  - Discovery engine (processing/discovery, report /reports/<id>.json when it exists): linked movers with their
 *    fitted track and speed, variables and unexplained candidates. Known static stars are only counted.
 * Everything is a "candidate" until checked (D13).
 */
import type { Manifest, Wcs } from '../lib/contracts';
import { skyToPixel } from '../lib/astro';

export interface ChangeCand { x: number; y: number; sigma: number; npix: number; kind: string; saturated?: boolean }
interface ReportPos { visit: number; ra_deg: number; dec_deg: number }
export interface ReportSource {
  id: string; class: string; confidence: number; reason: string;
  motion?: { speed_arcsec_yr: number; direction?: string; sig: number } | null;
  positions?: ReportPos[]; ra_deg?: number; dec_deg?: number;
  crossmatch?: { cat: string; id: string }[];
}
export interface Report { sources: ReportSource[]; summary?: Record<string, number> }

export interface Detection {
  id: string;
  kind: 'brighter' | 'fainter' | 'moved' | 'mover' | 'variable' | 'candidate';
  title: string;
  value: string;          // right-aligned figure (σ, ″/yr, ×)
  sub: string;            // one quiet line of context
  x: number; y: number;   // patch pixels (top-left origin)
  r: number;              // marker half-size in pixels
  from?: [number, number];        // moved: where it was
  track?: [number, number][];     // mover: fitted positions per visit
}

const KIND_LABEL: Record<Detection['kind'], string> = {
  brighter: 'Brighter', fainter: 'Fainter', moved: 'Shifted', mover: 'Moving object', variable: 'Variable', candidate: 'Unexplained',
};

/** Sky → patch pixel (top-left origin), via the shared astro helper (same row convention as the viewer). */
function toPix(wcs: Wcs, ra: number, dec: number, ny: number): [number, number] | null {
  const p = skyToPixel(wcs, ra, dec, ny);
  return Number.isFinite(p.x) && Number.isFinite(p.y) ? [p.x, p.y] : null;
}

/** The difference shown for a visit: visit 1 → this visit (visit 1 itself shows 1 → 2). */
function diffFor(m: Manifest, frame: number) {
  const to = frame === 0 ? 1 : frame;
  return (m.diffs as ({ from: number; to: number; candidates?: ChangeCand[] }[] | undefined))?.find((d) => d.from === 0 && d.to === to) ?? null;
}

export function buildDetections(m: Manifest, report: Report | null, frame: number): { list: Detection[]; pair: [number, number]; known: number } {
  const nx = m.nx ?? 64, ny = m.ny ?? nx;
  const d = diffFor(m, frame);
  const list: Detection[] = [];
  const cands = d?.candidates ?? [];
  // pair "moved" blobs: nearest opposite-sign partner within 4 px → one vector (fainter = old spot, brighter = new)
  const used = new Set<number>();
  cands.forEach((c, i) => {
    if (used.has(i)) return;
    if (c.kind === 'moved') {
      let best = -1, bd = 4.5;
      cands.forEach((o, j) => {
        if (j === i || used.has(j) || o.kind !== 'moved' || Math.sign(o.sigma) === Math.sign(c.sigma)) return;
        const dd = Math.hypot(o.x - c.x, o.y - c.y);
        if (dd < bd) { bd = dd; best = j; }
      });
      if (best >= 0) {
        used.add(i); used.add(best);
        const pos = c.sigma > 0 ? c : cands[best], neg = c.sigma > 0 ? cands[best] : c;
        list.push({ id: `c${i}`, kind: 'moved', title: KIND_LABEL.moved, value: `${Math.max(Math.abs(pos.sigma), Math.abs(neg.sigma)).toFixed(1)}σ`,
          sub: `${bd.toFixed(1)} px between visits${pos.saturated || neg.saturated ? ' · saturated core' : ''}`,
          x: pos.x, y: pos.y, r: 2.6, from: [neg.x, neg.y] });
        return;
      }
    }
    used.add(i);
    const k = c.sigma > 0 ? 'brighter' : 'fainter';
    list.push({ id: `c${i}`, kind: k, title: KIND_LABEL[k], value: `${c.sigma > 0 ? '+' : '−'}${Math.abs(c.sigma).toFixed(1)}σ`,
      sub: `${c.npix} px${c.saturated ? ' · saturated core' : ''}`, x: c.x, y: c.y, r: Math.max(1.8, Math.min(3.2, Math.sqrt(c.npix) * 0.8)) });
  });

  let known = 0;
  for (const s of report?.sources ?? []) {
    const wcs = m.wcs;
    if (!wcs) break;
    const mover = s.motion && s.motion.sig >= 5 && s.motion.speed_arcsec_yr >= 1;
    const kind: Detection['kind'] | null = mover ? 'mover' : s.class === 'variable' ? 'variable' : s.class.startsWith('candidate') ? 'candidate' : null;
    if (!kind) { if (s.class === 'known-star') known++; continue; }
    const ps = (s.positions?.length ? s.positions : [{ visit: 0, ra_deg: s.ra_deg ?? 0, dec_deg: s.dec_deg ?? 0 }])
      .map((p) => toPix(wcs, p.ra_deg, p.dec_deg, ny)).filter((p): p is [number, number] => Boolean(p));
    if (!ps.length) continue;
    const here = ps[Math.min(frame, ps.length - 1)];
    if (here[0] < -2 || here[1] < -2 || here[0] > nx + 1 || here[1] > ny + 1) continue;
    const match = s.crossmatch?.find((c) => c.cat !== '2MASS');
    const name = match ? `${match.cat === 'team targets.json' ? '' : match.cat + ' '}${match.id}` : 'no catalogue match';
    list.unshift({
      id: s.id, kind,
      title: KIND_LABEL[kind] + (mover && s.motion?.direction ? ` · ${s.motion.direction}` : ''),
      value: mover ? `${s.motion!.speed_arcsec_yr.toFixed(1)}″/yr` : `${Math.round(s.confidence * 100)}%`,
      sub: `${name} · ${s.class.replace('-', ' ')}`,
      x: here[0], y: here[1], r: 3.2, track: mover && ps.length > 1 ? ps : undefined,
    });
  }
  return { list, pair: [d?.from ?? 0, d?.to ?? 1], known };
}

/** SVG markers on the patch (viewBox = patch pixels; strokes stay crisp at any zoom). */
export function DetectionOverlay({ list, nx, ny, focus }: { list: Detection[]; nx: number; ny: number; focus: string | null }) {
  const bracket = (x: number, y: number, r: number) => {
    const l = r * 0.55;
    return `M${x - r},${y - r + l}V${y - r}H${x - r + l} M${x + r - l},${y - r}H${x + r}V${y - r + l} M${x + r},${y + r - l}V${y + r}H${x + r - l} M${x - r + l},${y + r}H${x - r}V${y + r - l}`;
  };
  return (
    <svg className="det-overlay" viewBox={`0 0 ${nx} ${ny}`} preserveAspectRatio="none" aria-hidden="true">
      {list.map((d) => {
        const cx = d.x + 0.5, cy = d.y + 0.5, on = focus === d.id, dim = focus && !on;
        return (
          <g key={d.id} className={`det det--${d.kind} ${on ? 'is-focus' : ''} ${dim ? 'is-dim' : ''}`}>
            {d.track && <polyline points={d.track.map((p) => `${p[0] + 0.5},${p[1] + 0.5}`).join(' ')} className="det__track" vectorEffect="non-scaling-stroke" />}
            {d.track?.map((p, i) => <circle key={i} cx={p[0] + 0.5} cy={p[1] + 0.5} r={0.35} className="det__dot" />)}
            {d.from && <line x1={d.from[0] + 0.5} y1={d.from[1] + 0.5} x2={cx} y2={cy} className="det__vec" vectorEffect="non-scaling-stroke" />}
            {d.from && <circle cx={d.from[0] + 0.5} cy={d.from[1] + 0.5} r={0.5} className="det__dot" />}
            <path d={bracket(cx, cy, on ? d.r * 1.25 : d.r)} className="det__br" vectorEffect="non-scaling-stroke" />
          </g>
        );
      })}
    </svg>
  );
}

/** Compact professional list for the card. */
export function DetectionPanel({ list, pair, known, focus, onFocus, hasReport }: {
  list: Detection[]; pair: [number, number]; known: number; focus: string | null; onFocus: (id: string | null) => void; hasReport: boolean;
}) {
  const counts = list.reduce<Record<string, number>>((a, d) => { a[d.kind] = (a[d.kind] ?? 0) + 1; return a; }, {});
  return (
    <div className="detp">
      <div className="detp__meta mono">
        <span>Visit {pair[0] + 1} → {pair[1] + 1}</span><span>threshold 5σ</span>
        {hasReport && known > 0 && <span>{known} known stars matched</span>}
      </div>
      {list.length === 0 ? (
        <p className="detp__empty">No significant change between these visits.</p>
      ) : (
        <>
          <div className="detp__chips">
            {(['mover', 'variable', 'candidate', 'moved', 'brighter', 'fainter'] as const).filter((k) => counts[k]).map((k) => (
              <span key={k} className={`detp__chip det--${k}`}><i />{counts[k]} {KIND_LABEL[k].toLowerCase()}</span>
            ))}
          </div>
          <ul className="detp__list" onMouseLeave={() => onFocus(null)}>
            {list.slice(0, 40).map((d) => (
              <li key={d.id}>
                <button className={`detp__row det--${d.kind} ${focus === d.id ? 'is-focus' : ''}`}
                  onMouseEnter={() => onFocus(d.id)} onFocus={() => onFocus(d.id)} onClick={() => onFocus(focus === d.id ? null : d.id)}>
                  <i className="detp__sw" />
                  <span className="detp__txt"><b>{d.title}</b><small>{d.sub}</small></span>
                  <span className="detp__val mono">{d.value}</span>
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
      <p className="detp__note">Change detection runs on every visit pair; moving-object linking and catalogue checks come from the discovery engine{hasReport ? '' : ' (not run for this patch)'}. Candidates, not discoveries.</p>
    </div>
  );
}
