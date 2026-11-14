# Contracts between the three chunks (see WORKSPLIT.md)
Change a field only after telling the other two chunks. Adding an optional field is fine.

- `api.md` (I1): HTTP API shapes (chunk A serves, frontend + B consume)
- `fixtures/barnards-star/stacks.npz` + `stacks.json` (I2): **real** SPHEREx merged images, the exact format chunk A produces and chunk B reads
- `report.md` (I3): what chunk B's scan/object report looks like
- `science.md` (I4): the files chunk C delivers

Load the fixture:
```python
import json, numpy as np
z = np.load('contracts/fixtures/barnards-star/stacks.npz'); m = json.load(open('contracts/fixtures/barnards-star/stacks.json'))
img = z['img']   # float32 [band, visit, y, x], MJy/sr, NaN = no data / saturated core
n = z['n']       # photos merged per [band, visit]
# m['bands'], m['visits'][i]['mjd'], m['grid']['wcs'] (FITS TAN header: astropy.wcs.WCS(m['grid']['wcs'])), m['band_lambda_um']
```
