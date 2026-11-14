# NASA-Xsphere — Planet X & SPHEREx

**NASA Space Apps Challenge 2026 · [Planet X and SPHEREx](https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/)** (difficulty: Advanced)

> **Submission closes Sun 15 Nov 2026, 23:59 local time — we submit by 22:00.**

## What we're building (one sentence)
A public web tool where anyone types a star's name or sky coordinates and sees **the same patch of sky at each SPHEREx
epoch blinking like a little video**, so moving objects (nearby stars, brown dwarfs) and changing ones (variable stars) jump
out — with the motion explained, the 102 infrared colours usable, and a shareable link. It's the blink comparator that
found Pluto in 1930, for NASA's newest all-sky survey.

Must work on: **Barnard's Star · ε Indi B · WISE 0855−0714 · RW Aurigae · R Draconis**.

## Start here (everyone, 15 min)
1. Read this file and **[PLAN.md](PLAN.md)** (timeline, checkpoints, cut order).
2. Read **your role file**:

| Role | People | File |
|---|---|---|
| 1 · Data — prepare, classify, choose the data | **Yasen, Sean** | [roles/01-data.md](roles/01-data.md) |
| 2 · Processing — algorithm, pipeline, bridge to the frontend | **Quirce, Giorgi** | [roles/02-processing.md](roles/02-processing.md) |
| 3 · Product engineer — product, UX, design, submission | **Niklas** | [roles/03-product.md](roles/03-product.md) |

3. Read **[CONTRACTS.md](CONTRACTS.md)** (what you hand to whom, exact formats) and **[DECISIONS.md](DECISIONS.md)** (what's locked).
4. At kick-off: tick your row in PLAN.md §8 and keep your scopes updated in **[STATUS.md](STATUS.md)**.

Each role file has: **mission · scopes (what "done" looks like) · decisions you must take (with a recommendation) ·
what to research · outputs & deadlines · dependencies/contracts · rabbit holes to avoid.**

## What the research already found (14 Nov)
- All data is public (IRSA SIA/TAP, cutout service, S3 bucket `nasa-irsa-spherex`), no login.
- The 5 targets have **3–4 SPHEREx epochs** each (R Draconis ~monthly: it's in the north ecliptic deep field).
- Motion between epochs is **only 1–2 pixels** (6.15″/px) — measured in real data for Barnard's Star and WISE 0855 and it
  matches their proper motions. The UI must make it visible (zoom, crosshair, track, difference mode, archival positions).
- **Each exposure sees the target at a different wavelength** (linear variable filter) → never blink across mixed wavelengths.
- Catalogue positions of fast movers are arcminutes off today → always propagate proper motion to the observation date.
- Bright targets (Barnard, RW Aur, R Dra) are saturated; WISE 0855 only appears at 3.8–5 µm after co-adding each epoch.
- Full research: [research/01-data.md](research/01-data.md) · [research/02-processing.md](research/02-processing.md) · [research/03-product.md](research/03-product.md). Working scripts: [spikes/](spikes/).

## Repo layout (planned)
```
data/            Data role: targets.json, inventory/, flags.json, bands.json, science-notes.md, scripts/
processing/      Processing role: frames.py, motion.py, spectrum.py, precompute.py, (api.py)
web/             Vite + React + TS app
  public/bundles/  precomputed bundles (Processing)
  src/viewer/ src/data/   <BlinkCanvas>, loaders (Giorgi)
  src/ui/ src/pages/ src/styles/   (Niklas)
design/          wireframes (Niklas)
submission/      video script, texts, references (Niklas + all)
spikes/          research scripts that already work + SIA tables for the 5 targets
research/        full research reports
```

## Rules of the road
- Branch per scope (`data/…`, `proc/…`, `web/…`), merge to `main` within hours, `main` always builds.
- Only edit folders you own (D16). Changing a contract = tell the consumers first.
- Words: say **"candidate"**, never "discovery". English everywhere. AI-generated media must be watermarked.
- Post in the team chat only when: blocked · a discovery changes a contract · a scope is done.

## Key links
SPHEREx at IRSA https://irsa.ipac.caltech.edu/Missions/spherex.html · Tutorials https://caltech-ipac.github.io/irsa-tutorials/spherex/ ·
Explanatory Supplement https://irsa.ipac.caltech.edu/data/SPHEREx/docs/SPHEREx_Expsupp.pdf · WiseView http://byw.tools/wiseview ·
Judging guide https://www.spaceappschallenge.org/resources/judging-awards-guide · Submission guide https://www.spaceappschallenge.org/resources/project-submission-guide/
