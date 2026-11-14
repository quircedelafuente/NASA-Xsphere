# I3 · Scan / object report (chunk B produces)

```json
{"zone":{"ra_deg":269.45,"dec_deg":4.74,"w_arcmin":2.9,"h_arcmin":2.9},
 "generated_utc":"2026-11-15T09:00:00Z","visits":3,"bands":["D4","D5","D6"],
 "summary":{"sources":41,"known_star":33,"known_asteroid":2,"variable":1,"artefact":4,"candidate":1},
 "summary_text":"plain-English paragraph (rules template, or the optional single LLM call)",
 "sources":[
  {"id":"s001","class":"known-star","confidence":0.97,
   "reason":"Moves 10.2″/yr north, matching Gaia DR3 4472832130942575872 within 0.5″.",
   "positions":[{"visit":0,"mjd":60920.1,"ra_deg":269.44825,"dec_deg":4.74161}],
   "motion":{"pmra_masyr":-790,"pmdec_masyr":10050,"sig":25.0,"chance_lines_expected":0.01},
   "flux":{"D4":[123.4,120.1,119.8]},
   "spectrum":[{"lam_um":4.42,"flux":5300.0,"visit":0}],
   "light_curve":[{"mjd":60920.1,"band":"D4","flux":123.4}],
   "crossmatch":[{"cat":"Gaia DR3","id":"4472832130942575872","sep_arcsec":0.4}],
   "flags":["saturated-core"],
   "appearance_class":"red-dwarf"}
 ]}
```
Classes: `known-star` · `known-asteroid` · `candidate-mover` · `variable` · `artefact` · `unknown-static`. `appearance_class` keys into `science/classes.json` (I4) and the 3D library (I5).
