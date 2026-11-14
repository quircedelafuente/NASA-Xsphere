/**
 * STUB of Giorgi's <BlinkCanvas> (C6) so the product shell can be built and demoed before P5 lands.
 * It honours the C6 props (mode, frameIndex, playing, fps, stretch, zoom, overlays, onPixelClick).
 * To swap in the real one, change the export in ../viewer.ts — nothing else in the UI imports this file.
 */
import { useEffect, useMemo, useRef } from 'react';
import type { BlinkCanvasProps } from '../lib/contracts';
import { MAX_FPS } from '../lib/url';
import { pixelToSky } from '../lib/astro';

function stretchValue(v: number, a: number, vmin: number, vmax: number) {
  const t = (v - vmin) / (vmax - vmin);
  const s = Math.asinh(t / a) / Math.asinh(1 / a);
  return Math.max(0, Math.min(1, s));
}

function robustSigma(arr: Float32Array) {
  const vals: number[] = [];
  for (let i = 0; i < arr.length; i += 3) if (Number.isFinite(arr[i])) vals.push(Math.abs(arr[i]));
  vals.sort((x, y) => x - y);
  return (vals[Math.floor(vals.length / 2)] || 1e-3) * 1.4826;
}

export function BlinkCanvasStub(props: BlinkCanvasProps) {
  const { manifest, frames, mode, frameIndex, playing, fps, stretch, zoom, overlays, onPixelClick, onFrameChange, invert, excludeEpochs } = props;
  const nx = manifest.nx ?? 64;
  const ny = manifest.ny ?? 64;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const active = useMemo(
    () => manifest.frames.map((_, i) => i).filter((i) => !(excludeEpochs ?? []).includes(i)),
    [manifest, excludeEpochs],
  );

  // Autoplay: ask the parent to advance (controlled component).
  useEffect(() => {
    if (!playing || mode === 'side' || active.length < 2) return;
    const ms = 1000 / Math.min(MAX_FPS, Math.max(0.25, fps));
    const id = window.setInterval(() => {
      const pos = active.indexOf(frameIndex);
      const next = active[(pos + 1) % active.length];
      onFrameChange?.(next);
    }, ms);
    return () => window.clearInterval(id);
  }, [playing, fps, frameIndex, active, mode, onFrameChange]);

  const diffs = useMemo(() => {
    if (!frames) return null;
    return frames.map((f, i) => {
      const j = i === 0 ? 1 : i - 1;
      const a = i === 0 ? frames[1] : f;
      const b = i === 0 ? f : frames[j];
      if (!a || !b) return null;
      const d = new Float32Array(f.length);
      for (let k = 0; k < f.length; k++) d[k] = a[k] - b[k];
      return { d, sigma: robustSigma(d) };
    });
  }, [frames]);

  useEffect(() => {
    const c = canvasRef.current;
    if (!c || !frames || frames.length === 0) return;
    const ctx = c.getContext('2d')!;
    const panels = mode === 'side' ? active : [frameIndex];
    const gap = mode === 'side' ? 6 : 0;
    const pz = mode === 'side' ? Math.max(2, Math.floor(zoom / Math.max(1, Math.ceil(panels.length / 2)))) : zoom;
    const W = panels.length * nx * pz + (panels.length - 1) * gap;
    const H = ny * pz;
    c.width = W;
    c.height = H;
    ctx.imageSmoothingEnabled = false;
    ctx.clearRect(0, 0, W, H);

    panels.forEach((fi, p) => {
      const img = ctx.createImageData(nx, ny);
      const src = mode === 'diff' ? diffs?.[fi]?.d : frames[fi];
      const sig = mode === 'diff' ? (diffs?.[fi]?.sigma ?? 1) * 5 : 1;
      if (!src) return;
      for (let k = 0; k < nx * ny; k++) {
        const v = src[k];
        let g: number;
        let masked = false;
        if (!Number.isFinite(v)) { masked = true; g = 0; }
        else if (mode === 'diff') g = Math.max(0, Math.min(1, 0.5 + v / (2 * sig)));
        else g = stretchValue(v, stretch.a, stretch.vmin, stretch.vmax);
        if (invert) g = 1 - g;
        const o = k * 4;
        if (masked && overlays.flags) { img.data[o] = 230; img.data[o + 1] = 159; img.data[o + 2] = 0; } // orange (CB-safe)
        else { const b = Math.round(g * 255); img.data[o] = b; img.data[o + 1] = b; img.data[o + 2] = b; }
        img.data[o + 3] = 255;
      }
      const off = document.createElement('canvas');
      off.width = nx; off.height = ny;
      off.getContext('2d')!.putImageData(img, 0, 0);
      const ox = p * (nx * pz + gap);
      ctx.drawImage(off, ox, 0, nx * pz, ny * pz);

      const f = manifest.frames[fi];
      const tp = f.target_px;
      // Predicted track
      if (overlays.track && manifest.target_track && manifest.target_track.length > 1) {
        ctx.strokeStyle = 'rgba(86,180,233,0.9)';
        ctx.lineWidth = Math.max(1, pz / 4);
        ctx.setLineDash([pz / 2, pz / 2]);
        ctx.beginPath();
        manifest.target_track.forEach((t, i) => {
          const X = ox + (t.x + 0.5) * pz, Y = (t.y + 0.5) * pz;
          if (i === 0) ctx.moveTo(X, Y); else ctx.lineTo(X, Y);
        });
        ctx.stroke();
        ctx.setLineDash([]);
        manifest.target_track.forEach((t, i) => {
          ctx.fillStyle = i === fi ? 'rgba(86,180,233,1)' : 'rgba(86,180,233,0.45)';
          ctx.beginPath();
          ctx.arc(ox + (t.x + 0.5) * pz, (t.y + 0.5) * pz, Math.max(1.5, pz / 5), 0, Math.PI * 2);
          ctx.fill();
        });
      }
      // Crosshair with a gap so the source stays visible
      if (overlays.crosshair && tp) {
        const X = ox + (tp[0] + 0.5) * pz, Y = (tp[1] + 0.5) * pz;
        const g = pz * 2.2, L = pz * 5;
        ctx.strokeStyle = 'rgba(240,228,66,0.95)';
        ctx.lineWidth = Math.max(1, pz / 6);
        ctx.beginPath();
        ctx.moveTo(X - L, Y); ctx.lineTo(X - g, Y);
        ctx.moveTo(X + g, Y); ctx.lineTo(X + L, Y);
        ctx.moveTo(X, Y - L); ctx.lineTo(X, Y - g);
        ctx.moveTo(X, Y + g); ctx.lineTo(X, Y + L);
        ctx.stroke();
      }
      // First frame of the loop gets a dashed border (WiseView convention: "the loop restarts here")
      if (mode === 'blink' && fi === active[0]) {
        ctx.strokeStyle = 'rgba(255,255,255,0.5)';
        ctx.lineWidth = 2;
        ctx.setLineDash([8, 6]);
        ctx.strokeRect(ox + 1, 1, nx * pz - 2, ny * pz - 2);
        ctx.setLineDash([]);
      }
    });
  }, [frames, diffs, mode, frameIndex, stretch, zoom, overlays, invert, manifest, nx, ny, active]);

  const handleClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!onPixelClick || mode === 'side') return;
    const c = e.currentTarget;
    const rect = c.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * nx;
    const y = ((e.clientY - rect.top) / rect.height) * ny;
    const { ra, dec } = pixelToSky(manifest.wcs, x - 0.5, y - 0.5, ny);
    onPixelClick(ra, dec, x, y);
  };

  if (!frames) return <div className="canvas-placeholder" />;
  return <canvas ref={canvasRef} className="blink-canvas" onClick={handleClick} role="img" aria-label="SPHEREx image sequence of the selected sky patch" />;
}
