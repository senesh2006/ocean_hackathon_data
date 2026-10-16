# Sri Lanka fish occurrence + environment dataset (ML-ready)
Built 2026-10-16. Scope: Sri Lankan waters, bounding box lat 4–11N, lon 77–85E. This is a box, not the exact EEZ polygon, so a few Indian / Maldives-adjacent records can fall inside it. To clip to the exact EEZ, use the Marine Regions EEZ (MRGID 8327).
Full per-file details: `catalog.csv` / `catalog.md`. Column meanings: `data_dictionary.csv`. Species: `species_list.csv`.

## Sources and validation
| Folder | Source | License | Validation |
|---|---|---|---|
| obis/ | OBIS API v3 (https://obis.org), Actinopteri | per-record (CC0/CC-BY/CC-BY-NC) | OBIS QC flags, WoRMS taxonomy |
| gbif/ | GBIF API (https://www.gbif.org), Actinopterygii, `hasGeospatialIssue=false` | per-record | GBIF geospatial QC, backbone taxonomy, `issues` |
| fishbase/ | FishBase country table C_Code=144 (v24.07, rOpenSci mirror on HuggingFace) | CC-BY-NC | expert checklist |
| iotc/ | IOTC retained catch, raw estimates, Sri Lanka fleet (https://iotc.org/data/datasets/latest/NC/ALL) | public, cite IOTC | officially reported and curated by the IOTC Secretariat |
| env/ | NOAA CRW SST v3.1 monthly, ESA OC-CCI v6 chl-a monthly, ETOPO 2022 (via NOAA OceanWatch ERDDAP) | public / CC-BY | operational QC'd products |

## Cleaning (scripts/build.py)
Records are dropped if they have no date, coordinates, or species, or fall outside the box. GBIF records with bad-coordinate issues are also dropped. Records more than about 5 km inland (ETOPO 0.05° land mask, dilated by 1 cell) go to `merged/srilanka_fish_inland_or_land_excluded.csv`; this is mostly freshwater species and land-located market or museum records. Duplicates are removed on species + lat/lon (3 dp) + date. Each record is matched to SST and chl-a for its month and nearest cell, with a monthly climatology fallback. Depth comes from ETOPO.

## Train-ready
`train_ready/features.parquet` contains: lat, lon, year, month, month_sin, month_cos, bathy_depth_m, log_bathy, sst_filled, log_chla, coord_uncertainty_m, depth_m, bor_* (basis-of-record one-hot), src_obis, coastal_snap, spatial_block_1deg, label_species, label_id, split_spatial, split_temporal.

```python
import pandas as pd
df = pd.read_parquet("train_ready/features.parquet")
X_cols = ["lat","lon","month_sin","month_cos","log_bathy","sst_filled","log_chla"]
tr = df[df.split_spatial=="train"]; te = df[df.split_spatial=="test"]
top = df.label_species.value_counts().index[:20]          # handle class imbalance
tr = tr[tr.label_species.isin(top)]
X, y = tr[X_cols].fillna(tr[X_cols].median()), tr.label_species
```

## ML caveats
- **Presence-only:** these are records of where a species was seen, not confirmed absences. Generate pseudo-absences or a background sample: random points in water cells inside the box, matched by month and with environment attached from env/. Or use target-group background, meaning other species' records as background so they carry the same sampling bias. Then fit MaxEnt / GBM / RF per species.
- **Uneven sampling effort:** records cluster near the coast, Colombo, Trincomalee and research cruises. Consider spatial thinning (for example 1 record per species per 5 km cell) and evaluate with the spatial split.
- **Class imbalance:** 1,090 species, long tail. Model the top-N species or species groups, or use class weights.
- **Time:** SST/chl exist only from 2003; earlier records use climatology. The temporal split is skewed because most records are from 2018 or later.
- **IOTC catch** is annual totals by fleet with no coordinates. Use it as a prior for tuna/billfish abundance, not as point labels.

## Refresh
1. Re-run the OBIS/GBIF API calls described in catalog.csv. For GBIF, page by year so the offset stays under 10k.
2. Re-download env/ from the ERDDAP URLs.
3. Download the latest IOTC zip.
4. Run `python scripts/build.py && python scripts/make_docs.py` (needs pandas, pyarrow).
