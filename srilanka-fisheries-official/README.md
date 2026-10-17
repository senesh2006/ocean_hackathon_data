# srilanka-fisheries-official

Official Sri Lankan fisheries statistics, extracted from two Ministry of Fisheries PDFs into tidy, long-format
CSV + Parquet files (each `.csv` has a `.parquet` twin with identical content). Added 2026-10-17 (Asia/Colombo).

> **Licence: none stated.** Both PDFs are Government of Sri Lanka (Ministry of Fisheries, Aquatic and Ocean
> Resources, Statistics Unit) publications with no licence statement. Cite the Ministry when you reuse them and treat
> reuse terms as unknown; ask the Ministry before republishing at scale. They are **not** covered by this repo's
> CC BY 4.0 compilation licence. The extraction scripts are MIT; the catalogs/QC notes are CC BY 4.0.

## Sources

| Source | URL | Local copy | sha256 |
|---|---|---|---|
| Annual Fisheries Statistical Bulletin 2025 (87 pages; 2025 values provisional) | <https://www.fisheries.gov.lk/wp-content/uploads/2026/10/Annual-Fisheries-Statistical-Bulletin-2025.pdf> | `raw/Annual-Fisheries-Statistical-Bulletin-2025.pdf` (6.99 MB) | `9e0a851d86530992fae440660a9ef8eff2d702bc926dc761aed0d97567720d7b` |
| Major Marine Fish Types by Commercial Group (species list; PDF created 2009) | <https://www.fisheries.gov.lk/wp-content/uploads/2026/07/fish_species_list.pdf> | `raw/fish_species_list.pdf` (145 KB) | `8a764baa2a14ab7d437b7ed22e4ddc41ce889d7c67be9b5873fdd7869541552c` |

Both retrieved 2026-10-17.

## Files

| File (csv + parquet) | Rows | What it is |
|---|---|---|
| `ministry_fish_species_list` | 91 | Commercial group → English, scientific (as printed **and** WoRMS-corrected, 20 typos fixed) and romanised Sinhala names; AphiaIDs; `is_fish` flag (list also has prawns, lobster, squid, sea cucumbers). Catalog: `ministry_fish_species_list_CATALOG.md` |
| `bulletin2025_t4_1` … `t4_11` | 64–261 each | Chapter 4 fish production: by sub-sector, district, fisheries district, commercial group (Sinhala trade names), district × group 2024/2025, inland/aquaculture, inland species groups, shrimp. Catalog: `bulletin2025_production_CATALOG.md` |
| `bulletin2025_t8_3_household_fish_consumption` | 220 | Average monthly household fish consumption by fish type (g), HIES rounds 2009/10, 2012/13, 2016, 2019 |
| `bulletin2025_t8_4_household_dried_fish_consumption` | 156 | Same for dried fish |
| `bulletin2025_t8_5_per_capita_fish_consumption` | 63 | Per capita fish consumption |
| `bulletin2025_t8_6_household_fish_expenditure` | 42 | Household fish expenditure |
| `bulletin2025_t8_1_8_2_gdp_fisheries` | 110 | Fisheries contribution to GDP |
| `bulletin2025_t6_10_dried_fish_supply` | 95 | Dried fish supply, local + imported |
| `bulletin2025_table_inventory` | 67 | Every table in the bulletin: pages, units, extractability, and which file (if any) it was extracted to |

Chapter 8 / 6.10 catalog: `bulletin2025_consumption_CATALOG.md`. Per-file index: `catalog.csv`.

## QC
- `qc_bulletin2025_ch4_totals_check.txt`, `qc_bulletin2025_consumption_checks.txt`: every value was checked against page
  renders and all totals were recomputed. All mismatches found are in the published PDF (rounding of provisional 2025
  figures, a few 2023 district rows), not extraction errors.
- Original cell text is kept (`value_as_published`, `*_as_published`); "-" is flagged, not converted to 0.

## Caveats
- 2025 is provisional; 2025 inland production (55,985 Mt) is about half of 2024 and probably partial-year.
- Tables 4.4/4.6/4.7 use the 15 DFAR **fisheries** districts; 4.2/4.3/4.9 use the 25 **administrative** districts.
- Catch tables are by commercial group, not species. Join to `ministry_fish_species_list` on the Sinhala/English
  group name to get scientific names.
- The species list is old (2009) and its Sinhala names are romanised only (no Sinhala script in the PDF).

## Scripts
`scripts/build_ministry_species_list.py`, `scripts/extract_bulletin2025_ch4.py`, `scripts/check_bulletin2025_ch4.py`,
`scripts/extract_bulletin2025_ch8.py`, `scripts/build_bulletin2025_inventory.py`. They need `pdftotext` (poppler-utils)
and pandas, and have a hardcoded base path `/workspace/srilanka-fisheries-official`; change it to this folder to rerun.

## Quick load
```python
import pandas as pd
species = pd.read_parquet("srilanka-fisheries-official/ministry_fish_species_list.parquet")
catch = pd.read_parquet("srilanka-fisheries-official/bulletin2025_t4_5_marine_catch_by_commercial_group.parquet")
catch = catch[~catch["is_total"]]
```
