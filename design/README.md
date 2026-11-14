# Design — U0 (owner: Niklas)

Breadboard, URL scheme (C5), states and the name. The running shell in `web/` *is* the wireframe:
screenshots of every screen and state are in [`screens/`](screens/). They use the mock bundle, so the images are simulated.

## 1. Name & tagline (decide by H+2)

| Option | Tagline | Notes |
|---|---|---|
| **SPHEREx Blink** ← current placeholder | *Watch the infrared sky move.* | Says what it does and which data. Fine to use the mission name in text, but **no mission logo** (D15). |
| Planet X Finder | *Spot what moves.* | Matches the challenge title, but suggests we find planets. Judges may call it overclaiming (D13). |
| Blinkwise | *Your browser is a blink comparator.* | Nods to WiseView, but too close to it in name. |

Changing it is one line: `PRODUCT` in `web/src/ui/copy.ts` plus `<title>` in `web/index.html`.

**✅ Decided (Niklas, Sat 14 Nov): SPHEREx Blink** · *Watch the infrared sky move.* It says what it does and which data, and it doesn't overclaim. Team to be told by H+2 (17:00).

## 2. Persona & core flow

- **Primary user:** a curious non-expert (student, amateur astronomer) who arrives from a shared link.
- **Secondary user:** a Backyard-Worlds-style power user. Everything expert sits in **More → Advanced**.

### 2a. Map-first flow (current, what `/` runs)

```
MAP  /                     dark sky · Milky Way · bright stars + constellation lines · 5 glowing markers · one search box
  [intro card] → Take the 60-second tour (?tour=1) | Explore on my own
  [search: name | decimal | sexagesimal] ─► fly to the target (or to the coordinates)
  [click a marker / zoom in] ─────────────► fly to the patch
      fov 30°→4°   simplified map fades into real survey imagery (Aladin Lite v3 / HiPS, loaded lazily)
      fov ≤ 1.5°   PATCH OPENS → only now download that target's SPHEREx frames ("Loading this patch…")
                   → blink plays in place on the map + FLOATING CARD
                        name · one-liner · Look for (+ Show me) · ▶/❚❚ · Blink | Difference · Short/Mid/Long colour · share
                        [More] → At a glance · Playback · Bands · Spectrum/light curve · Share/embed · Flag a candidate · Advanced
      fov > 3°     patch closes, blink stops, back to the map
      fov ≤ 1° with no target → "Not processed yet" (+ nearest target, IRSA link)
  URL follows the view: ?target=… &mode &band … &view=ra,dec,fov  (old C5 links open the same view on the map)

EMBED  /embed?…             unchanged minimal viewer (canvas + play + mode + "Open in SPHEREx Blink ↗")
```

**Message for Quirce (decider) and Giorgi (viewer). Copy and paste:**
> The main page is now a sky map instead of landing → viewer (this changes D1/C5). Every C5 param still works and old `?target=` / `?ra=&dec=` links open the same view on the map. `/embed` is unchanged. The only new param is UI-only, `view=ra,dec,fov` (the map camera). Frames are fetched only when a patch opens, so `<BlinkCanvas>` C6 props are unchanged. OK with you?

**FOV presets (2′/5′/10′, from the role file):** these are not built on purpose. The precomputed bundles are a fixed 64×64 px × 6.15″ ≈ 6.6′ cutout, so a preset could only crop. Map zoom already does that. Add presets only if the live backend (P6) comes back.

### 2b. Original landing → viewer breadboard (still used by `/embed`; `Landing.tsx` kept for reference)

```
LANDING  /
  [search box: name | decimal | sexagesimal] ──────────► VIEWER ?target= | ?ra=&dec=
  [5 demo target cards] ───────────────────────────────► VIEWER ?target=<id>
  [tab: Click on the sky (Aladin Lite)] → [Blink this spot] ► VIEWER ?ra=&dec=
  [Take the 2-minute tour] ────────────────────────────► VIEWER ?target=barnards-star&tour=1

VIEWER  /?target=…  (auto-plays at 1 fps, crosshair + date + λ on every frame)
  stage:   canvas · epoch strip · ‹ ▶ › · speed (≤ 2/s) · zoom
           mode: Blink | Difference | Side by side
           band chips: D1…D6 + "3.8–5 µm · where cold brown dwarfs glow"
           actions: Spectrum · Share/embed · Flag a candidate
           Advanced ▸ stretch · brightness limit · invert · problem pixels · crosshair · track · visits in loop
  side:    What am I seeing? → kind · one-liner · visit/date/λ · motion sentence · look for · best band
           · facts (C7) · where it used to be (archival) · problem-pixel legend (C3) · about this data
  tour:    3 cards per target (what it is → what to look for → did you see it?) → Next object
  keys:    Space · ← → · B / D / S · + −

EMBED  /embed?…   canvas + play + mode + "Open in SPHEREx Blink ↗"
```

## 3. C5 · URL scheme — PROPOSED, confirm with Giorgi

Exactly as in CONTRACTS.md C5, plus three optional UI-only params. Implementation: `web/src/ui/lib/url.ts`.

| Param | Values | Default | Notes |
|---|---|---|---|
| `target` | id from `index.json`, or any alias | — | Aliases are resolved and the URL is rewritten to the id |
| `ra`, `dec` | decimal deg (ICRS) | — | Within 3.6′ of a processed target → that target; otherwise the `live-not-available` state |
| `fov` | arcsec | 394 | Reserved for the live mode |
| `band` | `D1…D6`, `D56`, `ALL`, `mol-*` | target's `default_band` | |
| `mode` | `blink` · `diff` · `side` | `blink` (`side` if prefers-reduced-motion) | |
| `speed` | 0.25–2 fps | 1 | Capped at 2 (WCAG 2.3.1) |
| `frame` | int | 0 | Only written while paused |
| `stretch` | `asinh:<a>` | from the manifest | |
| `overlay` | comma list of `crosshair,track,flags,gaia` | `crosshair,track,flags` | |
| `zoom` | 2–14 | 8 | *UI extra* |
| `tour` | `1` | — | *UI extra*: opens the guided tour |
| `view` | `ra,dec,fov` (deg) | — | *UI extra (map-first)*: sky-map camera, so a shared link opens at the same zoom |

## 4. States (C5) → screens

| State | Trigger | Screen |
|---|---|---|
| `loading` | fetching the manifest/frames | grey square + "Fetching the sky…" |
| `ok` | ≥ 3 epochs | normal viewer |
| `two-epochs` | 2 frames | info card: blink + diff work, the track is a straight line |
| `one-epoch` | 1 frame | "Only one visit so far — come back after the next pass", playback disabled |
| `no-coverage` | `n_epochs: 0` in index.json, or a manifest with 0 frames | the map card shows "No SPHEREx images here yet" and no frames are fetched. **Processing: please emit `n_epochs: 0`** |
| `saturated-target` | `expected.saturated` + `OVERFLOW` at the target | info card suggesting Difference / D6 |
| `name-not-found` | unknown name | inline error under the search box, or a card plus target cards |
| `live-not-available` | coordinates far from every processed target | card plus IRSA link plus target cards (`screens/coords.png`) |

## 5. Visual rules
- Dark UI with **one accent** (`#56B4E9`). Crosshair is yellow `#F0E442`, problem pixels are orange `#E69F00`. All three are from the Okabe–Ito colour-blind-safe palette. No red–green.
- Greyscale frames, nearest-neighbour zoom (square pixels), and the same stretch for the whole sequence.
- Blink ≤ 2 Hz. `prefers-reduced-motion` → starts paused in Side-by-side. The motion sentence is the text alternative.
- Monospace for every number (coordinates, dates, λ).
- No NASA logos. Our mark is two offset dots (a "blink").

## 6. What I need from others
- **Giorgi:** `<BlinkCanvas>` with C6 props. The shell also passes optional `frames`, `onFrameChange`, `invert` and `excludeEpochs`; keep or drop them, but please tell me. To swap in yours, edit one line in `web/src/ui/viewer.ts`. Please also add `nx`/`ny` to the manifest (C4 example omits them).
- **Quirce:** a way to see 0-epoch targets in `index.json` (for the `no-coverage` state).
- **Sean/Yasen:** the full, line-by-line list is in [`needs-from-data.md`](needs-from-data.md). `science-notes.md` (C7). Every fact in `copy.ts` is marked `verify: true` until it's replaced. `flags.json` `plain` texts (C3). `bands.json` names for the band chips.
