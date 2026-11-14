import numpy as np, time
from astropy.wcs import WCS
from reproject import reproject_interp, reproject_exact, reproject_adaptive
def mk(ra,dec,rot,n,scale):
    w=WCS(naxis=2); w.wcs.ctype=["RA---TAN","DEC--TAN"]; w.wcs.crval=[ra,dec]; w.wcs.crpix=[n/2+0.5]*2
    c,s=np.cos(np.radians(rot)),np.sin(np.radians(rot))
    w.wcs.cd=np.array([[-c,s],[s,c]])*scale/3600; return w
for n in (60,120,300):
    src=mk(269.45,4.69,37,n+20,6.15); dst=mk(269.452,4.693,0,n,6.15)
    d=np.random.rand(n+20,n+20).astype('float32')
    for f in (reproject_interp,reproject_adaptive,reproject_exact):
        t=time.time()
        for _ in range(5): f((d,src),dst,shape_out=(n,n))
        print(n,f.__name__,f"{(time.time()-t)/5*1000:.1f} ms")
