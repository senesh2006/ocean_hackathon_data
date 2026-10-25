import pandas as pd, json
R='/workspace/ocean_hackathon_data/'
LA0,LA1,LO0,LO1=7.9,10.9,78.6,82.0
out={}
g=pd.read_csv(R+'Fishing_sl.csv',parse_dates=['month'])
g['north']=g.latitude.between(8.5,10.5)&g.longitude.between(78.9,81.5)
g['yr']=g.month.dt.year
t=g[g.yr.between(2018,2024)].groupby('yr').agg(nat=('fishing_hours','sum'))
t['north']=g[g.north&g.yr.between(2018,2024)].groupby('yr').fishing_hours.sum()
t=t.fillna(0).round(1)
out['timeline']=[dict(y=int(i),nat=float(r.nat),north=float(r.north)) for i,r in t.iterrows()]
m=g[g.north&(g.yr==2024)].groupby(g.month.dt.month).fishing_hours.sum().round(1)
out['north_monthly_2024']=[float(m.get(i,0)) for i in range(1,13)]
c=g[(g.yr==2024)&g.latitude.between(LA0,LA1)&g.longitude.between(LO0,LO1)].groupby(['latitude','longitude']).agg(h=('fishing_hours','sum'),l=('lka_hours','sum')).reset_index()
c=c[c.h>0]
out['ais_cells']=[[round(a,2),round(b,2),round(h,1),round(l,1)] for a,b,h,l in c.values]
N=['Jaffna','Kilinochchi','Mannar','Mullaitivu','Trincomalee']
b=pd.read_csv('bulletin2025_t3_2_3_3_boats_by_district.csv'); b=b[b.year==2024]
f=pd.read_csv('bulletin2025_t1_5_active_fishers_by_district.csv'); f=f[f.year==2024].set_index('fisheries_district').active_fishers
k=pd.read_csv(R+'srilanka-fisheries-official/bulletin2025_t4_4_marine_catch_by_fisheries_district.csv'); k=k[(k.year==2024)&(~k.is_total)].set_index('fisheries_district_std').value
d=[]
for _,r in b.sort_values('fisheries_district_no').iterrows():
    n=r.fisheries_district
    d.append(dict(d=n,north=n in N,boats=int(r.total_boats),ss=int(r.small_scale_boats),imul=int(0 if pd.isna(r.IMUL) else r.IMUL),iday=int(0 if pd.isna(r.IDAY) else r.IDAY),fishers=int(f.get(n)) if n in f.index else None,catch=float(k.get(n)) if n in k.index else None))
out['districts']=d
print('districts missing',[x['d'] for x in d if x['fishers'] is None or x['catch'] is None], 'catch keys',list(k.index))
s=pd.read_csv('nsdi_fish_landing_centres_harbours.csv'); s=s[s.has_geometry&s.lat.between(LA0,LA1)&s.lon.between(LO0,LO1)]
out['nsdi']=[[round(a,4),round(o,4),n,'H' if l=='fishing_harbor' else 'L'] for a,o,n,l in s[['lat','lon','name','layer']].values]
o=pd.read_csv('osm_fishing_sites_srilanka.csv'); o=o[o.fishing_related&o.lat.between(LA0,LA1)&o.lon.between(LO0,LO1)]
out['osm']=[[round(a,4),round(x,4),str(k2),'' if pd.isna(n) else str(n)] for a,x,k2,n in o[['lat','lon','kind','name']].values]
r=pd.read_csv('rousseau2017_artisanal_effort_0p5_cells.csv')
r=r[r.Lat.between(LA0-0.3,LA1+0.3)&r.Lon.between(LO0-0.3,LO1+0.3)&r.flag.isin(['LKA','IND'])]
rr=r.groupby(['Lat','Lon','flag']).NomActive_kWdays.sum().reset_index()
out['rousseau']=[[a,x,fl,round(v)] for a,x,fl,v in rr.values]
sa=pd.read_csv('sau_lka_eez144_catch_by_year_entity_sector_gear.csv')
sa=sa[sa.year>=1990]
sec=sa.pivot_table(index='year',columns='fishing_sector',values='tonnes',aggfunc='sum').fillna(0)
print(sec.columns.tolist())
out['sau_years']=[int(y) for y in sec.index]
out['sau_sector']={c2:[round(v) for v in sec[c2]] for c2 in sec.columns}
ent=sa.assign(e=sa.fishing_entity.where(sa.fishing_entity.isin(['Sri Lanka','India']),'Other')).pivot_table(index='year',columns='e',values='tonnes',aggfunc='sum').fillna(0)
out['sau_entity']={c2:[round(v) for v in ent[c2]] for c2 in ent.columns}
# coastline clip
cl=json.load(open('raw/basemap/ne_10m_coastline.geojson'))
segs=[]
def inb(p): return LA0-0.2<=p[1]<=LA1+0.2 and LO0-0.2<=p[0]<=LO1+0.2
for ft in cl['features']:
    geo=ft['geometry']; lines=geo['coordinates'] if geo['type']=='MultiLineString' else [geo['coordinates']]
    for ln in lines:
        cur=[]
        for p in ln:
            if inb(p): cur.append([round(p[0],3),round(p[1],3)])
            else:
                if len(cur)>1: segs.append(cur)
                cur=[]
        if len(cur)>1: segs.append(cur)
out['coast']=segs
print({k3:len(v) for k3,v in out.items() if isinstance(v,list)}, sum(len(s2) for s2 in segs))
json.dump(out,open('dashboard_data.json','w'),separators=(',',':'))
import os; print(os.path.getsize('dashboard_data.json'))
