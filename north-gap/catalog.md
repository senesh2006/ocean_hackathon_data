# North Sri Lanka AIS-gap: alternative data catalog
Built 2026-10-23, OSM layer updated 2026-10-24 (Asia/Colombo). Gap box: 8.5–10.5°N, 78.9–81.5°E.

Why this folder exists: GFW AIS fishing hours (`../Fishing_sl.csv`) show almost no activity in northern Sri Lanka (≈1% of national hours) even though the north has ~33% of marine catch and ~46% of boats — most northern boats are small FRP craft with no AIS. These tables are alternative, non-AIS evidence of northern fishing effort.

Every table is provided as both CSV and Parquet (same content; row counts checked equal). Raw downloads (`raw/`) are **not** included in the repo; see *Excluded* below.

## Evidence of the gap (`north_gap_summary_2024.csv/.parquet`)
| Metric | North | National | North % |
|---|---|---|---|
| GFW AIS fishing hours 2024 (repo Fishing_sl.csv) | 6,854.69 | 696,972.64 | 1.0 |
| Marine catch 2024 t (Bulletin T4.4, 5 northern districts) | 102,715 | 308,430 | 33.3 |
| Operating boats 2024 (T3.2) | 22,483 | 49,271 | 45.6 |
| Small-scale boats 2024 | 21,211 | 43,522 | 48.7 |
| Multi-day IMUL boats 2024 | 657 | 4,869 | 13.5 |
| Active marine fishers 2024 (T1.5) | 86,150 | 225,480 | 38.2 |
| Rousseau 2017 artisanal APW kW-days, LKA | 20,455,537 | 54,985,666 | 37.2 |
| Rousseau 2017 subsistence UP kW-days, LKA | 3,058,148 | 7,868,257 | 38.9 |
Northern districts = Jaffna, Kilinochchi, Mannar, Mullaitivu, Trincomalee (district ≠ bbox exactly).

## Files
| File | Source | Licence | Rows | Notes |
|---|---|---|---|---|
| bulletin2025_t3_2_3_3_boats_by_district.* | MoF Annual Fisheries Statistical Bulletin 2025 (PDF already in repo, pp.36–37) | Govt of Sri Lanka publication (no explicit licence; cite source) | per district × boat type, 2024 final + 2025 provisional | Totals validated 49,271 / 59,180 |
| bulletin2025_t1_5_active_fishers_by_district.* | Same bulletin p.20 | Govt of Sri Lanka publication (no explicit licence; cite source) | per district | Totals validated 225,480 (2024) / 226,154 (2025) |
| nsdi_fish_landing_centres_harbours.* | NSDI Sri Lanka ArcGIS REST, Economy_Structure MapServer layers 4 & 5 | none stated on service | 75 landing centres (2 no geometry) + 26 harbours | 13 landing centres + 5 harbours in bbox. Partial: MoF cites 931 minor landing centres |
| osm_fishing_sites_srilanka.* | OSM Overpass | © OpenStreetMap contributors, ODbL 1.0 (attribution + share-alike) | 747 (367 fishing-related; 58 in bbox) | Updated 2026-10-24: merged a second Overpass pull extended to 10.6°N (Point Pedro / Jaffna coast), +172 elements. First pull (to 10.0°N) not included |
| rousseau2017_artisanal_effort_0p5_srilanka_rows.* / _cells.* | Rousseau et al. 2024 Sci Data, IMAS portal mapped_2017_APW/UP | Creative Commons per IMAS record (confirm exact variant before redistribution) | 11,882 rows (_srilanka_rows); 161 rows = 71 cells (0.5°) × sector × flag (_cells) | lat 5–11, lon 78.5–82.5; LKA (144) + IND (356). Industrial file (7.8 GB) not fetched; a partial industrial download was discarded and is not included |
| sau_lka_eez144_catch_by_year_entity_sector_gear.* | Sea Around Us v50.1, EEZ 144 | CC BY-NC-SA 4.0 | 1,587 | 1950–2019, EEZ-level only (no cells) |
| north_gap_summary_2024.* | Derived: repo Fishing_sl.csv + bulletin tables + Rousseau | Mixed (inherits sources) | 9 | North vs national metrics shown above |
| dashboard_data.json | Derived from the tables above + repo Fishing_sl.csv + Natural Earth 10m coastline (public domain) | Mixed (inherits sources) | 11 keys: timeline, north_monthly_2024, ais_cells (378), districts (15), nsdi (28), osm (87), rousseau (57), sau_years/sau_sector/sau_entity, coast | Data feed for the north-gap dashboard |

## Scripts
| Script | Builds | Inputs |
|---|---|---|
| build_bulletin.py | bulletin2025_* tables | `../srilanka-fisheries-official/raw/Annual-Fisheries-Statistical-Bulletin-2025.pdf` (path in script is the box clone; adjust) |
| build_gap_summary.py | north_gap_summary_2024.* | `../Fishing_sl.csv`, `../srilanka-fisheries-official/bulletin2025_t4_4_marine_catch_by_fisheries_district.csv`, bulletin tables |
| build_nsdi.py | nsdi_fish_landing_centres_harbours.* | raw/nsdi_*.geojson (NSDI ArcGIS REST export; not in repo) |
| build_osm.py | osm_fishing_sites_srilanka.* | raw/osm_fishing_sites.json (Overpass export; not in repo) |
| build_rousseau.py | rousseau2017_* | raw/rousseau_2017_{APW,UP}_srilanka.csv (IMAS subsets; not in repo) |
| build_sau.py | sau_lka_eez144_* | raw/sau/SAU EEZ 144 v50-1.csv (Sea Around Us download; not in repo) |
| build_dashboard_data.py | dashboard_data.json | tables above, repo files, raw/basemap/ne_10m_coastline.geojson (not in repo) |
| fetch_gfw_sar_north.py | gfw_sar_north_monthly_0p1.* (not yet produced) | GFW 4Wings API, public-global-sar-presence:latest (v5); data GFW CC BY-NC 4.0. Not run yet (needs GFW_TOKEN env var) |

## How to run the SAR fetch
`GFW_TOKEN=... python3 fetch_gfw_sar_north.py` (token read from env, never printed) → `gfw_sar_north_monthly_0p1.csv/.parquet`, 0.1° monthly, matched (AIS) vs unmatched (dark) detections.

## Caveats
- GFW pipeline v5 (released 2026-10-21) is now `latest`; v5 fishing hours are materially lower than v4 → the repo's Fishing_sl.csv may not match a fresh pull.
- Repo AIS north hours by year: 2018 240.0, 2019 22.5, 2020 0, 2021 1.0, 2022 473.3, 2023 2,542.5, 2024 6,854.7 — regime change in 2022 nationally too.
- SAR detects mostly larger vessels (≳15 m); misses small FRP boats which dominate north.
- VIIRS VBD needs free EOG account login — not fetched.
- Rousseau effort ends 2017, yearly, 0.5°; IND cells in box include Indian side of Palk Bay.

## Excluded from the repo
- `raw/` (all raw downloads/caches: NSDI geojson, OSM Overpass JSON incl. the first pull `osm_fishing_sites_v1_to10N.json`, Rousseau APW/UP subsets, Sea Around Us zip/CSV, Natural Earth basemap).
- `raw/PARTIAL_INCOMPLETE_rousseau_2017_I_srilanka.csv` (truncated industrial-effort download — unusable).
- The local zip bundle. No tokens/secrets are stored anywhere in this folder; the SAR script reads `GFW_TOKEN` from the environment only.

## Licence notes
Sea Around Us data CC BY-NC-SA 4.0; OSM ODbL 1.0; GFW CC BY-NC 4.0; Rousseau et al. via IMAS (Creative Commons — confirm variant); MoF bulletin and NSDI: government sources, no explicit licence stated. Treat the folder as **non-commercial** use overall.
