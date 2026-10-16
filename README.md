# ocean_hackathon_data

Sri Lanka ocean and fisheries datasets for **Ocean Hackathon / SplitWater (GAL02)**.

| Path | Summary |
|------|---------|
| **[DATA.md](DATA.md)** | **Full data dictionary** — file types, columns, licences, and how datasets relate |
| [`Fishing_sl.csv`](Fishing_sl.csv) | Global Fishing Watch monthly fishing hours on a 0.1° grid (61,420 rows) |
| [`fish-data/`](fish-data/) | Fish occurrences (OBIS, GBIF), FishBase & IOTC reference tables, env grids, merged clean set, ML Parquet |

**Quick start:** read [DATA.md](DATA.md). For ML caveats and rebuild steps, see [`fish-data/README.md`](fish-data/README.md).

**Scope:** occurrence and env grids use lat 4–11°N, lon 77–85°E (bounding box, not exact EEZ).

Maintainer: [senesh2006](https://github.com/senesh2006).
