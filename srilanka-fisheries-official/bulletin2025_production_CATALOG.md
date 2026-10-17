# Annual Fisheries Statistical Bulletin 2025: Chapter 4 (Fish Production) tables

| | |
|---|---|
| **Publisher** | Statistics Unit, Ministry of Fisheries, Aquatic and Ocean Resources, Sri Lanka. Contributing sources per table: Department of Fisheries and Aquatic Resources (DFAR) and National Aquaculture Development Authority (NAQDA). |
| **Source URL** | https://www.fisheries.gov.lk/wp-content/uploads/2026/10/Annual-Fisheries-Statistical-Bulletin-2025.pdf |
| **Local copy** | `raw/Annual-Fisheries-Statistical-Bulletin-2025.pdf` (87 pages, 6,993,735 bytes, sha256 `9e0a851d86530992fae440660a9ef8eff2d702bc926dc761aed0d97567720d7b`) |
| **Retrieved** | 2026-10-17 (Asia/Colombo) |
| **Licence** | None stated. This is a Government of Sri Lanka publication. Cite the Ministry and check with it before redistributing the data. |
| **Coverage** | Chapter 4, Tables 4.1–4.11 (PDF pages 41–51, printed pages 27–37). Chapter 8 is handled separately. |
| **Method** | Read from the PDF text layer (`pdftotext -layout`). Each cell is assigned to a column using the fully populated Total row as an anchor. Every page was checked against a 110 dpi render (pdftoppm), and every row and column total was recomputed (`qc_bulletin2025_ch4_totals_check.txt`). Script: `scripts/extract_bulletin2025_ch4.py`. QC: `scripts/check_bulletin2025_ch4.py`. |

## Common columns (all files)
- `table_id`: bulletin table number, as a string (for example "4.10").
- `source_page_pdf`: the PDF page number.
- `year`: an integer.
- `year_status`: `provisional` where the bulletin marks the year with `*` (always 2025), otherwise `final`.
- `value`: a float. It is empty when the cell is not numeric.
- `value_as_published`: the cell exactly as printed, for example "1,240", "-", "na", "***". It is empty for a blank cell.
- `value_flag`: empty means numeric. Other values:
  - `dash`: "-" was printed. It probably means nil or not applicable, so it was not converted to 0.
  - `blank`: the cell was empty.
  - `na`: in 4.4 this means "Not available". In 4.9 the published note says it means "Negligible amount".
  - `N/A`.
  - In 4.5, `included_in_other_blood_fish (***)` and `included_in_others (**)`.
- `unit`: `Mt` (metric tonnes). The seaweed row in 4.8 uses `Mt (wet weight)`.
- `is_total`: True for Total and Sub-Total rows or columns. Filter on `is_total == False` before you aggregate.
- `source_url`.
- Names (`*_as_published`) are kept exactly as printed, including spellings like "Cannals", "Shrks/Sketes", "Travelly", "Vavunia" and "Matàra". The `*_std` columns hold a light normalisation for joins (Matàra→Matara, Tangalla→Tangalle, Mullaithivu→Mullaitivu, Vavunia→Vavuniya, Nuwara eliya→Nuwara Eliya).

## Files (each as .csv and .parquet)

| File | Table | Table-specific columns | Rows | Years |
|---|---|---|---|---|
| `bulletin2025_t4_1_fish_production_by_subsector` | 4.1 Annual fish production by fishing sub-sector | `column_group_as_published`, `subsector_as_published` (Coastal, Off shore/Deep Sea, Total Marine, Inland & Aquaculture, Total Fish Production, Estimated Wet Fish for Dry or Other Products) | 108 | 1960–2015 every 5 years, then 2020–2025 (2016–2019 not in this table) |
| `bulletin2025_t4_2_national_production_by_district` | 4.2 National fish production (marine + inland) by administrative district | `district_no`, `district_as_published`, `district_std` | 260 | 2016–2025 |
| `bulletin2025_t4_3_national_production_by_district_subsector` | 4.3 National production by district × sub-sector | `district_*`, `subsector_as_published` (Marine / Inland & Aquaculture / Total) | 234 | 2023–2025 |
| `bulletin2025_t4_4_marine_catch_by_fisheries_district` | 4.4 Marine catch by **fisheries** district (15 DFAR districts) | `fisheries_district_no/_as_published/_std` | 208 | 1983, 1990, 1995, 2000, 2005, 2010, 2015, 2020–2025 |
| `bulletin2025_t4_5_marine_catch_by_commercial_group` | 4.5 Marine catch by major commercial group | `group_no`, `fish_group_as_published` (Sinhala trade name, e.g. Thora, Balaya), `fish_group_english_as_published` (e.g. Seer, Skipjack tuna) | 140 | 2000, 2005, 2010, 2015, 2020–2025 |
| `bulletin2025_t4_6_marine_catch_district_by_group_2024` | 4.6 Marine production by fisheries district × commercial group, 2024 | `fisheries_district_*`, `fish_group_as_published` (header as printed, e.g. "Balaya (Skipjack tuna)", "Gal Ma'lu (Rock fish)") | 224 | 2024 |
| `bulletin2025_t4_7_marine_catch_district_by_group_2025` | 4.7 Same layout as 4.6, for 2025 (provisional) | same as 4.6 | 224 | 2025* |
| `bulletin2025_t4_8_inland_aquaculture_by_waterbody` | 4.8 Inland & aquaculture production by waterbody type | `system_as_published` (Capture Fishery / Culture Base Capture Fishery / Aquaculture (Freshwater) / Aquaculture (Brackishwater) / Seaweed), `waterbody_type_as_published` | 261 | 2015, 2018–2025 |
| `bulletin2025_t4_9_inland_aquaculture_by_district` | 4.9 Inland & aquaculture production by district | `district_*` | 260 | 2000, 2005, 2010, 2015, 2020–2025 |
| `bulletin2025_t4_10_inland_catch_by_species` | 4.10 Inland catch estimates by major species group | `species_group_as_published` (Tilapia, Carps/Mirigal, Catla/Rohu, Hiri Kanaya, Lula, …) | 156 | 2010–2015, 2020–2025 |
| `bulletin2025_t4_11_shrimp_production` | 4.11 Shrimp production (aquaculture, wild capture, total) and exported quantity | `measure_as_published` | 64 | 1990, 1995, 2000, 2005, 2010, 2015–2025 |

QC side files: `qc_bulletin2025_ch4_totals_check.txt` (every total mismatch found, all of them in the published PDF) and the scripts in `scripts/`.

## Known issues (all of these are in the published PDF, not extraction errors)
1. **Rounding in 2025 (provisional) figures.** In 4.7, row and column sums differ from the printed totals by 1–3 Mt. In 4.2, 4.3 and 4.9, the 2025 district sums are 2 Mt below the printed totals (364,188 vs 364,190; 55,983 vs 55,985).
2. **4.3 2023 rows where Marine + Inland ≠ Total:** Gampaha (+65), Hambantota (+20), Puttalam (−85). These cancel out in the column total.
3. **The inland totals disagree between tables:**
   - 4.10 for 2025 totals 55,711, but 4.1 and 4.9 give 55,985 (−274).
   - 4.8 gives 67,135 for 2015 against 67,300 in 4.1 and 4.9, and 102,324 for 2024 against 102,330.
4. **The 2025 inland figures are much lower than in 2024** (55,985 vs 102,330 Mt). They are provisional and probably cover only part of the year. Treat them with caution in trend models.
5. **4.5:** for 2000–2010, Thalapath (billfish) is included in "Tuna like fishes", and for 2000–2005 Kakuluwa (crabs) is included in "Others". These cells are flagged and left null. The 2025 "Others" value (39,006) is more than double 2024's (15,170).
6. **District systems differ.** Tables 4.4, 4.6 and 4.7 use the 15 DFAR **fisheries** districts (for example Negombo, Tangalle, Kalmunai and Chilaw). Tables 4.2, 4.3 and 4.9 use the 25 **administrative** districts. 4.3 Puttalam marine = 4.4 Puttalam + Chilaw. Kilinochchi in 4.4 is "na" before 2005.
7. **4.8:**
   - On the Culture Base "Rivers and Cannals" row, one dash is printed offset between the 2015 and 2018 columns. It was read as a dash for every year, with 2024 blank.
   - Freshwater "Ponds" for 2024 is printed as 1 (it was 326 in 2023).
   - The seaweed row is not part of the Total.
8. **"-" was kept as a flag, not 0.** Use `fillna(0)` only if you accept that "-" means nil.
9. **Number formatting.** 4.10 Carps 2022 is printed as "9530" without a comma, and 4.4 Colombo 2024 as "1045". Both were parsed correctly.
10. **These are commercial groups, not species.** Only names as published are given. Use the Ministry `fish_species_list` to map trade names to scientific names.
