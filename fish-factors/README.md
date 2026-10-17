# fish-factors: environmental and habitat factors for a Sri Lanka trawler model
Built 2026-10-16. This is separate from `fish-data/`, which is unchanged. Area: bounding box lat 4–11N, lon 77–85E. The box also covers some Indian waters (Palk Bay, Gulf of Mannar), so clip to the Sri Lanka EEZ (Marine Regions MRGID 8327) if needed.
Coordinates are WGS84; ERDDAP longitudes are 0–360 (equivalent to 77–85E). Every file is long format: time/month, lat, lon, value. See `catalog.csv` (file, source URL, licence, resolution, rows, dates) and `data_dictionary.csv`.

## Folders
- `sst/`: NOAA Coral Reef Watch monthly SST, 0.05°, last ~24 months.
- `chlorophyll/`: ESA OC-CCI v6 monthly chlorophyll-a, ~4 km. Latest is Jun 2026, because the product lags a few months.
- `wind/`: NOAA blended winds and wind stress, monthly, 0.25°, 2014 to latest. Wind stress drives upwelling; compute climatology with groupby(month).
  **Use the `_qc.csv` files** (added 2026-10-17, `scripts/qc_windstress.py`). The raw stress file has impossible values
  (|τ| up to 1,323 N/m²) that are in the NOAA product itself, 127 of the 133 on cells the product's own mask marks as land,
  and both raw files repeat every January from 2015 on. The `_qc` files drop the repeats, set land-mask cells and
  values above 3 N/m² (per component) or 1 N/m² (monthly |τ|) to NaN, and add `mask` and `qc_flag`. Every blanked or
  removed row is in `wind/qc/windstress_outliers.csv` and `wind/qc/winds_outliers.csv`. The raw files are unchanged.
- `sea_level_eddies/`: daily sea level anomaly, 0.25°. Positive values are warm (anticyclonic) eddies; negative values are cold (cyclonic) eddies or upwelling.
- `currents/`: daily surface currents (u/v), 0.25°.
- `salinity_surface/`: SMAP daily sea surface salinity, 0.25°. Coastal cells within ~40 km of land are often missing.
- `bottom_temp_salinity_oxygen_woa23/`: World Ocean Atlas 2023 monthly climatologies at 0/50/100/200 m and near-bottom. Near-bottom means the deepest standard level with data, which on the shelf is close to the seabed.
- `mixed_layer_depth/`: MLD computed from the WOA23 temperature profiles, using a 0.5 °C criterion.
- `rainfall/`: CHIRPS over Sri Lanka land, 0.05°, Jan 2024 to latest, as a proxy for river runoff. Also GPCP v2.3 over land and sea, 2.5°, 1979 to latest, plus its climatology.
- `climate_indices/`: monthly IOD Dipole Mode Index and ENSO Oceanic Niño Index, with phase labels.
- `moon_phase/`: daily illumination, moon age and phase for 2000–2027, computed with PyEphem.
- `monsoon_calendar/`: season for each month, rough-sea flags and a rough south-coast upwelling score.
- `seabed_shelf_habitat/`: ETOPO 2022 1-arc-minute grid with depth, slope, shelf_lt200m, trawlable_depth_10_200m, upper_slope_200_1000m, coral_reef and trawl_candidate.
- `coral_reefs_avoid/`: UNEP-WCMC coral reef polygons (v4.1), for areas to avoid.
- `species_flags/`: species from fish-data/species_list with FishBase habitat type plus is_demersal_or_reef, is_small_pelagic_family and trawl_target_likely.
- `scripts/`: the scripts used to download and rebuild everything.

## Skipped or limited, and why
- **Copernicus Marine** (GLORYS, BGC: actual near-bottom temperature, salinity, oxygen and currents, plus MLD time series): needs a free account, so it was skipped. With an account, `copernicusmarine subset` on GLOBAL_ANALYSISFORECAST_PHY_001_024 and BGC_001_028 would give the best near-bottom series.
- **HYCOM** (3-D and near-bottom currents): the THREDDS server didn't respond to automated requests from the box, so it was skipped. Near-bottom currents are therefore missing.
- **ERA5** wind: needs a free account, so NOAA blended winds were used instead.
- **GPM IMERG** rainfall: needs a NASA Earthdata login, so CHIRPS and GPCP were used instead.
- **Allen Coral Atlas**: downloads need an account, so UNEP-WCMC reefs were used instead.
- **Seabed sediment / substrate**: no open, shelf-resolution dataset for Sri Lanka was found; global sediment maps cover the deep sea only. Proxies used: slope and reef flags.
- **Tides**: no open gridded tidal-current product without a login (TPXO needs registration). Sri Lanka's tidal range is under 1 m.
- **WOA climatology vs recent data**: bottom temperature, salinity and oxygen are long-term climatologies, not data for the last 24 months.

## Using with fish-data
Join on (year, month) and the nearest grid cell, as in `fish-data/scripts/build.py`. For trawl models, restrict to cells where trawl_candidate=1 and species where trawl_target_likely=1.

## Known gaps in this build (CoastWatch ERDDAP returned errors / no data)
- **Wind speed**: Jan 2014 – Jan 2025 only; Feb 2025 onward returned 404s. **Wind stress**: Jan 2014 – Jan 2026, but monthly gaps are possible (143 of ~145 months present).
- **Sea level anomaly**: Oct 2024 – Sep 2026, with 20 of 24 months present; about Apr–Jul 2026 is missing.
- **SMAP salinity**: Nov 2024 – Sep 2026; Oct 2024 is missing.
- **Currents**: all 24 months present (Oct 2024 – Sep 2026).
- **Oct 2026 (the current month)** isn't included for any of the daily products.
- To fill the gaps, re-run `scripts/fill_gaps.py`.
