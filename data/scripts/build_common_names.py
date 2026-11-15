"""Builds data/common_names.json: well-known star and deep-sky names with their catalogue positions.

The engine uses it to forgive typos in common names ('betelgeuze', 'sirus', 'andromeda galxy'): the star catalogues
themselves do no fuzzy matching. Every name is looked up in CDS Sesame when this script runs; names it does not know
are dropped, so the file only holds names that resolve. Positions are J2000 catalogue positions (no proper motion).

Run (needs the network, ~2 min):  python data/scripts/build_common_names.py
"""
import json, pathlib, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend'))
from engine.resolve import sesame   # noqa: E402

NAMES = """
Sirius; Canopus; Arcturus; Vega; Capella; Rigel; Procyon; Achernar; Betelgeuse; Hadar; Altair; Acrux; Aldebaran; Antares;
Spica; Pollux; Fomalhaut; Deneb; Mimosa; Regulus; Adhara; Castor; Shaula; Gacrux; Bellatrix; Elnath; Miaplacidus; Alnilam;
Alnair; Alnitak; Alioth; Mirfak; Dubhe; Wezen; Kaus Australis; Alkaid; Sargas; Avior; Menkalinan; Atria; Alhena; Peacock;
Polaris; Mirzam; Alphard; Hamal; Algieba; Diphda; Nunki; Menkent; Alpheratz; Mirach; Saiph; Kochab; Rasalhague; Algol;
Almach; Denebola; Naos; Tiaki; Aspidiske; Alphecca; Mizar; Alcor; Sadr; Schedar; Eltanin; Mintaka; Caph; Dschubba; Merak;
Izar; Enif; Ankaa; Phecda; Sabik; Scheat; Alderamin; Aludra; Markab; Menkar; Zubenelgenubi; Zubeneschamali; Acrab; Arneb;
Gienah; Unukalhai; Sheratan; Phact; Kraz; Ruchbah; Muphrid; Hassaleh; Algenib; Rasalgethi; Albireo; Mira; Thuban; Megrez;
Vindemiatrix; Sadalsuud; Sadalmelik; Tarazed; Nashira; Deneb Algedi; Alcyone; Atlas; Electra; Maia; Merope; Taygeta;
Pleione; Celaeno; Sterope; Alshain; Sulafat; Sheliak; Rastaban; Edasich; Aldhibah; Altais; Nihal; Cursa; Zaurak; Acamar;
Meissa; Tabit; Propus; Tejat; Mebsuta; Wasat; Mekbuda; Gomeisa; Furud; Muliphein; Alzirr; Tegmine; Acubens; Zosma; Chertan;
Adhafera; Rasalas; Algorab; Porrima; Heze; Zavijava; Syrma; Seginus; Nekkar; Alkalurops; Kornephoros; Sarin; Marfik;
Yed Prior; Yed Posterior; Cebalrai; Alnasl; Kaus Media; Kaus Borealis; Ascella; Albaldah; Arkab; Rukbat; Dabih; Algedi;
Sadachbia; Skat; Ancha; Homam; Matar; Biham; Alrescha; Fumalsamakah; Errai; Alfirk; Segin; Achird; Titawin; Mothallah;
Mesarthim; Botein; Bharani; Ain; Chamukuy; Hassaleh; Almaaz; Haedus; Saclateni; Mahasim; Alula Borealis; Alula Australis;
Tania Borealis; Tania Australis; Talitha; Muscida; Cor Caroli; Chara; Diadem; Pherkad; Yildun; Giausar; Grumium; Alsafi;
Proxima Centauri; Rigil Kentaurus; Toliman; Barnard's Star; Wolf 359; Lalande 21185; Luyten's Star; Teegarden's Star;
Kapteyn's Star; Van Maanen's Star; Groombridge 1830; Lacaille 9352; Luhman 16; Ross 128; Ross 154; Ross 248; Tabby's Star;
Przybylski's Star; Scholz's Star; Herschel's Garnet Star; La Superba; Polaris Australis; Cervantes; Copernicus; Helvetios;
Eta Carinae; Tau Ceti; Epsilon Eridani; Epsilon Indi; Alpha Centauri; Beta Pictoris; Zeta Reticuli; 61 Cygni; 51 Pegasi;
70 Ophiuchi; 40 Eridani; R Coronae Borealis; T Tauri; FU Orionis; Chi Cygni; R Leonis; W Hydrae; R Doradus; VY Canis Majoris;
UY Scuti; Mu Cephei; Delta Cephei; RR Lyrae; SS Cygni; U Geminorum; Z Camelopardalis; P Cygni; S Doradus; Cygnus X-1;
Andromeda Galaxy; Triangulum Galaxy; Whirlpool Galaxy; Sombrero Galaxy; Pinwheel Galaxy; Cigar Galaxy; Bode's Galaxy;
Black Eye Galaxy; Sunflower Galaxy; Cartwheel Galaxy; Centaurus A; Large Magellanic Cloud; Small Magellanic Cloud;
Sculptor Galaxy; Antennae Galaxies; Tadpole Galaxy; Hoag's Object; Stephan's Quintet; Virgo A; Cygnus A; Fornax A;
Orion Nebula; Crab Nebula; Ring Nebula; Dumbbell Nebula; Helix Nebula; Eagle Nebula; Lagoon Nebula; Trifid Nebula;
Omega Nebula; Carina Nebula; Tarantula Nebula; Rosette Nebula; Horsehead Nebula; Flame Nebula; North America Nebula;
Pelican Nebula; Veil Nebula; Cat's Eye Nebula; Owl Nebula; Eskimo Nebula; Bubble Nebula; Cone Nebula; California Nebula;
Heart Nebula; Soul Nebula; Butterfly Nebula; Egg Nebula; Red Rectangle; Boomerang Nebula; Little Dumbbell Nebula;
Pleiades; Hyades; Beehive Cluster; Praesepe; Omega Centauri; 47 Tucanae; Hercules Cluster; Double Cluster; Jewel Box;
Wild Duck Cluster; Butterfly Cluster; Ptolemy Cluster; Coma Cluster; Virgo Cluster; Perseus Cluster; Bullet Cluster;
Sagittarius A*; Galactic Center; Cassiopeia A; Tycho's Supernova; Kepler's Supernova; SN 1987A; Vela Pulsar; Crab Pulsar;
Geminga; TRAPPIST-1; Kepler-186; Kepler-452; Kepler-22; Kepler-16; WASP-12; WASP-39; WASP-96; HAT-P-7; TOI-700; K2-18;
Gliese 581; Gliese 667 C; Gliese 876; Gliese 436; Gliese 1214; LHS 1140; HR 8799; Fomalhaut b; 55 Cancri; Upsilon Andromedae;
"""

# Names the catalogues only know under another label: common name -> what to look up.
LOOKUP = {"Large Magellanic Cloud": "LMC", "Pinwheel Galaxy": "M 101", "Beehive Cluster": "M 44", "Omega Nebula": "M 17",
          "Double Cluster": "NGC 869", "Ptolemy Cluster": "M 7", "Galactic Center": "Sgr A*", "Tycho's Supernova": "SN 1572",
          "Kepler's Supernova": "SN 1604", "Antennae Galaxies": "NGC 4038", "Soul Nebula": "IC 1848", "Tabby's Star": "KIC 8462852",
          "Van Maanen's Star": "van Maanen 2", "Zeta Reticuli": "zet01 Ret", "Gliese 581": "GJ 581", "Gliese 667 C": "GJ 667 C",
          "Gliese 876": "GJ 876", "Gliese 436": "GJ 436", "Gliese 1214": "GJ 1214", "Sterope": "21 Tau", "Ain": "eps Tau",
          "Haedus": "eta Aur", "Arkab": "bet01 Sgr", "Bharani": "41 Ari", "Alzirr": "ksi Gem", "Tiaki": "bet Gru"}

def main():
    names, seen = [], set()
    for n in NAMES.replace('\n', ' ').split(';'):
        n = n.strip()
        if n and n.lower() not in seen:
            seen.add(n.lower()); names.append(n)
    out, dropped = {}, []
    for i, n in enumerate(names):
        pos = sesame(LOOKUP.get(n, n)) or sesame(LOOKUP.get(n, n))   # one retry: a slow answer is not 'unknown'
        if pos:
            out[n] = [round(pos[0], 5), round(pos[1], 5)]
        else:
            dropped.append(n)
        if i % 25 == 0:
            print(f'{i}/{len(names)}', flush=True)
        time.sleep(0.05)
    doc = {'_about': 'Well-known names for typo-tolerant search. Built by data/scripts/build_common_names.py: edit there, not here. '
                     'Positions [ra_deg, dec_deg] are J2000 catalogue positions from CDS Sesame (SIMBAD/NED/VizieR), no proper motion.',
           'built': time.strftime('%Y-%m-%d'), 'names': out}
    (ROOT / 'data' / 'common_names.json').write_text(json.dumps(doc, ensure_ascii=False, indent=1) + '\n')
    print(f'{len(out)} names written; dropped (not known to Sesame): {dropped}')

if __name__ == '__main__':
    main()
