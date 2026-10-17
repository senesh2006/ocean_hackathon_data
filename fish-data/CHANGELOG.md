# CHANGELOG

## v3 (2026-10-17) — reviewer fixes
| Reviewer issue | Fix | Files changed/added |
|---|---|---|
| 73 freshwater-only species (214 records) in the marine set | `habitat_salinity`, `habitat_salinity_detail`, `freshwater_only` from FishBase; excluded from recommended sets, kept (flagged) in the full set | merged/*, train_ready/features*.parquet, species_list.csv, merged/srilanka_fish_inland_or_land_excluded.csv, fish-factors/species_flags/species_demersal_trawl_flags.csv |
| basisOfRecord case mix, licence strings not canonical | canonical `basis_of_record`; `license_norm` + `license_level`; raw files get `basis_of_record_norm`, `license_norm`, `license_level` (original columns untouched); OBIS dataset-level licence for records with no record licence | obis/obis_srilanka_fish.csv, gbif/gbif_srilanka_fish.csv, merged/*, train_ready/features*.parquet, qc/dropped_missing_coord_date_species.csv, NEW qc/obis_dataset_licenses.csv |
| Teleostei vs Actinopterygii | `class` harmonised to Actinopterygii, `class_original` kept | obis/, gbif/ (`class_validated_original`), merged/*, train_ready/*, qc/taxonomy_class_summary.csv, qc/taxonomy_validation_dropped.csv, qc/dropped_missing_coord_date_species.csv |
| ~62 FishBase name mismatches, species split across OBIS/GBIF names | WoRMS accepted names; FishBase SpecCode via accepted/v2/synonym names; species merged; re-deduplicated; species_list counts/tiers rebuilt; species flags rebuilt | merged/*, train_ready/*, species_list.csv, NEW qc/name_resolution_worms_fishbase.csv, NEW qc/_worms_match_raw.json, NEW qc/dropped_duplicates_after_name_merge.csv, fish-factors/species_flags/species_demersal_trawl_flags.csv |
| chl-a skew and lagoon outliers | `log10_chla_mg_m3`, `log10_chla_mg_m3_clim`, `chla_lagoon_outlier` (>10 mg m-3); README note; climatologies unchanged | merged/*, train_ready/*.parquet (incl. background_points), README.md |
| Docs | catalog/dictionary/README/FILES_TO_PUSH updated; build scripts added | catalog.csv, catalog.md, data_dictionary.csv, README.md, CHANGELOG.md, FILES_TO_PUSH.md, NEW scripts/build_v3.py, NEW scripts/make_docs_v3.py, qc/build_funnel.csv |

Counts v2 -> v3: clean records 6,066 -> 6,004; species 1,469 -> 1,437; recommended 3,367 -> 3,280; min10 609 rows / 43 species -> 599 / 42; >=20 tier 6 -> 6; background points 20,000 (unchanged points, new columns).

## v2 (2026-10-17, Asia/Colombo)

### Issue 1: v1 GBIF file was reptiles, not fish (CRITICAL)
- **Cause:** v1 queried GBIF with `classKey=11592253`, which is **Squamata** (lizards and snakes), believing it was Actinopterygii. As a result all 22,140 rows of v1 `gbif/gbif_srilanka_fish.csv` were reptiles, and so were 3,730 of the 7,355 rows in v1 merged and train_ready (Varanidae, Agamidae, Gekkonidae, Colubridae …). The FishBase merge did not flag this, because reptiles simply got no FishBase match.
- **Verified keys:** GBIF 204 = Actinopterygii, 121 = Elasmobranchii, 120 = Holocephali, 119 = Myxini, 11881065 = Petromyzonti, 238 = Sarcopterygii, 11592253 = Squamata. OBIS 10194 = Actinopterygii, 10193 = Elasmobranchii, 10196 = Holocephali, 10189 = Myxini.
- **Finding:** `classKey=204` returns **0** GBIF occurrences in the box. The GBIF backbone leaves `class` empty for ray-finned fish (for example, *Thunnus albacares* has class=null, order=Perciformes). This is why the class facet never offered a fish key.
- **Fix:** GBIF was re-pulled on 2026-10-17 with one query per chordate order with an empty class (48 orders; Copelata, a tunicate order, excluded) plus classKey 121. Same polygon, `hasGeospatialIssue=false`, `hasCoordinate=true`. That gives 12,728 raw fish rows: 12,326 Actinopterygii and 402 Elasmobranchii. Holocephali, Myxini and Petromyzonti have 0 records in GBIF for this box.
- OBIS: the 9,412 v1 rows were all verified as Teleostei using WoRMS (1,791/1,791 names). 251 Elasmobranchii, Holocephali and Myxini rows were added. `class` and `order` columns were added.
- **Hard validation** was added to `scripts/build.py`: a class allowlist, fossil exclusion, a drop log, and an assert that stops the build. Result: 0 non-fish rows.
- **Files:** gbif/gbif_srilanka_fish.csv, obis/obis_srilanka_fish.csv, merged/*, train_ready/features.parquet, species_list.csv, catalog.*, data_dictionary.csv, scripts/build.py, scripts/make_docs.py, qc/taxonomy_class_summary.csv, qc/taxonomy_validation_dropped.csv, qc/gbif_query_scope_by_order.csv, qc/build_funnel.csv, qc/dropped_missing_coord_date_species.csv. Outside this folder: /workspace/fish-factors-v2-species-flags/species_demersal_trawl_flags.csv.

### Issue 2: long tail of species
- `species_list.csv` gained these columns: genus, order, class, fish_group, n_obis, n_gbif, n_citizen_science, n_specimen, first_year, last_year, record_count_recommended, model_eligible_10, model_eligible_20, model_tier.
- New file `train_ready/features_recommended_min10.parquet` contains species with ≥10 recommended records.
- New label columns `label_genus`, `label_family`, `label_order` and `fish_group` support coarser modelling.
- **Files:** species_list.csv, train_ready/features.parquet, train_ready/features_recommended.parquet, train_ready/features_recommended_min10.parquet, data_dictionary.csv.

### Issue 3: presence-only bias
- New flags: `obs_type`, `is_citizen_science`, `is_specimen`, `pre_1980`, `obis_on_land_flag`, `bathy_ge0`, `coastal_snap` (kept), `depth_missing`, `recommended_training`.
- New `train_ready/background_points.parquet`: 10k uniform in-water points and 10k target-group points, environment-matched, with splits.
- New `train_ready/features_recommended.parquet` excludes ON_LAND and bathy≥0 rows. The full set is kept.
- The README now notes depth missingness (72.8 %).
- **basis_of_record bug fix:** GBIF enum values (PRESERVED_SPECIMEN) and lowercase OBIS values are normalised. In v1 the GBIF `bor_*` one-hots were all 0. `bor_MaterialCitation` was added.
- **Files:** merged/*, train_ready/*, README.md, data_dictionary.csv.

### Issue 4: environmental gaps
- New `sst_c_source` / `chla_mg_m3_source` columns take the values month_matched, climatology, climatology_nearest_cell or missing.
- Coastal NaN cells now fall back to the nearest valid cell's climatology (within 0.5°). Missing values drop from 938 to 6 (SST) and from 731 to 3 (chl).
- New `env/sst_monthly_climatology_2003_2026.csv` and `env/chla_monthly_climatology_2003_2026.csv`.
- The README documents that the fish-factors SST, chl, SLA, currents and SSS cover only about 24 months.
- **Files:** merged/*, train_ready/*, env/*_climatology_2003_2026.csv, README.md.

### Issue 5: GFW fishing effort
- No GFW file exists in any of our outputs, so no columns were added. The README describes how to add a `gfw_period` (pre/post 2022) flag and per-period normalisation if GFW data is added later.
- **Files:** README.md.

### Count changes v1 → v2
| | v1 | v2 |
|---|---|---|
| merged clean rows | 7,355 (3,730 reptiles) | 6,066 (all fish) |
| fish rows | 3,625 (OBIS only) | 6,066 (OBIS 3,719, GBIF 2,347): **+2,441 fish** |
| GBIF fish rows in clean set | 0 | 2,347 |
| species | 1,090 (incl. reptiles) | 1,469 fish |
| split_spatial train/val/test | 4,586 / 1,415 / 1,354 | 4,648 / 225 / 1,193 |
| split_temporal train/val/test | 1,652 / 768 / 4,935 | 3,088 / 665 / 2,313 |
| inland/land-excluded | 14,788 | 1,474 |

The spatial split blocks are reshuffled because the set of 1° blocks changed, and the blocks are now sorted before the seeded shuffle so the split is reproducible.

### Other notes
- **OBIS index drift:** today's OBIS API returns only 5,864 of the 9,412 Actinopterygii records pulled on 2026-10-16. For example, dataset 47ce299b… now returns 0 rows in the box, and the iNaturalist dataset returns fewer. v2 keeps the 9,412 v1 OBIS records (all WoRMS-verified Teleostei) and adds the new classes. All 5,864 of today's records are among the v1 IDs.
