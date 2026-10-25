import pandas as pd
frames=[]
for s in ["APW","UP"]:
    d=pd.read_csv(f"raw/rousseau_2017_{s}_srilanka.csv", on_bad_lines="skip")
    d=d.drop(columns=[c for c in d.columns if c.startswith("Unnamed") or c==""])
    d=d[pd.to_numeric(d["Lat"],errors="coerce").notna()]
    frames.append(d)
d=pd.concat(frames)
for c in ["Lat","Lon","NomActive","EffActive","NV","P","GT"]: d[c]=pd.to_numeric(d[c],errors="coerce")
d["SAUP"]=pd.to_numeric(d["SAUP"],errors="coerce").astype("Int64")
d["flag"]=d.SAUP.map({144:"LKA",356:"IND"}).fillna("other")
d["year"]=2017
d.to_csv("rousseau2017_artisanal_effort_0p5_srilanka_rows.csv",index=False)
d.to_parquet("rousseau2017_artisanal_effort_0p5_srilanka_rows.parquet",index=False)
cell=d.groupby(["year","Lat","Lon","Sector","flag"]).agg(NomActive_kWdays=("NomActive","sum"),EffActive_kWdays=("EffActive","sum"),NV=("NV","sum")).reset_index()
cell.to_csv("rousseau2017_artisanal_effort_0p5_cells.csv",index=False)
cell.to_parquet("rousseau2017_artisanal_effort_0p5_cells.parquet",index=False)
north=(cell.Lat.between(8.5,10.5))&(cell.Lon.between(78.9,81.5))
# Sri Lanka-ish domain: cells with any LKA effort
lka=cell[cell.flag=="LKA"]
nl=(lka.Lat.between(8.5,10.5))&(lka.Lon.between(78.9,81.5))
print("rows",len(d),"cells",cell[["Lat","Lon"]].drop_duplicates().shape[0])
for sec in ["APW","UP"]:
    t=lka[lka.Sector==sec].NomActive_kWdays.sum(); n=lka[(lka.Sector==sec)&nl].NomActive_kWdays.sum()
    print(sec,"LKA total kWdays",round(t),"north bbox",round(n),f"{100*n/t:.1f}%")
print("NV LKA total",round(lka.NV.sum()),"north",round(lka[nl].NV.sum()))
ind=cell[(cell.flag=="IND")&north]
print("IND effort in north bbox (kWdays) by sector:",ind.groupby("Sector").NomActive_kWdays.sum().round().to_dict(), "NV",round(ind.NV.sum()))
print("LKA effort in north bbox by sector:",lka[nl].groupby("Sector").NomActive_kWdays.sum().round().to_dict())
