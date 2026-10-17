"""Extract Chapter 4 (fish production) tables from the Sri Lanka Ministry of Fisheries
Annual Fisheries Statistical Bulletin 2025 into tidy long CSV + Parquet.
Values are read from the PDF text layer (pdftotext -layout); cell -> column assignment
uses the right-edge character position of each token, anchored on the fully populated
Total row of each table. Verified against page renders and row/column totals."""
import re, subprocess, sys
from pathlib import Path
import pandas as pd

ROOT = Path("/workspace/srilanka-fisheries-official")
PDF = ROOT / "raw" / "Annual-Fisheries-Statistical-Bulletin-2025.pdf"
SRC = "https://www.fisheries.gov.lk/wp-content/uploads/2026/10/Annual-Fisheries-Statistical-Bulletin-2025.pdf"
TOK = re.compile(r"(?<!\S)(\d{1,3}(?:,\d{3})+|\d+|-|na|N/A|\*\*\*|\*\*)(?!\S)")

def page(p):
    return subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-layout", str(PDF), "-"],
                          capture_output=True, text=True, check=True).stdout.splitlines()

def toks(s, start=0):
    return [(m.group(1), m.end() + start) for m in TOK.finditer(s)]

def assign(tokens, anchors):
    out = [None] * len(anchors)
    for t, e in tokens:
        i = min(range(len(anchors)), key=lambda k: abs(anchors[k] - e))
        if out[i] is not None:
            raise ValueError(f"collision {tokens} {anchors}")
        out[i] = t
    return out

def conv(raw):
    if raw is None:
        return None, "blank"
    if re.fullmatch(r"[\d,]+", raw):
        return float(raw.replace(",", "")), None
    return None, {"-": "dash", "na": "na", "N/A": "N/A", "***": "***", "**": "**"}[raw]

def yr(label):
    label = label.strip()
    return int(label.rstrip("*")), ("provisional" if label.endswith("*") else "final")

def rec(table, page_no, year_label, raw, **kw):
    y, st = yr(year_label)
    v, flag = conv(raw)
    d = {"table_id": table, "source_page_pdf": page_no, "year": y, "year_status": st}
    d.update(kw)
    d.update({"value": v, "value_as_published": raw if raw is not None else "", "value_flag": flag or "", "unit": "Mt"})
    return d

FD_STD = {"Matàra": "Matara", "Tangalla": "Tangalle", "Mullaithivu": "Mullaitivu"}

def split_label(line):
    """return (label_text, numeric_part_offset)"""
    m = re.match(r"^\s*(?:(\d{1,2})\s+)?(.*?)(?=\s{2,}(?:\d|-|na\b|N/A|\*\*)|\s*$)", line)
    return m

def district_table(p, years, table, kind, anchor_label="Total"):
    lines = page(p)
    tot = [l for l in lines if re.match(r"^\s*Total\b", l)][0]
    anchors = [e for _, e in toks(tot)]
    assert len(anchors) == len(years), (table, len(anchors), len(years))
    recs = []
    for l in lines:
        m = re.match(r"^\s*(\d{1,2})\s+([A-Za-zà' ]+?)\s{2,}", l)
        is_tot = bool(re.match(r"^\s*Total\b", l))
        if not (m or is_tot):
            continue
        if m:
            no, name = int(m.group(1)), m.group(2).strip()
            cells = assign(toks(l[m.end():], m.end()), anchors)
        else:
            no, name = None, "Total"
            cells = assign(toks(tot), anchors)
        for ylab, raw in zip(years, cells):
            r = {f"{kind}_no": no, kind + "_as_published": name,
                 kind + "_std": FD_STD.get(name, name.replace("Vavunia", "Vavuniya").replace("Nuwara eliya", "Nuwara Eliya")),
                 "is_total": is_tot}
            recs.append(rec(table, p, ylab, raw, **r))
    return recs

out = {}

# ---- 4.1 ----
lines = page(41)
cols41 = ["Coastal", "Off shore/Deep Sea", "Total Marine", "Inland & Aquaculture", "Total Fish Production",
          "Estimated Wet Fish for Dry or Other Products"]
parent = ["Marine Fish Catch", "Marine Fish Catch", "Marine Fish Catch", "", "", ""]
recs = []
for l in lines:
    m = re.match(r"^\s*(\d{4}\*?)\s+(.*)$", l)
    if not m: continue
    t = [x for x, _ in toks(m.group(2))]
    assert len(t) == 6, l
    for c, pa, raw in zip(cols41, parent, t):
        recs.append(rec("4.1", 41, m.group(1), raw, column_group_as_published=pa, subsector_as_published=c,
                        is_total=c.startswith("Total")))
out["bulletin2025_t4_1_fish_production_by_subsector"] = recs

# ---- 4.2 ----
y42 = [str(y) for y in range(2016, 2026)]
out["bulletin2025_t4_2_national_production_by_district"] = district_table(42, y42, "4.2", "district")

# ---- 4.3 ----
lines = page(43)
tot = [l for l in lines if re.match(r"^\s*Total\b", l)][0]
anchors = [e for _, e in toks(tot)]
colspec = [(y, s) for y in ["2023", "2024", "2025*"] for s in ["Marine", "Inland & Aquaculture", "Total"]]
recs = []
for l in lines:
    m = re.match(r"^\s*(\d{1,2})\s+([A-Za-z' ]+?)\s{2,}", l)
    is_tot = bool(re.match(r"^\s*Total\b", l))
    if not (m or is_tot): continue
    no, name = (int(m.group(1)), m.group(2).strip()) if m else (None, "Total")
    cells = assign(toks(l[m.end():], m.end()) if m else toks(tot), anchors)
    for (ylab, sub), raw in zip(colspec, cells):
        recs.append(rec("4.3", 43, ylab, raw, district_no=no, district_as_published=name,
                        district_std=name.replace("Vavunia", "Vavuniya").replace("Nuwara eliya", "Nuwara Eliya"),
                        subsector_as_published=sub, is_total=is_tot or sub == "Total"))
out["bulletin2025_t4_3_national_production_by_district_subsector"] = recs

# ---- 4.4 ----
y44 = ["1983", "1990", "1995", "2000", "2005", "2010", "2015", "2020", "2021", "2022", "2023", "2024", "2025*"]
out["bulletin2025_t4_4_marine_catch_by_fisheries_district"] = district_table(44, y44, "4.4", "fisheries_district")

# ---- 4.5 ----
lines = page(45)
y45 = ["2000", "2005", "2010", "2015", "2020", "2021", "2022", "2023", "2024", "2025*"]
tot = [l for l in lines if re.match(r"^\s*Total\b", l)][0]
anchors = [e for _, e in toks(tot)]
recs = []
for l in lines:
    m = re.match(r"^\s*(13)\s+(Others)\s{2,}()", l) or re.match(r"^\s*(\d{1,2})\s+(\S.*?)\s{2,}(\S.*?)\s{2,}(?=[\d*])", l)
    is_tot = bool(re.match(r"^\s*Total\b", l))
    if not (m or is_tot): continue
    if m:
        no, si, en = int(m.group(1)), m.group(2).strip(), m.group(3).strip()
        if no == 13: en = "Other marine varieties"
        cells = assign(toks(l[m.end():], m.end()), anchors)
    else:
        no, si, en = None, "Total", "Total"; cells = assign(toks(tot), anchors)
    for ylab, raw in zip(y45, cells):
        recs.append(rec("4.5", 45, ylab, raw, group_no=no, fish_group_as_published=si,
                        fish_group_english_as_published=en, is_total=is_tot))
for r in recs:
    if r["value_flag"] == "***": r["value_flag"] = "included_in_other_blood_fish (***)"
    if r["value_flag"] == "**": r["value_flag"] = "included_in_others (**)"
out["bulletin2025_t4_5_marine_catch_by_commercial_group"] = recs

# ---- 4.6 / 4.7 ----
G = ["Thora (Seer)", "Paraw (Trevally)", "Balaya (Skipjack tuna)", "Kelawalla (Yellowfin tuna)",
     "Tuna like fishes (other blood fishes)", "Thalapath (Billfish)", "Mora/Maduwa (Sharks/Skates)",
     "Gal Ma'lu (Rock fish)", "Shore Seine (Small fish)", "Issa (Shrimps)", "Pokirissa (Lobster)",
     "Kakuluwa (Crabs)", "Other fish", "Total"]
for p, ylab, tid, name in [(46, "2024", "4.6", "bulletin2025_t4_6_marine_catch_district_by_group_2024"),
                           (47, "2025*", "4.7", "bulletin2025_t4_7_marine_catch_district_by_group_2025")]:
    recs = []
    for l in page(p):
        m = re.match(r"^\s*(\d{1,2})\s+([A-Za-zà' ]+?)\s{2,}", l)
        is_tot = bool(re.match(r"^\s*Total\s+\d", l))
        if not (m or is_tot): continue
        t = [x for x, _ in toks(l[m.end():] if m else l)]
        assert len(t) == 14, (p, l)
        no, nm = (int(m.group(1)), m.group(2).strip()) if m else (None, "Total")
        for g, raw in zip(G, t):
            recs.append(rec(tid, p, ylab, raw, fisheries_district_no=no, fisheries_district_as_published=nm,
                            fisheries_district_std=FD_STD.get(nm, nm), fish_group_as_published=g,
                            is_total=is_tot or g == "Total"))
    out[name] = recs

# ---- 4.8 ----
lines = page(48)
y48 = ["2015", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025*"]
tot = [l for l in lines if re.match(r"^Total\b", l)][0]
anchors = [e for _, e in toks(tot)]
recs = []
section = None
sections = {"Capture Fishery": None}
ROWNAMES = ["Minor Perennial Reservoirs", "Seasonal Tanks", "Villu", "Rivers and Cannals", "Flood Plains", "Sub-Total",
            "Major Perennial Reservoirs", "Medium Perennial Reservoirs", "Estate Tanks", "Estate Ponds", "Cage Culture",
            "Pen Culture", "Ponds", "Shrimp Farms", "Lagoons (Fish)", "Raft", "Cement Tank"]
order = ["Capture Fishery"] * 6 + ["Culture Base Capture Fishery"] * 6 + ["Aquaculture (Freshwater)"] * 7 + ["Aquaculture (Brackishwater)"] * 8
i = 0
for l in lines:
    nm = None
    for rn in ROWNAMES:
        mm = re.search(r"(?<!\S)" + re.escape(rn) + r"(?=\s{2,})", l)
        if mm: nm = rn; break
    if nm and i < len(order):
        sec = order[i]; i += 1
        tk = toks(l[mm.end():], mm.end())
        if sec == "Culture Base Capture Fishery" and nm == "Rivers and Cannals":
            # published row shows dashes in every year except a blank 2024 cell (one dash is visually offset)
            vals = [t for t, _ in tk]; assert len(vals) == 8 and set(vals) == {"-"}, vals
            cells = ["-"] * 7 + [None] + ["-"]
        else:
            cells = assign(tk, anchors)
        for ylab, raw in zip(y48, cells):
            recs.append(rec("4.8", 48, ylab, raw, system_as_published=sec, waterbody_type_as_published=nm,
                            is_total=nm == "Sub-Total"))
    elif re.match(r"^Total\b", l) or l.startswith("Seaweed(Wet)"):
        lab = "Total" if l.startswith("Total") else "Seaweed(Wet)"
        cells = assign(toks(l[len(lab):], len(lab)), anchors)
        for ylab, raw in zip(y48, cells):
            recs.append(rec("4.8", 48, ylab, raw, system_as_published="" if lab == "Total" else "Seaweed",
                            waterbody_type_as_published=lab, is_total=lab == "Total"))
assert i == 27, i
for r in recs:
    if r["waterbody_type_as_published"] == "Seaweed(Wet)": r["unit"] = "Mt (wet weight)"
out["bulletin2025_t4_8_inland_aquaculture_by_waterbody"] = recs

# ---- 4.9 ----
y49 = ["2000", "2005", "2010", "2015", "2020", "2021", "2022", "2023", "2024", "2025*"]
recs = district_table(49, y49, "4.9", "district")
for r in recs:
    if r["value_flag"] == "na": r["value_flag"] = "na (published note: negligible amount)"
out["bulletin2025_t4_9_inland_aquaculture_by_district"] = recs

# ---- 4.10 ----
lines = page(50)
y410 = ["2010", "2011", "2012", "2013", "2014", "2015", "2020", "2021", "2022", "2023", "2024", "2025*"]
tot = [l for l in lines if re.match(r"^\s+Total\b", l)][0]
anchors = [e for _, e in toks(tot)]
SP = ["Tilapia", "Carps/Mirigal", "Catla/Rohu", "Hiri Kanaya", "Lula", "Cultured Shrimps", "Freshwater prawns",
      "Cultured Milk fish & Sea bass", "Sea cucumber", "Oyster and Crabs", "Lobster", "Other wild fish"]
recs = []
for l in lines:
    s = l.strip()
    nm = next((x for x in SP if s.startswith(x)), None)
    if s.startswith("Total"): nm = "Total"
    if not nm: continue
    st = l.index(nm) + len(nm)
    cells = assign(toks(l[st:], st), anchors)
    for ylab, raw in zip(y410, cells):
        recs.append(rec("4.10", 50, ylab, raw, species_group_as_published=nm, is_total=nm == "Total"))
out["bulletin2025_t4_10_inland_catch_by_species"] = recs

# ---- 4.11 ----
recs = []
for l in page(51):
    m = re.match(r"^\s*(\d{4}\*?)\s+(.*)$", l)
    if not m: continue
    t = [x for x, _ in toks(m.group(2))]; assert len(t) == 4
    for c, raw in zip(["Shrimps: Aquaculture", "Shrimps: Wild Capture", "Shrimps: Total", "Exported Quantity (1)"], t):
        recs.append(rec("4.11", 51, m.group(1), raw, measure_as_published=c, is_total=c == "Shrimps: Total"))
out["bulletin2025_t4_11_shrimp_production"] = recs

for name, recs in out.items():
    df = pd.DataFrame(recs)
    df["source_url"] = SRC
    for c in df.columns:
        if c.endswith("_no"): df[c] = df[c].astype("Int64")
    df.to_csv(ROOT / f"{name}.csv", index=False)
    df.to_parquet(ROOT / f"{name}.parquet", index=False)
    print(name, len(df))
