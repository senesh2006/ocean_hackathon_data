import pandas as pd,os,glob
D="2026-10-16"
def info(p):
  d=pd.read_parquet(p) if p.endswith("parquet") else pd.read_csv(p,low_memory=False,skiprows=[1] if p.startswith("env/") else None)
  sp="";dr=""
  for c in ["species","label_species","scientific_name","scientificName","SPECIES_SCIENTIFIC"]:
    if c in d: sp=d[c].nunique();break
  for c in ["date","date_year","eventDate","time","YEAR","year"]:
    if c in d:
      v=d[c].dropna().astype(str); 
      if len(v): dr=f"{v.min()[:10]} to {v.max()[:10]}";break
  return len(d),sp,dr
EZ="Sri Lanka waters box lat 4-11N, lon 77-85E"
meta={
"obis/obis_srilanka_fish.csv":("OBIS fish occurrences (raw)","OBIS API v3 https://obis.org (api.obis.org/v3/occurrence, taxonid 10194 Actinopteri)","Per-dataset CC0/CC-BY/CC-BY-NC (see license column); cite OBIS + datasets",EZ,"OBIS QC pipeline flags (flags column: on_land, no_depth, depth_exceeds_bath, etc.); WoRMS-matched taxonomy"),
"obis/obis_srilanka_fish_checklist.csv":("OBIS species checklist","https://obis.org api.obis.org/v3/checklist","CC-BY (OBIS)",EZ,"WoRMS-validated names"),
"gbif/gbif_srilanka_fish.csv":("GBIF ray-finned fish occurrences (raw)","GBIF API https://api.gbif.org/v1/occurrence/search (classKey 11592253 Actinopterygii, hasGeospatialIssue=false)","Per-record CC0/CC-BY/CC-BY-NC (license column); cite GBIF.org download",EZ,"Excludes GBIF geospatial-issue records; GBIF backbone taxonomy; issues column lists remaining interpretation flags"),
"fishbase/fishbase_srilanka_species.csv":("FishBase Sri Lanka country checklist (C_Code 144)","FishBase https://www.fishbase.se via rOpenSci mirror https://huggingface.co/datasets/cboettig/fishbase (v24.07)","CC-BY-NC 4.0 (FishBase)","Sri Lanka (country)","Expert-curated checklist; Status = native/introduced/etc."),
"iotc/iotc_retained_catch_srilanka_1950_2025.csv":("IOTC retained nominal catch, Sri Lanka fleet","https://iotc.org/data/datasets/latest/NC/ALL","Public domain, source acknowledgement required (IOTC)","IOTC statistical areas, Sri Lanka fleet","Officially reported by Sri Lanka, curated/consolidated by IOTC Secretariat (raw estimates, metric tonnes)"),
"env/sst_monthly.csv":("NOAA Coral Reef Watch monthly SST v3.1 (0.25 deg subsample)","https://oceanwatch.pifsc.noaa.gov/erddap/griddap/CRW_sst_v3_1_monthly.html","Public domain (NOAA)",EZ,"NOAA operational blended satellite product"),
"env/chla_monthly.csv":("ESA OC-CCI v6.0 monthly chlorophyll-a (0.25 deg subsample)","https://oceanwatch.pifsc.noaa.gov/erddap/griddap/esa-cci-chla-monthly-v6-0.html","CC-BY 4.0 (ESA CCI)",EZ,"Multi-sensor merged, bias-corrected; per-pixel uncertainty available upstream"),
"env/bathy_etopo2022.csv":("NOAA ETOPO 2022 bathymetry (0.05 deg subsample)","https://oceanwatch.pifsc.noaa.gov/erddap/griddap/ETOPO_2022_v1_60s.html","Public domain (NOAA NCEI)",EZ,"NCEI quality-controlled global relief model"),
"merged/srilanka_fish_occurrences_clean.parquet":("Merged clean marine occurrences + covariates (primary)","Derived (scripts/build.py)","Inherits record licenses (license column)",EZ,"Dropped no date/coords/species, out-of-box, bad-coord GBIF issues, >~5 km inland; deduped species+lat/lon(3dp)+date; matched SST/chl (month) & depth"),
"merged/srilanka_fish_occurrences_clean.csv":("Same as parquet (CSV copy)","Derived","Inherits",EZ,"As above"),
"merged/srilanka_fish_inland_or_land_excluded.csv":("Records excluded as inland/on-land (freshwater & land-located)","Derived","Inherits",EZ,"Kept for reference; not in training set"),
"train_ready/features.parquet":("ML feature table","Derived","Inherits",EZ,"Numeric/encoded features, label, spatial (1deg block) and temporal splits"),
"species_list.csv":("Species list (clean set)","Derived + FishBase names","Inherits",EZ,"Names from OBIS/GBIF; common names from FishBase"),
}
rows=[]
for p,(n,s,l,e,q) in meta.items():
  r,sp,dr=info(p);rows.append(dict(file_path=p,dataset_name=n,source_url=s,license_citation=l,date_range=dr,spatial_extent=e,row_count=r,species_count=sp,column_dictionary="data_dictionary.csv" if p.startswith(("merged","train")) else "README.md",qc_validation=q,download_date=D))
c=pd.DataFrame(rows);c.to_csv("catalog.csv",index=False)
open("catalog.md","w").write("# Data catalog\n\n"+c.to_markdown(index=False) if hasattr(c,"to_markdown") else "")
desc={"source":"OBIS or GBIF","record_id":"Source record id","scientific_name":"Name as published","species":"Accepted species","family":"Family","lat":"Latitude WGS84","lon":"Longitude WGS84","coord_uncertainty_m":"Coordinate uncertainty (m), GBIF only","depth_m":"Recorded sample depth (m)","basis_of_record":"Observation type","dataset":"Source dataset","license":"Record license","qc_flags":"OBIS flags / GBIF issues","date":"Event date YYYY-MM-DD","year":"Year","month":"Month","bathy_depth_m":"Seafloor depth from ETOPO2022 (m, 0 if coastal snap)","coastal_snap":"1 = record on coastline land cell within ~5 km of water","sst_c":"Monthly SST at record month/cell (C), NaN before 2003 (download window)","sst_c_clim":"Monthly SST climatology for cell (C)","chla_mg_m3":"Monthly chl-a at record month/cell (mg m-3), NaN before 2003 (download window)","chla_mg_m3_clim":"Monthly chl-a climatology for cell","month_sin":"sin(2pi month/12)","month_cos":"cos(2pi month/12)","log_bathy":"log1p(bathy_depth_m)","sst_filled":"sst_c else climatology","log_chla":"log10(chl-a, climatology filled)","src_obis":"1 if OBIS","spatial_block_1deg":"1-degree cell id floor(lat)*100+floor(lon)","label_species":"Species label","label_id":"Integer-encoded species","split_spatial":"train/val/test by 1-degree block (seed 42)","split_temporal":"train<2012, val 2012-2017, test>=2018"}
cols=list(pd.read_parquet("merged/srilanka_fish_occurrences_clean.parquet").columns)+list(pd.read_parquet("train_ready/features.parquet").columns)
dd=[];seen=set()
for x in cols:
  if x in seen: continue
  seen.add(x);dd.append(dict(column=x,description=desc.get(x,"One-hot basis_of_record" if x.startswith("bor_") else ""),in_merged=x in cols[:len(pd.read_parquet("merged/srilanka_fish_occurrences_clean.parquet").columns)]))
pd.DataFrame(dd).to_csv("data_dictionary.csv",index=False)
print(c[["file_path","row_count","species_count","date_range"]].to_string())
