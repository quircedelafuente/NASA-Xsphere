# Yasen's proposals (Data role) — 14 Nov 2026

Work in progress for discussion. Nothing here changes a contract (C1–C7); field ideas are proposals for Quirce to accept or not.

| File | What it is |
|---|---|
| `sample-site/index.html` | **Sample of the finished viewer**, one object (Barnard's Star), built from **108 real SPHEREx cutouts** (D4–D6, DR1+QR3, 3 visits). Blink / changes-only / side-by-side, predicted Gaia track, band chips, real spectrum points, share link. Open the file in a browser (58 KB, no server needed). Measured shift 9.8″ over 0.98 yr vs 10.2″ expected from Gaia pm. |
| `sample-site/build_sample.py` + `template.html` + `inject.py` | How it was built: reads cutouts from `dl/<target>/` (made with `spikes/cutout_downloader.py` or curl), reprojects to one grid, median per detector per visit, PNGs, aperture photometry. Throwaway, like spikes/. |
| `sample-3d/barnards-star-3d.html` | **Interactive 3D illustration** (Three.js): human-eye vs SPHEREx infrared view (with the real spectrum), temperature slider, flares, size vs Sun/Jupiter/Earth, its 4 planets, to-scale 3D map. Every number tagged measured / calculated / estimated. Some literature values still need a source (D-4). |
| `master-plan-100x.md` | **The full plan**: 10 measurable ways we beat WiseView, 10 product pillars (P1–P10) with tiers A/B/C, architecture, science checks per target, roadmap by role, cut order, risks. Yasen: yes to the 4 decisions; team to confirm. |
| `spherex-advantages.md` | One table: what SPHEREx gives us that WiseView never had, and what to build with each. |
| `engine-plan.md` | Data engine: watcher → fetcher → processor → classifier → publisher (+ MCP), sources, 3-layer rule-based classification, where computation happens. |
| `objects-and-3d.md` | What we can and cannot know about an object from the data (shape: no; size: calculated), and a class-based 3D model library proposal + optional `appearance` block for C1. |
| `resources-guide.md` | Plain-language guide to every challenge resource, with step-by-step links. |

**Prior art to know about:** github.com/mateibut/SPHEREx-Blink-3.0 (MIT, live) is an advanced SPHEREx blink tool built before the hackathon (blink, difference, find movers, catalogue cross-match, SkyBoT). Our edge has to be accessibility, explanations, 3D and the infrared ↔ eye story. Space Apps' rule on pre-existing code is unverified — check before reusing any of it.

Practical notes: IRSA answers "Server busy" above ~4 parallel cutout requests; on networks that inspect HTTPS (IE Wi-Fi), Python's urllib fails while curl works.
