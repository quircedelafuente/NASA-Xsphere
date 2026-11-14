import { squareCorners, type SkyRegion } from './geometry';

/** Sky backgrounds. Loaded by URL from NASA/IRSA, which allows cross-site use: requesting surveys by CDS id
 * (e.g. 'P/DSS2/color') routes to alasky.cds.unistra.fr, whose tiles returned 404 on the IE network (14 Nov),
 * leaving the map stuck on "loading". IRSA hosts the SPHEREx all-sky cube and mirrors of DSS2 and 2MASS. */
export const SURVEYS = {
  spherex: { name: 'SPHEREx all-sky (NASA, infrared)', url: 'https://irsa.ipac.caltech.edu/data/hips/SPHEREx/spherex_allsky_cube' },
  dss: { name: 'DSS2 colour (visible light)', url: 'https://irsa.ipac.caltech.edu/data/hips/CDS/DSS2/color' },
  twomass: { name: '2MASS colour (near-infrared)', url: 'https://irsa.ipac.caltech.edu/data/hips/CDS/2MASS/Color' },
} as const;
export type SurveyKey = keyof typeof SURVEYS;

export interface SkyViewer {
  pixelToSky(x: number, y: number): [number, number] | undefined;
  setSurvey(key: SurveyKey): void;
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
    cooFrame: 'ICRSd',
    log: false,                 // Aladin's usage ping is blocked on some networks and throws an uncaught error
    showReticle: false,
    showLayersControl: false,
    showGotoControl: false,
    showShareControl: false,
    showFullscreenControl: false,
    showSimbadPointerControl: false,
  });
  const setSurvey = (key: SurveyKey) => viewer.setBaseImageLayer(A.imageHiPS(SURVEYS[key].url, { name: SURVEYS[key].name }));
  setSurvey('dss');   // SPHEREx cube tiles render near-black with Aladin's default stretch; DSS is the readable default
  const overlay = A.graphicOverlay({ name: 'Selected region', color: '#6ee7d0', lineWidth: 3 });
  viewer.addOverlay(overlay);
  return {
    setSurvey,
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
