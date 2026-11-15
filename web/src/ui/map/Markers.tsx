/**
 * Target markers on the map patch, drawn in SCREEN pixels (not the 8× canvas), so lines stay ~1.5 px and
 * dots/arrows keep their size at every zoom. Every marker has a dark halo under an Okabe–Ito colour, a distinct
 * shape, and a hover tooltip. The same shapes appear in <MarkerLegend> on the card.
 *   ＋ yellow crosshair  = where the catalogue says the target is at this visit
 *   •→ white dots + arrow = the target's position at each visit, first → last (yellow ring = this visit)
 *   (white, not blue: the no-data mask is sky blue or orange, see lib/palette maskRgb)
 *   ◯ blue circles      = Gaia DR3 stars, moved to this visit's date
 *   □ orange squares    = AllWISE sources, where WISE saw them (~2010)
 */
import { useLayoutEffect, useRef, useState, type ReactElement } from 'react';
import type { GaiaJson, Manifest } from '../lib/contracts';
import { skyToPixel, formatMjdLong } from '../lib/astro';

export const MK = { cross: '#f0e442', track: '#ffffff', gaia: '#56b4e9', wise: '#e69f00' };

/** A path is only worth drawing when the target actually moves (a variable star's dots sit on one spot). */
export const trackMoves = (m: Manifest) => {
  const t = m.target_track ?? [];
  return t.length > 1 && Math.hypot(t[t.length - 1].x - t[0].x, t[t.length - 1].y - t[0].y) > 0.3;
};

type Show = { crosshair: boolean; track: boolean; gaia: GaiaJson | null; wise: GaiaJson | null };

export function MarkerOverlay({ manifest, frame, show }: { manifest: Manifest; frame: number; show: Show }) {
  const ref = useRef<SVGSVGElement>(null);
  const [size, setSize] = useState(0);
  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    setSize(el.getBoundingClientRect().width);
    const ro = new ResizeObserver(([e]) => setSize(e.contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const nx = manifest.nx ?? 64, ny = manifest.ny ?? nx;
  const s = size / nx;   // screen px per SPHEREx pixel
  const P = (x: number, y: number) => [(x + 0.5) * s, (y + 0.5) * s] as const;
  const f = manifest.frames[frame];
  const tp = f?.target_px;
  const tr = manifest.target_track ?? [];

  const cat = (rows: GaiaJson['sources'] | GaiaJson['wise'] | undefined, refEpoch: number) => {
    if (!rows || !manifest.wcs || !f) return [];
    const yrs = 2000 + (f.mjd - 51544.5) / 365.25 - refEpoch;
    return rows.flatMap((r) => {
      const dec = r.dec_deg + (r.pmdec_masyr * yrs) / 3.6e6;
      const ra = r.ra_deg + (r.pmra_masyr * yrs) / 3.6e6 / Math.cos((dec * Math.PI) / 180);
      const q = skyToPixel(manifest.wcs!, ra, dec, ny);
      return q.x < -1 || q.y < -1 || q.x > nx || q.y > ny ? [] : [P(q.x, q.y)];
    });
  };
  const rc = Math.max(5, s * 0.9);

  let arrow = '';
  if (tr.length > 1) {
    const [x1, y1] = P(tr[tr.length - 1].x, tr[tr.length - 1].y), [x0, y0] = P(tr[tr.length - 2].x, tr[tr.length - 2].y);
    const len = Math.hypot(x1 - x0, y1 - y0);
    if (len > 3) {   // arrowhead at the last visit, pointing along the motion
      const ux = (x1 - x0) / len, uy = (y1 - y0) / len, a = 7, w = 4;
      const tx = x1 + ux * 4, ty = y1 + uy * 4;
      arrow = `M${tx},${ty}L${tx - ux * a - uy * w},${ty - uy * a + ux * w}L${tx - ux * a + uy * w},${ty - uy * a - ux * w}Z`;
    }
  }

  return (
    <svg ref={ref} className="mk-overlay" viewBox={`0 0 ${size || 1} ${size || 1}`} aria-hidden="true">
      {size > 60 && (
        <>
          {show.gaia && (
            <g className="mk mk--gaia" style={{ ['--k' as string]: MK.gaia }}>
              <title>Gaia DR3 star, moved to this visit's date by its measured motion</title>
              {cat(show.gaia.sources, show.gaia.ref_epoch ?? 2016).map(([x, y], i) => <circle key={i} cx={x} cy={y} r={rc} />)}
            </g>
          )}
          {show.wise && (
            <g className="mk mk--wise" style={{ ['--k' as string]: MK.wise }}>
              <title>AllWISE source, where WISE saw it around 2010 (a moving star sits away from its square)</title>
              {cat(show.wise.wise, show.wise.ref_epoch_wise ?? 2010.5).map(([x, y], i) => <rect key={i} x={x - rc} y={y - rc} width={2 * rc} height={2 * rc} />)}
            </g>
          )}
          {show.crosshair && tp && (() => {
            const [X, Y] = P(tp[0], tp[1]), g = Math.max(9, s * 2.2), L = g + Math.max(9, s * 2.8);
            return (
              <g className="mk mk--cross" style={{ ['--k' as string]: MK.cross }}>
                <title>Expected position at this visit (from the star's catalogue motion)</title>
                <path d={`M${X - L},${Y}H${X - g}M${X + g},${Y}H${X + L}M${X},${Y - L}V${Y - g}M${X},${Y + g}V${Y + L}`} />
                <path className="mk__hit" d={`M${X - L},${Y}H${X - g}M${X + g},${Y}H${X + L}M${X},${Y - L}V${Y - g}M${X},${Y + g}V${Y + L}`} />
              </g>
            );
          })()}
          {show.track && trackMoves(manifest) && (
            <g className="mk mk--track" style={{ ['--k' as string]: MK.track }}>
              <title>{`Path across visits: ${formatMjdLong(tr[0].mjd)} → ${formatMjdLong(tr[tr.length - 1].mjd)} (ring = each visit, yellow = this visit, arrow = direction of motion)`}</title>
              <polyline points={tr.map((t) => P(t.x, t.y).join(',')).join(' ')} />
              <polyline className="mk__hit" points={tr.map((t) => P(t.x, t.y).join(',')).join(' ')} />
              {arrow && <path className="mk__arrow" d={arrow} />}
              {tr.map((t, i) => {
                const [x, y] = P(t.x, t.y);
                return <circle key={i} className={i === frame ? 'mk__now' : 'mk__dot'} cx={x} cy={y} r={i === frame ? 3.5 : 2.5} />;
              })}
            </g>
          )}
        </>
      )}
    </svg>
  );
}

/** One-line key for the markers currently on the patch (shapes match the overlay). */
export function MarkerLegend({ crosshair, track, gaia, wise, firstFrame, mask }: { crosshair: boolean; track: boolean; gaia: boolean; wise: boolean; firstFrame: boolean; mask: string | null }) {
  const items: [string, ReactElement][] = [];
  const sw = (d: ReactElement) => <svg width="16" height="12" viewBox="0 0 16 12" aria-hidden="true">{d}</svg>;
  if (crosshair) items.push(['Expected position', sw(<path d="M8 0V4M8 8V12M2 6H6M10 6H14" stroke={MK.cross} strokeWidth="1.6" />)]);
  if (track) items.push(['Path, visit 1 → last', sw(<><path d="M1 9L12 3" stroke={MK.track} strokeWidth="1.3" /><circle cx="2" cy="8.5" r="1.8" fill={MK.track} stroke="#000" strokeWidth=".8" /><path d="M15 1.5L9.5 2.5L12 6.5Z" fill={MK.track} /></>)]);
  if (gaia) items.push(['Gaia star', sw(<circle cx="8" cy="6" r="4.5" fill="none" stroke={MK.gaia} strokeWidth="1.4" />)]);
  if (wise) items.push(['WISE source (2010)', sw(<rect x="3.5" y="1.5" width="9" height="9" fill="none" stroke={MK.wise} strokeWidth="1.4" />)]);
  if (mask) items.push(['No usable data (e.g. saturated)', sw(<rect x="4" y="2" width="8" height="8" fill={mask} />)]);
  if (firstFrame) items.push(['Dashed border = first visit of the loop', sw(<path d="M1 6H5M7 6H11M13 6H15" stroke="#fff" strokeWidth="1.4" />)]);
  if (!items.length) return null;
  return (
    <ul className="mlegend small" aria-label="Map key">
      {items.map(([t, i]) => <li key={t}>{i}{t}</li>)}
    </ul>
  );
}
