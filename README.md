# ocean_hackathon_data

Sri Lanka ocean and fisheries datasets for **Ocean Hackathon / SplitWater (GAL02)**.

| Path | Summary |
|------|---------|
| **[DATA.md](DATA.md)** | **Full data dictionary** — file types, columns, licences, and how datasets relate |
| [`Fishing_sl.csv`](Fishing_sl.csv) | Global Fishing Watch monthly fishing hours on a 0.1° grid (61,420 rows) |
| [`fish-data/`](fish-data/) | Fish occurrences (OBIS, GBIF), FishBase & IOTC reference tables, env grids, merged clean set, ML Parquet |
| [`fish-factors/`](fish-factors/) | Environmental & habitat factors for trawl / distribution models (SST, chl-a, wind, WOA23, moon, monsoon, reefs, species flags) |

**Quick start:** read [DATA.md](DATA.md). Package notes: [`fish-data/README.md`](fish-data/README.md), [`fish-factors/README.md`](fish-factors/README.md).

**Scope:** occurrence and env grids use lat 4–11°N, lon 77–85°E (bounding box, not exact EEZ).

Maintainer: [senesh2006](https://github.com/senesh2006).
