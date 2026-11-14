# web/ — SPHEREx Blink front end (Vite + React + TypeScript)

```bash
cd web
npm install
npm run dev        # http://localhost:5173
npm run build      # type-check + production build in dist/
```

Deploy (U10): import the repo into Vercel and set **Root Directory = `web`**. `vercel.json` rewrites `/embed` to the SPA.

## Who owns what (D16)
| Path | Owner |
|---|---|
| `src/ui/`, `src/pages/`, `src/styles/`, `package.json`, `index.html`, `vercel.json` | Niklas |
| `src/viewer/`, `src/data/`, `public/bundles/` | Processing (Giorgi / Quirce) |

## Mock mode
If `public/bundles/index.json` is missing, the UI uses an in-memory mock (`src/ui/mock/mockBundle.ts`): five targets with simulated frames, tracks and spectra. An orange banner shows while it is active. As soon as Processing commits real bundles (C4), the UI uses them automatically.

## Swapping in the real viewer
`src/ui/viewer.ts` is the only place the UI imports `<BlinkCanvas>` / `<SpectrumChart>` from. Point it at `../viewer/…` when P5 lands.
The stubs in `src/ui/stubs/` follow C6 and can be deleted after that.

## Files
- `src/ui/lib/url.ts` — C5 URL scheme (parse/write)
- `src/ui/lib/contracts.ts` — TS types for C1/C3/C4/C6
- `src/ui/lib/palette.ts` — false colour of the frames (tint by wavelength; `?palette=grey` or Advanced → “Colour by wavelength” turns it off). Mirror of `processing/palette.py`
- `src/ui/lib/smooth.ts` — optional display smoothing of the square pixels (Advanced → “Smooth pixels”, or `?smooth=1`). Off by default: decision D7 keeps nearest-neighbour
- `src/ui/lib/data.ts` — bundle loading + mock fallback, name/coordinate resolution
- `src/ui/copy.ts` — **all UI text**; target facts are placeholders until C7 lands
- `src/pages/Landing.tsx`, `src/pages/Viewer.tsx` — the two screens (+ `/embed`)
