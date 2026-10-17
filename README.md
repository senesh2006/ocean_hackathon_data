# ocean_hackathon_data

Public data bundle for **Ocean Hackathon 2026 — SplitWater (GAL02)**: Sri Lankan waters and fisheries-related layers for the Futuora / team dashboard and ML work.

**Study area:** lat 4°–11°N, lon 77°–85°E (bounding box; includes parts of Palk Bay / Gulf of Mannar — clip to [Sri Lanka EEZ](https://marineregions.org/) MRGID 8327 if you need national waters only).

**Maintainer:** [senesh2006](https://github.com/senesh2006) · **Team mirror:** [Ocean-Hackathon-Futoura/data-source](https://github.com/Ocean-Hackathon-Futoura/data-source) · **App:** [splitwater-redesign](https://github.com/Ocean-Hackathon-Futoura/splitwater-redesign)

---

## Canonical repository & data library

**This repository — [senesh2006/ocean_hackathon_data](https://github.com/senesh2006/ocean_hackathon_data) — is the canonical source for every dataset listed here.** Cite it, clone from it and report issues against it. Releases are tagged here (latest: [`v3.0.0`](https://github.com/senesh2006/ocean_hackathon_data/releases/tag/v3.0.0)).

- [Ocean-Hackathon-Futoura/data-source](https://github.com/Ocean-Hackathon-Futoura/data-source) is the **team organisation's repository**. It holds the candidate-sources catalogue README plus a manually copied **v1 snapshot** (last updated 2026-10-16 23:13 Asia/Colombo). It is not a git fork or an automatic mirror, and it has **no v2/v3 data**: its `fish-data/` still has the v1 reptile-contaminated GBIF, merged and train_ready files. Use this repo for data.
- **Data library:** [DATA_LIBRARY.md](DATA_LIBRARY.md) (datasets, licence matrix, how to cite, versioning) · [data_library.csv](data_library.csv) (every file: source, licence, commercial-use flag, SHA-256) · [LICENSE](LICENSE) · [CITATION.cff](CITATION.cff) · [CHANGELOG.md](CHANGELOG.md)
- **Newer packages since this README was first written:** [`srilanka-fish-genetics/`](srilanka-fish-genetics/) (GenBank + BOLD barcodes), [`srilanka-fish-morphology/`](srilanka-fish-morphology/) (FishBase traits), [`srilanka-fish-movement-tagging/`](srilanka-fish-movement-tagging/) (how to request tagging data), and `splitwater_ro_log_1h_5s.csv` (provenance unknown). `updated data sets/` is a **superseded** v2 partial upload; use `fish-data/` (v3) instead. The fish-data counts in the "What’s in this repo" table below are from v1. v3 has 6,004 clean records and 1,437 species, all fish.

---

## Start here

| Document | Purpose |
|----------|---------|
| **[DATA.md](DATA.md)** | Full reference: every file, column groups, formats, licences, how datasets relate |
| [fish-data/README.md](fish-data/README.md) | Species occurrences, cleaning, ML caveats, rebuild steps |
| [fish-factors/README.md](fish-factors/README.md) | Environmental / habitat layers, ERDDAP gaps, trawl model notes |
| [srilanka-banned-marine/README.md](srilanka-banned-marine/README.md) | Banned / restricted marine species and gear–area rules (not legal advice) |

Machine-readable indexes: each package’s `catalog.csv` and `data_dictionary.csv`.

---

## What’s in this repo

| Path | What it is | Typical use |
|------|------------|-------------|
| [`Fishing_sl.csv`](Fishing_sl.csv) | Global Fishing Watch **fishing hours** on a 0.1° monthly grid (61,420 rows, 2012–2024) | Effort labels; SplitWater fish-likelihood model (v1) |
| [`fish-data/`](fish-data/) | **Species presence** (OBIS, GBIF), FishBase & IOTC tables, env grids, merged clean set (7,355 records, 1,090 species), `train_ready/features.parquet` | SDM / species models; join with factors |
| [`fish-factors/`](fish-factors/) | **Ocean & habitat covariates** (22 data files): SST, chlorophyll, wind, SLA, currents, SMAP salinity, WOA23 bottom T/S/O₂, MLD, rainfall, moon, monsoon, IOD/ONI, seabed/trawl grid, coral reefs, species trawl flags | Trawl / distribution models; richer env than `fish-data/env/` alone |
| [`srilanka-banned-marine/`](srilanka-banned-marine/) | **Regulatory context**: 90 banned/restricted species rows + 9 gear/area rules (FARA, FFPO, IOTC, DFAR sources) | Compliance overlays, bycatch risk, route planning |

---

## Quick load

```python
import pandas as pd

effort = pd.read_csv("Fishing_sl.csv", parse_dates=["month"])
occ = pd.read_parquet("fish-data/train_ready/features.parquet")
sst = pd.read_csv("fish-factors/sst/crw_sst_monthly_last24m_0.05deg.csv")
```

Parquet needs `pyarrow` or `fastparquet`. Large ERDDAP CSVs are **long format** (`time`, `latitude`, `longitude`, value columns).

---

## Licences

Sources differ: GFW effort is **CC BY-NC 4.0**; OBIS/GBIF are **per-record**; FishBase and some derived flags are **CC BY-NC**; most NOAA CoastWatch / WOA products are **public domain**; ESA chlorophyll is **CC BY 4.0**; UNEP-WCMC reefs are **non-commercial** with citation. See [DATA.md § Licences](DATA.md#8-licences-short) before redistributing or commercial use.

---

## Repository layout (top level)

```
ocean_hackathon_data/
├── README.md          ← this file
├── DATA.md            ← data dictionary
├── Fishing_sl.csv
├── fish-data/                 ← occurrences + env grids for build.py
├── fish-factors/              ← extended environmental & habitat stack
└── srilanka-banned-marine/    ← banned/restricted species & gear rules
```

Built **2026-10-16**. Refresh scripts live under each package’s `scripts/` folder.
