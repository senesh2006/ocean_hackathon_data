import json, pandas as pd
rows=[]
for f,layer in [('raw/nsdi_fish_landing_centers.geojson','fish_landing_center'),('raw/nsdi_fishing_harbors.geojson','fishing_harbour')]:
    for ft in json.load(open(f))['features']:
        g=ft['geometry']; c=g.get('coordinates') if g else None
        ok=bool(c) and len(c)==2
        lon,lat=(c if ok else (None,None))
        p=ft['properties']
        rows.append(dict(layer=layer,objectid=p.get('objectid'),name=p.get('name'),description=p.get('description'),lat=lat,lon=lon,has_geometry=ok,
          cell_lat=round((lat//0.1)*0.1+0.05,2) if ok else None,cell_lon=round((lon//0.1)*0.1+0.05,2) if ok else None,
          north_bbox=bool(ok and 8.5<=lat<=10.5 and 78.9<=lon<=81.5),
          source_url=f'https://gisapps.nsdi.gov.lk/server/rest/services/Srilanka/Economy_Structure/MapServer/{5 if layer=="fish_landing_center" else 4}'))
d=pd.DataFrame(rows); d.to_csv('nsdi_fish_landing_centres_harbours.csv',index=False); d.to_parquet('nsdi_fish_landing_centres_harbours.parquet',index=False)
print(d.groupby(['layer','has_geometry','north_bbox']).size()); print(d[d.north_bbox][['layer','name','lat','lon']].to_string())
