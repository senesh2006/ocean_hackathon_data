import pandas as pd,numpy as np,json,glob,os,datetime
os.makedirs("merged",exist_ok=True);os.makedirs("train_ready",exist_ok=True)
# GBIF raw from pages
rows=[]
for f in glob.glob("/tmp/gb2/*.json"):
  try: rows+=json.load(open(f))["results"]
  except: pass
cols=["key","scientificName","species","family","vernacularName","decimalLatitude","decimalLongitude","coordinateUncertaintyInMeters","depth","eventDate","year","month","basisOfRecord","datasetKey","datasetName","institutionCode","license","issues"]
g=pd.DataFrame(rows).reindex(columns=cols); g["issues"]=[";".join(i) if isinstance(i,list) else "" for i in g.issues]
g=g.drop_duplicates("key"); g.to_csv("gbif/gbif_srilanka_fish.csv",index=False)
o=pd.read_csv("obis/obis_srilanka_fish.csv")
a=pd.DataFrame({"source":"OBIS","record_id":o.id.astype(str),"scientific_name":o.scientificName,"species":o.species,"family":o.family,
 "lat":o.decimalLatitude,"lon":o.decimalLongitude,"coord_uncertainty_m":np.nan,"depth_m":o.depth,"event_date":o.eventDate,
 "basis_of_record":o.basisOfRecord,"dataset":o.datasetName,"license":o.license,"qc_flags":o["flags"].fillna("")})
b=pd.DataFrame({"source":"GBIF","record_id":g.key.astype(str),"scientific_name":g.scientificName,"species":g.species,"family":g.family,
 "lat":g.decimalLatitude,"lon":g.decimalLongitude,"coord_uncertainty_m":g.coordinateUncertaintyInMeters,"depth_m":g.depth,"event_date":g.eventDate,
 "basis_of_record":g.basisOfRecord,"dataset":g.datasetName,"license":g.license,"qc_flags":g.issues})
m=pd.concat([a,b],ignore_index=True); n0=len(m)
m["date"]=pd.to_datetime(m.event_date.astype(str).str[:10],errors="coerce",utc=True)
print("nodate",m.date.isna().sum(),"nosp",m.species.isna().sum());m=m.dropna(subset=["lat","lon","date","species"])
m=m[(m.lat.between(4,11))&(m.lon.between(77,85))]
m["year"]=m.date.dt.year;m["month"]=m.date.dt.month
m=m[(m.year>=1900)&(m.date<=pd.Timestamp.now(tz="UTC"))]
m=m[~m.qc_flags.str.contains("ZERO_COORDINATE|COORDINATE_INVALID|COORDINATE_OUT_OF_RANGE|COUNTRY_COORDINATE_MISMATCH",na=False)]
# dedupe across sources
m["_k"]=m.species+"|"+m.lat.round(3).astype(str)+"|"+m.lon.round(3).astype(str)+"|"+m.date.dt.strftime("%Y-%m-%d")
m=m.sort_values("source",ascending=False).drop_duplicates("_k").drop(columns="_k")
# bathy
bt=pd.read_csv("env/bathy_etopo2022.csv",skiprows=[1])
lat_u=np.sort(bt.latitude.unique());lon_u=np.sort(bt.longitude.unique())
Z=bt.pivot(index="latitude",columns="longitude",values="z").reindex(index=lat_u,columns=lon_u).values
def near(u,v): i=np.searchsorted(u,v).clip(1,len(u)-1); return np.where(np.abs(u[i-1]-v)<np.abs(u[i]-v),i-1,i)
ii=near(lat_u,m.lat.values);jj=near(lon_u,m.lon.values)
W=(Z<0);Wd=W.copy()
for di in(-1,0,1):
  for dj in(-1,0,1): Wd|=np.roll(np.roll(W,di,0),dj,1)
m["bathy_depth_m"]=Z[ii,jj]
m["coastal_snap"]=((Z[ii,jj]>=0)&Wd[ii,jj]).astype(int)
m["_water"]=Wd[ii,jj]
m[~m._water].drop(columns="_water").assign(date=lambda d:d.date.dt.strftime("%Y-%m-%d")).drop(columns="event_date").to_csv("merged/srilanka_fish_inland_or_land_excluded.csv",index=False)
print("pre-land",len(m),"land",(m.bathy_depth_m>=0).sum(),"land<=50m",((m.bathy_depth_m>=0)&(m.bathy_depth_m<=50)).sum())
m=m[m._water].drop(columns="_water")  # drop on land (>~5km inland)
m["bathy_depth_m"]=(-m.bathy_depth_m).clip(lower=0)
# monthly env
def envmatch(fn,var,out):
  e=pd.read_csv(fn,skiprows=[1]);e["t"]=pd.to_datetime(e.time).dt.tz_localize(None)+pd.Timedelta(days=1)
  e["ym"]=e.t.dt.year*100+e.t.dt.month
  la=np.sort(e.latitude.unique());lo=np.sort(e.longitude.unique())
  key=(e.ym.astype(str)+"_"+near(la,e.latitude.values).astype(str)+"_"+near(lo,e.longitude.values).astype(str))
  d=dict(zip(key,e[var]))
  k=((m.year*100+m.month).astype(str)+"_"+near(la,m.lat.values).astype(str)+"_"+near(lo,m.lon.values).astype(str))
  m[out]=k.map(d).astype(float)
  # climatology fallback
  e["mo"]=e.t.dt.month;c=e.groupby([near(la,e.latitude.values),near(lo,e.longitude.values),"mo"])[var].mean()
  ck=list(zip(near(la,m.lat.values),near(lo,m.lon.values),m.month))
  m[out+"_clim"]=[c.get(x,np.nan) for x in ck]
  return e
envmatch("env/sst_monthly.csv","sea_surface_temperature","sst_c")
envmatch("env/chla_monthly.csv","chlor_a","chla_mg_m3")
m["date"]=m.date.dt.strftime("%Y-%m-%d"); m=m.drop(columns="event_date")
m.to_parquet("merged/srilanka_fish_occurrences_clean.parquet",index=False)
m.to_csv("merged/srilanka_fish_occurrences_clean.csv",index=False)
print("raw",n0,"clean",len(m),"species",m.species.nunique(),"sst",m.sst_c.notna().sum(),"chl",m.chla_mg_m3.notna().sum())
# species list
fb=pd.read_csv("fishbase/fishbase_srilanka_species.csv",low_memory=False)
fb["sn"]=fb.Genus+" "+fb.Species
sl=m.groupby("species").agg(family=("family","first"),record_count=("record_id","size"),sources=("source",lambda s:";".join(sorted(set(s))))).reset_index()
sl=sl.merge(fb[["sn","FBname","Status","DemersPelag"]].drop_duplicates("sn"),left_on="species",right_on="sn",how="left").drop(columns="sn")
sl=sl.rename(columns={"species":"scientific_name","FBname":"common_name","Status":"fishbase_sri_lanka_status"}).sort_values("record_count",ascending=False)
sl.to_csv("species_list.csv",index=False)
# train ready
t=m.copy()
t["label_species"]=t.species; t["label_id"]=t.species.astype("category").cat.codes
t["month_sin"]=np.sin(2*np.pi*t.month/12);t["month_cos"]=np.cos(2*np.pi*t.month/12)
t["log_chla"]=np.log10(t.chla_mg_m3.fillna(t.chla_mg_m3_clim))
t["sst_filled"]=t.sst_c.fillna(t.sst_c_clim)
t["log_bathy"]=np.log1p(t.bathy_depth_m)
for c in ["PreservedSpecimen","HumanObservation","Occurrence","MaterialSample","MachineObservation"]:
  t["bor_"+c]=(t.basis_of_record==c).astype(int)
t["src_obis"]=(t.source=="OBIS").astype(int)
cell=(np.floor(t.lat)*100+np.floor(t.lon)).astype(int); t["spatial_block_1deg"]=cell
rng=np.random.RandomState(42);blocks=cell.unique();rng.shuffle(blocks)
sp={b:("test" if i%5==0 else "val" if i%5==1 else "train") for i,b in enumerate(blocks)}
t["split_spatial"]=cell.map(sp)
t["split_temporal"]=np.where(t.year>=2018,"test",np.where(t.year>=2012,"val","train"))
fc=["record_id","lat","lon","year","month","month_sin","month_cos","bathy_depth_m","log_bathy","sst_filled","log_chla","coord_uncertainty_m","depth_m"]+[c for c in t if c.startswith("bor_")]+["src_obis","coastal_snap","spatial_block_1deg","label_species","label_id","split_spatial","split_temporal"]
t[fc].to_parquet("train_ready/features.parquet",index=False)
print(t.split_spatial.value_counts().to_dict(),t.split_temporal.value_counts().to_dict())
print(m.date.min(),m.date.max())
