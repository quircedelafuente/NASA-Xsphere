import { act, cleanup, createEvent, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { StrictMode } from 'react';
import { SkyRegionSelector } from './SkyRegionSelector';
import { createSkyViewer } from './aladin';

vi.mock('./aladin', () => ({ createSkyViewer: vi.fn(), SURVEYS: { spherex: { name: 'SPHEREx', url: 'x' } } }));
afterEach(cleanup);

async function setup(callback = vi.fn()) {
  const pixelToSky = vi.fn((): [number, number] => [133.712345678901, -7.123456789012]);
  const drawRegion = vi.fn();
  vi.mocked(createSkyViewer).mockImplementation(async (host) => {
    host.append(document.createElement('canvas'));
    return { pixelToSky, drawRegion, setSurvey: vi.fn(), dispose: () => host.remove() };
  });
  render(<StrictMode><SkyRegionSelector onRegionSelected={callback} /></StrictMode>);
  await waitFor(() => expect((screen.getByText('Select region') as HTMLButtonElement).disabled).toBe(false));
  const canvas = document.querySelector('canvas')!;
  const map = screen.getByLabelText('Interactive Aladin sky map');
  vi.spyOn(map, 'getBoundingClientRect').mockReturnValue({ left: 50, top: 100, width: 800, height: 500 } as DOMRect);
  return { callback, pixelToSky, drawRegion, canvas };
}

function pointer(target: Element, type: 'pointerDown' | 'pointerMove' | 'pointerUp' | 'pointerCancel', x = 650, y = 250, id = 1, primary = true) {
  const event = createEvent[type](target, { bubbles: true });
  Object.defineProperties(event, {
    clientX: { value: x }, clientY: { value: y }, pointerId: { value: id },
    button: { value: 0 }, isPrimary: { value: primary },
  });
  fireEvent(target, event);
}

function clickSky(canvas: Element) { pointer(canvas, 'pointerDown'); pointer(canvas, 'pointerUp'); }

describe('sky selection interaction', () => {
  it('uses the off-center click and submits its full-precision coordinates once', async () => {
    const { canvas, pixelToSky, drawRegion, callback } = await setup();
    expect((screen.getByText('Use this region') as HTMLButtonElement).disabled).toBe(true);
    clickSky(canvas);
    expect(pixelToSky).not.toHaveBeenCalled();
    fireEvent.click(screen.getByText('Select region'));
    clickSky(canvas);
    expect(pixelToSky).toHaveBeenCalledWith(600, 150);
    const region = { ra_deg: 133.712345678901, dec_deg: -7.123456789012, width_deg: 0.1 };
    expect(drawRegion).toHaveBeenCalledWith(region);
    expect(callback).not.toHaveBeenCalled();
    // Pan, including returning to the original pixel, and zoom after selecting.
    pointer(canvas, 'pointerDown'); pointer(canvas, 'pointerMove', 700, 300);
    pointer(canvas, 'pointerMove'); pointer(canvas, 'pointerUp');
    fireEvent.wheel(canvas, { deltaY: -100 });
    expect(pixelToSky).toHaveBeenCalledTimes(1);
    const submit = screen.getByText('Use this region');
    fireEvent.click(submit); fireEvent.click(submit);
    await screen.findByText('Region submitted');
    expect(callback).toHaveBeenCalledTimes(1);
    expect(callback).toHaveBeenCalledWith(region);
  });

  it('ignores dragging, cancelled gestures, multitouch, and map controls', async () => {
    const { canvas, pixelToSky } = await setup();
    fireEvent.click(screen.getByText('Select region'));
    pointer(canvas, 'pointerDown'); pointer(canvas, 'pointerUp', 700, 300);
    pointer(canvas, 'pointerDown'); pointer(canvas, 'pointerCancel'); pointer(canvas, 'pointerUp');
    pointer(canvas, 'pointerDown'); pointer(canvas, 'pointerDown', 600, 200, 2, false); pointer(canvas, 'pointerUp');
    const control = document.createElement('button'); canvas.parentElement!.append(control);
    clickSky(control);
    expect(pixelToSky).not.toHaveBeenCalled();
    expect((screen.getByText('Use this region') as HTMLButtonElement).disabled).toBe(true);
  });

  it('replaces the selection and permits another explicit submission', async () => {
    const { canvas, pixelToSky, callback } = await setup();
    fireEvent.click(screen.getByText('Select region')); clickSky(canvas);
    fireEvent.click(screen.getByText('Use this region')); await screen.findByText('Region submitted');
    pixelToSky.mockReturnValue([42.123456789, 81]);
    clickSky(canvas);
    expect(callback).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByText('Use this region')); await screen.findByText('Region submitted');
    expect(callback).toHaveBeenLastCalledWith({ ra_deg: 42.123456789, dec_deg: 81, width_deg: 0.1 });
    expect(callback).toHaveBeenCalledTimes(2);
  });

  it('locks pending submissions and allows retry after a callback failure', async () => {
    let reject!: (reason: Error) => void;
    const callback = vi.fn(() => new Promise<void>((_, fail) => { reject = fail; }));
    const { canvas, pixelToSky } = await setup(callback);
    fireEvent.click(screen.getByText('Select region')); clickSky(canvas);
    fireEvent.click(screen.getByText('Use this region'));
    expect((screen.getByText('Submitting…') as HTMLButtonElement).disabled).toBe(true);
    clickSky(canvas); expect(pixelToSky).toHaveBeenCalledTimes(1);
    await act(async () => reject(new Error('Backend unavailable')));
    expect(screen.getByRole('alert').textContent).toBe('Backend unavailable');
    expect((screen.getByText('Use this region') as HTMLButtonElement).disabled).toBe(false);
  });
});
