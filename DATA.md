# Data reference — `ocean_hackathon_data`

Sri Lanka / Indian Ocean datasets for Ocean Hackathon (SplitWater, GAL02).  
**Study box (occurrence + env grids):** latitude 4°–11°N, longitude 77°–85°E (rectangle, not the exact EEZ).  
**Built:** 2026-10-16 (fish package). **Maintainer:** Senesh (`senesh2006`).

Machine-readable indexes: `fish-data/catalog.csv`, `fish-data/data_dictionary.csv`, `fish-data/species_list.csv`.

---

## Repository layout

```
ocean_hackathon_data/
├── README.md                 ← start here (short index)
├── DATA.md                   ← this file (schemas and types)
├── Fishing_sl.csv            ← fishing effort (AIS / GFW), monthly grid
└── fish-data/
    ├── catalog.csv           ← one row per file (counts, licences, QC)
    ├── data_dictionary.csv   ← merged + ML column definitions
    ├── species_list.csv      ← 1,090 species in clean marine set
    ├── obis/                 ← raw OBIS occurrences + checklist
    ├── gbif/                 ← raw GBIF occurrences
    ├── fishbase/             ← Sri Lanka country species table
    ├── iotc/                 ← retained catch by fleet (no coordinates)
    ├── env/                  ← SST, chlorophyll, bathymetry grids
    ├── merged/               ← cleaned occurrences + exclusions
    ├── train_ready/          ← ML feature table (Parquet)
    └── scripts/              ← build.py, make_docs.py
```

---

## File formats

| Format | Where used | Notes |
|--------|------------|--------|
| **CSV** | Most tables and ERDDAP exports | UTF-8 text; comma-separated |
| **Parquet** | `merged/*.parquet`, `train_ready/features.parquet` | Columnar binary; use pandas/pyarrow |
| **Python** | `fish-data/scripts/` | Regenerate merged + docs (needs pandas, pyarrow) |

---

## 1. Fishing effort — `Fishing_sl.csv`

**Type:** Gridded **activity** (hours), not catch or species presence.  
**Source:** Global Fishing Watch, BigQuery export (`sl_fishing.effort_monthly_v3`), Sri Lanka area.  
**Licence:** [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) (GFW terms apply).  
**Rows:** 61,420 cell-months · **Grid:** 0.1° × 0.1° · **Time:** monthly (`month`).

| Column | Type | Description |
|--------|------|-------------|
| `month` | date (YYYY-MM-DD) | First day of month |
| `latitude` | float | Cell centre latitude (°N) |
| `longitude` | float | Cell centre longitude (°E) |
| `fishing_hours` | float | Total fishing hours (all gear/types in export) |
| `longline_hours` | float | Longline fishing hours |
| `lka_hours` | float | Sri Lanka–flagged vessel hours |

**Use with:** SplitWater fish likelihood model (`splitwater-redesign`, labels 2022–2024).  
**Caveat:** AIS-tracked vessels only; effort jumps ~2022 when transmission increased — not a real “500× more fishing” signal.

---

## 2. Raw occurrence records

### 2.1 `fish-data/obis/obis_srilanka_fish.csv`

**Type:** Point **presence** records (Actinopteri via OBIS API v3).  
**Licence:** Per-row (`license` column): CC0, CC-BY, or CC-BY-NC.  
**Rows:** 9,412 · **Species:** 1,610 · **Dates:** 1755–2026.

| Column | Description |
|--------|-------------|
| `id` | OBIS occurrence ID |
| `scientificName`, `species`, `family` | Taxonomy (WoRMS-backed) |
| `decimalLatitude`, `decimalLongitude` | WGS84 coordinates |
| `eventDate`, `date_year` | Observation date |
| `depth` | Depth (m) if reported |
| `basisOfRecord` | e.g. HumanObservation, PreservedSpecimen |
| `datasetName`, `dataset_id`, `institutionCode` | Provenance |
| `flags` | OBIS QC flags (semicolon-separated) |
| `license` | Record licence |

### 2.2 `fish-data/gbif/gbif_srilanka_fish.csv`

**Type:** Point **presence** (Actinopterygii; API filter `hasGeospatialIssue=false`).  
**Licence:** Per-row (`license`).  
**Rows:** 22,140 · **Species:** 314 · **Dates:** 1846–2026.

| Column | Description |
|--------|-------------|
| `key` | GBIF occurrence key |
| `scientificName`, `species`, `family`, `vernacularName` | Taxonomy |
| `decimalLatitude`, `decimalLongitude` | WGS84 |
| `coordinateUncertaintyInMeters` | Horizontal uncertainty |
| `depth`, `eventDate`, `year`, `month` | Sample metadata |
| `basisOfRecord`, `datasetKey`, `datasetName`, `institutionCode` | Provenance |
| `license`, `issues` | Licence and remaining GBIF issue flags |

### 2.3 `fish-data/obis/obis_srilanka_fish_checklist.csv`

**Type:** Species **checklist** for the same box (not point records).  
**Rows:** 1,791 taxa.

| Column | Description |
|--------|-------------|
| `scientificName`, `taxonRank`, `family`, `order` | Taxonomy |
| `records` | Occurrence count in OBIS for this box |
| `is_marine`, `category` | Habitat / grouping |
| `acceptedNameUsageID` | WoRMS accepted name ID |

---

## 3. Reference tables (no coordinates)

### 3.1 `fish-data/fishbase/fishbase_srilanka_species.csv`

**Type:** Country **checklist** (FishBase `C_Code = 144`, mirror v24.07).  
**Licence:** CC-BY-NC 4.0 (FishBase).  
**Rows:** 1,201 species records.

Key fields for linking: `Genus`, `Species`, `FBname`, `Status`, `CurrentPresence`, `Freshwater` / `Brackish` / `Saltwater_*`, `DepthRangeShallow`, `DepthRangeDeep`, `DemersPelag`, `Importance_y`. Full FishBase country-table schema — see column headers in file.

### 3.2 `fish-data/iotc/iotc_retained_catch_srilanka_1950_2025.csv`

**Type:** **Annual retained catch** (metric tonnes), Sri Lanka fleet, IOTC nominal catch dataset.  
**Licence:** Public; cite IOTC.  
**Rows:** 6,782 · **Years:** 1950–2025 · **No lat/lon.**

| Column | Description |
|--------|-------------|
| `YEAR` | Calendar year |
| `FISHING_GROUND_CODE`, `FISHING_GROUND` | IOTC area |
| `FLEET_CODE`, `FLEET` | Fleet segment |
| `FISHERY_*`, `GEAR_*` | Fishery and gear classification |
| `SPECIES_*`, `SPECIES_SCIENTIFIC` | Species group / name |
| `FATE_*` | Retained vs other fate |
| `CATCH` | Catch (tonnes) |

**Use as:** Long-term trend or prior for tunas/billfish — not point labels for occurrence models.

### 3.3 `fish-data/species_list.csv`

**Type:** Derived **index** of species in the clean marine merged set.  
**Rows:** 1,090.

| Column | Description |
|--------|-------------|
| `scientific_name`, `family` | Taxonomy |
| `record_count` | Records in merged clean set |
| `sources` | OBIS and/or GBIF |
| `common_name` | From FishBase when available |
| `fishbase_sri_lanka_status` | FishBase country status |
| `DemersPelag` | Demersal / pelagic habit |

---

## 4. Environmental grids — `fish-data/env/`

Subsampled from NOAA OceanWatch ERDDAP over the study box. Same box as occurrences unless noted.

### 4.1 `sst_monthly.csv`

**Product:** NOAA Coral Reef Watch SST v3.1, monthly.  
**Licence:** Public domain (NOAA).  
**Rows:** 273,702 (time × lat × lon).

| Column | Description |
|--------|-------------|
| `time` | Month (datetime) |
| `latitude`, `longitude` | Grid cell (°) |
| `sea_surface_temperature` | SST (°C) |

**Coverage:** 2002-12 – 2026-09.

### 4.2 `chla_monthly.csv`

**Product:** ESA OC-CCI chlorophyll-a v6.0, monthly.  
**Licence:** CC-BY 4.0 (ESA CCI).  
**Rows:** 269,874.

| Column | Description |
|--------|-------------|
| `time` | Month |
| `latitude`, `longitude` | Grid cell (°) |
| `chlor_a` | Chlorophyll-a (mg m⁻³) |

**Coverage:** 2003-01 – 2026-06.

### 4.3 `bathy_etopo2022.csv`

**Product:** NOAA ETOPO 2022 global relief (0.05° subsample).  
**Licence:** Public domain (NCEI).  
**Rows:** 22,701.

| Column | Description |
|--------|-------------|
| `latitude`, `longitude` | Grid cell (°); row 2 in file is ERDDAP unit labels — skip when loading |
| `z` | Elevation/bathymetry (m); negative = below sea level |

---

## 5. Derived occurrence tables — `fish-data/merged/`

Built by `fish-data/scripts/build.py` from raw OBIS + GBIF + `env/`.

### 5.1 `srilanka_fish_occurrences_clean.csv` / `.parquet`

**Type:** Primary **clean marine presence** table with matched environment.  
**Rows:** 7,355 · **Species:** 1,090 · **Dates:** 1900-07-02 – 2026-10-05.

**Cleaning rules (summary):** drop missing date, coordinates, or species; drop out-of-box; drop bad GBIF coordinates; drop inland / on-land (> ~5 km from water via ETOPO mask); dedupe on species + lat/lon (3 dp) + date; attach SST, chlorophyll (month + climatology fallback), bathymetry.

| Column | Description |
|--------|-------------|
| `source` | `OBIS` or `GBIF` |
| `record_id` | Source ID |
| `scientific_name`, `species`, `family` | Taxonomy |
| `lat`, `lon` | WGS84 |
| `coord_uncertainty_m` | GBIF uncertainty (NaN for OBIS) |
| `depth_m` | Reported sample depth |
| `basis_of_record`, `dataset`, `license`, `qc_flags` | Metadata |
| `date`, `year`, `month` | Event time |
| `bathy_depth_m` | ETOPO seafloor depth at point (m); 0 if coastal snap |
| `coastal_snap` | 1 if on coastline land cell within ~5 km of water |
| `sst_c`, `sst_c_clim` | Monthly SST and climatology (°C) |
| `chla_mg_m3`, `chla_mg_m3_clim` | Chlorophyll and climatology |

### 5.2 `srilanka_fish_inland_or_land_excluded.csv`

**Type:** Records **removed** from the clean set (freshwater, land-located, etc.).  
**Rows:** 14,788 · **Species:** 432. Same column schema as clean set where applicable. For audit only — not used in `train_ready/`.

---

## 6. ML table — `fish-data/train_ready/features.parquet`

**Type:** One row per clean occurrence with encoded features, labels, and train/val/test splits.  
**Rows:** 7,355 · **Format:** Parquet.

**Features (examples):** `lat`, `lon`, `year`, `month`, `month_sin`, `month_cos`, `bathy_depth_m`, `log_bathy`, `sst_filled`, `log_chla`, `coord_uncertainty_m`, `depth_m`, `bor_*` (basis-of-record one-hot), `src_obis`, `coastal_snap`, `spatial_block_1deg`.

**Labels:** `label_species`, `label_id`.

**Splits:**

| Column | Rule |
|--------|------|
| `split_spatial` | train / val / test by 1° block (seed 42) |
| `split_temporal` | train &lt; 2012, val 2012–2017, test ≥ 2018 |

Full column list: `fish-data/data_dictionary.csv` (`in_merged` = in clean CSV; extra columns = ML-only).

```python
import pandas as pd
df = pd.read_parquet("fish-data/train_ready/features.parquet")
```

---

## 7. How the datasets differ

| Dataset | What it measures | Space | Time | Good for |
|---------|------------------|-------|------|----------|
| `Fishing_sl.csv` | Boat fishing **hours** (AIS) | 0.1° grid | Monthly 2012+ | Effort hotspots, SplitWater v1 labels |
| OBIS / GBIF raw | **Species seen** at a point | Points | Variable | Raw exploration, re-processing |
| Merged clean | Species presence + **env** at point | Points | 1900–2026 | Species distribution / SDM |
| IOTC | **Catch tonnes** by fleet/area | No points | Annual 1950–2025 | Stock trends, priors |
| FishBase | **Checklist** / traits | Country | — | Names, habitat, depth ranges |
| `env/*` | **Ocean fields** | Grid | Monthly / static | Covariates, re-matching |

**Presence-only:** occurrence files do not mean “species absent elsewhere.” Pair with background or pseudo-absence methods for SDMs (see `fish-data/README.md`).

---

## 8. Licences (short)

| Asset | Licence |
|-------|---------|
| `Fishing_sl.csv` | GFW — CC BY-NC 4.0 |
| OBIS / GBIF rows | Per-record in `license` column |
| FishBase table | CC-BY-NC 4.0 |
| IOTC catch | Public (acknowledge IOTC) |
| NOAA SST / ETOPO | Public domain |
| ESA chlorophyll | CC-BY 4.0 |
| Derived merged / Parquet | Inherits source record licences |

Redistribute or commercial use: check each source before republishing.

---

## 9. Regenerating derived files

From `fish-data/` (after refreshing raw downloads — see `fish-data/README.md`):

```bash
pip install pandas pyarrow
python scripts/build.py
python scripts/make_docs.py
```

Updates `merged/`, `train_ready/`, `catalog.*`, and `species_list.csv`.

---

## 10. Related repos

| Repo | Role |
|------|------|
| [splitwater-redesign](https://github.com/Ocean-Hackathon-Futoura/splitwater-redesign) | App; consumes `Fishing_sl.csv` via API for fish likelihood |
| [Ocean-Hackathon-Futoura/data-source](https://github.com/Ocean-Hackathon-Futoura/data-source) | Team mirror of `fish-data/` + `Fishing_sl.csv` |
