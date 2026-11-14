# Research — Product & design (for Niklas)

*Compiled 14 Nov 2026. Section A = sourced facts (with links); B–F = analysis and recommendations.*

**Deadline:** submission opens Sat 14 Nov 2026 09:00 and closes **Sun 15 Nov 2026 23:59 local time of the team's Local Event** (https://www.spaceappschallenge.org/resources/project-submission-guide/).

## A. Sourced facts

### 1. Challenge text — https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/
- Objective: "a public-facing web tool to display images of the sky from the SPHEREx mission, making it easy for anyone to quickly see how they change over time." User enters RA/Dec → series of images "like a little video".
- Test on Barnard's Star, Epsilon Indi B ("a pair of brown dwarfs orbiting a star"), WISE 0855 (RA 08h55m10.831s, Dec −7d14m42.53s), RW Aurigae, R Draconis.
- Optional: easy to update with new releases; creative display of 102 bands (e.g. co-add each of the six detector arrays for S/N; "extra kudos" for spectra on the fly); add/subtract epochs; user-chosen FOV; Gaia/WISE overlays; coordinates in URL (embeddable); metadata like contamination flags; Astropy and Aladin (CDS).
- Resources: IRSA SPHEREx, tutorial notebooks, WiseView ("used by the public to make hundreds of discoveries… use it as a model"), Gaia DR3 (MAST), CSA NEOSSat.
- Difficulty "Advanced"; subjects Astrophysics, Planets & Moons, Software.

### 2. Judging & submission
**Judging & Awards Guide** (https://www.spaceappschallenge.org/resources/judging-awards-guide): each project scored 1–5 on
- **Impact** (size of problem, reach)
- **Creativity** (novel or meaningful improvement)
- **Validity** (scientifically grounded, feasible — explicitly includes *"the usability and user-friendliness of the project"*)
- **Relevance** (addresses the challenge, NASA data "as a core component… rather than a superficial addition")
- **Presentation** (storytelling; "judges evaluate the demo and full project"; give it "equal attention")

Team ≤ 6 people. Demo = **30-second video or 7 slides incl. title**; over the limit = **ineligible** for Global Judging. English (or English subtitles). Global Nominees announced 3 Dec 2026, Finalists 17 Dec, Winners 26 Jan 2027. Relevant global awards: Best Use of Data, Best Storytelling, Most Inspirational, Art & Technology, Best Use of Science.

**Project Submission Guide** (https://www.spaceappschallenge.org/resources/project-submission-guide/): required Project Name, High-Level Summary, Demo link, Final Project link, Detailed Description, "Use of Super Intelligence (SI)", NASA Data, References. Links public, no login. Page accepts images (JPG/PNG/GIF ≤ 10 MB), not videos. For self-hosted sites, a FortiGuard classification is recommended. SI allowed but "SI should not be used to come up with your idea"; AI images/videos need a **visible watermark**; AI code/data acknowledged; no NASA logos or mission identifiers in generated content. ≥ 1 NASA dataset required. No one under 18 in the demo. All external resources in References. Suggested video: 0:00 who · 0:02 challenge · 0:05 title/tagline · 0:10 how it works + NASA data · 0:20–0:30 future.

### 3. SPHEREx facts that shape screens
- Launched Mar 2025, survey from May 2025, first all-sky map Dec 2025; 4 all-sky maps planned in 2 years; 6 detectors × 17 LVF colours = 102 (https://www.jpl.nasa.gov/news/nasas-spherex-observatory-completes-first-cosmic-map-like-no-other/).
- Spectral image: one file per detector, ~70 MB, 2040×2040 at **6.15″/px**; IMAGE (MJy/sr, zodi not subtracted), FLAGS, VARIANCE, ZODI, PSF, WCS-WAVE; **LVF: band centre changes along one axis of the array**. Bands 1: 0.75–1.09 µm (R≈39) · 2: 1.10–1.62 · 3: 1.63–2.41 · 4: 2.42–3.82 · 5: 3.83–4.41 (R≈112) · 6: 4.42–5.00 (R≈128) (https://caltech-ipac.github.io/spherex-archive-documentation/spherex-data-products).
- IRSA tool roadmap: Spectrophotometry (Aug 2025), LVF cutouts (Oct 2025), Custom Mosaic (May 2026), **Spectral Cube Cutout (Jan 2027)** (https://spherex.caltech.edu/page/data-tools) → a cube viewer is still novel.
- Professional comparator: IRSA SPHEREx Data Explorer — capped at 20 sources / 2 jobs, can take hours near ecliptic poles (https://irsa.ipac.caltech.edu/onlinehelp/spherex/spherex/sp.html).
- Pitch hook: Gagné et al. 2026 — SPHEREx QR2 spectra of **6,003 ultracool dwarfs, 947 newly identified**, with the Backyard Worlds collaboration (https://arxiv.org/abs/2604.22012).
- Proper motions: WISE 0855 ≈ 8.15″/yr (https://arxiv.org/pdf/1605.08620), Barnard ≈ 10.3″/yr, ε Indi ≈ 4.7″/yr (to verify).

### 4. Users of comparable projects
- **Backyard Worlds: Planet 9** (Zooniverse, 15 Feb 2017): 256×256 px unWISE flipbooks of 4 *difference* frames over ~4.5 yr, asinh stretch, W1→blue W2→red; volunteers mark movers and "dipoles"; confusers: partial subtractions, cosmic rays, ghosts, latents; discoveries surface on Talk (#dipole/#mover); first discovery 6 days after launch (https://ar5iv.arxiv.org/html/1705.02919).
- Scale: > 100k volunteers (2020); NASA cites ~150k (https://en.wikipedia.org/wiki/Backyard_Worlds; https://www.nasa.gov/universe/two-bizarre-brown-dwarfs-found-with-citizen-scientists-help).
- **April 2026: 3,006 motion-confirmed L/T dwarf candidates** (2,357 L, 649 T) + 28 co-moving companions, would "more than double the number of known L and T dwarfs", 76 authors mostly citizen scientists (https://arxiv.org/abs/2604.01323). March 2024: 89 new co-moving companions (https://arxiv.org/pdf/2403.04592).
- **Cool Neighbors** (2023): ML preselects, flipbook centred on candidate → ~3× more classifications per unit time (https://doaj.org/article/122c378549a84b31a3ddb968abc9ffa5; https://news.medill.northwestern.edu/chicago/?p=106059). Now "Finished… out of data".
- Motivation: "needle-in-the-haystack" puzzles; novices given hard tasks leave; "AI as a coach" (Medill article). No published survey of volunteer complaints was found.
- **Disk Detective**: > 30k volunteers in v1, 15 co-authors; v2 with 150k stars (https://science.nasa.gov/citizenscience/news/nasa-disk-detective-project-relaunches-with-150000-stars).

### 5. UX of comparable tools
- **WiseView** (http://byw.tools/wiseview): RA/Dec box (decimal or sexagesimal), FOV arcsec (default 60), band, sliders (blink interval, zoom, min/max, linearity, coadd window), ~10 checkboxes (invert, difference imaging, Gaia DR3 overlay, skip middle epochs…), shift-and-add by pm, synthetic object injection, Pan-STARRS panel; click to recentre; `+/−/.` epoch legend; **dashed border on frame 0** to show loop restart; URL state `ra, dec, size, band, speed, minbright, maxbright, linear, color, mode, zoom`; "built for Chrome"; no keyboard shortcuts. Powerful but expert-only (~25 controls).
- **Aladin Lite v3**: `A.aladin(div, {target, fov, survey})`, `setFov`, `newImageSurvey` (https://aladin.cds.unistra.fr/AladinLite/doc/API).
- ESASky, Legacy Survey viewer, Firefly, Stellarium Web, NASA Eyes (not fetched; assessment): Legacy viewer has good URL state; ESASky has name search but no blink; Firefly is table-heavy; Stellarium Web / NASA Eyes are the gold standard for non-experts.

### 6. Story material
- Clyde Tombaugh found Pluto on **18 Feb 1930** by blinking two plates taken six days apart (https://www.britannica.com/biography/Clyde-Tombaugh; https://www.lindahall.org/about/news/scientist-of-the-day/clyde-tombaugh/).
- WCAG 2.3.1: no more than 3 flashes per second (https://kb.daisy.org/publishing/docs/wcag/three-flashes-or-below-threshold.html).

## B. Design implications (analysis)
1. **Motion is 1–2 px** (6.15″/px; Barnard ~1.7 px/yr, WISE 0855 ~1.3, ε Indi B ~0.8) → nearest-neighbour zoom, crosshair, difference view (dipole), predicted motion arrow from Gaia pm.
2. **LVF trap**: each visit sees the source at a different λ; blinking raw frames mixes colour change with motion → frames must be wavelength-matched; show λ per frame.
3. **Few epochs** (~2–3) → design sparse/empty states first.

## C–F
Recommendations, contracts, demo script and risks are integrated into [`roles/03-product.md`](../roles/03-product.md) and [`CONTRACTS.md`](../CONTRACTS.md).
