import re, subprocess, pandas as pd
PDF='/workspace/ocean_hackathon_data/srilanka-fisheries-official/raw/Annual-Fisheries-Statistical-Bulletin-2025.pdf'
URL='https://www.fisheries.gov.lk/wp-content/uploads/2026/10/Annual-Fisheries-Statistical-Bulletin-2025.pdf'
def page(p): return subprocess.run(['pdftotext','-layout','-f',str(p),'-l',str(p),PDF,'-'],capture_output=True,text=True).stdout
def num(s): return None if s.strip() in ('-','') else int(s.replace(',',''))
row=re.compile(r'^\s*(\d{1,2})\s+([A-Za-z]+)\s+(.*)$')
NORTH={'Jaffna','Kilinochchi','Mannar','Mullaitivu','Trincomalee'}
out=[]
for p,yr,status in [(36,2024,'final'),(37,2025,'provisional')]:
    for line in page(p).splitlines():
        m=row.match(line)
        if not m: continue
        vals=m.group(3).split()
        if len(vals)!=7: continue
        cols=['IMUL','IDAY','OFRP','MTRB','NTRB','NBSB','total_boats']
        r=dict(table_id='3.2' if yr==2024 else '3.3',pdf_page=p,year=yr,year_status=status,fisheries_district_no=int(m.group(1)),fisheries_district=m.group(2).replace('Mullativu','Mullaitivu'))
        r.update({c:num(v) for c,v in zip(cols,vals)})
        out.append(r)
b=pd.DataFrame(out)
b['small_scale_boats']=b[['OFRP','MTRB','NTRB','NBSB']].fillna(0).sum(axis=1).astype(int)
b['ais_likely_boats_IMUL']=b.IMUL.fillna(0).astype(int)
b['pct_small_scale']=(100*b.small_scale_boats/b.total_boats).round(1)
b['north_focus']=b.fisheries_district.isin(NORTH)
b['source_url']=URL
# validate totals
for yr,g in b.groupby('year'):
    s=g[['IMUL','IDAY','OFRP','MTRB','NTRB','NBSB']].fillna(0).sum(axis=1)
    assert (s==g.total_boats).all(), (yr, g[s!=g.total_boats])
assert len(b)==30
tot={2024:49271,2025:59180}
for yr,g in b.groupby('year'): assert g.total_boats.sum()==tot[yr],(yr,g.total_boats.sum())
b.to_csv('bulletin2025_t3_2_3_3_boats_by_district.csv',index=False); b.to_parquet('bulletin2025_t3_2_3_3_boats_by_district.parquet',index=False)
# fishers table 1.5 (first table on page 20)
yrs=[1972,1989,1999,2004,2011,2016,2022,2023,2024,2025]
fo=[]
txt=page(20).split('Table 1.6')[0]
for line in txt.splitlines():
    m=row.match(line)
    if not m: continue
    vals=m.group(3).split()
    if len(vals)!=10: continue
    for y,v in zip(yrs,vals):
        fo.append(dict(table_id='1.5',pdf_page=20,year=y,year_status='provisional' if y==2025 else 'final',fisheries_district_no=int(m.group(1)),fisheries_district=m.group(2).replace('Mullativu','Mullaitivu'),active_fishers=num(v),north_focus=m.group(2).replace('Mullativu','Mullaitivu') in NORTH,source_url=URL))
f=pd.DataFrame(fo); assert f.fisheries_district.nunique()==15
assert f[f.year==2024].active_fishers.sum()==225480, f[f.year==2024].active_fishers.sum()
assert f[f.year==2025].active_fishers.sum()==226154
f.to_csv('bulletin2025_t1_5_active_fishers_by_district.csv',index=False); f.to_parquet('bulletin2025_t1_5_active_fishers_by_district.parquet',index=False)
print(b[b.year==2024][['fisheries_district','IMUL','total_boats','small_scale_boats','pct_small_scale']].to_string())
