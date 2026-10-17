import pandas as pd,os
D="2026-10-17"; EZ="Sri Lanka waters box lat 4-11N, lon 77-85E"
c=pd.read_csv("catalog.csv"); c=c[~c.file_path.str.startswith(("qc/name_resolution","qc/_worms","qc/obis_dataset","qc/dropped_duplicates"))].copy(); c["qc_validation"]=c.qc_validation.str.split(r" \| v3:").str[0]  # idempotent
def info(p):
  d=pd.read_parquet(p) if p.endswith("parquet") else pd.read_csv(p,low_memory=False,skiprows=[1] if p.startswith("env/") and "climatology" not in p else None)
  sp=""
  for k in ["accepted_name","label_species","scientific_name","species","scientificName","name_v2"]:
    if k in d: sp=d[k].nunique();break
  return len(d),sp
upd={"obis/obis_srilanka_fish.csv":"v3: + basis_of_record_norm, license_norm, license_level (record or OBIS dataset-level intellectualrights), class_original; class Teleostei->Actinopterygii",
 "gbif/gbif_srilanka_fish.csv":"v3: + basis_of_record_norm, license_norm, license_level, class_validated_original; class harmonised",
 "merged/srilanka_fish_occurrences_clean.parquet":"v3: WoRMS accepted_name (species_original kept), records re-deduplicated after name merge (62 dropped), class harmonised (class_original kept), habitat_salinity/freshwater_only from FishBase, license_norm, log10 chl-a, chla_lagoon_outlier; recommended_training now also excludes freshwater_only",
 "merged/srilanka_fish_occurrences_clean.csv":"v3: CSV copy of the parquet","merged/srilanka_fish_inland_or_land_excluded.csv":"v3: same annotation columns as the clean set",
 "train_ready/features.parquet":"v3: label_species = WoRMS accepted name; + log10_chla_mg_m3(_clim), chla_lagoon_outlier, habitat_salinity, freshwater_only, license_norm/level, class_original",
 "train_ready/features_recommended.parquet":"v3: excludes ON_LAND, bathy>=0 AND freshwater_only species; label_id re-encoded","train_ready/features_recommended_min10.parquet":"v3: species with >=10 v3-recommended records",
 "train_ready/background_points.parquet":"v3: + log10_chla_mg_m3(_clim), chla_lagoon_outlier (points unchanged)","species_list.csv":"v3: one row per WoRMS accepted name; names_merged, AphiaID, FishBase SpecCode + link method, habitat_salinity, freshwater_only; counts/tiers rebuilt",
 "qc/taxonomy_class_summary.csv":"v3: class harmonised + class_original + final_clean_rows_v3","qc/taxonomy_validation_dropped.csv":"v3: + class_original","qc/dropped_missing_coord_date_species.csv":"v3: class harmonised + class_original, basis_of_record normalised","qc/build_funnel.csv":"v3: v2 and v3 steps"}
c["qc_validation"]=[(q+" | "+upd[p]) if p in upd else q for p,q in zip(c.file_path,c.qc_validation)]
new=[("qc/name_resolution_worms_fishbase.csv","Name resolution: every v2 species name -> WoRMS accepted name + AphiaID + FishBase SpecCode + habitat_salinity","WoRMS REST AphiaRecordsByMatchNames https://www.marinespecies.org/rest/ (2026-10-17); FishBase v24.07 species+synonyms https://huggingface.co/datasets/cboettig/fishbase","WoRMS CC-BY 4.0; FishBase CC-BY-NC 4.0","Sri Lanka species list","Exact WoRMS matches 1465/1469; 74 names changed; FishBase linked 1461/1469"),
 ("qc/_worms_match_raw.json","Raw WoRMS AphiaRecordsByMatchNames responses (reproducibility)","https://www.marinespecies.org/rest/AphiaRecordsByMatchNames","CC-BY 4.0 (WoRMS)","n/a","Raw API output"),
 ("qc/obis_dataset_licenses.csv","OBIS dataset-level licence (intellectualrights) for datasets whose records lack a record licence","https://api.obis.org/v3/dataset/{id} (2026-10-17)","CC-BY (OBIS metadata)","n/a","Used for license_norm where license_level=dataset"),
 ("qc/dropped_duplicates_after_name_merge.csv","Records dropped as duplicates after merging synonyms (same accepted name, lat/lon 3dp, date)","Derived","Inherits","n/a","62 rows; GBIF copy dropped when OBIS has the same record")]
rows=[]
for p,n,s,l,e,q in new:
  r,sp=info(p); rows.append(dict(file_path=p,dataset_name=n,source_url=s,license_citation=l,date_range="",spatial_extent=e,row_count=r,species_count=sp,column_dictionary="README.md",qc_validation=q,download_date=D))
c=pd.concat([c,pd.DataFrame(rows)],ignore_index=True)
for i,p in enumerate(c.file_path):
  if p.endswith((".csv",".parquet")): c.loc[i,"row_count"],c.loc[i,"species_count"]=info(p)
c["download_date"]=c.download_date.fillna(D); c.to_csv("catalog.csv",index=False)
open("catalog.md","w").write("# Data catalog (fish-data v3)\n\nOne row per file. Licences: see license_citation and, for occurrence records, the per-record `license_norm` column.\n\n"+c.to_markdown(index=False)+"\n")
dd=pd.read_csv("data_dictionary.csv")
dd.loc[dd.column=="class","description"]="Class, harmonised: Actinopterygii (incl. WoRMS Teleostei), Elasmobranchii, Holocephali, Myxini. Original value in class_original"
dd.loc[dd.column=="species","description"]="v3: WoRMS accepted species name (same as accepted_name)"
dd.loc[dd.column=="label_species","description"]="Species label = WoRMS accepted name"
dd.loc[dd.column=="recommended_training","description"]="v3: 1 if obis_on_land_flag==0 and bathy_ge0==0 and freshwater_only==0"
dd.loc[dd.column=="basis_of_record","description"]="Darwin Core basisOfRecord, canonical CamelCase (PreservedSpecimen, HumanObservation, ...)"
add={"species_original":("merged/train_ready","Species name as in v2 (OBIS/GBIF name before WoRMS resolution)"),"accepted_name":("merged/species_list","WoRMS accepted (valid) name; synonyms merged"),
"class_original":("merged/train_ready/qc","Class before harmonisation (Teleostei = WoRMS/OBIS, Actinopterygii = GBIF)"),"aphia_id":("merged","WoRMS AphiaID of the matched name"),"accepted_aphia_id":("merged/species_list","WoRMS AphiaID of the accepted name"),
"worms_status":("merged","WoRMS status of the original name (accepted, superseded combination, unaccepted, ...)"),"fb_speccode":("merged/species_list","FishBase SpecCode"),"fishbase_name":("merged/species_list","FishBase valid name (may differ from WoRMS)"),
"fb_link_method":("species_list","accepted_name / v2_name / fishbase_synonym_of_accepted / unmatched"),"habitat_salinity":("merged/train_ready/species_list","marine if FishBase Saltwater=1; brackish if Saltwater=0 & Brack=1; freshwater if only Fresh=1; unknown if no FishBase link"),
"habitat_salinity_detail":("merged/species_list","All FishBase salinity flags set, e.g. freshwater;brackish;marine"),"freshwater_only":("merged/train_ready/species_list","1 if FishBase Saltwater=0 (freshwater and/or brackish, never marine). Excluded from recommended sets"),
"license_norm":("merged/train_ready/raw","Canonical licence: CC0-1.0, CC-BY-4.0, CC-BY-NC-4.0, unknown"),"license_level":("merged/train_ready/raw","record = record licence field; dataset = OBIS dataset intellectualrights; unknown"),
"basis_of_record_norm":("raw obis/gbif","Canonical basisOfRecord"),"log10_chla_mg_m3":("merged/train_ready/background","log10 of month-matched chl-a (NaN if not month-matched)"),"log10_chla_mg_m3_clim":("merged/train_ready/background","log10 of chl-a climatology"),
"chla_lagoon_outlier":("merged/train_ready/background","1 if chl-a (month or climatology fill) > 10 mg m-3 (lagoon/estuary/turbid coastal pixel; OC-CCI unreliable there)"),"recommended_training_v2":("merged","v2 definition (without freshwater exclusion), for comparison"),
"names_merged":("species_list","All v2 names merged into this accepted name"),"fb_fresh":("species_list","FishBase Fresh flag"),"fb_brack":("species_list","FishBase Brack flag"),"fb_saltwater":("species_list","FishBase Saltwater flag"),"n_chla_lagoon_outlier":("species_list","Records with chla_lagoon_outlier=1")}
dd=pd.concat([dd[~dd.column.isin(add)],pd.DataFrame([dict(column=k,description=v[1],in_merged=True,file=v[0]) for k,v in add.items()])])
dd.to_csv("data_dictionary.csv",index=False)
cols=set(pd.read_parquet("merged/srilanka_fish_occurrences_clean.parquet").columns)|set(pd.read_parquet("train_ready/features.parquet").columns)|set(pd.read_csv("species_list.csv").columns)
print("undocumented:",sorted(cols-set(dd.column)))
