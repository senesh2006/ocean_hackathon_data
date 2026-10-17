# Sri Lanka fish occurrence + environment dataset (ML-ready), v3
Built 2026-10-17 from v2 plus the reviewer's fixes (`scripts/build_v3.py`, run after v2 `scripts/build.py`). **Every record is a fish** (hard assert). See `CHANGELOG.md` (issue -> file mapping) and `FILES_TO_PUSH.md` (the full file list for the repo, including which v1 files to replace).

## What changed in v3
| Fix | What was done | Result |
|---|---|---|
| 1. Freshwater-only species | `habitat_salinity` (marine / brackish / freshwater / unknown, from FishBase v24.07 Saltwater/Brack/Fresh), `habitat_salinity_detail`, `freshwater_only` (= FishBase Saltwater 0) | 76 species / 225 records flagged (reviewer's 73/214 was on v2 names; WoRMS/FishBase synonym linking matched 3 more). Kept in the full set, **removed from `recommended_training`** (53 records left the recommended set) |
| 2. basisOfRecord + licence strings | `basis_of_record` canonical CamelCase everywhere (raw OBIS had `preservedspecimen` x272, GBIF enums); `license_norm` (CC0-1.0, CC-BY-4.0, CC-BY-NC-4.0, unknown) and `license_level` | 1,398 OBIS records had **no record licence**: filled from the OBIS dataset-level licence (`qc/obis_dataset_licenses.csv`, api.obis.org/v3/dataset). Clean set: CC-BY-4.0 2,385, CC-BY-NC-4.0 2,097, CC0-1.0 1,497, unknown 25 |
| 3. Class labels | `class` Teleostei -> Actinopterygii; `class_original` kept (merged, train_ready, raw obis/gbif, qc logs, class summary) | Actinopterygii 5,766, Elasmobranchii 235, Myxini 2, Holocephali 1 |
| 4. Names | WoRMS REST `AphiaRecordsByMatchNames` for all 1,469 v2 names -> `accepted_name`, `aphia_id`, `accepted_aphia_id`, `worms_status`; FishBase SpecCode via accepted name, v2 name, or FishBase synonyms table (`fb_link_method`) | 74 names changed (e.g. Carangoides ferdau -> Ferdauia ferdau, Alectis indica -> Alectis ciliaris); 1,469 names -> **1,437 accepted species**; 62 cross-source duplicates removed after merge (`qc/dropped_duplicates_after_name_merge.csv`). FishBase link 1,429/1,437 species (8 unmatched: recently described/revalidated names not in FishBase v24.07) |
| 5. chl-a | `log10_chla_mg_m3`, `log10_chla_mg_m3_clim`, `chla_lagoon_outlier` (= chl-a month value, else climatology, > 10 mg m-3) in merged, features and background points | 14 presence records and 36 background points flagged. Climatologies were **not** rebuilt (not needed) |

**Chl-a note:** values above 10 mg m-3 sit in lagoon, estuary or turbid nearshore pixels (e.g. off Puttalam/Kalpitiya, the Mannar–Palk Bay shallows, the Batticaloa coast). Ocean-colour algorithms over-estimate chl-a in turbid, CDOM-rich water, so treat these as unreliable: use `log10` features (the distribution is strongly skewed), and either drop `chla_lagoon_outlier==1` rows or cap them.

**Name note:** `species` and `label_species` are now the WoRMS accepted name. `species_original` holds the name as published by OBIS/GBIF. FishBase and WoRMS disagree for some genera (e.g. WoRMS *Turrum*/*Platycaranx* vs FishBase *Carangoides*); `fishbase_name` gives the FishBase name. family/order are the most common value among each accepted name's records.

**Spatial split:** the v2 1-degree block -> train/val/test assignment is reused unchanged so v2 and v3 are comparable.

## v2 documentation (still applies)
Built 2026-10-17. **v2 fixes a critical v1 bug: the v1 GBIF file was entirely reptiles (Squamata), not fish.** See `CHANGELOG.md` for every change, and `FILES_TO_PUSH.md` for the files to push.
Scope: Sri Lankan waters, bounding box lat 4–11N, lon 77–85E. This is a box, not the exact EEZ polygon, so some Indian and Maldives-adjacent records fall inside it. To clip to the EEZ, use Marine Regions MRGID 8327.
Per-file details: `catalog.csv` / `catalog.md`. Columns: `data_dictionary.csv`. Species: `species_list.csv`. Audit logs: `qc/`.

## Sources and validation
| Folder | Source | License | Validation |
|---|---|---|---|
| obis/ | OBIS API v3: Actinopterygii (10194), Elasmobranchii (10193), Holocephali (10196), Myxini (10189) | per record (CC0/CC-BY/CC-BY-NC) | OBIS QC flags; class from WoRMS for every name |
| gbif/ | GBIF API, `hasGeospatialIssue=false`. Pulled once per ray-finned fish order, plus classKey 121 (Elasmobranchii) | per record | GBIF geospatial QC; `class_validated` |
| fishbase/ | FishBase country table C_Code=144 (v24.07) | CC-BY-NC | expert checklist |
| iotc/ | IOTC retained catch, Sri Lanka fleet | public, cite IOTC | IOTC Secretariat (all tuna/billfish/shark categories, all fish) |
| env/ | NOAA CRW SST v3.1 monthly, ESA OC-CCI v6 chl-a monthly (2003–2026), ETOPO 2022, plus derived monthly climatologies | public / CC-BY | operational products |

**Why GBIF is queried by order:** the GBIF backbone leaves `class` empty for ray-finned fish. As a result `classKey=204` (Actinopterygii) returns **0** occurrences, and in v1 a facet key (11592253, Squamata) was mistaken for fish. v2 pulls every chordate order in the box whose backbone class is empty. The one exception is Copelata, a tunicate order (20 records), which is excluded. v2 also pulls classKey 121. `qc/gbif_query_scope_by_order.csv` lists every order and whether it was pulled.

**Hard taxonomy check (scripts/build.py):** every row must have a class in {Actinopterygii, Actinopteri, Teleostei, Elasmobranchii, Holocephali, Chondrichthyes, Myxini, Petromyzonti, Cladistia, Sarcopterygii (fish orders only)}. Anything else, and any fossil specimen, is dropped and logged to `qc/taxonomy_validation_dropped.csv`. A failed check stops the build (assert). Result in this build: 0 non-fish rows (`qc/taxonomy_class_summary.csv`). v3: Teleostei (WoRMS/OBIS) is now harmonised to Actinopterygii in `class`; the original value is in `class_original`.

## Cleaning
Records are dropped in this order:
1. Missing date, coordinates or species (logged in `qc/dropped_missing_coord_date_species.csv`)
2. Outside the box, before 1900, or GBIF bad-coordinate issues
3. Duplicates on species + lat/lon (3 dp) + date (OBIS copy kept)
4. More than about 5 km inland (ETOPO 0.05° land mask, dilated by 1 cell). These go to `merged/..._inland_or_land_excluded.csv`.

`qc/build_funnel.csv` gives row counts after each step.

## Bias / quality flags (merged + train_ready)
- `obs_type` with `is_citizen_science` and `is_specimen`. Citizen science is detected from the dataset name (iNaturalist, observation.org …). Specimen means PreservedSpecimen or MaterialSample.
- `pre_1980`: old records, often coarse locality and georeferenced afterwards.
- `obis_on_land_flag`: OBIS QC ON_LAND. `bathy_ge0`: the ETOPO cell is land, so the record was snapped from the coast. `coastal_snap` equals `bathy_ge0` inside the clean set.
- `recommended_training` = no ON_LAND flag and bathy < 0. The full set and the recommended subset are both provided.
- **Depth missingness:** `depth_m` (recorded sample depth) is missing for **72.8 %** of clean records (GBIF 71.5 %, OBIS 73.7 %). Don't use it as a feature without imputation; use ETOPO `bathy_depth_m` instead. `depth_missing` flags these rows.
- `basis_of_record` is normalised to Darwin Core camelCase. In v1, GBIF used enum values such as PRESERVED_SPECIMEN, so the GBIF `bor_*` one-hots were all 0.

## Environment matching
`sst_c_source` / `chla_mg_m3_source` take one of these values:
- `month_matched`: the value for the record's month and cell
- `climatology`: the 2003–2026 calendar-month mean for that cell
- `climatology_nearest_cell`: the record's 0.25° cell is NaN (coastal), so the nearest valid cell within 0.5° is used
- `missing`

Every record from before 2003 uses climatology. Standalone climatology tables: `env/*_monthly_climatology_2003_2026.csv`.
**fish-factors covariates** (separate folder) cover only about 24 months for SST, chl, SLA, currents and SSS (roughly Jul/Oct 2024 to Sep 2026). Use them for the trawler/recent-conditions work, not to match historical records. For older records, use the climatologies here, or the fish-factors items that are already long-term (WOA23 climatologies, GPCP 1979+, DMI/ONI 1870+, moon 2000–2027, wind 2014+).

## Fishing effort (Global Fishing Watch)
**No GFW file exists in any of our outputs** (fish-data, fish-factors, srilanka-banned-marine; a search for GFW/fishing effort found nothing). No GFW columns were added. If you add GFW apparent fishing effort later: AIS vessel coverage and GFW's model changed over time, and the user flagged a break around 2022. Add `gfw_period = pre_2022 / post_2022`, and normalise effort within each period (for example effort / period mean for that cell, or a z-score within the period) rather than comparing raw hours across the break.

## Train-ready files (`train_ready/`)
| File | Rows | Use |
|---|---|---|
| features.parquet | 6,004 | full clean set (v3) |
| features_recommended.parquet | 3,280 | ON_LAND, bathy≥0 and freshwater_only removed (v3) |
| features_recommended_min10.parquet | 599 (42 species) | species with ≥10 recommended records; label_id re-encoded |
| background_points.parquet | 20,000 | pseudo-absence / background, in water only |

Labels: `label_species`, `label_genus`, `label_family`, `label_order`, `fish_group`, for coarser modelling of the long tail. `species_list.csv` has `record_count`, `record_count_recommended`, `model_eligible_10`, `model_eligible_20`, and `model_tier`.
Background points: 10k `uniform_water` and 10k `target_group`. Target-group points are real presence locations jittered by up to 0.1° and kept only if in water, so they carry the same sampling bias. Dates are drawn from the presences' year-month distribution, and SST/chl are matched exactly as for presences, with the same split columns.

```python
# needs pandas + pyarrow (installed on this box for system python3 (user site) and in /workspace/.venv)
import pandas as pd
pres = pd.read_parquet("train_ready/features_recommended.parquet")
bg   = pd.read_parquet("train_ready/background_points.parquet")
X = ["month_sin","month_cos","log_bathy","sst_filled","log_chla"]
sp = pres[pres.label_species=="Acanthurus lineatus"].assign(presence=1)
d  = pd.concat([sp[X+["presence","split_spatial"]], bg[bg.bg_type=="target_group"][X+["presence","split_spatial"]]])
tr, te = d[d.split_spatial=="train"], d[d.split_spatial=="test"]
```

## ML caveats
- **Presence-only data.** Use the background file, and spatial thinning (for example 1 record per species per 5 km cell). Evaluate on `split_spatial`.
- **Long tail.** 1,469 species. 589 have a single record. Only 132 have ≥10 records and 43 have ≥20 (full set); in the recommended subset 43 have ≥10 and 6 have ≥20. Model at genus or family level, or only the top species.
- **Splits are imbalanced:** spatial val has only 225 rows (few 1° blocks). Temporal test (≥2018) is large because of iNaturalist.
- **Names differ between sources.** OBIS (WoRMS) and GBIF (backbone) can use different names for one species, e.g. *Carangoides* vs newer genera, or Carangiformes vs Perciformes. Expect a few species to be split across names.
- **A few freshwater or brackish species pass the 5 km land mask** (lagoons, estuaries), e.g. *Gibelion catla*, *Etroplus maculatus*. Filter with FishBase `DemersPelag` / Fresh if you want marine only.
- **IOTC** data is annual catch with no coordinates. Use it as a prior, not as point labels.

## Rebuild
```
/workspace/.venv/bin/python scripts/build.py && /workspace/.venv/bin/python scripts/make_docs.py
```
(raw API pages expected in /tmp/gb_v2, /tmp/obis_v2, /tmp/worms; see script header)
