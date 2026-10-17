# Sri Lanka fish DNA sequences (BOLD + GenBank)
Built 2026-10-17 (Asia/Colombo). Sequences and metadata for fish **collected in Sri Lanka**, mapped to the fish-data-v3 accepted names. Build: `python3 scripts/build_genetics.py` (needs Biopython; raw GenBank flatfiles were cached in /tmp/ncbi; re-fetch with the query in `raw/genbank_query.json`).

## Sources
| Source | How | Licence / terms |
|---|---|---|
| BOLD Systems Data Portal | `https://portal.boldsystems.org/api/query?query=geo:country/ocean:Sri Lanka;tax:class:Teleostei` (and `Elasmobranchii`), then `/api/documents/{query_id}/download?format=tsv`. The older v4 API (`v4.boldsystems.org/index.php/API_Public/combined`) returned "BOLD Public Offline" on 2026-10-17. In the portal taxonomy ray-finned fish are under class **Teleostei** (`class:Actinopterygii` / `Actinopteri` return 0). | BOLD public data packages are released under **CC BY-SA 4.0**. Cite BOLD (Ratnasingham & Hebert 2007, Mol Ecol Notes 7:355) and the record/BIN. |
| NCBI GenBank (nuccore) | E-utilities `esearch`+`efetch` (GenBank flatfile), term `(Actinopterygii[Organism] OR Chondrichthyes[Organism]) AND "Sri Lanka"[All Fields]` → 4,449 hits; kept the 3,955 whose `/country` (or `/geo_loc_name`) is Sri Lanka. All markers kept, labelled in `marker`. | NCBI places **no restrictions** on use or distribution of GenBank data, but some submitters may claim patent, copyright or other IP in all or part of the data (https://www.ncbi.nlm.nih.gov/genbank/). Cite accession + original publication. |

## Contents and coverage
| File | Rows |
|---|---|
| genbank_srilanka_fish_sequences_metadata.csv + fasta/genbank_srilanka_fish.fasta | 3,955 records / 343 organism names; COI 1,699, cytb 1,034, nuclear 508, ND 134, 16S 113, 12S 36, control region 25, other 406; 2,698 with lat/lon |
| bold_srilanka_fish_barcodes_metadata.csv + fasta/bold_srilanka_fish.fasta | 1,298 records (Teleostei 921, Elasmobranchii 377), 231 BINs, 204 species names, 792 with coordinates; COI-5P 1,293, 16S 5 |
| species_barcode_coverage.csv | one row per v3 species (1,437) |

- **v3 species with a Sri Lanka barcode** (BOLD record or GenBank COI): **184 of 1,437**; with any Sri Lanka sequence: 216. By model tier: >=20 records 5/6, >=10 records 21/36, <10 records 158/1,395.
- **Overlap:** 1,268 of the 1,298 BOLD records are the same sequences as GenBank accessions in the GenBank table (`also_in_genbank_table`); 1,040 BOLD records are "Mined from GenBank". BOLD's value-add is the **BIN** and curated specimen data. Don't double count.
- Many sequenced taxa are freshwater/endemic species (e.g. Puntius, Rasbora, Channa) that are not in the marine occurrence list; see `qc/sequenced_taxa_not_in_v3_occurrence_list.csv`.
- `name_match` shows how each record was mapped (v3 name incl. WoRMS synonyms, FishBase synonym, or not_in_v3). Identifications are as submitted; they were not re-checked against the sequences.
- Dates: GenBank records submitted 2003–2026; BOLD collection dates 2005–2026.

## Validation
Fish-only by query (NCBI organism filter Actinopterygii/Chondrichthyes; BOLD class filter). Country filter applied on the parsed `/country` qualifier, not on free text. Coordinates parsed from `/lat_lon` ("7.12 N 79.5 E") and BOLD `coord`. No sequences were edited.
Columns: `data_dictionary.csv`. Files: `catalog.csv` / `catalog.md`.
