import time, warnings, numpy as np, json
warnings.simplefilter('ignore')
from astropy.io import fits
from astropy.io.votable import parse_single_table
from astropy.wcs import WCS
from astropy.coordinates import SkyCoord
import astropy.units as u
from astropy.time import Time
gaia=SkyCoord(ra=269.44850252*u.deg,dec=4.73942045*u.deg,pm_ra_cosdec=-801.551*u.mas/u.yr,pm_dec=10362.394*u.mas/u.yr,distance=1.828*u.pc,obstime=Time(2016.0,format='jyear'))
rows=[]
for f in ['dl/sia.xml','dl/spherex_qr3.xml']:
    t=parse_single_table(f).to_table(use_names_over_ids=True)
    t=t[t['energy_bandpassname']=='SPHEREx-D3']
    t.sort('t_min'); rows+= [t[0], t[-1]]
for r in rows:
    j=json.loads(r['cloud_access'])['aws']; url=f"https://{j['bucket_name']}.s3.us-east-1.amazonaws.com/{j['key']}"
    T=time.time()
    with fits.open(url,use_fsspec=True,fsspec_kwargs={"block_size":512_000}) as h:
        hd=h['IMAGE'].header; w=WCS(hd); mjd=hd['MJD-AVG']
        c=gaia.apply_space_motion(new_obstime=Time(mjd,format='mjd'))
        x,y=w.world_to_pixel(c); xi,yi=int(round(float(x))),int(round(float(y)))
        im=h['IMAGE'].section[max(yi-8,0):yi+9,max(xi-8,0):xi+9]; fl=h['FLAGS'].section[max(yi-8,0):yi+9,max(xi-8,0):xi+9]
    if im.size<200: print('edge',mjd); continue
    nn=np.isnan(im).sum(); im=np.nan_to_num(im)
    py,px=np.unravel_index(np.nanargmax(im),im.shape)
    sub=im[py-1:py+2,px-1:px+2]; yy,xx=np.mgrid[-1:2,-1:2]
    cx=px+(sub*xx).sum()/sub.sum()+xi-8; cy=py+(sub*yy).sum()/sub.sum()+yi-8
    meas=w.pixel_to_world(cx,cy)
    print(f"MJD {mjd:.1f} predicted {c.ra.deg:.5f},{c.dec.deg:.5f} measured {meas.ra.deg:.5f},{meas.dec.deg:.5f} sep {c.separation(meas).arcsec:.1f}\" peak {np.nanmax(im):.1f} nNaN {nn} flags@peak {fl[py,px]} MJy/sr  {time.time()-T:.1f}s")
