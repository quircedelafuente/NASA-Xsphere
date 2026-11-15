import { pixelToSky, skyToPixel } from '../src/ui/lib/astro.ts';
// Run: node --experimental-strip-types scripts/check-astro.ts
const wcs = { ctype: ['RA---TAN','DEC--TAN'], crval: [269.44623883723, 4.7685838793225], crpix: [32.5, 32.5], cdelt: [-0.0017083333333333, -0.0017083333333333] } as any;
// Barnard's Star (Gaia DR3, moved to MJD 60924.26) must land on the engine's target_px [31.44, 32.26]
const yrs = 2000 + (60924.2625 - 51544.5) / 365.25 - 2016;
const dec = 4.739420051112412 + 10362.394 * yrs / 3.6e6, ra = 269.44850252543836 - 801.551 * yrs / 3.6e6 / Math.cos(dec * Math.PI / 180);
const p = skyToPixel(wcs, ra, dec, 64); console.log(p);
if (Math.abs(p.x - 31.44) > 0.3 || Math.abs(p.y - 32.26) > 0.3) throw new Error('skyToPixel off');
const q = pixelToSky(wcs, p.x, p.y, 64); if (Math.abs(q.ra - ra) > 1e-7 || Math.abs(q.dec - dec) > 1e-7) throw new Error('round trip off');
console.log('ok');
