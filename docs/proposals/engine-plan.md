# Data engine plan: keep pulling the data, sort it smartly (14 Nov 2026)

Fits the team repo (quircedelafuente/NASA-Xsphere): this engine **is** Yasen's D-2 (inventory) + "release-update script", and it feeds Processing's bundles (C4). Contract names below are the team's.

## The core problem, and the answer
Full SPHEREx photos are 65 MB each, **17–165 GB per star**. A browser can't take that, and NASA's server throttles us ("Server busy" seen today at 8 parallel requests).
**Answer: do the heavy work on our side, ahead of time, and ship only small results.**
Raw photo → small cutout (~4 MB, mostly a star-shape table) → finished frames + numbers (**a few KB each**). The website only ever loads the last step.

## The 5 machines in the engine

| # | Part | What it does | Runs where | Hackathon? |
|---|---|---|---|---|
| 1 | **Watcher** | Once a week, asks every source "anything new for our targets since last time?" Writes only what's new to the inventory (C2, append-only) | GitHub Actions on a weekly schedule (free), or a cron on the M2 | ✅ yes, as a script you run by hand; schedule after |
| 2 | **Fetcher** | Downloads only the needed pixels: byte-range reads from NASA's public Amazon copy (S3, 0.5–2.5 s each), cutout service as fallback. Max ~4 at a time, retries on "busy". Keeps a local cache, never in git | Same machine as 1 | ✅ |
| 3 | **Processor** | Per detector and per sky pass: align and merge the photos, make difference images, measure position and brightness at every wavelength. Output = bundle (C4) | Same machine; the MacBook Pro if it gets heavy | ✅ (Processing role owns the code) |
| 4 | **Classifier** | Sorts what it finds into plain categories with a confidence and a reason (see below) | Same machine | 🟡 rules version only |
| 5 | **Publisher** | Commits the small bundles → website redeploys itself (Vercel) | GitHub → Vercel | ✅ |

**Plus the MCP door:** a small MCP server exposes the same functions (`find_images`, `get_frames`, `measure`, `classify`, `gaia_nearby`), so Claude can run the engine in plain English during the build and in the pitch. ~30 lines on top.

## Sources it pulls from, and how

| Source | What we take | How (no login for any) | How often new |
|---|---|---|---|
| **SPHEREx @ IRSA** (DR1 + QR3, wide + deep) | Photo list per target, then pixels | SIA/TAP query → S3 byte ranges | **Weekly** |
| **Gaia DR3** | Exact position, motion, distance of known stars | ESA or IRSA TAP query | Fixed (next release DR4, date unverified) |
| **AllWISE / CatWISE2020 / 2MASS** | Where the star was 10–25 years ago ("where it was" dots) | IRSA TAP | Fixed |
| **SIMBAD / Sesame** | Name → coordinates, object type ("brown dwarf", "Mira variable") | CDS Sesame name resolver | Fixed |
| **JPL Horizons / Minor Planet Center** | Is a known asteroid or comet at this spot on this date? | Web API, by position + date | Daily (new asteroids) |
| **NEOSSat @ CADC** (Canada) | Extra photos of asteroids | CADC TAP | Optional, after the hackathon |

## The "smart" sorting: classifier
Three layers, each one cheap. Every label comes with **why**, so a non-expert sees the reason.

1. **Is this photo usable?** (rules from Sean's flag dictionary, C3). Hard flags at the star → reject; saturated → keep for position only; edge of chip → reject. Output: `usable` + `reject_reason`, already in C2.
2. **What is this object doing?** (measurements across passes)
   - Moves consistently across ≥3 passes → **mover** (speed in px/yr and ″/yr)
   - Brightness changes more than its noise → **variable** (amplitude, light curve when there are many passes, e.g. R Draconis)
   - Seen in one photo only → **artifact** (cosmic ray, ghost, glint)
3. **What kind of thing is it?** (cross-checks + colour)
   - Matches Gaia with the same motion → **known star** ✓ validates our measurement
   - Matches a known asteroid at that date (Horizons/MPC) → **known asteroid**
   - Moves, but nothing known is there → **candidate** (never "discovery", per team rule)
   - SPHEREx spectrum shape gives a type hint: brown dwarfs are dark around 3.3 µm (methane) and bright at 4.5 µm; ices and water show their own dips. → "brown-dwarf-like", "star-like", "galaxy-like"

**Hackathon version:** layers 1–3 as plain rules with scores (transparent, explainable, enough for 5 targets).
**After:** train a small model on thousands of objects that already have labels (SIMBAD types + Gaia motions) using the same features (motion, colours, variability, spectrum dips). Claude via MCP writes the plain-language explanation for each candidate.

## What the user's browser gets
Only the bundle: per target, `meta.json` + small PNG frames + difference frames + spectrum/light-curve points. **A few hundred KB per star.** A typed-in star that isn't prepared yet → (later) the server runs 2–4 on demand, stores the result, and the second visitor gets it instantly.

## Order to build (inside the team plan)
1. Watcher v0 = D-2 inventory script (SIA → C2), run by hand for the 5 targets. **← Yasen, H+2/H+3**
2. Fetcher with S3 reads + cache + retry (shared with Processing)
3. Classifier layer 1 (with Sean's flags) and layer 2 numbers in C2/bundle
4. Gaia/WISE cross-match (Yasen's D-6) → layer 3 "known star ✓"
5. Weekly schedule + MCP server, if time is left on Sunday

## Open decisions (team, each with a recommendation)
1. Weekly run on **GitHub Actions** (free, runs when your laptops are off). **Recommend yes**; the M2 is the fallback.
2. Classifier = **rules for the hackathon**, model later. **Recommend yes.**
3. Asteroid check via **JPL Horizons** included in layer 3. **Recommend: only if done by Sunday 11:00.**
4. Move this file to `data/ENGINE.md` once the team agrees.
