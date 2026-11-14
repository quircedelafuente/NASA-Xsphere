import { useLocation } from '../ui/lib/router';
import { parseUrl } from '../ui/lib/url';
import { Landing } from './Landing';
import { Viewer } from './Viewer';
import { SkyMap } from './SkyMap';

/**
 * "/"       → map-first experience (SkyMap). Old C5 links (?target=…, ?ra=&dec=) open the same view on the map.
 * "/embed"  → unchanged minimal Viewer, so existing embed snippets keep working.
 * Landing.tsx is kept for reference but no longer routed.
 */
export function App() {
  const loc = useLocation();
  const state = parseUrl(loc);
  const hasView = Boolean(state.target || (state.ra !== undefined && state.dec !== undefined));

  if (state.embed) return hasView ? <Viewer key={state.target ?? `${state.ra},${state.dec}`} state={state} embed /> : <Landing embed />;
  return <SkyMap loc={loc.pathname + loc.search} />;
}
