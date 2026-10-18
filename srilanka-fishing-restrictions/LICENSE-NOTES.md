# Licence and attribution notes: srilanka-fishing-restrictions

The package mixes sources. Attribute them as follows:

- **Marine Regions** (EEZ, 12 NM, 24 NM, Sri Lanka–India boundary lines; also used to clip the derived zones):
  Flanders Marine Institute (2023). *Maritime Boundaries Geodatabase*, version 12. https://www.marineregions.org/ — **CC BY 4.0**.
- **OpenStreetMap-derived shapes** (Pigeon Island, Yala, Kumana, Wilpattu, Rekawa lagoon, Mundel lagoon; retrieved through Nominatim):
  **© OpenStreetMap contributors, ODbL 1.0** (https://www.openstreetmap.org/copyright). Derived versions of these shapes stay under ODbL (share-alike).
- **geoBoundaries LKA ADM2** (used to compute the district coastal bands `LK-PURSE1986-*` and `LK-SCUBA-*`):
  Runfola et al., geoBoundaries (source: OpenStreetMap / Wambacher) — **ODbL 1.0**. The derived bands stay ODbL.
- **Natural Earth** 1:10m land (land mask, buffers): public domain.
- **WoRMS** AphiaIDs: WoRMS Editorial Board, *World Register of Marine Species*, https://www.marinespecies.org — CC BY 4.0.
- **Wikidata** reference points: CC0. Areas and dates are cited from the Wikipedia/UNDP pages linked in `zones.source_url`; they are facts, so cite those pages.
- **Sri Lanka Government Gazettes and Acts** (rules, gazette coordinates for the Kayankerni polygon, text extracts in `raw/`): official legal texts of the Democratic Socialist Republic of Sri Lanka. Cite each item by gazette number and date, e.g. "Gazette Extraordinary No. 2115/8 of 18.03.2019".
  - Main instruments: Fisheries and Aquatic Resources Act No. 2 of 1996 (consolidated 2024) and Amendment Act No. 11 of 2017; Fauna and Flora Protection Ordinance as amended by Act No. 22 of 2009.
  - DFAR gazettes, as listed in `regulations_register.csv`.
  - The original PDFs are **not** redistributed here. Use the `pdf_url` links.
- **IOTC** resolutions and **CITES** appendices / CoP20 notice: public intergovernmental documents; cite them.
- **WDPA / Protected Planet**: **not used and not included** (redistribution is restricted).
- The compilation itself (tables, rule coding, QC) is offered under **CC BY 4.0**, consistent with the repository LICENSE. The ODbL parts above keep their own terms.

**Disclaimer:** approximate geometries (`geometry_quality` = `approx_*`) are not legal boundaries. This dataset is not legal advice.
