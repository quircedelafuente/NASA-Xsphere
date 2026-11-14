/** ICRS decimal degrees. Width is the full angular extent, not a radius. */
export interface SkyRegion {
  ra_deg: number;
  dec_deg: number;
  width_deg: number;
}

export const REGION_WIDTH_DEG = 0.1;
export type SkyPoint = [number, number];
const RAD = Math.PI / 180;

export function regionAt(ra: number, dec: number): SkyRegion {
  if (!Number.isFinite(ra) || !Number.isFinite(dec) || Math.abs(dec) > 90) {
    throw new Error('This click is outside the sky projection. Try another point.');
  }
  // Preserve the viewer's full precision; only wrap RA if it needs wrapping.
  return {
    ra_deg: ra >= 0 && ra < 360 ? ra : ((ra % 360) + 360) % 360,
    dec_deg: dec,
    width_deg: REGION_WIDTH_DEG,
  };
}

/** North/east aligned TAN square; midpoint-to-midpoint angular width is exact.
 * Vector projection avoids the cos(dec) singularity and works across RA=0/poles.
 */
export function squareCorners(region: SkyRegion): SkyPoint[] {
  const ra = region.ra_deg * RAD;
  const dec = region.dec_deg * RAD;
  const center = [Math.cos(dec) * Math.cos(ra), Math.cos(dec) * Math.sin(ra), Math.sin(dec)];
  const east = [-Math.sin(ra), Math.cos(ra), 0];
  const north = [-Math.sin(dec) * Math.cos(ra), -Math.sin(dec) * Math.sin(ra), Math.cos(dec)];
  const half = Math.tan(region.width_deg * RAD / 2);
  return [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([x, y]) => {
    const v = center.map((c, i) => c + half * (x * east[i] + y * north[i]));
    return [
      ((Math.atan2(v[1], v[0]) / RAD) + 360) % 360,
      Math.atan2(v[2], Math.hypot(v[0], v[1])) / RAD,
    ];
  });
}
