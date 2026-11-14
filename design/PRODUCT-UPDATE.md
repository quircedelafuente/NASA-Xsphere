# Product update — Role 3 (Niklas) · Sat 14 Nov 2026

Status of the product scopes (U0–U10 in `roles/03-product.md`), with the decisions the team needs to know about.

## 1. Decisions

| Decision | Choice | Class |
|---|---|---|
| **Name & tagline** | **SPHEREx Blink** · *Watch the infrared sky move.* | Autonomous (H+2) |
| **Primary persona** | Curious non-expert arriving from a shared link. Expert controls live in More → Advanced | Autonomous |
| **Core flow** | **Map-first** (replaces landing → viewer). See section 2 | Team-lock (D1/C5): **needs OK from Quirce and Giorgi** |
| **FOV presets 2′/5′/10′** | Not built. Bundles are a fixed 64×64 px × 6.15″ ≈ 6.6′ cutout, so a preset could only crop; map zoom already does that. Revisit only if live mode (P6) returns | Autonomous |

## 2. Map-first core flow (for Quirce and Giorgi)

The main page is now a simplified sky map: dark sky, Milky Way, bright stars, constellation lines, 5 glowing target markers and one search box.

1. Search for a target or click a marker → the map flies there.
2. Between 30° and 4° field of view, the map fades into real survey imagery (Aladin Lite v3 / HiPS, loaded lazily).
3. At ≤ 1.5°, the patch opens. **Only then** are that target's SPHEREx frames downloaded. The blink plays in place on the map with a small floating card (name, one-liner, Look for, play/pause, Blink | Difference, Short/Mid/Long colour, share, More).
4. Zooming out past 3° closes the patch and returns to the map. An empty area shows "Not processed yet".

What stays the same:
- Every C5 parameter still works. Old `?target=` and `?ra=&dec=` links open the same view on the map.
- `/embed` is unchanged.
- `<BlinkCanvas>` C6 props are unchanged.
- The only new parameter is UI-only: `view=ra,dec,fov` (the map camera, in degrees).

## 3. Scope status

| Scope | Status |
|---|---|
| U0 Breadboard, URL scheme, name | ✅ `design/README.md` (map-first + C5 table) |
| U1 Shell, search, sky map | ✅ map-first |
| U2 Viewer controls + URL state | ✅ play/pause, speed ≤ 2 fps, frames, bands incl. D56, Blink/Difference/Side, zoom, Advanced, keyboard |
| U3 Explain layer + states | ✅ incl. `no-coverage` (`n_epochs: 0` → "No SPHEREx images here yet") |
| U4 Guided tour | ✅ 5 targets, 3 cards each |
| U5 Spectrum panel | ✅ on the stub chart, waiting for the real `<SpectrumChart>` |
| U6 Share / embed / OG image | ✅ `public/og.png` 1200×630 |
| U7 Flag a candidate | ✅ never says "discovery" |
| U8 λ slider | ⏸ optional, only if everything else is green |
| U9 Submission | 📝 drafts in `submission/` (map flow). Facts waiting for C7 |
| U10 Deploy (Vercel) | ⏳ not deployed yet |

## 4. What I need from the team

- **Quirce / Giorgi:** OK on the map-first flow (section 2).
- **Giorgi:** the real `<BlinkCanvas>` / `<SpectrumChart>`. The swap is one file, `web/src/ui/viewer.ts`. Please also add `nx`/`ny` to the manifest.
- **Quirce:** `n_epochs` per target in `index.json` (0 → no-coverage state). The release list for "NASA data used".
- **Yasen / Sean:** confirm every fact line by line in `design/needs-from-data.md` (C7), plus the `flags.json` plain texts (C3) and `bands.json` names.

## 5. Next deadlines

| When | What |
|---|---|
| H+3 (18:00 Sat) | Facts list to Data ✅ (`design/needs-from-data.md`) |
| H+6 (21:00 Sat, CP1) | First real bundle running in the shell |
| Sun 10:00 (CP2) | All flows on real data for the 5 targets |
| Sun 12:00 | Video script frozen |
| Sun 16:00 | Freeze: deployed, tested on 2 browsers and a phone |
| **Sun 22:00** | **Submitted** |
