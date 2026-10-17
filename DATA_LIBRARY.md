# Data library — ocean_hackathon_data v3.0.0

**Canonical repository:** <https://github.com/senesh2006/ocean_hackathon_data> (maintainer: Senesh Fernando, [@senesh2006](https://github.com/senesh2006)).
This is the single authoritative home of every file listed below. Releases are git tags on `main` (`v3.0.0` = current).

| Index | What it gives you |
|---|---|
| [`data_library.csv`](data_library.csv) / [`data_library.parquet`](data_library.parquet) | **One row per tracked file** (141 files): path, dataset, description, format, size, rows, SHA-256, source, SPDX licence, licence URL, `commercial_use_ok`, attribution, version, git commits, date retrieved, status, `superseded_by`, licence notes |
| [`LICENSE`](LICENSE) · [`LICENSES/`](LICENSES/) | Repository licence and full texts of MIT, CC BY 4.0, CC BY-NC 4.0, CC BY-SA 4.0, CC0 1.0 |
| [`CITATION.cff`](CITATION.cff) | How to cite (GitHub shows a “Cite this repository” button) |
| [`CHANGELOG.md`](CHANGELOG.md) | Version history (v1 reptile bug → v2 → v3) |
| [`scripts/build_data_library.py`](scripts/build_data_library.py) | Regenerates `data_library.*` (checksums, sizes, rows, licences) |
| package `catalog.csv` / `data_dictionary.csv` | Per-package file catalog and column definitions |

## Canonical repo and related repositories

| Repository | Role | Status |
|---|---|---|
| **[senesh2006/ocean_hackathon_data](https://github.com/senesh2006/ocean_hackathon_data)** | **Canonical**: all versions, tags, releases, data library | current (v3.0.0) |
| [Ocean-Hackathon-Futoura/data-source](https://github.com/Ocean-Hackathon-Futoura/data-source) | Team organisation repo: candidate data-sources catalogue (README by the team, started 2026-10-04) plus a **manual copy of the v1 bundle** (`Fishing_sl.csv`, `fish-data/`, `fish-factors/`, `srilanka-banned-marine/`; 65 files, last push 2026-10-16 23:13 Asia/Colombo) | **Related, not a mirror.** It is not a git fork or an automatic mirror, and it is not kept in sync. Its `fish-data/` files are byte-identical to v1 here (the GBIF, merged and train_ready files contain reptiles). It has no v2/v3 data, genetics, morphology or tagging. **Do not take data from it.** |

If the organisation repo is ever refreshed, copy from a tagged release here, and keep `data_library.csv` so its SHA-256 values can be checked.

## Datasets

| Folder | What it is | Main sources | Licence (most restrictive) | Commercial use |
|---|---|---|---|---|
| `fish-data/` (v3) | Validated **fish-only** occurrences for Sri Lankan waters (6,004 clean records, 1,437 species), env grids (SST, chl-a, bathymetry plus climatologies), ML tables (`train_ready/`, 20,000 background points), FishBase checklist, IOTC catch, QC audit | OBIS, GBIF, WoRMS, FishBase, NOAA CRW, ESA OC-CCI, ETOPO 2022, IOTC | Per-record CC0 / CC BY / **CC BY-NC**, so occurrence, merged and training files are non-commercial as a whole; FishBase-derived files are CC BY-NC | **no** for records and FishBase files. A commercial subset is possible by filtering `license_norm` to CC0-1.0 or CC-BY-4.0. Env, IOTC and WoRMS files: yes |
| `fish-factors/` | Ocean and habitat covariates: SST, chl-a, winds, SLA, currents, SMAP SSS, WOA23 bottom T/S/O₂, MLD, CHIRPS and GPCP rainfall, DMI/ONI, moon, monsoon, seabed/trawl grid, coral reefs, species trawl flags | NOAA ERDDAP, ESA CCI, WOA23, UCSB CHIRPS, GPCP, UNEP-WCMC, FishBase | Mostly US-Gov public domain. **UNEP-WCMC reefs (and the reef columns in the shelf grid) are non-commercial**; species flags are CC BY-NC | mostly yes; reefs, shelf grid and species flags: **no** |
| `srilanka-banned-marine/` | 90 banned/restricted species or groups plus 9 gear/area rules (bottom-trawl ban etc.). **Not legal advice** | FARA 1996 regulations and gazettes, FARA Amendment Act 11/2017, FFPO as amended by Act 22/2009, DFAR, IOTC CMMs, CITES/IUCN (context), WoRMS | CC BY 4.0 (original compilation; statutes are official texts) | yes |
| `srilanka-fish-genetics/` | 3,955 GenBank + 1,298 BOLD sequences collected in Sri Lanka (184 v3 species), FASTA plus metadata | NCBI GenBank, BOLD Systems | BOLD and its derivatives are **CC BY-SA 4.0 (share-alike)**; GenBank has no NCBI restrictions | yes (share-alike for BOLD) |
| `srilanka-fish-morphology/` | FishBase traits for all 1,437 species plus population tables (length-weight, maturity, fecundity, morphometrics) | FishBase v24.07 | **CC BY-NC 4.0** | **no** |
| `srilanka-fish-movement-tagging/` | Documentation only: how to request IOTC / Movebank / OBIS-SEAMAP / OTN tagging data | n/a | CC BY 4.0 (docs) | yes |
| `Fishing_sl.csv` | Global Fishing Watch fishing hours, 0.1° monthly, 2012–2024 (61,420 rows) | GFW BigQuery export (per DATA.md) | **CC BY-NC 4.0** (as stated in DATA.md; owner to confirm) | **no** |
| `splitwater_ro_log_1h_5s.csv` | SplitWater RO unit sample log (721 rows, 5 s interval) | **unknown** | **unknown: owner to confirm** (no licence grant until then) | unknown |
| `updated data sets/` | **Superseded** v2 partial upload (9 files). Each row in `data_library.csv` names its v3 replacement in `superseded_by` | as fish-data | as its fish-data counterpart | as counterpart |
| root docs and library files | README, DATA.md (v1-era reference), LICENSE, CITATION.cff, CHANGELOG, data library | this repo | CC BY 4.0 (docs), MIT (code) | yes |

## Licence matrix

Repository-level terms (see [`LICENSE`](LICENSE)):

1. **Original code** (`*.py`) is under **MIT**.
2. **Original compilation, documentation and metadata** are under **CC BY 4.0**.
3. **Third-party data keeps its original licence.** Where a file mixes sources, the **most restrictive** licence applies to the file as a whole: CC BY-NC parts are non-commercial, and BOLD-derived parts are CC BY-SA share-alike.

Files per licence (SPDX expression; `LicenseRef-*` are non-SPDX source terms, defined below):

| Licence | Files |
|---|---|
| `CC-BY-4.0` | 56 |
| `LicenseRef-PublicDomain-USGov` | 18 |
| `MIT` | 16 |
| `CC-BY-NC-4.0` | 15 |
| `CC0-1.0 AND CC-BY-4.0 AND CC-BY-NC-4.0` | 14 |
| `LicenseRef-LicenseText` | 6 |
| `CC-BY-SA-4.0` | 6 |
| `LicenseRef-NCBI-GenBank` | 3 |
| `LicenseRef-PublicDomain-CHIRPS` | 2 |
| `LicenseRef-PublicDomain-USGov AND LicenseRef-UNEP-WCMC-NonCommercial` | 2 |
| `LicenseRef-IOTC-Public-Acknowledge` | 1 |
| `LicenseRef-UNEP-WCMC-NonCommercial` | 1 |
| `unknown` | 1 |

`commercial_use_ok`: **yes 108 · no 32 · unknown 1** (of 141 files).

| Licence id | Meaning | Commercial | Share-alike | URL |
|---|---|---|---|---|
| `MIT` | Original code | yes | no | [LICENSES/MIT.txt](LICENSES/MIT.txt) |
| `CC-BY-4.0` | Repo compilation and docs; ESA CCI; WoRMS; OBIS checklist | yes | no | [LICENSES/CC-BY-4.0.txt](LICENSES/CC-BY-4.0.txt) |
| `CC-BY-NC-4.0` | FishBase, GFW, NC-licensed OBIS/GBIF records | **no** | no | [LICENSES/CC-BY-NC-4.0.txt](LICENSES/CC-BY-NC-4.0.txt) |
| `CC-BY-SA-4.0` | BOLD Systems and derivatives | yes | **yes** | [LICENSES/CC-BY-SA-4.0.txt](LICENSES/CC-BY-SA-4.0.txt) |
| `CC0-1.0` | Public-domain dedicated records | yes | no | [LICENSES/CC0-1.0.txt](LICENSES/CC0-1.0.txt) |
| `CC0-1.0 AND CC-BY-4.0 AND CC-BY-NC-4.0` | OBIS/GBIF-based files with **per-record** licences (`license_norm` column). Treated as NC as a whole; 25 clean records have `unknown` licence | **no** (filterable) | no | per record |
| `LicenseRef-PublicDomain-USGov` | NOAA / NASA / NCEI products (US Government works) | yes (cite) | no | https://www.usa.gov/government-copyright |
| `LicenseRef-PublicDomain-CHIRPS` | UCSB CHC CHIRPS (public domain) | yes (cite Funk et al. 2015) | no | https://www.chc.ucsb.edu/data/chirps |
| `LicenseRef-IOTC-Public-Acknowledge` | IOTC public data, acknowledgement required | yes | no | https://iotc.org/data/datasets |
| `LicenseRef-UNEP-WCMC-NonCommercial` | UNEP-WCMC General Data License | **no** | no | https://doi.org/10.34892/t2wk-5t34 |
| `LicenseRef-NCBI-GenBank` | NCBI places no restrictions; submitter claims possible | yes | no | https://www.ncbi.nlm.nih.gov/home/about/policies/ |
| `LicenseRef-LicenseText` | Verbatim licence texts | yes (unmodified) | n/a | LICENSES/ |
| `unknown` | Provenance or licence not established: **all rights reserved until confirmed** | unknown | unknown | — |

**Files with unknown licence:** `splitwater_ro_log_1h_5s.csv` only. Its timestamps (2026-10-17 10:00–11:00 +05:30) are later than its commit time (06:59 +05:30), which suggests a synthetic or sample log. The owner should confirm its origin and licence.
**Licence stated by the owner but not independently verified:** `Fishing_sl.csv` (GFW, CC BY-NC 4.0 per DATA.md).

## How to cite

Cite the library **and** the original sources of the files you use (`attribution` column in `data_library.csv`).

> Fernando, S. (2026). *ocean_hackathon_data: Sri Lanka fish occurrence, ocean environment, genetics, morphology and regulatory data library* (Version 3.0.0) [Data set]. GitHub. https://github.com/senesh2006/ocean_hackathon_data/releases/tag/v3.0.0

Key source citations: OBIS (www.obis.org) and GBIF.org (cite contributing datasets), WoRMS Editorial Board (doi:10.14284/170), Froese & Pauly (eds) FishBase v24.07, Ratnasingham & Hebert 2007 (BOLD), NCBI GenBank (cite accessions), NOAA Coral Reef Watch, ESA OC-CCI v6.0, NOAA NCEI ETOPO 2022 (doi:10.25921/fd45-gt74), WOA23 (Locarnini/Reagan/Garcia et al. 2024), Funk et al. 2015 (CHIRPS), GPCP v2.3, UNEP-WCMC coral reefs v4.1 (doi:10.34892/t2wk-5t34), IOTC Secretariat, Global Fishing Watch.

## Versioning policy

- The library uses **Semantic Versioning** with annotated git tags `vMAJOR.MINOR.PATCH` on `main`, each with a GitHub release and notes.
  - **MAJOR:** a change that breaks or invalidates earlier data, such as removed or renamed files or columns, a different record population, or a fix that changes meaning. Example: v1 → v2 removed reptiles.
  - **MINOR:** a new dataset, file or column added in a backward-compatible way. Example: a new package folder.
  - **PATCH:** documentation, metadata or licence fixes, or re-runs that don't change the data's meaning.
- The `version` column in `data_library.csv` gives the release in which each file's current content was introduced (`1.0.0`, `2.0.0`, `3.0.0 (fish-data v3)`, `3.0.0`). Package-internal labels such as fish-data `v3` stay as they are.
- `status` is one of `current`, `superseded` (kept for history; see `superseded_by`), `duplicate` or `unknown-provenance`. Files are **not deleted** when superseded, only marked.
- Tags: `v1.0.0` → `597ca80` (deprecated: reptile-contaminated fish-data), `v2.0.0` → `bba48b5` (partial v2 upload), `v3.0.0` → the merge of the data-library PR.
- On every release: run `git add -A && python scripts/build_data_library.py --check`, commit, update `CHANGELOG.md` and `CITATION.cff` (`version`, `date-released`), then tag.
- Integrity: `sha256` in `data_library.csv` lets you verify any copy, including copies in other repositories. The library files themselves (`data_library.csv/.parquet`) carry `self` instead of a hash.

## Regenerate

```bash
git add -A                                  # new files must be tracked to be listed
python scripts/build_data_library.py --check  # writes data_library.csv/.parquet; fails if a file is missing or a licence blank
```

Provenance and licence rules live in the `RULES` table in the script; descriptions come from each package's `catalog.csv`.
