import pandas as pd,numpy as np,xarray as xr,ephem,re
if 0:
  # indices
  L=open("climate_indices/raw_dmi_had_long.txt").read().split("\n")[1:]
  r=[]
  for l in L:
    p=l.split()
    if len(p)==13 and p[0].isdigit():
      for m,v in enumerate(p[1:],1):
        v=float(v)
        if v>-99: r.append(dict(year=int(p[0]),month=m,dmi=v))
  dmi=pd.DataFrame(r)
  o=pd.read_csv("climate_indices/raw_oni_cpc.txt",sep=r"\s+")
  cm={"DJF":1,"JFM":2,"FMA":3,"MAM":4,"AMJ":5,"MJJ":6,"JJA":7,"JAS":8,"ASO":9,"SON":10,"OND":11,"NDJ":12}
  o["month"]=o.SEAS.map(cm);o=o.rename(columns={"YR":"year","ANOM":"oni","SEAS":"oni_season"})[["year","month","oni_season","oni"]]
  ci=dmi.merge(o,on=["year","month"],how="outer").sort_values(["year","month"])
  ci["iod_phase"]=np.select([ci.dmi>=0.4,ci.dmi<=-0.4],["positive","negative"],"neutral")
  ci["enso_phase"]=np.select([ci.oni>=0.5,ci.oni<=-0.5],["el_nino","la_nina"],"neutral");ci.loc[ci.oni.isna(),"enso_phase"]=""
  ci.to_csv("climate_indices/dmi_oni_monthly.csv",index=False);print("ci",len(ci),ci.dropna(subset=["dmi"]).iloc[-1].to_dict(),ci.dropna(subset=["oni"]).iloc[-1].to_dict())
# GPCP
g=xr.open_dataset("/tmp/gpcp.nc",drop_variables=["time_bnds"]).precip.sel(lat=slice(2,13),lon=slice(75,87))
if g.lat.size==0: g=xr.open_dataset("/tmp/gpcp.nc",drop_variables=["time_bnds"]).precip.sel(lat=slice(13,2),lon=slice(75,87))
d=g.to_dataframe().reset_index().rename(columns={"precip":"precip_mm_day"});d.to_csv("rainfall/gpcp_v23_monthly_2.5deg.csv",index=False)
d["month"]=pd.to_datetime(d.time).dt.month;d.groupby(["month","lat","lon"]).precip_mm_day.mean().reset_index().to_csv("rainfall/gpcp_monthly_climatology_2.5deg.csv",index=False)
print("gpcp",len(d),d.time.max())
c=xr.open_dataset("/tmp/chirps.nc",decode_times=False)
v=c.precipitation;T=c["T"].values
t=pd.to_datetime("1960-01-01")+pd.to_timedelta((T).astype(int)*30.4375,unit="D") if "months since" in c["T"].attrs.get("units","") else None
units=c["T"].attrs.get("units","");print(units)
base=pd.Timestamp(re.search(r"since (\d{4}-\d{2}-\d{2})",units).group(1))
dates=[base+pd.DateOffset(months=int(np.floor(x))) for x in T]
df=v.to_dataframe().reset_index();df["date"]=df["T"].map(dict(zip(T,dates)));df=df.drop(columns="T").rename(columns={"X":"lon","Y":"lat","precipitation":"precip_mm_month"}).dropna()
df.to_csv("rainfall/chirps_v2_monthly_srilanka_land_0.05deg_2024_latest.csv",index=False)
isl=df.groupby("date").precip_mm_month.mean().reset_index().rename(columns={"precip_mm_month":"island_mean_precip_mm_month"});isl.to_csv("rainfall/chirps_island_mean_monthly.csv",index=False)
print("chirps",len(df),df.date.max())
# moon
rows=[]
for day in pd.date_range("2000-01-01","2027-12-31"):
  dt=ephem.Date(day.strftime("%Y/%m/%d")+" 18:30")  # midnight Sri Lanka
  m=ephem.Moon(dt);pn=ephem.previous_new_moon(dt);age=dt-pn
  rows.append(dict(date=day.date(),illumination_frac=round(m.moon_phase,4),moon_age_days=round(age,2),phase_angle_sin=round(np.sin(2*np.pi*age/29.530589),4),phase_angle_cos=round(np.cos(2*np.pi*age/29.530589),4),
   phase_name=["new","waxing_crescent","first_quarter","waxing_gibbous","full","waning_gibbous","last_quarter","waning_crescent"][int(((age/29.530589)*8+0.5))%8]))
pd.DataFrame(rows).to_csv("moon_phase/moon_daily_2000_2027_colombo_midnight.csv",index=False);print("moon",len(rows))
# monsoon calendar
s={1:"NE_monsoon",2:"NE_monsoon",3:"first_inter_monsoon",4:"first_inter_monsoon",5:"SW_monsoon",6:"SW_monsoon",7:"SW_monsoon",8:"SW_monsoon",9:"SW_monsoon",10:"second_inter_monsoon",11:"second_inter_monsoon",12:"NE_monsoon"}
pd.DataFrame([dict(month=m,season=s[m],sw_coast_rough_sea=int(5<=m<=9),east_coast_rough_sea=int(m in(11,12,1,2)),upwelling_south_coast_strength={6:3,7:3,8:3,5:2,9:2,12:1,1:1,2:1}.get(m,0)) for m in range(1,13)]).to_csv("monsoon_calendar/srilanka_monsoon_calendar.csv",index=False)
