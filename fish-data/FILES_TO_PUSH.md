# Files to push (v3)

Box root: `/workspace/fish-data-v3/`. Repo paths below are relative to the fish-data root (same layout as v1/v2; if your repo keeps it under `fish-data/`, prefix the paths with `fish-data/`). Every file is < 25 MB.

**Status is vs v2.** If the repo still has v1 or v2, pushing every `new` and `changed` file is enough. If you are setting up a repo from scratch, push **all** files listed (including `unchanged`).

| repo path | size | status vs v2 | reason |
|---|---|---|---|
| CHANGELOG.md | 0.01 MB | changed | v3 issue->file mapping |
| FILES_TO_PUSH.md | 0.00 MB | changed | this list |
| README.md | 0.01 MB | changed | v3 section |
| catalog.csv | 0.01 MB | changed | v3 files/counts |
| catalog.md | 0.03 MB | changed | v3 files/counts |
| data_dictionary.csv | 0.01 MB | changed | new columns |
| env/bathy_etopo2022.csv | 1.04 MB | unchanged | same as v2 |
| env/chla_monthly.csv | 17.97 MB | unchanged | same as v2 |
| env/chla_monthly_climatology_2003_2026.csv | 0.84 MB | unchanged | same as v2 |
| env/sst_monthly.csv | 10.87 MB | unchanged | same as v2 |
| env/sst_monthly_climatology_2003_2026.csv | 0.55 MB | unchanged | same as v2 |
| fishbase/fishbase_srilanka_species.csv | 0.32 MB | unchanged | same as v2 |
| gbif/gbif_srilanka_fish.csv | 5.94 MB | changed | + basis_of_record_norm, license_norm, license_level, class_validated_original; class harmonised |
| iotc/iotc_retained_catch_srilanka_1950_2025.csv | 1.71 MB | unchanged | same as v2 |
| merged/srilanka_fish_inland_or_land_excluded.csv | 0.77 MB | changed | same annotation columns |
| merged/srilanka_fish_occurrences_clean.csv | 3.62 MB | changed | CSV copy of the parquet |
| merged/srilanka_fish_occurrences_clean.parquet | 0.59 MB | changed | accepted names, dedupe, class harmonised, freshwater flags, license_norm, log10 chl, lagoon flag |
| obis/obis_srilanka_fish.csv | 2.99 MB | changed | + basis_of_record_norm, license_norm, license_level, class_original; class harmonised |
| obis/obis_srilanka_fish_checklist.csv | 0.13 MB | unchanged | same as v2 |
| qc/_worms_match_raw.json | 1.52 MB | new | raw WoRMS responses |
| qc/build_funnel.csv | 0.00 MB | changed | v3 steps appended |
| qc/dropped_duplicates_after_name_merge.csv | 0.01 MB | new | duplicates removed after synonym merge |
| qc/dropped_missing_coord_date_species.csv | 1.52 MB | changed | class harmonised, class_original, basis_of_record canonical |
| qc/gbif_query_scope_by_order.csv | 0.00 MB | unchanged | same as v2 |
| qc/name_resolution_worms_fishbase.csv | 0.22 MB | new | WoRMS/FishBase name resolution |
| qc/obis_dataset_licenses.csv | 0.01 MB | new | OBIS dataset licences |
| qc/taxonomy_class_summary.csv | 0.00 MB | changed | class harmonised, class_original, final_clean_rows_v3 |
| qc/taxonomy_validation_dropped.csv | 0.00 MB | changed | + class_original (0 rows) |
| research_factors.md | 0.01 MB | unchanged | same as v2 |
| scripts/build.py | 0.02 MB | unchanged | same as v2 |
| scripts/build_v3.py | 0.02 MB | new | v3 build |
| scripts/make_docs.py | 0.01 MB | unchanged | same as v2 |
| scripts/make_docs_v3.py | 0.01 MB | new | v3 docs |
| species_list.csv | 0.38 MB | changed | one row per accepted species; habitat/freshwater; FishBase link |
| train_ready/background_points.parquet | 1.33 MB | changed | + log10 chl, chla_lagoon_outlier |
| train_ready/features.parquet | 0.43 MB | changed | accepted-name labels + new columns |
| train_ready/features_recommended.parquet | 0.26 MB | changed | freshwater_only excluded; new columns |
| train_ready/features_recommended_min10.parquet | 0.07 MB | changed | rebuilt on v3 recommended (42 species) |

Plus, from `/workspace/fish-factors-v3-species-flags/`:

| repo path | box file | status | reason |
|---|---|---|---|
| fish-factors/species_flags/species_demersal_trawl_flags.csv | /workspace/fish-factors-v3-species-flags/species_demersal_trawl_flags.csv (0.35 MB) | changed | 1,437 accepted species; habitat_salinity/freshwater_only; FishBase SpecCode linkage; trawl_target_likely excludes freshwater_only |
| fish-factors/species_flags/README_v3.md | /workspace/fish-factors-v3-species-flags/README.md | new | how the v3 flags were built |
| fish-factors/species_flags/build_flags_v3.py | /workspace/fish-factors-v3-species-flags/scripts/build_flags.py | new | build script |

## Old v1 files that MUST be replaced (they contain reptile records or pre-v3 names)
Overwrite each of these with the v3 file at the same path:

- `fish-data/merged/srilanka_fish_occurrences_clean.parquet`, `fish-data/merged/srilanka_fish_occurrences_clean.csv`, `fish-data/merged/srilanka_fish_inland_or_land_excluded.csv` (v1 = ~48 % reptiles)
- `fish-data/gbif/gbif_srilanka_fish.csv` (v1 = 100 % reptiles)
- `fish-data/species_list.csv` (v1 top species were lizards)
- `fish-data/train_ready/features.parquet` (v1 = ~48 % reptiles)
- `fish-factors/species_flags/species_demersal_trawl_flags.csv` (v1 built from the reptile list)
- `fish-data/obis/obis_srilanka_fish.csv`, `catalog.csv`, `catalog.md`, `data_dictionary.csv`, `README.md`, `scripts/build.py`, `scripts/make_docs.py` (describe v1)

## Delete
Nothing needs deleting: every v1 file path still exists in v3 and is overwritten. Do not keep any v1 copy of the files above under another name.

## Unchanged since v1 (no need to re-push if already in the repo)
`obis/obis_srilanka_fish_checklist.csv`, `fishbase/fishbase_srilanka_species.csv`, `iotc/iotc_retained_catch_srilanka_1950_2025.csv`, `env/sst_monthly.csv`, `env/chla_monthly.csv`, `env/bathy_etopo2022.csv`, `research_factors.md`.
