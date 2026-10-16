import subprocess,io,time,pandas as pd,sys
CW="https://coastwatch.noaa.gov/erddap/griddap/"
J=[("wind/blended_winds_monthly_2014_latest.csv","noaacwBlendedWindsMonthly",["windspeed","u_wind","v_wind"],"2014-01-01","[(10.0)]"),
("wind/blended_windstress_monthly_2014_latest.csv","noaacwBlendedWindStressMonthly",["x_tau","y_tau"],"2014-01-01","[(10.0)]"),
("sea_level_eddies/sla_daily_last24m.csv","noaacwBLENDEDsshDaily",["sla"],"2024-10-01",""),
("currents/surface_currents_daily_last24m.csv","noaacwBLENDEDNRTcurrentsDaily",["u_current","v_current"],"2024-10-01",""),
("salinity_surface/smap_sss_daily_last24m.csv","noaacwSMAPsssDaily",["sss"],"2024-10-01","[(0.0)]")]
FB={"noaacwBlendedWindsMonthly":"2026-08-15","noaacwBlendedWindStressMonthly":"2026-08-15","noaacwBLENDEDsshDaily":"2026-10-15","noaacwBLENDEDNRTcurrentsDaily":"2026-10-14","noaacwSMAPsssDaily":"2026-10-14T12:00:00"}
def end(ds):
  for i in range(3):
    r=subprocess.run(["curl","-s","-m","60",f"https://coastwatch.noaa.gov/erddap/info/{ds}/index.csv"],capture_output=True,text=True).stdout
    l=[l for l in r.splitlines() if "time_coverage_end" in l]
    if l: return pd.Timestamp(l[0].split(",")[-1]).tz_localize(None)
  return pd.Timestamp(FB[ds])
def _old(ds):
  r=subprocess.run(["curl","-s","-m","60",f"https://coastwatch.noaa.gov/erddap/info/{ds}/index.csv"],capture_output=True,text=True).stdout
  return pd.Timestamp([l for l in r.splitlines() if "time_coverage_end" in l][0].split(",")[-1]).tz_localize(None)
for out,ds,vs,t0,x in J:
  try: d=pd.read_csv(out)
  except: d=pd.DataFrame(columns=["time"])
  have=set(pd.to_datetime(d.time).dt.strftime("%Y-%m")) if len(d) else set()
  e=end(ds); new=[]
  for a in pd.date_range(t0,e,freq="MS"):
    if a.strftime("%Y-%m") in have: continue
    b=min(a+pd.offsets.MonthEnd(0),e)
    for att in range(5):
      dfs=[]
      for v in vs:
        r=subprocess.run(["curl","-sg","-m","300",f"{CW}{ds}.csv?{v}[({a:%Y-%m-%d}):1:({b:%Y-%m-%dT%H:%M:%SZ})]{x}[(11):1:(4)][(77):1:(85)]"],capture_output=True,text=True).stdout
        if not r.startswith("time"): break
        dfs.append(pd.read_csv(io.StringIO(r),skiprows=[1]))
      if len(dfs)==len(vs):
        k=[c for c in dfs[0].columns if c not in vs];d0=dfs[0]
        for o in dfs[1:]: d0=d0.merge(o,on=k)
        new.append(d0);break
      time.sleep(15)
    else: print("still missing",out,a.date(),r[:80].replace("\n"," "),flush=True)
  if new: d=pd.concat([d]+new)
  d=d.drop_duplicates().sort_values(["time","latitude","longitude"]);d.to_csv(out,index=False)
  print(out,len(d),d.time.min(),d.time.max(),"end",e,flush=True)
