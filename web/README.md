# Sky region selector

Small standalone demo using the repository's planned Vite + React + TypeScript
stack (DECISIONS.md D10), with Aladin Lite 3.8.2. No coordinate request endpoint
or API client exists in this checkout. The C4 bundles and C5 URL format are not
an image-request API, so this component exposes a callback instead.

## Install and run (PowerShell)

Install Node.js 22.12+ (Node 22 LTS recommended), restart the VS Code terminal,
then from the repository root:

```powershell
cd web
npm ci
npm run dev
```

Open http://127.0.0.1:5173. Internet access and WebGL2 are needed for Aladin's
runtime assets and remote DSS2 sky tiles. This is sky context, not SPHEREx data.
If PowerShell blocks `npm.ps1`, use `npm.cmd` in place of `npm`.

This workspace also has an ignored portable Node runtime used for verification.
To use it without a system installation, run this from the repository root:

```powershell
$env:Path = "$PWD\.tools\node-v22.23.5-win-x64;$env:Path"
cd web
npm.cmd ci
npm.cmd run dev
```

That `.tools` folder is local and is not committed. Other teammates should install Node.
The frontend libraries are all declared in `package.json` and locked in
`package-lock.json`. The root `requirements.txt` only installs dependencies for
the existing Python research scripts; the frontend does not require Python:

```powershell
# Optional, from the repository root, for existing Python scripts only:
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Debug and inspect the output

1. Open the **NASA-Xsphere repository folder** in VS Code (not just `web` or an
   individual file). Install dependencies once using the instructions above.
2. Open **Run and Debug** (Ctrl+Shift+D), choose **Debug sky region selector (Edge)**,
   then press F5 or the green play button. The pre-launch task starts Vite and
   waits for port 5173 before opening Edge with the debugger attached. On Windows,
   it uses the local portable Node runtime when present, otherwise Node on PATH.
   No manual terminal startup or PATH change is needed in this workspace.
   Use Shift+F5 to stop debugging; stop the server with Ctrl+C in its task terminal
   or **Tasks: Terminate Task**. If you already started Vite manually, stop that
   instance before F5 so it does not occupy port 5173.
3. Set a breakpoint in `src/pages/SkyRegionDemo.tsx` inside
   `handleRegionSelected`. Press **Use this region** to inspect `region`.
4. The page's **Submitted payload** panel displays the exact JSON and submission
   count. Browser DevTools (F12) → Console also logs `[sky-region] submitted`.
   Browser logs appear in VS Code's Debug Console when launched with F5;
   they do not appear in Vite's terminal. Enable the Console's Info log level.

For extra Vite diagnostics, stop the task server and run `npm run dev:debug`
manually. The F5 configuration is in `.vscode/launch.json`; its automatic server
startup is in `.vscode/tasks.json`. See the
[VS Code task documentation](https://code.visualstudio.com/docs/debugtest/tasks)
for background pre-launch tasks.

## Reuse / backend connection point

```tsx
import { SkyRegionSelector, type SkyRegion } from './ui/sky-region/SkyRegionSelector';

<SkyRegionSelector onRegionSelected={handleRegionSelected} />
```

**Connect the backend in `src/pages/SkyRegionDemo.tsx`, `handleRegionSelected`.**
Replace the demo handler with your real client call and return its Promise.
No endpoint path is guessed here. Rejections are displayed by the selector and
allow retry; successful submissions stay disabled until another selection.
Selection and navigation never call the backend.

```ts
{ ra_deg: 133.7951, dec_deg: -7.2451, width_deg: 0.1 }
```

All values are numbers in ICRS decimal degrees. `ra_deg` is in [0,360),
`dec_deg` in [-90,90], and `width_deg` is the full width (6 arcminutes), not
a radius. Display values are rounded to 7 decimals; the callback is not rounded.
Do not reuse C5's arcsecond `fov` value as `width_deg` without conversion.

`src/ui/sky-region/aladin.ts` is the viewer adapter. It calls Aladin's
[`pix2world`](https://cds-astro.github.io/aladin-lite/Aladin.html#pix2world)
at the actual pointer position with the ICRS frame explicitly requested.
The outline is an Aladin celestial polygon, so the viewer reprojects it on pan
and zoom. `geometry.ts` constructs a north/east aligned TAN square with exactly
0.1° between opposing edge midpoints. This handles RA wrap and the poles without
using a naive ±0.05° RA box, which would shrink at high declination.

The component ignores gestures that move more than 4 CSS pixels, leave the map,
are cancelled, or involve another touch. Selecting remains active so another
click replaces the square. **Stop selecting** restores navigation-only clicks.

## Acceptance check

1. On load, confirm **Use this region** is disabled.
2. Press **Select region**, then click well away from the map center. A mint
   square should be centered on that exact click; RA/Dec appear below the map.
3. Note the coordinates. Drag the map, then zoom. The square should follow
   the same stars, change apparent size with zoom, and retain the coordinates.
4. Confirm the submission count is still 0. Press **Use this region** once:
   count becomes 1 and the JSON matches the selected patch. The button disables.
5. Click another position. The square and coordinates update; the submitted
   payload stays unchanged until you confirm again. The count then becomes 2.

```powershell
npm test
npm run build
```

Automated tests cover off-center pixel conversion, unchanged selection after
drag/zoom, exactly-once submission, replacement, pending/error states, gesture
rejection, precision, RA wrap, and high-declination/polar square geometry.
Interaction tests mock only the Aladin adapter; real tile rendering needs the
browser acceptance check above.
