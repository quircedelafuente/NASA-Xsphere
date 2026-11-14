/**
 * Hand-picked orientation layer for the simplified sky map: bright stars (J2000, approx. V mag)
 * and simple stick figures for constellations near our five targets plus a few famous ones.
 * Positions are rounded — this layer is for orientation only, never for science.
 */
export interface MapStar { id: string; name?: string; ra: number; dec: number; mag: number }
export interface Constellation { name: string; lines: [string, string][] }

const S = (id: string, ra: number, dec: number, mag: number, name?: string): MapStar => ({ id, ra, dec, mag, name });

export const STARS: MapStar[] = [
  // Orion
  S('betelgeuse', 88.79, 7.41, 0.5, 'Betelgeuse'), S('rigel', 78.63, -8.2, 0.1, 'Rigel'), S('bellatrix', 81.28, 6.35, 1.6),
  S('saiph', 86.94, -9.67, 2.1), S('alnitak', 85.19, -1.94, 1.8), S('alnilam', 84.05, -1.2, 1.7), S('mintaka', 83.0, -0.3, 2.2),
  S('meissa', 83.78, 9.93, 3.4),
  // Ursa Major
  S('dubhe', 165.93, 61.75, 1.8), S('merak', 165.46, 56.38, 2.4), S('phecda', 178.46, 53.69, 2.4), S('megrez', 183.86, 57.03, 3.3),
  S('alioth', 193.51, 55.96, 1.8), S('mizar', 200.98, 54.93, 2.2), S('alkaid', 206.89, 49.31, 1.9),
  // Ursa Minor
  S('polaris', 37.95, 89.26, 2.0, 'Polaris'), S('yildun', 263.05, 86.59, 4.4), S('epsumi', 251.49, 82.04, 4.2), S('zetumi', 236.01, 77.79, 4.3),
  S('kochab', 222.68, 74.16, 2.1), S('pherkad', 230.18, 71.83, 3.0), S('etaumi', 244.38, 75.76, 5.0),
  // Draco
  S('eltanin', 269.15, 51.49, 2.2), S('rastaban', 262.61, 52.3, 2.8), S('grumium', 268.38, 56.87, 3.8), S('kuma', 263.07, 55.18, 4.9),
  S('altais', 288.14, 67.66, 3.1), S('epsdra', 297.04, 70.27, 3.8), S('zetdra', 257.2, 65.71, 3.2), S('etadra', 245.99, 61.51, 2.7),
  S('thedra', 240.47, 58.57, 4.0), S('edasich', 231.23, 58.97, 3.3), S('thuban', 211.1, 64.38, 3.7), S('kapdra', 188.37, 69.79, 3.9),
  S('giausar', 172.85, 69.33, 3.8),
  // Cassiopeia
  S('caph', 2.29, 59.15, 2.3), S('schedar', 10.13, 56.54, 2.2), S('navi', 14.18, 60.72, 2.4), S('ruchbah', 21.45, 60.24, 2.7), S('segin', 28.6, 63.67, 3.4),
  // Cygnus, Lyra, Aquila
  S('deneb', 310.36, 45.28, 1.3, 'Deneb'), S('sadr', 305.56, 40.26, 2.2), S('gienah', 311.55, 33.97, 2.5), S('delcyg', 296.24, 45.13, 2.9),
  S('albireo', 292.68, 27.96, 3.1), S('vega', 279.23, 38.78, 0.0, 'Vega'), S('epslyr', 281.08, 39.67, 4.7), S('zetlyr', 281.19, 37.6, 4.3),
  S('sheliak', 282.52, 33.36, 3.5), S('sulafat', 284.74, 32.69, 3.3), S('dellyr', 283.63, 36.9, 4.3),
  S('altair', 297.7, 8.87, 0.8, 'Altair'), S('tarazed', 296.56, 10.61, 2.7), S('alshain', 298.83, 6.41, 3.7), S('delaql', 291.37, 3.11, 3.4),
  S('lamaql', 286.56, -4.88, 3.4), S('zetaql', 286.35, 13.86, 3.0), S('theaql', 302.83, -0.82, 3.2),
  // Ophiuchus (Barnard's Star lives here)
  S('rasalhague', 263.73, 12.56, 2.1, 'Rasalhague'), S('cebalrai', 265.87, 4.57, 2.8), S('kapoph', 254.42, 9.38, 3.2), S('yedprior', 243.59, -3.69, 2.7),
  S('epsoph', 244.58, -4.69, 3.2), S('zetoph', 249.29, -10.57, 2.6), S('sabik', 257.59, -15.72, 2.4), S('nuoph', 269.76, -9.77, 3.3),
  // Scorpius
  S('antares', 247.35, -26.43, 1.0, 'Antares'), S('graffias', 241.36, -19.81, 2.6), S('dschubba', 240.08, -22.62, 2.3), S('pisco', 239.71, -26.11, 2.9),
  S('sigsco', 245.3, -25.59, 2.9), S('tausco', 248.97, -28.22, 2.8), S('epssco', 252.54, -34.29, 2.3), S('musco', 252.97, -38.05, 3.0),
  S('zetsco', 253.5, -42.36, 3.6), S('etasco', 258.04, -43.24, 3.3), S('thesco', 264.33, -43.0, 1.9), S('iotsco', 266.9, -40.13, 3.0),
  S('kapsco', 265.62, -39.03, 2.4), S('shaula', 263.4, -37.1, 1.6),
  // Sagittarius
  S('kausaus', 276.04, -34.38, 1.8), S('nunki', 283.82, -26.3, 2.0), S('ascella', 285.65, -29.88, 2.6), S('kausmed', 275.25, -29.83, 2.7),
  S('kausbor', 276.99, -25.42, 2.8), S('alnasl', 271.45, -30.42, 3.0), S('phisgr', 281.41, -26.99, 3.2), S('tausgr', 286.74, -27.67, 3.3),
  // Crux & Centaurus
  S('acrux', 186.65, -63.1, 0.8), S('mimosa', 191.93, -59.69, 1.3), S('gacrux', 187.79, -57.11, 1.6), S('delcru', 183.79, -58.75, 2.8),
  S('rigilkent', 219.9, -60.83, -0.3, 'α Centauri'), S('hadar', 210.96, -60.37, 0.6),
  // Leo
  S('regulus', 152.09, 11.97, 1.4, 'Regulus'), S('denebola', 177.26, 14.57, 2.1), S('algieba', 154.99, 19.84, 2.0), S('zosma', 168.53, 20.52, 2.6),
  S('chertan', 168.56, 15.43, 3.3), S('etaleo', 151.83, 16.76, 3.5), S('epsleo', 146.46, 23.77, 3.0), S('muleo', 148.19, 26.01, 3.9),
  S('adhafera', 154.17, 23.42, 3.4),
  // Gemini, Canis Major/Minor
  S('castor', 113.65, 31.89, 1.6, 'Castor'), S('pollux', 116.33, 28.03, 1.1, 'Pollux'), S('alhena', 99.43, 16.4, 1.9), S('mebsuta', 100.98, 25.13, 3.0),
  S('tejat', 95.74, 22.51, 2.9), S('wasat', 110.03, 21.98, 3.5),
  S('sirius', 101.29, -16.72, -1.5, 'Sirius'), S('mirzam', 95.67, -17.96, 2.0), S('adhara', 104.66, -28.97, 1.5), S('wezen', 107.1, -26.39, 1.8),
  S('aludra', 111.02, -29.3, 2.4), S('procyon', 114.83, 5.22, 0.4, 'Procyon'), S('gomeisa', 111.79, 8.29, 2.9),
  // Taurus & Auriga (RW Aurigae)
  S('aldebaran', 68.98, 16.51, 0.9, 'Aldebaran'), S('elnath', 81.57, 28.61, 1.7), S('zettau', 84.41, 21.14, 3.0), S('gamtau', 64.95, 15.63, 3.7),
  S('epstau', 67.15, 19.18, 3.5), S('lamtau', 60.17, 12.49, 3.4), S('pleiades', 56.87, 24.11, 1.6, 'Pleiades'),
  S('capella', 79.17, 46.0, 0.1, 'Capella'), S('menkalinan', 89.88, 44.95, 1.9), S('theaur', 89.93, 37.21, 2.6), S('hassaleh', 74.25, 33.17, 2.7),
  S('epsaur', 75.49, 43.82, 3.0), S('etaaur', 76.63, 41.23, 3.2),
  // Hydra (WISE 0855)
  S('alphard', 141.9, -8.66, 2.0, 'Alphard'), S('zethya', 133.85, 5.95, 3.1), S('epshya', 131.69, 6.42, 3.4), S('delhya', 129.41, 5.7, 4.2),
  S('sighya', 129.69, 3.34, 4.4), S('etahya', 130.81, 3.4, 4.3), S('thehya', 138.59, 2.31, 3.9), S('iothya', 144.96, -1.14, 3.9),
  S('ups1hya', 147.87, -14.85, 4.1), S('muhya', 156.52, -16.84, 3.8), S('nuhya', 162.41, -16.19, 3.1), S('gamhya', 199.73, -23.17, 3.0),
  // Indus, Grus, Pavo (ε Indi)
  S('alpind', 309.39, -47.29, 3.1), S('betind', 313.7, -58.45, 3.7), S('theind', 319.97, -53.45, 4.4),
  S('alnair', 332.06, -46.96, 1.7), S('betgru', 340.67, -46.88, 2.1), S('gamgru', 328.48, -37.36, 3.0), S('delgru', 337.44, -43.5, 4.0),
  S('epsgru', 342.14, -51.32, 3.5), S('zetgru', 345.22, -52.75, 4.1),
  S('peacock', 306.41, -56.74, 1.9, 'Peacock'), S('betpav', 311.24, -66.2, 3.4), S('delpav', 302.18, -66.18, 3.6), S('etapav', 266.43, -64.72, 3.6),
  // Pegasus, Andromeda, Perseus
  S('markab', 346.19, 15.21, 2.5), S('scheat', 345.94, 28.08, 2.4), S('algenib', 3.31, 15.18, 2.8), S('alpheratz', 2.1, 29.09, 2.1),
  S('mirach', 17.43, 35.62, 2.1), S('almach', 30.97, 42.33, 2.1), S('mirfak', 51.08, 49.86, 1.8), S('algol', 47.04, 40.96, 2.1),
  // Bright singles
  S('arcturus', 213.92, 19.18, -0.1, 'Arcturus'), S('spica', 201.3, -11.16, 1.0, 'Spica'), S('canopus', 95.99, -52.7, -0.7, 'Canopus'),
  S('achernar', 24.43, -57.24, 0.5, 'Achernar'), S('fomalhaut', 344.41, -29.62, 1.2, 'Fomalhaut'),
];

export const STAR_BY_ID: Record<string, MapStar> = Object.fromEntries(STARS.map((s) => [s.id, s]));

const chain = (...ids: string[]): [string, string][] => ids.slice(1).map((id, i) => [ids[i], id]);

export const CONSTELLATIONS: Constellation[] = [
  { name: 'Orion', lines: [...chain('meissa', 'betelgeuse', 'alnitak', 'saiph'), ...chain('meissa', 'bellatrix', 'mintaka', 'rigel'), ...chain('mintaka', 'alnilam', 'alnitak'), ['betelgeuse', 'bellatrix']] },
  { name: 'Ursa Major', lines: [...chain('alkaid', 'mizar', 'alioth', 'megrez', 'dubhe', 'merak', 'phecda', 'megrez')] },
  { name: 'Ursa Minor', lines: [...chain('polaris', 'yildun', 'epsumi', 'zetumi', 'kochab', 'pherkad', 'etaumi', 'zetumi')] },
  { name: 'Draco', lines: [...chain('eltanin', 'rastaban', 'kuma', 'grumium', 'eltanin'), ...chain('grumium', 'altais', 'epsdra'), ...chain('altais', 'zetdra', 'etadra', 'thedra', 'edasich', 'thuban', 'kapdra', 'giausar')] },
  { name: 'Cassiopeia', lines: chain('caph', 'schedar', 'navi', 'ruchbah', 'segin') },
  { name: 'Cygnus', lines: [...chain('deneb', 'sadr', 'albireo'), ...chain('delcyg', 'sadr', 'gienah')] },
  { name: 'Lyra', lines: [...chain('vega', 'epslyr'), ...chain('vega', 'zetlyr', 'sheliak', 'sulafat', 'dellyr', 'zetlyr')] },
  { name: 'Aquila', lines: [...chain('tarazed', 'altair', 'alshain', 'theaql'), ...chain('altair', 'delaql', 'lamaql'), ['delaql', 'zetaql']] },
  { name: 'Ophiuchus', lines: chain('rasalhague', 'kapoph', 'yedprior', 'epsoph', 'zetoph', 'sabik', 'cebalrai', 'rasalhague').concat([['sabik', 'nuoph']]) },
  { name: 'Scorpius', lines: [...chain('graffias', 'dschubba', 'pisco'), ...chain('dschubba', 'sigsco', 'antares', 'tausco', 'epssco', 'musco', 'zetsco', 'etasco', 'thesco', 'iotsco', 'kapsco', 'shaula')] },
  { name: 'Sagittarius', lines: [...chain('alnasl', 'kausmed', 'kausaus', 'ascella', 'phisgr', 'kausmed'), ...chain('phisgr', 'kausbor', 'kausmed'), ...chain('phisgr', 'nunki', 'tausgr', 'ascella')] },
  { name: 'Crux', lines: [['acrux', 'gacrux'], ['mimosa', 'delcru']] },
  { name: 'Leo', lines: [...chain('regulus', 'etaleo', 'algieba', 'adhafera', 'muleo', 'epsleo'), ...chain('algieba', 'zosma', 'denebola', 'chertan', 'regulus'), ['zosma', 'chertan']] },
  { name: 'Gemini', lines: [...chain('castor', 'mebsuta', 'tejat'), ...chain('pollux', 'wasat', 'alhena'), ['castor', 'pollux']] },
  { name: 'Canis Major', lines: [...chain('mirzam', 'sirius', 'wezen', 'adhara'), ['wezen', 'aludra']] },
  { name: 'Canis Minor', lines: [['procyon', 'gomeisa']] },
  { name: 'Taurus', lines: [...chain('elnath', 'epstau', 'gamtau', 'aldebaran', 'zettau'), ['gamtau', 'lamtau']] },
  { name: 'Auriga', lines: chain('capella', 'menkalinan', 'theaur', 'elnath', 'hassaleh', 'etaaur', 'epsaur', 'capella') },
  { name: 'Hydra', lines: [...chain('delhya', 'sighya', 'etahya', 'zethya', 'epshya', 'delhya'), ...chain('zethya', 'thehya', 'iothya', 'alphard', 'ups1hya', 'muhya', 'nuhya', 'gamhya')] },
  { name: 'Indus', lines: chain('alpind', 'theind', 'betind') },
  { name: 'Grus', lines: [...chain('gamgru', 'delgru', 'betgru', 'epsgru', 'zetgru'), ['alnair', 'betgru']] },
  { name: 'Pavo', lines: [...chain('peacock', 'betpav', 'delpav', 'etapav')] },
  { name: 'Pegasus', lines: chain('markab', 'scheat', 'alpheratz', 'algenib', 'markab') },
  { name: 'Andromeda', lines: chain('alpheratz', 'mirach', 'almach') },
  { name: 'Perseus', lines: [['mirfak', 'algol']] },
];
