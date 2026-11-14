declare module 'aladin-lite' {
  interface Overlay {
    removeAll(): void;
    addFootprints(shapes: unknown[]): void;
  }
  interface Viewer {
    pix2world(x: number, y: number, frame?: string): [number, number] | undefined;
    getSize(): [number, number];
    addOverlay(overlay: Overlay): void;
    removeOverlay(overlay: Overlay): void;
  }
  const A: {
    init: Promise<unknown>;
    aladin(container: HTMLElement, options: Record<string, unknown>): Viewer;
    graphicOverlay(options: Record<string, unknown>): Overlay;
    polygon(vertices: [number, number][], options?: Record<string, unknown>): unknown;
  };
  export default A;
}
