import sys,json,subprocess,urllib.parse,pandas as pd
sys.path.insert(0,"scripts");from species_input import R
C=["scientific_name","common_name_en","sinhala_name","tamil_name","group","restriction_type","details","legal_instrument","gazette_number_and_date","source_url","iucn_status","cites_appendix","trawl_bycatch_risk","notes","taxon_rank_level"]
d=pd.DataFrame(R,columns=C)
def worms(n):
  u="https://www.marinespecies.org/rest/AphiaRecordsByName/"+urllib.parse.quote(n)+"?like=false&marine_only=false"
  for _ in range(3):
    r=subprocess.run(["curl","-s","-m","40",u],capture_output=True,text=True).stdout
    if r.strip().startswith("["):
      j=json.loads(r);acc=[x for x in j if x.get("status")=="accepted"] or j
      x=acc[0];return x.get("valid_AphiaID") or x["AphiaID"],x.get("valid_name"),x.get("rank"),x.get("status")
    if r=="" : return None,None,None,"not found"
  return None,None,None,"lookup failed"
W=[worms(n) for n in d.scientific_name];d["worms_aphia_id"]=[w[0] for w in W];d["worms_valid_name"]=[w[1] for w in W];d["worms_rank"]=[w[2] for w in W];d["worms_match_status"]=[w[3] for w in W]
sl=pd.read_csv("/workspace/fish-data/species_list.csv")
fb=pd.read_csv("/workspace/fish-data/merged/srilanka_fish_occurrences_clean.csv",usecols=["species","family"])
spp=set(sl.scientific_name.dropna());fams=set(fb.family.dropna());gen={s.split()[0] for s in spp}
def occ(r):
  for n in {r.scientific_name,r.worms_valid_name or ""}:
    if n in spp: return "yes"
    if " " not in n and (n in gen or n in fams): return "yes (genus/family level)"
  return "no"
d["in_occurrence_dataset"]=d.apply(occ,axis=1)
d["last_verified"]="2026-10-16"
d=d[["scientific_name","worms_valid_name","worms_aphia_id","worms_rank","worms_match_status","common_name_en","sinhala_name","tamil_name","group","restriction_type","details","legal_instrument","gazette_number_and_date","source_url","iucn_status","cites_appendix","trawl_bycatch_risk","in_occurrence_dataset","notes","taxon_rank_level","last_verified"]]
d.to_csv("srilanka_banned_restricted_marine_species.csv",index=False);d.to_parquet("srilanka_banned_restricted_marine_species.parquet",index=False)
print(len(d));print(d.groupby(["group","restriction_type"]).size().to_string());print(d.worms_match_status.value_counts().to_dict());print(d.in_occurrence_dataset.value_counts().to_dict())
print(d[d.worms_match_status!="accepted"][["scientific_name","worms_valid_name","worms_match_status"]].to_string())
