# Sri Lanka fish species niche & diet dataset

Built 2026-10-20 for the Sri Lankan fish prediction project (repo `senesh2006/ocean_hackathon_data`, study box lat 4–11 N, lon 77–85 E). It gives one row per species (all 1,437 species in `fish-data/species_list.csv`, v3) describing **the conditions it lives in, the conditions it avoids, its habitat, and what it eats**, plus a long predator–prey table.

## Files
| File | Rows | Content |
|---|---|---|
| `species_niche.csv` / `.parquet` | 1,437 species × 146 columns | taxonomy and IDs, FishBase habitat/depth/temperature/trophic/feeding, AquaMaps HSPEN envelope, observed local ranges from the repo's records, avoided-conditions and prey summaries |
| `species_prey.csv` / `.parquet` | 48,407 predator–prey pairs | long format: FishBase fooditems (6,015), FishBase diet (4,091), GloBI eats/preysOn (38,301) |
| `data_dictionary.csv` | every column | description, units, source, non-null count |
| `coverage_stats.csv` | | species with each kind of data |
| `scripts/` | | `fetch_globi.py`, `join_env.py`, `build_niche.py`, `make_docs.py` (rerun in that order) |
| `catalog.md`, `qc_summary.json` | | file catalog and validation results (row counts, checks, SHA-256 per file) |
| `data_dictionary.parquet`, `coverage_stats.parquet` | | Parquet copies of the two CSVs |
| `raw/` (**not in this repo**) | | FishBase parquet tables, AquaMaps HSPEN subset, GloBI JSON cache (~64 MB). Excluded from the push; see `catalog.md` → *Regenerating the raw caches* |
| `work/` | | per-record env joins for occurrences (`occ_env.parquet`) and background points (`bg_env.parquet`) |

## Sources (all retrieved 2026-10-20)
| Source | What was used | Licence |
|---|---|---|
| FishBase v24.07, rOpenSci parquet mirror (`huggingface.co/datasets/cboettig/fishbase`, `data/fb/v24.07/parquet`) | `species` (DemersPelag, depth ranges, AnaCat, length), `estimate` (trophic level, TempPref), `stocks` (TempMin/Max, EnvTemp, resilience, IUCN), `ecology` (habitat flags, FeedingType), `fooditems`, `diet` + `diet_items` | CC BY-NC 4.0. Cite Froese R. & Pauly D. (eds) FishBase, www.fishbase.org, version 06/2024 |
| AquaMaps HSPEN (`aquamapsdb` SQLite from archive.org, as used by the `aquamapsdata` R package; table `hspen_r` + `speciesoccursum_r`) | min / preferred min / preferred max / max for depth, temperature, salinity, bottom O2, primary production, distance to land | CC BY-NC 4.0. Cite Kaschner K. et al. AquaMaps, www.aquamaps.org. **The archive snapshot dates from Dec 2020 (envelopes created 2019–2020)** |
| GloBI, Global Biotic Interactions (`api.globalbioticinteractions.org/interaction`, `interactionType=eats,preysOn`, `exactNameMatchOnly`, `includeObservations`) | prey of each species, with study citation per row | Depends on each underlying dataset; the citation is kept in `species_prey.citation`. Cite Poelen J.H. et al. 2014, Ecological Informatics, plus the datasets you use |
| Repo `fish-data` v3 + `fish-factors` | occurrences (6,004), 10,000 uniform-water background points, SST (NOAA CRW), chl-a (ESA OC-CCI), ETOPO 2022 depth, WOA23 salinity/temperature/oxygen climatologies, MLD, seabed slope and coral reef cells | as in the repo (`LICENSES`) |

Because FishBase and AquaMaps are CC BY-NC, the combined tables are **non-commercial only**.

## How the columns were built
- **IDs**: `accepted_aphia_id` and `fb_speccode` come from the repo's WoRMS/FishBase name resolution. AquaMaps is linked by SpecCode (1,224) or name (1). GloBI was queried with both the accepted name and the FishBase name, and the results were merged.
- **Observed local ranges (`obs_*`)**: each record in `train_ready/features.parquet` was matched to the repo's grids. SST and chl-a use the repo's own month-matched-else-climatology values. WOA23 and MLD use the nearest valid cell in the same calendar month (≤0.5°, or ≤1° for O2), and slope/coral use the 1-arcmin grid. For each species and variable the table gives n, p5, p50 and p95, plus min and max for SST, chl-a, depth, SSS and bottom O2. Chl-a lagoon outliers (>10 mg m-3) and coast-snapped records with ETOPO depth 0 are excluded from those variables.
- **Avoided conditions**:
  - `avoid_local_summary` covers species with **≥10 records** only (131 species). It lists any variable (seabed depth, SST, chl-a, SSS) where ≥20% of the study area's water (the 10,000 `uniform_water` background points) falls outside the species' observed min–max. This means "never observed there", not proven absence.
  - `avoid_aquamaps_summary` gives the AquaMaps absolute min/max for the parameters AquaMaps actually used. `am_frac_study_area_outside_envelope` is the share of study-area water outside them. Temperature and salinity are layer-matched: surface uses repo SST/WOA SSS, bottom uses WOA bottom T/S. For pelagic species only the minimum depth limits the seabed.
  - `avoid_fishbase_summary` gives FishBase maximum depth and the freshwater-only flag.
- **Prey groups**: FishBase items map from `FoodII`. GloBI items map from the target taxon path, falling back to keywords in the name when there is no path. `prey_main_groups` is the share of distinct prey names per group across all sources.

## Coverage (out of 1,437 species)
FishBase link 1,429 (99.4%) · habitat type 1,429 · depth range 1,193 (83%) · TempPref 1,240 (86%) · stock TempMin/Max 190 (13%) · trophic level 1,427 (874 observed, the rest model-predicted) · feeding type 857 (60%) · habitat flags 1,031 (72%)
AquaMaps envelope 1,225 (85%); oxygen was used by AquaMaps for only 54 species
Local ranges for all 1,437, but only 355 have ≥5 records, 131 have ≥10 (local avoidance) and 44 have ≥20
Prey data 1,013 (70.5%): FishBase fooditems 904, FishBase diet 393, GloBI 982. Species-level prey examples 417. Prey recorded in Sri Lanka or the study box: 40 species
Full table: `coverage_stats.csv`.

## Caveats
- **Small samples.** 589 species have one record, so their `obs_*` percentiles describe one or two points. Check `obs_reliability` and `n_records` before using local ranges.
- **Sampling bias.** Records cluster near the coast: dive sites, markets, landing sites and iNaturalist. Oceanic tunas show seabed depths of ~7 m because they are recorded where they're landed, so their local "avoids deep water" signal is a sampling artefact. For pelagic species, trust FishBase/AquaMaps over local depth.
- **Global vs local.** FishBase `TempPref*` and AquaMaps envelopes are built from global occurrence cells. They are wider than what Sri Lankan waters actually span: SST there is ~25–31 °C, so a 2–33 °C AquaMaps range rarely excludes anything locally.
- **Environment layers.** WOA23 values are monthly climatologies and SST/chl-a are partly climatology (all pre-2003 records), so they describe typical conditions, not the conditions on the day.
- **GloBI** aggregates many studies from all oceans. Some rows are FishBase-derived (`via_fishbase_in_globi`, 2,010 rows), so don't double-count them against the FishBase rows. Names are not standardised: 3,184 GloBI rows (`other/unresolved`) could not be grouped, e.g. "unidentified", "Animalia" or names without a taxon path. Some GloBI data come from aquarium or lab studies.
- **FishBase diet** items are often coarse ("bony fish", "algae"). `diet_percent_max` is the maximum across studies, not a mean.
- Nothing has been invented or imputed: a blank means the source has no value. Freshwater-only species (76) are kept and flagged (`freshwater_only`).
