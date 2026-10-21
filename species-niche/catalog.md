# species-niche — catalog

Sri Lanka fish species niche & diet dataset. Built 2026-10-20, pushed 2026-10-21 (Asia/Colombo). Futoura / Ocean Hackathon GAL02 SplitWater. Study box lat 4–11 N, lon 77–85 E. Species key: `scientific_name` (WoRMS accepted name, same 1,437 species as `fish-data/species_list.csv` v3). Full method, coverage and caveats: `README.md`.

## Files
| file | rows × cols | what |
|---|---|---|
| `species_niche.csv` / `.parquet` | 1,437 × 146 | One row per species: taxonomy and IDs (AphiaID, FishBase SpecCode, AquaMaps ID); FishBase habitat, depth, temperature preference, trophic level, feeding type, habitat flags; AquaMaps HSPEN envelopes (depth, temperature, salinity, bottom O2, primary production, distance to land); observed local ranges (`obs_*`: n, p5/p50/p95, min/max) from the repo's records; avoided-conditions summaries (`avoid_local_summary`, `avoid_aquamaps_summary`, `avoid_fishbase_summary`); prey summaries (`prey_main_groups`, `prey_top_group`, `prey_example_taxa`, `fb_diet_top_items`, …). |
| `species_prey.csv` / `.parquet` | 48,407 × 22 | Long predator–prey table. One row per predator × prey item × source: FishBase fooditems 6,015 · FishBase diet 4,091 · GloBI eats/preysOn 38,301. Key columns: `predator_scientific_name` (joins to `species_niche.scientific_name`), `source`, `interaction_type`, `prey_name`, `prey_rank`, `prey_group`, `prey_category_l1..l3`, `prey_taxon_path`, life stages, `diet_percent_max`, `n_records`, `recorded_in_sri_lanka`, `recorded_in_study_box`, `locality_examples`, `citation`, `via_fishbase_in_globi`, `globi_query_name`. |
| `data_dictionary.csv` / `.parquet` | 168 × 7 | Every column of both tables: description, units, source, non-null count, % of species. |
| `coverage_stats.csv` / `.parquet` | 25 × 3 | How many species have each kind of data (FishBase link 99.4 %, AquaMaps 85.2 %, prey any source 70.5 %, …). |
| `work/occ_env.parquet` | 6,004 × 23 | Intermediate: each repo occurrence joined to extra env grids (WOA23 T/S/O2, MLD, slope, coral). Output of `join_env.py`, input to `build_niche.py`. Derived from repo data only. |
| `work/bg_env.parquet` | 20,000 × 21 | Same join for the repo's background points (incl. 10,000 `uniform_water`). |
| `scripts/fetch_globi.py` | – | Downloads GloBI `eats`/`preysOn` interactions per species name (accepted + FishBase name) into `raw/globi_obs/` (one JSON per name, 1,467 names). |
| `scripts/join_env.py` | – | Builds `work/*.parquet` from `fish-data/train_ready/` and `fish-factors/`. |
| `scripts/build_niche.py` | – | Builds `species_niche.*` and `species_prey.*` from `raw/` + `work/`. |
| `scripts/make_docs.py` | – | Writes `data_dictionary.csv` and `coverage_stats.csv`. |
| `README.md` | – | Method, sources, coverage, caveats. |
| `qc_summary.json` | – | Validation results and SHA-256 / size of every file in this folder. |

## Sources and licences
| source | used for | licence |
|---|---|---|
| FishBase v24.07 (rOpenSci parquet mirror, huggingface.co/datasets/cboettig/fishbase, `data/fb/v24.07/parquet`) | `fb_*` columns, FishBase prey rows | CC BY-NC 4.0 — Froese R. & Pauly D. (eds) FishBase, www.fishbase.org, version 06/2024 |
| AquaMaps HSPEN (`aquamapsdb` am.db SQLite on archive.org, as used by the `aquamapsdata` R package; tables `hspen_r`, `speciesoccursum_r`; snapshot Dec 2020) | `am_*` columns, `avoid_aquamaps_summary` | CC BY-NC 4.0 — Kaschner K. et al., AquaMaps, www.aquamaps.org |
| GloBI (api.globalbioticinteractions.org/interaction) | GloBI prey rows | Per underlying dataset; citation kept per row in `species_prey.citation`. Cite Poelen J.H. et al. 2014, Ecological Informatics |
| This repo: `fish-data` v3, `fish-factors` | `obs_*`, local avoidance, `work/` | as in `LICENSES` |

Because FishBase and AquaMaps are CC BY-NC, **the combined tables are non-commercial only**.

## Excluded from the repo: raw caches (~64 MB)
`raw/` was not pushed (FishBase parquet tables 17 MB, AquaMaps HSPEN subset 0.8 MB, GloBI JSON cache 47 MB / 1,467 files). The published tables were built from these exact snapshots (retrieved 2026-10-20).

### Regenerating the raw caches
Scripts use absolute paths (`/workspace/species_niche/` for the build folder, `/workspace/ocean_hackathon_data/` for this repo); edit `B`, `R`, `W`, `OUT` at the top of each script if your layout differs.
1. **FishBase** → `raw/fishbase/`: download `species`, `estimate`, `stocks`, `ecology`, `fooditems`, `diet`, `diet_items`, `families` `.parquet` from huggingface.co/datasets/cboettig/fishbase under `data/fb/v24.07/parquet/`.
2. **AquaMaps** → `raw/aquamaps/`: get the `aquamapsdb` (am.db) archive from archive.org (the one the `aquamapsdata` R package downloads), then export `hspen_r` and `speciesoccursum_r` rows for this repo's species (linked by FishBase SpecCode, else name) to `hspen_srilanka_subset.csv` and `speciesoccursum_srilanka_subset.csv`.
3. **GloBI** → `raw/globi_obs/`: `python scripts/fetch_globi.py` (3 polite workers, retries). GloBI changes over time, so a fresh fetch may give slightly different row counts than 38,301.
4. `python scripts/join_env.py` (optional — `work/` is included) → `python scripts/build_niche.py` → `python scripts/make_docs.py`.

## Validation (see `qc_summary.json`)
1,437 species rows (= `fish-data/species_list.csv`, no duplicates) · 48,407 prey rows (no exact duplicates, no blank prey names, every predator present in `species_niche`) · CSV and Parquet shapes identical for all four tables · data dictionary covers every column of both tables.
