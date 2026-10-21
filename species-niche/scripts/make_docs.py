import pandas as pd, re, numpy as np
B = "/workspace/species_niche/"
d = pd.read_csv(B + "species_niche.csv"); p = pd.read_csv(B + "species_prey.csv")
REPO = "repo fish-data/species_list.csv (v3)"; FBS = "FishBase v24.07 (rOpenSci HF parquet mirror)"; AMS = "AquaMaps HSPEN (aquamapsdb am.db, archive.org; hspen_r)"
LOCAL = "derived: repo occurrences (fish-data/train_ready/features.parquet) joined to repo env grids"
D = {
 "scientific_name": ("WoRMS accepted name used as species key in the repo", "", REPO),
 "fishbase_name": ("Name of the species in FishBase", "", REPO), "common_name": ("FishBase common name", "", REPO),
 "family": ("Family (most common across records)", "", REPO), "order": ("Order", "", REPO), "class": ("Class", "", REPO), "fish_group": ("Coarse group (ray_finned, shark_ray, ...)", "", REPO),
 "accepted_aphia_id": ("WoRMS AphiaID of the accepted name", "", REPO), "fb_speccode": ("FishBase SpecCode", "", REPO), "fb_link_method": ("How the FishBase SpecCode was linked", "", REPO),
 "am_species_id": ("AquaMaps SpeciesID (key into hspen_r)", "", AMS), "am_link_method": ("How AquaMaps was linked (fb_speccode / accepted_name / fishbase_name)", "", "derived"),
 "fishbase_sri_lanka_status": ("FishBase country status for Sri Lanka (C_Code 144), blank if the species is not on the FishBase Sri Lanka checklist", "", REPO),
 "habitat_salinity": ("marine / brackish / freshwater from FishBase Saltwater/Brack/Fresh", "", REPO), "freshwater_only": ("1 if FishBase lists freshwater only", "0/1", REPO),
 "preferred_conditions_summary": ("Text summary of conditions the species stays in: local p5-p95 SST and seabed depth (only if n_records>=5), AquaMaps preferred temp/depth, FishBase usual depth and habitats", "", "derived"),
 "avoided_conditions_summary": ("Text summary of conditions the species avoids: local avoidance (n>=10), AquaMaps unsuitable range, FishBase max depth; joined with ' | '", "", "derived"),
 "prey_main_groups": ("Top 5 harmonised prey groups with share of distinct prey taxa across FishBase + GloBI", "% of distinct prey names", "derived from species_prey.csv"),
 "n_records": ("Clean occurrence records in the repo (v3)", "count", REPO), "n_records_recommended": ("Records in the recommended training subset", "count", REPO), "model_tier": ("Repo model tier by record count", "", REPO),
 "fb_demers_pelag": ("FishBase habitat type (DemersPelag): pelagic-oceanic, pelagic-neritic, reef-associated, demersal, benthopelagic, bathydemersal, ...", "", FBS + " species"),
 "fb_migration": ("FishBase migration category (AnaCat)", "", FBS + " species"),
 "fb_depth_min_m": ("FishBase shallowest recorded depth (DepthRangeShallow)", "m", FBS + " species"), "fb_depth_max_m": ("FishBase deepest recorded depth (DepthRangeDeep)", "m", FBS + " species"),
 "fb_depth_common_min_m": ("FishBase usual depth, shallow (DepthRangeComShallow)", "m", FBS + " species"), "fb_depth_common_max_m": ("FishBase usual depth, deep (DepthRangeComDeep)", "m", FBS + " species"),
 "fb_max_length_cm": ("FishBase max length", "cm", FBS + " species"), "fb_climate_zone": ("FishBase environment/climate zone (EnvTemp)", "", FBS + " stocks"),
 "fb_temp_min_c": ("FishBase stocks TempMin (often from aquarium/lab literature)", "°C", FBS + " stocks"), "fb_temp_max_c": ("FishBase stocks TempMax", "°C", FBS + " stocks"),
 "fb_temp_pref_min_c": ("FishBase estimate TempPrefMin (10th percentile of temperature in occupied cells; AquaMaps-based)", "°C", FBS + " estimate"),
 "fb_temp_pref_mean_c": ("FishBase estimate TempPrefMean", "°C", FBS + " estimate"), "fb_temp_pref_max_c": ("FishBase estimate TempPrefMax (90th percentile)", "°C", FBS + " estimate"),
 "fb_trophic_level": ("FishBase trophic level (estimate.Troph)", "TL (2=herbivore ... 4.5=top predator)", FBS + " estimate"), "fb_trophic_level_se": ("SE of trophic level", "TL", FBS + " estimate"),
 "fb_trophic_level_basis": ("Whether trophic level comes from observed diet/food items or is model-predicted", "", FBS + " estimate.TrophObserved"),
 "fb_feeding_path": ("Benthic vs pelagic food chain (FeedingPath)", "", FBS + " estimate"), "fb_habitats": ("Habitat flags set in FishBase ecology (any stock)", "; list", FBS + " ecology"),
 "fb_social_behaviour": ("schooling / shoaling / solitary flags", "; list", FBS + " ecology"), "fb_feeding_type": ("FishBase main feeding type", "", FBS + " ecology.FeedingType"),
 "fb_diet_troph": ("Trophic level from diet composition studies", "TL", FBS + " ecology"), "fb_food_troph": ("Trophic level from food items", "TL", FBS + " ecology"),
 "fb_resilience": ("FishBase resilience (High/Medium/Low/Very low)", "", FBS + " stocks"), "fb_iucn_code": ("IUCN category as stored in FishBase (may lag the live Red List)", "", FBS + " stocks"),
 "am_layer": ("Which layer AquaMaps used for temp/salinity: s = surface, b = bottom", "", AMS), "am_pelagic_flag": ("AquaMaps pelagic flag (1 = only min depth limits the seabed)", "0/1", AMS),
 "am_n_occurrence_cells": ("Number of 0.5° cells with occurrences used to fit the envelope", "count", AMS + " speciesoccursum_r"), "am_date_created": ("Envelope creation date", "date", AMS),
 "obs_n_cells_0p1deg": ("Distinct 0.1° cells with records", "count", LOCAL), "obs_months": ("Calendar months with records", "list", LOCAL),
 "obs_frac_coral_reef_cell": ("Fraction of records in a UNEP-WCMC coral reef cell (fish-factors seabed_shelf_habitat 1 arcmin)", "0-1", LOCAL),
 "obs_frac_shelf_lt200m": ("Fraction of records (with seabed depth >0) on the shelf (<200 m)", "0-1", LOCAL),
 "obs_reliability": ("Reliability of local ranges by n_records: none / very low (<5) / low (5-19) / moderate (20-49) / good (>=50)", "", "derived"),
 "avoid_local_summary": ("Only species with n_records>=10: variables where >=20% of study-area water (10,000 uniform_water background points) lies outside the species' observed min-max", "", LOCAL),
 "avoid_local_max_frac_bg_outside": ("Largest single-variable fraction of uniform background outside the observed min-max (depth, SST, chl-a, SSS)", "0-1", LOCAL),
 "avoid_aquamaps_summary": ("AquaMaps min/max limits (outside = unsuitable) for parameters the model used (YN=1)", "", AMS),
 "am_frac_study_area_outside_envelope": ("Fraction of uniform background points (study area water) outside the AquaMaps min/max for depth, temp, salinity, bottom O2 (layer-matched to repo SST/WOA23)", "0-1", "derived: AquaMaps x repo grids"),
 "avoid_fishbase_summary": ("FishBase max depth and freshwater-only flag as avoidance hints", "", FBS),
 "prey_n_pairs_fishbase": ("Distinct prey items in FishBase fooditems + diet for this predator", "count", "species_prey.csv"),
 "prey_n_pairs_globi": ("Distinct prey name x interaction type pairs in GloBI", "count", "species_prey.csv"),
 "prey_top_group": ("Harmonised prey group with most distinct prey taxa", "", "species_prey.csv"),
 "prey_example_taxa": ("Up to 8 species-level prey names, most frequently recorded first", "; list", "species_prey.csv"),
 "fb_diet_top_items": ("Top 5 items by max % in FishBase diet composition studies", "%", FBS + " diet/diet_items"),
 "prey_recorded_in_sri_lanka_or_box": ("Any prey record from Sri Lanka (FishBase C_Code 144) or with coordinates in lat 4-11N lon 77-85E (GloBI)", "bool", "species_prey.csv"),
 "data_retrieved": ("Date sources were downloaded", "date", "")}
AMP = {"depth": ("depth", "m"), "temp": ("temperature (surface or bottom per am_layer)", "°C"), "salinity": ("salinity (surface or bottom per am_layer)", "psu"),
       "o2": ("bottom dissolved oxygen", "mmol m-3 (≈ umol/L)"), "primprod": ("primary production", "mgC m-2 day-1"), "landdist": ("distance to land", "km")}
LV = {"sst_c": ("SST, month-matched NOAA CRW else 2003-2026 climatology (repo sst_filled)", "°C"), "chla_mg_m3": ("chl-a, ESA OC-CCI month or climatology (10**log_chla); lagoon outliers >10 mg/m3 excluded", "mg m-3"),
      "seabed_depth_m": ("ETOPO 2022 seabed depth (records snapped to coast with depth 0 excluded)", "m"), "sss_psu": ("WOA23 surface salinity monthly climatology 0.25°", "psu"),
      "t100m_c": ("WOA23 temperature at 100 m (thermocline proxy)", "°C"), "bottom_temp_c": ("WOA23 near-bottom temperature", "°C"), "bottom_sal_psu": ("WOA23 near-bottom salinity", "psu"),
      "bottom_o2_umolkg": ("WOA23 near-bottom dissolved oxygen (1° grid)", "umol kg-1"), "mld_m": ("Mixed layer depth from WOA23 T (0.5 °C criterion)", "m"), "slope_deg": ("Seabed slope (1 arcmin)", "degrees")}
rows = []
for c in d.columns:
    if c in D: desc, u, s = D[c]
    elif m := re.match(r"am_(\w+?)_used$", c): desc, u, s = (f"1 if AquaMaps used {AMP[m.group(1)][0]} in the model", "0/1", AMS)
    elif m := re.match(r"am_(depth|temp|salinity|o2|primprod|landdist)_(min|prefmin|prefmax|max)_", c):
        lab = {"min": "absolute minimum", "prefmin": "preferred minimum (10th pct)", "prefmax": "preferred maximum (90th pct)", "max": "absolute maximum"}[m.group(2)]
        desc, u, s = (f"AquaMaps envelope {lab} of {AMP[m.group(1)][0]}", AMP[m.group(1)][1], AMS)
    elif m := re.match(r"obs_(.+)_(n|p05|p50|p95|min|max)$", c):
        v = m.group(1); st = {"n": "number of records with a value for", "p05": "5th percentile of", "p50": "median of", "p95": "95th percentile of", "min": "minimum of", "max": "maximum of"}[m.group(2)]
        desc, u, s = (f"Observed local {st} {LV[v][0]} at the species' records", "count" if m.group(2) == "n" else LV[v][1], LOCAL)
    else: desc, u, s = ("", "", "")
    rows.append({"file": "species_niche.csv", "column": c, "description": desc, "units": u, "source": s, "non_null": int(d[c].notna().sum()), "pct_species": round(100 * d[c].notna().mean(), 1)})
PD = {"predator_scientific_name": ("Predator = repo species (WoRMS accepted name)", "", REPO), "predator_family": ("Predator family", "", REPO), "predator_common_name": ("Predator common name", "", REPO),
      "source": ("FishBase fooditems / FishBase diet / GloBI", "", ""), "interaction_type": ("food item, diet composition item (FishBase); eats or preysOn (GloBI)", "", ""),
      "prey_name": ("Prey taxon or item name as given by the source (FishBase prey SpecCode resolved to binomial when available)", "", ""),
      "prey_rank": ("Taxonomic rank of prey (GloBI path ranks; FishBase: 'species' when the name is a binomial)", "", ""),
      "prey_group": ("Harmonised prey group (finfish, cephalopods, crustaceans (planktonic), crustaceans (benthic/other), other molluscs, worms, echinoderms, cnidarians/jellyfish, sponges/tunicates, other zooplankton, other benthic invertebrates, phytoplankton, algae/plants, detritus, fish eggs/larvae, insects/terrestrial invertebrates, tetrapods, other, other/unresolved). FishBase: from FoodII; GloBI: from taxon path, else name keywords", "", "derived"),
      "prey_category_l1": ("FishBase FoodI (detritus, plants, zoobenthos, zooplankton, nekton, others)", "", FBS), "prey_category_l2": ("FishBase FoodII", "", FBS), "prey_category_l3": ("FishBase FoodIII", "", FBS),
      "prey_taxon_path": ("GloBI target taxon path", "", "GloBI"), "prey_life_stage": ("Prey life stage(s)", "", ""), "predator_life_stage": ("Predator life stage(s)", "", ""),
      "diet_percent_max": ("Max % contribution of the item in FishBase diet studies", "%", FBS + " diet_items"), "n_records": ("Number of source rows/observations aggregated into this pair", "count", ""),
      "recorded_in_sri_lanka": ("FishBase record from Sri Lanka (C_Code 144)", "bool", FBS), "recorded_in_study_box": ("GloBI observation with coordinates inside lat 4-11N lon 77-85E", "bool", "GloBI"),
      "locality_examples": ("Up to 3 FishBase localities", "", FBS), "citation": ("FishBase RefNo(s), or up to 3 GloBI study citations", "", ""),
      "via_fishbase_in_globi": ("GloBI row whose citation mentions FishBase (possible duplicate of FishBase rows)", "bool", "GloBI"), "globi_query_name": ("Name(s) queried in GloBI (accepted and/or FishBase name)", "", "GloBI")}
for c in p.columns:
    desc, u, s = PD.get(c, ("", "", ""))
    rows.append({"file": "species_prey.csv", "column": c, "description": desc, "units": u, "source": s, "non_null": int(p[c].notna().sum()), "pct_species": np.nan})
dd = pd.DataFrame(rows); dd.to_csv(B + "data_dictionary.csv", index=False)
print("undocumented:", dd[dd.description == ""].column.tolist())
# coverage
cov = {"species_total": len(d), "fishbase_linked": d.fb_speccode.notna().sum(), "fb_habitat_type": d.fb_demers_pelag.notna().sum(), "fb_depth_range": d.fb_depth_max_m.notna().sum(),
       "fb_temp_pref": d.fb_temp_pref_mean_c.notna().sum(), "fb_temp_min_max_stocks": d.fb_temp_min_c.notna().sum(), "fb_trophic_level": d.fb_trophic_level.notna().sum(),
       "fb_trophic_level_observed": (d.fb_trophic_level_basis == "observed (diet/food items)").sum(), "fb_feeding_type": d.fb_feeding_type.notna().sum(), "fb_habitats": d.fb_habitats.notna().sum(),
       "aquamaps_envelope": d.am_species_id.notna().sum(), "aquamaps_o2_used": (d.am_o2_used == 1).sum(), "aquamaps_primprod_used": (d.am_primprod_used == 1).sum(),
       "local_ranges_any": (d.n_records > 0).sum(), "local_n_ge5": (d.n_records >= 5).sum(), "local_n_ge10_avoidance": d.avoid_local_summary.notna().sum(), "local_n_ge20": (d.n_records >= 20).sum(),
       "prey_any_source": d.prey_main_groups.notna().sum(), "prey_fishbase_fooditems": p[p.source == "FishBase fooditems"].predator_scientific_name.nunique(),
       "prey_fishbase_diet": p[p.source == "FishBase diet"].predator_scientific_name.nunique(), "prey_globi": p[p.source == "GloBI"].predator_scientific_name.nunique(),
       "prey_species_level_examples": d.prey_example_taxa.notna().sum(), "prey_recorded_in_sri_lanka_or_box": (d.prey_recorded_in_sri_lanka_or_box == True).sum(),
       "avoided_conditions_summary_any": d.avoided_conditions_summary.notna().sum(), "prey_pairs_total": len(p)}
cv = pd.DataFrame({"metric": list(cov), "n": [int(v) for v in cov.values()]}); cv["pct_of_species"] = (100 * cv.n / len(d)).round(1); cv.loc[cv.metric == "prey_pairs_total", "pct_of_species"] = np.nan
cv.to_csv(B + "coverage_stats.csv", index=False); print(cv.to_string())
print(p.source.value_counts().to_string()); print(p.prey_group.value_counts().to_string())
