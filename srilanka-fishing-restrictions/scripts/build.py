#!/usr/bin/env python3
"""Build the Sri Lanka fishing-restrictions dataset from raw/ sources.
Run with /workspace/.venv-geo/bin/python scripts/build.py (needs shapely, pyproj, pyshp, pandas, pyarrow, requests-free urllib).
Network is only used for WoRMS AphiaID lookups (cached in raw/worms_cache.json)."""
import json, re, os, math, datetime, urllib.request, urllib.parse, time, warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
import pandas as pd
import shapefile
from shapely.geometry import shape, mapping, Point, Polygon, MultiPolygon, LineString, box
from shapely.ops import unary_union, transform
from shapely.validation import make_valid
from pyproj import Transformer

ROOT = '/workspace/fishing-restrictions'
RAW = f'{ROOT}/raw'
OUT = ROOT
BBOX = box(77, 4, 85, 11)
to_m = Transformer.from_crs('EPSG:4326', 'EPSG:5235', always_xy=True).transform   # SLD99 / Sri Lanka Grid 1999 (metres)
to_ll = Transformer.from_crs('EPSG:5235', 'EPSG:4326', always_xy=True).transform
kand = Transformer.from_crs('EPSG:5234', 'EPSG:4326', always_xy=True).transform   # Kandawala / Sri Lanka Grid (old)

def area_km2(g):
    return transform(to_m, g).area / 1e6 if g is not None and not g.is_empty else 0.0

def buf_km(g, km):
    return transform(to_ll, transform(to_m, g).buffer(km * 1000, resolution=16))

# ---------------- base layers ----------------
def load_fc(p):
    return json.load(open(p))['features']

eez = [f for f in load_fc(f'{RAW}/mr_eez.json') if f['properties']['territory1'] == 'Sri Lanka'][0]
EEZ = make_valid(shape(eez['geometry']))
ts = [f for f in load_fc(f'{RAW}/mr_eez_12nm.json') if f['properties']['territory1'] == 'Sri Lanka'][0]
TS12 = make_valid(shape(ts['geometry']))
cz = [f for f in load_fc(f'{RAW}/mr_eez_24nm.json') if f['properties']['territory1'] == 'Sri Lanka'][0]
CZ24 = make_valid(shape(cz['geometry']))
SLW = unary_union([EEZ, TS12, CZ24])   # marine part of 'Sri Lanka Waters'

# Natural Earth land (shared with wrecks task)
sf = shapefile.Reader('/workspace/wrecks/raw/ne_10m_land/ne_10m_land.shp')
land_parts = []
for s in sf.shapes():
    g = shape(s.__geo_interface__)
    if g.intersects(box(76, 3, 86, 12)):
        land_parts.append(g.intersection(box(76, 3, 86, 12)))
LAND = make_valid(unary_union(land_parts))
SL_LAND = [p for p in (LAND.geoms if hasattr(LAND, 'geoms') else [LAND]) if p.contains(Point(80.7, 7.8))][0]

districts = {f['properties']['shapeName'].replace(' District', ''): make_valid(shape(f['geometry']))
             for f in load_fc(f'{RAW}/gb_lka_adm2.geojson')}

def coastal_band(district_names, km):
    parts = [buf_km(districts[d], km) for d in district_names]
    g = unary_union(parts).difference(LAND).intersection(SLW.buffer(0.01))
    return make_valid(g)

def circle_km2(lon, lat, km2):
    r = math.sqrt(km2 / math.pi)
    return buf_km(Point(lon, lat), r)

# ---------------- zones ----------------
zones = []      # dicts with geometry (shapely or None)
def Z(**kw):
    kw.setdefault('geometry', None)
    zones.append(kw)

MR_URL = 'https://www.marineregions.org/'
MR_LIC = 'CC BY 4.0 (Flanders Marine Institute, Marine Regions v12 / MRGID)'
Z(zone_id='LK-EEZ', name='Sri Lanka Exclusive Economic Zone', zone_type='maritime_zone', authority='Maritime Zones Law No. 22 of 1976',
  description='200 NM EEZ; with the territorial sea and contiguous zone this is the marine part of "Sri Lanka Waters" (FARA 1996 s.69 definition). Nationwide rules attach here.',
  geometry=EEZ, geometry_source=f'Marine Regions WFS MarineRegions:eez MRGID {eez["properties"]["mrgid"]}', geometry_quality='authoritative_dataset',
  licence=MR_LIC, source_url='https://marineregions.org/gazetteer.php?p=details&id=8346', public_repo_ok=True)
Z(zone_id='LK-TS12', name='Sri Lanka territorial sea (12 NM)', zone_type='maritime_zone', authority='Maritime Zones Law No. 22 of 1976',
  description='12 NM territorial sea polygon.', geometry=TS12, geometry_source=f'Marine Regions WFS MarineRegions:eez_12nm MRGID {ts["properties"]["mrgid"]}',
  geometry_quality='authoritative_dataset', licence=MR_LIC, source_url='https://marineregions.org/gazetteer.php?p=details&id=49069', public_repo_ok=True)
Z(zone_id='LK-SLW', name='Sri Lanka Waters (marine part: EEZ + 12 NM + 24 NM)', zone_type='maritime_zone', authority='Fisheries and Aquatic Resources Act No. 2 of 1996, s.69 (definition)',
  description='Union of EEZ, territorial sea and contiguous zone. Note: legal "Sri Lanka Waters" also includes historic waters and all public inland waters (lagoons, rivers, tanks), which are not drawn here.',
  geometry=SLW, geometry_source='union of LK-EEZ, LK-TS12 and Marine Regions 24 NM', geometry_quality='authoritative_dataset_derived', licence=MR_LIC,
  source_url='https://lankalaw.net/wp-content/uploads/2025/03/Fisheries-and-Aquatic-Resources-Act-Consolidated-2024.pdf', public_repo_ok=True)

# IMBL (treaty boundary lines)
for i, f in enumerate([f for f in load_fc(f'{RAW}/mr_eez_boundaries.json') if f['properties'].get('line_name') == 'Sri Lanka - India']):
    p = f['properties']
    Z(zone_id=f'LK-IMBL-{i+1}', name=f'Sri Lanka–India maritime boundary (IMBL), {p["doc_date"][:4]} agreement', zone_type='boundary_line',
      authority=p['source1'], description='Treaty maritime boundary. Fishing by foreign (incl. Indian) boats on the Sri Lankan side is illegal without a licence (Fisheries (Regulation of Foreign Fishing Boats) Act No. 59 of 1979, as amended 2018). Indian bottom-trawler incursions occur mainly in Palk Bay / Palk Strait north of Mannar–Jaffna.',
      geometry=make_valid(shape(f['geometry'])), geometry_source=f'Marine Regions WFS MarineRegions:eez_boundaries ({p["line_type"]}, {p["length_km"]} km)',
      geometry_quality='authoritative_dataset', licence=MR_LIC, source_url='https://www.marineregions.org/eezmethodology.php', public_repo_ok=True)

# Coastal gear-limit bands
ALL_COASTAL = ['Colombo','Gampaha','Kalutara','Galle','Matara','Hambantota','Ampara','Batticaloa','Trincomalee','Mullaitivu','Kilinochchi','Jaffna','Mannar','Puttalam']
band_all = make_valid(buf_km(SL_LAND, 11.26).difference(LAND).intersection(SLW.buffer(0.01)))
Z(zone_id='LK-SURROUND-7MI', name='Surrounding-net exclusion band, 7 miles (11.26 km) from coast', zone_type='coastal_gear_band', authority='Fishing Operations Regulations 1996 (Amendment), Gazette Ext. 2115/8 of 18.03.2019, reg. 9(7)',
  description='No surrounding nets within 7 miles / 6.08 NM / 11.26 km of the coast, all districts. Band computed by buffering the Natural Earth 1:10m Sri Lanka coastline 11.26 km (SLD99 metres).',
  geometry=band_all, geometry_source='computed: NE 10m land buffer 11.26 km, minus land, clipped to Sri Lanka Waters', geometry_quality='computed_from_rule_coarse_coastline',
  licence='derived (Natural Earth public domain + Marine Regions CC BY 4.0)', source_url='https://files.fisheriesdept.gov.lk/dfar_web/uploads/pdfs/', public_repo_ok=True)
ps7 = ['Colombo','Kalutara','Galle','Matara','Hambantota','Ampara','Batticaloa','Trincomalee']
ps10 = ['Gampaha','Puttalam','Mannar','Mullaitivu','Jaffna']
Z(zone_id='LK-PURSE1986-7MI', name='Purse-seine exclusion band 1986: 7 miles (Colombo, Kalutara, Galle, Matara, Hambantota, Ampara, Batticaloa, Trincomalee)', zone_type='coastal_gear_band',
  authority='Purse-Seine Net Fishing Regulations 1986, Gazette Ext. 437/46 of 19.01.1987 (Fisheries Ordinance Cap. 212)',
  description='No purse-seine net (with or without light) within 7 miles of shore in these districts. Statute miles assumed (11.27 km). Per-district bands overlap slightly at district borders.',
  geometry=coastal_band(ps7, 11.27), geometry_source='computed: geoBoundaries ADM2 (simplified) district buffer minus NE land', geometry_quality='computed_from_rule_coarse_coastline',
  licence='derived (geoBoundaries ODbL 1.0 + Natural Earth + Marine Regions CC BY 4.0)', source_url='DFAR register row 37', public_repo_ok=True)
Z(zone_id='LK-PURSE1986-10MI', name='Purse-seine exclusion band 1986: 10 miles (Gampaha, Puttalam, Mannar, Mullaitivu, Jaffna)', zone_type='coastal_gear_band',
  authority='Purse-Seine Net Fishing Regulations 1986, Gazette Ext. 437/46 of 19.01.1987',
  description='No purse-seine net within 10 miles of shore in these districts. Statute miles assumed (16.09 km). Kilinochchi not listed (district created 1984 boundaries may differ).',
  geometry=coastal_band(ps10, 16.09), geometry_source='computed: geoBoundaries ADM2 (simplified) district buffer minus NE land', geometry_quality='computed_from_rule_coarse_coastline',
  licence='derived (geoBoundaries ODbL 1.0 + Natural Earth + Marine Regions CC BY 4.0)', source_url='DFAR register row 37', public_repo_ok=True)
scuba4 = ['Colombo','Gampaha','Kalutara','Galle','Matara','Hambantota','Ampara','Batticaloa','Puttalam','Mannar','Jaffna','Mullaitivu','Kilinochchi']
Z(zone_id='LK-SCUBA-CHANK-4NM', name='No scuba chank / bêche-de-mer collection within 4 NM (7.4 km) – 13 districts', zone_type='coastal_gear_band',
  authority='Gazette Ext. 2115/8 of 18.03.2019, reg. 14', description='Scuba-diving for chank and bêche-de-mer only beyond 4 NM (7.4 km) from the coast in the listed districts.',
  geometry=coastal_band(scuba4, 7.4), geometry_source='computed district buffer', geometry_quality='computed_from_rule_coarse_coastline',
  licence='derived (geoBoundaries ODbL 1.0 + Natural Earth + Marine Regions CC BY 4.0)', source_url='DFAR register row 94', public_repo_ok=True)
Z(zone_id='LK-SCUBA-CHANK-2NM-TRINCO', name='No scuba chank / bêche-de-mer collection within 2 NM (3.7 km) – Trincomalee', zone_type='coastal_gear_band',
  authority='Gazette Ext. 2115/8 of 18.03.2019, reg. 14 proviso', description='Trincomalee District limit is 2 NM (3.7 km) (gazette text says "from the boat", read as from the coast).',
  geometry=coastal_band(['Trincomalee'], 3.7), geometry_source='computed district buffer', geometry_quality='computed_from_rule_coarse_coastline',
  licence='derived (geoBoundaries ODbL 1.0 + Natural Earth + Marine Regions CC BY 4.0)', source_url='DFAR register row 94', public_repo_ok=True)

# Lobster south-coast area (Bentara estuary -> Kumbukkan estuary), offshore extent not stated -> clipped to 12 NM
clip = Polygon([(79.993, 6.421), (79.62, 6.30), (79.62, 4.9), (82.4, 4.9), (82.05, 6.22), (81.737, 6.484), (81.0, 6.95), (80.2, 6.95), (79.993, 6.421)])
Z(zone_id='LK-LOBSTER-SOUTH', name='South-coast spiny lobster area (Bentara estuary to Kumbukkan estuary)', zone_type='species_management_area',
  authority='Lobster Fisheries Management Regulations 2000, Gazette Ext. 1123/2 of 13.03.2000, Schedule I',
  description='Sea area of the southern coastal belt from the Bentara River estuary to the Kumbukkan River estuary. Offshore limit is not stated in the gazette; drawn to 12 NM. River-mouth positions are approximate (Bentara ~79.993E 6.421N; Kumbukkan ~81.737E 6.484N).',
  geometry=make_valid(TS12.intersection(clip).difference(LAND)), geometry_source='computed: TS12 clipped between approximate estuary positions', geometry_quality='approx_extent_offshore_limit_unspecified',
  licence='derived (Marine Regions CC BY 4.0 + Natural Earth)', source_url='DFAR register row 146', public_repo_ok=True)

# Kayankerni Marine Sanctuary — exact gazette coordinates (Kandawala / Sri Lanka Grid, EPSG:5234)
kay_pts = [(278940,312029),(281712,312134),(286491,311129),(286495,309193),(284452,306614),(284149,306877),(284380,307553),(283794,308593),
           (283629,308609),(283114,308681),(282940,308793),(282358,309282),(282062,309522),(281716,310198),(281613,310101),(281496,310053),
           (281380,309994),(280917,309977),(278940,312029)]
KAY = make_valid(Polygon([kand(x, y) for x, y in kay_pts]))
Z(zone_id='LK-MPA-KAYANKERNI', name='Kayankerni Marine Sanctuary', zone_type='marine_protected_area', designation='Sanctuary (FFPO s.2(2))',
  authority='Fauna and Flora Protection Ordinance; Order in Gazette Ext. 2118/59 of 11.04.2019',
  description='953 ha incl. adjacent maritime zone, Thennadi Bay / Vandeloos Bay, Batticaloa. Polygon digitised from the gazette schedule coordinates (stated as "SLD 99" but they fit the Kandawala Sri Lanka Grid EPSG:5234). Gazette point "3060614N" read as 306614N (typo).',
  geometry=KAY, geometry_source='gazette schedule coordinates (digitised)', geometry_quality='gazette_coordinates', licence='Sri Lanka Government Gazette (public legal text; coordinates are facts)',
  source_url='https://kayankerni.org/wp-content/uploads/2022/11/Kayankerni-Sanctuary-Declaration.pdf', official_area_km2=9.53, public_repo_ok=True)

# OSM polygons via Nominatim (ODbL)
nom = json.load(open(f'{RAW}/nominatim/nominatim_results.json'))
def osm_geom(query, osm_id):
    for x in nom.get(query, []):
        if x['osm_id'] == osm_id:
            return make_valid(shape(x['geojson'])), f'OSM {x["osm_type"]}/{osm_id} via Nominatim'
    return None, None
OSM_LIC = 'ODbL 1.0 (© OpenStreetMap contributors) – share-alike, attribution required'
g, src = osm_geom('Pigeon Island National Park', 439357706)
Z(zone_id='LK-MPA-PIGEON', name='Pigeon Island (Marine) National Park', zone_type='marine_protected_area', designation='National Park (FFPO); managed as Marine National Park',
  authority='Fauna and Flora Protection Ordinance; Gazette 1291/16 of 04.06.2003', description='Islands + surrounding reef off Nilaveli, Trincomalee; official area 471.4 ha.',
  geometry=g, geometry_source=src, geometry_quality='osm_polygon', licence=OSM_LIC, source_url='https://www.openstreetmap.org/way/439357706', official_area_km2=4.714, public_repo_ok=True)
for q, oid, zid, nm, des, auth, akm2 in [
    ('Yala National Park', 16908453, 'LK-PA-YALA', 'Yala National Park (coastal)', 'National Park (FFPO)', 'FFPO', None),
    ('Kumana National Park', 18136442, 'LK-PA-KUMANA', 'Kumana National Park (coastal)', 'National Park (FFPO)', 'FFPO', None),
    ('Wilpattu National Park', 15434166, 'LK-PA-WILPATTU', 'Wilpattu National Park (coastal)', 'National Park (FFPO)', 'FFPO', None)]:
    g, src = osm_geom(q, oid)
    Z(zone_id=zid, name=nm, zone_type='coastal_protected_area', designation=des, authority=auth,
      description='Mainly terrestrial park with coastal lagoons/villus; FFPO s.6A bans fishing in its waters without a permit.', geometry=g, geometry_source=src,
      geometry_quality='osm_polygon', licence=OSM_LIC, source_url=f'https://www.openstreetmap.org/relation/{oid}', official_area_km2=akm2, public_repo_ok=True)
g, src = osm_geom('Rekawa Lagoon', 5437464)
Z(zone_id='LK-FMA-REKAWA', name='Rekawa Lagoon Fisheries Management Area', zone_type='fisheries_management_area', authority='Rekawa Lagoon FMA Regulations, Gazette Ext. 1067/4 of 16.02.1999',
  description='Whole Rekawa lagoon (GN divisions Rekawa W/E, Marakolliya, Medagama, Wellaodaya, Medilla, Netolpitiya), ~11 km from Tangalle towards Hambantota.',
  geometry=g, geometry_source=src, geometry_quality='osm_polygon_lagoon_water', licence=OSM_LIC, source_url='https://www.openstreetmap.org/relation/5437464', public_repo_ok=True)
g, src = osm_geom('Puttalam Lagoon', 531320793)
Z(zone_id='LK-FMA-MUNDEL', name='Old Dutch Canal and Mundal (Mundel) Lagoon fishing area', zone_type='fisheries_management_area', authority='Gazette Ext. 916/11 of 28.03.1996',
  description='Trap nets and drag nets banned; drift nets < 5.1 cm (2 in) mesh banned. Only the lagoon is drawn (OSM water polygon); the Old Dutch canal is not.',
  geometry=g, geometry_source=src, geometry_quality='osm_polygon_lagoon_water_partial', licence=OSM_LIC, source_url='https://www.openstreetmap.org/way/531320793', public_repo_ok=True)

# Approximate (equal-area circle) MPAs – NOT boundaries
def approx(zid, name, lon, lat, km2, desig, auth, desc, src_url, marine=True):
    c = circle_km2(lon, lat, km2)
    if marine:
        c = make_valid(c.difference(LAND))
    Z(zone_id=zid, name=name, zone_type='marine_protected_area' if marine else 'coastal_protected_area', designation=desig, authority=auth,
      description=desc + f' GEOMETRY IS AN EQUAL-AREA CIRCLE ({km2} km²) AROUND A REFERENCE POINT, NOT THE LEGAL BOUNDARY.',
      geometry=c, geometry_source=f'circle {km2} km² around Wikidata/Wikipedia reference point ({lat}, {lon})' + (', minus land' if marine else ''),
      geometry_quality='approx_point_buffer', licence='point: Wikidata CC0 / Wikipedia CC BY-SA; area: cited source', source_url=src_url, official_area_km2=km2, public_repo_ok=True)
approx('LK-MPA-BARREEF', 'Bar Reef Marine Sanctuary', 79.7333, 8.3833, 306.7, 'Sanctuary (FFPO)', 'FFPO; Gazette 708/24 of 03.04.1992',
       'Largest coral reef MPA, off Kalpitiya, Puttalam; IUCN IV, WDPA 62936.', 'https://mptf.undp.org/sites/default/files/documents/2024-04/2023_preparatory_grant_report_sri_lanka.docx.pdf')
approx('LK-MPA-HIKKADUWA', 'Hikkaduwa (Marine) National Park', 80.0925, 6.145, 1.016, 'National Park (FFPO)', 'FFPO; sanctuary 18.05.1979, National Park 19.09.2002',
       'Fringing coral reef, Galle District.', 'https://en.wikipedia.org/wiki/Hikkaduwa_National_Park')
approx('LK-MPA-ADAMSBRIDGE', "Adam's Bridge Marine National Park", 79.62833, 9.07083, 189.9, 'Marine National Park (FFPO)', 'FFPO; declared 22.06.2015',
       'Shoals between Mannar Island and the IMBL. Under FFPO, customary/traditional activities may be allowed with conditions.', "https://en.wikipedia.org/wiki/Adam%27s_Bridge_Marine_National_Park")
approx('LK-PA-VANKALAI', 'Vankalai Sanctuary', 79.91667, 8.93333, 48.39, 'Sanctuary (FFPO); Ramsar site', 'FFPO; declared 2008',
       'Coastal wetland/lagoon and shallow sea, Mannar.', 'https://en.wikipedia.org/wiki/Vankalai_Sanctuary', marine=False)
approx('LK-PA-KOKKILAI', 'Kokkilai Sanctuary', 80.93194, 9.02361, 19.95, 'Sanctuary (FFPO)', 'FFPO; declared 18.05.1951',
       'Kokkilai lagoon, Mullaitivu/Trincomalee.', 'https://en.wikipedia.org/wiki/Kokkilai_Sanctuary', marine=False)
approx('LK-PA-CHUNDIKKULAM', 'Chundikkulam National Park', 80.50694, 9.49861, 195.65, 'National Park (FFPO)', 'FFPO; sanctuary 1938, NP 22.06.2015',
       'Chundikkulam lagoon and coast, Kilinochchi/Jaffna.', 'https://en.wikipedia.org/wiki/Chundikkulam_National_Park', marine=False)
approx('LK-PA-BUNDALA', 'Bundala National Park', 81.225, 6.21389, 33.39, 'National Park (FFPO); Ramsar site', 'FFPO; NP 1993, re-gazetted 2004',
       'Coastal lagoons, Hambantota.', 'https://en.wikipedia.org/wiki/Bundala_National_Park', marine=False)
# Madiha–Polhena coral reef FMA – approximate point only
Z(zone_id='LK-FMA-MADIHA-POLHENA', name='Madiha–Polhena Coral Reef Ecosystem Fisheries Management Area', zone_type='fisheries_management_area',
  authority='FARA s.31(1)(a) Order, Gazette Ext. 1191/6 of 02.07.2001', description='Covers GN divisions 411A Madiha West, 411B Madiha East and 412 Polhena (Matara). No boundary coordinates published; geometry is a 1 km circle around Polhena reef (approx.).',
  geometry=make_valid(buf_km(Point(80.5205, 5.9370), 1.0).difference(LAND)), geometry_source='approximate point (Polhena reef) + 1 km buffer, minus land', geometry_quality='approx_point_buffer',
  licence='derived', source_url='DFAR register row 172', public_repo_ok=True)

# Areas with no drawable geometry (attribute only)
for zid, nm, ztype, auth, desc, src in [
  ('LK-FMA-NEGOMBO', 'Negombo Lagoon Fishery Management Area', 'fisheries_management_area', 'Gazette Ext. 1038/16 of 30.07.1998',
   'Lagoon to high-tide level incl. stream mouths; seaward limit = straight line Kutti Duwa – Duwa Point.', 'DFAR register row 88'),
  ('LK-FMA-CHILAW', 'Chilaw Lagoon', 'fisheries_management_area', 'Gazette Ext. 916/12 of 28.03.1996; plan Gazette Ext. 2375/21 of 12.03.2024',
   'Harasdel (stake/barrier nets) only from 1 mile south of Chilaw Bridge, ≥100 m apart, mesh ≥ 4 cm.', 'DFAR register rows 134, 222'),
  ('LK-FMA-BATTICALOA', 'Batticaloa Lagoon fishery management area', 'fisheries_management_area', 'Gazette Ext. 1167/3 of 15.01.2001',
   'Karaivalai / drag-net (madel) banned in the area; drift nets < 7.62 cm (3 in) mesh banned in Sector 2; no new kottus/enclosures.', 'DFAR register row 156'),
  ('LK-FMA-MATARA-THOTAMUNA', 'Matara Thotamuna–Ginigasmulla fishing area', 'fisheries_management_area', 'Gazette Ext. 1149/3 of 12.09.2000',
   'Matara (Thotamuna) fishing harbour area bounded E by Browns Hill (Thobana), N by shore, W by Belligala & Chulankara Island, S by Hambiyawa. Only listed gears; drift nets only beyond 375 m of Hambiyawa; madel only Jan–Mar and no nylon nets.', 'DFAR register row 151'),
  ('LK-NILWELLA-HARBOUR', 'Nilwella fisheries harbour area (1.5 NM)', 'gear_restricted_area', 'Nilwella Fisheries Regulations No.1 of 2011, Gazette Ext. 1711/4 of 20.06.2011',
   'Within 1.5 NM in territorial waters between Nilwella Point (Berawagala, Dugahawella) and Hanwella (Nilwella): rod-and-line only.', 'DFAR register row 207'),
  ('LK-CUTTLEFISH-UDAPPUWA', 'Udappuwa & Semuthu Thoduwa cuttlefish FAD area (Puttalam)', 'gear_restricted_area', 'Gazette Ext. 1733/23 of 23.11.2011',
   'Cuttlefish FADs (Pila athu branches only, ≤1.1 m) only >8 km offshore, depth ≥16 m, placed Jan–Mar only, ≤10 per OBM boat per week, GPS-registered.', 'DFAR register row 58'),
  ('LK-FMA-SOUTH-MATARA-GALLE', 'South Coast (Matara & Galle) FMA – ornamental fish & lobster', 'fisheries_management_area', 'Order Gazette Ext. 1665/18 (04.08.2010); regs Gazette Ext. 1770/25 of 10.08.2012',
   'Live ornamental fish / lobster only with endorsed licence; ≤20 (NTRB) / ≤25 (MTRB/OFRP) bottom-set gillnet pieces; 06:00–18:00 only. Area boundary in Order 1665/18 not obtained.', 'DFAR register row 64'),
  ('LK-FMA-SOUTH-HAMBANTOTA', 'South Coast (Hambantota) FMA – chank & lobster', 'fisheries_management_area', 'Order Gazette Ext. 1665/18 (04.08.2010); regs Gazette Ext. 1774/36 of 07.09.2012',
   'Chank/lobster only with endorsed licence, separate licence per category, gillnet piece limits, logbooks. Area boundary not obtained.', 'DFAR register row 70'),
  ('LK-GAMPAHA-PROHIB-2011', 'Prohibited fishing area off Gampaha (2011–2013, expired)', 'temporary_closure', 'FARA s.34 notices, Gazette Ext. 1702/2 of 18.04.2011, extended by 1784/4 (12.11.2012) and 1801/28 of 14.03.2013',
   'All fishing prohibited in a charted area off Gampaha, Apr 2011 – 31 Mar 2013. Chart coordinates illegible in the scanned gazette; not digitised. EXPIRED.', 'DFAR register rows 55, 73'),
  ('LK-RES-BOLGODA', 'Bolgoda Reservoir (inland)', 'inland_fisheries_area', 'Bolgoda Reservoir (Fishing Operations) Regulations 2007, Gazette Ext. 1493/18 of 20.04.2007',
   'Mesh ≥ 4 in; prawn nets restricted Aug–Sep; no mechanised boats.', 'DFAR register row 46'),
  ('LK-FMA-PARAKRAMA', 'Parakrama Samudraya FMA (inland)', 'inland_fisheries_area', 'Gazette Ext. 1244/1 of 08.07.2002 and 1255/24 of 26.09.2002',
   'Only gill nets, mesh ≥ 4 in, max 1,500 meshes per piece; no fishing 09:00–15:00.', 'DFAR register rows 110, 177'),
  ('LK-MPA-RUMASSALA', 'Rumassala Sanctuary (marine part)', 'marine_protected_area', 'FFPO sanctuary (2003, reported)',
   'Reported sanctuary with marine area near Galle/Unawatuna; boundary/gazette not verified in this build.', 'not verified'),
]:
    Z(zone_id=zid, name=nm, zone_type=ztype, authority=auth, description=desc, geometry=None, geometry_source='none (boundary text only / not obtained)',
      geometry_quality='no_geometry', licence='Sri Lanka Government Gazette (public legal text)', source_url=src, public_repo_ok=True)

# ---------------- zone rules ----------------
R = []
def rule(zone_id, restriction_type, summary, legal_basis, gazette_no=None, gazette_date=None, gears=None, species=None, months=None, hours=None,
         status='in_force', source_url=None, verified_from='gazette_text', notes=None):
    R.append(dict(rule_id=f'R{len(R)+1:03d}', zone_id=zone_id, restriction_type=restriction_type, summary=summary, gears_banned_or_limited=gears,
                  species_scope=species, closed_months=months, allowed_hours=hours, legal_basis=legal_basis, gazette_no=gazette_no, gazette_date=gazette_date,
                  status=status, verified_from=verified_from, source_url=source_url, notes=notes))
DF = 'https://files.fisheriesdept.gov.lk/dfar_web/uploads/pdfs/'
ACT = 'https://lankalaw.net/wp-content/uploads/2025/03/Fisheries-and-Aquatic-Resources-Act-Consolidated-2024.pdf'
U = {r['row_id']: r['pdf_url'] for r in json.load(open(f'{RAW}/dfar_rows.json'))}
rule('LK-SLW','gear_ban','Bottom trawl nets towed by motorised/mechanised boats banned: no use, possession, import, transport, purchase or sale; no new licences.','FARA s.28A, inserted by Fisheries and Aquatic Resources (Amendment) Act No. 11 of 2017',None,'2017-07-25',gears='bottom trawl (motorised/mechanised)',source_url='https://lankalaw.net/wp-content/uploads/2024/02/11-2017_E.pdf',verified_from='act_text',notes='Certified 25.07.2017. Penalty up to 2 years and/or fine ≥ Rs 50,000.')
rule('LK-SLW','method_ban','Explosives, poison, stupefying substances (incl. dynamite) banned for fishing; no possession or trade in fish caught this way.','FARA s.27 (as amended by Act No. 4 of 2004)',None,'1996-01-31',gears='explosives / poison',source_url=ACT,verified_from='act_text',notes='gazette_date = Act No. 2 of 1996 certification date (approx.)')
rule('LK-SLW','gear_ban','Monofilament nets: no use, possession, import, transport, purchase or sale for fishing.','Monofilament Nets Prohibition Regulations','1454/33','2006-07-21',gears='monofilament nets',source_url=U.get(198),verified_from='gazette_ocr')
rule('LK-SLW','gear_ban','Spear guns and hand-held spears banned for fishing; spear guns may not be possessed or carried on local boats.','Prohibition of Use of Spears in Fishing Operations Regulations No.1 of 2017','2008/31','2017-03-03',gears='spear gun; hand spear',source_url=U.get(79))
rule('LK-SLW','method_ban','No artificial light to attract fish (DG may permit for small-scale rod & line, scoop net, hand line, traps). Light limits on boats; no generators on NTRB/MTRB/NBSB/OFRP/IDAY.','Fishing Operations Regulations 1996 (Amendment) reg. 9(3)-(6)','2115/8','2019-03-18',gears='light attraction; generators on small boats',source_url=U.get(94))
rule('LK-SLW','time_window','Diving fishing operations only 06:00–18:00; separate licence per target type; scuba boats max 2 divers + skipper and ≤8 cylinders; no harpoons/spears on chank, bêche-de-mer, lobster and ornamental scuba boats.','Fishing Operations Regulations 1996 (Amendment) Part II regs 11-18','2115/8','2019-03-18',gears='diving / scuba',hours='06:00-18:00',source_url=U.get(94))
rule('LK-SLW','gear_limit','Stake nets (ja kottu) not near coral reefs, seagrass, marine-mammal habitat or beach-seine areas; guide net ≤ 75 m, mesh ≥ 1.25 in; ≥ 300 m apart.','Fishing Operations Regulations 1996 (Amendment) Part III regs 20-26','2115/8','2019-03-18',gears='stake net (ja kottu)',source_url=U.get(94))
rule('LK-SLW','seasonal_closure','No licence holder may catch lobster anywhere in the Sri Lanka sea area in February, September and October.','FARA s.34 notice: Declaration of prohibited time period for lobster','1601/36','2009-05-15',species='lobster (Panulirus spp., Scyllaridae)',months='2,9,10',source_url=U.get(203),verified_from='gazette_ocr',notes='DFAR register lists 2009-05-05; the gazette masthead reads FRIDAY, MAY 15, 2009 (signed 04.05.2009).')
rule('LK-SLW','gear_ban','No dredging or trawling to take chank (live or dead); DG may declare closed seasons/areas.','Chank Fisheries Management and Export Regulations 2003','1298/1','2003-07-21',gears='dredge; trawl',species='Turbinella pyrum',source_url=U.get(183),verified_from='gazette_ocr')
rule('LK-SLW','gear_ban','No mechanised dredging for dead shells; dead-shell collection, possession and transport need a licence.','Fisheries Management (Collection of dead shells) Regulations 2012','1780/31','2012-10-19',gears='mechanised dredge',species='dead shells',source_url=U.get(179))
rule('LK-SLW','gear_limit','Blue swimming crab: only with an operation licence; nylon polyfilament nets only; bottom-set gillnet mesh ≥ 4.5 in, ply ≤ 6; OFRP/MTRB/NTRB only; no dredging or seabed damage.','Blue Swimming Crab Fishery Management Regulations 2022','2277/04','2022-04-25',gears='monofilament; gillnet <4.5 in; dredge',species='Portunus pelagicus',source_url=U.get(216))
rule('LK-SLW','permit_required','Mud crab fishing only with an operation licence; no dredging or habitat damage.','Mud Crab Fishery Management Regulations 2024','2371/35','2024-02-15',gears='dredge',species='Scylla serrata',source_url=U.get(219))
rule('LK-SLW','permit_required','Every mechanised fishing boat needs a departure and arrival permit for each trip; AIS/MMSI required.','Departure and Arrival of Mechanized Fishing Boats Regulations No.1 of 2023','2319/20','2023-02-13',source_url=U.get(106))
rule('LK-SLW','permit_required','No fishing anywhere in Sri Lanka Waters without a licence under the Fishing Operations Regulations 1996.','Fishing Operations Regulations 1996 reg. 9(2) (inserted 2019)','2115/8','2019-03-18',source_url=U.get(94))
rule('LK-SLW','permit_required','Recreational fishing needs a licence. Catch may not be sold; ETP species must be released; no stainless hooks; none in closed seasons, spawning/breeding areas or MPAs (DFAR/DWC).','Recreational Fishing Management Regulations 2023','2319/19','2023-02-13',source_url=U.get(116))
rule('LK-SLW','habitat_protection','No effluent discharge, dumping or reclamation harming aquatic resources; no mangrove removal; no activity threatening fish conservation without a DG permit.','Conservation of Fish and Aquatic Resources within Sri Lanka Waters Regulations 2016','2008/30','2017-03-03',source_url=U.get(225))
rule('LK-SURROUND-7MI','gear_ban','No surrounding nets within 7 miles (6.08 NM / 11.26 km) of the coast.','Fishing Operations Regulations 1996 (Amendment) reg. 9(7)','2115/8','2019-03-18',gears='surrounding net (incl. purse seine, ring net)',source_url=U.get(94))
rule('LK-PURSE1986-7MI','gear_ban','No purse-seine net (with or without light) within 7 miles of shore; outside that, permit required; net ≤ 225 m, mesh ≥ 3/8 in, lamps ≤ 1,500 W (tuna purse seines exempt from length/lamp limits).','Purse-Seine Net Fishing Regulations 1986','437/46','1987-01-19',gears='purse seine',source_url=U.get(37),verified_from='gazette_ocr',status='in_force_uncertain',notes='Made under the Fisheries Ordinance (Cap. 212), repealed by FARA 1996; whether it is saved was not verified. Largely overtaken by 2115/8.')
rule('LK-PURSE1986-10MI','gear_ban','No purse-seine net within 10 miles of shore (Gampaha, Puttalam, Mannar, Mullaitivu, Jaffna).','Purse-Seine Net Fishing Regulations 1986','437/46','1987-01-19',gears='purse seine',source_url=U.get(37),verified_from='gazette_ocr',status='in_force_uncertain',notes='Same caveat as the 7-mile band.')
rule('LK-SCUBA-CHANK-4NM','gear_ban','Scuba collection of chank and bêche-de-mer only beyond 4 NM (7.4 km).','Fishing Operations Regulations 1996 (Amendment) reg. 14','2115/8','2019-03-18',gears='scuba diving',species='Turbinella pyrum; Holothuroidea',source_url=U.get(94))
rule('LK-SCUBA-CHANK-2NM-TRINCO','gear_ban','Trincomalee: scuba collection of chank and bêche-de-mer only beyond 2 NM (3.7 km).','Fishing Operations Regulations 1996 (Amendment) reg. 14 proviso','2115/8','2019-03-18',gears='scuba diving',species='Turbinella pyrum; Holothuroidea',source_url=U.get(94))
rule('LK-LOBSTER-SOUTH','permit_required','Spiny lobster here only with a licence endorsed "valid for the taking of south coast spiny lobster".','Lobster Fisheries Management Regulations 2000 reg. 2','1123/2','2000-03-13',species='Panulirus spp.',source_url=U.get(146),verified_from='gazette_ocr')
rule('LK-LOBSTER-SOUTH','seasonal_closure','No spiny-lobster fishing in February and September (2000 rule; nationwide Feb/Sep/Oct closure added in 2009).','Lobster Fisheries Management Regulations 2000 reg. 3','1123/2','2000-03-13',species='Panulirus spp.',months='2,9',source_url=U.get(146),verified_from='gazette_ocr')
for z, d, ref in [('LK-MPA-KAYANKERNI','Sanctuary on state land/waters','2118/59'),('LK-MPA-PIGEON','National Park','1291/16'),('LK-MPA-BARREEF','Sanctuary','708/24'),
                  ('LK-MPA-HIKKADUWA','National Park',None),('LK-MPA-ADAMSBRIDGE','Marine National Park',None),('LK-PA-VANKALAI','Sanctuary',None),('LK-PA-KOKKILAI','Sanctuary',None),
                  ('LK-PA-CHUNDIKKULAM','National Park',None),('LK-PA-BUNDALA','National Park',None),('LK-PA-YALA','National Park',None),('LK-PA-KUMANA','National Park',None),('LK-PA-WILPATTU','National Park',None),('LK-MPA-RUMASSALA','Sanctuary',None)]:
    rule(z,'no_take_without_permit',f'{d}: no fishing or taking of any aquatic animal or plant without a DWC permit (free permits possible for customary village subsistence fishing). Recreational fishing banned in MPAs (2319/19 reg. 8(6)).',
         'Fauna and Flora Protection Ordinance s.6A (inserted by Act No. 22 of 2009)', ref, None, source_url='https://faolex.fao.org/docs/pdf/SRL022041.pdf', verified_from='act_text',
         notes='s.6A applies to National Reserves (not Strict Natural Reserves) and to Sanctuaries on state land. Marine National Parks may allow traditional practices with conditions (DWC).')
rule('LK-FMA-NEGOMBO','gear_ban','Banned: trawl, push net, moxi net, gill/trammel nets on coral reefs or rocks, digging polychaete worms. Licences must be endorsed for Negombo Lagoon.','Negombo Lagoon FMA Regulations 1998 reg. 3-4','1038/16','1998-07-30',gears='trawl; push net; moxi net; gill/trammel net on reefs',source_url=U.get(88),verified_from='gazette_ocr')
rule('LK-FMA-NEGOMBO','no_fishing_buffer','All fishing banned within 150 m of the lagoon shores and islands except stake nets, cast nets, crab traps, small shrimp nets, rod/handline, manual traps and eel traps.','Negombo Lagoon FMA Regulations 1998 reg. 8','1038/16','1998-07-30',source_url=U.get(88),verified_from='gazette_ocr')
rule('LK-FMA-NEGOMBO','time_window','Trammel (disco) nets only 18:00–06:00; ≤ 600 m of head-rope per operation.','Negombo Lagoon FMA Regulations 1998 reg. 5-7','1038/16','1998-07-30',gears='trammel net',hours='18:00-06:00',source_url=U.get(88),verified_from='gazette_ocr')
rule('LK-FMA-REKAWA','gear_limit','Residents only; cast nets and drift nets only, plus ≤ 25 jakotuwa (no new ones); mesh ≥ 3 in for fish and ≥ 3/4 in for prawns; net ≤ 145 m; no mechanised craft; drift nets only in Maha Eliya; permit required.','Rekawa Lagoon FMA Regulations 1998','1067/4','1999-02-16',gears='all nets except cast/drift; mechanised craft',source_url=U.get(95),verified_from='gazette_ocr')
rule('LK-FMA-MUNDEL','gear_ban','No trap nets or drag nets; no drift nets with mesh < 5.1 cm (2 in).','Old Dutch Canal and Mundal Lagoon Fishing Regulations 1996','916/11','1996-03-28',gears='trap net; drag net; drift net <2 in',source_url=U.get(128),verified_from='gazette_ocr')
rule('LK-FMA-CHILAW','gear_limit','Harasdel only from 1 mile south of Chilaw Bridge, ≥ 100 m apart, mesh ≥ 4 cm (1.5 in). Management plan 2024 adds further measures (not parsed).','Chilaw Lagoon Fisheries Regulations 1996; Chilaw Lagoon plan','916/12','1996-03-28',gears='harasdel',source_url=U.get(134),verified_from='gazette_ocr')
rule('LK-FMA-BATTICALOA','gear_ban','Drag net (karaivalai/madel) banned in the area; drift nets < 3 in banned in Sector 2; no new kottus/enclosures without committee approval.','Fishery Management (Batticaloa Lagoon) Regulations 2001','1167/3','2001-01-15',gears='drag net; drift net <3 in (sector 2)',source_url=U.get(156),verified_from='gazette_ocr')
rule('LK-FMA-MATARA-THOTAMUNA','gear_limit','Only Second-Schedule gears (madel, ahuranadel, ketayapanna, maruwel panna, cast nets, lobster nets); drift nets only > 375 m from Hambiyawa; lobster only in specified waraya; madel only Jan–Mar and no nylon nets.','Fisheries Management (Matara District, Thotamuna, Ginigasmulla) Regulations 2000','1149/3','2000-09-12',months='madel closed 4-12',source_url=U.get(151),verified_from='gazette_ocr')
rule('LK-NILWELLA-HARBOUR','gear_ban','Rod and line only.','Nilwella Fisheries Regulations No.1 of 2011','1711/4','2011-06-20',gears='all gear except rod & line',source_url=U.get(207))
rule('LK-CUTTLEFISH-UDAPPUWA','gear_limit','Cuttlefish FADs only > 8 km offshore at ≥ 16 m depth, deployed Jan–Mar only, ≤ 10 per boat per week; GPS-registered; no surface buoys.','Cuttlefish fishing regulations (Udappuwa & Semuthu Thoduwa)','1733/23','2011-11-23',gears='FAD placement',species='cuttlefish (Sepiidae)',months='FAD placement only 1-3',source_url=U.get(58),verified_from='gazette_ocr')
rule('LK-FMA-SOUTH-MATARA-GALLE','permit_required','Live ornamental fish/lobster only with an endorsed licence; ≤ 20/25 gillnet pieces; 06:00–18:00 only.','Regulations 2012','1770/25','2012-08-10',hours='06:00-18:00',species='ornamental fish; lobster',source_url=U.get(64))
rule('LK-FMA-SOUTH-HAMBANTOTA','permit_required','Chank/lobster only with an endorsed licence (one per category); gillnet limits; logbooks.','Regulations 2012','1774/36','2012-09-07',species='Turbinella pyrum; lobster',source_url=U.get(70))
rule('LK-FMA-MADIHA-POLHENA','management_area','Declared Fishery Management Area (s.31); no area-specific regulations found in the DFAR register.','FARA s.31(1)(a) Order','1191/6','2001-07-02',source_url=U.get(172),verified_from='gazette_ocr')
rule('LK-GAMPAHA-PROHIB-2011','temporary_closure','All fishing prohibited in the charted area off Gampaha, April 2011 to 31 March 2013.','FARA s.34 notices','1702/2','2011-04-18',status='expired',source_url=U.get(55),notes='Extended by 1784/4 (12.11.2012) and 1801/28 (14.03.2013).')
rule('LK-RES-BOLGODA','gear_limit','Mesh ≥ 4 in; nets of 2.5 in+ mesh may not be used for prawns in Aug–Sep; no mechanised boats.','Bolgoda Reservoir (Fishing Operations) Regulations 2007','1493/18','2007-04-20',months='8,9 (prawn nets)',source_url=U.get(46),verified_from='gazette_ocr')
rule('LK-FMA-PARAKRAMA','gear_limit','Gill nets only, mesh ≥ 4 in (101.6 mm); no fishing 09:00–15:00.','Parakrama Samudraya FMA Regulations 2002','1255/24','2002-09-26',gears='all except gill net',hours='closed 09:00-15:00',source_url=U.get(177),verified_from='gazette_ocr')
for z in [z for z in zones if z['zone_type'] == 'boundary_line']:
    rule(z['zone_id'],'foreign_fishing_ban','No fishing by foreign boats on the Sri Lankan side without a licence/permit (Indian trawlers crossing the IMBL fish illegally; bottom trawling is banned for everyone).',
         'Fisheries (Regulation of Foreign Fishing Boats) Act No. 59 of 1979 (as amended by Act No. 1 of 2018); FARA s.28A',None,None,verified_from='secondary',source_url='https://www.marineregions.org/',
         notes='Act text not downloaded in this build; cited from secondary knowledge. Verify before public use.')

# ---------------- species ----------------
S = []
def sp(name, rule_type, detail, legal_basis, instrument, date=None, en=None, si=None, ta=None, applies='Sri Lanka Waters', status='in_force', src=None, verified='gazette_text', notes=None):
    S.append(dict(scientific_name=name, common_name_en=en, sinhala_name=si, tamil_name=ta, rule_type=rule_type, rule_detail=detail, applies_in=applies,
                  legal_basis=legal_basis, instrument=instrument, instrument_date=date, status=status, verified_from=verified, source_url=src, notes=notes))
sp('Cephalopholis sonnerati','total_ban','No catch, possession, transport, purchase, display, sale or export.','Prohibition of Catching Fish Species Thambuwa Regulations 2017 (FARA s.29, 61)','Gazette Ext. 2014/4','2017-04-11',en='Tomato hind',si='Thambuwa',src=U.get(82))
for n,e in [('Alopias vulpinus','Common thresher shark'),('Alopias superciliosus','Bigeye thresher shark'),('Alopias pelagicus','Pelagic thresher shark'),('Carcharhinus longimanus','Oceanic whitetip shark'),('Rhincodon typus','Whale shark')]:
    sp(n,'total_ban','No catch in Sri Lanka Waters (research exception). On the high seas: no catch, retention, transhipment, landing or sale.','Shark Fisheries Management Regulations 2015 + Shark Fisheries Management (High Seas) Regulations 2015','Gazette Ext. 1938/2','2015-10-26',en=e,applies='Sri Lanka Waters + high seas (SL vessels)',src=U.get(213))
sp('Rhincodon typus','gear_restriction','No deliberate purse-seine sets in areas frequented by whale sharks (high seas).','Shark Fisheries Management (High Seas) Regulations 2015 reg. 5','Gazette Ext. 1938/2','2015-10-26',en='Whale shark',applies='high seas (SL vessels)',src=U.get(213))
sp('Selachii','finning_ban','No finning; fins must stay naturally attached when retained, transhipped or landed; release live sharks, especially juveniles and pregnant females.','Shark Fisheries Management Regulations 2015 regs 3-4','Gazette Ext. 1938/2','2015-10-26',en='All sharks',src=U.get(213))
sp('Panulirus ornatus','size_limit','Carapace length ≥ 10 cm (tail ≥ 14 cm if no carapace); no soft-shell; no berried females or removal of eggs/pleopods.','Lobster Fisheries Management Regulations 2000 regs 4-5','Gazette Ext. 1123/2','2000-03-13',en='Ornate spiny lobster',src=U.get(146),verified='gazette_ocr')
for n,e in [('Panulirus homarus','Scalloped spiny lobster'),('Panulirus longipes','Longlegged spiny lobster'),('Panulirus versicolor','Painted spiny lobster'),('Panulirus penicillatus','Pronghorn spiny lobster'),('Panulirus polyphagus','Mud spiny lobster')]:
    sp(n,'size_limit','Carapace length ≥ 6 cm (tail ≥ 10 cm); no soft-shell; no berried females or removal of eggs.','Lobster Fisheries Management Regulations 2000 regs 4-5','Gazette Ext. 1123/2','2000-03-13',en=e,src=U.get(146),verified='gazette_ocr')
sp('Panulirus','seasonal_closure','No lobster fishing in February, September and October (all Sri Lanka sea areas).','FARA s.34 notice','Gazette Ext. 1601/36','2009-05-15',en='Spiny lobsters',src=U.get(203),verified='gazette_ocr')
sp('Panulirus','export_restriction','Export only under a DG licence; no export of spiny/slipper lobster, flesh or tails in February and September; selling flesh needs a permit.','Lobster Fisheries Management Regulations 2000 regs 6-9','Gazette Ext. 1123/2','2000-03-13',en='Spiny lobsters',src=U.get(146),verified='gazette_ocr')
sp('Scyllaridae','berried_ban','No berried slipper lobsters; no egg removal; export only under licence (none in Feb/Sep).','Lobster Fisheries Management Regulations 2000 regs 5, 8','Gazette Ext. 1123/2','2000-03-13',en='Slipper lobsters',src=U.get(146),verified='gazette_ocr')
sp('Turbinella pyrum','size_limit','No possession, purchase, sale, transport or export of chank < 70 mm diameter; harvest only with a licence; no dredging/trawling; permits for possession; export licence.','Chank Fisheries Management and Export Regulations 2003','Gazette Ext. 1298/1','2003-07-21',en='Sacred chank',si='Hakgediya',src=U.get(183),verified='gazette_ocr')
sp('Scylla serrata','size_limit','Carapace width ≥ 130 mm; no berried crabs (release alive); licence required.','Mud Crab Fishery Management Regulations 2024','Gazette Ext. 2371/35','2024-02-15',en='Giant mud crab',src=U.get(219))
sp('Portunus pelagicus','size_limit','No processing or export of crabs < 100 g wet weight; gillnet mesh ≥ 4.5 in.','Blue Swimming Crab Fishery Management Regulations 2022','Gazette Ext. 2277/04','2022-04-25',en='Blue swimming crab',src=U.get(216))
for n in ['Cephalopholis argus','Cephalopholis boenak','Cephalopholis formosa','Cephalopholis miniata','Cephalopholis sonnerati','Epinephelus areolatus','Epinephelus caeruleopunctatus','Epinephelus hexagonatus','Epinephelus malabaricus','Epinephelus merra','Epinephelus morrhua','Epinephelus tauvina','Epinephelus tukula','Epinephelus undulosus','Plectropomus laevis','Lates calcarifer']:
    sp(n,'export_permit_live','Added in 1999 to Part II (live export restricted: DFAR permit required).','Export and Import of Live Fish Regulations 1998 (Gazette Ext. 1036/13) reg. 3, as amended','Gazette Ext. 1098/3','1999-09-20',src=U.get(294),verified='gazette_ocr')
for n in ['Chaetodon semeion','Centropyge bispinosa','Pygoplites diacanthus','Coris aygula','Labroides bicolor','Pterois radiata','Platax pinnatus','Epinephelus lanceolatus','Epinephelus flavocaeruleus','Plectorhinchus obscurus','Plectorhinchus albovittatus','Chrysiptera kuiteri']:
    sp(n,'export_ban_live','Schedule Part I: export in live form PROHIBITED.','Export and Import of Live Fish Regulations 1998 reg. 2','Gazette Ext. 1036/13','1998-07-16',src=U.get(298),verified='gazette_ocr',notes='Marine part of Part I only; freshwater species omitted.')
for n in ['Chaetodon octofasciatus','Chaetodon ornatissimus','Chaetodon falcula','Chaetodon xanthocephalus','Chaetodon ephippium','Chaetodon unimaculatus','Chaetodon madagascariensis','Chaetodon bennetti','Chaetodon meyeri','Chaetodon triangulum','Heniochus monoceros','Heniochus pleurotaenia','Centropyge flavipectoralis','Balistoides conspicillum','Pseudobalistes fuscus','Variola louti','Variola albimarginata']:
    sp(n,'export_permit_live','Schedule Part II: live export only under a DFAR permit.','Export and Import of Live Fish Regulations 1998 reg. 3','Gazette Ext. 1036/13','1998-07-16',src=U.get(298),verified='gazette_ocr',notes='Marine part of Part II only.')
# FFPO Schedule II (strictly protected) marine/estuarine
for n,e,s_,t_ in [('Balaenoptera musculus','Blue whale','Thalmaha','Thimingila'),('Balaenoptera physalus','Fin whale','Thalmaha','Thimingila'),('Megaptera novaeangliae','Humpback whale','Thalmaha','Thimingila'),
                  ('Physeter macrocephalus','Sperm whale','Thalmaha',None),('Kogia breviceps','Pygmy sperm whale','Thalmaha',None),('Kogia sima','Dwarf sperm whale','Thalmaha',None),
                  ('Delphinus delphis','Common dolphin','Mulla','Pomigra'),('Dugong dugon','Dugong','Muhudu Ura','Kadaipudru'),('Crocodylus porosus','Saltwater crocodile','Geta Kimbula','Semmukku muthalei'),
                  ('Caretta caretta','Loggerhead sea turtle','Olugedi Kesbawa / Kannadi Kesbawa','Perunthalai amai'),('Chelonia mydas','Green turtle','Gal Kasbawa / Mas Kasbawa / Vali Kesbawa','Pal amai'),
                  ('Eretmochelys imbricata','Hawksbill sea turtle','Pothu Kasbawa / Leli Kesbawa','Nana amai'),('Lepidochelys olivacea','Olive ridley sea turtle','Battu Kesbawa / Mada Kesbawa','Pul amai'),
                  ('Dermochelys coriacea','Leatherback sea turtle','Dara Kesbawa / Thun Dara Kesbawa','Dhoni amai')]:
    sp(n,'total_ban','Strictly protected: no killing, capture, possession, sale or transport.','Fauna and Flora Protection Ordinance s.30, Schedule II (Act No. 22 of 2009)','FFPO (Amendment) Act No. 22 of 2009','2009-01-01',en=e,si=s_,ta=t_,src='https://www.env.gov.lk/web/images/downloads/acts/fauna_and_flora_protection_amendment_act_2009.pdf',verified='act_text',
       notes='Other mammals not in Schedule I (incl. all other cetaceans) are also protected under s.30. Sinhala/Tamil names are the romanised forms printed in the Act. instrument_date is year only.')
for n,e in [('Pterois radiata','Clearfin lionfish'),('Centropyge bispinosa','Twospined angelfish'),('Pygoplites diacanthus','Regal angelfish'),('Coris aygula','Clown coris'),('Labroides bicolor','Bicolor cleaner wrasse'),('Chaetodon semion','Dotted butterflyfish'),('Platax pinnatus','Dusky batfish')]:
    sp(n,'total_ban','Protected fish: no catch, kill, possession, sale, transport or export (incl. eggs).','FFPO s.31A, Schedule VI (Act No. 22 of 2009)','FFPO (Amendment) Act No. 22 of 2009','2009-01-01',en=e,src='https://www.env.gov.lk/web/images/downloads/acts/fauna_and_flora_protection_amendment_act_2009.pdf',verified='act_text')
inv = [('Dardanus megistos','Red hermit crab'),('Hymenocera picta','Harlequin (painted) shrimp'),('Enoplometopus','Reef lobsters'),('Cerianthus','Sand / tube anemones'),('Ceriantharia','Tube anemones'),
       ('Pocillopora',None),('Stylophora',None),('Seriatopora','Birdsnest coral'),('Acropora','Table coral'),('Montipora','Velvet coral'),('Astreopora',None),('Pavona',None),('Leptoseris',None),('Pachyseris speciosa',None),
       ('Coscinaraea',None),('Fungiidae','Mushroom corals'),('Favia',None),('Favites','Pineapple coral'),('Platygyra','Brain coral'),('Leptoria phrygia','Brain coral'),('Diploastrea heliopora',None),('Goniastrea',None),
       ('Hydnophora','Horn coral'),('Merulina','Cabbage coral'),('Symphyllia',None),('Lobophyllia',None),('Acanthastrea',None),('Echinophyllia',None),('Pectinia','Carnation coral'),('Euphyllia',None),
       ('Plerogyra sinuosa','Bubble coral'),('Physogyra','Bubble coral'),('Catalaphyllia jardinei','Elegance coral'),('Tubastraea','Sun coral'),('Turbinaria','Turban / cup coral'),('Porites','Pore coral'),
       ('Goniopora',None),('Millepora','Fire corals'),('Distichopora violacea','Scarlet coral'),('Stylaster','Lace coral'),('Antipatharia','Black corals'),('Alcyonacea','Soft corals & sea fans'),('Ellisellidae','Sea whips'),
       ('Sabellastarte','Fan worms'),('Spirobranchus','Christmas-tree worms'),('Tibia insulaechorab',None),('Charonia tritonis',"Triton's trumpet"),('Strombus listeri',"Lister's conch"),('Lambis lambis','Common spider conch'),
       ('Lambis chiragra','Chiragra spider conch'),('Cypraea tigris','Tiger cowrie'),('Talparia talpa','Mole cowrie'),('Leporicypraea mappa','Map cowrie'),('Arestorides argus','Eyed cowrie'),('Cypraecassis rufa','Bullmouth helmet'),
       ('Cassis cornuta','Horned helmet'),('Chicoreus palmarosae','Rose-branch murex'),('Hexabranchus','Spanish dancer'),('Tridacna','Giant clams'),('Nautilus','Nautilus'),('Argonauta','Paper nautilus'),
       ('Heterocentrotus mamillatus','Slate pencil urchin'),('Pseudocolochirus','Royal sea cucumber')]
for n,e in inv:
    sp(n,'total_ban','Protected invertebrate: no collection, possession, sale, transport or export.','FFPO s.31B, Schedule VII (Act No. 22 of 2009)','FFPO (Amendment) Act No. 22 of 2009','2009-01-01',en=e,src='https://www.env.gov.lk/web/images/downloads/acts/fauna_and_flora_protection_amendment_act_2009.pdf',verified='act_text',
       notes='Names normalised from the schedule spelling (e.g. Tibia insulae→Tibia insulaechorab, Hymenocera elegans→H. picta, Cypraea talpa→Talparia talpa, Cypraea mappa→Leporicypraea mappa, Cypraea argus→Arestorides argus, Gorgonacea folded into Alcyonacea). Schedule lists more coral genera; family/order rows cover them.')
# IOTC
IO='https://iotc.org/sites/default/files/documents/2026/09/IOTC-2026-WPEB22AS-05_-_CMMs_0.pdf'
for n,e in [('Carcharhinus longimanus','Oceanic whitetip shark'),('Alopiidae','Thresher sharks'),('Rhincodon typus','Whale shark')]:
    sp(n,'retention_ban_rfmo','No retention (scientific sampling of dead fish by observers only).','IOTC Resolution 25/08 (supersedes 12/09, 13/05, 13/06, 17/05, 18/02); binding on Sri Lanka as an IOTC member','IOTC Res. 25/08','2026-01-01',en=e,applies='IOTC area (SL-flagged vessels)',src=IO,verified='rfmo_document')
sp('Mobulidae','retention_ban_rfmo','No setting on or targeting; no retention, transhipment, landing or storage; subsistence fishers may not sell.','IOTC Resolution 26/03 (supersedes 19/03)','IOTC Res. 26/03','2026-05-01',en='Manta and devil rays',applies='IOTC area',status='adopted_2026_supersedes_19_03',src=IO,verified='rfmo_document',notes='Adopted at S30 (May 2026). 19/03 had the same retention ban. instrument_date approximate (session month).')
for n,e in [('Isurus oxyrinchus','Shortfin mako'),('Isurus paucus','Longfin mako')]:
    sp(n,'release_required_rfmo','Release when brought alongside; may be retained only if dead at haulback (verified by EMS/observer); no transhipment.','IOTC Resolution 25/09','IOTC Res. 25/09',None,en=e,applies='IOTC area',src=IO,verified='rfmo_document')
sp('Cheloniidae','bycatch_mitigation_rfmo','Marine turtle bycatch: safe handling/release and reporting.','IOTC Resolution 12/04','IOTC Res. 12/04',None,en='Hard-shelled sea turtles',applies='IOTC area',src=IO,verified='rfmo_document')
sp('Cetacea','bycatch_mitigation_rfmo','No purse-seine sets around cetaceans; safe release; reporting (vessels on IOTC record).','IOTC Resolution 23/06 (supersedes 13/04)','IOTC Res. 23/06',None,en='Whales and dolphins',applies='IOTC area',src=IO,verified='rfmo_document')
# CITES (Sri Lanka party since 1979)
C26='https://cites.org/sites/default/files/eng/app/2026/E-Appendices-2026-03-05.pdf'
FWS='https://www.fws.gov/sites/default/files/documents/2026-01/ole-public-bulletin-cites-cop20-amendments-to-appendices-i-and-ii-pb-26-001-01_13_2026.pdf'
cites = [('Carcharhinus longimanus','I','Oceanic whitetip shark',FWS,'cop20_bulletin'),('Mobulidae','I','Manta & devil rays',FWS,'cop20_bulletin'),('Rhincodon typus','I','Whale shark',FWS,'cop20_bulletin'),
         ('Pristidae','I','Sawfishes',C26,'secondary'),('Cheloniidae','I','Sea turtles',C26,'secondary'),('Dermochelys coriacea','I','Leatherback turtle',C26,'secondary'),('Dugong dugon','I','Dugong',C26,'secondary'),
         ('Balaenoptera musculus','I','Blue whale',C26,'secondary'),('Megaptera novaeangliae','I','Humpback whale',C26,'secondary'),('Physeter macrocephalus','I','Sperm whale',C26,'secondary'),
         ('Carcharhinidae','II','Requiem sharks (all other species)',C26,'secondary'),('Sphyrnidae','II','Hammerhead sharks',C26,'secondary'),('Alopias','II','Thresher sharks',C26,'secondary'),
         ('Isurus','II','Mako sharks',C26,'secondary'),('Carcharodon carcharias','II','White shark',C26,'secondary'),('Rhinidae','II','Wedgefishes (zero export quota, wild, commercial)',FWS,'cop20_bulletin'),
         ('Glaucostegus','II','Giant guitarfishes (zero export quota, wild, commercial)',FWS,'cop20_bulletin'),('Mustelus','II','Smooth-hounds (from 2026)',FWS,'cop20_bulletin'),('Centrophoridae','II','Gulper sharks (from 2026)',FWS,'cop20_bulletin'),
         ('Hippocampus','II','Seahorses',C26,'secondary'),('Cheilinus undulatus','II','Humphead wrasse',C26,'secondary'),('Tridacnidae','II','Giant clams',C26,'secondary'),
         ('Scleractinia','II','Hard corals',C26,'secondary'),('Antipatharia','II','Black corals',C26,'secondary'),('Milleporidae','II','Fire corals',C26,'secondary'),('Stylasteridae','II','Lace corals',C26,'secondary'),
         ('Holothuria fuscogilva','II','White teatfish',C26,'secondary'),('Holothuria nobilis','II','Black teatfish',C26,'secondary'),('Holothuria whitmaei','II','Black teatfish (Pacific)',C26,'secondary'),
         ('Thelenota','II','Thelenota sea cucumbers',C26,'secondary'),('Holothuria lessoni','II','Golden sandfish (listing effective 2027-06-05)',FWS,'cop20_bulletin'),('Cetacea','II','All cetaceans not in App. I',C26,'secondary')]
for n,app,e,src,ver in cites:
    sp(n,f'cites_appendix_{app}',('No commercial international trade in wild specimens (App. I).' if app=='I' else 'International trade only with CITES permits + non-detriment finding (App. II).') + ' Sri Lanka implements CITES through the FFPO / DWC and DFAR export regulations (2023/51).',
       'CITES Appendices (valid from 05.03.2026)','CITES',('2027-06-05' if 'lessoni' in n else '2026-03-05'),en=e,applies='international trade (export/import)',status=('delayed_effect' if 'lessoni' in n else 'in_force'),src=src,verified=ver,
       notes=('cites.org is behind a Cloudflare challenge from the box; listing taken from the CoP20 notice (FWS bulletin) or, for older listings, from the CITES appendices PDF index plus general knowledge. Check against the official PDF before public use.' if ver=='secondary' else None))

# ---------------- WoRMS ----------------
cache_p = f'{RAW}/worms_cache.json'
cache = json.load(open(cache_p)) if os.path.exists(cache_p) else {}
def worms(name):
    if name in cache: return cache[name]
    url = 'https://www.marinespecies.org/rest/AphiaRecordsByName/' + urllib.parse.quote(name) + '?like=false&marine_only=false'
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'futoura-hackathon/1.0'}), timeout=30) as r:
            body = r.read()
        recs = json.loads(body) if body else []
    except Exception as ex:
        recs = {'error': str(ex)}
    cache[name] = recs; time.sleep(0.3)
    return recs
for s in S:
    recs = worms(s['scientific_name'])
    if isinstance(recs, list) and recs:
        acc = [r for r in recs if r.get('status') == 'accepted'] or recs
        r = acc[0]
        s.update(aphia_id=r['AphiaID'], worms_status=r['status'], worms_valid_aphia_id=r.get('valid_AphiaID'), worms_valid_name=r.get('valid_name'), worms_rank=r.get('rank'))
    else:
        s.update(aphia_id=None, worms_status='not_found' if isinstance(recs, list) else 'lookup_error', worms_valid_aphia_id=None, worms_valid_name=None, worms_rank=None)
json.dump(cache, open(cache_p, 'w'))

# ---------------- regulations register ----------------
rows = json.load(open(f'{RAW}/dfar_rows.json'))
MONTHS = {m: i for i, m in enumerate(['JANUARY','FEBRUARY','MARCH','APRIL','MAY','JUNE','JULY','AUGUST','SEPTEMBER','OCTOBER','NOVEMBER','DECEMBER'], 1)}
reg = []
for r in rows:
    if not r['name_en'] or not re.search(r'\(Engl', r['name_en']): continue
    rid = r['row_id']; txt = ''; mode = None
    for suf, m in [('.txt', 'text_layer'), ('.ocr.txt', 'ocr')]:
        p = f'{RAW}/gazettes/dfar_{rid}{suf}'
        if os.path.exists(p):
            t = open(p, errors='ignore').read()
            if len(t.split()) > 50 and (mode is None):
                txt, mode = t, m
    num = re.search(r'(\d{3,4})\s*/\s*(\d{1,2})', r['number'] or '')
    gaz_date = None
    if txt and num:
        pat = re.compile(r'No\.?\s*' + num.group(1) + r'\s*/\s*0?' + str(int(num.group(2))) + r'\s*[-–—.]+\s*(?:[A-Za-z]+DAY)?[\s,]*([A-Za-z]+)\s*(\d{1,2})\s*,?\s*(\d{4})', re.I)
        m = pat.search(txt)
        if m and m.group(1).upper() in MONTHS:
            try: gaz_date = datetime.date(int(m.group(3)), MONTHS[m.group(1).upper()], int(m.group(2))).isoformat()
            except ValueError: pass
    reg.append(dict(dfar_row_id=rid, topic=r['topic'], title=re.sub(r'\s*\(Engl\w*\)\s*', '', r['name_en']).strip(), gazette_ref=(r['number'] or '').strip(),
                    gazette_no=(f'{num.group(1)}/{num.group(2)}' if num else None), register_date=r['date'], gazette_date_from_pdf=gaz_date,
                    date_check=('match' if gaz_date == r['date'] else ('mismatch' if gaz_date else 'not_checked')),
                    pdf_downloaded=os.path.exists(f'{RAW}/gazettes/dfar_{rid}.pdf'), text_source=mode, pdf_url=r['pdf_url'],
                    licence='Sri Lanka Government publication – public legal text; copyright status unclear (cite, link, quote; avoid bulk re-hosting PDFs)'))

# ---------------- QC ----------------
qc = {'generated': datetime.datetime.now().astimezone().isoformat(timespec='seconds'), 'zones': {}, 'species': {}, 'rules': {}, 'register': {}}
zrows = []
features = []
for z in zones:
    g = z.pop('geometry')
    rec = dict(z)
    if g is not None and not g.is_empty:
        g = make_valid(g)
        if g.geom_type == 'GeometryCollection':
            polys = [p for p in g.geoms if p.geom_type in ('Polygon', 'MultiPolygon')]
            lines = [p for p in g.geoms if p.geom_type in ('LineString', 'MultiLineString')]
            g = unary_union(polys) if polys else unary_union(lines)
        line = g.geom_type in ('LineString', 'MultiLineString')
        sea = g if line else g.difference(LAND)
        rec.update(geometry_type=g.geom_type, is_valid=bool(g.is_valid), in_bbox=bool(BBOX.contains(g)) if z['zone_type'] not in ('maritime_zone','boundary_line') else bool(BBOX.intersects(g)),
                   area_km2=None if line else round(area_km2(g), 3), sea_area_km2=None if line else round(area_km2(sea), 3),
                   sea_fraction=None if line else round(area_km2(sea) / max(area_km2(g), 1e-9), 3), touches_sea=bool(line or not sea.is_empty),
                   centroid_lon=round(g.representative_point().x, 5), centroid_lat=round(g.representative_point().y, 5),
                   bbox_minx=round(g.bounds[0], 4), bbox_miny=round(g.bounds[1], 4), bbox_maxx=round(g.bounds[2], 4), bbox_maxy=round(g.bounds[3], 4))
        features.append({'type': 'Feature', 'id': z['zone_id'], 'properties': {k: v for k, v in rec.items()}, 'geometry': mapping(g)})
    else:
        rec.update(geometry_type=None, is_valid=None, in_bbox=None, area_km2=None, sea_area_km2=None, sea_fraction=None, touches_sea=None,
                   centroid_lon=None, centroid_lat=None, bbox_minx=None, bbox_miny=None, bbox_maxx=None, bbox_maxy=None)
    sf_ = rec.get('sea_fraction')
    rec['water_context'] = (None if rec.get('geometry_type') is None else 'line' if sf_ is None else 'marine' if sf_ >= 0.9 else 'mixed_land_sea' if sf_ > 0.01 else 'lagoon_or_inland_water (Natural Earth land mask includes lagoons)')
    rec['n_rules'] = sum(1 for r in R if r['zone_id'] == z['zone_id'])
    zrows.append(rec)
zdf = pd.DataFrame(zrows)
rdf = pd.DataFrame(R)
sdf = pd.DataFrame(S)
gdf = pd.DataFrame(reg)

# date validation
def valid_date(s):
    if s is None or (isinstance(s, float) and math.isnan(s)): return True
    try: d = datetime.date.fromisoformat(s); return datetime.date(1900,1,1) <= d <= datetime.date(2027,12,31)
    except Exception: return False
qc['zones'] = dict(rows=len(zdf), with_geometry=int(zdf.geometry_type.notna().sum()), invalid=int((zdf.is_valid == False).sum()), outside_bbox=zdf.loc[zdf.in_bbox == False, 'zone_id'].tolist(),
                   no_sea_overlap=zdf.loc[zdf.touches_sea == False, 'zone_id'].tolist(), no_sea_overlap_note='all are lagoon/inland-water zones (Rekawa, Mundel lagoons; Kumana, Bundala lagoon parks): legally part of Sri Lanka Waters but masked as land by Natural Earth 1:10m', water_context_counts=zdf.water_context.value_counts().to_dict(), bbox_rule='polygons must lie inside lon 77-85 / lat 4-11; maritime_zone and boundary_line only need to intersect (EEZ reaches 2.57N-11.45N, 85.23E)', geometry_quality_counts=zdf.geometry_quality.value_counts().to_dict(),
                   area_vs_official=[dict(zone_id=r.zone_id, area_km2=r.area_km2, official_km2=r.official_area_km2) for r in zdf.itertuples() if isinstance(getattr(r, 'official_area_km2', None), float) and not math.isnan(r.official_area_km2)])
qc['rules'] = dict(rows=len(rdf), bad_dates=rdf.loc[~rdf.gazette_date.apply(valid_date), 'rule_id'].tolist(), orphan_zone_ids=sorted(set(rdf.zone_id) - set(zdf.zone_id)),
                   status_counts=rdf.status.value_counts().to_dict(), restriction_type_counts=rdf.restriction_type.value_counts().to_dict(), verified_from_counts=rdf.verified_from.value_counts().to_dict())
qc['species'] = dict(rows=len(sdf), unique_taxa=int(sdf.scientific_name.nunique()), aphia_found=int(sdf.aphia_id.notna().sum()), aphia_missing=sorted(sdf.loc[sdf.aphia_id.isna(), 'scientific_name'].unique().tolist()),
                     unaccepted_names=sorted({(a, b) for a, b, c in zip(sdf.scientific_name, sdf.worms_valid_name, sdf.worms_status) if c not in ('accepted', None, 'not_found', 'lookup_error')}),
                     bad_dates=sdf.loc[~sdf.instrument_date.apply(valid_date), 'scientific_name'].tolist(), rule_type_counts=sdf.rule_type.value_counts().to_dict())
qc['register'] = dict(rows=len(gdf), pdfs_downloaded=int(gdf.pdf_downloaded.sum()), text_source_counts=gdf.text_source.value_counts(dropna=False).astype(int).to_dict() if len(gdf) else {},
                      date_check_counts=gdf.date_check.value_counts().to_dict(), date_mismatches=gdf.loc[gdf.date_check == 'mismatch', ['dfar_row_id', 'gazette_no', 'register_date', 'gazette_date_from_pdf']].to_dict('records'))
# AphiaID sanity: positive ints
qc['species']['aphia_ids_positive_int'] = bool(all(int(a) > 0 for a in sdf.aphia_id.dropna()))

def write(df, name):
    df = df.copy()
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].apply(lambda v: v if v is None or isinstance(v, (str, bool, int, float)) else json.dumps(v, default=str))
    df.to_csv(f'{OUT}/{name}.csv', index=False)
    df.to_parquet(f'{OUT}/{name}.parquet', index=False)
write(zdf, 'zones'); write(rdf, 'zone_rules'); write(sdf, 'species_rules'); write(gdf, 'regulations_register')
json.dump({'type': 'FeatureCollection', 'name': 'sri_lanka_fishing_restriction_zones', 'crs': {'type': 'name', 'properties': {'name': 'urn:ogc:def:crs:OGC:1.3:CRS84'}},
           'features': features}, open(f'{OUT}/zones.geojson', 'w'), default=str)
json.dump(qc, open(f'{OUT}/qc_summary.json', 'w'), indent=2, default=str)
print(json.dumps(qc, indent=1, default=str)[:6000])
