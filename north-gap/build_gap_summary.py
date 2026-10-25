import pandas as pd
R='/workspace/ocean_hackathon_data/'
g=pd.read_csv(R+'Fishing_sl.csv',parse_dates=['month'])
g['north']=g.latitude.between(8.5,10.5)&g.longitude.between(78.9,81.5)
y=g[g.month.dt.year==2024]
ais_n=y[y.north].fishing_hours.sum(); ais_t=y.fishing_hours.sum()
lka_n=y[y.north].lka_hours.sum(); lka_t=y.lka_hours.sum()
cells_n=y[y.north][['latitude','longitude']].drop_duplicates().shape[0]
cells_n_pos=y[y.north&(y.fishing_hours>0)][['latitude','longitude']].drop_duplicates().shape[0]
N=['Jaffna','Kilinochchi','Mannar','Mullaitivu','Trincomalee']
c=pd.read_csv(R+'srilanka-fisheries-official/bulletin2025_t4_4_marine_catch_by_fisheries_district.csv')
c=c[(c.year==2024)&(~c.is_total)]
b=pd.read_csv('bulletin2025_t3_2_3_3_boats_by_district.csv'); b=b[b.year==2024]
f=pd.read_csv('bulletin2025_t1_5_active_fishers_by_district.csv'); f=f[f.year==2024]
def sh(df,col,key): 
    n=df[df[key].isin(N)][col].sum(); t=df[col].sum(); return n,t
rows=[]
def add(metric,n,t,unit,src,note=''):
    rows.append(dict(metric=metric,north_value=round(float(n),2),national_value=round(float(t),2),north_share_pct=round(100*n/t,1) if t else None,unit=unit,year=2024,source=src,note=note))
add('GFW AIS apparent fishing hours (all flags)',ais_n,ais_t,'hours','Fishing_sl.csv (repo)','north = cells in 8.5-10.5N, 78.9-81.5E')
add('GFW AIS fishing hours, Sri Lanka flag',lka_n,lka_t,'hours','Fishing_sl.csv (repo)','north = bbox')
add('Marine catch',*sh(c,'value','fisheries_district_std'),'tonnes','Bulletin 2025 Table 4.4 (repo)','north = Jaffna+Kilinochchi+Mannar+Mullaitivu+Trincomalee districts')
add('Operating fishing boats (all)',*sh(b,'total_boats','fisheries_district'),'boats','Bulletin 2025 Table 3.2 (new extract)','north = 5 districts')
add('Small-scale boats (OFRP+MTRB+NTRB+NBSB)',*sh(b,'small_scale_boats','fisheries_district'),'boats','Bulletin 2025 Table 3.2 (new extract)','north = 5 districts')
add('Multi-day boats IMUL (most likely AIS-equipped)',*sh(b,'ais_likely_boats_IMUL','fisheries_district'),'boats','Bulletin 2025 Table 3.2 (new extract)','north = 5 districts')
add('Active marine fishers',*sh(f,'active_fishers','fisheries_district'),'fishers','Bulletin 2025 Table 1.5 (new extract)','north = 5 districts')
s=pd.DataFrame(rows); s.to_csv('north_gap_summary_2024.csv',index=False); s.to_parquet('north_gap_summary_2024.parquet',index=False)
print(s[['metric','north_value','national_value','north_share_pct']].to_string()); print('north cells',cells_n,'with >0 hours in 2024',cells_n_pos)
m=g[g.north&(g.month.dt.year>=2022)].groupby('month').fishing_hours.sum(); print(m.tail(12).round(1))
