# Sources for data/targets.json

Generated 2026-11-14T14:30:29Z by `data/scripts/targets.py` (live queries to IRSA TAP, https://irsa.ipac.caltech.edu/TAP).
Re-run to regenerate. Values marked LITERATURE must be checked against the cited paper before launch.

| Target | Field | Source |
|---|---|---|
| barnards-star | ra, dec, pm, parallax, ref_epoch | Gaia DR3 4472832130942575872 (G=8.19) via IRSA TAP gaia_dr3_source |
| barnards-star | archival 2MASS | 17574849+0441405 via IRSA TAP fp_psc (nearest within 3″ of the propagated position) |
| barnards-star | archival AllWISE | J175747.94+044323.8 via IRSA TAP allwise_p3as_psd (nearest within 3″ of the propagated position) |
| eps-indi-b | ra, dec, pm, parallax, ref_epoch | Gaia DR3 6412596012146801152 (G=18.03) via IRSA TAP gaia_dr3_source |
| eps-indi-b | archival 2MASS | 22041052-5646577 via IRSA TAP fp_psc (nearest within 3″ of the propagated position) |
| eps-indi-b | archival AllWISE | J220415.75-564724.4 via IRSA TAP allwise_p3as_psd (nearest within 3″ of the propagated position) |
| wise-0855 | ra, dec, ref_epoch | AllWISE J085510.74-071442.5 (W2=13.704) via IRSA TAP allwise_p3as_psd; epoch = w1mjdmean |
| wise-0855 | pmra, pmdec | LITERATURE, unverified: research/01-data.md [U]; check Luhman & Esplin 2016 (arXiv:1605.08620) |
| wise-0855 | plx_mas | not set: needs a literature value with citation |
| wise-0855 | archival 2MASS | not detected (no source within 3″ of the propagated position) |
| rw-aurigae | ra, dec, pm, parallax, ref_epoch | Gaia DR3 156430822114424576 (G=12.18) via IRSA TAP gaia_dr3_source |
| rw-aurigae | archival 2MASS | 05074953+3024050 via IRSA TAP fp_psc (nearest within 3″ of the propagated position) |
| rw-aurigae | archival AllWISE | J050749.54+302404.7 via IRSA TAP allwise_p3as_psd (nearest within 3″ of the propagated position) |
| r-draconis | ra, dec, pm, parallax, ref_epoch | Gaia DR3 1648328016354496384 (G=6.37) via IRSA TAP gaia_dr3_source |
| r-draconis | archival 2MASS | 16324023+6645180 via IRSA TAP fp_psc (nearest within 3″ of the propagated position) |
| r-draconis | archival AllWISE | J163240.19+664517.9 via IRSA TAP allwise_p3as_psd (nearest within 3″ of the propagated position) |

Archival positions are checked automatically: each must lie within 3″ of the position propagated with the proper motion (column `offset_from_prediction_arcsec`). Text fields (kind, variability, notes) come from the team research (research/01-data.md) and need the science notes (D-4) for citations.
