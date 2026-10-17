import pandas as pd, glob
R="/workspace/srilanka-fisheries-official/"
def L(n): return pd.read_csv(glob.glob(R+f"bulletin2025_t4_{n}_*.csv")[0])
issues=[]
def cmp(tag, a, b, tol=0):
    if abs(a-b)>tol: issues.append(f"{tag}: computed {a:,.0f} vs published {b:,.0f} (diff {a-b:+,.0f})")
# 4.1
d=L("1"); p=d.pivot_table(index="year",columns="subsector_as_published",values="value")
for y,r in p.iterrows():
    cmp(f"4.1 {y} Coastal+Offshore=TotalMarine", r["Coastal"]+r["Off shore/Deep Sea"], r["Total Marine"])
    cmp(f"4.1 {y} Marine+Inland=Total", r["Total Marine"]+r["Inland & Aquaculture"], r["Total Fish Production"])
# district tables: sum districts vs Total row
for n,key in [("2","district_as_published"),("4","fisheries_district_as_published"),("9","district_as_published")]:
    d=L(n)
    for y,g in d.groupby("year"):
        cmp(f"4.{n} {y} sum(districts)=Total", g[~g.is_total].value.sum(), g[g.is_total].value.iloc[0])
# 4.3
d=L("3")
for (y,sub),g in d.groupby(["year","subsector_as_published"]):
    cmp(f"4.3 {y} {sub} col sum", g[g.district_as_published!="Total"].value.sum(), g[g.district_as_published=="Total"].value.iloc[0])
for (y,dn),g in d.groupby(["year","district_as_published"]):
    s=g.set_index("subsector_as_published").value.fillna(0)
    cmp(f"4.3 {y} {dn} M+I=T", s["Marine"]+s["Inland & Aquaculture"], s["Total"])
# 4.5
d=L("5")
for y,g in d.groupby("year"):
    cmp(f"4.5 {y} col sum", g[~g.is_total].value.sum(), g[g.is_total].value.iloc[0])
# 4.6/4.7
for n in ["6","7"]:
    d=L(n)
    for dn,g in d.groupby("fisheries_district_as_published"):
        cmp(f"4.{n} row {dn}", g[g.fish_group_as_published!="Total"].value.sum(), g[g.fish_group_as_published=="Total"].value.iloc[0])
    for gr,g in d.groupby("fish_group_as_published"):
        cmp(f"4.{n} col {gr}", g[g.fisheries_district_as_published!="Total"].value.sum(), g[g.fisheries_district_as_published=="Total"].value.iloc[0])
# 4.8
d=L("8")
for y,g in d.groupby("year"):
    subs=0
    for sec,gs in g.groupby("system_as_published"):
        if sec in ("","Seaweed"): continue
        st=gs[gs.waterbody_type_as_published=="Sub-Total"].value.iloc[0]; subs+=st
        cmp(f"4.8 {y} {sec} subtotal", gs[~gs.is_total].value.sum(), st)
    cmp(f"4.8 {y} sum(subtotals)=Total", subs, g[g.waterbody_type_as_published=="Total"].value.iloc[0])
# 4.10
d=L("10")
for y,g in d.groupby("year"):
    cmp(f"4.10 {y} col sum", g[~g.is_total].value.sum(), g[g.is_total].value.iloc[0])
# 4.11
d=L("11"); p=d.pivot_table(index="year",columns="measure_as_published",values="value")
for y,r in p.iterrows(): cmp(f"4.11 {y} aq+wild=total", r["Shrimps: Aquaculture"]+r["Shrimps: Wild Capture"], r["Shrimps: Total"])
# cross-table
t1=L("1").pivot_table(index="year",columns="subsector_as_published",values="value")
for n,col in [("2","Total Fish Production"),("4","Total Marine"),("9","Inland & Aquaculture")]:
    d=L(n); tt=d[d.is_total].set_index("year").value
    for y,v in tt.items():
        if y in t1.index: cmp(f"X 4.{n} total vs 4.1 {col} {y}", v, t1.loc[y,col])
d5=L("5"); tt=d5[d5.is_total].set_index("year").value
for y,v in tt.items(): cmp(f"X 4.5 total vs 4.1 marine {y}", v, t1.loc[y,"Total Marine"])
d10=L("10"); tt=d10[d10.is_total].set_index("year").value
for y,v in tt.items():
    if y in t1.index: cmp(f"X 4.10 total vs 4.1 inland {y}", v, t1.loc[y,"Inland & Aquaculture"])
d8=L("8"); tt=d8[d8.waterbody_type_as_published=="Total"].set_index("year").value
for y,v in tt.items(): cmp(f"X 4.8 total vs 4.1 inland {y}", v, t1.loc[y,"Inland & Aquaculture"] if y in t1.index else v)
# 4.6/4.7 total row vs 4.5, 4.4 by district
for n,y in [("6",2024),("7",2025)]:
    d=L(n); t=d[d.fisheries_district_as_published=="Total"].set_index("fish_group_as_published").value
    g5=d5[d5.year==y].set_index("fish_group_english_as_published").value
    for a,b in zip(t.values, g5.values): cmp(f"X 4.{n} group totals vs 4.5 {y}", a, b)
    d4=L("4"); d4y=d4[d4.year==y].set_index("fisheries_district_std").value
    tt=d[d.fish_group_as_published=="Total"].set_index("fisheries_district_std").value
    for k,v in tt.items(): cmp(f"X 4.{n} district total vs 4.4 {k} {y}", v, d4y[k])
d11=L("11"); 
print("\n".join(issues) if issues else "ALL CHECKS PASS"); print(len(issues),"issues")
