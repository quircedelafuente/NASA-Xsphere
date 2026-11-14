import sys, glob, json, warnings, numpy as np
warnings.filterwarnings('ignore')
from astropy.io import fits
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord, Distance
from astropy.time import Time
import astropy.units as u
name=sys.argv[1]
tg={"Barnard":dict(ra=269.44850252543836,dec=4.73942,pmra=-802.0,pmdec=10362.0,plx=546.98,ep=2016.0),
 "WISE0855":dict(ra=133.7947597,dec=-7.2451456,pmra=-8118.,pmdec=680.,plx=439.,ep=2010.5),
 "RWAur":dict(ra=76.95608,dec=30.4012,pmra=3.,pmdec=-27.,plx=6.4,ep=2016.0),
 "EpsIndB":dict(ra=331.07645,dec=-56.79381,pmra=3982.,pmdec=-2467.,plx=274.8,ep=2016.0)}[name]
c0=SkyCoord(ra=tg['ra']*u.deg,dec=tg['dec']*u.deg,pm_ra_cosdec=tg['pmra']*u.mas/u.yr,pm_dec=tg['pmdec']*u.mas/u.yr,distance=Distance(parallax=tg['plx']*u.mas),obstime=Time(tg['ep'],format='jyear'))
BAD = sum(1<<b for b in [0,1,2,6,7,9,10,11,15,17,19,20,22,23,24,25,26,27,28])  # everything except FULLSAMPLE(12), PHANMISS(14), SOURCE(21)
rows=[]
for fn in sorted(glob.glob(f'dl/{name}/*.fits')):
    try: h=fits.open(fn)
    except Exception: continue
    H=h['IMAGE'].header; w=WCS(H); 
    im=h['IMAGE'].data-h['ZODI'].data; var=h['VARIANCE'].data; fl=h['FLAGS'].data
    mjd=H['MJD-AVG']
    cp=c0.apply_space_motion(new_obstime=Time(mjd,format='mjd'))
    x,y=w.world_to_pixel(SkyCoord(cp.ra,cp.dec))
    xi,yi=int(round(float(x))),int(round(float(y)))
    if not (4<=xi<im.shape[1]-4 and 4<=yi<im.shape[0]-4): continue
    sw=WCS(H,fobj=h,key='W'); sw.sip=None
    lam=float(sw.pixel_to_world_values(float(x),float(y))[0])
    ys,xs=np.mgrid[0:im.shape[0],0:im.shape[1]]
    r=np.hypot(xs-x,ys-y)
    ap=r<2.0; ann=(r>5)&(r<9)&((fl&BAD)==0)
    bkg=np.nanmedian(im[ann])
    f=np.nansum(im[ap]-bkg); e=np.sqrt(np.nansum(var[ap]))
    badap=int(np.any(fl[ap]&BAD))
    # flux-weighted centroid in 5x5 box -> sky
    sl=(slice(yi-3,yi+4),slice(xi-3,xi+4)); s=np.clip(np.nan_to_num(im[sl]-bkg),0,None)
    if s.sum()>0:
        cx=(s*xs[sl]).sum()/s.sum(); cy=(s*ys[sl]).sum()/s.sum()
        cs=w.pixel_to_world(cx,cy); dra=(cs.ra.deg)*3600; ddec=cs.dec.deg*3600
    else: cs=None
    omega=H.get('OMEGA_MEDIAN',37.9)*(u.arcsec**2).to(u.sr)
    rows.append(dict(mjd=mjd,det=H['DETECTOR'],lam=lam,f_mJy=f*omega*1e9,e_mJy=e*omega*1e9,snr=f/e if e>0 else 0,bad=badap,
                     cra=cs.ra.deg if cs else np.nan,cdec=cs.dec.deg if cs else np.nan,ra_pred=cp.ra.deg,dec_pred=cp.dec.deg,fwhm=H.get('PSF_FWHM')))
import pandas as pd
d=pd.DataFrame(rows).sort_values('mjd')
d['epoch']=(d.mjd.diff()>20).cumsum()
d.to_csv(f'phot_{name}.csv',index=False)
print(name, 'files analysed',len(d))
for ep,g in d.groupby('epoch'):
    gg=g[g.bad==0]
    print(f" epoch {ep}: {Time(g.mjd.min(),format='mjd').iso[:10]}..{Time(g.mjd.max(),format='mjd').iso[:10]} n={len(g)} good={len(gg)} lam {g.lam.min():.2f}-{g.lam.max():.2f}um")
    for det,q in gg.groupby('det'):
        wts=1/q.e_mJy**2; F=(q.f_mJy*wts).sum()/wts.sum(); E=1/np.sqrt(wts.sum())
        print(f"   D{det}: n={len(q)} stackedflux={F:.3f}±{E:.3f} mJy (S/N {F/E:.1f}); median single S/N {q.snr.median():.1f}")
