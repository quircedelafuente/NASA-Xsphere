# Spikes — scripts that already worked during research (14 Nov)

Setup: `python3 -m venv venv && venv/bin/pip install astropy astroquery pyvo pandas reproject photutils fsspec aiohttp`

| Script | What it proves | Notes |
|---|---|---|
| `sia_coverage_5targets.py` | Coverage + epoch clusters for the 5 targets (propagates pm to 2026.0, SIA on DR1/QR3 wide+deep) | Writes `sia_<target>.ecsv`. Results already saved in `sia/` |
| `sia/*.ecsv` | Full SIA tables for the 5 targets (all metadata incl. `cloud_access` S3 keys) | Start D-2 from these without querying |
| `cutout_downloader.py` | Parallel IRSA cutouts with retries (`python cutout_downloader.py WISE0855 5,6 0.05`) | ~1 cutout/s, HTTP 503s → retries; needs `sia/targets2026.json` + ecsv in cwd |
| `s3_section_read.py` | Byte-range read of one exposure from the public S3 bucket | 0.5–2.5 s vs 8.6 s via cutouts |
| `propagate_pm_check.py` | Barnard lands within ~1 px of the Gaia-propagated position in every epoch | expects SIA VOTables in `dl/` — adapt paths to `sia/*.ecsv` |
| `reproject_bench.py` | `reproject_interp/adaptive/exact` timings (64² interp ≈ 10 ms) | synthetic WCS |
| `forced_phot_centroids.py` | Forced photometry + centroids per exposure | produced the WISE 0855 S/N numbers |
| `epoch_shift.py` | Centroid shift per epoch vs first epoch (`python epoch_shift.py Barnard 0`) | Barnard +9.8″ Dec / 0.99 yr; WISE 0855 −7.4″ RA |

These are throwaway research code: copy ideas into `data/` and `processing/`, don't import from here.
