# Sri Lanka: marine life that fishers are banned or restricted from catching
Built 2026-10-16. **This is not legal advice.** Regulations change, so always confirm with the Department of Fisheries and Aquatic Resources (DFAR, https://fisheriesdept.gov.lk/fisheries-regulation/), the Department of Wildlife Conservation (DWC), and the latest Gazette (www.documents.gov.lk).

## Files
- `srilanka_banned_restricted_marine_species.csv` / `.parquet`: 90 rows, one per species, genus or group.
- `gear_area_rules.csv` / `.parquet`: rules that apply to methods and places rather than species. **Note: bottom trawling has been banned in Sri Lanka waters since the FARA (Amendment) Act No. 11 of 2017.**
- `catalog.csv`, `data_dictionary.csv`, and `scripts/`: species_input.py holds the curated entries; build.py does the WoRMS matching and the occurrence-dataset flag.

## Method
1. Primary legal texts were read where available:
   - Shark Fisheries Management Regulations 2015 (Gazette 1938/2), plus the High Seas version.
   - Fauna and Flora Protection (Amendment) Act No. 22 of 2009, with schedules II (strictly protected mammals and reptiles), VI (protected fish) and VII (protected invertebrates and corals), parsed from the official PDF.
   - The DFAR regulations list.
   - The IOTC 2026 summary of conservation and management measures (CMMs), including Res. 25/08, 25/09, 26/03, 12/04 and 23/06.
2. Size limits for lobster, chank and mud crab come from secondary sources quoting the gazettes. The gazette titles and numbers were verified on the DFAR list. These are flagged in `notes`.
3. CITES and IUCN columns are context from published listings. They were not re-queried row by row, so check them at checklist.cites.org and iucnredlist.org.
4. Names were matched with the WoRMS REST API (`worms_aphia_id`, `worms_valid_name`, `worms_match_status`). The match status describes the input name; the valid name is given alongside.
5. `in_occurrence_dataset` compares against fish-data/species_list.csv, which was read only. That dataset contains ray-finned fish only, so sharks, rays, turtles, mammals and invertebrates can never match.

## Caveats
- Cetaceans: the Ordinance protects every mammal NOT in Schedule I, so all whales and dolphins are protected. Schedule II lists only the strictly protected ones.
- Mobulid (manta/devil) rays: IOTC prohibits retention, but no national gazette ban was found. Sri Lanka's 2025-30 shark plan (NPOA) only proposes one.
- Ornamental-fish export lists (protected / restricted export) come from a secondary NARA report and are marked UNVERIFIED.
- No gazetted size limit or season was found for sea cucumbers.
- The species content of Gazette 2008/30 (2017) and the lobster closed-season dates in Gazette 1601/36 were not retrieved.
- Sinhala and Tamil names come from the 2009 schedules where given; otherwise they are common usage or blank.
