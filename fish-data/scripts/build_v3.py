"""fish-data v3 = v2 outputs + reviewer fixes. Run from dataset root: python3 scripts/build_v3.py
Inputs: v2 outputs (copied into this folder), WoRMS AphiaRecordsByMatchNames results (qc/_worms_match_raw.json, fetched 2026-10-17),
FishBase v24.07 species + synonyms tables (rOpenSci HF mirror https://huggingface.co/datasets/cboettig/fishbase, cached /tmp/fbp/*.parquet)."""
import pandas as pd,numpy as np,json,re,os
FISH_CLASSES={"Actinopterygii","Elasmobranchii","Holocephali","Myxini","Petromyzonti"}
CLASS_MAP={"Teleostei":"Actinopterygii","Actinopteri":"Actinopterygii","Cladistia":"Actinopterygii","Chondrichthyes":"Elasmobranchii"}
BOR={k.lower().replace("_",""):k for k in ["PreservedSpecimen","HumanObservation","MaterialSample","MaterialCitation","MachineObservation","Occurrence","FossilSpecimen","LivingSpecimen","Observation"]}
def bor_norm(s): return s.map(lambda x: BOR.get(str(x).lower().replace("_","").replace(" ",""),x) if pd.notna(x) else x)
def lic_norm(x):
  if pd.isna(x) or str(x).strip()=="": return "unknown"
  s=str(x).lower().replace("_","-").replace(" ","")
  if "zero" in s or "cc0" in s or "waived" in s or "publicdomain" in s: return "CC0-1.0"
  nc="nc" in s.replace("licenses/","").split("/")[0] or "by-nc" in s or "bync" in s
  ver="4.0" if "4.0" in s else "3.0" if "3.0" in s else "unspecified"
  if "by" in s: return f"CC-BY-NC-{ver}" if nc else f"CC-BY-{ver}"
  return "other:"+str(x)
FUN=[]
def fun(step,df): FUN.append({"step":step,"rows":len(df),"OBIS":int((df.source=="OBIS").sum()),"GBIF":int((df.source=="GBIF").sum())})
# ---------- raw files: add normalised columns (original columns untouched) ----------
o=pd.read_csv("obis/obis_srilanka_fish.csv",low_memory=False)
o["basis_of_record_norm"]=bor_norm(o.basisOfRecord)
# 1,4xx OBIS records have no record-level licence: fall back to the dataset-level intellectualrights (api.obis.org/v3/dataset/{id}, fetched 2026-10-17, qc/obis_dataset_licenses.csv)
DSL=pd.read_csv("qc/obis_dataset_licenses.csv").set_index("dataset_id").intellectualrights
o["license_level"]=np.where(o.license.notna(),"record",np.where(o.dataset_id.map(DSL).notna(),"dataset","unknown"))
o["license_norm"]=np.where(o.license.notna(),o.license.map(lic_norm),o.dataset_id.map(DSL).map(lic_norm))
o["class_original"]=o.get("class_original",o["class"]); o["class"]=o["class_original"].replace(CLASS_MAP); o.to_csv("obis/obis_srilanka_fish.csv",index=False)
g=pd.read_csv("gbif/gbif_srilanka_fish.csv",low_memory=False)
g["basis_of_record_norm"]=bor_norm(g.basisOfRecord); g["license_norm"]=g.license.map(lic_norm); g["license_level"]="record"
LN=pd.concat([o.assign(rid=o.id.astype(str))[["rid","license_norm","license_level"]].assign(src="OBIS"),g.assign(rid=g.key.astype(str))[["rid","license_norm","license_level"]].assign(src="GBIF")]).drop_duplicates(["src","rid"]).set_index(["src","rid"])
g["class_validated_original"]=g.get("class_validated_original",g.class_validated); g["class_validated"]=g.class_validated_original.replace(CLASS_MAP); g.to_csv("gbif/gbif_srilanka_fish.csv",index=False)
# ---------- WoRMS accepted names ----------
W=json.load(open("qc/_worms_match_raw.json")); wr=[]
for n,x in W.items():
  if not x: wr.append(dict(name_v2=n,accepted_name=n,aphia_id=np.nan,accepted_aphia_id=np.nan,worms_status="no_match",worms_match_type="none")); continue
  acc=[r for r in x if r.get("status")=="accepted"]; r=acc[0] if acc else x[0]
  vn=r.get("valid_name") or n
  wr.append(dict(name_v2=n,accepted_name=vn,aphia_id=r.get("AphiaID"),accepted_aphia_id=r.get("valid_AphiaID"),worms_status=r.get("status"),worms_match_type=r.get("match_type")))
wr=pd.DataFrame(wr)
# ---------- FishBase linkage (accepted name -> v2 name -> FishBase synonyms) ----------
sp=pd.read_parquet("/tmp/fbp/species.parquet",columns=["SpecCode","Genus","Species","FBname","Fresh","Brack","Saltwater","DemersPelag","DepthRangeShallow","DepthRangeDeep"]); sp["sn"]=sp.Genus+" "+sp.Species
syn=pd.read_parquet("/tmp/fbp/synonyms.parquet",columns=["SynGenus","SynSpecies","SpecCode","Status"]); syn["sn"]=syn.SynGenus.str.strip()+" "+syn.SynSpecies.str.strip()
syn=syn[syn.SpecCode.isin(sp.SpecCode)]
sn2code=sp.drop_duplicates("sn").set_index("sn").SpecCode
syn2code=syn.sort_values("Status",key=lambda s:s.ne("accepted name")).drop_duplicates("sn").set_index("sn").SpecCode
def fbcode(r):
  for nm,how in [(r.accepted_name,"accepted_name"),(r.name_v2,"v2_name")]:
    if nm in sn2code.index: return sn2code[nm],how
  for nm,how in [(r.accepted_name,"fishbase_synonym_of_accepted"),(r.name_v2,"fishbase_synonym_of_v2_name")]:
    if nm in syn2code.index: return syn2code[nm],how
  return np.nan,"unmatched"
x=wr.apply(fbcode,axis=1,result_type="expand"); wr["fb_speccode"]=x[0]; wr["fb_link_method"]=x[1]
fbi=sp.drop_duplicates("SpecCode").set_index("SpecCode")
wr["fishbase_name"]=wr.fb_speccode.map(fbi.sn)
for c in ["Fresh","Brack","Saltwater"]: wr["fb_"+c.lower()]=wr.fb_speccode.map(fbi[c])
def hab(r):
  if pd.isna(r.fb_saltwater): return "unknown"
  return "marine" if r.fb_saltwater==1 else "brackish" if r.fb_brack==1 else "freshwater" if r.fb_fresh==1 else "unknown"
wr["habitat_salinity"]=wr.apply(hab,axis=1)
wr["habitat_salinity_detail"]=[";".join([k for k,v in [("freshwater",r.fb_fresh),("brackish",r.fb_brack),("marine",r.fb_saltwater)] if v==1]) or "unknown" for r in wr.itertuples()]
wr["freshwater_only"]=(wr.fb_saltwater==0).astype(int)   # reviewer definition: FishBase Saltwater=0 (freshwater and/or brackish, never marine)
wr.to_csv("qc/name_resolution_worms_fishbase.csv",index=False)
NM=wr.set_index("name_v2")
def annotate(d):
  d=d.copy()
  d["species_original"]=d.get("species_original",d.species)
  for c in ["accepted_name","aphia_id","accepted_aphia_id","worms_status","fb_speccode","fishbase_name","habitat_salinity","habitat_salinity_detail","freshwater_only"]:
    d[c]=d.species_original.map(NM[c])
  d["accepted_name"]=d.accepted_name.fillna(d.species_original); d["freshwater_only"]=d.freshwater_only.fillna(0).astype(int); d["habitat_salinity"]=d.habitat_salinity.fillna("unknown")
  d["species"]=d.accepted_name; d["genus"]=d.accepted_name.str.split().str[0]
  d["class_original"]=d.get("class_original",d["class"]); d["class"]=d["class_original"].replace(CLASS_MAP)
  d["basis_of_record"]=bor_norm(d.basis_of_record)
  ix=pd.MultiIndex.from_arrays([d.source,d.record_id.astype(str)]); d["license_norm"]=LN.license_norm.reindex(ix).values; d["license_level"]=LN.license_level.reindex(ix).values
  d["license_norm"]=d.license_norm.fillna("unknown")
  return d
# ---------- merged ----------
m=pd.read_parquet("merged/srilanka_fish_occurrences_clean.parquet"); fun("v2_clean",m)
m=annotate(m)
# family/order: most common value among records of the accepted name (OBIS=WoRMS, GBIF=backbone may differ)
for c in ["family","order"]: m[c]=m.groupby("accepted_name")[c].transform(lambda s:s.mode().iloc[0] if s.notna().any() else np.nan)
m["_k"]=m.accepted_name+"|"+m.lat.round(3).astype(str)+"|"+m.lon.round(3).astype(str)+"|"+m.date
dup=m.sort_values("source",ascending=False).duplicated("_k"); m.sort_values("source",ascending=False)
mm=m.sort_values("source",ascending=False); d=mm[mm.duplicated("_k")]
d.assign(reason="duplicate_after_accepted_name_merge")[["source","record_id","species_original","accepted_name","lat","lon","date","reason"]].to_csv("qc/dropped_duplicates_after_name_merge.csv",index=False)
m=mm.drop_duplicates("_k").drop(columns="_k").sort_index(); fun("after_accepted_name_dedupe",m)
m["chla_filled"]=m.chla_mg_m3.fillna(m.chla_mg_m3_clim)
m["log10_chla_mg_m3"]=np.log10(m.chla_mg_m3); m["log10_chla_mg_m3_clim"]=np.log10(m.chla_mg_m3_clim)
m["chla_lagoon_outlier"]=(m.chla_filled>10).astype(int); m=m.drop(columns="chla_filled")
m["recommended_training_v2"]=m.recommended_training
m["recommended_training"]=((m.obis_on_land_flag==0)&(m.bathy_ge0==0)&(m.freshwater_only==0)).astype(int)
fun("recommended_subset_v3",m[m.recommended_training==1]); fun("freshwater_only_records_in_clean",m[m.freshwater_only==1])
assert m["class"].isin(FISH_CLASSES).all(), m["class"].value_counts()
lead=["source","record_id","scientific_name","species_original","accepted_name","species","genus","family","order","class","class_original"]
m=m[lead+[c for c in m.columns if c not in lead]]
m.to_parquet("merged/srilanka_fish_occurrences_clean.parquet",index=False); m.to_csv("merged/srilanka_fish_occurrences_clean.csv",index=False)
ex=pd.read_csv("merged/srilanka_fish_inland_or_land_excluded.csv",low_memory=False)
ex=annotate(ex); ex.to_csv("merged/srilanka_fish_inland_or_land_excluded.csv",index=False)
# qc logs
for f in ["qc/dropped_missing_coord_date_species.csv","qc/taxonomy_validation_dropped.csv"]:
  q=pd.read_csv(f,low_memory=False)
  if "class_original" not in q: q.insert(q.columns.get_loc("class")+1,"class_original",q["class"])
  q["class"]=q["class_original"].replace(CLASS_MAP); q["basis_of_record"]=bor_norm(q.basis_of_record); q.to_csv(f,index=False)
cs=pd.read_csv("qc/taxonomy_class_summary.csv")
if "class_original" not in cs: cs.insert(1,"class_original",cs["class"])
cs["class"]=cs.class_original.replace(CLASS_MAP)
fin=m.groupby(["source","class_original"]).size().rename("final_clean_rows_v3")
cs=cs.drop(columns=[c for c in ["final_clean_rows_v3"] if c in cs]).merge(fin.reset_index(),on=["source","class_original"],how="left").fillna({"final_clean_rows_v3":0})
cs["is_fish_class"]=cs["class"].isin(FISH_CLASSES); cs.to_csv("qc/taxonomy_class_summary.csv",index=False)
f0=pd.read_csv("qc/build_funnel.csv"); f0["build"]="v2"; f1=pd.DataFrame(FUN); f1["build"]="v3"; pd.concat([f0,f1]).to_csv("qc/build_funnel.csv",index=False)
# ---------- species list ----------
rec=m[m.recommended_training==1]
sl=m.groupby("accepted_name").agg(genus=("genus","first"),family=("family","first"),order=("order","first"),**{"class":("class","first")},fish_group=("fish_group","first"),
   names_merged=("species_original",lambda s:";".join(sorted(set(s)))),record_count=("record_id","size"),n_obis=("source",lambda s:(s=="OBIS").sum()),n_gbif=("source",lambda s:(s=="GBIF").sum()),
   n_citizen_science=("is_citizen_science","sum"),n_specimen=("is_specimen","sum"),first_year=("year","min"),last_year=("year","max"),
   sources=("source",lambda s:";".join(sorted(set(s)))),n_chla_lagoon_outlier=("chla_lagoon_outlier","sum")).reset_index()
sl["record_count_recommended"]=sl.accepted_name.map(rec.accepted_name.value_counts()).fillna(0).astype(int)
sl["model_eligible_10"]=(sl.record_count_recommended>=10).astype(int); sl["model_eligible_20"]=(sl.record_count_recommended>=20).astype(int)
sl["model_tier"]=np.select([sl.record_count_recommended>=20,sl.record_count_recommended>=10],[">=20",">=10"],"<10")
w1=wr.drop_duplicates("accepted_name").set_index("accepted_name")
for c in ["accepted_aphia_id","fb_speccode","fishbase_name","fb_link_method","fb_fresh","fb_brack","fb_saltwater","habitat_salinity","habitat_salinity_detail","freshwater_only"]: sl[c]=sl.accepted_name.map(w1[c])
sl["freshwater_only"]=sl.freshwater_only.fillna(0).astype(int)
sl["common_name"]=sl.fb_speccode.map(fbi.FBname); sl["DemersPelag"]=sl.fb_speccode.map(fbi.DemersPelag)
cty=pd.read_csv("fishbase/fishbase_srilanka_species.csv",low_memory=False).drop_duplicates("SpecCode").set_index("SpecCode")
sl["fishbase_sri_lanka_status"]=sl.fb_speccode.map(cty.Status)
sl=sl.rename(columns={"accepted_name":"scientific_name"}).sort_values("record_count",ascending=False); sl.to_csv("species_list.csv",index=False)
# ---------- train_ready ----------
v2f=pd.read_parquet("train_ready/features.parquet"); SP=v2f.drop_duplicates("spatial_block_1deg").set_index("spatial_block_1deg").split_spatial
t=m.copy()
t["month_sin"]=np.sin(2*np.pi*t.month/12);t["month_cos"]=np.cos(2*np.pi*t.month/12)
t["sst_filled"]=t.sst_c.fillna(t.sst_c_clim); t["log_chla"]=np.log10(t.chla_mg_m3.fillna(t.chla_mg_m3_clim)); t["log_bathy"]=np.log1p(t.bathy_depth_m)
t["label_species"]=t.accepted_name; t["label_id"]=t.label_species.astype("category").cat.codes
t["label_genus"]=t.genus; t["label_family"]=t.family; t["label_order"]=t["order"]
for c in ["PreservedSpecimen","HumanObservation","Occurrence","MaterialSample","MachineObservation","MaterialCitation"]: t["bor_"+c]=(t.basis_of_record==c).astype(int)
t["src_obis"]=(t.source=="OBIS").astype(int)
cell=(np.floor(t.lat)*100+np.floor(t.lon)).astype(int); t["spatial_block_1deg"]=cell
assert cell.isin(SP.index).all(); t["split_spatial"]=cell.map(SP)
t["split_temporal"]=np.where(t.year>=2018,"test",np.where(t.year>=2012,"val","train"))
fc=["record_id","lat","lon","year","month","month_sin","month_cos","bathy_depth_m","log_bathy","sst_filled","log_chla","log10_chla_mg_m3","log10_chla_mg_m3_clim","chla_lagoon_outlier","sst_c_source","chla_mg_m3_source",
    "coord_uncertainty_m","depth_m","depth_missing"]+[c for c in t if c.startswith("bor_")]+["src_obis","license_norm","license_level","obs_type","is_citizen_science","is_specimen","pre_1980",
    "obis_on_land_flag","bathy_ge0","coastal_snap","habitat_salinity","freshwater_only","recommended_training","spatial_block_1deg","label_species","species_original","label_id","label_genus","label_family","label_order","class","class_original","fish_group",
    "split_spatial","split_temporal"]
t[fc].to_parquet("train_ready/features.parquet",index=False)
r=t[t.recommended_training==1].copy(); r["label_id"]=r.label_species.astype("category").cat.codes; r[fc].to_parquet("train_ready/features_recommended.parquet",index=False)
el=set(sl.scientific_name[sl.model_eligible_10==1]); r10=r[r.label_species.isin(el)].copy()
r10["label_id"]=r10.label_species.astype("category").cat.codes; r10[fc].to_parquet("train_ready/features_recommended_min10.parquet",index=False)
bg=pd.read_parquet("train_ready/background_points.parquet")
bg["log10_chla_mg_m3"]=np.log10(bg.chla_mg_m3); bg["log10_chla_mg_m3_clim"]=np.log10(bg.chla_mg_m3_clim)
bg["chla_lagoon_outlier"]=(bg.chla_mg_m3.fillna(bg.chla_mg_m3_clim)>10).astype(int); bg.to_parquet("train_ready/background_points.parquet",index=False)
# ---------- checks ----------
for p,n in [("merged/srilanka_fish_occurrences_clean.parquet",len(m)),("train_ready/features.parquet",len(t)),("train_ready/features_recommended.parquet",len(r)),("train_ready/features_recommended_min10.parquet",len(r10)),("train_ready/background_points.parquet",len(bg))]:
  assert len(pd.read_parquet(p))==n
assert len(pd.read_csv("merged/srilanka_fish_occurrences_clean.csv",low_memory=False))==len(m)
assert sl.record_count.sum()==len(m) and sl.record_count_recommended.sum()==len(r)
assert r.freshwater_only.sum()==0 and t["class"].isin(FISH_CLASSES).all() and r10.label_species.nunique()==len(el)
print("clean",len(m),"species",m.accepted_name.nunique(),"v2 names",m.species_original.nunique(),m["class"].value_counts().to_dict())
print("class_original",m.class_original.value_counts().to_dict())
print("fw_only species",sl.freshwater_only.sum(),"fw records",int(m.freshwater_only.sum()),"habitat",m.habitat_salinity.value_counts().to_dict())
print("recommended",len(r),"min10",len(r10),"species10",len(el),"species20",int(sl.model_eligible_20.sum()))
print("lic",m.license_norm.value_counts().to_dict(),"bor",m.basis_of_record.value_counts().to_dict())
print("lagoon outliers",int(m.chla_lagoon_outlier.sum()),"bg",int(bg.chla_lagoon_outlier.sum()))
print("names changed",(wr.accepted_name!=wr.name_v2).sum(),"fb link",wr.fb_link_method.value_counts().to_dict())
print("splits",t.split_spatial.value_counts().to_dict(),r.split_spatial.value_counts().to_dict())
