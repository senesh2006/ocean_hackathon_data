"""Morphology / life-history traits for the fish-data-v3 species, from FishBase v24.07 tables
(rOpenSci mirror https://huggingface.co/datasets/cboettig/fishbase/tree/main/data/fb/v24.07/parquet, downloaded 2026-10-17 to /tmp/fbp).
Linkage: fish-data-v3 species_list.fb_speccode (WoRMS accepted name -> FishBase name or FishBase synonym)."""
import pandas as pd,numpy as np,os
os.chdir("/workspace/srilanka-fish-morphology"); P="/tmp/fbp/"
sl=pd.read_csv("/workspace/fish-data-v3/species_list.csv")
base=sl[["scientific_name","fb_speccode","fishbase_name","family","order","class","record_count","model_tier"]].copy()
codes=set(base.fb_speccode.dropna().astype(int)); c2n=base.dropna(subset=["fb_speccode"]).assign(fb_speccode=lambda d:d.fb_speccode.astype(int)).drop_duplicates("fb_speccode").set_index("fb_speccode").scientific_name
def rd(t,sc): d=pd.read_parquet(P+t+".parquet"); d=d.rename(columns={sc:"SpecCode"}); return d[d.SpecCode.isin(codes)].copy()
sp=rd("species","SpecCode")[["SpecCode","BodyShapeI","Length","LTypeMaxM","CommonLength","LTypeComM","Weight","DemersPelag","AnaCat","DepthRangeShallow","DepthRangeDeep","DepthRangeComShallow","DepthRangeComDeep","LongevityWild","Vulnerability","Fresh","Brack","Saltwater","Dangerous","Electrogenic"]]
sp=sp.rename(columns={"BodyShapeI":"body_shape","Length":"max_length_cm","LTypeMaxM":"max_length_type","CommonLength":"common_length_cm","LTypeComM":"common_length_type","Weight":"max_weight_g","DemersPelag":"demers_pelag","AnaCat":"migration_category","LongevityWild":"longevity_wild_y","Vulnerability":"fishing_vulnerability_0_100"})
es=rd("estimate","SpecCode")[["SpecCode","MaxLengthTL","Troph","seTroph","a","b","Method_ab","K","Linf","TempPrefMin","TempPrefMean","TempPrefMax","DepthMin","DepthMax","PredPreyRatioMin","PredPreyRatioMax"]]
es=es.rename(columns={"MaxLengthTL":"est_max_length_TL_cm","Troph":"trophic_level","seTroph":"trophic_level_se","a":"lw_a_bayes","b":"lw_b_bayes","Method_ab":"lw_method","K":"growth_K_per_y","Linf":"growth_Linf_cm","TempPrefMin":"temp_pref_min_c","TempPrefMean":"temp_pref_mean_c","TempPrefMax":"temp_pref_max_c","DepthMin":"est_depth_min_m","DepthMax":"est_depth_max_m"}).drop_duplicates("SpecCode")
md=rd("morphdat","Speccode")
MDC=["BodyShapeII","Forehead","TypeofEyes","TypeofMouth","PosofMouth","TypeofScales","CShape","DorsalSpinesMin","DorsalSpinesMax","DorsalSoftRaysMin","DorsalSoftRaysMax","AnalFinSpinesMin","AnalFinSpinesMax","Araymin","Araymax","VertebraeTotalMin","VertebraeTotalMax","GillRakersTotalMin","GillRakersTotalMax","ScalesLateralmin","ScalesLateralmax","BarbelsNo","GasBladder"]
mdf=md.groupby("SpecCode")[MDC].first().reset_index(); mdf.columns=["SpecCode"]+["md_"+c for c in MDC]
mm=rd("morphmet","Speccode"); mm=mm[mm.Doubtful.fillna(0).astype(str).isin(["0","False","false","0.0"])] if "Doubtful" in mm else mm
for a,bb,n in [("BD","TL","body_depth_over_TL"),("HL","TL","head_length_over_TL"),("ED","HL","eye_diam_over_HL"),("PDL","TL","predorsal_over_TL"),("CH","TL","caudal_height_over_TL"),("BD","SL","body_depth_over_SL")]:
  mm[n]=pd.to_numeric(mm[a],errors="coerce")/pd.to_numeric(mm[bb],errors="coerce").replace(0,np.nan)
mmf=mm.groupby("SpecCode").agg(morphmet_n_pictures=("PicName","size"),body_depth_over_TL=("body_depth_over_TL","median"),body_depth_over_SL=("body_depth_over_SL","median"),head_length_over_TL=("head_length_over_TL","median"),
  eye_diam_over_HL=("eye_diam_over_HL","median"),predorsal_over_TL=("predorsal_over_TL","median"),caudal_height_over_TL=("caudal_height_over_TL","median"),caudal_aspect_ratio_morphmet=("AspectRatio","median")).reset_index()
sw=rd("swimming","SpecCode")[["SpecCode","AdultType","AdultMode","AspectRatio"]].drop_duplicates("SpecCode").rename(columns={"AdultType":"swim_type","AdultMode":"swim_mode","AspectRatio":"caudal_aspect_ratio"})
ec=rd("ecology","SpecCode"); ECC=["FeedingType","Schooling","Shoaling","Solitary","Benthic","Pelagic","Demersal","CoralReefs","SeaGrassBeds","Mangroves","Estuaries","Lagoons","Rocky","SoftBottom","Sand","Mud","Oceanic","Neritic","Epipelagic","Mesopelagic","Bathypelagic","Seamounts"]
ecf=ec.groupby("SpecCode")[ECC].first().reset_index(); ecf.columns=["SpecCode"]+["eco_"+c for c in ECC]
mat=rd("maturity","Speccode"); matf=mat.groupby("SpecCode").agg(length_at_maturity_Lm_cm_median=("Lm","median"),age_at_maturity_tm_y_median=("tm","median"),maturity_n_studies=("Lm","size")).reset_index()
pc=rd("popchar","Speccode"); pcf=pc.groupby("SpecCode").agg(popchar_Lmax_cm_max=("Lmax","max"),popchar_Wmax_g_max=("Wmax","max"),popchar_tmax_y_max=("tmax","max"),popchar_n=("Lmax","size")).reset_index()
lw=rd("poplw","SpecCode"); lwf=lw.groupby("SpecCode").agg(poplw_a_median=("a","median"),poplw_b_median=("b","median"),poplw_n_studies=("a","size"),poplw_n_sri_lanka=("C_Code",lambda s:(s.astype(str).str.strip()=="144").sum())).reset_index()
t=base.copy(); t["SpecCode"]=t.fb_speccode
for d in [sp,es,mdf,mmf,sw,ecf,matf,pcf,lwf]: t=t.merge(d,on="SpecCode",how="left")
t=t.drop(columns="SpecCode")
t["fishbase_url"]=np.where(t.fb_speccode.notna(),"https://www.fishbase.se/summary/"+t.fb_speccode.fillna(0).astype(int).astype(str),None)
t["source"]="FishBase v24.07 (species, estimate, morphdat, morphmet, swimming, ecology, maturity, popchar, poplw) via rOpenSci HF mirror"
t["license"]="CC BY-NC 4.0 (FishBase); cite Froese & Pauly (eds) FishBase www.fishbase.org, version 2024"
t.to_csv("srilanka_fish_species_traits.csv",index=False); t.to_parquet("srilanka_fish_species_traits.parquet",index=False)
# per-population / per-specimen tables
def out(d,name,sc="SpecCode"):
  d=d.copy(); d.insert(0,"scientific_name",d[sc].map(c2n))
  if "C_Code" in d: d["is_sri_lanka_population"]=(d.C_Code.astype(str).str.strip()=="144").astype(int)
  d.to_csv(f"population_tables/{name}.csv",index=False); return len(d)
n={}
n["poplw"]=out(lw,"poplw_length_weight_by_population"); n["popll"]=out(rd("popll","SpecCode"),"popll_length_length_conversions")
n["popchar"]=out(pc,"popchar_max_length_weight_age_by_population"); n["maturity"]=out(mat,"maturity_by_population")
n["fecundity"]=out(rd("fecundity","SpecCode"),"fecundity_by_population")
n["morphdat"]=out(md,"morphdat_meristics_morphology"); n["morphmet"]=out(mm,"morphmet_morphometrics_by_picture")
assert len(t)==len(sl)
cov={"species_v3":len(t),"fishbase_linked":int(t.fb_speccode.notna().sum()),"max_length":int(t.max_length_cm.notna().sum()),"body_shape":int(t.body_shape.notna().sum()),
 "trophic_level":int(t.trophic_level.notna().sum()),"lw_bayes_ab":int(t.lw_a_bayes.notna().sum()),"morphdat":int(t[[c for c in t if c.startswith("md_")]].notna().any(axis=1).sum()),
 "morphmet_ratios":int(t.body_depth_over_TL.notna().sum()),"swimming":int(t.swim_mode.notna().sum()),"ecology":int(t[[c for c in t if c.startswith("eco_")]].notna().any(axis=1).sum()),
 "maturity_Lm":int(t.length_at_maturity_Lm_cm_median.notna().sum()),"poplw":int(t.poplw_n_studies.notna().sum()),"poplw_sri_lanka":int((t.poplw_n_sri_lanka>0).sum()),"temp_pref":int(t.temp_pref_mean_c.notna().sum())}
pd.Series(cov).rename("species_with_data").to_csv("coverage_stats.csv"); print(cov); print(n)
