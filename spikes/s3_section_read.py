import time, warnings, numpy as np
warnings.simplefilter('ignore')
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
url="https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/dr1/level2/2025W33_2C/l2b-v27-2026-228/6/level2_2025W33_2C_0321_1D6_spx_l2b-v27-2026-228.fits"
t=time.time()
with fits.open(url, use_fsspec=True, fsspec_kwargs={"block_size":512_000}) as h:
    hd=h['IMAGE'].header; w=WCS(hd)
    x,y=w.world_to_pixel(SkyCoord(269.452,4.693,unit='deg')); x,y=int(x),int(y)
    t1=time.time()
    img=h['IMAGE'].section[y-15:y+15,x-15:x+15]
    t2=time.time()
    fl=h['FLAGS'].section[y-15:y+15,x-15:x+15]
    t3=time.time()
    var=h['VARIANCE'].section[y-15:y+15,x-15:x+15]; zodi=h['ZODI'].section[y-15:y+15,x-15:x+15]
    t4=time.time()
print(f"open+hdr {t1-t:.2f}s img {t2-t1:.2f}s flags {t3-t2:.2f}s var+zodi {t4-t3:.2f}s", img.shape, np.nanmax(img), fl.max())
