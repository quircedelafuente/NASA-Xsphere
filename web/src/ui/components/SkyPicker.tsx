/**
 * "Click on the sky" picker using Aladin Lite v3 (CDS), loaded lazily from the CDN only when the tab opens.
 * Docs: https://aladin.cds.unistra.fr/AladinLite/doc/API
 */
import { useEffect, useRef, useState } from 'react';
import { navigate } from '../lib/router';
import { viewUrl } from '../lib/url';
import type { Catalog } from '../lib/useCatalog';
import { formatDec, formatRa } from '../lib/astro';

import { loadAladin } from '../map/aladin';

export function SkyPicker({ catalog }: { catalog: Catalog | null }) {
  const ref = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [picked, setPicked] = useState<{ ra: number; dec: number } | null>(null);

  useEffect(() => {
    let alive = true;
    loadAladin()
      .then(() => {
        if (!alive || !ref.current) return;
        const a = window.A.aladin(ref.current, {
          survey: 'P/allWISE/color', fov: 180, target: '0 0', projection: 'AIT',
          showReticle: true, showZoomControl: true, showLayersControl: false, showFullscreenControl: false,
          showGotoControl: false, showFrame: false, cooFrame: 'ICRS',
        });
        if (catalog) {
          const cat = window.A.catalog({ name: 'Demo targets', sourceSize: 14, color: '#f0e442', onClick: 'showPopup' });
          a.addCatalog(cat);
          cat.addSources(Object.values(catalog.metas).map((m) =>
            window.A.marker(m.ra_deg, m.dec_deg, { popupTitle: m.name, popupDesc: `<a href="${viewUrl({ target: m.id })}">Open in the blink viewer →</a>` })));
        }
        a.on('click', (e: { ra: number; dec: number }) => { if (e && Number.isFinite(e.ra)) setPicked({ ra: e.ra, dec: e.dec }); });
        setStatus('ready');
      })
      .catch(() => alive && setStatus('error'));
    return () => { alive = false; };
  }, [catalog]);

  return (
    <div className="sky">
      <div ref={ref} className="sky__map" aria-label="Interactive all-sky map (Aladin Lite)" />
      {status === 'loading' && <p className="sky__status">Loading the sky map…</p>}
      {status === 'error' && <p className="sky__status">The sky map couldn’t load (it needs the Aladin service). The search box and demo targets above still work.</p>}
      {picked && (
        <div className="sky__picked">
          <span className="mono">{formatRa(picked.ra)} {formatDec(picked.dec)}</span>
          <button onClick={() => navigate(viewUrl({ ra: picked.ra, dec: picked.dec }))}>Blink this spot</button>
        </div>
      )}
    </div>
  );
}
