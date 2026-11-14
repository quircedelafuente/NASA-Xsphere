/**
 * Lazy loader for Aladin Lite v3 (CDS), pinned to an exact npm release on jsDelivr.
 * The old "api/v3/latest/aladin.js" URL on the CDS server returns 404 (checked 14 Nov 2026).
 * The package is an ES module, so it is loaded with a dynamic import — only when first needed.
 */
export const ALADIN_SRC = 'https://cdn.jsdelivr.net/npm/aladin-lite@3.8.2/dist/aladin.js';

// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare global { interface Window { A?: any } }

// eslint-disable-next-line @typescript-eslint/no-explicit-any
let loader: Promise<any> | null = null;

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function loadAladin(): Promise<any> {
  if (window.A) return Promise.resolve(window.A);
  if (!loader) {
    loader = import(/* @vite-ignore */ ALADIN_SRC)
      .then(async (m) => {
        const A = m.default;
        await A.init;
        window.A = A;
        return A;
      })
      .catch((e) => {
        loader = null;
        throw e;
      });
  }
  return loader;
}

/**
 * HiPS survey shown when zooming in: DSS2 colour (optical), tried on several mirrors in order.
 * Checked 14 Nov 2026: the CDS alasky copies returned 404 and the IRSA mirror worked. IRSA's 2MASS colour
 * tiles showed bright green blocks around WISE 0855, so DSS2 is used as the default.
 */
export const HIPS_MIRRORS = [
  'https://irsa.ipac.caltech.edu/data/hips/CDS/DSS2/color',
  'https://alasky.cds.unistra.fr/DSS/DSSColor',
  'https://irsa.ipac.caltech.edu/data/hips/CDS/2MASS/Color',
];
export const HIPS_CREDIT = 'DSS2';

/** First mirror whose `properties` file answers, or null if none does (offline, blocked…). */
export async function pickHips(): Promise<string | null> {
  for (const base of HIPS_MIRRORS) {
    try {
      const ctl = new AbortController();
      const t = window.setTimeout(() => ctl.abort(), 6000);
      const r = await fetch(`${base}/properties`, { signal: ctl.signal });
      window.clearTimeout(t);
      if (r.ok) return base;
    } catch { /* try the next mirror */ }
  }
  return null;
}
