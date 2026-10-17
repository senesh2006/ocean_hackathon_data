# Changelog — ocean_hackathon_data

All notable changes to this data library. Versions follow [Semantic Versioning](https://semver.org/) as described in
[DATA_LIBRARY.md § Versioning policy](DATA_LIBRARY.md#versioning-policy). Package-level detail for the fish occurrence
data is in [fish-data/CHANGELOG.md](fish-data/CHANGELOG.md). Times are Asia/Colombo (UTC+05:30).

Canonical repository: <https://github.com/senesh2006/ocean_hackathon_data>

## [3.0.0] — 2026-10-17 — fish-only validated data library

Git: fish-data v3 commit `92f6590`, merged in PR #1 (`420a92a`); data library added in PR #2. Tag `v3.0.0`.

### Added
- **Data library:** `LICENSE` (MIT for code, CC BY 4.0 for the compilation and docs, third-party data keeps its own licence),
  `LICENSES/` (full texts of MIT, CC BY 4.0, CC BY-NC 4.0, CC BY-SA 4.0 and CC0 1.0), `data_library.csv` / `.parquet`
  (one row per tracked file: source, SPDX licence, commercial-use flag, citation, SHA-256, rows, status),
  `DATA_LIBRARY.md`, `CITATION.cff`, this `CHANGELOG.md`, and `scripts/build_data_library.py` to regenerate the library.
- Canonical-repo declaration in `README.md` and `DATA_LIBRARY.md`.
- `srilanka-fish-genetics/`: 3,955 GenBank and 1,298 BOLD sequences collected in Sri Lanka (184 species with a barcode). BOLD data is CC BY-SA 4.0.
- `srilanka-fish-morphology/`: FishBase v24.07 traits for all 1,437 species plus population tables (CC BY-NC 4.0).
- `srilanka-fish-movement-tagging/`: documentation only; no open tagging data could be downloaded.
- fish-data QC files: WoRMS/FishBase name resolution, OBIS dataset licences, duplicates dropped after the name merge.

### Changed
- fish-data v3: WoRMS accepted names (74 names corrected, 62 duplicate records dropped), 76 freshwater-only species
  flagged and removed from the recommended training sets, normalised `basis_of_record` and `license_norm`, class
  harmonised to Actinopterygii, log-scaled chlorophyll and a lagoon-outlier flag. 6,004 clean records, 1,437 species,
  3,280 recommended training rows.
- The old v1 files in `fish-data/merged/`, `fish-data/species_list.csv`, `fish-data/train_ready/features.parquet` and
  `fish-factors/species_flags/` were overwritten with v3.
- `srilanka-banned-marine/catalog.csv`: the blank source fields are now filled in from the package README and scripts,
  and `source_url` and `license` columns were added.

### Deprecated
- `updated data sets/`: a partial v2 upload. Every file in it is superseded by its fish-data v3 counterpart
  (see `superseded_by` in `data_library.csv`). It is kept for history; do not use it.

### Known issues
- `splitwater_ro_log_1h_5s.csv`: the source and licence are unknown, so the owner needs to confirm them. Its timestamps
  (2026-10-17 10:00–11:00 +05:30) are later than the time it was committed (06:59 +05:30), so it looks like a sample or
  synthetic log.
- `DATA.md` still describes the v1 counts (7,355 records, 1,090 species). Use `fish-data/README.md` and `data_library.csv` for current numbers.
- The occurrence data is presence-only and biased toward the coast. Only 42 species have 10 or more recommended records.
- Most fish-factors dynamic grids (SST, chlorophyll, SLA, currents, SSS) cover only about the last 24 months.

## [2.0.0] — 2026-10-17 — GBIF reptile fix (partial upload)

Git: `bba48b5` ("Add updated datasets folder…"). Tag `v2.0.0`.

- Re-pulled GBIF as real fish (one query per ray-finned fish order plus Elasmobranchii): 12,728 raw records.
- Added hard fish-class validation, bias flags (citizen science, specimen, pre-1980, on-land), background points,
  climatology fallbacks with source labels, and model-eligibility tiers.
- **Only 9 of the v2 files were uploaded, and they went to `updated data sets/`**, so the main `fish-data/`
  tree on main still held the v1 files until v3.

## [1.0.0] — 2026-10-16 — initial bundle (DEPRECATED: reptile-contaminated)

Git: `cba22d1` … `597ca80`. Tag `v1.0.0` points at `597ca80`, the complete v1 bundle with fish-data, fish-factors
parts 1–2, srilanka-banned-marine and `Fishing_sl.csv`. (`73e2172` then added the SplitWater RO sample log.)

- **Critical bug:** the GBIF query used `classKey=11592253`, which is Squamata (lizards and snakes), not
  Actinopterygii. All 22,140 rows of v1 `gbif/gbif_srilanka_fish.csv` were reptiles, and 3,730 of the 7,355 rows
  in the v1 merged and train_ready tables were reptiles (Varanidae, Agamidae, Gekkonidae, Colubridae…).
  **Do not use v1 fish-data.** The environmental layers (`fish-factors/`, `fish-data/env/`), IOTC, FishBase and
  banned-marine files from v1 were not affected and are still current.
