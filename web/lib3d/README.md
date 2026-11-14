# lib3d · class-based 3D models (chunk A8, contract I5)
`renderObject(el, {cls, temp_K, binary, temp2_K, ...})` → controller `{setView('eye'|'ir'), setTemp(K), setSpots(bool), setSpin(bool), flare(), dispose()}`.
Classes: `red-dwarf`, `star`, `brown-dwarf`, `mira`, `young-star`, `asteroid`, `comet`. Uses npm `three` (≥0.160); `demo.html` loads it from a CDN via an import map (serve the folder over http, e.g. `python3 -m http.server`).
All models are illustrations: dials (colour from temperature, period, binary) come from data; values in demo.html are placeholders until `science/classes.json` (chunk C) gives cited numbers. `appearance_class` in the scan report (I3) picks the model.
