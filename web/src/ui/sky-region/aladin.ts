import { squareCorners, type SkyRegion } from './geometry';

export interface SkyViewer {
  pixelToSky(x: number, y: number): [number, number] | undefined;
  drawRegion(region: SkyRegion): void;
  dispose(): void;
}

/** Keep vendor APIs here; the React component owns the interaction and handoff. */
export async function createSkyViewer(host: HTMLElement): Promise<SkyViewer> {
  const { default: A } = await import('aladin-lite');
  await A.init;
  // A cancelled React effect must never create a viewer in a detached container.
  if (!host.isConnected) throw new Error('Sky map was unmounted.');
  const viewer = A.aladin(host, {
    target: '133.7951 -7.2451',
    fov: 0.7,
    survey: 'P/DSS2/color',
    cooFrame: 'ICRSd',
    showReticle: false,
    showLayersControl: false,
    showGotoControl: false,
    showShareControl: false,
    showFullscreenControl: false,
    showSimbadPointerControl: false,
  });
  const overlay = A.graphicOverlay({ name: 'Selected region', color: '#6ee7d0', lineWidth: 3 });
  viewer.addOverlay(overlay);
  return {
    pixelToSky(x, y) {
      // CSS pixels -> viewer pixels; do not multiply by devicePixelRatio.
      const rect = host.getBoundingClientRect();
      const [width, height] = viewer.getSize();
      return viewer.pix2world(x * width / rect.width, y * height / rect.height, 'ICRS');
    },
    drawRegion(region) {
      overlay.removeAll();
      overlay.addFootprints([A.polygon(squareCorners(region))]);
    },
    dispose() {
      viewer.removeOverlay(overlay);
      // Aladin v3 has no public destroy method. Removing its own host also
      // prevents late initialization from attaching to a subsequent mount.
      host.remove();
    },
  };
}
