# I4 · Science files (chunk C delivers, in `science/`)
Every number carries a `source` (citation or URL).

`flags.json`: `{"bits":{"1":{"name":"OVERFLOW","class":"hard|soft|info","plain":"Too bright: the detector saturated here."}}, "hard_mask_bits":[...]}`

`bands.json`: `{"molecules":[{"id":"co2","name":"Carbon dioxide (ice/gas)","lam_um":4.27,"window_um":[4.2,4.33],"source":"..."}]}`

`classes.json`:
```json
{"brown-dwarf":{"rules":{"dip_um":[3.3],"rise_um":[4.5],"min_motion_px_yr":0.3},
  "temp_K":[250,2500],"radius_rjup":[0.8,1.2],
  "appearance":{"model":"banded-ball","features":["cloud-bands"],"eye_colour_from_temp":true},
  "plain":"A failed star: too small to shine like the Sun, glowing faintly in infrared.","source":"..."}}
```
`notes/<target-id>.md`: 3–5 cited facts per target, written for non-experts.
