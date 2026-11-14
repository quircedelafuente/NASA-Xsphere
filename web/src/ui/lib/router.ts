/** Tiny pushState router — enough for "/" and "/embed" plus query params (C5). */
import { useEffect, useState } from 'react';

type Loc = { pathname: string; search: string };
const listeners = new Set<() => void>();

function current(): Loc {
  return { pathname: window.location.pathname, search: window.location.search };
}

export function navigate(url: string, opts: { replace?: boolean } = {}) {
  if (url === window.location.pathname + window.location.search) return;
  if (opts.replace) window.history.replaceState(null, '', url);
  else window.history.pushState(null, '', url);
  listeners.forEach((l) => l());
}

export function useLocation(): Loc {
  const [loc, setLoc] = useState<Loc>(current);
  useEffect(() => {
    const update = () => setLoc(current());
    listeners.add(update);
    window.addEventListener('popstate', update);
    return () => {
      listeners.delete(update);
      window.removeEventListener('popstate', update);
    };
  }, []);
  return loc;
}
