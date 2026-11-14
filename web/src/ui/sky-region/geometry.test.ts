import { describe, expect, it } from 'vitest';
import { regionAt, squareCorners } from './geometry';

describe('spherical square', () => {
  it.each([[133.7951, -7.2451], [359.999, 0], [40, 85], [0, 90], [20, -90]])(
    'keeps a 0.1-degree tangent square at RA %s Dec %s', (ra, dec) => {
      const rad = Math.PI / 180;
      const r = ra * rad, d = dec * rad;
      const center = [Math.cos(d) * Math.cos(r), Math.cos(d) * Math.sin(r), Math.sin(d)];
      const east = [-Math.sin(r), Math.cos(r), 0];
      const north = [-Math.sin(d) * Math.cos(r), -Math.sin(d) * Math.sin(r), Math.cos(d)];
      const dot = (a: number[], b: number[]) => a.reduce((sum, v, i) => sum + v * b[i], 0);
      for (const [lon, lat] of squareCorners(regionAt(ra, dec))) {
        expect(lon).toBeGreaterThanOrEqual(0); expect(lon).toBeLessThan(360);
        const v = [Math.cos(lat * rad) * Math.cos(lon * rad), Math.cos(lat * rad) * Math.sin(lon * rad), Math.sin(lat * rad)];
        expect(Math.abs(Math.atan(dot(v, east) / dot(v, center)) / rad)).toBeCloseTo(0.05, 9);
        expect(Math.abs(Math.atan(dot(v, north) / dot(v, center)) / rad)).toBeCloseTo(0.05, 9);
      }
    },
  );
  it('preserves precision, wraps RA, and rejects invalid projection coordinates', () => {
    expect(regionAt(133.795123456789, -7.245123456789).ra_deg).toBe(133.795123456789);
    expect(regionAt(-1, 0).ra_deg).toBe(359);
    expect(() => regionAt(NaN, 0)).toThrow();
    expect(() => regionAt(0, 91)).toThrow();
  });
});
