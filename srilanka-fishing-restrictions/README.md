# Sri Lanka fishing restrictions: where and what it is illegal to catch

Built 2026-10-18 (Asia/Colombo). **Not legal advice.** Always confirm with DFAR (https://fisheriesdept.gov.lk), DWC, and the latest Gazette (www.documents.gov.lk).

This package complements [`../srilanka-banned-marine/`](../srilanka-banned-marine/). It adds **spatial zones**, rules attached to those zones, and species rules checked against the gazette texts. Examples include the lobster closed season Feb/Sep/Oct (1601/36) and the marine lists in the 1998 live-fish export schedules (1036/13).

| file | rows | contents |
|---|---|---|
| `zones.geojson` | 28 features | Zone geometries (WGS84): EEZ, 12 NM, IMBL lines, coastal gear bands, MPAs, lagoon FMAs |
| `zones.csv` / `.parquet` | 40 | All zones, including 12 with text-only boundaries (`geometry_quality = no_geometry`) |
| `zone_rules.csv` / `.parquet` | 56 | Rules per zone: type, gears, species, closed months, hours, legal basis, gazette no./date, status, `verified_from` |
| `species_rules.csv` / `.parquet` | 189 / 167 taxa | National bans, size limits, seasons and live-export lists; FFPO protected species; IOTC; CITES I/II; WoRMS AphiaIDs |
| `regulations_register.csv` / `.parquet` | 104 | English DFAR regulations, with PDF links and a check of each register date against the gazette |
| `catalog.md` | – | Full method, validation and gaps |
| `qc_summary.json` | – | Validation output |
| `scripts/` | – | `build.py` (builds the tables) and `ocr.py` (RapidOCR for scanned gazettes) |
| `raw/` | – | Source snapshots and gazette text extracts. **No PDFs.** |

> ⚠️ **Approximate geometries are NOT legal boundaries.** Check `geometry_quality`:
> - **Suitable for masks:** `authoritative_dataset`, `gazette_coordinates`, `osm_polygon*`, `computed_from_rule_coarse_coastline`.
> - **Indicative only; do not present as legal limits:**
>   - `approx_point_buffer`: equal-area circles for Bar Reef, Hikkaduwa, Adam's Bridge, Vankalai, Kokkilai, Chundikkulam, Bundala and Madiha–Polhena.
>   - `approx_extent_offshore_limit_unspecified`: the south-coast lobster area.

See [LICENSE-NOTES.md](LICENSE-NOTES.md) for attribution.
