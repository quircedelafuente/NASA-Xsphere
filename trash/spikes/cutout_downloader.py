import sys, os, time, urllib.request, numpy as np
from concurrent.futures import ThreadPoolExecutor
from astropy.table import Table
name, dets, size = sys.argv[1], sys.argv[2].split(','), float(sys.argv[3])
import json; P=json.load(open('targets2026.json'))[name]
t=Table.read(f'sia_{name}.ecsv')
t=t[np.isin(t['energy_bandpassname'],[f'SPHEREx-D{d}' for d in dets])]
if len(sys.argv)>4: t=t[np.isin(t['obs_collection'],sys.argv[4].split(','))]
os.makedirs(f'dl/{name}',exist_ok=True)
def get(row):
    fn=f"dl/{name}/{row['obs_id']}_{row['energy_bandpassname'][-2:]}.fits"
    if os.path.exists(fn): return fn,0
    url=row['access_url']+f"?center={P['ra']},{P['dec']}&size={size}"
    for a in range(3):
        try:
            t0=time.time(); urllib.request.urlretrieve(url,fn); return fn,time.time()-t0
        except Exception as e: err=e; time.sleep(3)
    return None,str(err)
t0=time.time()
with ThreadPoolExecutor(5) as ex: res=list(ex.map(get,t))
ok=[r for r in res if r[0]]
print(name,'requested',len(t),'ok',len(ok),'wall',round(time.time()-t0,1),'s; failures',[r[1] for r in res if not r[0]][:3])
print('total MB',sum(os.path.getsize(r[0]) for r in ok)/1e6)
