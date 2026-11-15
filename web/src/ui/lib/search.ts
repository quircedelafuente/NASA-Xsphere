/**
 * Forgiving name search for the target list (search box suggestions, Enter, and ?target= links).
 *
 * A query finds a target when it is close to its name, id or one of its aliases:
 *  - case, accents, apostrophes, hyphens and spaces do not matter ("BARNARDS STAR", "wise0855", "WISE-0855")
 *  - a part of the name is enough ("barnard", "draconis", "0855")
 *  - words may be in any order ("star barnard")
 *  - small typos are forgiven in words of 4+ letters ("bernard star", "r draconus"); numbers must be right
 *  - "epsilon" = "eps" = "ε"
 * Every word of the query must find a partner in the same name, so "epsilon indi a" or "north star" find nothing.
 */

export interface Named { id: string; name: string }
type Aliases = Record<string, { aliases?: string[] } | undefined>;

/** Lowest score that counts as a match (1 = exact). */
export const MIN_SCORE = 0.7;

const clean = (s: string) =>
  s
    .toLowerCase()
    .replace(/ε/g, 'eps')
    .replace(/epsilon/g, 'eps')
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '') // accents
    .replace(/['’`´]/g, ''); // Barnard's → barnards

/** Words of a name: letters and digits, split at everything else and between letters and digits ("wise0855" → wise, 0855). */
export const words = (s: string) => clean(s).match(/[a-z]+|[0-9]+/g) ?? [];
const compact = (s: string) => words(s).join('');

/** Edit distance where swapping two neighbouring letters counts as one mistake. */
function distance(a: string, b: string): number {
  const m = a.length, n = b.length;
  let prev2: number[] = [], prev = Array.from({ length: n + 1 }, (_, j) => j);
  for (let i = 1; i <= m; i++) {
    const cur = [i];
    for (let j = 1; j <= n; j++) {
      const cost = a[i - 1] === b[j - 1] ? 0 : 1;
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) cur[j] = Math.min(cur[j], prev2[j - 2] + 1);
    }
    prev2 = prev;
    prev = cur;
  }
  return prev[n];
}

/** Mistakes forgiven in a word of this length. */
const allowed = (len: number) => (len < 4 ? 0 : len < 6 ? 1 : len < 9 ? 2 : 3);

/** How well one query word fits one word of a name, 0..1. */
function wordScore(q: string, c: string): number {
  if (q === c) return 1;
  if (/^[0-9]+$/.test(q)) {
    // numbers: never "nearly right". 855 = 0855; a leading part is fine (0855 of 08551083).
    if (!/^[0-9]+$/.test(c)) return 0;
    if (q.replace(/^0+/, '') === c.replace(/^0+/, '')) return 1;
    return c.startsWith(q) || c.replace(/^0+/, '').startsWith(q.replace(/^0+/, '')) ? 0.9 : 0;
  }
  if (c.startsWith(q)) return 0.9; // "barnard" of "barnards", "dra" of "draconis"
  const max = allowed(q.length);
  if (!max) return 0;
  let best = 0;
  const full = distance(q, c);
  if (full <= max) best = 1 - full / Math.max(q.length, c.length);
  // typo in an unfinished word: compare with the start of the name's word
  for (let len = q.length - 1; len <= q.length + 1; len++) {
    if (len < 4 || len >= c.length) continue;
    const d = distance(q, c.slice(0, len));
    if (d <= max) best = Math.max(best, 0.9 * (1 - d / Math.max(q.length, len)));
  }
  return best;
}

/** How well a query fits one name, 0..1. */
export function nameScore(query: string, name: string): number {
  const qw = words(query).filter((w) => w !== 'the');
  const cw = words(name);
  if (!qw.length || !cw.length) return 0;
  const q = qw.join(''), c = cw.join('');
  if (q === c) return 1;
  let best = 0;
  if (c.startsWith(q)) best = 0.95;
  else if (q.length >= 4 && c.includes(q)) best = 0.85;
  // word by word, any order: each query word needs a partner
  let sum = 0;
  for (const w of qw) {
    let s = 0;
    for (const x of cw) s = Math.max(s, wordScore(w, x));
    sum += s;
  }
  best = Math.max(best, (sum / qw.length) * 0.99); // just under an exact match
  // one long word typed without its spaces ("barnardstar", "rwaurigea"). Not for several words: there each word
  // must fit on its own, or "epsilon indi a" and "rs aurigae" would pass as near misses.
  if (qw.length === 1 && q.length >= 5) {
    const d = distance(q, c);
    if (d <= allowed(q.length)) best = Math.max(best, 0.9 * (1 - d / Math.max(q.length, c.length)));
  }
  return best;
}

/** Targets that fit the query, best first (ties keep the list order). */
export function searchTargets<T extends Named>(query: string, index: T[], metas: Aliases = {}): T[] {
  if (!compact(query)) return [];
  return index
    .map((e, i) => ({ e, i, s: Math.max(...[e.id, e.name, ...(metas[e.id]?.aliases ?? [])].map((n) => nameScore(query, n))) }))
    .filter((x) => x.s >= MIN_SCORE)
    .sort((a, b) => b.s - a.s || a.i - b.i)
    .map((x) => x.e);
}
