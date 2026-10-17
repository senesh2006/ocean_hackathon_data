"""v2 build. Run from the dataset root with a python that has pandas+pyarrow
(e.g. /workspace/.venv/bin/python scripts/build.py).
Raw API pages: GBIF in /tmp/gb_v2/*.json (per fish order + classKey 121), OBIS extra classes in /tmp/obis_v2/,
WoRMS class lookup in /tmp/worms/worms.json."""
import pandas as pd,numpy as np,json,glob,os,re
os.makedirs("merged",exist_ok=True);os.makedirs("train_ready",exist_ok=True);os.makedirs("qc",exist_ok=True)
FISH_CLASSES={"Actinopterygii","Actinopteri","Teleostei","Elasmobranchii","Holocephali","Chondrichthyes","Myxini","Petromyzonti","Cladistia","Sarcopterygii"}
SARCO_FISH_ORDERS={"Coelacanthiformes","Ceratodontiformes","Lepidosireniformes"}  # Sarcopterygii only counts if a fish order
# Ray-finned fish orders. GBIF backbone leaves class EMPTY for these, so classKey=204 returns 0 occurrences.
ACTINO_ORDERS=set("""Acanthuriformes Acipenseriformes Albuliformes Amiiformes Anabantiformes Anguilliformes Ateleopodiformes Atheriniformes
Aulopiformes Batrachoidiformes Beloniformes Beryciformes Blenniiformes Carangiformes Centrarchiformes Cetomimiformes Characiformes
Cichliformes Clupeiformes Cypriniformes Cyprinodontiformes Elopiformes Esociformes Gadiformes Gasterosteiformes Gobiesociformes Gobiiformes
Gonorynchiformes Gymnotiformes Holocentriformes Kurtiformes Labriformes Lampriformes Lepisosteiformes Lophiiformes Mugiliformes
Mulliformes Myctophiformes Notacanthiformes Ophidiiformes Osmeriformes Osteoglossiformes Pempheriformes Perciformes Percopsiformes
Pleuronectiformes Polymixiiformes Polypteriformes Salmoniformes Scombriformes Scorpaeniformes Siluriformes Spariformes Stephanoberyciformes
Stomiiformes Synbranchiformes Syngnathiformes Tetraodontiformes Trachichthyiformes Zeiformes Istiophoriformes Callionymiformes
Uranoscopiformes Moroniformes Lutjaniformes Priacanthiformes Lobotiformes Chaetodontiformes Ephippiformes Siganiformes Trachiniformes""".split())
drop_log=[]
def log(df,src,reason):
  if len(df): drop_log.append(pd.DataFrame({"source":src,"record_id":df["record_id"].astype(str),"scientific_name":df["scientific_name"],
      "class":df["class"],"order":df["order"],"family":df["family"],"basis_of_record":df["basis_of_record"],"reason":reason}))
# ---------------- GBIF ----------------
rows=[]
for f in glob.glob("/tmp/gb_v2/*.json"): rows+=json.load(open(f))["results"]
cols=["key","scientificName","species","genus","family","order","class","classKey","orderKey","taxonKey","vernacularName","decimalLatitude","decimalLongitude",
      "coordinateUncertaintyInMeters","depth","eventDate","year","month","basisOfRecord","datasetKey","datasetName","institutionCode","license","issues"]
g=pd.DataFrame(rows).reindex(columns=cols); g["issues"]=[";".join(i) if isinstance(i,list) else "" for i in g.issues]
g=g.drop_duplicates("key")
g["class_validated"]=np.where(g["class"].notna(),g["class"],np.where(g["order"].isin(ACTINO_ORDERS),"Actinopterygii",None))
g.to_csv("gbif/gbif_srilanka_fish.csv",index=False)
# ---------------- OBIS ----------------
o=pd.read_csv("obis/obis_srilanka_fish.csv") if "class" in pd.read_csv("obis/obis_srilanka_fish.csv",nrows=1) else None
if o is None:  # first v2 run: annotate v1 OBIS rows with WoRMS class, append Elasmobranchii/Holocephali/Myxini pulls
  o=pd.read_csv("/workspace/fish-data/obis/obis_srilanka_fish.csv")
  ck=pd.read_csv("obis/obis_srilanka_fish_checklist.csv")
  w=pd.DataFrame(json.load(open("/tmp/worms/worms.json")))[["AphiaID","class","order"]]
  ck=ck.merge(w.rename(columns={"AphiaID":"acceptedNameUsageID","order":"w_order"}),on="acceptedNameUsageID",how="left")
  mp=ck.drop_duplicates("scientificName").set_index("scientificName")
  o["class"]=o.scientificName.map(mp["class"]); o["order"]=o.scientificName.map(mp["w_order"]); o["obis_query_taxonid"]=10194
  keep=list(o.columns.drop(["class","order","obis_query_taxonid"]))
  ex=[]
  for t in [10193,10196,10189]:
    d=pd.DataFrame(json.load(open(f"/tmp/obis_v2/obis_{t}.json")))
    if len(d):
      d["flags"]=[";".join(x) if isinstance(x,list) else x for x in d.get("flags",pd.Series([None]*len(d)))]
      d=d.reindex(columns=keep+["class","order"]); d["obis_query_taxonid"]=t; ex.append(d)
  o=pd.concat([o]+ex,ignore_index=True).drop_duplicates("id")
  o.to_csv("obis/obis_srilanka_fish.csv",index=False)
# ---------------- merge ----------------
a=pd.DataFrame({"source":"OBIS","record_id":o.id.astype(str),"scientific_name":o.scientificName,"species":o.species,"genus":o.scientificName.str.split().str[0],
 "family":o.family,"order":o["order"],"class":o["class"],
 "lat":o.decimalLatitude,"lon":o.decimalLongitude,"coord_uncertainty_m":np.nan,"depth_m":o.depth,"event_date":o.eventDate,
 "basis_of_record":o.basisOfRecord,"dataset":o.datasetName,"license":o.license,"qc_flags":o["flags"].fillna("")})
b=pd.DataFrame({"source":"GBIF","record_id":g.key.astype(str),"scientific_name":g.scientificName,"species":g.species,"genus":g.genus,"family":g.family,
 "order":g["order"],"class":g.class_validated,
 "lat":g.decimalLatitude,"lon":g.decimalLongitude,"coord_uncertainty_m":g.coordinateUncertaintyInMeters,"depth_m":g.depth,"event_date":g.eventDate,
 "basis_of_record":g.basisOfRecord,"dataset":g.datasetName,"license":g.license,"qc_flags":g.issues})
m=pd.concat([a,b],ignore_index=True); n0=len(m)
# GBIF returns basisOfRecord as enums (PRESERVED_SPECIMEN); normalise to Darwin Core camelCase like OBIS (v1 bug: GBIF bor_* one-hots were all 0)
BOR={k.lower().replace("_",""):k for k in ["PreservedSpecimen","HumanObservation","MaterialSample","MaterialCitation","MachineObservation","Occurrence","FossilSpecimen","LivingSpecimen","Observation"]}
m["basis_of_record"]=[BOR.get(str(x).lower().replace("_",""),x) for x in m.basis_of_record]
FUN=[]
def fun(step,df): FUN.append({"step":step,"rows":len(df),"OBIS":int((df.source=="OBIS").sum()),"GBIF":int((df.source=="GBIF").sum())})
fun("raw_combined",m)
# ---- HARD taxonomy validation ----
fish=m["class"].isin(FISH_CLASSES)&~((m["class"]=="Sarcopterygii")&~m["order"].isin(SARCO_FISH_ORDERS))
log(m[~fish],"merge","class_not_fish"); m=m[fish]
fos=m.basis_of_record.astype(str)=="FossilSpecimen"
log(m[fos],"merge","fossil_specimen"); m=m[~fos]
assert m["class"].isin(FISH_CLASSES).all()
m["fish_group"]=m["class"].map({"Actinopterygii":"ray_finned","Actinopteri":"ray_finned","Teleostei":"ray_finned","Cladistia":"ray_finned","Elasmobranchii":"shark_ray","Holocephali":"chimaera","Chondrichthyes":"shark_ray","Myxini":"hagfish","Petromyzonti":"lamprey","Sarcopterygii":"lobe_finned_fish"}); fun("after_taxonomy_validation",m)
m["date"]=pd.to_datetime(m.event_date.astype(str).str[:10],errors="coerce",utc=True)
bad=m.lat.isna()|m.lon.isna()|m.date.isna()|m.species.isna(); log(m[bad],"merge","missing_coord_date_or_species"); m=m[~bad]; fun("after_drop_missing_coord_date_species",m)
m=m[(m.lat.between(4,11))&(m.lon.between(77,85))]
m["year"]=m.date.dt.year;m["month"]=m.date.dt.month
m=m[(m.year>=1900)&(m.date<=pd.Timestamp.now(tz="UTC"))]
m=m[~m.qc_flags.str.contains("ZERO_COORDINATE|COORDINATE_INVALID|COORDINATE_OUT_OF_RANGE|COUNTRY_COORDINATE_MISMATCH",na=False)]; fun("after_box_year_coordqc",m)
m["_k"]=m.species+"|"+m.lat.round(3).astype(str)+"|"+m.lon.round(3).astype(str)+"|"+m.date.dt.strftime("%Y-%m-%d")
m=m.sort_values("source",ascending=False).drop_duplicates("_k").drop(columns="_k"); fun("after_dedupe",m)
# ---- bias / observation-type flags ----
ds=m.dataset.fillna("").astype(str); bor=m.basis_of_record.fillna("").astype(str)
cs=ds.str.contains(r"iNaturalist|observation\.org|naturgucker|citizen|eBird|Pl@ntNet|Reef Check|REEF ",case=False)
m["obs_type"]=np.select([cs,bor.isin(["PreservedSpecimen","MaterialSample","LivingSpecimen"]),
  bor.str.contains("Machine|MACHINE"),bor.str.contains("Human|HUMAN|Observation|OBSERVATION")],
  ["citizen_science","specimen","machine_observation","other_human_observation"],"other_or_unknown")
m["is_citizen_science"]=(m.obs_type=="citizen_science").astype(int); m["is_specimen"]=(m.obs_type=="specimen").astype(int)
m["pre_1980"]=(m.year<1980).astype(int)
m["obis_on_land_flag"]=m.qc_flags.str.contains("ON_LAND",na=False).astype(int)
m["depth_missing"]=m.depth_m.isna().astype(int)
# ---- bathy ----
bt=pd.read_csv("env/bathy_etopo2022.csv",skiprows=[1])
lat_u=np.sort(bt.latitude.unique());lon_u=np.sort(bt.longitude.unique())
Z=bt.pivot(index="latitude",columns="longitude",values="z").reindex(index=lat_u,columns=lon_u).values
def near(u,v): i=np.searchsorted(u,v).clip(1,len(u)-1); return np.where(np.abs(u[i-1]-v)<np.abs(u[i]-v),i-1,i)
ii=near(lat_u,m.lat.values);jj=near(lon_u,m.lon.values)
W=(Z<0);Wd=W.copy()
for di in(-1,0,1):
  for dj in(-1,0,1): Wd|=np.roll(np.roll(W,di,0),dj,1)
m["etopo_z_m"]=Z[ii,jj]
m["bathy_ge0"]=(Z[ii,jj]>=0).astype(int)
m["coastal_snap"]=((Z[ii,jj]>=0)&Wd[ii,jj]).astype(int)
m["_water"]=Wd[ii,jj]
m[~m._water].drop(columns="_water").assign(date=lambda d:d.date.dt.strftime("%Y-%m-%d")).drop(columns="event_date").to_csv("merged/srilanka_fish_inland_or_land_excluded.csv",index=False)
m=m[m._water].drop(columns="_water"); fun("after_land_mask_FINAL_clean",m); fun("recommended_subset",m[(m.obis_on_land_flag==0)&(m.etopo_z_m<0)])
m["bathy_depth_m"]=(-m.etopo_z_m).clip(lower=0)
# ---- env with source tracking ----
ENV={}
def envload(fn,var):
  e=pd.read_csv(fn,skiprows=[1]);e["t"]=pd.to_datetime(e.time).dt.tz_localize(None)+pd.Timedelta(days=1)
  e["ym"]=e.t.dt.year*100+e.t.dt.month; e["mo"]=e.t.dt.month
  la=np.sort(e.latitude.unique());lo=np.sort(e.longitude.unique())
  e["i"]=near(la,e.latitude.values);e["j"]=near(lo,e.longitude.values)
  mon=e.dropna(subset=[var]).set_index(["ym","i","j"])[var]; mon=mon[~mon.index.duplicated()]
  clim=e.groupby(["i","j","mo"])[var].mean()
  return la,lo,mon,clim
def envmatch(df,fn,var,out):
  if fn not in ENV: ENV[fn]=envload(fn,var)
  la,lo,mon,clim=ENV[fn]; i=near(la,df.lat.values);j=near(lo,df.lon.values)
  df[out]=mon.reindex(pd.MultiIndex.from_arrays([(df.year*100+df.month).values,i,j])).values
  df[out+"_clim"]=clim.reindex(pd.MultiIndex.from_arrays([i,j,df.month.values])).values
  near_c=np.full(len(df),np.nan); miss=np.where(df[out].isna().values&df[out+"_clim"].isna().values)[0]
  for q in miss:  # nearest cell (<=2 cells, ~0.5 deg) that has a climatology value for that month (coastal cells are NaN in the 0.25deg grid)
    best=None
    for r in (1,2):
      for di in range(-r,r+1):
        for dj in range(-r,r+1):
          v=clim.get((i[q]+di,j[q]+dj,df.month.values[q]),np.nan)
          if not np.isnan(v):
            d=di*di+dj*dj
            if best is None or d<best[0]: best=(d,v)
      if best: break
    if best: near_c[q]=best[1]
  df[out+"_clim"]=np.where(df[out+"_clim"].isna(),near_c,df[out+"_clim"])
  df[out+"_source"]=np.select([df[out].notna(),~np.isnan(near_c),df[out+"_clim"].notna()],["month_matched","climatology_nearest_cell","climatology"],"missing")
  return df
SST=("env/sst_monthly.csv","sea_surface_temperature");CHL=("env/chla_monthly.csv","chlor_a")
m=envmatch(m,*SST,"sst_c"); m=envmatch(m,*CHL,"chla_mg_m3")
m["recommended_training"]=((m.obis_on_land_flag==0)&(m.bathy_ge0==0)).astype(int)
m["date"]=m.date.dt.strftime("%Y-%m-%d"); m=m.drop(columns="event_date")
m.to_parquet("merged/srilanka_fish_occurrences_clean.parquet",index=False)
m.to_csv("merged/srilanka_fish_occurrences_clean.csv",index=False)
print("raw",n0,"clean",len(m),"species",m.species.nunique(),m.source.value_counts().to_dict(),m["class"].value_counts().to_dict())
# ---- species list ----
fb=pd.read_csv("fishbase/fishbase_srilanka_species.csv",low_memory=False); fb["sn"]=fb.Genus+" "+fb.Species
rec=m[m.recommended_training==1]
sl=m.groupby("species").agg(genus=("genus","first"),family=("family","first"),order=("order","first"),**{"class":("class","first")},fish_group=("fish_group","first"),
   record_count=("record_id","size"),n_obis=("source",lambda s:(s=="OBIS").sum()),n_gbif=("source",lambda s:(s=="GBIF").sum()),
   n_citizen_science=("is_citizen_science","sum"),n_specimen=("is_specimen","sum"),first_year=("year","min"),last_year=("year","max"),
   sources=("source",lambda s:";".join(sorted(set(s))))).reset_index()
sl["record_count_recommended"]=sl.species.map(rec.species.value_counts()).fillna(0).astype(int)
sl["model_eligible_10"]=(sl.record_count_recommended>=10).astype(int); sl["model_eligible_20"]=(sl.record_count_recommended>=20).astype(int)
sl["model_tier"]=np.select([sl.record_count_recommended>=20,sl.record_count_recommended>=10],[">=20",">=10"],"<10")
sl=sl.merge(fb[["sn","FBname","Status","DemersPelag"]].drop_duplicates("sn"),left_on="species",right_on="sn",how="left").drop(columns="sn")
sl=sl.rename(columns={"species":"scientific_name","FBname":"common_name","Status":"fishbase_sri_lanka_status"}).sort_values("record_count",ascending=False)
sl.to_csv("species_list.csv",index=False)
# ---- train ready ----
def feats(t):
  t["month_sin"]=np.sin(2*np.pi*t.month/12);t["month_cos"]=np.cos(2*np.pi*t.month/12)
  t["sst_filled"]=t.sst_c.fillna(t.sst_c_clim); t["log_chla"]=np.log10(t.chla_mg_m3.fillna(t.chla_mg_m3_clim))
  t["log_bathy"]=np.log1p(t.bathy_depth_m); return t
t=feats(m.copy())
t["label_species"]=t.species; t["label_id"]=t.species.astype("category").cat.codes
t["label_genus"]=t.genus; t["label_family"]=t.family; t["label_order"]=t["order"]
for c in ["PreservedSpecimen","HumanObservation","Occurrence","MaterialSample","MachineObservation","MaterialCitation"]:
  t["bor_"+c]=(t.basis_of_record==c).astype(int)
t["src_obis"]=(t.source=="OBIS").astype(int)
cell=(np.floor(t.lat)*100+np.floor(t.lon)).astype(int); t["spatial_block_1deg"]=cell
rng=np.random.RandomState(42);blocks=np.sort(cell.unique());rng.shuffle(blocks)
sp={b:("test" if i%5==0 else "val" if i%5==1 else "train") for i,b in enumerate(blocks)}
t["split_spatial"]=cell.map(sp)
t["split_temporal"]=np.where(t.year>=2018,"test",np.where(t.year>=2012,"val","train"))
fc=["record_id","lat","lon","year","month","month_sin","month_cos","bathy_depth_m","log_bathy","sst_filled","log_chla","sst_c_source","chla_mg_m3_source",
    "coord_uncertainty_m","depth_m","depth_missing"]+[c for c in t if c.startswith("bor_")]+["src_obis","obs_type","is_citizen_science","is_specimen","pre_1980",
    "obis_on_land_flag","bathy_ge0","coastal_snap","recommended_training","spatial_block_1deg","label_species","label_id","label_genus","label_family","label_order","class","fish_group",
    "split_spatial","split_temporal"]
t[fc].to_parquet("train_ready/features.parquet",index=False)
r=t[t.recommended_training==1]; r[fc].to_parquet("train_ready/features_recommended.parquet",index=False)
el=set(sl.scientific_name[sl.model_eligible_10==1]); r10=r[r.label_species.isin(el)].copy()
r10["label_id"]=r10.label_species.astype("category").cat.codes; r10[fc].to_parquet("train_ready/features_recommended_min10.parquet",index=False)
print("full",len(t),t.split_spatial.value_counts().to_dict(),t.split_temporal.value_counts().to_dict())
print("recommended",len(r),"min10",len(r10),"species10",len(el),"species20",sl.model_eligible_20.sum())
# ---- background / pseudo-absence points ----
rng=np.random.RandomState(7); wi,wj=np.where(W); N=10000
k=rng.randint(0,len(wi),N)
u=pd.DataFrame({"lat":lat_u[wi[k]]+rng.uniform(-0.025,0.025,N),"lon":lon_u[wj[k]]+rng.uniform(-0.025,0.025,N),"bg_type":"uniform_water"})
# target-group: jitter real (recommended) record locations by <=0.1 deg, keep only in-water cells -> carries the same sampling bias
s=r.sample(N*2,replace=True,random_state=8)
tg=pd.DataFrame({"lat":s.lat.values+rng.uniform(-0.1,0.1,N*2),"lon":s.lon.values+rng.uniform(-0.1,0.1,N*2),"bg_type":"target_group"})
tg=tg[(tg.lat.between(4,11))&(tg.lon.between(77,85))]
tg=tg[W[near(lat_u,tg.lat.values),near(lon_u,tg.lon.values)]].head(N)
bg=pd.concat([u,tg],ignore_index=True)
# dates drawn from the occurrence (year,month) distribution -> temporally matched to presences
ym=r[["year","month"]].sample(len(bg),replace=True,random_state=9).values; bg["year"]=ym[:,0]; bg["month"]=ym[:,1]
bi=near(lat_u,bg.lat.values);bj=near(lon_u,bg.lon.values); bg["bathy_depth_m"]=(-Z[bi,bj]).clip(min=0)
bg=envmatch(bg,*SST,"sst_c"); bg=envmatch(bg,*CHL,"chla_mg_m3"); bg=feats(bg)
bc=(np.floor(bg.lat)*100+np.floor(bg.lon)).astype(int); bg["spatial_block_1deg"]=bc; bg["split_spatial"]=bc.map(sp).fillna("train")
bg["split_temporal"]=np.where(bg.year>=2018,"test",np.where(bg.year>=2012,"val","train")); bg["presence"]=0
bg.insert(0,"bg_id",["bg_%05d"%i for i in range(len(bg))])
bg.to_parquet("train_ready/background_points.parquet",index=False)
print("background",bg.bg_type.value_counts().to_dict(),bg.sst_c_source.value_counts().to_dict())
DL=pd.concat(drop_log,ignore_index=True) if drop_log else pd.DataFrame(columns=["source","record_id","scientific_name","class","order","family","basis_of_record","reason"])
DL[DL.reason!="missing_coord_date_or_species"].to_csv("qc/taxonomy_validation_dropped.csv",index=False)
DL[DL.reason=="missing_coord_date_or_species"].to_csv("qc/dropped_missing_coord_date_species.csv",index=False)
# class summary: what came in, what survived validation, what is in the final clean set
raw_cls=pd.concat([o["class"].fillna("NULL").rename("c").to_frame().assign(src="OBIS"),g["class_validated"].fillna("NULL").rename("c").to_frame().assign(src="GBIF")])
cs=raw_cls.groupby(["src","c"]).size().rename("raw_rows").reset_index().rename(columns={"src":"source","c":"class"})
fin=m.groupby(["source","class"]).size().rename("final_clean_rows").reset_index()
cs=cs.merge(fin,on=["source","class"],how="outer").fillna(0); cs["is_fish_class"]=cs["class"].isin(FISH_CLASSES)
cs.to_csv("qc/taxonomy_class_summary.csv",index=False); print(cs.to_string())
pd.DataFrame(FUN).to_csv("qc/build_funnel.csv",index=False); print(pd.DataFrame(FUN).to_string())
