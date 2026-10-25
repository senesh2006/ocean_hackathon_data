"""Fetch GFW Sentinel-1 SAR vessel detections for northern Sri Lanka on the 0.1 deg monthly grid.

Usage (token is read from the environment, never printed):
    set GFW_TOKEN=...            (Windows)   |  export GFW_TOKEN=...   (Linux/Mac)
    python fetch_gfw_sar_north.py 2024-01-01 2025-01-01
Writes gfw_sar_north_monthly_0p1.csv and .parquet: one row per cell x month x matched flag
(matched=false = not broadcasting AIS, i.e. "dark"). Free GFW token, non-commercial terms.
Docs: https://globalfishingwatch.org/our-apis/documentation/docs/v3/4wings
"""
import os, sys, json, time, urllib.request, urllib.parse
import pandas as pd
TOKEN = (os.environ.get('GFW_TOKEN') or os.environ.get('GFW_API_TOKEN') or '').strip()
if not TOKEN: sys.exit('Set GFW_TOKEN in the environment first.')
start, end = (sys.argv[1:3] + ['2024-01-01', '2025-01-01'])[:2] if len(sys.argv) >= 3 else ('2024-01-01', '2025-01-01')
BBOX = [[78.9, 8.5], [81.5, 8.5], [81.5, 10.5], [78.9, 10.5], [78.9, 8.5]]
GEO = {"type": "Polygon", "coordinates": [BBOX]}
DATASET = 'public-global-sar-presence:latest'
def report(matched):
    qs = [('spatial-resolution', 'LOW'), ('temporal-resolution', 'MONTHLY'), ('spatial-aggregation', 'false'),
          ('datasets[0]', DATASET), ('date-range', f'{start},{end}'), ('format', 'JSON'),
          ('filters[0]', f"matched='{matched}'")]
    url = 'https://gateway.api.globalfishingwatch.org/v3/4wings/report?' + urllib.parse.urlencode(qs)
    req = urllib.request.Request(url, data=json.dumps({'geojson': GEO}).encode(), method='POST',
                                 headers={'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json', 'User-Agent': 'SplitWater-data/1.0'})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return json.load(r), r.headers.get('x-datasets')
        except urllib.error.HTTPError as e:
            if e.code in (429, 524) and attempt < 4: time.sleep(20 * (attempt + 1)); continue
            sys.exit(f'GFW HTTP {e.code}: {e.read()[:300]!r}')
rows = []
for matched in ('true', 'false'):
    js, ver = report(matched)
    for entry in js.get('entries', []):
        for _, arr in entry.items():
            for x in arr or []:
                val = x.get('detections', x.get('hours', x.get('vessel_ids')))
                rows.append(dict(month=str(x.get('date'))[:7], lat=x['lat'], lon=x['lon'], matched_ais=matched == 'true',
                                 detections=val, dataset_version=ver))
    time.sleep(2)  # GFW allows one report at a time per token
d = pd.DataFrame(rows)
if d.empty: sys.exit('No detections returned for this bbox/date range.')
d['cell_lat'] = (d.lat // 0.1 * 0.1 + 0.05).round(2); d['cell_lon'] = (d.lon // 0.1 * 0.1 + 0.05).round(2)
d.to_csv('gfw_sar_north_monthly_0p1.csv', index=False); d.to_parquet('gfw_sar_north_monthly_0p1.parquet', index=False)
print(d.groupby(['month', 'matched_ais']).detections.sum().unstack())
print('cells with any detection:', d[['cell_lat', 'cell_lon']].drop_duplicates().shape[0])
