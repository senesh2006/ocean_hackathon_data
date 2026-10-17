# Annual Fisheries Statistical Bulletin 2025: consumption and utilisation tables

| | |
|---|---|
| Source | Ministry of Fisheries, Aquatic and Ocean Resources (Statistics Unit), Sri Lanka. *Annual Fisheries Statistical Bulletin 2025* (87-page PDF; PDF ModDate 21 Sep 2026). |
| URL | https://www.fisheries.gov.lk/wp-content/uploads/2026/10/Annual-Fisheries-Statistical-Bulletin-2025.pdf |
| Local copy | `raw/Annual-Fisheries-Statistical-Bulletin-2025.pdf` (6,993,735 bytes) |
| Retrieved | 2026-10-17 |
| Licence | **None stated.** This is a Sri Lankan government publication. Cite the Ministry, and treat reuse terms as unknown. Get permission before republishing at scale. Underlying sources: HIES (Dept. of Census & Statistics) for 8.3, 8.4 and 8.6; DCS National Accounts for 8.1 and 8.2. |
| Extraction | `scripts/extract_bulletin2025_ch8.py` (pdftotext -layout, then pandas). Inventory: `scripts/build_bulletin2025_inventory.py`. |
| QC | `qc_bulletin2025_consumption_checks.txt`. Every value was checked against page renders. Totals reconcile within published rounding. |

All files are tidy long format with one value per row. Every file has `source_document`, `source_table`, `source_pdf_page` and `source_printed_page` (printed page = PDF page − 14). Each CSV has a `.parquet` twin with identical content.

## Files

### `bulletin2025_t8_3_household_fish_consumption.csv` (220 rows)
Table 8.3, *Average Monthly Household Fish Consumption (grams)*. HIES rounds 2009/2010, 2012/2013, 2016 and 2019. National level only: the table has no sector, urban/rural or district split.

| column | meaning |
|---|---|
| survey_period | HIES round as published ("2009/2010", "2012/2013", "2016", "2019") |
| survey_year_start, survey_year_end | integer years |
| household_size_persons | average household size in that round (4.0 / 3.9 / 3.8 / 3.7) |
| row_order | row order in the PDF (null for the Grams/Day/Person row) |
| group | Marine large fish / Marine small fish / Inland (freshwater) fish / Crustaceans & cephalopods / All. Taken from the subtotal each row sits under. |
| row_type | item, subtotal, total, or derived (Grams/Day/Person) |
| fish_type_as_published | trade name exactly as printed, typos included ("Crustacians Total", "Salaya/ Sudaya") |
| english_name_in_bulletin, english_name_bulletin_ref | English name the bulletin itself gives for the same Sinhala name in Tables 4.5, 4.6 or 7.1 |
| editor_english_hint, editor_scientific_hint, editor_hint_confidence | **Not from the PDF.** Editor's identification, rated high, medium or low. Low = unverified. |
| measure | quantity, percent_of_total, or grams_per_day_per_person |
| value | number (null when not reported) |
| unit | g/household/month, %, or g/day/person |
| value_flag | published; blank_not_reported (cell empty in PDF); or dash_published ("-" in PDF) |
| survey | HIES, Department of Census & Statistics |

27 published rows × 4 rounds × 2 measures, plus 4 Grams/Day/Person rows.

### `bulletin2025_t8_4_household_dried_fish_consumption.csv` (156 rows)
Table 8.4, *Average Monthly Household Dried Fish Consumption (grams)*. Same rounds and same columns as 8.3, with group = "Dried fish". 19 published rows (18 types + Total) × 4 × 2, plus 4 Grams/Day/Person rows.

### `bulletin2025_t8_5_per_capita_fish_consumption.csv` (63 rows)
Table 8.5, *Per Capita Consumption of Fish, Dried Fish and Canned Fish*, in kg/person/year. Rounds: 1995/96, 2002/03, 2006/07, 2009/10, 2012/13, 2016, 2019.
Columns: section (Fresh Fish / Dried Fish / Canned Fish), item_as_published, row_type (item/total), survey_period, survey_year_start, value, unit. Published source: Statistics Division, Ministry of Fisheries.

### `bulletin2025_t8_6_household_fish_expenditure.csv` (42 rows)
Table 8.6, *Monthly Household Expenditure for Fish and Fishery Products & Contribution to Food Basket*. Same 7 rounds as 8.5. Six indicators: household size; average household expenditure (Rs, current prices); food expenditure (Rs); food ratio (%); fish share of the food basket (%, includes canned fish); dried-fish share (%).
Columns: item_as_published (wrapped labels joined, footnote markers kept), survey_period, value, unit, footnote (footnote text expanded).

### `bulletin2025_t8_1_8_2_gdp_fisheries.csv` (110 rows)
Tables 8.1 and 8.2, *GDP by Industrial Origin*, at current and constant (2015) market prices, Rs million, 2015–2025. Columns: source_table, price_basis, year, estimate_status (final; revised as at 17 Mar 2026 for 2023–24; provisional for 2025), indicator (GDP, Agriculture sector, Fishing - Marine, Fishing - Inland, Fishing - Total), value, unit.

### `bulletin2025_t6_10_dried_fish_supply.csv` (95 rows), bonus utilisation table from chapter 6
Table 6.10, *Estimated Supply of Dried Fish (Mt)*. Years 1995, 2000, 2005, then 2010–2025 (2025 provisional). Columns: year, estimate_status, component (Local production (1); Imported - Sprats/Other/Total (2); Total dried fish supply), value, unit (tonnes), footnote.
- (1) Local production is estimated from production, import/export and canned-fish data.
- (2) Imports come from customs returns.

### `bulletin2025_table_inventory.csv` (67 rows)
Every table listed in the bulletin's table of contents. Columns: table_no, section, title (body wording), printed_page, pdf_page, years_covered, breakdown, units, source_agency, extractability (clean / moderate / difficult / not_present), notes, extracted_file.

## Known issues
1. **8.3 "Balaya/Kelawalla" row:** the first row is printed as "Balaya/Kelawalla" and the next row as "Kelawalla". The first row almost certainly means Balaya (skipjack) alone, but both are kept as published. Don't add the two together as "tuna" without noting this.
2. **Blank vs dash:** in 8.3, Maduwa (2009/10–2016) and Linna (2009/10, 2012/13) are blank. Hedella shows "-" for 2009/10–2016. In 8.4, Thalapath (2009/10) and Freshwater smoked fishes (2009/10, 2012/13) are blank. These categories were probably counted under "Other/Others" in those rounds, so per-species trends across rounds are not like-for-like.
3. **Groups in 8.3:** "Crustacians Total" (sic) also includes "Cuttle & Others". "Others" appears three times, under small fish, inland fish and so on. Use `group` + `fish_type_as_published` + `row_order` as the key.
4. **Rounding:** items differ from subtotals by up to 0.3 g, and percentages sum to 99.8–100.2.
5. **Coverage:** the newest HIES round is 2019. The 2025 bulletin has no post-2019 consumption data. Everything is national; there are no district or urban/rural splits.
6. **Name identification:** low-confidence editor hints (Hedella, Keerameen, Anguluwa) need checking, for example against `ministry_fish_species_list.csv` or NARA.
7. **8.1/8.2 titles** say 2010–2025, but the rows start at 2015. 8.1's title also reads "Current (2015) Market Prices" as printed.
8. **The inventory found gaps:**
   - Tables 4.12 (shrimp aquaculture) and 5.7 (fingerling production value) are in the table of contents, but their pages (PDF p.52 and p.62) are blank.
   - Several table-of-contents titles give different year ranges from the table bodies: 4.9, 5.6, 6.8 and 6.9.
9. **Licence:** no licence is stated.
