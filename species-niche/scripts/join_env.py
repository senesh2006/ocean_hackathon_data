"""Join repo occurrences (fish-data/train_ready/features.parquet) and background points to extra
fish-factors grids. Nearest valid cell in the same calendar month (max 0.5 deg for 0.25-deg grids,
1.0 deg for the 1-deg O2 grid). Output: work/occ_env.parquet, work/bg_env.parquet"""
import pandas as pd, numpy as np
from scipy.spatial import cKDTree
R = "/workspace/ocean_hackathon_data/"
W = "/workspace/species_niche/work/"
import os; os.makedirs(W, exist_ok=True)
occ = pd.read_parquet(R + "fish-data/train_ready/features.parquet")
bg = pd.read_parquet(R + "fish-data/train_ready/background_points.parquet")
FF = R + "fish-factors/"
T = pd.read_csv(FF + "bottom_temp_salinity_oxygen_woa23/woa23_temperature_monthly_clim_0.25deg.csv")
S = pd.read_csv(FF + "bottom_temp_salinity_oxygen_woa23/woa23_salinity_monthly_clim_0.25deg.csv")
O = pd.read_csv(FF + "bottom_temp_salinity_oxygen_woa23/woa23_oxygen_monthly_clim_1.00deg.csv")
H = pd.read_parquet(FF + "seabed_shelf_habitat/shelf_habitat_grid_1arcmin.parquet")
grids = [  # (table, columns -> new names, max dist deg)
    (T, {"t_0m": "woa_t_surface_c", "t_100m": "woa_t_100m_c", "t_bottom": "woa_t_bottom_c", "mld_t0.5_m": "mld_m"}, 0.5),
    (S, {"s_0m": "woa_sss_psu", "s_bottom": "woa_s_bottom_psu"}, 0.5),
    (O, {"o_0m": "woa_o2_surface_umolkg", "o_bottom": "woa_o2_bottom_umolkg"}, 1.0),
]
def attach(pts):
    pts = pts.copy()
    for g, cols, md in grids:
        for c, new in cols.items():
            pts[new] = np.nan
            for m in range(1, 13):
                gm = g[(g.month == m) & g[c].notna()]
                idx = np.where(pts.month.values == m)[0]
                if len(gm) == 0 or len(idx) == 0: continue
                tr = cKDTree(gm[["lat", "lon"]].values)
                d, j = tr.query(pts.iloc[idx][["lat", "lon"]].values, distance_upper_bound=md)
                ok = np.isfinite(d)
                vals = np.full(len(idx), np.nan); vals[ok] = gm[c].values[j[ok]]
                pts.iloc[idx, pts.columns.get_loc(new)] = vals
    # static seabed habitat (1 arcmin): slope, coral reef cell (water cells only)
    h = H[H.is_water == 1] if "is_water" in H else H
    tr = cKDTree(h[["lat", "lon"]].values)
    d, j = tr.query(pts[["lat", "lon"]].values, distance_upper_bound=0.05)
    ok = np.isfinite(d)
    for c, new in [("slope_deg", "slope_deg"), ("coral_reef", "coral_reef_cell")]:
        v = np.full(len(pts), np.nan); v[ok] = h[c].values[j[ok]]; pts[new] = v
    pts["chla_mg_m3"] = 10 ** pts["log_chla"]
    pts["sst_c"] = pts["sst_filled"]
    return pts
keep = ["lat", "lon", "month", "bathy_depth_m", "sst_filled", "log_chla"]
o = attach(occ[["record_id", "label_species", "recommended_training", "chla_lagoon_outlier", "depth_m"] + keep])
b = attach(bg[["bg_id", "bg_type", "chla_lagoon_outlier"] + keep])
o.to_parquet(W + "occ_env.parquet", index=False); b.to_parquet(W + "bg_env.parquet", index=False)
print(o.notna().mean().round(3)); print(b.notna().mean().round(3))
