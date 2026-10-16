import pandas as pd,numpy as np,json
from shapely.geometry import shape,Point
from shapely.strtree import STRtree
from shapely import contains_xy,union_all
e=pd.read_csv("/tmp/etopo60.csv",skiprows=[1])
la=np.sort(e.latitude.unique());lo=np.sort(e.longitude.unique())
Z=e.pivot(index="latitude",columns="longitude",values="z").reindex(index=la,columns=lo).values
dy=1852*(la[1]-la[0])*60;dx=dy*np.cos(np.deg2rad(la))[:,None]
gy,gx=np.gradient(Z,dy,axis=0),np.gradient(Z,axis=1)/dx
slope=np.degrees(np.arctan(np.hypot(gy,gx)))
L,O=np.meshgrid(la,lo,indexing="ij")
d=pd.DataFrame(dict(lat=L.ravel(),lon=O.ravel(),elev_m=Z.ravel(),slope_deg=slope.ravel().round(3)))
d["depth_m"]=(-d.elev_m).clip(lower=0)
d["is_water"]=(d.elev_m<0).astype(int)
d["shelf_lt200m"]=((d.elev_m<0)&(d.elev_m>-200)).astype(int)
d["trawlable_depth_10_200m"]=((d.elev_m<=-10)&(d.elev_m>-200)).astype(int)
d["upper_slope_200_1000m"]=((d.elev_m<=-200)&(d.elev_m>-1000)).astype(int)
g=json.load(open("coral_reefs_avoid/unep_wcmc_coral_reefs_v4_1_srilanka.geojson"))
reef=union_all([shape(f["geometry"]) for f in g["features"]])
d["coral_reef"]=contains_xy(reef.buffer(0.01),d.lon.values,d.lat.values).astype(int)  # cell centre within ~1 km of mapped reef
d["trawl_candidate"]=((d.trawlable_depth_10_200m==1)&(d.coral_reef==0)).astype(int)
d.to_parquet("seabed_shelf_habitat/shelf_habitat_grid_1arcmin.parquet",index=False)
d[d.is_water==1].to_csv("seabed_shelf_habitat/shelf_habitat_grid_1arcmin_water.csv",index=False)
print(len(d),d[["is_water","shelf_lt200m","trawlable_depth_10_200m","upper_slope_200_1000m","coral_reef","trawl_candidate"]].sum().to_dict())
