# Decision log

**Decider:** Quirce (requested the plan; breaks deadlocks after hearing everyone) · **Challenger:** Niklas (pokes holes in scope and cuts)
**Rule:** a logged decision is not reopened because of a preference — only with new information (a hill-chart reason: stuck, collision, data says otherwise) and the decider.
**Classes:** **Team-lock** = must be agreed before parallel work (others build against it) · **Consultative** = owner proposes, named person reviews · **Autonomous** = owner decides alone.

Status: `PROPOSED` until the kick-off (H0–H1), then `LOCKED`.

| # | Decision | Class | Owner / locked by | Constrains | Rationale |
|---|---|---|---|---|---|
| D1 | **Product = "SPHEREx blink comparator"**: pick a target (name, coordinates, demo chip) → see the same sky patch at each SPHEREx epoch as a blink / difference / side-by-side, with crosshair, predicted motion track, flags and a spectrum. | Team-lock | Quirce (after kick-off) | everything | Exactly what the challenge asks; everything else is extra. |
| D2 | **On-demand data** *(changed 14 Nov, Yasen; replaces "Demo is 100 % static")*: NASA data is fetched only when a user searches a name, enters coordinates or draws a zone; results are cached; the 5 official targets are **pre-warmed in the cache** so judges never wait. See WORKSPLIT.md. | Team-lock | Quirce (please confirm) | Chunks A + B, frontend | The point of the tool is any position and autonomous zone scans; caching + pre-warm keeps the demo safe. |
| D3 | **Data releases** = DR1 + QR3, wide + deep: `spherex_dr1`, `spherex_dr1_deep`, `spherex_qr3`, `spherex_qr3_deep` (list lives in `config.yaml`, adding a release = re-run). QR2 excluded (old pipeline, must not be mixed with R7). | Team-lock | Data | Processing | "Easy to update with new releases" is an explicit consideration. |
| D4 | **Epoch = one survey pass**: sort exposures by time, split when the gap is **> 60 days**; if a group spans > 60 days (ecliptic-pole deep field, e.g. R Dra) split it **by calendar month**. Expect 3–4 epochs for 4 targets, ~18 monthly epochs for R Dra. | Team-lock | Data | Processing, Product copy | Measured: a pass spreads over 1–7 weeks with small trailing clusters; R Dra is observed ~monthly (2,493 images). |
| D5 | **Never blink across different wavelengths.** All frames in one sequence share a band window (`D1…D6`, `D56`, molecule windows). | Team-lock | Processing | Data band choice, Product band chips | LVF: each exposure samples a different λ; mixing them fakes variability/motion. Top validity risk. |
| D6 | **Positions are propagated with proper motion** (Gaia DR3 @2016.0; WISE 0855 is not in Gaia → AllWISE position @~2010.5 + literature pm) to each exposure's `MJD-AVG`. Catalogue positions are never used directly for cutouts. | Team-lock | Data (values) + Processing (math) | C1, C2, C4 | Measured: Barnard's J2000 position is 4.4′ off; WISE 0855's 2010 position ~2′ off. |
| D7 | **Common grid**: TAN, north up, native 6.15″/px, 64×64 by default (≈6.6′). Display upscales with nearest-neighbour. | Team-lock | Processing | C4, C6 | Motion is only 1–2 px; smoothing hides it. |
| D8 | **One stretch per sequence** (asinh, percentiles over all frames), re-stretchable client-side from float32. | Team-lock | Processing | C4, C6 | Per-frame stretch causes flicker and destroys variability. |
| D9 | **Contracts C1–C7** in [CONTRACTS.md](CONTRACTS.md), with mock files committed in Phase 0. | Team-lock | all → Quirce | all | Lets the three roles start in parallel. |
| D10 | **Stack**: Python 3.11 (astropy, astroquery, reproject, photutils, fsspec/s3fs, numpy) for data + processing; frontend = Vite + React + TypeScript, canvas 2D for frames, Aladin Lite v3 for the sky map, a light chart lib for spectra; static deploy on Vercel. | Team-lock | Quirce + Niklas | repo layout | Everyone can run it; static deploy matches D2. Niklas may swap UI libs (Autonomous) as long as C6 holds. |
| D11 | **Data access** = byte-range reads of the public S3 bucket `nasa-irsa-spherex` (astropy `use_fsspec=True` + `.section`), IRSA cutout service as fallback, with retries. | Consultative | Processing (Data reviews) | Data inventory includes S3 keys | Measured ~0.5–2.5 s vs ~8.6 s per exposure; the cutout service also always ships a 3.9 MB PSF table. |
| D12 | **Motion story**: SPHEREx shows 1–2 px shifts, so the viewer must give zoom + crosshair + predicted track + difference mode; a long-baseline context (unWISE/WiseView link or overlay) is `~`. | Consultative | Niklas (Processing reviews) | Product S10, Processing S6 | Avoid a demo where "nothing moves". |
| D13 | **Words**: we say **"candidate"**, never "discovery". | Team-lock | Niklas | copy, video | Validity; judges are scientists. |
| D14 | **No-gos** for this hackathon: PSF matching (HOTPANTS etc.), science-grade forced photometry, user accounts/login, our own database, a real volume-rendering 3D cube in the core path (only `~` after freeze-safe), mobile-first design. | Team-lock | Quirce | all | Rabbit holes that don't fit ~35 h. |
| D15 | **Submission rules**: everything in English; demo = 30-second video (≤30 s, otherwise ineligible); AI ("SI") use disclosed; AI-generated images/video watermarked; no NASA logos in generated assets; nobody under 18 on screen; every external resource in References. | Team-lock | Niklas (owner of submission) | Product S13 | Official submission guide. |
| D16 | **Repo & collision rules**: trunk-based, short branches (`data/…`, `proc/…`, `web/…`), merge to `main` at least every few hours, `main` always deployable. Folder owners: `data/` → Data; `processing/` + `web/public/bundles/` + `web/src/viewer|data/` → Processing; `web/src/ui|pages|styles/` + `submission/` → Niklas. `config.yaml` → Quirce. `web/package.json` → Niklas (others ask). | Team-lock | Quirce | all | No two people editing the same files. |
| D17 | **Feature freeze** Sunday 16:00 local; after that only bug fixes, copy and the video. **Submit by Sunday 22:00** (official close 23:59 local). | Team-lock | Quirce | all | Fixed time, variable scope; buffer for upload problems. |

## Decisions each role takes alone (Autonomous) — examples
- Data: which bonus targets, exact rejection thresholds inside C3's classes, script structure.
- Processing: reprojection method, co-add algorithm details, caching, code structure.
- Product: layout, typography, colour palette (colour-blind safe), component library, copy wording (within D13).

Add new rows at the bottom. Format: `| D18 | … | class | who | constrains | why |`.
