from astroquery.ipac.irsa import Irsa
from astropy.coordinates import SkyCoord, Distance
from astropy.time import Time
import astropy.units as u, numpy as np, time, json
from collections import Counter
T=Time('2026-01-01')
tg={
 "Barnard":    dict(ra=269.44850252543836,dec=4.73942,pmra=-802.0,pmdec=10362.0,plx=546.98,ep=2016.0),
 "EpsIndB":    dict(ra=331.07645,dec=-56.79381,pmra=3982.,pmdec=-2467.,plx=274.8,ep=2016.0),
 "WISE0855":   dict(ra=133.7947597,dec=-7.2451456,pmra=-8118.,pmdec=680.,plx=439.,ep=2010.5),
 "RWAur":      dict(ra=76.95608,dec=30.4012,pmra=3.,pmdec=-27.,plx=6.4,ep=2016.0),
 "RDra":       dict(ra=248.16738,dec=66.75501,pmra=-21.,pmdec=6.,plx=1.,ep=2016.0),
}
out={}
for name,p in tg.items():
    c=SkyCoord(ra=p['ra']*u.deg,dec=p['dec']*u.deg,pm_ra_cosdec=p['pmra']*u.mas/u.yr,pm_dec=p['pmdec']*u.mas/u.yr,distance=Distance(parallax=p['plx']*u.mas),obstime=Time(p['ep'],format='jyear'))
    c26=c.apply_space_motion(new_obstime=T)
    c26=SkyCoord(c26.ra,c26.dec)
    t0=time.time()
    r=Irsa.query_sia(pos=(c26,1*u.arcsec), collection=['spherex_dr1','spherex_qr3','spherex_dr1_deep','spherex_qr3_deep'])
    dt=time.time()-t0
    r=r[r['dataproduct_subtype']=='science'] if 'dataproduct_subtype' in r.colnames else r
    tmin=np.sort(np.array(r['t_min']))
    # cluster: gap > 20 days
    clusters=[]; 
    for x in tmin:
        if not clusters or x-clusters[-1][-1]>20: clusters.append([x])
        else: clusters[-1].append(x)
    # distinct exposures within cluster: group by t_min rounded to 0.01 d (detectors simultaneous)
    print(f"\n=== {name}  pos2026=({c26.ra.deg:.5f},{c26.dec.deg:.5f}) query {dt:.1f}s  N={len(r)}")
    print(" collections:",dict(Counter(r['obs_collection'])))
    print(" detectors:",dict(sorted(Counter(r['energy_bandpassname']).items())))
    print(" size kB: median",np.median(r['access_estsize']),"total GB",np.sum(r['access_estsize'])/1e6)
    for cl in clusters:
        cl=np.array(cl); ts=Time(cl,format='mjd')
        nexp=len(np.unique(np.round(cl,3)))
        print(f"  epoch {ts.min().iso[:10]} -> {ts.max().iso[:10]}: {len(cl)} images, {nexp} distinct exposure times(~pointings)")
    out[name]=dict(ra=c26.ra.deg,dec=c26.dec.deg,n=len(r))
    r.write(f"sia_{name}.ecsv",overwrite=True)
json.dump(out,open('targets2026.json','w'),indent=1)
