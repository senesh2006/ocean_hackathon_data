import subprocess,sys,time,pandas as pd,io,os
from concurrent.futures import ThreadPoolExecutor
CW="https://coastwatch.noaa.gov/erddap/griddap/";OW="https://oceanwatch.pifsc.noaa.gov/erddap/griddap/"
J0=[("wind/blended_winds_monthly_2014_latest.csv",CW,"noaacwBlendedWindsMonthly",["windspeed","u_wind","v_wind"],"2014-01-01","2026-10-31","[(10.0)]",12),
("wind/blended_windstress_monthly_2014_latest.csv",CW,"noaacwBlendedWindStressMonthly",["x_tau","y_tau"],"2014-01-01","2026-10-31","[(10.0)]",12),
("sea_level_eddies/sla_daily_last24m.csv",CW,"noaacwBLENDEDsshDaily",["sla"],"2024-10-01","2026-10-31","",2),
("currents/surface_currents_daily_last24m.csv",CW,"noaacwBLENDEDNRTcurrentsDaily",["u_current","v_current"],"2024-10-01","2026-10-31","",2),
("salinity_surface/smap_sss_daily_last24m.csv",CW,"noaacwSMAPsssDaily",["sss"],"2024-10-01","2026-10-31","[(0.0)]",1),
("sst/crw_sst_monthly_last24m_0.05deg.csv",OW,"CRW_sst_v3_1_monthly",["sea_surface_temperature"],"2024-09-01","2026-10-31","",6),
("chlorophyll/esa_cci_chla_monthly_last24m_4km.csv",OW,"esa-cci-chla-monthly-v6-0",["chlor_a"],"2024-07-01","2026-10-31","",6)]
J=[j for j in J0 if j[1]==CW]
def run(j):
  out,B,ds,vs,t0,t1,x,step=j; parts=[]
  starts=pd.date_range(t0,t1,freq=f"{step}MS")
  for a in starts:
    b=min(a+pd.DateOffset(months=step)-pd.Timedelta(days=1),pd.Timestamp(t1))
    ok=False
    for att in range(6):
      for L in ("[(11):1:(4)]","[(4):1:(11)]"):
        dfs=[]
        for v in vs:
          q=f"{v}[({a:%Y-%m-%d}):1:({b:%Y-%m-%d})]{x}{L}[(77):1:(85)]"
          r=subprocess.run(["curl","-sg","-m","300",B+ds+".csv?"+q],capture_output=True,text=True).stdout
          if not r.startswith("time"): break
          dfs.append(pd.read_csv(io.StringIO(r),skiprows=[1]))
        if len(dfs)==len(vs):
          k=[c for c in dfs[0].columns if c not in vs];d0=dfs[0]
          for o in dfs[1:]: d0=d0.merge(o,on=k)
          parts.append(d0);ok=True;break
        if "outside" in r or "out of range" in r.lower() or "No data" in r: ok=True;break
      if ok:break
      time.sleep(10)
    if not ok: print("chunk fail",out,a,r[:150],flush=True)
  if parts:
    d=pd.concat(parts);d.to_csv(out,index=False);return f"{out} {len(d)} {d.time.max()}"
  return f"FAIL {out}"
with ThreadPoolExecutor(3) as ex:
  for r in ex.map(run,J): print(r,flush=True)
