# ministry_fish_species_list: catalog

**Files:** `ministry_fish_species_list.csv` (UTF-8 with BOM) and `ministry_fish_species_list.parquet`. The two files hold the same data.
**Source:** Ministry of Fisheries and Aquatic Resources (MFAR), Sri Lanka, *Major Marine Fish Types by Commercial Group*. The PDF footer reads "Source: Statistics Unit of MFAR".
**URL:** https://www.fisheries.gov.lk/wp-content/uploads/2026/07/fish_species_list.pdf. The raw copy is at `raw/fish_species_list.pdf` (3 pages, SHA-256 below). Its PDF metadata gives a creation date of 2009-06-17, so the list is old even though the upload path is 2026/07.
**Retrieved:** 2026-10-17
**Licence:** The document states no licence. It is a Sri Lankan government publication. Cite MFAR when you reuse it, and don't assume it is CC-licensed.
**Rows:** 91. Each row is one scientific-name entry in the PDF, in the PDF's order.
**How it was built:** I took the text with `pdftotext -layout` and checked every row by hand against the page images (rendered with `pdftoppm`), because merged cells make the text layer ambiguous. I then validated the names against the WoRMS REST API `AphiaRecordsByMatchNames` (marine_only=false). The raw WoRMS responses are in `raw/worms_match_responses.json`. The script that rebuilds everything is `scripts/build_ministry_species_list.py`.

## Columns
| column | description |
|---|---|
| row_id | 1–91, the order in the PDF |
| pdf_page | PDF page number (1–3) |
| commercial_group | MFAR commercial group (Seer, Paraw, Balaya, Kelawalla, Other Blood fish, Sharks, Skate, Rock Fish/Galmalu, Shore Seine, Prawns, Lobster, Other). The cell is merged in the PDF, so its value is repeated on every row it covers. One row (Mullets) is blank in the PDF. |
| english_name | English name as printed, typos included. Merged cells such as "Jack, Trevallies", "Marlins", "Squids" and "Cuttle fish" are repeated on each row they cover. |
| scientific_name_as_published | **Exactly as printed. Never edited.** |
| sinhala_name_as_published | The "Sinhala Name" cell exactly as printed. It is all romanised, because the PDF contains **no Sinhala script**. |
| sinhala_name_romanised | The Sinhala part of the cell, with "/" and "and" alternatives separated by "; " |
| english_alt_name_in_sinhala_col | English names that appear inside the Sinhala column (e.g. "Black teatfish", "Electric ray") |
| worms_query_name | The name sent to WoRMS: the published name with typos fixed and "sp."/"spp." removed |
| correction_type | none / sp_suffix_removed / capitalisation / spelling_fixed / wrong_name_replaced |
| scientific_name_accepted | Accepted name in WoRMS (valid_name) |
| aphia_id | AphiaID of the matched record |
| accepted_aphia_id | AphiaID of the accepted name. It differs from aphia_id when the matched name is a synonym. |
| rank | Species / Genus / Family |
| taxonomic_status | WoRMS status of the matched name (accepted / unaccepted, etc.) |
| family, class | Taxonomy from WoRMS |
| is_fish | True for Teleostei and Elasmobranchii. False for crustaceans, cephalopods and sea cucumbers. |
| match_status | exact / exact_after_correction / exact_ambiguous. Ambiguous means WoRMS returned more than one record and the accepted one was used. |
| worms_match_type | WoRMS match_type value |
| notes | Typos fixed, merged-cell readings and data-quality flags |
| retrieved_utc | Date retrieved (UTC) |

## Summary
- All 91 rows matched WoRMS (0 unmatched). 69 matched exactly, 20 matched only after a correction and 2 were ambiguous (Dasyatis and Epinephelus undulosus; the accepted record was used for both).
- By rank: 68 species, 22 genus and 1 family (Belonidae).
- 63 rows are fish (51 Teleostei, 12 Elasmobranchii). The other 28 are 13 crustaceans, 5 cephalopods and 10 sea cucumbers.

## Known issues
- **Typos in scientific names (20 fixed in worms_query_name only):** Scomberomorus commersoni→commerson; Caranx hebiri→heberi; Makariya indika→Makaira indica; Makariya mazara→Makaira mazara; Thunnus abesus→obesus; Carcharhinus Falciformis/Longimanus→lower case; prionace gluaca→Prionace glauca; Siganus so.→sp.; Selar crumenophtthalamus→crumenophthalmus; Lepturacanthus savalaa→savala; Ilish sp.→Ilisha; Penaeus semesulsctus→semisulcatus; Panulirus homorus→homarus; Loligo duvauceli→duvaucelii; Holothuria fucogilva→fuscogilva; Actinopygs→Actinopyga; Theienota→Thelenota; Srichopus→Stichopus.
- **Wrong name:** the wahoo row reads "Acanthocybium commersoni", which looks copied from the row above. It was replaced with *Acanthocybium solandri*.
- **Outdated names** (WoRMS gives the accepted name): Carangoides→Turrum (2 rows), Makaira indica→Istiompax indica, Tetrapturus audax→Kajikia audax, Liza→Chelon, Loligo→Uroteuthis (2 rows), Sepia pharaonis/aculeata→Acanthosepion, and subgenus forms for Penaeus and Holothuria.
- **Duplicate:** *Amblygaster clupeoides* appears twice ("Bleeker's smooth belly"/Gal Hurulla and "Smoothbelly Sardinells"/Keeramin). The second row may have been meant as *A. leiogaster*.
- **Merged-cell reading:** *Panulirus polyphagus* (Mada issa = mud spiny lobster) sits under the merged "Slipper lobster" cell.
- The **Mullets** row has a blank commercial group in the PDF.
- English typos were kept as printed: Rabbitfsh, Sardinells, Javanees, Numbfishers, String rays, Ocean white strip, Gar fisher, Batoid Fisher, Beach de mer, tearfish, Lolyfish.
- Some Sinhala cells hold English or Tamil text: "Electric ray", "valuvadi cownose ray".
- The list says "marine" but includes *Macrobrachium rosenbergii* (a freshwater/brackish prawn).
- 23 rows are only resolved to genus or family, so they can't be joined to species-level occurrence data without a decision on how to handle them.
**raw PDF SHA-256:** `8a764baa2a14ab7d437b7ed22e4ddc41ce889d7c67be9b5873fdd7869541552c`
