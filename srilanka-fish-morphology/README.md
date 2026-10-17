# Sri Lanka fish morphology & life-history traits (FishBase)
Built 2026-10-17 (Asia/Colombo) for the 1,437 accepted species in fish-data-v3. Build: `python3 scripts/build_morphology.py` (reads FishBase parquet tables cached in /tmp/fbp; re-download from the URL below).

## Source and licence
FishBase v24.07 tables via the rOpenSci mirror: https://huggingface.co/datasets/cboettig/fishbase/tree/main/data/fb/v24.07/parquet (`species`, `estimate`, `morphdat`, `morphmet`, `swimming`, `ecology`, `maturity`, `popchar`, `poplw`, `popll`, `fecundity`).
**Licence: CC BY-NC 4.0** (non-commercial). Cite: Froese, R. and D. Pauly (eds). 2024. FishBase. www.fishbase.org, version (07/2024).
Join: `scientific_name` = fish-data-v3 accepted name; `fb_speccode` = FishBase SpecCode (resolved in fish-data-v3 via WoRMS accepted name, v2 name or FishBase synonyms).

## Files
- `srilanka_fish_species_traits.csv/.parquet`: one row per species (1,437 rows, 112 columns): body shape, max/common length, max weight, depth range, trophic level, Bayesian length-weight a/b, von Bertalanffy K/Linf, preferred temperature, morphdat meristics (`md_*`, first FishBase morphology record), morphmet picture ratios (median body depth/TL, head/TL, eye/head, caudal aspect ratio), swimming mode, ecology/habitat flags (`eco_*`, FishBase coding -1 = yes, 0 = no), maturity, population max size and LW summaries.
- `population_tables/`: per-population or per-study rows (original FishBase columns + `scientific_name`, + `is_sri_lanka_population` where FishBase gives a country code): poplw 3,626 rows, popll 4,056, popchar 3,248, maturity 1,196, fecundity 406, morphdat 1,260, morphmet 1,635.

## Coverage (species of 1,437)
FishBase-linked 1,429; max length 1,393; body shape 1,427; trophic level 1,427; length-weight a/b (Bayesian) 1,421; preferred temperature 1,240; morphdat 1,178; morphmet ratios 1,103; ecology 1,103; population LW 779 (only 10 species have a Sri Lankan LW study); maturity Lm 266; swimming mode 331. See `coverage_stats.csv`.

## Caveats
- Many `estimate` values (trophic level, a/b, K) are model predictions from relatives, not measurements. Check `lw_method` and the population tables for measured values.
- morphmet measurements are in picture units; only ratios are meaningful.
- Not included: FISHMORPH (Brosse et al. 2021) covers freshwater species only, so it does not cover this marine list; it was not downloaded. No other openly licensed marine morphology dataset was added.
Columns: `data_dictionary.csv`. Files: `catalog.csv` / `catalog.md`.
