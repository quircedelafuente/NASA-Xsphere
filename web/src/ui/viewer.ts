/**
 * The ONE place the UI imports viewer components from.
 * When Giorgi's components land in web/src/viewer/, change these two lines to:
 *   export { BlinkCanvas } from '../viewer/BlinkCanvas';
 *   export { SpectrumChart } from '../viewer/SpectrumChart';
 */
export { BlinkCanvasStub as BlinkCanvas } from './stubs/BlinkCanvasStub';
export { SpectrumChartStub as SpectrumChart } from './stubs/SpectrumChartStub';
