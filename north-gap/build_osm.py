import json, pandas as pd
d=json.load(open('raw/osm_fishing_sites.json'))
rows=[]
for e in d['elements']:
    t=e.get('tags',{}); lat=e.get('lat',e.get('center',{}).get('lat')); lon=e.get('lon',e.get('center',{}).get('lon'))
    if lat is None: continue
    kind=('fish_market' if t.get('amenity')=='fish_market' else 'seafood_shop' if t.get('shop')=='seafood' else
          'harbour' if ('harbour' in t or t.get('landuse')=='harbour' or t.get('seamark:type')=='harbour' or t.get('leisure')=='marina') else
          'fishing_industrial' if t.get('industrial')=='fishing' else t.get('man_made','named_fishing_site'))
    name=t.get('name:en') or t.get('name') or ''
    fishy=any(k in (name+' '+json.dumps(t)).lower() for k in ['fish','anchorage','landing','harbour','harbor'])
    rows.append(dict(osm_type=e['type'],osm_id=e['id'],lat=round(lat,6),lon=round(lon,6),kind=kind,name=name,fishing_related=fishy or kind in('fish_market','seafood_shop','fishing_industrial'),
        cell_lat=round((lat//0.1)*0.1+0.05,2),cell_lon=round((lon//0.1)*0.1+0.05,2),north_bbox=(8.5<=lat<=10.5 and 78.9<=lon<=81.5),
        tags=json.dumps(t,ensure_ascii=False)))
o=pd.DataFrame(rows).drop_duplicates(['osm_type','osm_id'])
o['source_url']='https://www.openstreetmap.org/'+o.osm_type+'/'+o.osm_id.astype(str)
o.to_csv('osm_fishing_sites_srilanka.csv',index=False); o.to_parquet('osm_fishing_sites_srilanka.parquet',index=False)
print(len(o)); print(o.groupby(['north_bbox','kind']).size()); print('fishing_related',o.fishing_related.sum(),'north fishing_related',o[o.north_bbox&o.fishing_related].shape[0])
print(o[o.north_bbox&o.fishing_related][['name','kind','lat','lon']].head(40).to_string())
