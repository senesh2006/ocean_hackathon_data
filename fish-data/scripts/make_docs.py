import pandas as pd,os,glob
D="2026-10-17"
def info(p):
  d=pd.read_parquet(p) if p.endswith("parquet") else pd.read_csv(p,low_memory=False,skiprows=[1] if p.startswith("env/") and "climatology" not in p else None)
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
"obis/obis_srilanka_fish.csv":("OBIS fish occurrences (raw, v2: + class/order columns, + Elasmobranchii/Holocephali/Myxini)","OBIS API v3 https://obis.org (api.obis.org/v3/occurrence; taxonid 10194 Actinopterygii [v1 pull 2026-10-16], 10193 Elasmobranchii, 10196 Holocephali, 10189 Myxini [2026-10-17])","Per-dataset CC0/CC-BY/CC-BY-NC (see license column); cite OBIS + datasets",EZ,"OBIS QC flags; class from WoRMS (AphiaRecordsByAphiaIDs) for all names; hard fish-class check in build.py"),
"obis/obis_srilanka_fish_checklist.csv":("OBIS species checklist","https://obis.org api.obis.org/v3/checklist","CC-BY (OBIS)",EZ,"WoRMS-validated names"),
"gbif/gbif_srilanka_fish.csv":("GBIF fish occurrences (raw, v2 corrected; v1 was Squamata/reptiles)","GBIF API https://api.gbif.org/v1/occurrence/search, hasGeospatialIssue=false, hasCoordinate=true; one query per ray-finned fish orderKey (GBIF backbone leaves class empty for these, so classKey 204 returns 0) + classKey 121 Elasmobranchii; see qc/gbif_query_scope_by_order.csv","Per-record CC0/CC-BY/CC-BY-NC (license column); cite GBIF.org download",EZ,"Excludes geospatial-issue records; class_validated = backbone class, or Actinopterygii when order is a known ray-finned order; hard fish-class check in build.py"),
"fishbase/fishbase_srilanka_species.csv":("FishBase Sri Lanka country checklist (C_Code 144)","FishBase https://www.fishbase.se via rOpenSci mirror https://huggingface.co/datasets/cboettig/fishbase (v24.07)","CC-BY-NC 4.0 (FishBase)","Sri Lanka (country)","Expert-curated checklist; Status = native/introduced/etc."),
"iotc/iotc_retained_catch_srilanka_1950_2025.csv":("IOTC retained nominal catch, Sri Lanka fleet","https://iotc.org/data/datasets/latest/NC/ALL","Public domain, source acknowledgement required (IOTC)","IOTC statistical areas, Sri Lanka fleet","Officially reported by Sri Lanka, curated/consolidated by IOTC Secretariat (raw estimates, metric tonnes)"),
"env/sst_monthly.csv":("NOAA Coral Reef Watch monthly SST v3.1 (0.25 deg subsample)","https://oceanwatch.pifsc.noaa.gov/erddap/griddap/CRW_sst_v3_1_monthly.html","Public domain (NOAA)",EZ,"NOAA operational blended satellite product"),
"env/chla_monthly.csv":("ESA OC-CCI v6.0 monthly chlorophyll-a (0.25 deg subsample)","https://oceanwatch.pifsc.noaa.gov/erddap/griddap/esa-cci-chla-monthly-v6-0.html","CC-BY 4.0 (ESA CCI)",EZ,"Multi-sensor merged, bias-corrected; per-pixel uncertainty available upstream"),
"env/bathy_etopo2022.csv":("NOAA ETOPO 2022 bathymetry (0.05 deg subsample)","https://oceanwatch.pifsc.noaa.gov/erddap/griddap/ETOPO_2022_v1_60s.html","Public domain (NOAA NCEI)",EZ,"NCEI quality-controlled global relief model"),
"env/sst_monthly_climatology_2003_2026.csv":("SST monthly climatology (calendar month mean/std, 2003-2026) 0.25 deg","Derived from env/sst_monthly.csv","Public domain (NOAA)",EZ,"For matching pre-2003 records / fish-factors 24-month gap"),
"env/chla_monthly_climatology_2003_2026.csv":("Chl-a monthly climatology (calendar month mean/std, 2003-2026) 0.25 deg","Derived from env/chla_monthly.csv","CC-BY 4.0 (ESA CCI)",EZ,"For matching pre-2003 records / fish-factors 24-month gap"),
"merged/srilanka_fish_occurrences_clean.parquet":("Merged clean marine FISH occurrences + covariates + bias flags (primary, full set)","Derived (scripts/build.py)","Inherits record licenses (license column)",EZ,"Dropped no date/coords/species, out-of-box, bad-coord GBIF issues, >~5 km inland; deduped species+lat/lon(3dp)+date; matched SST/chl (month) & depth"),
"merged/srilanka_fish_occurrences_clean.csv":("Same as parquet (CSV copy)","Derived","Inherits",EZ,"As above"),
"merged/srilanka_fish_inland_or_land_excluded.csv":("Records excluded as inland/on-land (freshwater & land-located)","Derived","Inherits",EZ,"Kept for reference; not in training set"),
"train_ready/features.parquet":("ML feature table, full clean set","Derived","Inherits",EZ,"Features, species/genus/family/order labels, bias flags, env source, spatial+temporal splits"),
"train_ready/features_recommended.parquet":("ML feature table, recommended subset","Derived","Inherits",EZ,"Excludes OBIS ON_LAND-flagged and ETOPO bathy>=0 (coast-snapped) records"),
"train_ready/features_recommended_min10.parquet":("ML feature table, recommended subset, species with >=10 recommended records","Derived","Inherits",EZ,"label_id re-encoded within this subset"),
"train_ready/background_points.parquet":("Pseudo-absence / background points (in-water only)","Derived (ETOPO water cells, env/)","CC-BY / public (env sources)",EZ,"10k uniform in-water + 10k target-group (jittered presence locations, in-water); dates drawn from presence year-month distribution; SST/chl matched like presences"),
"qc/taxonomy_class_summary.csv":("Class counts raw vs final per source","Derived","n/a",EZ,"Proves 0 non-fish classes"),
"qc/taxonomy_validation_dropped.csv":("Rows dropped by the hard fish-class / fossil check","Derived","n/a",EZ,"0 rows in this build (non-fish excluded at query level, see gbif_query_scope_by_order.csv)"),
"qc/dropped_missing_coord_date_species.csv":("Rows dropped for missing coordinates/date/species","Derived","Inherits",EZ,"Audit log"),
"qc/build_funnel.csv":("Row counts after each build step, by source","Derived","n/a",EZ,"Audit"),
"qc/gbif_query_scope_by_order.csv":("GBIF chordate orders in box, backbone class, downloaded yes/no","GBIF API facets","n/a",EZ,"Documents which orders were pulled as fish"),
"species_list.csv":("Species list (clean set) with counts and model-eligibility tiers","Derived + FishBase names","Inherits",EZ,"record_count (full), record_count_recommended, model_eligible_10/_20, model_tier; FishBase common name/status"),
}
rows=[]
for p,(n,s,l,e,q) in meta.items():
  r,sp,dr=info(p);rows.append(dict(file_path=p,dataset_name=n,source_url=s,license_citation=l,date_range=dr,spatial_extent=e,row_count=r,species_count=sp,column_dictionary="data_dictionary.csv" if p.startswith(("merged","train")) else "README.md",qc_validation=q,download_date=D))
c=pd.DataFrame(rows);c.to_csv("catalog.csv",index=False)
open("catalog.md","w").write("# Data catalog\n\n"+c.to_markdown(index=False) if hasattr(c,"to_markdown") else "")
desc={"source":"OBIS or GBIF","record_id":"Source record id","scientific_name":"Name as published","species":"Accepted species","family":"Family","lat":"Latitude WGS84","lon":"Longitude WGS84","coord_uncertainty_m":"Coordinate uncertainty (m), GBIF only","depth_m":"Recorded sample depth (m)","basis_of_record":"Observation type","dataset":"Source dataset","license":"Record license","qc_flags":"OBIS flags / GBIF issues","date":"Event date YYYY-MM-DD","year":"Year","month":"Month","bathy_depth_m":"Seafloor depth from ETOPO2022 (m, positive down, 0 if coastal snap)","coastal_snap":"1 = record on coastline land cell within ~5 km of water","sst_c":"Monthly SST at record month/cell (C), NaN before 2003 (download window)","sst_c_clim":"Monthly SST climatology 2003-2026 for cell (C); nearest cell within 0.5 deg if record cell is NaN","chla_mg_m3":"Monthly chl-a at record month/cell (mg m-3), NaN before 2003 (download window)","chla_mg_m3_clim":"Monthly chl-a climatology 2003-2026 for cell; nearest cell within 0.5 deg if record cell is NaN","month_sin":"sin(2pi month/12)","month_cos":"cos(2pi month/12)","log_bathy":"log1p(bathy_depth_m)","sst_filled":"sst_c else climatology","log_chla":"log10(chl-a, climatology filled)","src_obis":"1 if OBIS","genus":"Genus","order":"Order (WoRMS for OBIS, GBIF backbone for GBIF; can differ, e.g. Carangiformes vs Perciformes)","class":"Class: Teleostei (WoRMS/OBIS) and Actinopterygii (GBIF) are both ray-finned fish; Elasmobranchii, Holocephali, Myxini","fish_group":"Harmonised group: ray_finned / shark_ray / chimaera / hagfish","obs_type":"citizen_science (iNaturalist etc. by dataset name) / specimen (PreservedSpecimen, MaterialSample) / other_human_observation / machine_observation / other_or_unknown","is_citizen_science":"1 if obs_type citizen_science","is_specimen":"1 if obs_type specimen","pre_1980":"1 if year < 1980","obis_on_land_flag":"1 if OBIS QC flagged ON_LAND","depth_missing":"1 if no recorded sample depth (depth_m)","etopo_z_m":"Raw ETOPO2022 elevation at record cell (m, negative = sea)","bathy_ge0":"1 if ETOPO cell is land/0 m (record snapped from coast)","sst_c_source":"month_matched / climatology / climatology_nearest_cell / missing","chla_mg_m3_source":"month_matched / climatology / climatology_nearest_cell / missing","recommended_training":"1 if obis_on_land_flag==0 and bathy_ge0==0","label_genus":"Genus label (coarser)","label_family":"Family label (coarser)","label_order":"Order label (coarser)","bor_MaterialCitation":"One-hot basis_of_record","spatial_block_1deg":"1-degree cell id floor(lat)*100+floor(lon)","label_species":"Species label","label_id":"Integer-encoded species","split_spatial":"train/val/test by 1-degree block (seed 42)","split_temporal":"train<2012, val 2012-2017, test>=2018"}
cols=list(pd.read_parquet("merged/srilanka_fish_occurrences_clean.parquet").columns)+list(pd.read_parquet("train_ready/features.parquet").columns)
dd=[];seen=set()
for x in cols:
  if x in seen: continue
  seen.add(x);dd.append(dict(column=x,description=desc.get(x,"One-hot basis_of_record" if x.startswith("bor_") else ""),in_merged=x in cols[:len(pd.read_parquet("merged/srilanka_fish_occurrences_clean.parquet").columns)]))
pd.DataFrame(dd).to_csv("data_dictionary.csv",index=False)
print(c[["file_path","row_count","species_count","date_range"]].to_string())
# v2: background points + species_list columns
extra={"bg_id":("background_points","Background point id"),"bg_type":("background_points","uniform_water = uniform over ETOPO water cells; target_group = presence locations jittered <=0.1 deg, kept if in water (same sampling bias as presences)"),
"presence":("background_points","0 = background / pseudo-absence"),
"record_count":("species_list","Records in full clean set"),"record_count_recommended":("species_list","Records in recommended subset"),"n_obis":("species_list","Records from OBIS"),"n_gbif":("species_list","Records from GBIF"),
"n_citizen_science":("species_list","Citizen-science records"),"n_specimen":("species_list","Specimen records"),"first_year":("species_list","Earliest record year"),"last_year":("species_list","Latest record year"),
"model_eligible_10":("species_list","1 if record_count_recommended >= 10"),"model_eligible_20":("species_list","1 if record_count_recommended >= 20"),"model_tier":("species_list",">=20 / >=10 / <10 (recommended-subset counts)"),
"common_name":("species_list","FishBase common name"),"fishbase_sri_lanka_status":("species_list","FishBase country Status"),"DemersPelag":("species_list","FishBase habitat type"),"sources":("species_list","Sources with records")}
dd=pd.read_csv("data_dictionary.csv"); dd["file"]="merged/train_ready"
add=pd.DataFrame([dict(column=k,description=v[1],in_merged=False,file=v[0]) for k,v in extra.items() if k not in set(dd.column)])
pd.concat([dd,add]).to_csv("data_dictionary.csv",index=False)
