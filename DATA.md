# Data reference — `ocean_hackathon_data`

Sri Lanka / Indian Ocean datasets for Ocean Hackathon (SplitWater, GAL02).  
**Study box (occurrence + env grids):** latitude 4°–11°N, longitude 77°–85°E (rectangle, not the exact EEZ).  
**Built:** 2026-10-16 (`fish-data`; `fish-factors` parts 1–2, complete). **Maintainer:** Senesh ([senesh2006](https://github.com/senesh2006)).

Machine-readable indexes: `fish-data/catalog.csv`, `fish-factors/catalog.csv`, column defs in each package’s `data_dictionary.csv`, `fish-data/species_list.csv`.

---

## Repository layout

```
ocean_hackathon_data/
├── README.md                 ← start here (short index)
├── DATA.md                   ← this file (schemas and types)
├── Fishing_sl.csv            ← fishing effort (AIS / GFW), monthly grid
├── srilanka-banned-marine/   ← banned/restricted species & gear–area rules
├── fish-factors/             ← env + habitat covariates (trawl / SDM; 22 catalogued files)
│   ├── sst/, chlorophyll/, wind/, sea_level_eddies/, currents/, salinity_surface/
│   ├── bottom_temp_salinity_oxygen_woa23/, mixed_layer_depth/, rainfall/
│   ├── climate_indices/, moon_phase/, monsoon_calendar/
│   ├── seabed_shelf_habitat/, coral_reefs_avoid/, species_flags/, scripts/
│   └── catalog.csv, data_dictionary.csv, README.md
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
| **CSV** | Most tables and ERDDAP exports | UTF-8 text; comma-separated; some ERDDAP bathy files have a units row on line 2 |
| **Parquet** | `fish-data/merged/`, `fish-data/train_ready/`, `fish-factors/seabed_shelf_habitat/` | Columnar binary; use pandas/pyarrow |
| **GeoJSON** | `fish-factors/coral_reefs_avoid/` | UNEP-WCMC reef polygons |
| **Python** | `fish-data/scripts/`, `fish-factors/scripts/` | Download, merge, and regenerate docs |

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
| `fish-data/env/*` | **Ocean fields** (long history) | Grid | Monthly / static | Used in `build.py` merged set |
| `fish-factors/*` | **Richer env + habitat** | Grid / vector / species | Daily–monthly + climatologies | Trawl models, extra covariates |

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

## 10. Environmental factors — `fish-factors/`

**Type:** Gridded and tabular **covariates** for trawl or species-distribution models. Complements `fish-data/env/` (which only has longer SST/chl/bathy used in `build.py`). Join to occurrences on `(year, month)` and nearest grid cell — see `fish-factors/README.md`.

**Area:** same box (4–11°N, 77–85°E). ERDDAP longitudes may appear as 0–360° (equivalent to 77–85°E).

**Column-level detail:** `fish-factors/data_dictionary.csv` (every column per file).

### 10.1 Complete file inventory

| File | Dataset | Resolution | Rows (approx.) | Date range |
|------|---------|------------|----------------|------------|
| `sst/crw_sst_monthly_last24m_0.05deg.csv` | NOAA CRW SST v3.1 | 0.05°, monthly | 590,226 | 2024-08 – 2026-09 |
| `chlorophyll/esa_cci_chla_monthly_last24m_4km.csv` | ESA OC-CCI chl-a v6 | ~4 km, monthly | 782,808 | 2024-07 – 2026-06 |
| `wind/blended_winds_monthly_2014_latest.csv` | NOAA blended 10 m winds | 0.25°, monthly | 136,851 | 2014-01 – 2025-01 |
| `wind/blended_windstress_monthly_2014_latest.csv` | Wind stress τ | 0.25°, monthly | 147,378 | 2014-01 – 2026-01 |
| `sea_level_eddies/sla_daily_last24m.csv` | Sea level anomaly | 0.25°, daily | 581,856 | 2024-10 – 2026-09 |
| `currents/surface_currents_daily_last24m.csv` | Surface u/v currents | 0.25°, daily | 695,739 | 2024-10 – 2026-09 |
| `salinity_surface/smap_sss_daily_last24m.csv` | SMAP sea surface salinity | 0.25°, daily | 637,362 | 2024-11 – 2026-09 |
| `bottom_temp_salinity_oxygen_woa23/woa23_temperature_monthly_clim_0.25deg.csv` | WOA23 temperature climatology | 0.25°, monthly clim. | 8,436 | months 1–12 |
| `bottom_temp_salinity_oxygen_woa23/woa23_salinity_monthly_clim_0.25deg.csv` | WOA23 salinity climatology | 0.25°, monthly clim. | 8,436 | months 1–12 |
| `bottom_temp_salinity_oxygen_woa23/woa23_oxygen_monthly_clim_1.00deg.csv` | WOA23 oxygen climatology | 1°, monthly clim. | 492 | months 1–12 |
| `mixed_layer_depth/mld_from_woa23_temperature_monthly_clim_0.25deg.csv` | Mixed layer depth (0.5 °C) | 0.25°, monthly clim. | 8,436 | months 1–12 |
| `rainfall/chirps_v2_monthly_srilanka_land_0.05deg_2024_latest.csv` | CHIRPS rainfall (land) | 0.05°, monthly | 79,744 | 2024-01 – 2026-08 |
| `rainfall/chirps_island_mean_monthly.csv` | CHIRPS island mean | monthly | 32 | 2024-01 – 2026-08 |
| `rainfall/gpcp_v23_monthly_2.5deg.csv` | GPCP v2.3 land + ocean | 2.5°, monthly | 11,400 | 1979-01 – 2026-06 |
| `rainfall/gpcp_monthly_climatology_2.5deg.csv` | GPCP climatology | 2.5° | 240 | climatology |
| `climate_indices/dmi_oni_monthly.csv` | IOD (DMI) + ENSO (ONI) | basin index | 1,880 | 1870 – 2026-05 |
| `moon_phase/moon_daily_2000_2027_colombo_midnight.csv` | Moon phase (PyEphem) | daily | 10,227 | 2000 – 2027 |
| `monsoon_calendar/srilanka_monsoon_calendar.csv` | Monsoon / rough sea / upwelling | by month | 12 | climatology |
| `seabed_shelf_habitat/shelf_habitat_grid_1arcmin_water.csv` | Depth, slope, trawl flags (water) | 1 arc-min | 162,835 | static |
| `seabed_shelf_habitat/shelf_habitat_grid_1arcmin.parquet` | Same grid incl. land | 1 arc-min | 202,501 cells | static |
| `coral_reefs_avoid/unep_wcmc_coral_reefs_v4_1_srilanka.geojson` | Coral reef polygons | vector | 79 features | static |
| `species_flags/species_demersal_trawl_flags.csv` | Demersal / trawl-target flags | per species | 1,090 | static |

Source URLs and licence strings: `fish-factors/catalog.csv`.

### 10.2 Common column patterns

| Pattern | Example columns | Files |
|---------|-----------------|-------|
| ERDDAP time series | `time`, `latitude`, `longitude`, value | SST, chl, wind, SLA, currents, SMAP |
| WOA23 climatology | `month`, `lat`, `lon`, depth-level temps/salinity/O₂ | `woa23_*.csv`, MLD |
| Tabular index | month or species keys + flags | monsoon, climate indices, species_flags |
| Habitat grid | `lat`, `lon`, `depth_m`, `slope_deg`, `shelf_lt200m`, `trawl_candidate`, … | seabed CSV / Parquet |

**Value columns (selected):** `sea_surface_temperature` (°C), `chlor_a` (mg m⁻³), `windspeed` / `u_wind` / `v_wind`, `x_tau` / `y_tau`, `sla` (m), `u_current` / `v_current` (m s⁻¹), `sss` (PSU).

### 10.3 Gaps and refresh

CoastWatch ERDDAP did not return all months for every product (wind ends ~2025-01; SLA missing ~Apr–Jul 2026; coastal SMAP often NaN). See **Known gaps** in `fish-factors/README.md`. Re-download: `fish-factors/scripts/dl_erddap.py`, gap fill: `fill_gaps.py`.

**Licences:** NOAA public domain (most CoastWatch / WOA); ESA CCI CC-BY 4.0; UNEP-WCMC reefs non-commercial ([doi:10.34892/t2wk-5t34](https://doi.org/10.34892/t2wk-5t34)); FishBase-derived flags CC-BY-NC.

---

## 11. Regulations — `srilanka-banned-marine/`

**Type:** Curated **legal/regulatory reference** (not legal advice). Built 2026-10-16. Confirm with [DFAR](https://fisheriesdept.gov.lk/fisheries-regulation/) and current Gazettes before operational use.

| File | Rows | Description |
|------|------|-------------|
| `srilanka_banned_restricted_marine_species.csv` / `.parquet` | 90 | Species, genus, or groups with ban, size limit, season, or export restrictions |
| `gear_area_rules.csv` / `.parquet` | 9 | Method and area rules (e.g. **bottom trawling ban** under FARA Amendment Act No. 11 of 2017) |
| `scripts/species_input.py`, `build.py` | — | Curated entries; WoRMS matching; `in_occurrence_dataset` flag vs `fish-data/species_list.csv` |

**Key columns (species table):** `scientific_name`, `worms_valid_name`, `worms_aphia_id`, `restriction_type`, `details`, `legal_instrument`, `gazette_number_and_date`, `trawl_bycatch_risk`, `in_occurrence_dataset`, `notes`.

**Key columns (gear/area):** `rule`, `details`, `legal_instrument`, `gazette_number_and_date`, `source_url`.

Full column list: `srilanka-banned-marine/data_dictionary.csv`. Method and caveats: `srilanka-banned-marine/README.md`.

---

## 12. Related repos

| Repo | Role |
|------|------|
| [splitwater-redesign](https://github.com/Ocean-Hackathon-Futoura/splitwater-redesign) | App; consumes `Fishing_sl.csv` via API for fish likelihood |
| [Ocean-Hackathon-Futoura/data-source](https://github.com/Ocean-Hackathon-Futoura/data-source) | Team mirror of `fish-data/`, `fish-factors/`, and `Fishing_sl.csv` |
