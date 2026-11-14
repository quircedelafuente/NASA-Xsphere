# What Product needs from Data (feeds C7) — H+3 output

Owner: Niklas → for **Yasen / Sean** (science notes, C7) and **Quirce / Giorgi** (bundles, C4).
Every number or fact the site or the video shows is listed here. The UI text lives in `web/src/ui/copy.ts`; items there marked `verify: true` stay until they are confirmed.
Please reply per line with **✅ value + source**, a **corrected value + source**, or **❌ drop it**.

## 1. Per target (`TARGET_COPY` in `copy.ts`)

| Target | Claim in the UI / tour | Need |
|---|---|---|
| Barnard's Star | ~6 light-years away | distance + source |
| | Fastest apparent motion of any star, ~10″/yr | pm (″/yr) + PA |
| | Saturates the SPHEREx detector at its centre | Is `OVERFLOW` set at the target in our bundle? In which bands? |
| | "Shifts a pixel or two to the north between visits"; tour: "hop north" | direction + px between our epochs (6.15″/px) |
| ε Indi B | A pair of brown dwarfs orbiting ε Indi A | confirm wording (Ba/Bb) |
| | ~12 light-years away | distance + source |
| | Moves "several arcseconds a year" | pm (″/yr); research note says ≈ 4.7″/yr *to verify* |
| | Best band 3.8–5 µm | confirm `default_band` = D56 |
| WISE 0855−0714 | ~7 light-years away | distance + source |
| | "Near the temperature of a freezer", "colder than the North Pole in winter" | T_eff (K) + source; we'll drop the comparison if it doesn't hold |
| | Found in 2014 | discovery paper (Luhman 2014?) |
| | Invisible in short bands, visible only at 3.8–5 µm | Does our bundle show it? (D1 empty, D56 detected) |
| | pm ≈ 8.15″/yr (arXiv 1605.08620) | confirm |
| | "Check its spectrum for water and methane" | Does our SPHEREx spectrum actually show H₂O / CH₄? If not, the tour line and video shot 0:18–0:22 are cut |
| RW Aurigae | Young star system, still has its disc, "a few million years old" | age + source |
| | Dims/brightens irregularly from dust | source |
| | No noticeable motion | confirm pm is small at 6.15″/px |
| R Draconis | Mira variable, period "roughly 8 months" | period (days) + source |
| | Near the north ecliptic pole, visited about monthly | number of epochs in our bundle |
| | "Best light curve of the five" | confirm epoch count |

For every mover we also need **`archival_positions`** in `meta.json` (survey, epoch, RA/Dec). They feed the "then vs now" sentence and the yellow ring on the map.

## 2. Mission facts (`ABOUT.facts`, landing intro, video)

| Claim | Where | Need |
|---|---|---|
| Launched March 2025 | About, video 0:04 | source (JPL) |
| Maps the whole sky every six months | intro, About, video | confirm wording (4 maps in 2 years) |
| 102 colours = 6 detectors × 17 bands, 0.75–5 µm | intro, About, video | ✅ JPL + IRSA docs (in research), just confirm |
| 6.15″ per pixel | About | ✅ IRSA data-products page |
| Tombaugh found Pluto by blinking two plates (1930) | intro, video 0:00 | ✅ Britannica: 18 Feb 1930, plates six days apart |
| Volunteers found thousands of brown dwarfs by blinking | ε Indi B tour, video | number: 3,006 L/T candidates (arXiv 2604.01323) — confirm the wording "candidates" |
| SPHEREx spectra of 6,003 ultracool dwarfs, 947 new (arXiv 2604.22012) | project texts | confirm before using |

## 3. From Processing (bundles, C4)

- `index.json`: `n_epochs` per target (0 → the site now shows "No SPHEREx images here yet").
- `manifest.json`: `nx`/`ny` (the UI assumes 64×64 if they are missing).
- `flags.json` with a `plain` sentence per flag (C3). Until then the UI uses `FLAG_LEGEND_FALLBACK` (OVERFLOW / SOURCE / BLOOM).
- `bands.json` names for the band chips.
- The release list for the "NASA data used" section (`spherex_dr1`, `…_deep`, `qr3`, `…_deep`?).

## 4. UI component and copy inventory (for Giorgi)

| Component | File | Uses |
|---|---|---|
| Sky map, flight, patch, floating card | `src/pages/SkyMap.tsx`, `src/ui/map/*` | catalog (C1/C4), `<BlinkCanvas>` |
| Blink canvas | `src/ui/viewer.ts` → stub, later `../viewer/BlinkCanvas` | C6 props + optional `frames`, `onFrameChange`, `invert`, `excludeEpochs` |
| Spectrum / light curve | `src/ui/components/SpectrumPanel.tsx` | `<SpectrumChart>`, `spectrum.json` |
| Explain / glance / states | `ExplainPanel.tsx`, `Controls.tsx` (`StateCard`) | `STATES`, `TARGET_COPY`, flags (C3) |
| Tour | `src/ui/components/Tour.tsx` | `TARGET_COPY[*].tour` |
| Share / embed / flag a candidate | `src/ui/components/SharePanel.tsx`, `/embed` → `src/pages/Viewer.tsx` | C5 URL |
| All UI text | `src/ui/copy.ts` | C7 |
