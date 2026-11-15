import { forwardRef, useMemo, useRef, useState } from 'react';
import { parseCoords, formatDec, formatRa } from '../lib/astro';
import { matchTarget, resolveName } from '../lib/data';
import { searchTargets } from '../lib/search';
import type { Catalog } from '../lib/useCatalog';
import { KIND_LABEL, STATES } from '../copy';
import { BlinkMark } from '../components/Chrome';

export type SearchHit = { kind: 'target'; id: string } | { kind: 'coords'; ra: number; dec: number };

/**
 * The one control on the first screen. Accepts a target name / alias, decimal degrees or sexagesimal
 * (reuses parseCoords + matchTarget). Shows the demo targets as suggestions while focused.
 */
export const MapSearch = forwardRef<HTMLInputElement, { catalog: Catalog | null; onHit: (h: SearchHit) => void }>(
  function MapSearch({ catalog, onHit }, ref) {
    const [q, setQ] = useState('');
    const [open, setOpen] = useState(false);
    const [err, setErr] = useState<string | null>(null);
    const [active, setActive] = useState(-1);
    const [busy, setBusy] = useState(false);
    const lookup = useRef(0);

    const suggestions = useMemo(() => {
      if (!catalog) return [];
      const t = q.trim();
      if (!t) return catalog.index;
      if (parseCoords(t)) return [];
      return searchTargets(t, catalog.index, catalog.metas); // forgiving: case, apostrophes, word order, small typos
    }, [q, catalog]);

    const coords = parseCoords(q.trim());

    const go = (h: SearchHit) => {
      setErr(null);
      setOpen(false);
      setActive(-1);
      (document.activeElement as HTMLElement | null)?.blur();
      onHit(h);
    };

    const submit = (e: React.FormEvent) => {
      e.preventDefault();
      const text = q.trim();
      if (active >= 0 && suggestions[active]) { setQ(suggestions[active].name); go({ kind: 'target', id: suggestions[active].id }); return; }
      if (!text) return;
      if (coords) { go({ kind: 'coords', ...coords }); return; }
      if (!catalog) return;
      const hit = matchTarget(text, catalog.index, catalog.metas);
      if (hit) { setQ(hit.name); go({ kind: 'target', id: hit.id }); return; }
      // Not one of our prepared targets: ask the engine, which knows every catalogued name (CDS Sesame: SIMBAD, NED, VizieR).
      setOpen(false);
      setErr(null);
      setBusy(true);
      const ticket = ++lookup.current;
      resolveName(text).then((m) => {
        if (ticket !== lookup.current) return; // the visitor typed something else meanwhile
        setBusy(false);
        if (!m) { setErr(STATES['name-not-found'].body); return; }
        const known = m.id ? catalog.index.find((e) => e.id === m.id) : undefined;
        if (known) { setQ(known.name); go({ kind: 'target', id: known.id }); }
        else go({ kind: 'coords', ra: m.ra, dec: m.dec });
      });
    };

    const onKeyDown = (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); setActive((a) => Math.min(suggestions.length - 1, a + 1)); }
      else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((a) => Math.max(-1, a - 1)); }
      else if (e.key === 'Escape') { setOpen(false); setErr(null); (e.target as HTMLInputElement).blur(); }
    };

    const showList = open && (suggestions.length > 0 || coords);

    return (
      <form className="msearch" onSubmit={submit} role="search" onPointerDown={(e) => e.stopPropagation()}>
        <div className="msearch__box">
          <BlinkMark />
          <label htmlFor="map-search" className="sr-only">Search a star name or sky coordinates</label>
          <input
            ref={ref}
            id="map-search"
            value={q}
            onChange={(e) => { setQ(e.target.value); setErr(null); setOpen(true); setActive(-1); lookup.current++; setBusy(false); }}
            onFocus={() => setOpen(true)}
            onBlur={() => window.setTimeout(() => setOpen(false), 150)}
            onKeyDown={onKeyDown}
            placeholder="Search a star or coordinates…"
            autoComplete="off"
            spellCheck={false}
            role="combobox"
            aria-expanded={Boolean(showList)}
            aria-controls="map-search-list"
            aria-activedescendant={active >= 0 ? `ms-opt-${active}` : undefined}
            aria-describedby={err ? 'map-search-err' : undefined}
          />
          {q && <button type="button" className="msearch__clear" aria-label="Clear search" onClick={() => { setQ(''); setErr(null); }}>✕</button>}
          <button type="submit" className="msearch__go" aria-label="Search">
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" strokeWidth="2.2" /><path d="M16.5 16.5 21 21" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" /></svg>
          </button>
        </div>
        {showList && (
          <ul className="msearch__list" id="map-search-list" role="listbox">
            {coords && (
              <li role="option" aria-selected={false}>
                <button type="button" onMouseDown={(e) => e.preventDefault()} onClick={() => go({ kind: 'coords', ...coords })}>
                  <span className="msearch__name">Go to coordinates</span>
                  <span className="msearch__meta mono">{formatRa(coords.ra)} {formatDec(coords.dec)}</span>
                </button>
              </li>
            )}
            {!q.trim() && <li className="msearch__hint" aria-hidden="true">Objects with SPHEREx blinks ready</li>}
            {suggestions.map((e, i) => (
              <li key={e.id} id={`ms-opt-${i}`} role="option" aria-selected={i === active}>
                <button type="button" className={i === active ? 'is-active' : ''} onMouseDown={(ev) => ev.preventDefault()} onClick={() => { setQ(e.name); go({ kind: 'target', id: e.id }); }}>
                  <span className="msearch__dot" aria-hidden="true" />
                  <span className="msearch__name">{e.name}</span>
                  <span className="msearch__meta">{KIND_LABEL[e.kind]}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
        {busy && <p className="msearch__err" role="status">Looking up “{q.trim()}” in the star catalogues…</p>}
        {err && <p id="map-search-err" className="msearch__err" role="alert"><strong>{STATES['name-not-found'].title}.</strong> {err}</p>}
      </form>
    );
  },
);
