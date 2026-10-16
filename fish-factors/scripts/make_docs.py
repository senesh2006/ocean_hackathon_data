import pandas as pd,glob,os
D="2026-10-16";B="lat 4-11N, lon 77-85E (box; includes some Indian waters, e.g. Palk Bay / Gulf of Mannar)"
CW="https://coastwatch.noaa.gov/erddap/griddap/";OW="https://oceanwatch.pifsc.noaa.gov/erddap/griddap/"
M={
"sst/crw_sst_monthly_last24m_0.05deg.csv":("Sea surface temperature, monthly",OW+"CRW_sst_v3_1_monthly.html","Public domain (NOAA Coral Reef Watch)","0.05 deg, monthly"),
"chlorophyll/esa_cci_chla_monthly_last24m_4km.csv":("Chlorophyll-a, monthly",OW+"esa-cci-chla-monthly-v6-0.html","CC-BY 4.0 (ESA OC-CCI)","~4 km (1/24 deg), monthly"),
"wind/blended_winds_monthly_2014_latest.csv":("Wind speed and u/v at 10 m, monthly",CW+"noaacwBlendedWindsMonthly.html","Public domain (NOAA NCEI Blended Sea Winds)","0.25 deg, monthly"),
"wind/blended_windstress_monthly_2014_latest.csv":("Wind stress x/y, monthly (upwelling driver)",CW+"noaacwBlendedWindStressMonthly.html","Public domain (NOAA)","0.25 deg, monthly"),
"sea_level_eddies/sla_daily_last24m.csv":("Sea level anomaly (eddies), daily",CW+"noaacwBLENDEDsshDaily.html","Public domain (NOAA CoastWatch blended SSH)","0.25 deg, daily"),
"currents/surface_currents_daily_last24m.csv":("Surface geostrophic + Ekman currents u/v, daily",CW+"noaacwBLENDEDNRTcurrentsDaily.html","Public domain (NOAA CoastWatch)","0.25 deg, daily"),
"salinity_surface/smap_sss_daily_last24m.csv":("Sea surface salinity, SMAP, daily (8-day running)",CW+"noaacwSMAPsssDaily.html","Public domain (NOAA/NASA SMAP)","0.25 deg, daily"),
"bottom_temp_salinity_oxygen_woa23/woa23_temperature_monthly_clim_0.25deg.csv":("WOA23 temperature monthly climatology, surface/50/100/200 m and bottom (deepest level, up to 1500 m)","https://www.ncei.noaa.gov/products/world-ocean-atlas","Public domain (NOAA NCEI). Cite Locarnini et al. 2024","0.25 deg, monthly climatology 2005-2022 (B5C2)"),
"bottom_temp_salinity_oxygen_woa23/woa23_salinity_monthly_clim_0.25deg.csv":("WOA23 salinity monthly climatology, surface/50/100/200 m and bottom","https://www.ncei.noaa.gov/products/world-ocean-atlas","Public domain (NOAA NCEI). Cite Reagan et al. 2024","0.25 deg, monthly climatology 2005-2022"),
"bottom_temp_salinity_oxygen_woa23/woa23_oxygen_monthly_clim_1.00deg.csv":("WOA23 dissolved oxygen monthly climatology (umol/kg), surface/50/100/200 m and bottom","https://www.ncei.noaa.gov/products/world-ocean-atlas","Public domain (NOAA NCEI). Cite Garcia et al. 2024","1 deg, monthly climatology, all years"),
"mixed_layer_depth/mld_from_woa23_temperature_monthly_clim_0.25deg.csv":("Mixed layer depth (0.5 C temperature criterion), from WOA23 profiles","derived from WOA23","Public domain","0.25 deg, monthly climatology"),
"rainfall/chirps_v2_monthly_srilanka_land_0.05deg_2024_latest.csv":("CHIRPS v2 rainfall over Sri Lanka land (river runoff proxy)","https://iridl.ldeo.columbia.edu/SOURCES/.UCSB/.CHIRPS/.v2p0/.monthly/.global/","Public domain (UCSB CHG)","0.05 deg, monthly"),
"rainfall/chirps_island_mean_monthly.csv":("CHIRPS island-mean monthly rainfall","derived","Public domain","island mean, monthly"),
"rainfall/gpcp_v23_monthly_2.5deg.csv":("GPCP v2.3 rainfall over land and ocean, 1979 to latest","https://psl.noaa.gov/data/gridded/data.gpcp.html","Public domain (NOAA PSL / GPCP)","2.5 deg, monthly"),
"rainfall/gpcp_monthly_climatology_2.5deg.csv":("GPCP monthly climatology, all years","derived","Public domain","2.5 deg"),
"climate_indices/dmi_oni_monthly.csv":("Indian Ocean Dipole Mode Index (HadISST) and Oceanic Niño Index (CPC)","https://psl.noaa.gov/gcos_wgsp/Timeseries/DMI/ ; https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt","Public domain (NOAA)","basin index, monthly"),
"moon_phase/moon_daily_2000_2027_colombo_midnight.csv":("Moon illumination, age and phase (computed)","computed with PyEphem","n/a","daily, at Colombo midnight"),
"monsoon_calendar/srilanka_monsoon_calendar.csv":("Sri Lanka monsoon season calendar, rough-sea and upwelling flags","Dept. of Meteorology season definitions; de Vos et al. 2014 (doi:10.5194/bg-11-5909-2014)","n/a","by month"),
"seabed_shelf_habitat/shelf_habitat_grid_1arcmin_water.csv":("Depth, slope, shelf (<200 m), trawlable 10-200 m, upper slope, reef and trawl-candidate flags (water cells)",OW+"ETOPO_2022_v1_60s.html","Public domain (NOAA ETOPO 2022) + UNEP-WCMC reefs","1 arc-min (~1.85 km)"),
"seabed_shelf_habitat/shelf_habitat_grid_1arcmin.parquet":("Same grid, all cells including land","as above","as above","1 arc-min"),
"coral_reefs_avoid/unep_wcmc_coral_reefs_v4_1_srilanka.geojson":("Warm-water coral reef polygons (areas to avoid trawling)","https://data-gis.unep-wcmc.org/server/rest/services/HabitatsAndBiotopes/Global_Distribution_of_Coral_Reefs/FeatureServer/1","UNEP-WCMC terms: non-commercial use; cite doi:10.34892/t2wk-5t34","vector polygons"),
"species_flags/species_demersal_trawl_flags.csv":("Species list with demersal / reef / small-pelagic / trawl-target flags","derived from fish-data species_list + FishBase","CC-BY-NC (FishBase)","per species"),
}
rows=[]
for p,(n,s,l,res) in M.items():
  if not os.path.exists(p): rows.append(dict(file_path=p,dataset=n,source_url=s,license=l,resolution=res,row_count=0,date_start="",date_end="",spatial_extent=B,status="MISSING (download failed)",download_date=D));continue
  if p.endswith(".geojson"):
    import json;r=len(json.load(open(p))["features"]);a=b=""
  else:
    d=pd.read_parquet(p) if p.endswith("parquet") else pd.read_csv(p,low_memory=False);r=len(d);a=b=""
    for c in ["time","date"]:
      if c in d: a,b=str(d[c].min())[:10],str(d[c].max())[:10];break
    else:
      if "year" in d: a,b=f"{d.year.min()}",f"{d.dropna(subset=[d.columns[2]]).year.max()}-{d.dropna(subset=[d.columns[2]]).iloc[-1].month:02.0f}"
      elif "month" in d: a,b="climatology months 1","12"
  rows.append(dict(file_path=p,dataset=n,source_url=s,license=l,resolution=res,row_count=r,date_start=a,date_end=b,spatial_extent=B,status="ok",download_date=D))
c=pd.DataFrame(rows);c.to_csv("catalog.csv",index=False);open("catalog.md","w").write("# fish-factors catalog\n\n"+c.to_markdown(index=False))
dd=[]
for p in M:
  if not os.path.exists(p) or p.endswith(".geojson"): continue
  d=pd.read_parquet(p) if p.endswith("parquet") else pd.read_csv(p,nrows=5)
  for col in d.columns: dd.append(dict(file_path=p,column=col,dtype=str(d[col].dtype)))
DESC={"sea_surface_temperature":"SST (C)","chlor_a":"chlorophyll-a (mg m-3)","windspeed":"10 m wind speed (m/s)","u_wind":"eastward wind (m/s)","v_wind":"northward wind (m/s)","x_tau":"eastward wind stress (N/m2)","y_tau":"northward wind stress (N/m2)","sla":"sea level anomaly (m); +ve = anticyclonic/warm eddy, -ve = cyclonic/upwelling","u_current":"eastward surface current (m/s)","v_current":"northward surface current (m/s)","sss":"sea surface salinity (PSU)","deepest_level_m":"deepest WOA standard level with data (~ seabed depth on shelf)","t_bottom":"near-bottom temperature (C)","s_bottom":"near-bottom salinity (PSU)","o_bottom":"near-bottom dissolved oxygen (umol/kg)","mld_t0.5_m":"mixed layer depth (m), first depth with T < T_surface - 0.5 C","precip_mm_month":"rainfall (mm/month)","precip_mm_day":"rainfall (mm/day)","dmi":"Dipole Mode Index (C); >=0.4 positive IOD","oni":"Oceanic Nino Index (C); >=0.5 El Nino","illumination_frac":"fraction of the moon lit (0-1)","moon_age_days":"days since new moon","depth_m":"seabed depth (m, positive down)","slope_deg":"seabed slope (degrees)","shelf_lt200m":"1 = water shallower than 200 m","trawlable_depth_10_200m":"1 = 10-200 m depth","upper_slope_200_1000m":"1 = 200-1000 m depth","coral_reef":"1 = within ~1 km of mapped coral reef","trawl_candidate":"1 = 10-200 m and not reef","is_demersal_or_reef":"FishBase DemersPelag is demersal / reef / bathydemersal / benthopelagic","trawl_target_likely":"demersal or trawl-typical family, shallow depth limit < 200 m"}
for r in dd:
  k=r["column"];r["description"]=DESC.get(k) or next((v for kk,v in DESC.items() if k.startswith(kk.split("_")[0]+"_") and kk.startswith(k[:2])),"")
pd.DataFrame(dd).to_csv("data_dictionary.csv",index=False)
print(c[["file_path","row_count","date_end","status"]].to_string())
