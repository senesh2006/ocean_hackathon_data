import xarray as xr,numpy as np,pandas as pd
U="https://www.ncei.noaa.gov/thredds-ocean/dodsC/woa23/DATA/"
def get(var,code,grid,res,m):
  ds=xr.open_dataset(f"{U}{var}/netcdf/{grid}/{res}/woa23_{grid}_{code}{m:02d}_{'04' if res=='0.25' else '01'}.nc",decode_times=False)
  a=ds[f"{code}_an"].isel(time=0).sel(lat=slice(4,11),lon=slice(77,85)).load()
  return a
out={}
for var,code,grid,res in [("temperature","t","B5C2","0.25"),("salinity","s","B5C2","0.25"),("oxygen","o","all","1.00")]:
  rows=[]
  for m in range(1,13):
    a=get(var,code,grid,res,m); d=a.depth.values; v=a.values
    valid=~np.isnan(v); has=valid.any(0)
    last=np.where(has,valid.shape[0]-1-np.argmax(valid[::-1],0),0)
    bot=np.take_along_axis(v,last[None],0)[0]; bd=d[last]
    for i,la in enumerate(a.lat.values):
      for j,lo in enumerate(a.lon.values):
        if not has[i,j]: continue
        r=dict(month=m,lat=la,lon=lo,deepest_level_m=bd[i,j],**{f"{code}_bottom":bot[i,j]})
        for z in (0,50,100,200):
          k=np.where(d==z)[0]; r[f"{code}_{z}m"]=v[k[0],i,j] if len(k) else np.nan
        if code=="t":
          prof=v[:,i,j]; ok=~np.isnan(prof); dz=d[ok]; p=prof[ok]
          below=np.where(p<p[0]-0.5)[0]; r["mld_t0.5_m"]=dz[below[0]] if len(below) else dz[-1]
        rows.append(r)
    print(var,m,flush=True)
  df=pd.DataFrame(rows); out[code]=df
  df.to_csv(f"bottom_temp_salinity_oxygen_woa23/woa23_{var}_monthly_clim_{res}deg.csv",index=False)
out["t"][["month","lat","lon","mld_t0.5_m"]].to_csv("mixed_layer_depth/mld_from_woa23_temperature_monthly_clim_0.25deg.csv",index=False)
