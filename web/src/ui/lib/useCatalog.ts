import { useEffect, useState } from 'react';
import type { IndexEntry, TargetMeta } from './contracts';
import { isMock, loadIndex, loadMeta } from './data';

export interface Catalog {
  index: IndexEntry[];
  metas: Record<string, TargetMeta>;
  mock: boolean;
}

let cache: Promise<Catalog> | null = null;

export function getCatalog(): Promise<Catalog> {
  if (!cache) {
    cache = (async () => {
      const index = await loadIndex();
      const metaList = await Promise.all(index.map((e) => loadMeta(e.id).catch(() => null)));
      const metas: Record<string, TargetMeta> = {};
      metaList.forEach((m) => { if (m) metas[m.id] = m; });
      return { index, metas, mock: await isMock() };
    })();
  }
  return cache;
}

export function useCatalog(): Catalog | null {
  const [cat, setCat] = useState<Catalog | null>(null);
  useEffect(() => {
    let alive = true;
    getCatalog().then((c) => alive && setCat(c));
    return () => { alive = false; };
  }, []);
  return cat;
}
