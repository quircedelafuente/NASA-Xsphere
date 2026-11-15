# lib3d · class-based 3D models (chunk A8, contract I5)
`renderObject(el, {cls, temp_K, binary, temp2_K, ...})` → controller `{setView('eye'|'ir', lam_um?), setTemp(K), setSpots(bool), setSpin(bool), flare(), dispose()}`.
Classes: `red-dwarf`, `star`, `brown-dwarf`, `mira`, `young-star`, `asteroid`, `comet`. Uses npm `three` (≥0.160); `demo.html` loads it from a CDN via an import map (serve the folder over http, e.g. `python3 -m http.server`).
All models are illustrations: dials (colour from temperature, period, binary) come from data; values in demo.html are placeholders until `science/classes.json` (chunk C) gives cited numbers. `appearance_class` in the scan report (I3) picks the model.
The `'ir'` view uses the same false colour as the photos (one tint per wavelength: `web/src/ui/lib/palette.ts`, `processing/palette.py`; keep the three in sync). Pass the centre wavelength of the band on screen as `lam_um`; without it the tint is the 3.1 µm amber.
