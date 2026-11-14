# Role 3 · Product engineer & design — **Niklas**

**Mission:** design the whole product — **who it is for, what they do, what they see and how it is explained** — build the
website shell around the viewer, and own the **submission** (30-second video, project page). The judges score
*usability* inside **Validity** and give **Presentation** equal weight: this role decides a big part of the score.

**You own:** `web/src/ui/`, `web/src/pages/`, `web/src/styles/`, `web/package.json`, `submission/`, the C5 URL scheme.
**You consume:** bundles (C4) and `<BlinkCanvas>` (C6) from Giorgi/Quirce; science notes (C7) and flag texts (C3) from Yasen/Sean.
**Challenger:** you are also the team's hole-poker on scope and cuts (see DECISIONS.md).

---

## 1. Scopes

| ID | Scope | Must/~ | Appetite | Done looks like |
|---|---|---|---|---|
| U0 | **Breadboard + wireframes + URL scheme** (C5) | must | 2 h (H0–H2) | Low-fi wireframes of landing + viewer + states pushed to `design/`; URL params agreed with Giorgi. |
| U1 | **App shell & landing**: smart search box (name / decimal / sexagesimal), 5 demo target chips, "click on the sky" tab (Aladin Lite v3) | must | 4 h | Typing "Barnard" or `269.45 4.74` or clicking a chip lands on the viewer with the right URL. |
| U2 | **Viewer page** around `<BlinkCanvas>`: play/pause, speed (≤ 2 fps), prev/next frame, epoch strip with dates, band chips (D1–D6, D56), mode toggle Blink / Difference / Side-by-side, zoom, "Advanced" drawer (stretch, invert, include/exclude epochs, flag overlay) | must | 5 h | All controls drive the canvas; state round-trips through the URL (shareable). Keyboard: Space, ←/→, D. |
| U3 | **Explain layer**: "What am I seeing?" side panel (object card from C7, motion arrow + plain sentence, flags legend from C3), band chips with plain copy, empty/error states (C5) | must | 4 h | A non-expert understands each of the 5 targets without reading anything else. |
| U4 | **Guided tour of the 5 targets** (3-step cards each: what it is → what to look for → "did you see it?") | must | 3 h | The tour is the demo script; it works start-to-finish on the deployed site. |
| U5 | **Spectrum panel** around `<SpectrumChart>` with labelled molecule bands (H₂O, CH₄, CO₂, CO) | must | 2 h | Clicking "Spectrum" on WISE 0855 / R Dra shows the chart with labels. |
| U6 | **Share / embed**: copy link, `/embed?…` minimal view, Open Graph image (PNG from bundle) | must (embed ~) | 1.5 h | A pasted link reproduces the exact view. |
| U7 | `~` **Flag a candidate**: click → prefilled form (RA/Dec, epochs, band, permalink, checklist) → download JSON / open GitHub issue | ~ | 2 h | Never says "discovery". |
| U8 | `~` **λ slider / 3D cube** UI around `<CubeSlider>` | ~ | 2 h | Only after freeze-safe. |
| U9 | **Submission**: 30-s video, project page texts, references, SI disclosure, deploy URL reachable without login | must | 5 h (Sun) | Submitted by Sunday 22:00 local. |
| U10 | **Deploy** on Vercel (static) + check from a phone/another network | must | 1 h | Public URL works with all 5 targets. |

## 2. Product decisions you must take (with recommendation)

| Decision | Recommendation (from research) | Class |
|---|---|---|
| **Primary persona** | Curious non-expert (student, amateur astronomer) arriving from a shared link. Secondary: Backyard-Worlds-style power user → everything expert goes in an "Advanced" drawer. | Autonomous (tell the team) |
| **Core flow** (breadboard) | Landing: *Pick a target* (search · 5 chips · sky map) → **Viewer** (auto-plays blink ~1 fps, crosshair + date + λ on each frame) → side panel *What am I seeing?* → actions: Spectrum · Compare bands · Share/Embed · (~)Flag a candidate | Team-lock (C5) |
| **Input methods** | One tolerant box (name, decimal, sexagesimal — like WiseView) + Aladin Lite sky picker + FOV presets (2′ / 5′ / 10′) instead of a free arcsec field | Autonomous |
| **Default view** | Blink, band `D56` for brown dwarfs / `D1–D2` for bright stars (whatever Data's `default_band` says), zoom ×8 nearest-neighbour, crosshair + predicted track ON | Consultative (Processing) |
| **Controls visible vs hidden** | Visible: play/pause, speed, frames, zoom, band chips, mode toggle. Hidden (Advanced): stretch, min/max, invert, epoch +/−, flags overlay. WiseView shows ~25 controls at once — that's the anti-pattern. | Autonomous |
| **How to explain bands** | 6 detector chips + `D56` named in plain words ("3.8–5 µm · where cold brown dwarfs glow"), molecule labels on the spectrum; never bit numbers for flags — "problem pixels" overlay with a legend | Autonomous |
| **Motion is tiny (1–2 px)** | Make it visible: zoom, crosshair, track arrow, **difference mode** (mover = black/white dipole), plain sentence "moved 10″ south-west between Aug 2025 and Sep 2026". Consider a "long baseline" link to WiseView. | Consultative (D12) |
| **Few epochs (2–3)** | Design the sparse states first: 1 epoch → "come back in 6 months", 2 → blink + diff, 3 → full. Show the epoch strip so users see there are only 3. | Team-lock (C5 states) |
| **False colour & accessibility** | Greyscale blink by default; false colour with colour-blind-safe ramps (cividis/magma or blue–orange, never red–green); blink ≤ 2 Hz (WCAG 2.3.1 forbids > 3 flashes/s); `prefers-reduced-motion` → start paused + side-by-side; keyboard operable; text alternative for motion. | Autonomous |
| **Desktop vs mobile** | Desktop-first (judges, demo); responsive single column for mobile without the sky map/cube. | Autonomous |
| **3D cube** | Not core. A λ slider over the same cutout tells the "102 colours" story in 5 seconds; real 3D only if everything else is green. | Team-lock D14 |
| **Visual identity** | Dark UI, one accent colour, monospace numbers; **no NASA logos/mission marks in generated assets**; watermark AI-generated images. | Autonomous (D15 is locked) |
| **Name & tagline** | Pick early (needed for repo, page title, video). Ideas: "Blink" / "SPHEREx Blink" / "Planet X Finder"… — your call, tell the team by H+2. | Autonomous |

## 3. What to research (time-boxed, ~2 h total at the start)

1. **WiseView** (http://byw.tools/wiseview) — the model the challenge points to: blink speed, FOV, Gaia overlay, difference imaging, URL params (`ra, dec, size, band, speed, minbright, maxbright, linear, mode, zoom`), the dashed border on frame 0 to show the loop restart, the `+/−/.` epoch legend. Note what is confusing for a newcomer.
2. **Backyard Worlds** flipbook (Zooniverse): 4 difference frames, movers vs "dipoles", how volunteers mark candidates; Cool Neighbors centres each flipbook on an ML candidate → ~3× faster classification. Paper: https://ar5iv.arxiv.org/html/1705.02919
3. **Aladin Lite v3** embedding (`A.aladin(div, {target, fov, survey})`, HiPS surveys) for the sky picker: https://aladin.cds.unistra.fr/AladinLite/doc/API
4. **Stellarium Web / NASA Eyes** as the bar for "non-expert friendly": search-first, almost no visible parameters.
5. **Judging & submission** (read both pages fully, 20 min): https://www.spaceappschallenge.org/resources/judging-awards-guide · https://www.spaceappschallenge.org/resources/project-submission-guide/
   - 5 criteria scored 1–5: Impact, Creativity, Validity (*includes usability*), Relevance (NASA data as core), Presentation.
   - Demo: **30-second video or 7 slides** (over the limit = ineligible). English (or English subtitles).
   - Required fields: name, high-level summary, demo link, final project link (public, no login), detailed description, use of SI, NASA data, references.
   - Awards to aim at: *Best Use of Data*, *Best Storytelling*, *Most Inspirational*, *Art & Technology*.
6. Accessibility: WCAG 2.3.1 three flashes https://kb.daisy.org/publishing/docs/wcag/three-flashes-or-below-threshold.html

## 4. Outputs & deadlines (H0 = kick-off)

| When | Output | For |
|---|---|---|
| H+2 | Breadboard + low-fi wireframes (`design/`), **URL scheme confirmed** (C5), name/tagline | Giorgi (viewer props), everyone |
| H+3 | Component list + all UI copy placeholders + list of numbers/facts you need from Data (feeds C7) | Data (science notes), Giorgi |
| H+6 (CP1) | App shell running with the mock bundle, then the first real bundle | Integration |
| Sun 10:00 (CP2) | All flows working on real data for 5 targets; tour cards drafted | Polish |
| Sun 12:00 | Video script + shot list frozen | Recording |
| Sun 16:00 (freeze) | Deployed, QA'd on 2 browsers + phone | — |
| Sun 20:00 | Video (≤ 30 s, English subtitles) + all submission texts | Team review |
| **Sun 22:00** | **Submitted** | — |

## 5. Dependencies & contracts

**You need from Processing (Giorgi/Quirce):** mock bundle + `<BlinkCanvas>` stub at H+1 (C4, C6); real bundles at CP1 / CP2.
**While waiting:** build the shell, search box, chips, copy and states against the mock.
**You need from Data (Yasen/Sean):** `targets.json` (C1) for chips/aliases; `flags.json` plain texts (C3); `science-notes.md` (C7) for cards, tour and video.
**You owe everyone:** C5 URL scheme + states by H+2; final wording review of C3/C7 plain texts; the submission.

## 6. Demo / video storyline (draft — 30 s hard limit)
- 0:00–0:04 "In 1930 Clyde Tombaugh found Pluto by blinking two photographs." (archival-style blink; credit or watermark)
- 0:04–0:08 "Volunteers have since found thousands of cold worlds the same way. NASA's SPHEREx now photographs the whole sky in 102 colours every six months."
- 0:08–0:22 Live: type "Barnard's Star" → it shifts → Difference (dipole) → band chip on WISE 0855 (only visible at 3.8–5 µm) → spectrum → R Draconis brightens in place.
- 0:22–0:30 "Share a link. Flag a candidate. Your browser is a blink comparator." + name + URL.
Facts must come from C7 (e.g. Backyard Worlds' 3,006 L/T candidates paper, arXiv 2604.01323; SPHEREx ultracool dwarf spectra, arXiv 2604.22012 — Data verifies).

## 7. Rabbit holes
- Control overload (WiseView has ~25 controls on one screen).
- Building the 3D cube or the "flag a candidate" backend before the core flow works.
- Depending on live IRSA calls during judging (D2: static).
- Video over 30 s (ineligible) · AI assets without watermark · NASA logo in generated art · saying "discovery".
- Blinking faster than 2 Hz.
