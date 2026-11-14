# I1 · API (chunk A serves)

All coordinates ICRS degrees. Jobs are async: POST returns a job id, GET polls status + progress; partial results appear as visits finish.
```
GET  /resolve?q=barnard            → {"matches":[{"name":"Barnard's Star","ra_deg":269.448,"dec_deg":4.739,"source":"targets.json|Sesame"}]}
POST /view   {"ra_deg","dec_deg","fov_arcmin":3,"bands":["D4","D5","D6"]}   → {"job":"v_ab12"}
GET  /view/v_ab12                  → {"status":"fetching|merging|done","progress":0.4,"visits":[...],"frames_png":{...},"stacks_url":"/files/v_ab12/stacks.npz"}
POST /scan   {"box":{"ra_deg","dec_deg","w_arcmin","h_arcmin"}} → {"job":"s_cd34"}
GET  /scan/s_cd34                  → I3 report + {"status","progress"}
GET  /object/barnards-star         → targets.json entry + latest report + science notes
```

Errors: `{"error":"name-not-found|outside-coverage|nasa-busy|zone-too-large","message":"plain English"}`
