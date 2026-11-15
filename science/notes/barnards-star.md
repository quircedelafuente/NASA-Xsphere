# Mission and story

- **SPHEREx** is a NASA all-sky infrared survey telescope launched 11 March 2025 [L✓ https://science.nasa.gov/mission/spherex/]. It maps the whole sky in **102 colours (0.75–5.0 µm)**, 4 times in 2 years, so each patch of sky is seen at several *epochs*. [D] Explanatory Supplement (the NASA page itself gives only 'all-sky spectral survey over two years'; get the 102/4× numbers from https://spherex.caltech.edu).
- It will collect data on **over 450 million galaxies and over 100 million Milky Way stars**, to study the origin of the universe, galaxy history and interstellar ices. [L✓] NASA page. Movers are a by-product, which is the point of this challenge.
- Colours come from **linear variable filters**: the wavelength changes along the detector, so one exposure sees each object at one colour only. That's why we never blink frames of different colours (D5). [M/D] Explanatory Supplement §3.4.4.
- Each target is seen about once per colour per survey pass, ~2 passes per year ~6 months apart. [D] Supplement §1.4.
- Pixels are 6.15″; one detector image is 2040×2040 px (~3.5°×~3.5° per detector). [D]
- **Blink comparator:** Clyde Tombaugh found Pluto in 1930 by blinking photographic plates taken days apart; the thing that "jumps" is the planet. https://www.britannica.com/biography/Clyde-Tombaugh [L]
- **Backyard Worlds:** citizen scientists blink WISE images to find cold brown dwarfs; **3,006** new motion-confirmed L and T dwarf candidates (2,357 L + 649 T; photometric types, spectroscopy still needed) [L✓] arXiv 2604.01323. SPHEREx spectrophotometry for **6,003 ultracool dwarfs** (L0–Y1; 947 newly identified), which more than doubles ultracool dwarfs with spectra (3,449 → 7,402) [L✓] Gagné et al., arXiv 2604.22012 (its three sub-counts sum to 6,005: quote 6,003 as the paper's headline).
- Data are public, no login, from IRSA (Caltech/IPAC). Release used: DR1 + QR3 (pipeline R7). [D]

## Barnard's Star

1. A faint red dwarf (spectral type M4 [L]; surface ~3,100–3,200 K: 3134 ± 102 K, Dawson & De Robertis 2004, or 3223 ± 17 K; radius ~0.19–0.20 of the Sun's [L✓ via https://en.wikipedia.org/wiki/Barnard%27s_Star]) only **~1.83 pc (6 light-years)** away: Gaia parallax 546.98 mas → 1.828 pc. [M]; 1.8266 pc [L✓] Wikipedia/Britannica.
2. It has the **fastest proper motion of any star: 10.39″ per year** = 1.69 SPHEREx pixels/yr, so it moves by 1 px in ~7 months. Gaia pm (−801.55, +10362.39) mas/yr. [M]
3. We measured it in SPHEREx: **+9.8″ in Dec over 0.99 yr** (expected +10.3″). [M]
4. It is approaching us at **~110 km/s** (−110.6 km/s) and will be closest around **AD 11,800**, at ~3.8 light-years (sources differ: 3.75–3.85 ly, 11,700–11,800). [L✓] Wikipedia, Britannica; say 'about 12,000 years' / 'about 3.8 ly'.
5. Caveat: it's bright in SPHEREx; its core is saturated (NaN) in all 168 D1–D3 frames we checked. Use D5/D6 or the difference view; the motion is still measurable. [M]

*Cut from data/science-notes.md (tags: [M] measured by the team, [L✓] checked against the source, [L] not yet checked).*
