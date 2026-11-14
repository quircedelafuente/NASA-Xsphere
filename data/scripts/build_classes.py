"""Builds science/classes.json (C3 of WORKSPLIT, contract I4) and science/notes/<target-id>.md.

  python data/scripts/build_classes.py

Readers: processing/discovery/classify.py takes `discovery_rules`; web/lib3d takes each class's `appearance`;
the frontend takes `plain`. Every number has a source id from SOURCES below. `checked` says how far it was verified:
  "read"       = the number was read on the source page on 14 Nov 2026
  "search"     = the number was quoted from that source in a web search on 14 Nov 2026; the page itself was not opened
  "calculated" = follows from other numbers here
  "team"       = a working threshold chosen by the team, tested on our 5 targets, not a literature value
"""
import json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[2]

SOURCES = {
 "mamajek": {"cite": "E. Mamajek, 'A Modern Mean Dwarf Stellar Color and Effective Temperature Sequence', version 2022.04.16 (extends Pecaut & Mamajek 2013, ApJS 208, 9)",
             "url": "https://www.pas.rochester.edu/~emamajek/EEM_dwarf_UBVIJHK_colors_Teff.txt"},
 "dawson2004": {"cite": "Dawson & De Robertis 2004, 'Barnard's Star and the M Dwarf Temperature Scale' (Teff 3134 +/- 102 K, R 0.200 +/- 0.008 Rsun), as quoted on Wikipedia", "url": "https://en.wikipedia.org/wiki/Barnard%27s_Star"},
 "luhman2014": {"cite": "Luhman 2014, discovery of WISE J085510.83-071442.5 (Teff 225-260 K)", "url": "https://arxiv.org/abs/1404.6501"},
 "ydwarfs2026": {"cite": "'The Coldest Known Y Dwarfs: Estimates of their Effective Temperatures' (Y dwarfs: Teff < 500 K)", "url": "https://arxiv.org/abs/2603.24740"},
 "kirkpatrick2021": {"cite": "Kirkpatrick et al. 2021, 20-pc census of 525 L, T and Y dwarfs (old brown dwarfs have radii very close to 1 Jupiter radius)", "url": "https://arxiv.org/abs/2011.11616"},
 "king2010": {"cite": "King et al. 2010, A&A 510, A99, 'eps Indi Ba, Bb: a detailed study of the nearest known brown dwarfs' (Teff 1300-1340 K and 880-940 K)", "url": "https://www.aanda.org/articles/aa/abs/2010/02/aa12981-09/aa12981-09.html"},
 "chen2022": {"cite": "'Precise Dynamical Masses of Epsilon Indi Ba and Bb' (2022): dynamical masses of eps Indi Ba and Bb (66.92 +/- 0.36 and 53.25 +/- 0.29 Jupiter masses)", "url": "https://arxiv.org/abs/2205.08077"},
 "gcvs": {"cite": "General Catalogue of Variable Stars, type M (Mira): V amplitude 2.5-11 mag, period 80-1000 d", "url": "https://arxiv.org/abs/1310.2412"},
 "mira_models": {"cite": "'Dynamical Opacity-Sampling Models of Mira Variables. II' (model series: Rosseland radius 241-260 Rsun, Teff 2750-2860 K). Which of the Mira model papers the search quoted is not certain: open it before citing in the submission", "url": "https://arxiv.org/abs/1107.3619"},
 "mira_iota": {"cite": "IOTA/FLUOR interferometry of Mira stars (R Aql: Teff 3072 +/- 161 K, Rosseland radius 250 Rsun)", "url": "https://arxiv.org/abs/astro-ph/0004013"},
 "mira_kamp": {"cite": "Spectro-interferometric study of Miras: near-infrared K amplitudes typically 0.3-0.8 mag, bolometric 0.5-1.2 mag. Which paper the search quoted is not certain: open it before citing in the submission", "url": "https://www.aanda.org/10.1051/0004-6361/201527614"},
 "ttauri": {"cite": "T Tauri stars: ages < 10 Myr, masses < 2 Msun; spectral types K0-M6 (Barrado y Navascues & Martin 2003; LAMOST DR6 study)", "url": "https://arxiv.org/abs/2305.09237"},
 "rwaur": {"cite": "'Recurring Occultations of RW Aurigae by Coagulated Dust in the Tidally Disrupted Circumstellar Disk' (dimmings of ~2 mag in 2010-11 and > 2 mag in 2014-16)", "url": "https://arxiv.org/abs/1512.03745"},
 "neowise_thermal": {"cite": "'Asteroid thermal modeling in the presence of reflected sunlight with an application to WISE/NEOWISE observational data': at 3.4 and 4.6 um asteroid fluxes mix reflected sunlight and thermal emission", "url": "https://arxiv.org/abs/1605.06490"},
 "atlas3i": {"cite": "'SPHEREx Discovery of Strong Water Ice Absorption and an Extended Carbon Dioxide Coma in 3I/ATLAS' (2025 (CO2 gas at 4.26 um, coma >= 30 px ~ 348,000 km; gas windows 3.0 / 4.26 / 4.7 um)", "url": "https://arxiv.org/abs/2508.15469"},
 "reports": {"cite": "Our own runs on the 5 targets, 14 Nov 2026", "url": "processing/discovery/reports/"},
}

READ = {"mamajek", "luhman2014"}          # pages opened and read; everything else was seen quoted in search results

def v(value, src, checked=None, note=None):
    if checked in (None, "read"):
        checked = "read" if src in READ else "search"
    d = {"value": value, "source": src, "checked": checked}
    if note: d["note"] = note
    return d

# Same numbers as the classifier's built-in defaults (processing/discovery/classify.py), so delivering this file does
# not change any result; it records where each science threshold comes from. Plain numbers: classify.py reads them as is.
DISCOVERY_RULES = {
 "brown_dwarf_d6_over_d4": 1.5,
 "mira_min_ratio": 2.5,
 "red_dwarf_min_bp_rp": 2.0,
 "variable_min_ratio": 1.25,
}
DISCOVERY_RULES_WHY = {
 "brown_dwarf_d6_over_d4": v(1.5, "reports", "team", "Brightness at 4.7 um over brightness at 3.1 um. A plain star falls to ~0.44 here (calculated: Rayleigh-Jeans tail, (3.12/4.71)^2); methane at 3.3 um makes T and Y dwarfs much brighter at 4.7 um. Separates eps Indi B and WISE 0855 from every field star in our 5 reports. Not a published limit."),
 "mira_min_ratio": v(2.5, "reports", "team", "Factor between brightest and faintest visit above which a variable is drawn as a Mira. 2.5 = 1 magnitude. Our R Dra shows a factor ~17 (halo light, core saturated); RW Aur 1.9. Caution: published K-band amplitudes of Miras are 0.3-0.8 mag (factor 1.3-2.1, source mira_kamp), so a quiet Mira can fall below this and be drawn as a young star. The GCVS definition (2.5-11 mag) is for visible light, not infrared."),
 "red_dwarf_min_bp_rp": v(2.0, "mamajek", "read", "Gaia colour BP-RP. Table: M0V = 1.84, M2V = 2.23, so 2.0 means 'about M1 or later'."),
 "variable_min_ratio": v(1.25, "reports", "team", "Smallest brightest/faintest ratio we call variable (with the chi-square test). Chosen above our photometry scatter; not a literature value."),
}

CLASSES = {
 "red-dwarf": {
  "plain": "A small, cool star, the most common kind in the Milky Way. Faint in visible light, easy to see in infrared.",
  "rules": {"gaia_bp_rp_min": DISCOVERY_RULES_WHY["red_dwarf_min_bp_rp"],
            "spectrum": "Brightest near 1-2 um, then falls steadily to 5 um (no rise at the red end).",
            "motion": "Nearby ones move measurably: Barnard's Star 10.39 arcsec/yr (data/science-notes.md)."},
  "temp_K": v([2380, 3850], "mamajek", note="M9V to M0V"),
  "radius_rsun": v([0.102, 0.588], "mamajek", note="M9V to M0V"),
  "appearance": {"model": "red-dwarf", "temp_K": v(3210, "mamajek", note="M4V, the type of Barnard's Star"), "features": ["starspots", "flares"], "eye_colour_from_temp": True},
 },
 "brown-dwarf": {
  "plain": "A failed star: too small to shine like the Sun, glowing faintly in infrared as it cools.",
  "rules": {"d6_over_d4_min": DISCOVERY_RULES_WHY["brown_dwarf_d6_over_d4"],
            "dip_um": v([1.6, 2.2, 3.3], "king2010", "read", "Methane bands of T dwarfs (windows in data/bands.json). The 3.3 um band is the deepest."),
            "rise_um": v([4.5], "luhman2014", "read", "Cold brown dwarfs are brightest at 4-5 um; WISE 0855 was found in the WISE 4.6 um band and we see it only above ~3.8 um."),
            "motion": "The ones SPHEREx can see are close, so they move: our two are 4.7 and ~8.1 arcsec/yr (data/science-notes.md)."},
  "temp_K": v([225, 2270], "mamajek", note="Upper end: L0 = 2270 K (mamajek). Lower end: WISE 0855, the coldest known, 225-260 K (luhman2014). Y dwarfs are below 500 K (ydwarfs2026)."),
  "radius_rjup": v([0.9, 1.0], "kirkpatrick2021", note="'Very close to 1 Jupiter radius'. Mamajek's table gives 0.091-0.104 Rsun for L5 to Y0 = 0.9-1.0 Rjup (calculated, 1 Rjup = 0.1028 Rsun)."),
  "mass_mjup_examples": v([53.25, 66.92], "chen2022", note="eps Indi Bb and Ba, measured from their orbit. The usual 13-80 Jupiter-mass range for the class was not re-checked: do not quote it yet."),
  "appearance": {"model": "brown-dwarf", "temp_K": v(1000, "king2010", "team", "Mid T dwarf, between eps Indi Bb (880-940 K) and Ba (1300-1340 K)."), "features": ["cloud-bands"], "eye_colour_from_temp": True,
                 "note": "Below ~700 K the true colour is black to the eye: lib3d draws it warmer so it is visible and must label that."},
 },
 "mira": {
  "plain": "A swollen, dying red giant that pulses: it brightens and fades over months, over and over.",
  "rules": {"variable_ratio_min": DISCOVERY_RULES_WHY["mira_min_ratio"],
            "period_days": v([80, 1000], "gcvs"), "visual_amplitude_mag": v([2.5, 11], "gcvs"),
            "k_band_amplitude_mag": v([0.3, 0.8], "mira_kamp"),
            "motion": "None: these are far away."},
  "temp_K": v([2750, 3072], "mira_models", note="Models 2750-2860 K (mira_models); R Aql measured 3072 +/- 161 K (mira_iota). The temperature changes through the cycle."),
  "radius_rsun": v([241, 260], "mira_models", note="Rosseland radius; R Aql measured 250 Rsun (mira_iota). The radius depends on the wavelength it is measured at."),
  "appearance": {"model": "mira", "temp_K": v(2800, "mira_models", note="middle of the model range"), "features": ["pulsation", "extended-glow"], "eye_colour_from_temp": True},
 },
 "young-star": {
  "plain": "A newborn star, a few million years old, still wrapped in the disk of gas and dust it formed from.",
  "rules": {"variable_ratio_max": DISCOVERY_RULES_WHY["mira_min_ratio"],
            "variability": v("irregular; dust from the disk can dim it by ~2 mag for months to years", "rwaur"),
            "spectrum": "Extra infrared light from the warm disk: flatter from 2 to 5 um than a bare star of the same temperature.",
            "motion": "None: the nearest star-forming regions are ~140 pc away (data/science-notes.md)."},
  "age_myr_max": v(10, "ttauri"), "mass_msun_max": v(2, "ttauri"),
  "temp_K": v([2810, 5270], "mamajek", "calculated", "Spectral types K0 to M6 (ttauri) on the dwarf temperature scale: K0V = 5270 K, M6V = 2810 K. Young stars of the same type can differ by ~100-200 K."),
  "appearance": {"model": "young-star", "temp_K": v(4440, "mamajek", "calculated", "K5V, mid-range. RW Aur's own temperature is not in our notes yet."), "features": ["dust-disk", "jets", "flicker"], "eye_colour_from_temp": True},
 },
 "star": {
  "plain": "An ordinary star far in the background. It stays put and keeps its brightness.",
  "rules": {"d6_over_d4_typical": v(0.44, "reports", "calculated", "Rayleigh-Jeans tail between the centres of D4 (3.12 um) and D6 (4.71 um): (3.12/4.71)^2."),
            "motion": "Not significant over the SPHEREx baseline.", "variability": "Below variable_min_ratio."},
  "temp_K": v([3850, 5770], "mamajek", note="M0V to G2V (the Sun's type): what dominates a SPHEREx field. Hotter stars exist but are rare."),
  "appearance": {"model": "star", "temp_K": v(5270, "mamajek", note="K0V"), "features": [], "eye_colour_from_temp": True},
 },
 "asteroid": {
  "plain": "A rock orbiting the Sun. It crosses the patch so fast that it shows up in one visit and is gone in the next.",
  "rules": {"seen_in_visits": v(1, "reports", "team", "Our rule: a source seen once, at the place and date where SkyBoT puts a known asteroid."),
            "spectrum": v("At 3.4 and 4.6 um its light is a mix of reflected sunlight and its own heat", "neowise_thermal"),
            "motion": "Too fast to link between visits 6 months apart. Speed on the sky and surface temperature were not re-checked: no numbers yet."},
  "appearance": {"model": "asteroid", "features": ["irregular-rock"], "eye_colour_from_temp": False},
 },
 "comet": {
  "plain": "A dirty snowball from the outer Solar System. Near the Sun its ices turn to gas and form a fuzzy cloud, the coma.",
  "rules": {"emission_um": v([3.0, 4.26, 4.7], "atlas3i", "read", "Water, carbon dioxide and carbon monoxide gas. In 3I/ATLAS SPHEREx saw CO2 at 4.26 um and no H2O or CO gas."),
            "extended": v("wider than a star: the CO2 coma of 3I/ATLAS reached at least 30 SPHEREx pixels (~348,000 km)", "atlas3i"),
            "motion": "Moves between exposures, like an asteroid."},
  "appearance": {"model": "comet", "features": ["coma", "tail"], "eye_colour_from_temp": False},
  "note": "No comet is among our 5 targets and the classifier has no comet rule yet: this entry is for the 3D library and the text.",
 },
}

# Measured values of the 5 targets for the 3D dials (web/lib3d/appearance.json) with their sources.
TARGET_VALUES = {
 "barnards-star": {"cls": "red-dwarf", "temp_K": v(3134, "dawson2004", note="+/- 102 K; another published value is 3223 +/- 17 K"), "radius_rsun": v(0.200, "dawson2004", note="+/- 0.008; 0.187 is also published")},
 "eps-indi-b": {"cls": "brown-dwarf", "binary": True, "temp_K": v([1300, 1340], "king2010", note="Ba"), "temp2_K": v([880, 940], "king2010", note="Bb"),
                "mass_mjup": v([66.92, 53.25], "chen2022", note="Ba, Bb")},
 "wise-0855": {"cls": "brown-dwarf", "temp_K": v([225, 260], "luhman2014", note="true colour is black to the eye")},
 "rw-aurigae": {"cls": "young-star", "temp_K": None, "note": "no checked temperature yet: keep 'assumed' in appearance.json"},
 "r-draconis": {"cls": "mira", "temp_K": None, "period_days": v([245, 246], "gcvs", "team", "245-246 d in secondary lists; confirm in AAVSO VSX (open item in data/science-notes.md)")},
}

out = {"_about": "Science layer per object class (contract I4, WORKSPLIT C3). Built by data/scripts/build_classes.py: edit there, not here. "
                 "Each number is {value, source, checked}. checked: 'read' = read on the source page 14 Nov 2026; 'search' = quoted from that source in a web search, page not opened; "
                 "'calculated'; 'team' = our working threshold, not a literature value. Class entries sit at the top level under the ids in class_ids.",
       "discovery_rules": DISCOVERY_RULES, "discovery_rules_why": DISCOVERY_RULES_WHY,
       "class_ids": list(CLASSES), **CLASSES, "target_values": TARGET_VALUES, "sources": SOURCES}
used = set(re.findall(r'"source": "([a-z0-9_]+)"', json.dumps(out)))
assert used <= set(SOURCES), used - set(SOURCES)
(ROOT / "science" / "classes.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")

# ---- science/notes/<id>.md: one file per target, cut from data/science-notes.md (served by GET /object/<id>) ----
notes = (ROOT / "data" / "science-notes.md").read_text()
ids = {t["id"] for t in json.loads((ROOT / "data" / "targets.json").read_text())}
done = []
for m in re.finditer(r"^## (.+?) \(`([a-z0-9-]+)`\)(.*?)\n(.*?)(?=^## |\Z)", notes, re.S | re.M):
    name, tid, rest, body = m.groups()
    if tid in ids:
        (ROOT / "science" / "notes" / f"{tid}.md").write_text(f"# {name}{rest}\n\n{body.strip()}\n\n*Cut from data/science-notes.md (tags: [M] measured by the team, [L✓] checked against the source, [L] not yet checked).*\n")
        done.append(tid)
assert set(done) == ids, ids - set(done)
print("classes:", list(CLASSES), "| sources:", len(SOURCES), "| notes:", sorted(done))
