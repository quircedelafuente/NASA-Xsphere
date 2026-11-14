# How the SPHEREx system works, and how to use each resource (14 Nov 2026)

## The system in 5 steps
1. **The telescope.** SPHEREx photographs the whole sky every 6 months. It has **6 detectors (D1–D6)**, and each one covers its own slice of infrared colour. Within one photo, the colour also changes from one side to the other (a "rainbow filter"). So any one star, in any one photo, is seen in one exact colour. That adds up to 102 colours (bands) across the six detectors.
2. **The archive (IRSA, at Caltech).** Every photo lands here, a new batch each week. Each photo is a FITS file (the standard astronomy image format) with 7 layers inside: the image, quality flags, a noise map, the glow from solar-system dust (zodi), the star shape (PSF) and two colour maps.
3. **Searching.** You ask the archive: "which photos cover this point, from which detector?" You get back a list of files with dates. For WISE 0855 we got 48.
4. **Cutting out.** The full files are hundreds of MB. You add `?center=RA,Dec&size=0.1` to a file's web address and get back only a small square (about 4 MB).
5. **Showing it.** Put the squares in date order and play them like a flip-book. Anything that moves or flickers is what we're looking for.

**Our tool does steps 3 → 5 automatically, for any position someone types in.**

## Each resource

### 1. NASA/IPAC Infrared Science Archive (IRSA): the SPHEREx page
irsa.ipac.caltech.edu/Missions/spherex.html. **This is the main one.** Everything else hangs off it.
- **SPHEREx Data Explorer:** a website where you search by clicking. Type a star name, pick the "Spectral Image Search" tab, and you get every photo, a preview and a scissors icon for cutouts. **Use it first, by hand, to see what our tool must automate.**
- **Data Release 1 / Quick Releases:** the photo collections. DR1 is the reprocessed set (out Nov 2026). The Quick Releases (QR3) are the newer weekly photos. Use both together.
- **Cutout Tool:** cuts the small squares out of a full photo (step 4). Our app calls this through a web address; nobody clicks it.
- **Moving Object Search Tool (MOST):** type an asteroid or comet name and it finds the photos where that object should appear. Good for a demo ("watch this asteroid cross").
- **Spectrophotometry Tool:** gives the brightness of a source in every colour, which is a spectrum. That's the "extra kudos" item. We can call it instead of computing it ourselves.
- **Mosaic Tool:** stitches many photos into one bigger picture. Useful for a larger field of view.
- **Source Discovery Tool:** finds all bright spots in an area automatically.
- **Catalog Search:** lists of already-measured sources, in table form.
- **Cloud Data Access (AWS S3):** the same files on Amazon's cloud. It's faster in bulk, but we don't need it for a weekend.
- **Comet 3I/ATLAS, SPLICES:** special collections (an interstellar comet, ice-rich sources). Optional demo material.
- **Explanatory Supplement (PDF) / Archive User Guide:** the manuals. Read them only when something looks strange, for example what a flag means.
- **Program Interfaces:** the rules for asking the archive by code (TAP, SIA). This is what our server speaks.

### 2. SPHEREx tutorial notebooks
caltech-ipac.github.io/irsa-tutorials/spherex/. Ready-made Python recipes from the archive team. Each one is a page of code plus an explanation, which you can run in Jupyter.
- **Introduction:** opens one photo, shows the 7 layers, and searches the simple way (SIA).
- **Cutouts:** ⭐ our core recipe. Find all photos of a point → download cutouts → sort by date. Steps 3 and 4 above, already written.
- **PSF:** how a point of light is smeared in a photo. Needed only for precise measurements.
- **Source Discovery Tool:** how to call that tool from code.
- **Mosaic Cubes:** build a stacked picture in many colours.
- **HiPS Cubes:** the whole sky as a zoomable map with 102 colour layers, like Google Maps for the sky. ⭐ Good background layer for our page.

### 3. WiseView
byw.tools/wiseview. **Our model.** (The IE network blocks this site, so this description is from memory and not checked today.) It's the flip-book tool for the older WISE telescope, used by Backyard Worlds volunteers to find hundreds of brown dwarfs. You type RA/Dec, it plays the images over the years, and you can change the size, contrast and speed, and switch to a "difference" view. **The challenge is basically "WiseView for SPHEREx", plus the colours.** Try it on your phone's data, off the IE Wi-Fi.

### 4. Gaia mission data (DR3)
archive.stsci.edu/missions-and-data/gaia. A European telescope (2014–2025) that measured the exact position, distance and **motion** of more than a billion stars. We use it to draw an arrow on each star that Gaia says is moving. If a dot moves in SPHEREx and Gaia agrees, it's real. If it moves and Gaia doesn't know it, it may be a discovery. Use DR3, the latest release.

### 5. Canadian Space Agency resources (all optional)
- **NEOSSat:** a small Canadian satellite that hunts asteroids and space debris. Background reading.
- **Canadian Astronomy Data Centre (CADC):** the archive that holds NEOSSat's photos, like IRSA is for SPHEREx.
- **NEOSSat Data Tutorial (GitHub):** Python recipes to download, filter and view NEOSSat FITS files, plus a second notebook on first asteroid analysis.
- **NEOSSat Dataset (Canada open data):** the photos themselves, free licence.
**Our use:** none this weekend. It's a second telescope we could add later to confirm asteroids.

## Which pieces our app uses
Typed position → **our server** → IRSA search (Program Interfaces) → Cutout Tool → small PNGs, kept → **our page** plays them, draws Gaia arrows, and has an optional HiPS sky map behind and a spectrum on click. An MCP server lets Claude call the same server.

---
# Step by step, with links (checked 14 Nov 2026)

## A. SPHEREx Data Explorer: try this first, about 5 min
Link: https://irsa.ipac.caltech.edu/applications/spherex/
1. Open the link and wait about 10 s for the start screen.
2. Click the **Spectral Image Search** tab at the top. The whole-sky map appears. Yellow = covered, red = the extra-deep areas.
3. In the box "Coordinates or Object Name", type `08h55m10.831s -07d14m42.53s` (WISE 0855). You can also type a name like `Barnard's Star`, and it looks the name up itself.
4. Click **Search**. After about 20 s you get **258 photos** (all 6 detectors) and the first photo on the right.
5. In the filter box under **energy_bandpassname**, type `SPHEREx-D2` and press Enter. That leaves **48 photos**, one detector, May 2025 → May 2026 (column **t_min** = date, in astronomers' day numbers).
6. Click any row to see that photo on the right. Note that each one is a **62 MB** download.
7. Click the **Coverage** tab. Every photo shows as a rectangle on the sky, all overlapping our target.
8. Tick a few rows → **Generate Download Script** → tick **Cutouts** (default 1.2′ square) → this would give you a script that downloads only the small squares. I pressed Cancel in the video.
9. **Spectrophotometry Tool** tab: type a position → Submit → after a few minutes you get the source's spectrum (brightness in every colour). It runs as a job; watch it in **Job Monitor**.
10. **Mosaic Tool** tab: same idea, stitches photos into one big image.

## B. The SPHEREx page (the hub)
Link: https://irsa.ipac.caltech.edu/Missions/spherex.html
Scroll down. Every tool from section 1 of this guide is a link there. Worth clicking:
- **Moving Object Search Tool** → type an asteroid name, for example `Ceres` → it lists SPHEREx photos where it should be.
- **SPHEREx Explanatory Supplement** (PDF manual) → only when something is unclear.

## C. Tutorial notebooks (our code recipes)
Links:
- All: https://caltech-ipac.github.io/irsa-tutorials/spherex/
- ⭐ Cutouts: https://caltech-ipac.github.io/irsa-tutorials/spherex-cutouts/
- ⭐ HiPS all-sky cube: https://caltech-ipac.github.io/irsa-tutorials/spherex-hipscube/
- Intro: https://caltech-ipac.github.io/irsa-tutorials/spherex-intro/
1. Open one and just read top to bottom: text explains, grey boxes are code, the box under each shows its result.
2. You don't need to run them. I'll turn the Cutouts recipe into our app's server.
3. If a teammate wants to run one: the **Launch kernel** button at the top runs it in the browser.

## D. WiseView (the model to copy)
Link: http://byw.tools/wiseview. **Blocked on IE Wi-Fi: use your phone's hotspot.**
1. Type `133.7951 -7.2451` (WISE 0855) in the position box and press Go.
2. It plays the WISE images over the years as a loop. Look for the dot that walks.
3. Play with size, speed and the "diff" setting, which subtracts images so only changes stay.
4. Note what feels good and what's annoying; our version should beat it. (These steps are from memory, since I couldn't open the site here.)

## E. Gaia (motion arrows)
Link: https://archive.stsci.edu/missions-and-data/gaia
1. Reading page only; data access is through MAST search or code.
2. Easier for checking one star: https://simbad.cds.unistra.fr/simbad/ → type `Barnard's Star` → look at "Proper motions" (how many milliarcseconds a year it moves).
3. Our app pulls Gaia DR3 by code; nothing for you to click.

## F. Canadian resources (optional, skip this weekend)
- NEOSSat: https://www.asc-csa.gc.ca/eng/satellites/neossat/ (read)
- CADC archive: https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/ (search for NEOSSat photos)
- Tutorial: https://github.com/asc-csa/NEOSSAT_Tutorial (Python recipes, English half below the French)
- Dataset: https://data.asc-csa.gc.ca/dataset/neossat (raw photos, free licence)

## G. The challenge itself
https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/ (Details tab = task; Resources tab = list above; Teams tab = other teams on it)
