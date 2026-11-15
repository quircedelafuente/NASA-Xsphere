/**
 * Optional display smoothing: draws a smooth surface through the SPHEREx pixels instead of flat squares.
 *
 * It is display only and adds no detail: SPHEREx pixels are 6.15″ and that is all the sharpness there is. The team
 * default stays nearest-neighbour (decision D7), so this is off unless the viewer asks for it (Advanced, or ?smooth=1).
 *
 * How: Catmull-Rom interpolation of the already-stretched values (0..1), ×4 per axis. Each new value is kept between
 * its two neighbouring pixels, so a bright star never gets a dark ring or a brighter-than-measured peak, and the
 * measured pixel values are still exactly there at the pixel centres' neighbours. Cost: ~0.3 M multiplications a frame.
 */
export const SMOOTH_FACTOR = 4;

/** Give masked (NaN) pixels the mean of their valid neighbours so they do not drag the pixels around them down. In place. */
function fillMasked(g: Float32Array, nx: number, ny: number) {
  for (let pass = 0; pass < 4; pass++) {
    const todo: [number, number][] = [];
    for (let y = 0; y < ny; y++) {
      for (let x = 0; x < nx; x++) {
        if (!Number.isNaN(g[y * nx + x])) continue;
        let s = 0, n = 0;
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            const X = x + dx, Y = y + dy;
            if (X < 0 || Y < 0 || X >= nx || Y >= ny) continue;
            const v = g[Y * nx + X];
            if (!Number.isNaN(v)) { s += v; n++; }
          }
        }
        if (n) todo.push([y * nx + x, s / n]);
      }
    }
    if (!todo.length) return;
    for (const [k, v] of todo) g[k] = v;
  }
  for (let k = 0; k < g.length; k++) if (Number.isNaN(g[k])) g[k] = 0;
}

/** One axis: `n` samples spaced `stride` apart starting at `at` in `src` → n·f samples in `dst`. */
function line(src: Float32Array, at: number, stride: number, n: number, dst: Float32Array, dAt: number, dStride: number, f: number) {
  for (let j = 0; j < n * f; j++) {
    const x = (j + 0.5) / f - 0.5;
    const i = Math.floor(x), t = x - i;
    const p0 = src[at + Math.max(0, Math.min(n - 1, i - 1)) * stride];
    const p1 = src[at + Math.max(0, Math.min(n - 1, i)) * stride];
    const p2 = src[at + Math.max(0, Math.min(n - 1, i + 1)) * stride];
    const p3 = src[at + Math.max(0, Math.min(n - 1, i + 2)) * stride];
    const v = p1 + 0.5 * t * (p2 - p0 + t * (2 * p0 - 5 * p1 + 4 * p2 - p3 + t * (3 * (p1 - p2) + p3 - p0)));
    dst[dAt + j * dStride] = Math.max(Math.min(p1, p2), Math.min(Math.max(p1, p2), v)); // no overshoot
  }
}

/** nx × ny values (NaN = masked) → (nx·f) × (ny·f) smooth values. The input is not changed. */
export function upsample(values: Float32Array, nx: number, ny: number, f = SMOOTH_FACTOR): Float32Array {
  const g = Float32Array.from(values);
  fillMasked(g, nx, ny);
  const wide = new Float32Array(nx * f * ny);
  for (let y = 0; y < ny; y++) line(g, y * nx, 1, nx, wide, y * nx * f, 1, f);
  const out = new Float32Array(nx * f * ny * f);
  for (let x = 0; x < nx * f; x++) line(wide, x, nx * f, ny, out, x, nx * f, f);
  return out;
}
