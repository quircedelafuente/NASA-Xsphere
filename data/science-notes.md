# Science notes (C7) — D-4, owner Sean

Every number the app or video shows must come from here. Status tags: **[M]** measured by our team on 14 Nov 2026 (see `research/01-data.md`), **[L]** literature, quoted from memory of the paper and **still to be re-checked against the link before the video** (re-check = open the link, confirm the number, change `[L]` to `[L✓]`).
Positions/pm in the app come from `data/targets.json`, not from here.

## Mission and story

- **SPHEREx** is a NASA all-sky infrared survey telescope launched 11 March 2025. It maps the whole sky in **102 colours (0.75–5.0 µm)**, 4 times in 2 years, so each patch of sky is seen at several *epochs*. [L] https://science.nasa.gov/mission/spherex/
- Its main goals are cosmic inflation, the history of galaxies, and ices (water, CO₂, CO) in star-forming clouds. Movers are a by-product, which is the point of this challenge. [L] same link.
- Colours come from **linear variable filters**: the wavelength changes along the detector, so one exposure sees each object at one colour only. That's why we never blink frames of different colours (D5). [M/D] Explanatory Supplement §3.4.4.
- Each target is seen about once per colour per survey pass, ~2 passes per year ~6 months apart. [D] Supplement §1.4.
- Pixels are 6.15″; one detector image is 2040×2040 px (~3.5°×~3.5° per detector). [D]
- **Blink comparator:** Clyde Tombaugh found Pluto in 1930 by blinking photographic plates taken days apart; the thing that "jumps" is the planet. https://www.britannica.com/biography/Clyde-Tombaugh [L]
- **Backyard Worlds:** citizen scientists blink WISE images to find cold brown dwarfs; 3,006 L/T candidates (arXiv 2604.01323) [L]; SPHEREx has 6,003 ultracool dwarf spectra (arXiv 2604.22012) [L]. (Both IDs given by the team research; re-check wording.)
- Data are public, no login, from IRSA (Caltech/IPAC). Release used: DR1 + QR3 (pipeline R7). [D]

## Barnard's Star (`barnards-star`)
1. A faint red dwarf (spectral type M4) only **~1.83 pc (6 light-years)** away: Gaia parallax 546.98 mas → 1.828 pc. [L/M] Gaia DR3.
2. It has the **fastest proper motion of any star: 10.39″ per year** = 1.69 SPHEREx pixels/yr, so it moves by 1 px in ~7 months. Gaia pm (−801.55, +10362.39) mas/yr. [M]
3. We measured it in SPHEREx: **+9.8″ in Dec over 0.99 yr** (expected +10.3″). [M]
4. It is approaching us at ~110 km/s and is expected to get closest in ~10,000 years (still ~1.1 pc). [L] check number.
5. Caveat: it's bright in SPHEREx; its core is saturated (NaN) in all 168 D1–D3 frames we checked. Use D5/D6 or the difference view; the motion is still measurable. [M]

## ε Indi B (`epsilon-indi-b`) — Ba and Bb
1. A pair of **brown dwarfs** (spectral types ~T1 + T6) orbiting the Sun-like star ε Indi A at ~3.6 pc. Binary separation is ~0.7″, far below one SPHEREx pixel, so we see a single blob. [L] Dieterich et al. 2018; Chen et al. 2022 (dynamical masses ~66 and ~53 Jupiter masses, to verify).
2. Proper motion 4.68″/yr = 0.76 px/yr, moves with its parent star. Gaia DR3 6412596012146801152 (G=18.0). [M]
3. Brown dwarfs are brighter in the red end of SPHEREx (D5/D6) than in the blue; methane makes them dim around 1.6, 2.2 and 3.3 µm. [L] 
4. Caveat: faint and next to the very bright ε Indi A: check ghosts/crosstalk (QA).

## WISE 0855−0714 (`wise-0855`)
1. **Coldest known brown dwarf, ~250 K** (about −25 °C ≈ a cold winter day). Discovered by Luhman 2014 from WISE motion. [L] https://arxiv.org/abs/1404.6501 (re-check)
2. At **~2.3 pc** it is the 4th/5th closest system to the Sun. Parallax ~439 mas → 2.28 pc. [L] Luhman & Esplin 2016, https://arxiv.org/abs/1605.08620 
3. It was found precisely because it moves: **~8.1″/yr**, 1.33 px/yr. We saw −7.4″ in RA over 0.985 yr. [M]
4. It is **invisible below ~3.8 µm** and shows up only in D5/D6 (S/N 3–5 per exposure, 10–14 per epoch co-add): use `D56` and co-adds. [M]
5. Caveat: not in Gaia. Catalogue position (2010) is ~127″ (~20 px) off today → always propagate. [M]

## RW Aurigae (`rw-aurigae`)
1. A **young star (T Tauri type)** in the Taurus region, ~140 pc, with a disk and a companion; it is a famously irregular variable. [L] check.
2. Has had long **dimming events** (2010, 2014, 2016–17, and 2024-25 reported), thought to be dust from a disk disrupted by an encounter. [L] check which are in SPHEREx dates; do not claim a link to our data.
3. Static position (pm < 0.03″/yr): any change is brightness, not motion. [M]
4. Caveat: saturated (OVERFLOW 100/101 frames). Our D5 flux fell ~2.2 Jy → ~1.2 Jy (Sep 2025 → Sep 2026) but this is NOT reliable. [M, unreliable] Do not put in the video without QA.

## R Draconis (`r-draconis`)
1. A **Mira variable**: a pulsating old giant that swells and fades by several magnitudes (typically 100×+ in visible light) in a period of **≈ 245 d**. [L] GCVS/AAVSO, re-check.
2. In the north ecliptic **deep field** → **2,493 SPHEREx images, ~monthly Apr 2025 → Sep 2026**, enough for a real light curve (~2 cycles). [M]
3. Static position. Mira variability is much stronger at short than long wavelengths (it is the colour of cool giant). Expect large changes in D1/D2. [L]
4. Caveat: each epoch spans weeks and mixes colours inside a detector; compare the same band only (D5).

## Do not claim
- That SPHEREx "discovered" any of these. These are known objects; the demo shows SPHEREx's ability to reveal them.
- Planets around Barnard's Star in the UI text (disputed/unconfirmed in literature) unless Niklas needs it; then re-check.
- Any WISE 0855 flux in mJy without our QA (0.4–0.6 mJy [M] rough).
