# fish-factors species flags, v3
Replaces `fish-factors/species_flags/species_demersal_trawl_flags.csv` (v1 was built from a reptile-contaminated list; v2 used pre-WoRMS names).
- Input: `/workspace/fish-data-v3/species_list.csv` (1,437 WoRMS accepted fish species) + FishBase v24.07 species table (https://huggingface.co/datasets/cboettig/fishbase, `data/fb/v24.07/parquet/species.parquet`), joined on FishBase **SpecCode** (resolved via accepted name, v2 name or FishBase synonyms), not on name strings.
- Rows: 1,437. Classes: Actinopterygii 1,356, Elasmobranchii 79, Myxini 1, Holocephali 1 (asserted fish-only). FishBase-matched: 1,429 (v2: 1,407).
- New columns vs v2: names_merged, accepted_aphia_id, fb_speccode, fishbase_name, fb_link_method, habitat_salinity, habitat_salinity_detail, freshwater_only (76 species).
- Flags (same logic as v1/v2): is_demersal_or_reef (1,227), is_reef_associated, is_small_pelagic_family, shelf_depth_possible_lt200m, is_elasmobranch, fishbase_matched, trawl_target_likely (943; v3 also requires freshwater_only = 0).
- Licence: FishBase CC BY-NC 4.0 (cite Froese & Pauly, FishBase 2024); WoRMS CC BY 4.0.
- Rebuild: `python3 scripts/build_flags.py`.
