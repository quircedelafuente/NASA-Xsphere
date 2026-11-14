import { useState } from 'react';
import { parseCoords } from '../lib/astro';
import { matchTarget } from '../lib/data';
import { navigate } from '../lib/router';
import { viewUrl } from '../lib/url';
import type { Catalog } from '../lib/useCatalog';
import { STATES } from '../copy';

/** One tolerant box: target name / alias, decimal degrees, or sexagesimal (WiseView-style). */
export function SearchBox({ catalog, compact, embed }: { catalog: Catalog | null; compact?: boolean; embed?: boolean }) {
  const [q, setQ] = useState('');
  const [err, setErr] = useState<string | null>(null);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = q.trim();
    if (!text) return;
    const c = parseCoords(text);
    if (c) {
      setErr(null);
      navigate(viewUrl({ ra: c.ra, dec: c.dec }, { embed }));
      return;
    }
    if (!catalog) return;
    const hit = matchTarget(text, catalog.index, catalog.metas);
    if (hit) {
      setErr(null);
      navigate(viewUrl({ target: hit.id }, { embed }));
    } else {
      setErr(STATES['name-not-found'].body);
    }
  };

  return (
    <form className={`search ${compact ? 'search--compact' : ''}`} onSubmit={submit} role="search">
      <label htmlFor="sky-search" className="sr-only">Star name or sky coordinates</label>
      <input
        id="sky-search"
        value={q}
        onChange={(e) => { setQ(e.target.value); setErr(null); }}
        placeholder={compact ? 'Name or RA Dec…' : 'Try “Barnard’s Star”, “269.45 4.74” or “08h55m10.8s −7d14m42s”'}
        autoComplete="off"
        spellCheck={false}
        aria-describedby={err ? 'search-err' : undefined}
      />
      <button type="submit">{compact ? 'Go' : 'Show me'}</button>
      {err && <p id="search-err" className="search__err" role="alert"><strong>{STATES['name-not-found'].title}.</strong> {err}</p>}
    </form>
  );
}
