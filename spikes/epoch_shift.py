import sys,pandas as pd,numpy as np
from astropy.time import Time
d=pd.read_csv(f'phot_{sys.argv[1]}.csv'); minsnr=float(sys.argv[2])
g=d.dropna(subset=["cra","cdec"])
print(sys.argv[1],'centroid-quality rows',len(g),'of',len(d))
ref=None
for ep,q in g.groupby('epoch'):
    cosd=np.cos(np.radians(q.cdec.mean()))
    ra=q.cra.mean(); dec=q.cdec.mean(); n=len(q)
    sra=q.cra.std()*3600*cosd/np.sqrt(n); sdec=q.cdec.std()*3600/np.sqrt(n)
    # offset of measured centroid vs PM-predicted position at that time
    off_ra=((q.cra-q.ra_pred)*3600*cosd).median(); off_dec=((q.cdec-q.dec_pred)*3600).median()
    t=Time(q.mjd.mean(),format='mjd').decimalyear
    if ref is None: ref=(ra,dec,t)
    dra=(ra-ref[0])*3600*cosd; ddec=(dec-ref[1])*3600
    print(f" epoch {ep} t={t:.3f} n={n}: shift vs first epoch dRA*={dra:+.2f}\" dDec={ddec:+.2f}\" (|d|={np.hypot(dra,ddec):.2f}\" ={np.hypot(dra,ddec)/6.15:.2f} px; ±{sra:.2f},{sdec:.2f}); meas-minus-PMpred = ({off_ra:+.2f},{off_dec:+.2f})\"")
