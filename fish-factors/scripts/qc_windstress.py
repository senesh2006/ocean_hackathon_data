"""QC for the NOAA NCEI Blended Sea Winds monthly files in fish-factors/wind/.

Writes NEW files and never touches the raw downloads:
  wind/blended_windstress_monthly_2014_latest_qc.csv   (x_tau, y_tau + mask + qc_flag)
  wind/blended_winds_monthly_2014_latest_qc.csv        (windspeed, u_wind, v_wind + mask + qc_flag)
  wind/qc/windstress_outliers.csv                       every wind-stress row dropped or blanked, with reason
  wind/qc/winds_outliers.csv                            same for the wind-speed file
  wind/qc/blended_winds_landmask_0.25deg.csv            the product's own land/ocean mask for our box
  wind/qc/qc_summary.json                               counts per flag

Why (task 2.62, see CHANGELOG 3.1.0):
  * The raw stress file has |tau| up to 1,323 N/m2. Re-querying ERDDAP (noaacwBlendedWindStressMonthly) on
    2026-10-17 returned byte-identical values, so the bad values are in the upstream product, not our download.
    127 of the 133 impossible rows sit on cells the product's own `mask` variable marks as LAND (mask=0).
  * Both raw files repeat every January from 2015 on (dl_erddap.py asks for 12-month chunks ending 31 Dec;
    ERDDAP snaps that to the nearest time step, the next year's 15 Jan). The repeats are identical copies.

qc_flag (value columns are set to NaN for every flag except 0 and 4):
  0 good                       ocean cell, value within physical limits
  1 land_mask                  product mask = 0 (land). Values here are not ocean stress/winds.
  2 impossible_gt_3Nm2         ocean cell, |x_tau| or |y_tau| > 3 N/m2 (same bound as the team's physical_ranges).
                               Even a 30 m/s hurricane wind gives tau ~ rho_a*Cd*U^2 = 1.2*2.5e-3*900 ~ 2.7 N/m2
                               instantaneously; a monthly MEAN above 3 is impossible.
  3 implausible_monthly_gt_1   ocean cell, |tau| = hypot(x_tau, y_tau) > 1 N/m2 (monthly mean). The highest
                               monthly-mean wind speed in the companion file over 2014-2025 is 11.2 m/s, which
                               gives tau ~ 1.22*2.5e-3*11.2^2 ~ 0.38 N/m2 even with a generous drag coefficient.
                               Ocean 99.9th percentile of |tau| is 0.49 N/m2. 15 of the 18 ocean rows caught by flags 2+3
                               are on cells next to land.
  4 no_data                    the product itself has no value (NaN) for this ocean cell/month; kept as NaN.
  (winds file) 2 impossible    windspeed < 0 or > 50 m/s, |u|,|v| > 50 m/s  (none found)
Duplicate January rows are removed (first copy kept) and listed in the outliers files as reason=duplicate_row.

Run:  python fish-factors/scripts/qc_windstress.py            (uses the cached mask)
      python fish-factors/scripts/qc_windstress.py --refresh-mask   (re-downloads the mask from ERDDAP)
"""
import io, json, os, subprocess, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
FF = os.path.dirname(HERE)
WIND = os.path.join(FF, "wind")
QC = os.path.join(WIND, "qc")
MASK_CSV = os.path.join(QC, "blended_winds_landmask_0.25deg.csv")
ERDDAP = "https://coastwatch.noaa.gov/erddap/griddap/noaacwBlendedWindStressMonthly.csv"
KEY = ["time", "latitude", "longitude"]
HARD_TAU = 3.0      # N/m2, per component
MONTHLY_TAU = 1.0   # N/m2, magnitude of monthly mean
FLAG_TEXT = {0: "good", 1: "land_mask", 2: "impossible_gt_3Nm2", 3: "implausible_monthly_gt_1Nm2", 4: "no_data"}


def get_mask(refresh=False):
    if os.path.exists(MASK_CSV) and not refresh:
        return pd.read_csv(MASK_CSV)
    q = "mask[(2020-01-15)][(10.0)][(4):1:(11)][(77):1:(85)]"
    r = subprocess.run(["curl", "-sg", "-m", "300", ERDDAP + "?" + q], capture_output=True, text=True).stdout
    if not r.startswith("time"):
        sys.exit("could not download mask from ERDDAP: " + r[:200])
    m = pd.read_csv(io.StringIO(r), skiprows=[1])[["latitude", "longitude", "mask"]]
    m["mask_meaning"] = m["mask"].map({0: "land", 1: "ocean", 2: "lake", 3: "river", 6: "model"})
    os.makedirs(QC, exist_ok=True)
    m.to_csv(MASK_CSV, index=False)
    return m


def dedupe(d):
    dup = d.duplicated(KEY, keep="first")
    out = d[dup].copy()
    out["reason"] = "duplicate_row"
    out["detail"] = "identical repeat of the same time/cell (ERDDAP chunk-boundary overlap in dl_erddap.py)"
    return d[~dup].copy(), out


def qc_stress(mask):
    raw = pd.read_csv(os.path.join(WIND, "blended_windstress_monthly_2014_latest.csv"))
    d, dropped = dedupe(raw)
    d = d.merge(mask[["latitude", "longitude", "mask"]], on=["latitude", "longitude"], how="left")
    tau = np.hypot(d.x_tau, d.y_tau)
    flag = np.zeros(len(d), dtype=int)
    has = d.x_tau.notna() | d.y_tau.notna()
    flag[(~has).values] = 4
    flag[((d["mask"] != 1) & has).values] = 1
    ocean = (d["mask"] == 1) & has
    flag[(ocean & (tau > MONTHLY_TAU)).values] = 3
    flag[(ocean & ((d.x_tau.abs() > HARD_TAU) | (d.y_tau.abs() > HARD_TAU))).values] = 2
    d["qc_flag"] = flag
    d["qc_reason"] = d.qc_flag.map(FLAG_TEXT)
    bad = d.qc_flag.isin([1, 2, 3])
    rep = d[bad].copy()
    rep["reason"] = rep.qc_reason
    rep["tau_magnitude"] = tau[bad].round(6)
    rep["detail"] = np.where(rep.x_tau.abs().gt(HARD_TAU) | rep.y_tau.abs().gt(HARD_TAU),
                             "also exceeds 3 N/m2 (physically impossible)", "")
    d.loc[bad, ["x_tau", "y_tau"]] = np.nan
    cols = ["time", "latitude", "longitude", "x_tau", "y_tau", "mask", "reason", "detail"]
    out = pd.concat([rep.drop(columns=["qc_flag", "qc_reason"]), dropped], ignore_index=True)
    out = out[[c for c in cols[:5] + ["tau_magnitude", "mask", "reason", "detail", "zlev"] if c in out.columns]]
    d.to_csv(os.path.join(WIND, "blended_windstress_monthly_2014_latest_qc.csv"), index=False)
    out.sort_values(["reason", "time", "latitude", "longitude"]).to_csv(os.path.join(QC, "windstress_outliers.csv"), index=False)
    return raw, d, out, tau


def qc_winds(mask):
    raw = pd.read_csv(os.path.join(WIND, "blended_winds_monthly_2014_latest.csv"))
    d, dropped = dedupe(raw)
    d = d.merge(mask[["latitude", "longitude", "mask"]], on=["latitude", "longitude"], how="left")
    has = d.windspeed.notna()
    flag = np.zeros(len(d), dtype=int)
    flag[(~has).values] = 4
    flag[((d["mask"] != 1) & has).values] = 1
    imp = (d["mask"] == 1) & has & ((d.windspeed < 0) | (d.windspeed > 50) | (d.u_wind.abs() > 50) | (d.v_wind.abs() > 50))
    flag[imp.values] = 2
    d["qc_flag"] = flag
    d["qc_reason"] = d.qc_flag.map({0: "good", 1: "land_mask", 2: "impossible_wind", 4: "no_data"})
    bad = d.qc_flag.isin([1, 2])
    rep = d[bad].copy()
    rep["reason"] = rep.qc_reason
    rep["detail"] = ""
    d.loc[bad, ["windspeed", "u_wind", "v_wind"]] = np.nan
    out = pd.concat([rep.drop(columns=["qc_flag", "qc_reason"]), dropped], ignore_index=True)
    out = out[["time", "latitude", "longitude", "windspeed", "u_wind", "v_wind", "mask", "reason", "detail", "zlev"]]
    d.to_csv(os.path.join(WIND, "blended_winds_monthly_2014_latest_qc.csv"), index=False)
    out.sort_values(["reason", "time", "latitude", "longitude"]).to_csv(os.path.join(QC, "winds_outliers.csv"), index=False)
    return raw, d, out


QC_DOCS = {
    "wind/blended_windstress_monthly_2014_latest_qc.csv": ("Wind stress x/y, monthly, QC'd (USE THIS): duplicates removed, land cells and impossible values set NaN, qc_flag column", "https://coastwatch.noaa.gov/erddap/griddap/noaacwBlendedWindStressMonthly.html", "Public domain (NOAA); QC by ocean_hackathon_data"),
    "wind/blended_winds_monthly_2014_latest_qc.csv": ("Wind speed and u/v at 10 m, monthly, QC'd (USE THIS): duplicates removed, land cells set NaN, qc_flag column", "https://coastwatch.noaa.gov/erddap/griddap/noaacwBlendedWindsMonthly.html", "Public domain (NOAA NCEI Blended Sea Winds); QC by ocean_hackathon_data"),
    "wind/qc/windstress_outliers.csv": ("Every wind-stress row removed (duplicate) or blanked (land / impossible / implausible), with reason", "derived (qc_windstress.py)", "Public domain (NOAA) values; CC BY 4.0 compilation"),
    "wind/qc/winds_outliers.csv": ("Every wind-speed row removed (duplicate) or blanked (land), with reason", "derived (qc_windstress.py)", "Public domain (NOAA) values; CC BY 4.0 compilation"),
    "wind/qc/blended_winds_landmask_0.25deg.csv": ("NOAA Blended Sea Winds land/ocean mask for the 0.25 deg box (time-invariant 2014-2026)", "https://coastwatch.noaa.gov/erddap/griddap/noaacwBlendedWindStressMonthly.html", "Public domain (NOAA)"),
}
RAW_STATUS = "current (raw; use _qc)"
COL_DESC = {
    "mask": "NOAA Blended Winds mask from the product: 0=land, 1=ocean (2=lake, 3=river, 6=model do not occur here)",
    "mask_meaning": "text form of mask",
    "qc_flag": "0 good; 1 land_mask (NaN); 2 impossible |component|>3 N/m2 (NaN); 3 implausible monthly |tau|>1 N/m2 (NaN); 4 no_data upstream",
    "qc_reason": "text form of qc_flag",
    "tau_magnitude": "hypot(x_tau, y_tau) of the original value (N/m2)",
    "reason": "why the row was removed or blanked (duplicate_row, land_mask, impossible_gt_3Nm2, implausible_monthly_gt_1Nm2)",
    "detail": "extra note",
    "x_tau": "eastward wind stress (N/m2)", "y_tau": "northward wind stress (N/m2)",
    "windspeed": "10 m wind speed (m/s)", "u_wind": "eastward wind (m/s)", "v_wind": "northward wind (m/s)",
}


def update_docs():
    """Add/refresh the QC rows in fish-factors/catalog.csv, catalog.md and data_dictionary.csv (other rows untouched)."""
    today = pd.Timestamp.now().strftime("%Y-%m-%d")
    cat_p = os.path.join(FF, "catalog.csv")
    cat = pd.read_csv(cat_p, dtype=str, keep_default_na=False)
    cat = cat[~cat.file_path.isin(QC_DOCS)]
    for raw in ["wind/blended_winds_monthly_2014_latest.csv", "wind/blended_windstress_monthly_2014_latest.csv"]:
        cat.loc[cat.file_path == raw, "status"] = RAW_STATUS
    template = cat[cat.file_path == "wind/blended_windstress_monthly_2014_latest.csv"].iloc[0].to_dict()
    new, dd = [], []
    for rel, (name, src, lic) in QC_DOCS.items():
        d = pd.read_csv(os.path.join(FF, rel), low_memory=False)
        r = dict(template, file_path=rel, dataset=name, source_url=src, license=lic, row_count=str(len(d)),
                 status="ok (QC)", download_date=today,
                 date_start=str(d.time.min())[:10] if "time" in d else "", date_end=str(d.time.max())[:10] if "time" in d else "")
        if "landmask" in rel:
            r["resolution"] = "0.25 deg, static (time-invariant)"
        new.append(r)
        for c in d.columns:
            dd.append(dict(file_path=rel, column=c, dtype=str(d[c].dtype), description=COL_DESC.get(c, "")))
    cat = pd.concat([cat, pd.DataFrame(new)], ignore_index=True)
    cat.to_csv(cat_p, index=False)
    open(os.path.join(FF, "catalog.md"), "w").write("# fish-factors catalog\n\n" + cat.to_markdown(index=False))
    dd_p = os.path.join(FF, "data_dictionary.csv")
    old = pd.read_csv(dd_p, dtype=str, keep_default_na=False)
    old = old[~old.file_path.isin(QC_DOCS)]
    pd.concat([old, pd.DataFrame(dd)], ignore_index=True).to_csv(dd_p, index=False)


def main():
    mask = get_mask("--refresh-mask" in sys.argv)
    sraw, s, sout, tau = qc_stress(mask)
    wraw, w, wout = qc_winds(mask)
    oc = s[s.qc_flag == 0]
    summ = dict(
        windstress=dict(raw_rows=len(sraw), duplicate_rows_removed=int((sout.reason == "duplicate_row").sum()),
                        qc_rows=len(s), flags={FLAG_TEXT[k]: int(v) for k, v in s.qc_flag.value_counts().sort_index().items()},
                        raw_rows_abs_gt_3=int(((sraw.x_tau.abs() > 3) | (sraw.y_tau.abs() > 3)).sum()),
                        unique_rows_abs_gt_3=int(((s.merge(sraw.drop_duplicates(KEY), on=KEY, suffixes=("", "_r"))
                                                   .pipe(lambda x: (x.x_tau_r.abs() > 3) | (x.y_tau_r.abs() > 3))).sum())),
                        max_abs_after_qc=dict(x_tau=float(oc.x_tau.abs().max()), y_tau=float(oc.y_tau.abs().max())),
                        p99_tau_after_qc=float(np.hypot(oc.x_tau, oc.y_tau).quantile(0.99))),
        winds=dict(raw_rows=len(wraw), duplicate_rows_removed=int((wout.reason == "duplicate_row").sum()), qc_rows=len(w),
                   flags={k: int(v) for k, v in w.qc_reason.value_counts().items()},
                   max_windspeed_after_qc=float(w.windspeed.max())),
        thresholds=dict(component_abs_max_Nm2=HARD_TAU, monthly_tau_magnitude_max_Nm2=MONTHLY_TAU),
        mask_cells={str(k): int(v) for k, v in mask["mask"].value_counts().items()},
    )
    with open(os.path.join(QC, "qc_summary.json"), "w") as f:
        json.dump(summ, f, indent=2)
    update_docs()
    print(json.dumps(summ, indent=2))


if __name__ == "__main__":
    main()
