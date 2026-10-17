"""Sri Lanka fish DNA barcodes. Inputs:
 - BOLD Systems Data Portal API (portal.boldsystems.org/api, 2026-10-17): query geo:country/ocean:Sri Lanka;tax:class:Teleostei and ;tax:class:Elasmobranchii (v4 API_Public was offline: 'BOLD Public Offline'; class:Actinopterygii/Actinopteri return 0 in portal taxonomy)
 - NCBI nuccore via E-utilities (esearch+efetch gb, 2026-10-17): (Actinopterygii[Organism] OR Chondrichthyes[Organism]) AND "Sri Lanka"[All Fields]; GenBank flatfiles cached /tmp/ncbi/*.gb
Names mapped to fish-data-v3 accepted names (qc/name_resolution_worms_fishbase.csv)."""
import pandas as pd,numpy as np,glob,re,os
from Bio import SeqIO
os.chdir("/workspace/srilanka-fish-genetics")
V3="/workspace/fish-data-v3/"
sl=pd.read_csv(V3+"species_list.csv"); nr=pd.read_csv(V3+"qc/name_resolution_worms_fishbase.csv")
syn=pd.read_parquet("/tmp/fbp/synonyms.parquet",columns=["SynGenus","SynSpecies","SpecCode"]); syn["sn"]=syn.SynGenus.str.strip()+" "+syn.SynSpecies.str.strip()
code2acc=sl.dropna(subset=["fb_speccode"]).set_index("fb_speccode").scientific_name
M={**dict(zip(nr.name_v2,nr.accepted_name)),**{a:a for a in sl.scientific_name}}
syn2acc={r.sn:code2acc[r.SpecCode] for r in syn.itertuples() if r.SpecCode in code2acc.index}
def v3name(n):
  if not isinstance(n,str): return None,"none"
  n2=" ".join(n.split()[:2])
  if n2 in M: return M[n2],"v3_name"
  if n2 in syn2acc: return syn2acc[n2],"fishbase_synonym"
  return None,"not_in_v3"
def marker(s):
  s=(s or "").upper()
  if re.search(r"\bCO[XI]?1\b|\bCOI\b|CYTOCHROME C OXIDASE SUBUNIT (I|1)\b|COX1",s): return "COI"
  if re.search(r"\bCYTB\b|\bCYT ?B\b|CYTOCHROME B",s): return "CYTB"
  if "16S" in s: return "16S"
  if "12S" in s: return "12S"
  if "COMPLETE GENOME" in s and "MITOCHONDRI" in s: return "mitogenome"
  if re.search(r"\bD-LOOP|CONTROL REGION",s): return "control_region"
  if re.search(r"\bND[1-6]L?\b|NADH",s): return "ND"
  if re.search(r"RAG|RHODOPSIN|\bRHO\b|18S|28S|ITS",s): return "nuclear"
  return "other"
# ---------- GenBank ----------
rows=[];fa=[]
for f in sorted(glob.glob("/tmp/ncbi/gb_*.gb")):
  for rec in SeqIO.parse(f,"genbank"):
    src=[x for x in rec.features if x.type=="source"]; q=src[0].qualifiers if src else {}
    genes=sorted({g for x in rec.features if x.type in("gene","CDS","rRNA") for g in x.qualifiers.get("gene",[])+x.qualifiers.get("product",[])})
    country=";".join(q.get("country",q.get("geo_loc_name",[])))
    ll=q.get("lat_lon",[None])[0]; lat=lon=np.nan
    if ll:
      mm=re.match(r"([\d.]+) ([NS]) ([\d.]+) ([EW])",ll)
      if mm: lat=float(mm[1])*(1 if mm[2]=="N" else -1); lon=float(mm[3])*(1 if mm[4]=="E" else -1)
    org=rec.annotations.get("organism"); acc,how=v3name(org)
    try: seq=str(rec.seq)
    except Exception: seq=""
    tax=rec.annotations.get("taxonomy",[])
    rows.append(dict(source="GenBank",record_id=rec.id,organism=org,v3_accepted_name=acc,name_match=how,
      class_ncbi="Chondrichthyes" if "Chondrichthyes" in tax else "Actinopterygii" if "Actinopterygii" in tax else ";".join(tax[:6]),
      family_ncbi=next((t for t in tax if t.endswith("idae")),None),marker=marker(" ".join(genes)+" "+rec.description),genes=";".join(genes)[:300],definition=rec.description,
      seq_length=len(rec.seq),country=country,country_is_sri_lanka=int("sri lanka" in country.lower()),lat_lon_raw=ll,lat=lat,lon=lon,
      collection_date=";".join(q.get("collection_date",[])),specimen_voucher=";".join(q.get("specimen_voucher",[])),isolate=";".join(q.get("isolate",[])),
      bold_id=";".join(x.split(":",1)[1] for x in rec.dbxrefs if x.startswith("BOLD")) or None,
      reference=(rec.annotations.get("references") or [None])[0].title if rec.annotations.get("references") else None,
      submission_date=rec.annotations.get("date"),url=f"https://www.ncbi.nlm.nih.gov/nuccore/{rec.id}",license="NCBI/INSDC: no NCBI use restrictions; submitters may claim rights (see README)"))
    if seq and "sri lanka" in country.lower(): fa.append(f">{rec.id}|{org}|{acc or 'NA'}|{rows[-1]['marker']}\n{seq}\n")
gb=pd.DataFrame(rows)
gb.to_csv("qc/genbank_all_hits_incl_non_sri_lanka_country.csv",index=False) if os.makedirs("qc",exist_ok=True) is None else None
gbs=gb[gb.country_is_sri_lanka==1].drop(columns=["country_is_sri_lanka"])
gbs.to_csv("genbank_srilanka_fish_sequences_metadata.csv",index=False)
open("fasta/genbank_srilanka_fish.fasta","w").write("".join(fa))
# ---------- BOLD ----------
b=pd.concat([pd.read_csv(f"raw/portal_{t}.tsv",sep="\t",low_memory=False,dtype=str) for t in ["Teleostei","Elasmobranchii"]],ignore_index=True).drop_duplicates("processid")
def pc(s):
  try: a=eval(s) if isinstance(s,str) and s.startswith("[") else None; return (a[0],a[1]) if a else (np.nan,np.nan)
  except Exception: return (np.nan,np.nan)
cc=b.coord.map(pc); b["lat"]=[c[0] for c in cc]; b["lon"]=[c[1] for c in cc]
nm=b.species.map(v3name); b["v3_accepted_name"]=[x[0] for x in nm]; b["name_match"]=[x[1] for x in nm]
b["seq_length"]=b.nuc.fillna("").str.replace("-","").str.len()
bo=pd.DataFrame({"source":"BOLD","record_id":b.processid,"sampleid":b.sampleid,"bin_uri":b.bin_uri,"class_bold":b["class"],"order":b["order"],"family":b.family,"genus":b.genus,
  "species_bold":b.species,"identification":b.identification,"identification_rank":b.identification_rank,"v3_accepted_name":b.v3_accepted_name,"name_match":b.name_match,
  "marker":b.marker_code,"seq_length":b.seq_length,"genbank_accession":b.insdc_acs,"country":b["country/ocean"],"province_state":b["province/state"],"region":b.region,"site":b.site,
  "lat":b.lat,"lon":b.lon,"coord_source":b.coord_source,"depth":b.depth,"habitat":b.habitat,"collection_date_start":b.collection_date_start,"collectors":b.collectors,
  "identified_by":b.identified_by,"institution":b.inst,"voucher_type":b.voucher_type,"recordsets":b.bold_recordset_code_arr,
  "url":"https://portal.boldsystems.org/record/"+b.processid,"license":"BOLD public data: CC BY-SA 4.0 (BOLD public data packages); cite BOLD + record"})
bo.to_csv("bold_srilanka_fish_barcodes_metadata.csv",index=False)
with open("fasta/bold_srilanka_fish.fasta","w") as fh:
  for r in b.itertuples():
    s=str(r.nuc) if isinstance(r.nuc,str) else ""
    if s: fh.write(f">{r.processid}|{r.species if isinstance(r.species,str) else 'NA'}|{r.bin_uri if isinstance(r.bin_uri,str) else 'NA'}|{r.marker_code}\n{s}\n")
# ---------- per-species coverage vs v3 ----------
cov=sl[["scientific_name","family","class","record_count","model_tier"]].copy()
bc=bo.dropna(subset=["v3_accepted_name"]).groupby("v3_accepted_name").agg(bold_records=("record_id","size"),bold_bins=("bin_uri",lambda s:";".join(sorted(set(s.dropna())))),bold_with_coords=("lat",lambda s:s.notna().sum()))
gc=gbs.dropna(subset=["v3_accepted_name"]).groupby("v3_accepted_name").agg(genbank_records=("record_id","size"),genbank_coi=("marker",lambda s:(s=="COI").sum()),genbank_cytb=("marker",lambda s:(s=="CYTB").sum()),genbank_with_latlon=("lat",lambda s:s.notna().sum()))
cov=cov.merge(bc,left_on="scientific_name",right_index=True,how="left").merge(gc,left_on="scientific_name",right_index=True,how="left")
for c in ["bold_records","bold_with_coords","genbank_records","genbank_coi","genbank_cytb","genbank_with_latlon"]: cov[c]=cov[c].fillna(0).astype(int)
cov["n_bold_bins"]=cov.bold_bins.fillna("").map(lambda s:len([x for x in s.split(";") if x]))
cov["has_sri_lanka_barcode"]=((cov.bold_records>0)|(cov.genbank_coi>0)).astype(int); cov["has_any_sri_lanka_sequence"]=((cov.bold_records>0)|(cov.genbank_records>0)).astype(int)
cov.sort_values("record_count",ascending=False).to_csv("species_barcode_coverage.csv",index=False)
nv=pd.concat([bo[bo.name_match=="not_in_v3"].assign(name=bo.species_bold)[["source","name","family"]],gbs[gbs.name_match=="not_in_v3"].assign(name=gbs.organism,family=gbs.family_ncbi)[["source","name","family"]]])
nv.groupby(["name","family"]).source.agg(lambda s:";".join(sorted(set(s)))+f" ({len(s)})").reset_index().rename(columns={"source":"sources_and_count"}).to_csv("qc/sequenced_taxa_not_in_v3_occurrence_list.csv",index=False)
print("genbank hits",len(gb),"country SL",len(gbs),gbs.marker.value_counts().to_dict(),"latlon",gbs.lat.notna().sum())
print("bold",len(bo),bo.class_bold.value_counts().to_dict(),"coords",bo.lat.notna().sum(),"bins",bo.bin_uri.nunique(),bo.marker.value_counts().to_dict())
print("v3 species with SL barcode",cov.has_sri_lanka_barcode.sum(),"any seq",cov.has_any_sri_lanka_sequence.sum(),"bold sp",(cov.bold_records>0).sum(),"gb sp",(cov.genbank_records>0).sum())
print("bold mapped",bo.v3_accepted_name.notna().sum(),"gb mapped",gbs.v3_accepted_name.notna().sum(),"genbank species",gbs.organism.nunique(),"bold species",bo.species_bold.nunique())
# overlap flag: BOLD records mined from / deposited in GenBank that are also in the GenBank table
gacc=set(gbs.record_id.str.split(".").str[0])
bo["also_in_genbank_table"]=bo.genbank_accession.fillna("").str.split(".").str[0].isin(gacc).astype(int)
bo.to_csv("bold_srilanka_fish_barcodes_metadata.csv",index=False); print("bold also in genbank table",bo.also_in_genbank_table.sum())
