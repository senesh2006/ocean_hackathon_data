import pandas as pd
df = pd.read_csv("raw/sau/SAU EEZ 144 v50-1.csv")
print(df.columns.tolist())
keep=[c for c in ["area_name","year","fishing_entity","fishing_sector","gear_type","catch_type","reporting_status","functional_group","commercial_group","tonnes","landed_value"] if c in df.columns]
g = df.groupby([c for c in ["year","fishing_entity","fishing_sector","gear_type","catch_type","reporting_status"] if c in df.columns], dropna=False)[[c for c in ["tonnes","landed_value"] if c in df.columns]].sum().reset_index()
g.to_csv("sau_lka_eez144_catch_by_year_entity_sector_gear.csv", index=False)
g.to_parquet("sau_lka_eez144_catch_by_year_entity_sector_gear.parquet", index=False)
print(len(g), g.year.min(), g.year.max())
y=g[g.year==2019]
print(y.groupby("fishing_sector").tonnes.sum().round(0))
print(y.groupby("fishing_entity").tonnes.sum().round(0).sort_values(ascending=False).head())
print(g[g.fishing_entity=="India"].groupby("year").tonnes.sum().round(0).tail(5))
