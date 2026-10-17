#!/usr/bin/env python3
"""Regenerate data_library.csv / data_library.parquet: one row for EVERY file tracked by git.

Usage (from the repo root):
    git add -A            # new files must be in the index to be listed
    python scripts/build_data_library.py
    python scripts/build_data_library.py --check   # fail if any tracked file is missing or a licence is blank

Computes size_bytes, rows (CSV/TSV/Parquet/FASTA/GeoJSON), sha256 per file.
Descriptions come from each package's catalog.csv where available; provenance and licence come from
the RULES table below (first matching rule wins). Edit RULES when you add a new dataset.
Licence: MIT (this script).  Data library metadata: CC BY 4.0.
"""
import csv, fnmatch, hashlib, json, os, subprocess, sys

LIBRARY_VERSION = "3.1.0"
CANONICAL_REPO = "https://github.com/senesh2006/ocean_hackathon_data"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_CSV = "data_library.csv"
OUT_PARQUET = "data_library.parquet"
SELF_FILES = {OUT_CSV, OUT_PARQUET}

LIC_URL = {
    "MIT": "https://opensource.org/license/mit",
    "CC-BY-4.0": "https://creativecommons.org/licenses/by/4.0/",
    "CC-BY-NC-4.0": "https://creativecommons.org/licenses/by-nc/4.0/",
    "CC-BY-SA-4.0": "https://creativecommons.org/licenses/by-sa/4.0/",
    "CC0-1.0": "https://creativecommons.org/publicdomain/zero/1.0/",
    "LicenseRef-PublicDomain-USGov": "https://www.usa.gov/government-copyright",
    "LicenseRef-PublicDomain-CHIRPS": "https://www.chc.ucsb.edu/data/chirps",
    "LicenseRef-IOTC-Public-Acknowledge": "https://iotc.org/data/datasets",
    "LicenseRef-UNEP-WCMC-NonCommercial": "https://doi.org/10.34892/t2wk-5t34",
    "LicenseRef-NCBI-GenBank": "https://www.ncbi.nlm.nih.gov/home/about/policies/",
    "LicenseRef-LicenseText": "LICENSES/",
    "unknown": "unknown",
}
OCC_MIX = "CC0-1.0 AND CC-BY-4.0 AND CC-BY-NC-4.0"
OCC_NOTE = ("Per-record licences (license / license_norm column). As a whole the file is CC BY-NC 4.0 "
            "(most restrictive); filter license_norm in {CC0-1.0, CC-BY-4.0} for a commercially usable subset; "
            "rows with license_norm=unknown must be treated as all-rights-reserved.")
CITE_OBIS = "OBIS (2026) Ocean Biodiversity Information System, IOC-UNESCO, www.obis.org, accessed 2026-10-17; cite contributing datasets"
CITE_GBIF = "GBIF.org (2026) GBIF Occurrence Search, https://www.gbif.org, accessed 2026-10-17; cite contributing datasets"
CITE_FB = "Froese R. & Pauly D. (eds) (2024) FishBase, version 06/2024 (v24.07), www.fishbase.org"
CITE_WORMS = "WoRMS Editorial Board (2026) World Register of Marine Species, https://www.marinespecies.org, doi:10.14284/170"
CITE_BOLD = "Ratnasingham S. & Hebert P.D.N. (2007) BOLD: The Barcode of Life Data System. Mol. Ecol. Notes 7:355-364; BOLD Systems portal.boldsystems.org"
CITE_NCBI = "Sayers E.W. et al. GenBank. Nucleic Acids Res.; NCBI nuccore, cite each accession and its publication"
CITE_SELF = "Fernando S. (2026) ocean_hackathon_data: Sri Lanka fish & ocean data library v3.0.0. " + CANONICAL_REPO
CITE_NOAA_CRW = "NOAA Coral Reef Watch (2018, updated daily) CoralTemp / CRW SST v3.1 monthly; via ERDDAP"
CITE_ESA = "Sathyendranath S. et al. (2019) ESA Ocean Colour CCI v6.0, Sensors 19:4285; via NOAA ERDDAP"
CITE_ETOPO = "NOAA NCEI (2022) ETOPO 2022 15 Arc-Second Global Relief Model, doi:10.25921/fd45-gt74"
CITE_WOA = "NOAA NCEI World Ocean Atlas 2023 (Locarnini et al. 2024; Reagan et al. 2024; Garcia et al. 2024)"
CITE_UNEP = "UNEP-WCMC, WorldFish Centre, WRI, TNC (2021) Global distribution of warm-water coral reefs v4.1, doi:10.34892/t2wk-5t34"
CITE_CHIRPS = "Funk C. et al. (2015) The climate hazards infrared precipitation with stations (CHIRPS). Sci. Data 2:150066"
CITE_GPCP = "Adler R.F. et al. (2003, updated) GPCP v2.3 monthly precipitation; data from NOAA PSL"
CITE_IOTC = "IOTC Secretariat (2025) Nominal catch dataset (IOTC-DATASETS NC), https://iotc.org"
CITE_GFW = "Global Fishing Watch (2024) fishing effort, https://globalfishingwatch.org (CC BY-NC 4.0)"

def R(pattern, **kw):
    kw["pattern"] = pattern
    return kw

# Each rule: pattern (fnmatch on repo path) -> metadata. First match wins.
RULES = [
    # ---------- data library itself ----------
    R("LICENSES/*", dataset="data-library", source_name="Creative Commons / SPDX (verbatim licence text)",
      source_url="https://creativecommons.org/licenses/ ; https://spdx.org/licenses/MIT.html",
      license="LicenseRef-LicenseText", commercial_use_ok="yes", attribution="Verbatim licence text; do not modify",
      license_note="Full licence text reproduced verbatim from the official source.", description="Full licence text"),
    R("LICENSE", dataset="data-library", source_name="ocean_hackathon_data", source_url=CANONICAL_REPO,
      license="LicenseRef-LicenseText", commercial_use_ok="yes", attribution=CITE_SELF,
      description="Repository licence: MIT (code), CC BY 4.0 (compilation/docs), third-party data keeps original licence"),
    R("scripts/build_data_library.py", dataset="data-library", source_name="ocean_hackathon_data (original code)",
      source_url=CANONICAL_REPO, license="MIT", commercial_use_ok="yes", attribution=CITE_SELF,
      description="Regenerates data_library.csv/.parquet (sha256, sizes, rows, licences) for every tracked file"),
    R("data_library.*", dataset="data-library", source_name="ocean_hackathon_data (original compilation)",
      source_url=CANONICAL_REPO, license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_SELF,
      description="Machine-readable data library: one row per tracked file with provenance, licence, checksum"),
    R("DATA_LIBRARY.md", dataset="data-library", description="Human-readable data library: datasets, licence matrix, citation, versioning, canonical repo"),
    R("CITATION.cff", dataset="data-library", description="Citation File Format metadata for citing this data library"),
    R("CHANGELOG.md", dataset="data-library", description="Repository-level version history (v1.0.0 reptile bug, v2.0.0, v3.0.0)"),
    R("README.md", dataset="root", description="Repository index README (incl. canonical-repo declaration)"),
    R("DATA.md", dataset="root", description="Full data reference written for v1 (schemas, formats, licences); counts in it predate v3"),

    # ---------- root data files added by the owner ----------
    R("Fishing_sl.csv", dataset="root/gfw-fishing-effort", source_name="Global Fishing Watch (BigQuery export sl_fishing.effort_monthly_v3, per DATA.md)",
      source_url="https://globalfishingwatch.org/our-apis", license="CC-BY-NC-4.0", commercial_use_ok="no", attribution=CITE_GFW,
      date_retrieved="2026-10-07", version="GFW effort_monthly_v3",
      license_note="Licence as stated by the owner in DATA.md (GFW terms, CC BY-NC 4.0); originally uploaded to Ocean-Hackathon-Futoura/data-source on 2026-10-06/07. Owner to confirm export terms.",
      description="GFW fishing hours on 0.1 deg monthly grid, Sri Lanka area, 2012-2024 (AIS vessels only; coverage jump ~2022)"),
    R("splitwater_ro_log_1h_5s.csv", dataset="root/splitwater-ro-log", source_name="unknown (added by owner, commit 73e2172)",
      source_url="unknown", license="unknown", commercial_use_ok="unknown", attribution="unknown - owner to confirm",
      date_retrieved="unknown", version="unknown", status="unknown-provenance",
      license_note="unknown - owner to confirm. Timestamps (2026-10-17 10:00-11:00 +05:30) are later than the commit time (06:59 +05:30), so this looks like a synthetic/sample log rather than a real device recording.",
      description="SplitWater reverse-osmosis unit sample log, 1 h at 5 s interval (GPS, conductivity, temp, pH, flow in/out)"),

    # ---------- superseded duplicates ----------
    R("updated data sets/*", dataset="updated data sets (superseded)", status="superseded", version="v2 (partial upload, commit bba48b5)",
      license_note_prefix="Superseded duplicate of the fish-data v3 file listed in superseded_by; kept for history, do not use. "),

    # ---------- package documentation / metadata (original work) ----------
    R("*/catalog.csv", description_fallback="Package catalog: one row per file with source, licence, counts"),
    R("*/catalog.md", description_fallback="Package catalog (Markdown)"),
    R("*/data_dictionary.csv", description_fallback="Column definitions for the package's files"),
    R("*/README.md", description_fallback="Package README"),

    # ---------- fish-data ----------
    R("fish-data/obis/obis_srilanka_fish.csv", dataset="fish-data/obis", source_name="OBIS", source_url="https://api.obis.org/v3/occurrence",
      license=OCC_MIX, commercial_use_ok="no", attribution=CITE_OBIS, license_note=OCC_NOTE),
    R("fish-data/obis/obis_srilanka_fish_checklist.csv", dataset="fish-data/obis", source_name="OBIS", source_url="https://api.obis.org/v3/checklist",
      license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_OBIS, license_note="Catalog: CC-BY (OBIS) species checklist."),
    R("fish-data/gbif/*", dataset="fish-data/gbif", source_name="GBIF", source_url="https://api.gbif.org/v1/occurrence/search",
      license=OCC_MIX, commercial_use_ok="no", attribution=CITE_GBIF, license_note=OCC_NOTE),
    R("fish-data/fishbase/*", dataset="fish-data/fishbase", source_name="FishBase v24.07 (rOpenSci mirror)", source_url="https://huggingface.co/datasets/cboettig/fishbase",
      license="CC-BY-NC-4.0", commercial_use_ok="no", attribution=CITE_FB),
    R("fish-data/iotc/*", dataset="fish-data/iotc", source_name="IOTC Secretariat", source_url="https://iotc.org/data/datasets/latest/NC/ALL",
      license="LicenseRef-IOTC-Public-Acknowledge", commercial_use_ok="yes", attribution=CITE_IOTC,
      license_note="Catalog: public domain, source acknowledgement required (IOTC)."),
    R("fish-data/env/sst_*", dataset="fish-data/env", source_name="NOAA Coral Reef Watch SST v3.1 via ERDDAP", source_url="https://oceanwatch.pifsc.noaa.gov/erddap/griddap/CRW_sst_v3_1_monthly.html",
      license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution=CITE_NOAA_CRW),
    R("fish-data/env/chla_*", dataset="fish-data/env", source_name="ESA OC-CCI v6.0 via NOAA ERDDAP", source_url="https://oceanwatch.pifsc.noaa.gov/erddap/griddap/esa-cci-chla-monthly-v6-0.html",
      license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_ESA),
    R("fish-data/env/bathy_*", dataset="fish-data/env", source_name="NOAA NCEI ETOPO 2022 via ERDDAP", source_url="https://oceanwatch.pifsc.noaa.gov/erddap/griddap/ETOPO_2022_v1_60s.html",
      license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution=CITE_ETOPO),
    R("fish-data/merged/*", dataset="fish-data/merged", source_name="Derived: OBIS + GBIF + WoRMS + FishBase + NOAA/ESA env (scripts/build_v3.py)", source_url=CANONICAL_REPO,
      license=OCC_MIX, commercial_use_ok="no", attribution=CITE_SELF + "; " + CITE_OBIS + "; " + CITE_GBIF + "; " + CITE_FB,
      license_note=OCC_NOTE + " FishBase-derived columns (habitat_salinity, freshwater_only) are CC BY-NC."),
    R("fish-data/train_ready/background_points.parquet", dataset="fish-data/train_ready", source_name="Derived: ETOPO water cells + NOAA SST + ESA chl-a", source_url=CANONICAL_REPO,
      license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_SELF + "; " + CITE_ETOPO + "; " + CITE_ESA,
      license_note="Catalog: CC-BY / public (env sources). Target-group points are jittered presence locations; if you treat locations as derived from CC BY-NC records, use non-commercially."),
    R("fish-data/train_ready/*", dataset="fish-data/train_ready", source_name="Derived from fish-data/merged (scripts/build_v3.py)", source_url=CANONICAL_REPO,
      license=OCC_MIX, commercial_use_ok="no", attribution=CITE_SELF + "; " + CITE_OBIS + "; " + CITE_GBIF + "; " + CITE_FB, license_note=OCC_NOTE),
    R("fish-data/species_list.csv", dataset="fish-data", source_name="Derived: occurrences + WoRMS + FishBase names/habitat", source_url=CANONICAL_REPO,
      license="CC-BY-NC-4.0", commercial_use_ok="no", attribution=CITE_SELF + "; " + CITE_WORMS + "; " + CITE_FB,
      license_note="Contains FishBase common names/status/habitat (CC BY-NC 4.0)."),
    R("fish-data/qc/name_resolution_worms_fishbase.csv", dataset="fish-data/qc", source_name="WoRMS REST + FishBase v24.07", source_url="https://www.marinespecies.org/rest/",
      license="CC-BY-NC-4.0", commercial_use_ok="no", attribution=CITE_WORMS + "; " + CITE_FB, license_note="WoRMS parts CC BY 4.0; FishBase SpecCode/habitat parts CC BY-NC 4.0 (most restrictive applies)."),
    R("fish-data/qc/_worms_match_raw.json", dataset="fish-data/qc", source_name="WoRMS REST AphiaRecordsByMatchNames", source_url="https://www.marinespecies.org/rest/AphiaRecordsByMatchNames",
      license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_WORMS),
    R("fish-data/qc/obis_dataset_licenses.csv", dataset="fish-data/qc", source_name="OBIS dataset metadata API", source_url="https://api.obis.org/v3/dataset",
      license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_OBIS),
    R("fish-data/qc/gbif_query_scope_by_order.csv", dataset="fish-data/qc", source_name="GBIF API facets", source_url="https://api.gbif.org/v1/occurrence/search",
      license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_GBIF, license_note="Aggregate facet counts only (no records)."),
    R("fish-data/qc/taxonomy_class_summary.csv", dataset="fish-data/qc", source_name="Derived (counts)", source_url=CANONICAL_REPO,
      license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_SELF, license_note="Aggregate counts only."),
    R("fish-data/qc/build_funnel.csv", dataset="fish-data/qc", source_name="Derived (counts)", source_url=CANONICAL_REPO,
      license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_SELF, license_note="Aggregate counts only."),
    R("fish-data/qc/*", dataset="fish-data/qc", source_name="Derived audit rows from OBIS + GBIF", source_url=CANONICAL_REPO,
      license=OCC_MIX, commercial_use_ok="no", attribution=CITE_SELF + "; " + CITE_OBIS + "; " + CITE_GBIF, license_note=OCC_NOTE),
    R("fish-data/*", dataset="fish-data"),

    # ---------- fish-factors ----------
    R("fish-factors/sst/*", dataset="fish-factors/sst", source_name="NOAA Coral Reef Watch SST v3.1 via ERDDAP", license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution=CITE_NOAA_CRW),
    R("fish-factors/chlorophyll/*", dataset="fish-factors/chlorophyll", source_name="ESA OC-CCI v6.0 via NOAA ERDDAP", license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_ESA),
    R("fish-factors/wind/blended_windstress_monthly_2014_latest.csv", dataset="fish-factors/wind", source_name="NOAA NCEI Blended Sea Winds via CoastWatch ERDDAP", license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution="NOAA NCEI Blended Sea Winds; NOAA CoastWatch ERDDAP", status="current (raw; use _qc)",
      license_note="RAW download, kept unchanged. Contains upstream bad values (|tau| up to 1,323 N/m2, mostly on land-mask cells) and repeated January rows. Use blended_windstress_monthly_2014_latest_qc.csv."),
    R("fish-factors/wind/blended_winds_monthly_2014_latest.csv", dataset="fish-factors/wind", source_name="NOAA NCEI Blended Sea Winds via CoastWatch ERDDAP", license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution="NOAA NCEI Blended Sea Winds; NOAA CoastWatch ERDDAP", status="current (raw; use _qc)",
      license_note="RAW download, kept unchanged. Contains repeated January rows and values on land-mask cells. Use blended_winds_monthly_2014_latest_qc.csv."),
    R("fish-factors/wind/*_qc.csv", dataset="fish-factors/wind", source_name="NOAA NCEI Blended Sea Winds via CoastWatch ERDDAP; QC by ocean_hackathon_data (fish-factors/scripts/qc_windstress.py)", license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution="NOAA NCEI Blended Sea Winds; NOAA CoastWatch ERDDAP; " + CITE_SELF, date_retrieved="2026-10-16",
      license_note="QC'd copy of the raw file: duplicate rows removed, land-mask cells and physically impossible values set to NaN; see qc_flag."),
    R("fish-factors/wind/qc/*", dataset="fish-factors/wind/qc", source_name="Derived by qc_windstress.py from NOAA NCEI Blended Sea Winds", license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution="NOAA NCEI Blended Sea Winds; NOAA CoastWatch ERDDAP; " + CITE_SELF, date_retrieved="2026-10-17"),
    R("fish-factors/scripts/qc_windstress.py", dataset="fish-factors/scripts", source_name="ocean_hackathon_data (original code)", source_url=CANONICAL_REPO, license="MIT", commercial_use_ok="yes", attribution=CITE_SELF,
      description="QC for the NOAA blended wind and wind-stress files: writes *_qc.csv and wind/qc/ outlier lists without touching the raw files"),
    R("fish-factors/wind/*", dataset="fish-factors/wind", source_name="NOAA NCEI Blended Sea Winds via CoastWatch ERDDAP", license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution="NOAA NCEI Blended Sea Winds; NOAA CoastWatch ERDDAP"),
    R("fish-factors/sea_level_eddies/*", dataset="fish-factors/sea_level_eddies", source_name="NOAA CoastWatch blended SSH via ERDDAP", license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution="NOAA CoastWatch blended sea level anomaly; ERDDAP noaacwBLENDEDsshDaily"),
    R("fish-factors/currents/*", dataset="fish-factors/currents", source_name="NOAA CoastWatch blended NRT currents via ERDDAP", license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution="NOAA CoastWatch blended currents; ERDDAP noaacwBLENDEDNRTcurrentsDaily"),
    R("fish-factors/salinity_surface/*", dataset="fish-factors/salinity_surface", source_name="NASA/NOAA SMAP SSS via CoastWatch ERDDAP", license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution="NOAA CoastWatch / NASA SMAP sea surface salinity; ERDDAP noaacwSMAPsssDaily"),
    R("fish-factors/bottom_temp_salinity_oxygen_woa23/*", dataset="fish-factors/woa23", source_name="NOAA NCEI World Ocean Atlas 2023", license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution=CITE_WOA),
    R("fish-factors/mixed_layer_depth/*", dataset="fish-factors/mixed_layer_depth", source_name="Derived from WOA23 temperature", source_url="https://www.ncei.noaa.gov/products/world-ocean-atlas", license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution=CITE_WOA + "; " + CITE_SELF),
    R("fish-factors/rainfall/chirps*", dataset="fish-factors/rainfall", source_name="UCSB Climate Hazards Center CHIRPS v2 via IRI Data Library", source_url="https://iridl.ldeo.columbia.edu/SOURCES/.UCSB/.CHIRPS/.v2p0/.monthly/.global/", license="LicenseRef-PublicDomain-CHIRPS", commercial_use_ok="yes", attribution=CITE_CHIRPS),
    R("fish-factors/rainfall/gpcp*", dataset="fish-factors/rainfall", source_name="GPCP v2.3 via NOAA PSL", source_url="https://psl.noaa.gov/data/gridded/data.gpcp.html", license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution=CITE_GPCP),
    R("fish-factors/climate_indices/*", dataset="fish-factors/climate_indices", source_name="NOAA PSL DMI (HadISST) + NOAA CPC ONI", source_url="https://psl.noaa.gov/gcos_wgsp/Timeseries/DMI/ ; https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt", license="LicenseRef-PublicDomain-USGov", commercial_use_ok="yes", attribution="NOAA PSL Dipole Mode Index (from HadISST1.1, Met Office Hadley Centre); NOAA CPC Oceanic Nino Index", license_note="Catalog: public domain (NOAA). DMI is computed from HadISST (Met Office); cite HadISST (Rayner et al. 2003)."),
    R("fish-factors/moon_phase/*", dataset="fish-factors/moon_phase", source_name="Computed with PyEphem (original)", source_url=CANONICAL_REPO, license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_SELF, license_note="Computed astronomical values (catalog: n/a); released under the repo compilation licence."),
    R("fish-factors/monsoon_calendar/*", dataset="fish-factors/monsoon_calendar", source_name="Compiled from Dept. of Meteorology season definitions; de Vos et al. 2014", source_url="https://doi.org/10.5194/bg-11-5909-2014", license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_SELF + "; de Vos A. et al. (2014) Biogeosciences 11:5909-5930", license_note="Original compilation of published season definitions (catalog: n/a)."),
    R("fish-factors/seabed_shelf_habitat/*", dataset="fish-factors/seabed_shelf_habitat", source_name="Derived: NOAA ETOPO 2022 + UNEP-WCMC coral reefs v4.1", source_url="https://oceanwatch.pifsc.noaa.gov/erddap/griddap/ETOPO_2022_v1_60s.html", license="LicenseRef-PublicDomain-USGov AND LicenseRef-UNEP-WCMC-NonCommercial", commercial_use_ok="no", attribution=CITE_ETOPO + "; " + CITE_UNEP, license_note="Depth/slope columns are public domain; coral_reef and trawl_candidate columns are derived from UNEP-WCMC reefs (non-commercial). Drop those columns for commercial use."),
    R("fish-factors/coral_reefs_avoid/*", dataset="fish-factors/coral_reefs_avoid", source_name="UNEP-WCMC Global Distribution of Coral Reefs v4.1", source_url="https://data-gis.unep-wcmc.org/server/rest/services/HabitatsAndBiotopes/Global_Distribution_of_Coral_Reefs/FeatureServer/1", license="LicenseRef-UNEP-WCMC-NonCommercial", commercial_use_ok="no", attribution=CITE_UNEP),
    R("fish-factors/species_flags/species_demersal_trawl_flags.csv", dataset="fish-factors/species_flags", source_name="Derived from fish-data v3 species_list + FishBase", source_url=CANONICAL_REPO, license="CC-BY-NC-4.0", commercial_use_ok="no", attribution=CITE_SELF + "; " + CITE_FB, date_retrieved="2026-10-17"),
    R("fish-factors/species_flags/*", dataset="fish-factors/species_flags", date_retrieved="2026-10-17"),
    R("fish-factors/scripts/*.log", dataset="fish-factors/scripts", description="Log of the last fill_gaps.py run", license="CC-BY-4.0"),
    R("fish-factors/*", dataset="fish-factors"),

    # ---------- banned / restricted marine ----------
    R("srilanka-banned-marine/*.csv", dataset="srilanka-banned-marine",
      source_name="Compiled from Sri Lanka FARA No.2 of 1996 regulations (Shark Fisheries Mgmt Regs 2015, Gazette 1938/2; Lobster Regs 2000, Gazette 1123/2; Monofilament Nets Regs, Gazette 1454/33), FARA (Amendment) Act No.11 of 2017, Fauna & Flora Protection Ordinance as amended by Act No.22 of 2009, DFAR regulations list, IOTC CMMs 2026, CITES/IUCN listings, WoRMS",
      source_url="https://fisheriesdept.gov.lk/fisheries-regulation/ ; https://faolex.fao.org/docs/pdf/srl161923.pdf ; https://faolex.fao.org/docs/pdf/srl100103.pdf ; https://lankalaw.net/wp-content/uploads/2024/02/11-2017_E.pdf ; https://iotc.org/sites/default/files/documents/2026/09/IOTC-2026-WPEB22AS-05_-_CMMs_0.pdf ; https://checklist.cites.org ; https://www.iucnredlist.org ; https://www.marinespecies.org",
      license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_SELF + "; cite the legal instrument in each row; " + CITE_WORMS, date_retrieved="2026-10-16", version="v1 (built 2026-10-16)",
      license_note="Original compilation (CC BY 4.0). Underlying statutes/gazettes are official texts; CITES appendix and IUCN status columns are factual context, not re-queried row by row. NOT LEGAL ADVICE."),
    R("srilanka-banned-marine/*.parquet", dataset="srilanka-banned-marine", same_as_csv=True),
    R("srilanka-banned-marine/*", dataset="srilanka-banned-marine", date_retrieved="2026-10-16", version="v1 (built 2026-10-16)"),

    # ---------- genetics ----------
    R("srilanka-fish-genetics/fasta/genbank*", dataset="srilanka-fish-genetics", source_name="NCBI GenBank (nuccore, E-utilities)", source_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/", license="LicenseRef-NCBI-GenBank", commercial_use_ok="yes", attribution=CITE_NCBI, license_note="NCBI places no restrictions on use; some submitters may claim patent/copyright on specific sequences."),
    R("srilanka-fish-genetics/genbank*", dataset="srilanka-fish-genetics", source_name="NCBI GenBank (nuccore, E-utilities)", source_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/", license="LicenseRef-NCBI-GenBank", commercial_use_ok="yes", attribution=CITE_NCBI, license_note="NCBI places no restrictions on use; some submitters may claim patent/copyright on specific sequences."),
    R("srilanka-fish-genetics/qc/genbank*", dataset="srilanka-fish-genetics/qc", source_name="NCBI GenBank", source_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/", license="LicenseRef-NCBI-GenBank", commercial_use_ok="yes", attribution=CITE_NCBI),
    R("srilanka-fish-genetics/raw/genbank_query.json", dataset="srilanka-fish-genetics/raw", source_name="NCBI query log (original)", source_url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/", license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_SELF),
    R("srilanka-fish-genetics/raw/portal_*", dataset="srilanka-fish-genetics/raw", source_name="BOLD Systems Data Portal API", source_url="https://portal.boldsystems.org/api", license="CC-BY-SA-4.0", commercial_use_ok="yes", attribution=CITE_BOLD, license_note="Share-alike: derived datasets must be released under CC BY-SA 4.0."),
    R("srilanka-fish-genetics/fasta/bold*", dataset="srilanka-fish-genetics", source_name="BOLD Systems Data Portal API", source_url="https://portal.boldsystems.org/api", license="CC-BY-SA-4.0", commercial_use_ok="yes", attribution=CITE_BOLD, license_note="Share-alike: derived datasets must be released under CC BY-SA 4.0."),
    R("srilanka-fish-genetics/bold*", dataset="srilanka-fish-genetics", source_name="BOLD Systems Data Portal API", source_url="https://portal.boldsystems.org/api", license="CC-BY-SA-4.0", commercial_use_ok="yes", attribution=CITE_BOLD, license_note="Share-alike: derived datasets must be released under CC BY-SA 4.0."),
    R("srilanka-fish-genetics/species_barcode_coverage.csv", dataset="srilanka-fish-genetics", source_name="Derived: BOLD + GenBank + fish-data v3", source_url=CANONICAL_REPO, license="CC-BY-SA-4.0", commercial_use_ok="yes", attribution=CITE_SELF + "; " + CITE_BOLD + "; " + CITE_NCBI, license_note="Derived from BOLD CC BY-SA data, so share-alike applies."),
    R("srilanka-fish-genetics/qc/sequenced_taxa*", dataset="srilanka-fish-genetics/qc", source_name="Derived: BOLD + GenBank", source_url=CANONICAL_REPO, license="CC-BY-SA-4.0", commercial_use_ok="yes", attribution=CITE_SELF + "; " + CITE_BOLD + "; " + CITE_NCBI, license_note="Derived from BOLD CC BY-SA data, so share-alike applies."),
    R("srilanka-fish-genetics/*", dataset="srilanka-fish-genetics"),

    # ---------- morphology ----------
    R("srilanka-fish-morphology/coverage_stats.csv", dataset="srilanka-fish-morphology", source_name="Derived counts from FishBase v24.07", source_url=CANONICAL_REPO, license="CC-BY-4.0", commercial_use_ok="yes", attribution=CITE_SELF + "; " + CITE_FB, license_note="Aggregate coverage counts only (catalog: n/a)."),
    R("srilanka-fish-morphology/*.csv", dataset="srilanka-fish-morphology", source_name="FishBase v24.07 (rOpenSci mirror)", source_url="https://huggingface.co/datasets/cboettig/fishbase/tree/main/data/fb/v24.07/parquet", license="CC-BY-NC-4.0", commercial_use_ok="no", attribution=CITE_FB),
    R("srilanka-fish-morphology/population_tables/*", dataset="srilanka-fish-morphology/population_tables", source_name="FishBase v24.07 (rOpenSci mirror)", source_url="https://huggingface.co/datasets/cboettig/fishbase/tree/main/data/fb/v24.07/parquet", license="CC-BY-NC-4.0", commercial_use_ok="no", attribution=CITE_FB),
    R("srilanka-fish-morphology/*.parquet", dataset="srilanka-fish-morphology", source_name="FishBase v24.07 (rOpenSci mirror)", source_url="https://huggingface.co/datasets/cboettig/fishbase/tree/main/data/fb/v24.07/parquet", license="CC-BY-NC-4.0", commercial_use_ok="no", attribution=CITE_FB),
    R("srilanka-fish-morphology/*", dataset="srilanka-fish-morphology"),
    R("srilanka-fish-movement-tagging/*", dataset="srilanka-fish-movement-tagging", license_note="Documentation only; no tagging data is redistributed."),
]

# Fallback by file kind (original work of this repo)
def kind_defaults(path):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".py":
        return dict(license="MIT", commercial_use_ok="yes", source_name="ocean_hackathon_data (original code)",
                    attribution=CITE_SELF)
    return dict(license="CC-BY-4.0", commercial_use_ok="yes", source_name="ocean_hackathon_data (original documentation/metadata)",
                attribution=CITE_SELF)

FORMAT = {".csv": "CSV", ".tsv": "TSV", ".parquet": "Parquet", ".md": "Markdown", ".py": "Python", ".json": "JSON",
          ".geojson": "GeoJSON", ".fasta": "FASTA", ".txt": "Text", ".log": "Text log", ".cff": "CFF (YAML)", "": "Text"}

V1_COMMITS_END = "597ca80"   # last commit of the v1 bundle (tag v1.0.0)
V2_COMMIT = "bba48b5"        # 'updated data sets' upload (tag v2.0.0)
V3_COMMIT = "92f6590"        # fish-data v3
V3_0_0_COMMIT = "92dace4"    # tag v3.0.0 (data library)

def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def count_rows(p, fmt):
    try:
        if fmt in ("CSV", "TSV"):
            csv.field_size_limit(1 << 30)
            with open(p, newline="", encoding="utf-8", errors="replace") as f:
                n = sum(1 for _ in csv.reader(f, delimiter="\t" if fmt == "TSV" else ","))
            return str(max(n - 1, 0))
        if fmt == "Parquet":
            import pyarrow.parquet as pq
            return str(pq.ParquetFile(p).metadata.num_rows)
        if fmt == "FASTA":
            with open(p, encoding="utf-8", errors="replace") as f:
                return str(sum(1 for l in f if l.startswith(">")))
        if fmt == "GeoJSON":
            return str(len(json.load(open(p)).get("features", [])))
    except Exception as e:  # noqa
        return "error:" + type(e).__name__
    return ""

def load_catalogs():
    """Map repo path -> catalog row (description, source_url, licence text, download_date)."""
    cat = {}
    for pkg in ["fish-data", "fish-factors", "srilanka-banned-marine", "srilanka-fish-genetics",
                "srilanka-fish-morphology", "srilanka-fish-movement-tagging", "updated data sets"]:
        fp = os.path.join(ROOT, pkg, "catalog.csv")
        if not os.path.exists(fp):
            continue
        for r in csv.DictReader(open(fp, encoding="utf-8")):
            rel = r.get("file_path") or r.get("file") or ""
            if pkg == "updated data sets":
                rel = os.path.basename(rel)
            cat[f"{pkg}/{rel}"] = dict(
                description=r.get("dataset_name") or r.get("dataset") or r.get("description") or "",
                source_url=r.get("source_url") or "",
                catalog_license=r.get("license_citation") or r.get("license") or r.get("sources") or "",
                date_retrieved=r.get("download_date") or r.get("built") or "")
    return cat

def match(path):
    for rule in RULES:
        if fnmatch.fnmatchcase(path, rule["pattern"]):
            return rule
    return {}

def _is_ancestor(a, b):
    return subprocess.run(["git", "merge-base", "--is-ancestor", a, b], cwd=ROOT,
                          capture_output=True).returncode == 0

def version_for(path, last_commit):
    """Library version in which the file's current content was introduced."""
    if not last_commit:
        return LIBRARY_VERSION
    if _is_ancestor(last_commit, V1_COMMITS_END):
        return "1.0.0"
    if _is_ancestor(last_commit, V2_COMMIT):
        return "2.0.0"
    if _is_ancestor(last_commit, V3_COMMIT):
        return "3.0.0 (fish-data v3)"
    if _is_ancestor(last_commit, V3_0_0_COMMIT):
        return "3.0.0"
    return LIBRARY_VERSION

COLUMNS = ["path", "dataset", "description", "format", "size_bytes", "rows", "sha256", "source_name", "source_url",
           "license", "license_url", "commercial_use_ok", "attribution", "version", "first_added_commit", "last_commit",
           "last_commit_date", "date_retrieved", "status", "superseded_by", "license_note", "catalog_license_text"]

def build():
    files = [l for l in git("ls-files", "-z").split("\0") if l]
    for sf in sorted(SELF_FILES):
        if sf not in files:
            files.append(sf)
    dirty = set()
    for l in git("status", "--porcelain", "-z").split("\0"):
        if len(l) > 3:
            dirty.add(l[3:])
    cat = load_catalogs()
    by_base = {}
    for f in files:
        if f.startswith("fish-data/") or f.startswith("fish-factors/species_flags/"):
            by_base.setdefault(os.path.basename(f), f)
    rows = []
    for path in sorted(files):
        full = os.path.join(ROOT, path)
        ext = os.path.splitext(path)[1].lower()
        fmt = FORMAT.get(ext, ext.lstrip(".").upper() or "Text")
        rule = dict(match(path))
        superseded_by = ""
        if path.startswith("updated data sets/"):
            superseded_by = by_base.get(os.path.basename(path), "")
            if superseded_by:
                base = dict(match(superseded_by))
                prefix = rule.get("license_note_prefix", "")
                base.update({k: v for k, v in rule.items() if k not in ("pattern", "license_note_prefix")})
                base["license_note"] = prefix + base.get("license_note", "")
                rule = base
        if rule.get("same_as_csv"):
            csv_rule = dict(match(path[:-len(ext)] + ".csv"))
            csv_rule.update({k: v for k, v in rule.items() if k not in ("pattern", "same_as_csv")})
            rule = csv_rule
        meta = kind_defaults(path)
        meta.update({k: v for k, v in rule.items() if k not in ("pattern", "same_as_csv", "license_note_prefix")})
        if rule.get("pattern", "").startswith("*/"):
            meta["dataset"] = os.path.dirname(path)
        c = cat.get(path, {})
        if not c and superseded_by:
            c = cat.get(superseded_by, {})
        is_self = path in SELF_FILES
        exists = os.path.exists(full)
        log = git("log", "--format=%h|%cs", "--", path).strip().splitlines()
        last_commit, last_date = (log[0].split("|") if log else ("", ""))
        if path in dirty or path in SELF_FILES:   # changed in this (uncommitted) release
            last_commit, last_date = "", ""
        first_commit = log[-1].split("|")[0] if log else ""
        lic = meta.get("license") or "unknown"
        row = dict(
            path=path,
            dataset=meta.get("dataset") or path.split("/")[0],
            description=meta.get("description") or c.get("description") or meta.get("description_fallback") or
                        {"Python": "Build / download script", "Markdown": "Documentation"}.get(fmt, "") or
                        (os.path.basename(path).replace("_", " ")),
            format=fmt,
            size_bytes=str(os.path.getsize(full)) if exists and not is_self else ("self" if is_self else "missing"),
            rows=(count_rows(full, fmt) if exists and not is_self else "") or "n/a",
            sha256=sha256(full) if exists and not is_self else ("self (not computable)" if is_self else "missing"),
            source_name=meta.get("source_name") or "unknown",
            source_url=meta.get("source_url") or c.get("source_url") or "unknown",
            license=lic,
            license_url=" ; ".join(LIC_URL.get(x.strip(), "unknown") for x in lic.split(" AND ")),
            commercial_use_ok=meta.get("commercial_use_ok") or "unknown",
            attribution=meta.get("attribution") or "unknown",
            version=meta.get("version") or version_for(path, last_commit),
            first_added_commit=first_commit or "this release",
            last_commit=last_commit or "this release",
            last_commit_date=last_date or "this release",
            date_retrieved=meta.get("date_retrieved") or c.get("date_retrieved") or "n/a (original work)",
            status=meta.get("status") or "current",
            superseded_by=superseded_by or "",
            license_note=meta.get("license_note", ""),
            catalog_license_text=c.get("catalog_license", ""),
        )
        if row["source_name"].startswith("ocean_hackathon_data") and not meta.get("source_url"):
            row["source_url"] = CANONICAL_REPO
        rows.append(row)
    return files, rows

def main():
    files, rows = build()
    with open(os.path.join(ROOT, OUT_CSV), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)
    try:
        import pandas as pd
        pd.DataFrame(rows, columns=COLUMNS).to_parquet(os.path.join(ROOT, OUT_PARQUET), index=False)
    except Exception as e:
        print("parquet skipped:", e)
    listed = {r["path"] for r in rows}
    missing = [f for f in files if f not in listed]
    blank = [r["path"] for r in rows if not r["license"].strip() or not r["commercial_use_ok"].strip()]
    print(f"{len(rows)} files listed; missing={len(missing)}; blank licence={len(blank)}")
    if "--check" in sys.argv and (missing or blank):
        print("missing:", missing, "blank:", blank)
        sys.exit(1)

if __name__ == "__main__":
    main()
