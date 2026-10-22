#!/usr/bin/env python3
"""Rebuild dashboard/dashboard_data.json from the files in this repo.

Scans every git-tracked file (except dashboard/), reads row/column counts,
time coverage, spatial extent and licence (from data_library.csv or folder
catalogs), groups CSV+Parquet twins into one table, builds the map layers
(restriction zones, 800 sampled fish occurrences, GFW effort grid) and
writes the compact JSON that index.html renders. Then run build_html.py
to re-embed it into index.html.

Usage:  python dashboard/build_dashboard.py [--repo PATH] [--out PATH]
Needs:  pandas, pyarrow, numpy, shapely
"""
import json, re, os, sys, subprocess, collections, argparse
import numpy as np, pandas as pd, pyarrow.parquet as pq
from shapely.geometry import shape
from shapely.ops import unary_union

HERE=os.path.dirname(os.path.abspath(__file__))
ap=argparse.ArgumentParser()
ap.add_argument('--repo',default=os.path.dirname(HERE))
ap.add_argument('--out',default=os.path.join(HERE,'dashboard_data.json'))
args=ap.parse_args()
R=os.path.abspath(args.repo); os.chdir(R)
EXCLUDE=('dashboard/',)

# ---------------------------------------------------------------- 1. scan files
files=[f for f in subprocess.check_output(['git','ls-files']).decode().split('\n') if f and not f.startswith(EXCLUDE)]
lib=pd.read_csv('data_library.csv').set_index('path')
out=[]
LAT=re.compile(r'^(lat|latitude|decimallatitude|lat_c|lat_center|y_lat|centroid_lat|lat_deg|cell_lat|lat_dd)$',re.I)
LON=re.compile(r'^(lon|lng|long|longitude|decimallongitude|lon_c|lon_center|x_lon|centroid_lon|lon_deg|cell_lon|lon_dd)$',re.I)
TIME=re.compile(r'(date|time|year|month|period|^yr$)',re.I)
def last_commit(f):
    s=subprocess.check_output(['git','log','-1','--format=%h|%cs','--',f]).decode().strip(); return s.split('|')
for f in files:
    ext=f.rsplit('.',1)[-1].lower() if '.' in f.split('/')[-1] else ''
    size=os.path.getsize(f); rec=dict(path=f,ext=ext,size=size)
    rec['commit'],rec['date']=last_commit(f)
    df=None
    try:
        if ext=='csv': df=pd.read_csv(f,low_memory=False)
        elif ext=='tsv': df=pd.read_csv(f,sep='\t',low_memory=False,on_bad_lines='skip')
        elif ext=='parquet':
            t=pq.read_table(f); df=t.to_pandas() if t.num_rows<3_000_000 else None
            rec['rows']=t.num_rows; rec['cols']=t.num_columns
        elif ext=='geojson':
            g=json.load(open(f)); rec['rows']=len(g.get('features',[])); 
            props=set();xs=[];ys=[]
            def walk(c):
                if isinstance(c[0],(int,float)): xs.append(c[0]); ys.append(c[1])
                else:
                    for k in c: walk(k)
            for ft in g['features']:
                props|=set((ft.get('properties') or {}).keys())
                if ft.get('geometry'): walk(ft['geometry']['coordinates'])
            rec['cols']=len(props)
            if xs: rec['bbox']=[min(xs),min(ys),max(xs),max(ys)]
        elif ext=='fasta':
            rec['rows']=sum(1 for l in open(f) if l.startswith('>')); rec['cols']=2
    except Exception as e: rec['err']=str(e)[:200]
    if df is not None:
        rec['rows']=len(df); rec['cols']=df.shape[1]; rec['columns']=list(map(str,df.columns))[:80]
        la=[c for c in df.columns if LAT.match(str(c))]; lo=[c for c in df.columns if LON.match(str(c))]
        if la and lo:
            a=pd.to_numeric(df[la[0]],errors='coerce'); o=pd.to_numeric(df[lo[0]],errors='coerce')
            if a.notna().any(): rec['bbox']=[float(o.min()),float(a.min()),float(o.max()),float(a.max())]; rec['latlon']=[str(la[0]),str(lo[0])]
        tc=[c for c in df.columns if TIME.search(str(c))]
        tmin=tmax=None; used=None
        for c in tc:
            s=df[c].dropna()
            if s.empty: continue
            cl=str(c).lower()
            if re.search(r'year',cl) and not re.search(r'date',cl):
                v=pd.to_numeric(s,errors='coerce').dropna(); v=v[(v>1700)&(v<2100)]
                if v.empty: continue
                a,b=str(int(v.min())),str(int(v.max()))
            else:
                d=pd.to_datetime(s.astype(str).str.slice(0,25),errors='coerce',utc=True,format='mixed').dropna()
                d=d[(d.dt.year>1700)&(d.dt.year<2100)]
                if len(d)<0.5*len(s) or d.empty: continue
                a,b=d.min().strftime('%Y-%m-%d'),d.max().strftime('%Y-%m-%d')
            if tmin is None or a<tmin: tmin=a
            if tmax is None or b>tmax: tmax=b
            used=(used or [])+[str(c)]
        if tmin: rec['tmin'],rec['tmax'],rec['tcols']=tmin,tmax,used
    if f in lib.index:
        L=lib.loc[f]
        for k in ['dataset','description','source_name','license','commercial_use_ok','status','superseded_by','rows']:
            rec['lib_'+k]=None if pd.isna(L[k]) else str(L[k])
    out.append(rec); print('scan',f,rec.get('rows'),rec.get('err',''),file=sys.stderr)
scan=json.loads(json.dumps(out,default=str))

# ---------------------------------------------------------------- 2. classify files
def theme(p):
    if p=='Fishing_sl.csv' or p.startswith('fish-data/iotc') or (p.startswith('srilanka-fisheries-official') and 'species_list' not in p): return 'Fisheries & catch'
    if p.startswith(('srilanka-fishing-restrictions','srilanka-banned-marine')): return 'Regulations'
    if p.startswith('splitwater'): return 'Water & RO'
    if 'train_ready' in p or 'species-niche/work' in p: return 'ML training'
    if any(k in p for k in ['rainfall','wind/','climate_indices','monsoon','moon_phase']): return 'Climate & weather'
    if any(k in p for k in ['seabed','coral_reefs','bathy']): return 'Habitat & seabed'
    if p.startswith('fish-factors/species_flags'): return 'Species & biodiversity'
    if p.startswith('fish-factors') or 'fish-data/env' in p or 'chla_monthly' in p: return 'Ocean environment'
    return 'Species & biodiversity'
def dataset(p):
    if '/' not in p:
        return {'Fishing_sl.csv':'GFW fishing effort (root)','splitwater_ro_log_1h_5s.csv':'SplitWater RO log (root)'}.get(p,'Repo metadata')
    return p.split('/')[0]
def role(p):
    b=p.split('/')[-1]
    if re.search(r'catalog|data_dictionary|coverage_stats|table_inventory|^data_library',b,re.I): return 'Metadata'
    if '/qc/' in p or b.startswith('qc_') or 'outliers' in b or 'landmask' in b or b=='build_funnel.csv' or 'excluded' in b: return 'QC'
    if '/raw/' in p or b.startswith('raw_') or 'work/' in p: return 'Raw / intermediate'
    return 'Data'
def lic_override(p):
    if p.startswith('species-niche/work'): return 'CC0-1.0 AND CC-BY-4.0 AND CC-BY-NC-4.0'
    if p.startswith('species-niche'): return 'CC-BY-NC-4.0'
    if p.startswith('srilanka-fishing-restrictions/zones'): return 'CC-BY-4.0 AND ODbL-1.0'
    if p=='srilanka-fishing-restrictions/raw/gb_lka_adm2.geojson': return 'ODbL-1.0'
    if p.startswith('srilanka-fishing-restrictions'): return 'CC-BY-4.0 (compilation of LK gazettes)'
    return None
def src_override(p):
    if p.startswith('species-niche/species_prey'): return 'GloBI + FishBase v24.07'
    if p.startswith('species-niche/work'): return 'Derived: fish-data v3 + fish-factors'
    if p.startswith('species-niche'): return 'FishBase v24.07 + AquaMaps HSPEN + fish-data v3'
    if p.startswith('srilanka-fishing-restrictions/zones'): return 'Marine Regions v12 + OSM/Nominatim + gazettes + Natural Earth'
    if p.startswith('srilanka-fishing-restrictions/raw/gb'): return 'geoBoundaries LKA ADM2'
    if p.startswith('srilanka-fishing-restrictions'): return 'LK Govt Gazettes / DFAR / IOTC / CITES'
    return None
def lclass(l):
    l=l or 'unknown'
    if 'unknown' in l: return 'Unknown'
    if 'NC' in l or 'NonCommercial' in l: return 'Non-commercial'
    if 'GovLK' in l or 'IOTC' in l or 'GenBank' in l: return 'Custom / no stated licence'
    if 'SA' in l or 'ODbL' in l: return 'Share-alike'
    return 'Open'
def pretty(l):
    m={'CC-BY-4.0':'CC BY 4.0','CC-BY-NC-4.0':'CC BY-NC 4.0','CC0-1.0 AND CC-BY-4.0 AND CC-BY-NC-4.0':'Mixed CC0 / CC BY / CC BY-NC','LicenseRef-GovLK-NoStatedLicence':'LK Govt, no stated licence','LicenseRef-PublicDomain-USGov':'Public domain (US Gov)','LicenseRef-PublicDomain-CHIRPS':'Public domain (CHIRPS)','LicenseRef-UNEP-WCMC-NonCommercial':'UNEP-WCMC non-commercial','LicenseRef-PublicDomain-USGov AND LicenseRef-UNEP-WCMC-NonCommercial':'Public domain + UNEP-WCMC NC','LicenseRef-IOTC-Public-Acknowledge':'IOTC public, acknowledge','LicenseRef-NCBI-GenBank':'NCBI GenBank terms','CC-BY-SA-4.0':'CC BY-SA 4.0','CC-BY-4.0 AND ODbL-1.0':'CC BY 4.0 + ODbL 1.0','ODbL-1.0':'ODbL 1.0','unknown':'Unknown (owner to confirm)'}
    return m.get(l,l)
YEARCOLS={'year','YEAR','date_year','survey_year_start'}
DATECOLS={'time','date','month','eventDate','timestamp','register_date','gazette_date','instrument_date','collection_date','collection_date_start'}
def tcov(p,ext):
    # recompute observation-time coverage from data columns only
    if ext not in ('csv','parquet','tsv'): return None,None
    if role(p)=='Metadata' or 'population_tables' in p: return None,None
    df=pd.read_parquet(p) if ext=='parquet' else pd.read_csv(p,sep='\t' if ext=='tsv' else ',',low_memory=False,on_bad_lines='skip')
    yc=[c for c in df.columns if c in YEARCOLS]
    if p.endswith('fish-data/species_list.csv'): yc=['first_year','last_year']
    if yc:
        v=pd.concat([pd.to_numeric(df[c],errors='coerce') for c in yc]).dropna(); v=v[(v>1700)&(v<2100)]
        if not v.empty: return str(int(v.min())),str(int(v.max()))
    dc=[c for c in df.columns if c in DATECOLS]
    best=None
    for c in dc:
        s=df[c].dropna().astype(str).str.slice(0,19)
        d=pd.to_datetime(s,errors='coerce',format='mixed').dropna()
        if d.empty or len(d)<0.5*len(s): continue
        a,b=d.min().strftime('%Y-%m'),d.max().strftime('%Y-%m')
        best=(a if not best or a<best[0] else best[0], b if not best or b>best[1] else best[1])
    return best if best else (None,None)
recs=[]
for r in scan:
    p=r['path']; ext=r['ext']
    if ext in ('py','md','cff','') or p.startswith('LICENSES') or p=='LICENSE': kind='doc'
    elif ext in ('csv','parquet','geojson','tsv','fasta'): kind='table'
    else: kind='rawdoc'
    lic=lic_override(p) or r.get('lib_license') or ('CC-BY-4.0' if kind=='doc' else 'unknown')
    t0,t1=tcov(p,ext) if kind=='table' else (None,None)
    recs.append(dict(p=p,ext=ext,kind=kind,size=r['size'],rows=r.get('rows'),cols=r.get('cols'),bbox=r.get('bbox'),
        date=r['date'],ds=dataset(p),th=theme(p),role=role(p),lic=lic,src=src_override(p) or r.get('lib_source_name') or '',
        desc=r.get('lib_description') or '',status=r.get('lib_status') or 'current',t0=t0,t1=t1))
# superseded folder
for x in recs:
    if x['p'].startswith('updated data sets/'): x['status']='superseded (v2)'
print(len(recs), collections.Counter(x['kind'] for x in recs))

# ---------------------------------------------------------------- 3. map frame
R=R.rstrip('/')+'/'
zones=json.load(open(R+'srilanka-fishing-restrictions/zones.geojson'))
eez=[f for f in zones['features'] if f['properties']['zone_id']=='LK-EEZ'][0]
eg=shape(eez['geometry']); print('eez bounds',eg.bounds)
minx,miny,maxx,maxy=eg.bounds; minx-=0.2;maxx+=0.2;miny-=0.2;maxy+=0.2
W=600; S=W/(maxx-minx); H=round((maxy-miny)*S)
mp=dict(W=W,H=H,bounds=[minx,miny,maxx,maxy])

# ---------------------------------------------------------------- 4. group into tables
tables={}
for r in recs:
    if r['kind']!='table': continue
    key=re.sub(r'\.(csv|parquet)$','',r['p']) if r['ext'] in ('csv','parquet') else r['p']
    t=tables.setdefault(key,dict(r, fmts=[], size=0, files=0, nrows=set()))
    t['fmts'].append(r['ext'].upper().replace('GEOJSON','GeoJSON').replace('PARQUET','Parquet').replace('FASTA','FASTA'))
    t['size']+=r['size']; t['files']+=1; t['nrows'].add(r['rows'])
    if r['date']>t['date']: t['date']=r['date']
    if r.get('bbox') and not t.get('bbox'): t['bbox']=r['bbox']
mism=[k for k,t in tables.items() if len(t['nrows'])>1]
print('rowcount mismatch csv/parquet:',mism)
T=[]
for k,t in tables.items():
    name=k.split('/')[-1]
    T.append(dict(id=k,name=name,ds=t['ds'],th=t['th'],role=t['role'],fmt=' + '.join(sorted(set(t['fmts']))),files=t['files'],rows=t['rows'],cols=t['cols'],size=t['size'],
      t0=t['t0'],t1=t['t1'],sp=bool(t.get('bbox')),bbox=[round(v,2) for v in t['bbox']] if t.get('bbox') else None,src=t['src'],lic=t['lic'],date=t['date'],status=t['status'],desc=t['desc']))
# raw doc groups
G=collections.OrderedDict()
for r in recs:
    if r['kind']!='rawdoc': continue
    d=os.path.dirname(r['p']) or '.'
    g=G.setdefault(d,dict(n=0,size=0,exts=collections.Counter(),date='',r=r))
    g['n']+=1; g['size']+=r['size']; g['exts'][r['ext']]+=1; g['date']=max(g['date'],r['date'])
for d,g in G.items():
    r=g['r']
    T.append(dict(id=d+'/ (raw files)',name=f"{d.split('/')[-1]}/ ({g['n']} files)",ds=r['ds'],th=r['th'],role='Raw / intermediate' if r['role']!='QC' else 'QC',fmt=' + '.join(f"{v} {k.upper()}" for k,v in g['exts'].items()),files=g['n'],rows=None,cols=None,size=g['size'],t0=None,t1=None,sp=False,bbox=None,src=r['src'],lic=r['lic'],date=g['date'],status=r['status'],desc=''))
docs=[r for r in recs if r['kind']=='doc']
D=dict(tables=T,map=mp,nfiles=len(recs),totalsize=sum(r['size'] for r in recs),ndocs=len(docs),docsize=sum(r['size'] for r in docs),
   nraw=sum(1 for r in recs if r['kind']=='rawdoc'), ntablefiles=sum(1 for r in recs if r['kind']=='table'))
cur=[t for t in T if t['status']!='superseded (v2)']
print('unique tables',sum(1 for t in T if t['rows'] is not None),'data tables', sum(1 for t in T if t['role']=='Data'))
print('rows all',sum(t['rows'] or 0 for t in T),'rows current',sum(t['rows'] or 0 for t in cur),'rows current Data',sum(t['rows'] or 0 for t in cur if t['role']=='Data'))
print('size',sum(r['size'] for r in recs)/1e6)
for th,c in collections.Counter(t['th'] for t in T).items(): print(th,c)
print(set(t['lic'] for t in T))

# ---------------------------------------------------------------- 5. compact for the page
minx,miny,maxx,maxy=mp['bounds']; S=mp['W']/(maxx-minx)
def lclass(l):
    if 'unknown' in l: return 'Unknown'
    if 'NC' in l or 'NonCommercial' in l: return 'Non-commercial'
    if 'GovLK' in l or 'IOTC' in l or 'GenBank' in l: return 'Custom / no stated licence'
    if 'SA' in l or 'ODbL' in l: return 'Share-alike'
    return 'Open'
pretty={'CC-BY-4.0':'CC BY 4.0','CC-BY-NC-4.0':'CC BY-NC 4.0','CC0-1.0 AND CC-BY-4.0 AND CC-BY-NC-4.0':'Mixed CC0 / CC BY / CC BY-NC (per record)','LicenseRef-GovLK-NoStatedLicence':'LK Govt, no stated licence','LicenseRef-PublicDomain-USGov':'Public domain (US Gov)','LicenseRef-PublicDomain-CHIRPS':'Public domain (CHIRPS)','LicenseRef-UNEP-WCMC-NonCommercial':'UNEP-WCMC non-commercial','LicenseRef-PublicDomain-USGov AND LicenseRef-UNEP-WCMC-NonCommercial':'Public domain + UNEP-WCMC non-commercial','LicenseRef-IOTC-Public-Acknowledge':'IOTC public, acknowledge','LicenseRef-NCBI-GenBank':'NCBI GenBank terms','CC-BY-SA-4.0':'CC BY-SA 4.0','CC-BY-4.0 AND ODbL-1.0':'CC BY 4.0 + ODbL 1.0','ODbL-1.0':'ODbL 1.0','unknown':'Unknown (owner to confirm)','CC-BY-4.0 (compilation of LK gazettes)':'CC BY 4.0 (compilation of LK gazettes)'}
T=D['tables']
for t in T:
    if t['role']=='Metadata': t['th']='Catalog & metadata'
    if t['ds']=='Repo metadata': t['th']='Catalog & metadata'
DS=sorted(set(t['ds'] for t in T)); TH=sorted(set(t['th'] for t in T)); RO=['Data','QC','Metadata','Raw / intermediate']
SRC=sorted(set(t['src'] for t in T)); LIC=sorted(set(t['lic'] for t in T))
rows=[[t['id'],DS.index(t['ds']),TH.index(t['th']),RO.index(t['role']),t['fmt'],t['files'],t['rows'],t['cols'],t['size'],t['t0'],t['t1'],1 if t['sp'] else 0,SRC.index(t['src']),LIC.index(t['lic']),t['date'],1 if 'superseded' in t['status'] else 0] for t in T]
# map compaction
zones=json.load(open(R+'srilanka-fishing-restrictions/zones.geojson'))
def P(x,y): return f"{(x-minx)*S:.0f} {(maxy-y)*S:.0f}"
def path(g):
    out=[]
    if g.geom_type in ('Polygon','MultiPolygon'):
        for p in ([g] if g.geom_type=='Polygon' else g.geoms):
            for ring in [p.exterior]+list(p.interiors):
                pts=[]
                for x,y in ring.coords:
                    q=P(x,y)
                    if not pts or pts[-1]!=q: pts.append(q)
                if len(pts)>=4: out.append('M'+'L'.join(pts)+'Z')
    else:
        for l in ([g] if g.geom_type=='LineString' else g.geoms):
            out.append('M'+'L'.join(P(x,y) for x,y in l.coords))
    return ''.join(out)
zc=pd.read_csv(R+'srilanka-fishing-restrictions/zones.csv').set_index('zone_id')
Z=[]
for f in zones['features']:
    pr=f['properties']; zid=pr['zone_id']
    if zid=='LK-SLW': continue
    tol=0.03 if zid=='LK-EEZ' else 0.01
    g=shape(f['geometry']).simplify(tol,preserve_topology=True)
    n=zc.loc[zid,'n_rules']; a=pr.get('area_km2')
    Z.append([zid,pr['name'],pr['zone_type'],pr['geometry_quality'],None if a is None or pd.isna(a) else round(a),0 if pd.isna(n) else int(n),path(g)])
m=pd.read_parquet(R+'fish-data/merged/srilanka_fish_occurrences_clean.parquet')
smp=m.sample(800,random_state=7)
occ=[v for x,y in zip(smp.lon,smp.lat) for v in (round((x-minx)*S),round((maxy-y)*S))]
g=pd.read_csv(R+'Fishing_sl.csv')
g['la']=np.floor((g.latitude)/0.2)*0.2; g['lo']=np.floor((g.longitude)/0.2)*0.2
c=g.groupby(['la','lo']).fishing_hours.sum().reset_index(); c=c[c.fishing_hours>0]
mx=np.log10(c.fishing_hours.max())
gfw=[v for la,lo,h in zip(c.la,c.lo,c.fishing_hours) for v in (round((lo-minx)*S,1),round((maxy-la-0.2)*S,1),max(1,round(9*np.log10(max(h,1))/mx)))]
adm=json.load(open(R+'srilanka-fishing-restrictions/raw/gb_lka_adm2.geojson'))
from shapely.ops import unary_union
land=unary_union([shape(f['geometry']).buffer(0) for f in adm['features']]).simplify(0.01)
M=dict(W=mp['W'],H=mp['H'],cell=round(0.2*S,1),land=path(land),zones=Z,occ=occ,gfw=gfw,gfwMax=round(float(c.fishing_hours.max())),gfwTotal=round(float(g.fishing_hours.sum())),gfwCells=len(c),occN=len(m),
  gfwRange=[str(g.month.min())[:7],str(g.month.max())[:7]], ticks=[[lon,round((lon-minx)*S)] for lon in range(78,86,2)], lticks=[[lat,round((maxy-lat)*S)] for lat in range(4,12,2)])
OUT=dict(ds=DS,th=TH,ro=RO,src=SRC,lic=LIC,licP=[pretty.get(l,l) for l in LIC],licC=[lclass(l) for l in LIC],t=rows,nfiles=D['nfiles'],totalsize=D['totalsize'],ndocs=D['ndocs'],nraw=D['nraw'],ntf=D['ntablefiles'],map=M)


# ---------------------------------------------------------------- 6. final clean-up
# Shorter source labels for display
SRC_SHORT={
 'Compiled from Sri Lanka FARA No.2 of 1996 regulations (Shark Fisheries Mgmt Regs 2015, Gazette 1938/2; Lobster Regs 2000, Gazette 1123/2; Monofilament Nets Regs, Gazette 1454/33), FARA (Amendment) Act No.11 of 2017, Fauna & Flora Protection Ordinance as amended by Act No.22 of 2009, DFAR regulations list, IOTC CMMs 2026, CITES/IUCN listings, WoRMS':
   'Compiled from FARA 1996 regulations, Act No.11 of 2017, FFPO 2009, DFAR list, IOTC CMMs 2026, CITES/IUCN, WoRMS',
 'Ministry of Fisheries Sri Lanka (Statistics Unit) fish species list; names validated with WoRMS':
   'Ministry of Fisheries Sri Lanka (Statistics Unit) species list, names checked with WoRMS',
 'Ministry of Fisheries Sri Lanka (Statistics Unit), Annual Fisheries Statistical Bulletin 2025':
   'Ministry of Fisheries Sri Lanka (Statistics Unit), Fisheries Statistical Bulletin 2025',
 'NOAA NCEI Blended Sea Winds via CoastWatch ERDDAP; QC by ocean_hackathon_data (fish-factors/scripts/qc_windstress.py)':
   'NOAA NCEI Blended Sea Winds via CoastWatch ERDDAP, QC by qc_windstress.py',
}
OUT['src']=[SRC_SHORT.get(s,s) for s in OUT['src']]
# NCBI GenBank terms are custom terms, not non-commercial ('NC' matched 'NCBI')
OUT['licC']=['Custom / no stated licence' if 'GenBank' in l else c for l,c in zip(OUT['lic'],OUT['licC'])]
# Whole-pixel GFW cell positions
M['gfw']=[v if i%3==2 else round(v) for i,v in enumerate(M['gfw'])]
# EEZ and 12 NM sea: keep the outer outline only (drawn as dashed outlines)
for z in M['zones']:
    if z[0] in ('LK-EEZ','LK-TS12'):
        z[6]=re.findall(r'M[^MZ]+Z',z[6])[0]
OUT['snapshot']=subprocess.check_output(['git','rev-parse','--short','HEAD']).decode().strip()
with open(args.out,'w') as fh: json.dump(OUT,fh,separators=(',',':'))
print('wrote',args.out,os.path.getsize(args.out),'bytes;',len(OUT['t']),'inventory entries;',OUT['nfiles'],'files')

# ---------------------------------------------------------------- 7. flat inventory CSV (same numbers as the page)
def write_inventory_csv(O, path):
    cols=['path','dataset','theme','role','format','files','rows','cols','size_bytes','time_start','time_end','spatial','source','licence','licence_type','last_commit_date','superseded']
    recs=[[r[0],O['ds'][r[1]],O['th'][r[2]],O['ro'][r[3]],r[4],r[5],r[6],r[7],r[8],r[9],r[10],bool(r[11]),O['src'][r[12]],O['licP'][r[13]],O['licC'][r[13]],r[14],bool(r[15])] for r in O['t']]
    pd.DataFrame(recs,columns=cols).astype({'rows':'Int64','cols':'Int64'}).to_csv(path,index=False)
write_inventory_csv(OUT, os.path.join(os.path.dirname(os.path.abspath(args.out)),'dashboard_inventory.csv'))
