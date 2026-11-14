# Work plan — Planet X & SPHEREx (Shape Up, lite)

**Window:** kick-off Sat 14 Nov ~15:00 → **submit Sun 15 Nov 22:00** (official close 23:59 local time of our Local Event) · ~31 h wall-clock incl. sleep
**People:** Yasen, Sean (Data) · Quirce, Giorgi (Processing) · Niklas (Product) · **Decider:** Quirce · **Challenger:** Niklas
**Approval:** ⏳ pending — each person ticks their row in §8 at kick-off.

> Labels: **[Book]** = Shape Up principle · **[Inference]** = our adaptation for a 5-person, 1.5-day hackathon.
> The split by role (data / processing / product) was chosen by the team; Shape Up would rather split by vertical
> slices. We keep the roles but **force a vertical slice first** (one target end-to-end by CP1) and make every
> handoff a written contract ([CONTRACTS.md](CONTRACTS.md)) so nobody waits. [Inference]

## 1. Assumptions (confirm at kick-off)
- Kick-off ~15:00 Sat; everyone works until ~01:00, sleeps, resumes ~08:30 Sun. *(Recommended confirm)*
- Deadline = local event time; we target **22:00 Sunday** to leave buffer. *(Recommended confirm)*
- Everyone has Python 3.11 + Node 20 and a GitHub account invited to this repo. *(Safe default)*
- Data is pulled on demand (name, coordinates or a drawn zone) with a cache; the 5 targets are pre-warmed (D2, changed 14 Nov). Static frontend + Python API backend. See WORKSPLIT.md.
- Team ≤ 6 people (rule) ✔︎.

## 2. Appetite [Book ch02, ch07]
Fixed time, variable scope, **no extension** (circuit breaker). Build capacity ≈ 5 people × ~16 focused h ≈ **80 person-hours**,
of which the last ~6 h (Sun 16:00–22:00) are reserved for QA, video and submission — **no new scope after freeze**.

## 3. Problem, outcomes, no-gos
- **Problem:** SPHEREx maps the whole sky every 6 months in 102 near-IR colours; nobody can look at it all. Moving and changing objects (brown dwarfs, nearby stars, variables) are found by blinking epochs — we make that possible for anyone, from a link.
- **Must-have outcomes** (the challenge's literal ask + what judges score):
  1. Enter coordinates / name → see the same patch at each SPHEREx epoch as a blink. ✅ required
  2. Works and looks right on all 5 test targets. ✅ required
  3. Understandable by a non-expert (usability is in *Validity*). 
  4. Uses the 102 bands meaningfully (band chips + spectrum on the fly — "extra kudos").
  5. Shareable URL with coordinates (embeddable).
  6. A ≤ 30 s video and complete submission page.
- **Nice-to-have (`~`):** live backend for any coordinates · difference/shift-and-add search · Gaia overlay · flag-a-candidate · molecule filters · λ slider / 3D cube · long-baseline WISE context.
- **No-gos:** see D14 (PSF matching, science-grade photometry, accounts, DB, 3D volume in core path, mobile-first).

## 4. Rabbit holes & spikes [Book ch04]
| Unknown | Status | Resolution |
|---|---|---|
| Do the targets have multiple SPHEREx epochs? | **Answered** (measured): Barnard 3, ε Indi B 4, WISE 0855 3 (DR1 only), RW Aur 3, R Dra ~monthly | patch (D4) |
| Is motion visible? | 1–2 px only | patch: zoom + crosshair + track + diff (D7, D12) |
| LVF makes each exposure a different λ | known | patch: wavelength-matched sequences only (D5) |
| Fetching data fast enough | S3 section reads 0.5–2.5 s/exposure measured | patch (D11); precompute (D2) |
| Saturated bright targets | measured on Barnard | patch: flag + D56/diff (Processing ↔ Product) |
| 3D cube | expensive | cut back to λ slider; volume only `~` (D14) |
| **Spike P0** | Quirce, H0–H3 | Barnard D56 3-epoch frames from the scripts in `spikes/`. Fallback if it fails: use IRSA cutout service. |

## 5. Scopes (by owner — details in each role file)
| ID | Scope | Owner | h | Must/~ | Depends on |
|---|---|---|---|---|---|
| D-1 | Target catalogue C1 | Yasen | 2 | must | — |
| D-2 | Coverage inventory C2 (5 targets) | Yasen | 4 | must | D-1 |
| D-3 | Flag dictionary C3 + quality rules | Sean | 3 | must | — |
| D-4 | Science notes C7 (facts + sources) | Sean | 3 | must | D-1 |
| D-5 | Band/molecule windows table | Sean | 2 | must (molecules ~) | — |
| D-6 | Archival positions (2MASS/AllWISE/Gaia) + Gaia field | Yasen | 2 | must-lite / ~ | D-1 |
| D-7 | Release-update script + data QA of bundles | Yasen + Sean | 2 | must | P4 |
| P0 | Spike: Barnard thin slice | Quirce | 3 | must | — |
| P1 | Frame engine | Quirce | 6 | must | C2 (spike meanwhile) |
| P2 | Difference, track, Gaia | Giorgi | 4 | must | P1 grid |
| P3 | Spectrum | Giorgi | 3 | must | C2 |
| P4 | Precompute & publish | Quirce | 2 | must | P1–P3 |
| P5 | Viewer component `<BlinkCanvas>` | Giorgi | 6 | must | C4 mock |
| P6 | Live API | Quirce | 4 | ~ | P4 |
| P7 | λ slider / cube | Giorgi | 4 | ~ | P1 |
| P8 | Molecule filters | Quirce | 3 | ~ | D-5 |
| U0 | Breadboard, wireframes, URL scheme | Niklas | 2 | must | — |
| U1 | Shell, landing, search, sky picker | Niklas | 4 | must | C1 (mock ok) |
| U2 | Viewer page & controls | Niklas | 5 | must | C6 |
| U3 | Explain layer & states | Niklas | 4 | must | C3, C7 |
| U4 | Guided tour (5 targets) | Niklas | 3 | must | C7 |
| U5 | Spectrum panel | Niklas | 2 | must | P3 |
| U6 | Share / embed | Niklas | 1.5 | must | C5 |
| U7 | Flag a candidate | Niklas | 2 | ~ | — |
| U9 | Submission + video | Niklas (+ all) | 5 | must | everything |
| U10 | Deploy (Vercel) | Niklas | 1 | must | — |

**Load check (must only):** Yasen ~10 h · Sean ~10 h · Quirce ~11 h · Giorgi ~13 h · Niklas ~27.5 h ⚠️
**Imbalance fix [Inference]:** Niklas carries UI + design + submission. So: **Yasen and Sean take over U4 content (tour cards text) and the
submission texts (Detailed Description, NASA data, References) once their data scopes are done (~Sat 23:00)**; Giorgi
owns all viewer-level rendering; Quirce writes the technical part of the description. Niklas keeps design, UX, copy
editing, video and the final submit.

## 6. Critical path
`P0 spike → P1 frame engine (Barnard) → CP1 integrated slice → P4 all bundles → U2/U4 on real data → video → submit`
Everything else hangs off it in parallel. Prefer cutting `~` over touching this chain.

## 7. Timeline & checkpoints
| When (local) | What | Pass criterion | If failing |
|---|---|---|---|
| Sat 15:00 (H0) | Kick-off (45 min): read README + your role file, lock D1–D17, tick §8 | all rows ticked | decider locks |
| Sat 16:00 (H+1) | Mocks committed: `data/targets.json` (Yasen), C4 mock bundle + `<BlinkCanvas>` stub (Quirce/Giorgi), wireframes started | files on `main` | — |
| Sat 17:00 (H+2) | Coverage of all 5 targets known (Data) · URL scheme + name (Niklas) | inventory for ≥ 3 targets | drop the target with no epochs from the demo, keep it as a "no coverage" state |
| **Sat 21:00 (CP1)** | **First integrated slice**: Barnard D56 real frames blinking in Niklas' page | visible on a local build | all hands on the slice until it works; cut P6 |
| Sun 01:00 | Sleep. Push everything first. | `main` builds | — |
| **Sun 11:00 (CP2)** | All 5 targets bundled; diff + spectrum on real data; all must-have UI flows | deployed preview | cut remaining `~`; one person per broken target |
| Sun 12:00 | Video script + shot list frozen | — | — |
| **Sun 16:00 (freeze)** | Feature freeze, deploy to production | public URL works from a phone | ship what works |
| Sun 20:00 | Video ≤ 30 s + all texts reviewed by the team | — | 7-slide fallback |
| **Sun 22:00** | **Submitted** | confirmation | buffer until 23:59 |

**Hill chart:** each owner keeps their scopes in [STATUS.md](STATUS.md) as `uphill` (still figuring out) / `downhill` (just executing) / `done (merged)`. A dot that doesn't move for 3 h = raise your hand. **Sync is exception-driven:** post only when blocked, when a discovery affects a contract, or when a scope is done. [Book ch12 + Inference]

## 8. Approval gate
| Person | Owned scopes | Load (must) | First independent slice (no waiting) | OK? |
|---|---|---|---|---|
| Yasen | D-1, D-2, D-6~, D-7, tour text | ~10 h + texts | `targets.json` for 5 targets from Gaia/SIMBAD | ☐ |
| Sean | D-3, D-4, D-5, D-7, submission texts | ~10 h + texts | `flags.json` from the FLAGS header keys | ☐ |
| Quirce | P0, P1, P4, P6~, P8~ · decider | ~11 h | Spike P0 with `spikes/` scripts | ☐ |
| Giorgi | P2, P3, P5, P7~ | ~13 h | `<BlinkCanvas>` against the mock bundle | ☐ |
| Niklas | U0–U6, U9, U10, U7~ · challenger | ~23 h after rebalance | Breadboard + wireframes | ☐ |

## 9. Collision rules [Inference]
Folder ownership and branch rules: **D16**. Contracts first (C1–C7 mocks at H+1). Trunk-based: branches live hours, not days; `main` always builds.
Registry files: `config.yaml` → Quirce · `web/package.json` → Niklas · `requirements.txt` → Quirce (ask to add a dependency).

## 10. Cut order (if behind) [Book ch13]
1. P6 live API → static only, "process this position" shows a friendly message
2. P7/U8 cube & λ slider
3. U7 flag-a-candidate
4. P8 molecule filters (keep detector band chips)
5. Gaia field overlay (keep the archival-positions list: cheap and the most convincing motion visual)
6. Side-by-side mode (keep blink + diff)
7. Sky picker (keep search box + chips)
**Never cut:** blink of the 5 targets, wavelength-matched frames, explanation panel, shareable URL, the video.
