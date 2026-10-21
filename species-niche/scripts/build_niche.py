"""Build species_niche.csv and species_prey.csv for the Sri Lanka fish dataset.
Inputs: repo fish-data/species_list.csv; FishBase v24.07 parquet (rOpenSci HF mirror) in raw/fishbase;
AquaMaps HSPEN subset (raw/aquamaps, from archive.org aquamapsdb am.db); GloBI cache raw/globi_obs;
work/occ_env.parquet + work/bg_env.parquet from join_env.py. Never fills values that a source lacks."""
import json, glob, os, re, numpy as np, pandas as pd
B = "/workspace/species_niche/"; R = "/workspace/ocean_hackathon_data/"; FB = B + "raw/fishbase/"
sl = pd.read_csv(R + "fish-data/species_list.csv")
sl["fb_speccode"] = sl.fb_speccode.astype("Int64"); sl["accepted_aphia_id"] = sl.accepted_aphia_id.astype("Int64")
codes = set(sl.fb_speccode.dropna().astype(int))
rd = lambda t: pd.read_parquet(FB + t + ".parquet")
yes = lambda v: v in (-1, 1, "-1", "1", True)

# ---------------- FishBase species-level ----------------
sp = rd("species"); sp = sp[sp.SpecCode.isin(codes)].set_index("SpecCode")
est = rd("estimate"); est = est[est.SpecCode.isin(codes)].drop_duplicates("SpecCode").set_index("SpecCode")
st = rd("stocks"); st = st[st.SpecCode.isin(codes)]
st["_lv"] = (~st.Level.fillna("").str.lower().str.startswith("species")).astype(int)
st = st.sort_values(["SpecCode", "_lv", "StockCode"]).drop_duplicates("SpecCode").set_index("SpecCode")
eco = rd("ecology"); eco = eco[eco.SpecCode.isin(codes)]
HAB = {"Neritic": "neritic", "Oceanic": "oceanic", "Epipelagic": "epipelagic", "Mesopelagic": "mesopelagic", "Bathypelagic": "bathypelagic",
       "Intertidal": "intertidal", "SubLittoral": "sublittoral", "Estuaries": "estuaries", "Mangroves": "mangroves", "Lagoons": "lagoons",
       "CoralReefs": "coral reefs", "ReefFlats": "reef flats", "DropOffs": "drop-offs", "SeaGrassBeds": "seagrass beds", "Macrophyte": "macrophytes",
       "SoftBottom": "soft bottom", "Sand": "sand", "Mud": "mud", "HardBottom": "hard bottom", "Rocky": "rocky", "Rubble": "rubble",
       "Crevices": "crevices", "Caves": "caves", "Seamounts": "seamounts", "Burrows": "burrows", "Benthic": "benthic", "Demersal": "demersal", "Pelagic": "pelagic"}
def eco_row(g):
    habs = [lab for c, lab in HAB.items() if c in g and g[c].apply(yes).any()]
    soc = [lab for c, lab in [("Schooling", "schooling"), ("Shoaling", "shoaling"), ("Solitary", "solitary")] if g[c].apply(yes).any()]
    ft = g.FeedingType.dropna(); ft = ft[ft.str.strip() != ""]
    return pd.Series({"fb_habitats": "; ".join(habs) or np.nan, "fb_social_behaviour": "; ".join(soc) or np.nan,
                      "fb_feeding_type": "; ".join(sorted(set(ft))) or np.nan,
                      "fb_diet_troph": g.DietTroph.dropna().iloc[0] if g.DietTroph.notna().any() else np.nan,
                      "fb_food_troph": g.FoodTroph.dropna().iloc[0] if g.FoodTroph.notna().any() else np.nan})
ecoS = eco.groupby("SpecCode").apply(eco_row, include_groups=False)

def clean_txt(v):
    if v is None or (isinstance(v, float) and np.isnan(v)): return np.nan
    v = str(v).strip(); return v if v else np.nan
fbcols = pd.DataFrame(index=sorted(codes))
fbcols["fb_demers_pelag"] = sp.DemersPelag.map(clean_txt)
fbcols["fb_migration"] = sp.AnaCat.map(clean_txt)
fbcols["fb_depth_min_m"] = sp.DepthRangeShallow; fbcols["fb_depth_max_m"] = sp.DepthRangeDeep
fbcols["fb_depth_common_min_m"] = sp.DepthRangeComShallow; fbcols["fb_depth_common_max_m"] = sp.DepthRangeComDeep
fbcols["fb_max_length_cm"] = sp.Length
fbcols["fb_climate_zone"] = st.EnvTemp.map(clean_txt)
fbcols["fb_temp_min_c"] = st.TempMin; fbcols["fb_temp_max_c"] = st.TempMax
fbcols["fb_temp_pref_min_c"] = est.TempPrefMin; fbcols["fb_temp_pref_mean_c"] = est.TempPrefMean; fbcols["fb_temp_pref_max_c"] = est.TempPrefMax
fbcols["fb_trophic_level"] = est.Troph; fbcols["fb_trophic_level_se"] = est.seTroph
fbcols["fb_trophic_level_basis"] = est.TrophObserved.map(lambda v: "observed (diet/food items)" if v in (1, -1) else ("model-predicted" if pd.notna(v) else np.nan))
fbcols["fb_feeding_path"] = est.FeedingPath.map(clean_txt)
fbcols = fbcols.join(ecoS)
fbcols["fb_resilience"] = st.Resilience.map(clean_txt)
fbcols["fb_iucn_code"] = st.IUCN_Code.map(clean_txt)
fbcols.index.name = "fb_speccode"

# ---------------- AquaMaps HSPEN ----------------
ao = pd.read_csv(B + "raw/aquamaps/speciesoccursum_srilanka_subset.csv"); ah = pd.read_csv(B + "raw/aquamaps/hspen_srilanka_subset.csv")
ao["binomial"] = ao.Genus + " " + ao.Species
am = ah.merge(ao[["SpeciesID", "SpecCode", "binomial", "OccurCells"]], on="SpeciesID", how="left")
amcols = {"SpeciesID": "am_species_id", "Layer": "am_layer", "Pelagic": "am_pelagic_flag", "OccurCells": "am_n_occurrence_cells", "DateCreated": "am_date_created"}
P = {"Depth": ("depth", "m"), "Temp": ("temp", "c"), "Salinity": ("salinity", "psu"), "Oxy": ("o2", "mmol_m3"), "PrimProd": ("primprod", "mgc_m2_d"), "LandDist": ("landdist", "km")}
for k, (n, u) in P.items():
    amcols[k + "YN"] = f"am_{n}_used"
    for s, s2 in [("Min", "min"), ("PrefMin", "prefmin"), ("PrefMax", "prefmax"), ("Max", "max")]:
        amcols[k + s] = f"am_{n}_{s2}_{u}"
am = am.rename(columns=amcols)
am["am_date_created"] = am.am_date_created.astype(str).str[:10]
amkeep = list(amcols.values())
am_by_code = am.dropna(subset=["SpecCode"]).drop_duplicates("SpecCode").set_index(am.dropna(subset=["SpecCode"]).drop_duplicates("SpecCode").SpecCode.astype(int))[amkeep]
am_by_name = am.drop_duplicates("binomial").set_index("binomial")[amkeep]

# ---------------- base table ----------------
base = sl[["scientific_name", "fishbase_name", "common_name", "family", "order", "class", "fish_group", "accepted_aphia_id", "fb_speccode",
           "fb_link_method", "fishbase_sri_lanka_status", "habitat_salinity", "freshwater_only", "record_count", "record_count_recommended", "model_tier"]].copy()
base = base.rename(columns={"record_count": "n_records", "record_count_recommended": "n_records_recommended"})
df = base.merge(fbcols, left_on="fb_speccode", right_index=True, how="left")
amrows = []
for _, r in base.iterrows():
    hit = None; how = np.nan
    if pd.notna(r.fb_speccode) and int(r.fb_speccode) in am_by_code.index: hit = am_by_code.loc[int(r.fb_speccode)]; how = "fb_speccode"
    elif r.scientific_name in am_by_name.index: hit = am_by_name.loc[r.scientific_name]; how = "accepted_name"
    elif pd.notna(r.fishbase_name) and r.fishbase_name in am_by_name.index: hit = am_by_name.loc[r.fishbase_name]; how = "fishbase_name"
    d = hit.to_dict() if hit is not None else {c: np.nan for c in amkeep}; d["am_link_method"] = how; amrows.append(d)
df = pd.concat([df.reset_index(drop=True), pd.DataFrame(amrows)], axis=1)

# ---------------- local observed ranges ----------------
occ = pd.read_parquet(B + "work/occ_env.parquet"); bg = pd.read_parquet(B + "work/bg_env.parquet")
occ.loc[occ.chla_lagoon_outlier == 1, "chla_mg_m3"] = np.nan
occ.loc[occ.bathy_depth_m <= 0, "bathy_depth_m"] = np.nan   # coastal-snapped records carry 0, not a real depth
bgu = bg[bg.bg_type == "uniform_water"].copy(); bgu.loc[bgu.chla_lagoon_outlier == 1, "chla_mg_m3"] = np.nan
VARS = {"sst_c": "sst_c", "chla_mg_m3": "chla_mg_m3", "bathy_depth_m": "seabed_depth_m", "woa_sss_psu": "sss_psu", "woa_t_100m_c": "t100m_c",
        "woa_t_bottom_c": "bottom_temp_c", "woa_s_bottom_psu": "bottom_sal_psu", "woa_o2_bottom_umolkg": "bottom_o2_umolkg", "mld_m": "mld_m", "slope_deg": "slope_deg"}
loc = []
g = occ.groupby("label_species")
for name, d in g:
    row = {"scientific_name": name, "obs_n_cells_0p1deg": int((d.lat.round(1).astype(str) + "_" + d.lon.round(1).astype(str)).nunique()),
           "obs_months": ",".join(str(m) for m in sorted(d.month.dropna().astype(int).unique())),
           "obs_frac_coral_reef_cell": round(d.coral_reef_cell.mean(), 3) if d.coral_reef_cell.notna().any() else np.nan,
           "obs_frac_shelf_lt200m": round((d.bathy_depth_m.dropna() < 200).mean(), 3) if d.bathy_depth_m.notna().any() else np.nan}
    for v, lab in VARS.items():
        x = d[v].dropna()
        row[f"obs_{lab}_n"] = len(x)
        for q in (5, 50, 95): row[f"obs_{lab}_p{q:02d}"] = round(float(np.percentile(x, q)), 4) if len(x) else np.nan
        if v in ("sst_c", "chla_mg_m3", "bathy_depth_m", "woa_sss_psu", "woa_o2_bottom_umolkg"):
            row[f"obs_{lab}_min"] = round(float(x.min()), 4) if len(x) else np.nan; row[f"obs_{lab}_max"] = round(float(x.max()), 4) if len(x) else np.nan
    loc.append(row)
loc = pd.DataFrame(loc)
df = df.merge(loc, on="scientific_name", how="left")
def rel(n):
    return "none" if n == 0 else "very low (<5)" if n < 5 else "low (5-19)" if n < 20 else "moderate (20-49)" if n < 50 else "good (>=50)"
df["obs_reliability"] = df.n_records.fillna(0).astype(int).map(rel)

# ---------------- avoided conditions ----------------
AV = [("bathy_depth_m", "seabed_depth_m", "seabed depth", "m"), ("sst_c", "sst_c", "SST", "°C"), ("chla_mg_m3", "chla_mg_m3", "chl-a", "mg/m3"),
      ("woa_sss_psu", "sss_psu", "surface salinity", "psu")]
bgvals = {v: bgu[v].dropna().values for v, *_ in AV}
def local_avoid(r):
    if r.n_records < 10: return np.nan, np.nan
    parts, mx = [], 0.0
    for v, lab, txt, u in AV:
        lo, hi = r[f"obs_{lab}_min"], r[f"obs_{lab}_max"]
        if pd.isna(lo): continue
        b = bgvals[v]
        fhi, flo = (b > hi).mean(), (b < lo).mean()
        if fhi >= 0.2: parts.append(f"never recorded at {txt} > {hi:.3g} {u} ({fhi:.0%} of study-area water is above)")
        if flo >= 0.2: parts.append(f"never recorded at {txt} < {lo:.3g} {u} ({flo:.0%} of study-area water is below)")
        mx = max(mx, fhi + flo)
    return ("; ".join(parts) or "no strong local avoidance signal"), round(mx, 3)
la = df.apply(local_avoid, axis=1, result_type="expand"); df["avoid_local_summary"] = la[0]; df["avoid_local_max_frac_bg_outside"] = la[1]
# AquaMaps envelope vs study-area water (uniform background): fraction of background points outside min/max on depth, temp, salinity
def am_avoid(r):
    if pd.isna(r.am_species_id): return np.nan, np.nan
    parts, outside = [], np.zeros(len(bgu), bool)
    tcol = "woa_t_bottom_c" if r.am_layer == "b" else "sst_c"; scol = "woa_s_bottom_psu" if r.am_layer == "b" else "woa_sss_psu"
    for n, u, txt, col in [("depth", "m", "depth", "bathy_depth_m"), ("temp", "c", "temperature", tcol), ("salinity", "psu", "salinity", scol), ("o2", "mmol_m3", "bottom O2", "woa_o2_bottom_umolkg")]:
        lo, hi, used = r[f"am_{n}_min_{u}"], r[f"am_{n}_max_{u}"], r[f"am_{n}_used"]
        if pd.isna(lo) or pd.isna(hi) or used != 1: continue
        unit = {"m": "m", "c": "°C", "psu": "psu", "mmol_m3": "mmol/m3"}[u]
        if n == "depth" and r.am_pelagic_flag == 1: parts.append(f"seabed depth < {lo:g} m (pelagic: max depth {hi:g} m not used as a seabed limit)")
        else: parts.append(f"{txt} < {lo:g} or > {hi:g} {unit}")
        x = bgu[col].values
        if n == "depth": x = np.maximum(x, 0)
        outside |= np.where(np.isnan(x), False, (x < lo) | (x > hi)) if n != "depth" else (x < lo)  # depth: AquaMaps uses bottom depth >= min; species can sit above deep seabed
        if n == "depth" and r.am_pelagic_flag != 1: outside |= (x > hi)
    return ("AquaMaps unsuitable: " + "; ".join(parts)) if parts else np.nan, round(outside.mean(), 3)
aa = df.apply(am_avoid, axis=1, result_type="expand"); df["avoid_aquamaps_summary"] = aa[0]; df["am_frac_study_area_outside_envelope"] = aa[1]
def fb_avoid(r):
    p = []
    if pd.notna(r.fb_depth_max_m): p.append(f"FishBase: not recorded deeper than {r.fb_depth_max_m:g} m")
    if r.freshwater_only == 1: p.append("freshwater-only species (FishBase): marine records likely lagoon/estuary or misidentified")
    return "; ".join(p) or np.nan
df["avoid_fishbase_summary"] = df.apply(fb_avoid, axis=1)
df["avoided_conditions_summary"] = df[["avoid_local_summary", "avoid_aquamaps_summary", "avoid_fishbase_summary"]].apply(
    lambda s: " | ".join(x for x in s if isinstance(x, str) and x != "no strong local avoidance signal") or np.nan, axis=1)
# preferred conditions text
def pref(r):
    p = []
    if r.n_records >= 5 and pd.notna(r.obs_sst_c_p05): p.append(f"local SST {r.obs_sst_c_p05:.1f}-{r.obs_sst_c_p95:.1f} °C (p5-p95, n={int(r.obs_sst_c_n)})")
    if r.n_records >= 5 and pd.notna(r.obs_seabed_depth_m_p05): p.append(f"seabed depth {r.obs_seabed_depth_m_p05:.0f}-{r.obs_seabed_depth_m_p95:.0f} m")
    if pd.notna(r.am_temp_prefmin_c): p.append(f"AquaMaps preferred temp {r.am_temp_prefmin_c:g}-{r.am_temp_prefmax_c:g} °C ({'bottom' if r.am_layer=='b' else 'surface'})")
    if pd.notna(r.am_depth_prefmin_m): p.append(f"AquaMaps preferred depth {r.am_depth_prefmin_m:g}-{r.am_depth_prefmax_m:g} m")
    if pd.notna(r.fb_depth_common_min_m) and pd.notna(r.fb_depth_common_max_m): p.append(f"FishBase usual depth {r.fb_depth_common_min_m:g}-{r.fb_depth_common_max_m:g} m")
    if isinstance(r.fb_habitats, str): p.append("habitats: " + r.fb_habitats)
    return "; ".join(p) or np.nan
df["preferred_conditions_summary"] = df.apply(pref, axis=1)

# ---------------- prey (long) ----------------
FOODII = {"finfish": "finfish", "fish (early stages)": "fish eggs/larvae", "benth. crust.": "crustaceans (benthic/other)", "plank. crust.": "crustaceans (planktonic)",
          "plank. crust": "crustaceans (planktonic)", "cephalopods": "cephalopods", "mollusks": "other molluscs", "molluscs": "other molluscs", "worms": "worms",
          "echinoderms": "echinoderms", "cnidarians": "cnidarians/jellyfish", "jellyfish/hydroids": "cnidarians/jellyfish", "sponges/tunicates": "sponges/tunicates",
          "other plank. invertebrates": "other zooplankton", "other benth. invertebrates": "other benthic invertebrates", "phytoplankton": "phytoplankton",
          "other plants": "algae/plants", "detritus": "detritus", "insects": "insects/terrestrial invertebrates", "other terrest. invertebrates": "insects/terrestrial invertebrates",
          "mammals": "tetrapods", "birds": "tetrapods", "herps": "tetrapods", "others": "other"}
def group_fb(f1, f2, name=""):
    k = str(f2).strip().lower() if pd.notna(f2) else ""
    if k in FOODII:
        g = FOODII[k]
        if g == "other molluscs" and re.search(r"squid|octopus|sepia|loligo|cephalop|cuttle", str(name), re.I): g = "cephalopods"
        return g
    return {"detritus": "detritus", "plants": "algae/plants", "zooplankton": "other zooplankton", "zoobenthos": "other benthic invertebrates", "nekton": "other nekton"}.get(str(f1).strip().lower(), "other") if pd.notna(f1) else "unknown"
PATHMAP = [(r"cephalopoda", "cephalopods"), (r"actinopterygii|actinopteri|teleostei|chondrichthyes|elasmobranchii|osteichthyes|myxini|pisces|holocephali", "finfish"),
           (r"copepoda|euphausiacea|mysida|ostracoda|branchiopoda|cladocera|hyperiidea|thecostraca \| .*nauplius", "crustaceans (planktonic)"),
           (r"crustacea|malacostraca|decapoda|stomatopoda|isopoda|amphipoda|cumacea|tanaidacea|cirripedia|arthropoda", "crustaceans (benthic/other)"),
           (r"insecta|arachnida|myriapoda", "insects/terrestrial invertebrates"),
           (r"mollusca", "other molluscs"), (r"annelida|polychaeta|nematoda|sipuncula|platyhelminthes|nemertea|echiura|oligochaeta", "worms"),
           (r"echinodermata", "echinoderms"), (r"cnidaria|ctenophora", "cnidarians/jellyfish"), (r"porifera|tunicata|ascidiacea|thaliacea|appendicularia", "sponges/tunicates"),
           (r"chaetognatha|foraminifera|radiozoa|rotifera|ciliophora", "other zooplankton"),
           (r"bacillariophyta|dinophyceae|dinoflagellata|myzozoa|cyanobacteria|haptophyta|bacillariophyceae", "phytoplankton"),
           (r"chlorophyta|rhodophyta|phaeophyceae|ochrophyta|plantae|tracheophyta|viridiplantae|streptophyta|charophyta", "algae/plants"),
           (r"\baves\b|mammalia|reptilia|amphibia|testudines|squamata", "tetrapods"), (r"bryozoa|brachiopoda|hemichordata", "other benthic invertebrates")]
NAMEMAP = [(r"priapul|sipuncul", "worms"), (r"autotroph", "algae/plants"), (r"^(para|acro|clauso|neo|cala|eu)?calanus|^euterpina|^oithona|^oncaea|^corycaeus|^acartia|^temora|^centropages", "crustaceans (planktonic)"),
           (r"^krohnitta|^sagitta|^flaccisagitta|^parasagitta|chaetognath", "other zooplankton"), (r"squid|octopus|cuttle|cephalop", "cephalopods"), (r"fish egg|larva(e)? of fish|fish larv", "fish eggs/larvae"),
           (r"\bfish|finfish|teleost|anchov|sardin|herring|goby|gobies", "finfish"), (r"copepod|krill|euphaus|mysid|zooplank|ostracod|cladocer", "crustaceans (planktonic)"),
           (r"shrimp|prawn|crab|lobster|crustac|amphipod|isopod|stomatopod|decapod", "crustaceans (benthic/other)"), (r"worm|polychaet|nematod", "worms"),
           (r"bivalv|gastropod|snail|clam|mussel|mollus", "other molluscs"), (r"urchin|echinoderm|ophiur|starfish|holothur|sea cucumber", "echinoderms"),
           (r"jellyfish|medus|hydroid|coral|cnidar|ctenophor|siphonoph", "cnidarians/jellyfish"), (r"sponge|tunicat|salp|ascidian|appendicular", "sponges/tunicates"),
           (r"phytopl|diatom|dinoflag", "phytoplankton"), (r"alga|seaweed|plant|seagrass", "algae/plants"), (r"detrit|debris|organic matter", "detritus"), (r"insect", "insects/terrestrial invertebrates")]
def group_globi(name, path):
    p = str(path).lower() if pd.notna(path) else ""
    for rx, gname in PATHMAP:
        if p and re.search(rx, p): return gname
    n = str(name).lower()
    k = n.strip()
    if k in FOODII: return FOODII[k]
    for rx, gname in NAMEMAP:
        if re.search(rx, n): return gname
    return "other/unresolved"
def rank_of(path, ranks):
    if pd.isna(ranks) or pd.isna(path): return np.nan
    r = [x.strip() for x in str(ranks).split("|")]
    return r[-1] if r and r[-1] else np.nan
name2acc = {}
for _, r in sl.iterrows():
    name2acc[r.scientific_name] = r.scientific_name
    if pd.notna(r.fishbase_name): name2acc.setdefault(r.fishbase_name, r.scientific_name)
code2acc = dict(zip(sl.fb_speccode.dropna().astype(int), sl.loc[sl.fb_speccode.notna(), "scientific_name"]))
allsp = rd("species"); allsp["binomial"] = allsp.Genus + " " + allsp.Species; spname = dict(zip(allsp.SpecCode, allsp.binomial))
prey = []
fi = rd("fooditems"); fi = fi[fi.SpecCode.isin(codes)].copy()
fi["prey_name"] = fi.Foodname.map(clean_txt)
fi.loc[fi.PreySpecCode.notna() & fi.PreySpecCode.isin(spname.keys()), "prey_name_fb"] = fi.PreySpecCode.map(spname)
fi["prey_name"] = fi.prey_name_fb.fillna(fi.prey_name).fillna(fi.FoodIII.map(clean_txt)).fillna(fi.FoodII.map(clean_txt))
fi["sl"] = fi.C_Code.astype(str).str.strip() == "144"
for (spc, pn), d in fi.groupby(["SpecCode", "prey_name"], dropna=False):
    r0 = d.iloc[0]
    prey.append({"predator_scientific_name": code2acc[spc], "source": "FishBase fooditems", "interaction_type": "food item", "prey_name": pn,
                 "prey_rank": "species" if re.match(r"^[A-Z][a-z]+ [a-z]+$", str(pn)) and not re.search(r" (sp|spp)\.?$", str(pn)) else np.nan, "prey_group": group_fb(r0.FoodI, r0.FoodII, pn),
                 "prey_category_l1": clean_txt(r0.FoodI), "prey_category_l2": clean_txt(r0.FoodII), "prey_category_l3": clean_txt(r0.FoodIII),
                 "prey_taxon_path": np.nan, "prey_life_stage": "; ".join(sorted(set(d.PreyStage.dropna().astype(str)))) or np.nan,
                 "predator_life_stage": "; ".join(sorted(set(d.PredatorStage.dropna().astype(str)))) or np.nan,
                 "diet_percent_max": np.nan, "n_records": len(d), "recorded_in_sri_lanka": bool(d.sl.any()), "recorded_in_study_box": np.nan,
                 "locality_examples": "; ".join(sorted(set(d.Locality.dropna().astype(str).str.strip()))[:3]) or np.nan,
                 "citation": "FishBase v24.07 fooditems; RefNo " + ", ".join(sorted(set(d.FoodsRefNo.dropna().astype(int).astype(str)))[:5]),
                 "via_fishbase_in_globi": np.nan})
dt = rd("diet"); di = rd("diet_items"); dt = dt[dt.Speccode.isin(codes)]
di = di.merge(dt[["DietCode", "Speccode", "Locality", "C_Code", "DietRefNo", "SampleStage"]], on="DietCode")
di["prey_name"] = di.DietSpeccode.map(spname).where(di.DietSpeccode.notna() & di.DietSpeccode.isin(spname.keys()))
di["prey_name"] = di.prey_name.fillna(di.ItemName.map(clean_txt)).fillna(di.FoodIII.map(clean_txt)).fillna(di.FoodII.map(clean_txt))
di["sl"] = di.C_Code.astype(str).str.strip() == "144"
for (spc, pn), d in di.groupby(["Speccode", "prey_name"], dropna=False):
    r0 = d.iloc[0]
    prey.append({"predator_scientific_name": code2acc[spc], "source": "FishBase diet", "interaction_type": "diet composition item", "prey_name": pn,
                 "prey_rank": "species" if re.match(r"^[A-Z][a-z]+ [a-z]+$", str(pn)) and not re.search(r" (sp|spp)\.?$", str(pn)) else np.nan, "prey_group": group_fb(r0.FoodI, r0.FoodII, pn),
                 "prey_category_l1": clean_txt(r0.FoodI), "prey_category_l2": clean_txt(r0.FoodII), "prey_category_l3": clean_txt(r0.FoodIII),
                 "prey_taxon_path": np.nan, "prey_life_stage": "; ".join(sorted(set(d.Stage.dropna().astype(str)))) or np.nan,
                 "predator_life_stage": "; ".join(sorted(set(d.SampleStage.dropna().astype(str)))) or np.nan,
                 "diet_percent_max": d.DietPercent.max(), "n_records": len(d), "recorded_in_sri_lanka": bool(d.sl.any()), "recorded_in_study_box": np.nan,
                 "locality_examples": "; ".join(sorted(set(d.Locality.dropna().astype(str).str.strip()))[:3]) or np.nan,
                 "citation": "FishBase v24.07 diet; RefNo " + ", ".join(sorted(set(d.DietRefNo.dropna().astype(int).astype(str)))[:5]),
                 "via_fishbase_in_globi": np.nan})
gl_cov = {}
for f in glob.glob(B + "raw/globi_obs/*.json"):
    j = json.load(open(f)); qn = j["query_name"]; acc = name2acc.get(qn)
    if not j["data"]: continue
    d = pd.DataFrame(j["data"], columns=j["columns"])
    d = d[d.target_taxon_name.notna() & (d.target_taxon_name.str.strip() != "")]
    if d.empty: continue
    gl_cov[acc] = gl_cov.get(acc, 0) + len(d)
    d["inbox"] = d.latitude.between(4, 11) & d.longitude.between(77, 85)
    for (pn, it), x in d.groupby(["target_taxon_name", "interaction_type"]):
        r0 = x.iloc[0]; cits = sorted(set(x.study_title.dropna().astype(str)))
        prey.append({"predator_scientific_name": acc, "source": "GloBI", "interaction_type": it, "prey_name": pn,
                     "prey_rank": rank_of(r0.target_taxon_path, r0.target_taxon_path_ranks), "prey_group": group_globi(pn, r0.target_taxon_path),
                     "prey_category_l1": np.nan, "prey_category_l2": np.nan, "prey_category_l3": np.nan, "prey_taxon_path": clean_txt(r0.target_taxon_path),
                     "prey_life_stage": "; ".join(sorted(set(x.target_specimen_life_stage.dropna().astype(str))))[:200] or np.nan,
                     "predator_life_stage": "; ".join(sorted(set(x.source_specimen_life_stage.dropna().astype(str))))[:200] or np.nan,
                     "diet_percent_max": np.nan, "n_records": len(x), "recorded_in_sri_lanka": np.nan, "recorded_in_study_box": bool(x.inbox.any()),
                     "locality_examples": np.nan, "citation": " || ".join(c[:300] for c in cits[:3]) + (f" || (+{len(cits)-3} more)" if len(cits) > 3 else ""),
                     "via_fishbase_in_globi": any("fishbase" in c.lower() for c in cits), "_query": qn})
prey = pd.DataFrame(prey)
prey["globi_query_name"] = prey.pop("_query")
# if both accepted and FishBase name were queried in GloBI, merge duplicates
gmask = prey.source == "GloBI"
g = prey[gmask].groupby(["predator_scientific_name", "interaction_type", "prey_name"], as_index=False).agg(
    {**{c: "first" for c in prey.columns if c not in ("predator_scientific_name", "interaction_type", "prey_name", "n_records", "globi_query_name", "recorded_in_study_box", "via_fishbase_in_globi")},
     "n_records": "sum", "globi_query_name": lambda s: ";".join(sorted(set(s))), "recorded_in_study_box": "max", "via_fishbase_in_globi": "max"})
prey = pd.concat([prey[~gmask], g], ignore_index=True)
fam = df.set_index("scientific_name")[["family", "common_name"]]
prey.insert(1, "predator_family", prey.predator_scientific_name.map(fam.family)); prey.insert(2, "predator_common_name", prey.predator_scientific_name.map(fam.common_name))
prey = prey.sort_values(["predator_scientific_name", "source", "prey_group", "prey_name"]).reset_index(drop=True)

# prey summaries per species
def summ(d):
    out = {}
    out["prey_n_pairs_fishbase"] = int(d.source.str.startswith("FishBase").sum()); out["prey_n_pairs_globi"] = int((d.source == "GloBI").sum())
    gg = d[~d.prey_group.isin(["unknown", "other/unresolved", "other"])].groupby("prey_group").prey_name.nunique().sort_values(ascending=False)
    tot = gg.sum()
    out["prey_main_groups"] = "; ".join(f"{k} ({v/tot:.0%})" for k, v in gg.head(5).items()) if tot else np.nan
    out["prey_top_group"] = gg.index[0] if tot else np.nan
    isbin = d.prey_name.astype(str).str.match(r"^[A-Z][a-z]+ [a-z]+$") & ~d.prey_name.astype(str).str.contains(r" (?:sp|spp|larvae|eggs|juveniles|remains)$")
    spp = d[isbin & ((d.prey_rank == "species") | (d.source.str.startswith("FishBase") & isbin) | (d.prey_rank.isna() & isbin & (d.prey_group != "other/unresolved")))].groupby("prey_name").n_records.sum().sort_values(ascending=False)
    out["prey_example_taxa"] = "; ".join(spp.head(8).index) or np.nan
    fbd = d[d.source == "FishBase diet"].dropna(subset=["diet_percent_max"]).sort_values("diet_percent_max", ascending=False)
    out["fb_diet_top_items"] = "; ".join(f"{r.prey_name} ({r.diet_percent_max:g}%)" for r in fbd.head(5).itertuples()) or np.nan
    out["prey_recorded_in_sri_lanka_or_box"] = bool((d.recorded_in_sri_lanka == True).any() or (d.recorded_in_study_box == True).any())
    return pd.Series(out)
ps = prey.groupby("predator_scientific_name").apply(summ, include_groups=False)
df = df.merge(ps, left_on="scientific_name", right_index=True, how="left")
for c in ["prey_n_pairs_fishbase", "prey_n_pairs_globi"]: df[c] = df[c].fillna(0).astype(int)
df["prey_recorded_in_sri_lanka_or_box"] = df.prey_recorded_in_sri_lanka_or_box.astype("boolean")
df["prey_main_groups"] = df.prey_main_groups.where(df.prey_main_groups.notna(), np.nan)
df["data_retrieved"] = "2026-10-20"
# column order
front = ["scientific_name", "fishbase_name", "common_name", "family", "order", "class", "fish_group", "accepted_aphia_id", "fb_speccode", "fb_link_method", "am_species_id", "am_link_method",
         "fishbase_sri_lanka_status", "habitat_salinity", "freshwater_only", "preferred_conditions_summary", "avoided_conditions_summary", "prey_main_groups"]
df = df[front + [c for c in df.columns if c not in front]]
df.to_csv(B + "species_niche.csv", index=False); prey.to_csv(B + "species_prey.csv", index=False)
df.to_parquet(B + "species_niche.parquet", index=False); prey.to_parquet(B + "species_prey.parquet", index=False)
print(df.shape, prey.shape)
