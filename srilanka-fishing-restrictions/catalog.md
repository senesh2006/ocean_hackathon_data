# Sri Lanka fishing restrictions — "where/what is illegal to catch" (built 2026-10-18, Asia/Colombo)

Futoura / Ocean Hackathon GAL02 SplitWater. Everything was taken from primary legal texts where possible: DFAR gazettes (via the DFAR GraphQL register), the Fisheries and Aquatic Resources Act (consolidated 2024), the FFPO amendment Act 22/2009, IOTC CMM documents and the CITES CoP20 notice. `verified_from` on every rule records how each item was checked.

## Files (each table is in both CSV and Parquet)
| file | rows | what |
|---|---|---|
| `zones.geojson` | 28 features | Zone geometries in WGS84. Properties are the same as `zones.csv`. |
| `zones.csv/.parquet` | 40 | All zones, including 12 with no geometry: boundary text only, or boundary not obtained. |
| `zone_rules.csv/.parquet` | 56 | Rules attached to zones, joined on `zone_id`. Columns: restriction_type, gears, species, closed months, hours, legal basis, gazette no./date, status. |
| `species_rules.csv/.parquet` | 189 rows / 167 taxa | Species rules: Sri Lankan bans, size limits, seasons and live-export bans; FFPO protected marine species; IOTC retention bans; CITES I/II. Every row has a WoRMS AphiaID and the accepted name. |
| `regulations_register.csv/.parquet` | 104 | Every English-language DFAR register entry, with PDF URL, text source (text layer or OCR) and a check of the register date against the gazette masthead. |
| `qc_summary.json` | – | Validation results. |
| `scripts/build.py`, `scripts/ocr.py` | – | Rebuilds everything from `raw/`. Run with `/workspace/.venv-geo/bin/python`; RapidOCR is used for scanned gazettes. |
| `raw/` | – | Source snapshots: DFAR GraphQL JSON, gazette PDFs with .txt and .ocr.txt, Marine Regions WFS GeoJSON, geoBoundaries ADM2, Nominatim/OSM, Wikidata/Wikipedia, the Kayankerni gazette, FFPO texts, FARA texts, IOTC PDFs, and `worms_cache.json`. |

## How to use it in the model
- **Hard "illegal" masks.** Use the zones with `geometry_quality` of `authoritative_dataset`, `gazette_coordinates`, `osm_polygon`, or `computed_from_rule_coarse_coastline`.
- **Rough masks only.** `approx_point_buffer` and `approx_extent_offshore_limit_unspecified` are indicative (equal-area circles or estimated extents). Never present them as legal boundaries.
- **Rules that apply everywhere** are attached to `LK-SLW`, which is all marine Sri Lanka Waters:
  - bottom-trawl ban;
  - explosives and poison ban;
  - monofilament ban;
  - spear ban;
  - light-attraction ban;
  - lobster closure in Feb, Sep and Oct;
  - licence requirements.
- **Species rules:** join `species_rules` to catch or prediction outputs on `worms_valid_aphia_id`.

## Key verified rules
- **Bottom trawling** by motorised or mechanised boats is banned in all Sri Lanka Waters: no use, possession, import or sale (FARA s.28A, Act No. 11 of 2017, certified 25.07.2017).
- **Surrounding nets** are banned within 7 miles (6.08 NM / 11.26 km) of the coast (Gazette 2115/8, 18.03.2019).
  - Purse seines were banned within 7 or 10 miles depending on district in 1986 (437/46). That rule was made under the repealed Fisheries Ordinance, so its status is uncertain.
- **Scuba collection of chank and bêche-de-mer** is allowed only beyond 4 NM (Trincomalee: 2 NM). Diving is allowed only 06:00–18:00 (2115/8).
- **Lobster:**
  - No lobster fishing anywhere in Feb, Sep and Oct (1601/36). The gazette masthead says 15.05.2009; the DFAR register says 05.05.2009.
  - South-coast area from Bentara to Kumbukkan: closed Feb and Sep, and an endorsed licence is required (1123/2, 2000).
  - Size limits: *P. ornatus* CL ≥ 10 cm; other *Panulirus* CL ≥ 6 cm. No soft-shell or berried lobsters.
- **Sharks** (1938/2, 2015):
  - No catch of thresher (3 spp.), oceanic whitetip or whale shark.
  - Fins must be naturally attached.
- **Species bans and limits:**
  - Thambuwa (*Cephalopholis sonnerati*): total ban (2014/4, 2017).
  - Mud crab: CW ≥ 130 mm and no berried crabs (2371/35, 2024).
  - Blue swimming crab: ≥ 100 g; gillnet mesh ≥ 4.5 in (2277/04, 2022).
  - Chank: ≥ 70 mm; no dredging or trawling (1298/1, 2003). This **repealed** the 2001 Sea Shells regulations (1188/3). Those shells are now protected under FFPO Schedule VII instead.
- **Inside FFPO national parks, marine national parks and state-land sanctuaries**, no fishing is allowed without a DWC permit (FFPO s.6A, Act 22/2009). Recreational fishing is banned in MPAs (2319/19, 2023).
- **Lagoon fisheries management areas:**
  - Negombo: trawl, push and moxi nets banned; no fishing within 150 m of shore except listed gears.
  - Rekawa: residents only, cast and drift nets only.
  - Batticaloa: drag nets banned.
  - Mundel: trap and drag nets banned.
  - Chilaw.
- **Nilwella harbour, 1.5 NM:** rod and line only.

## Licences: what can go in the public data repo
| source | licence | public repo? |
|---|---|---|
| Marine Regions (EEZ, 12/24 NM, IMBL lines) | CC BY 4.0 | **Yes**, with attribution |
| Natural Earth (land mask used in computations) | Public domain | Yes |
| geoBoundaries LKA ADM2 (district bands) | ODbL 1.0 | Yes, but share-alike: derived bands carry ODbL |
| OSM polygons via Nominatim (Pigeon Island, Yala, Kumana, Wilpattu, Rekawa, Mundel) | ODbL 1.0 | Yes, share-alike plus attribution "© OpenStreetMap contributors" |
| Gazette texts and coordinates (Kayankerni polygon, rules) | Sri Lankan government legal texts; copyright status unclear | Facts and rule tables: **yes** (cite the gazette). Avoid re-hosting the PDFs in bulk; link to the DFAR URLs. |
| WoRMS AphiaIDs | CC BY 4.0 | Yes, cite WoRMS |
| Wikidata points | CC0 | Yes |
| Wikipedia areas and dates | CC BY-SA | Facts only (not copyrightable); cite |
| IOTC and CITES documents | Public intergovernmental documents | Yes (facts, cite) |
| **WDPA / Protected Planet** | Restrictive: no redistribution | **Not used.** The UNEP-WCMC ArcGIS service was down ("Could not access any server machines"). The team app already uses WDPA; keep it out of the public repo. |

Recommendation: everything in this folder **except `raw/gazettes/*.pdf`** can go to the public repo. Add an ODbL notice for the OSM and geoBoundaries-derived geometries. **Nothing has been pushed.**

## Validation (see qc_summary.json)
- **Geometries:**
  - 28 drawn geometries, 0 invalid.
  - All polygons lie inside lon 77–85, lat 4–11. The EEZ and IMBL only need to intersect the box, because the EEZ extends to 2.57–11.45°N.
  - Sea overlap: 14 marine, 4 mixed, 4 lines, 6 lagoon/inland. The lagoon/inland ones are Rekawa, Mundel, Kumana, Bundala, Yala and Wilpattu: Natural Earth 1:10m masks lagoons as land, but these are legally Sri Lanka Waters.
- **Areas against official figures:**
  - Kayankerni polygon is 19.3 km². The gazette says 953 ha of *land* plus the adjacent maritime zone, so a larger total is expected.
  - Pigeon Island (OSM) is 3.16 km² against 4.71 km² official.
  - The approximate circles match their official areas by construction. Hikkaduwa shrinks to 0.56 km² once land is removed.
- **Dates:** all ISO dates are valid. 36 register dates were confirmed against gazette mastheads; 1 mismatch (1601/36).
- **AphiaIDs:** 189/189 found, all positive integers. 13 names are unaccepted in WoRMS; the accepted name is given in `worms_valid_name` (e.g. *Pterois radiata* → *Pteropterus radiatus*, *Strombus listeri* → *Mirabilistrombus listeri*).

## Known gaps / caveats
- **No boundary polygons** were found for:
  - Negombo, Chilaw and Batticaloa lagoon FMAs;
  - South Coast FMAs (Order 1665/18);
  - Matara–Thotamuna;
  - Nilwella;
  - Udappuwa;
  - Madiha–Polhena (only an approximate 1 km circle);
  - Rumassala.
  
  Bar Reef, Hikkaduwa, Adam's Bridge, Vankalai, Kokkilai, Chundikkulam and Bundala are **equal-area circles**, not boundaries. OSM Overpass was down (all four mirrors returned 500/504), which limited polygon retrieval.
- **Gampaha prohibited area 2011–13:** expired, and the chart was too illegible to digitise.
- **Beach-seine (madel) sites:** Schedule A of 337/48 (82-page scan) was not parsed.
- **Not parsed:**
  - the full Fishing Operations Regulations 1996 (948/25, 56-page scan; OCR text is in raw/);
  - the gear-marking regulations;
  - the 2024 Chilaw plan.
- **Live-fish export lists:** the marine species in 1036/13 (1998) are included. Part I is a live-export ban (12 spp.); Part II needs a permit (17 spp., plus 16 groupers and barramundi added by 1098/3 in 1999). Freshwater species are omitted.
- **Missing PDF:** DFAR register rows 171 and 297 both point to the cultured-coral import/export PDF. The "Conservation of Coral Reefs and Artificial Substrate Regulations" PDF is missing from the DFAR site.
- **Indian trawler incursion areas:** no open dataset found. Only the treaty IMBL lines are included, and the Foreign Fishing Boats Act rule is cited from secondary knowledge (`verified_from = secondary`).
- **CITES:** cites.org is behind Cloudflare from the box. The CoP20 changes (oceanic whitetip, Mobulidae and whale shark moved to App. I; *Mustelus* and Centrophoridae added to App. II, from 05.03.2026) were verified via the USFWS CoP20 bulletin. Older listings are marked `secondary`; check them against the official PDF before publishing.
- **OCR:** OCR text (RapidOCR) has spacing errors. Rules taken from OCR were read manually and are marked `gazette_ocr`.
- **Not legal advice.** Closed seasons can be changed by s.34 notices published in newspapers, which are not all on the DFAR site.

## Repository copy
This folder is the published copy. **Gazette PDFs are not included**: download them from the DFAR URLs in `regulations_register.pdf_url`. Their extracted text (`raw/gazettes/*.txt`, `*.ocr.txt`) is included. Not included: the DFAR site JS bundle and HTML, other source PDFs (FFPO, FARA, IOTC, the Kayankerni gazette: text extracts are included instead), Wikipedia wikitext, the Protected Planet page, and failed-download stubs. `scripts/build.py` expects the full `raw/` tree under `/workspace/fishing-restrictions/`, so adjust `ROOT` to rebuild.
