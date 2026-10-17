"""Extract chapter 8 (consumption/economy) tables + Table 6.10 (dried fish supply)
from the Sri Lanka Annual Fisheries Statistical Bulletin 2025 into tidy long CSV/Parquet.
Source text: pdftotext -layout; verified against page renders (PDF pages 83-86, 72)."""
import re, subprocess, pandas as pd
from pathlib import Path

BASE = Path("/workspace/srilanka-fisheries-official")
PDF = BASE / "raw/Annual-Fisheries-Statistical-Bulletin-2025.pdf"
URL = "https://www.fisheries.gov.lk/wp-content/uploads/2026/10/Annual-Fisheries-Statistical-Bulletin-2025.pdf"

def page_text(p):
    return subprocess.run(["pdftotext", "-f", str(p), "-l", str(p), "-layout", str(PDF), "-"],
                          capture_output=True, text=True, check=True).stdout.splitlines()

NUM = r"(?:-?[\d,]+\.\d+|-?[\d,]+|-)(?=\s|$)"
def split_row(line):
    """Return (label, [tokens]) where tokens are numeric strings or '-'."""
    m = re.match(r"^\s*(.*?[A-Za-z\)\]&/%])\s{2,}(.*)$", line) or re.match(r"^\s*(.*?[A-Za-z\)])\s+(\S.*)$", line)
    if not m: return None
    label, rest = m.group(1).strip(), m.group(2)
    toks = re.findall(NUM, rest)
    return label, toks

def num(t):
    if t is None or t == "-": return None
    return float(t.replace(",", ""))

# English hints: NOT in the PDF. Editor-supplied, with confidence.
HINTS = {
 "Balaya/Kelawalla": ("Skipjack tuna / Yellowfin tuna (as published; likely meant Balaya = skipjack only, see Kelawalla row)", "Katsuwonus pelamis / Thunnus albacares", "medium"),
 "Balaya": ("Skipjack tuna", "Katsuwonus pelamis", "high"),
 "Kelawalla": ("Yellowfin tuna", "Thunnus albacares", "high"),
 "Mora": ("Sharks", "Selachimorpha", "high"),
 "Mora/Keelan": ("Sharks (Sinhala/Tamil names)", "Selachimorpha", "medium"),
 "Thalapath": ("Sailfish / billfish", "Istiophorus platypterus (Istiophoridae)", "high"),
 "Paraw": ("Trevallies / jacks", "Carangidae (e.g. Caranx spp.)", "high"),
 "Seer": ("Seer fish (narrow-barred Spanish mackerel)", "Scomberomorus commerson", "high"),
 "Maduwa": ("Rays / skates", "Batoidea", "medium"),
 "Sprats": ("Anchovies (sprats, 'haal masso')", "Stolephorus / Encrasicholina spp.", "high"),
 "Hedella": ("Rainbow sardine (uncertain)", "Dussumieria spp. (uncertain)", "low"),
 "Hurulla": ("Herrings / sardinellas", "Sardinella spp.", "medium"),
 "Salaya/ Sudaya": ("Sardines (Salaya = sardinellas, Sudaya = white sardine)", "Sardinella / Amblygaster spp.", "medium"),
 "Salaya": ("Sardines / sardinellas", "Sardinella / Amblygaster spp.", "medium"),
 "Karalla/Katuwalla": ("Ponyfishes / silverbellies", "Leiognathidae", "medium"),
 "Kumbala": ("Indian mackerel", "Rastrelliger kanagurta", "high"),
 "Linna": ("Scads", "Decapterus spp.", "medium"),
 "Lula": ("Striped snakehead", "Channa striata", "high"),
 "Thilapiya": ("Tilapia", "Oreochromis spp.", "high"),
 "Prawns": ("Prawns / shrimps", "Penaeidae etc.", "high"),
 "Crabs": ("Crabs", "Brachyura", "high"),
 "Cuttle & Others": ("Cuttlefish, squid & other", "Cephalopoda etc.", "high"),
 "Cuttle fish": ("Cuttlefish", "Sepiidae", "high"),
 "Keerameen": ("Small dried fish, identity unclear (Tamil 'keeri meen')", "", "low"),
 "Katta": ("Queenfish", "Scomberoides spp.", "medium"),
 "Koduwa": ("Barramundi / Asian seabass", "Lates calcarifer", "medium"),
 "Anjila": ("Eels", "Anguilliformes", "medium"),
 "Anguluwa": ("Identity unclear", "", "low"),
}

# English names that the bulletin ITSELF gives for the same trade names (Tables 4.5, 4.6, 7.1/7.2)
BULLETIN_EN = {
 "Balaya": ("Skipjack tuna", "T4.5; T7.1"), "Kelawalla": ("Yellowfin tuna", "T4.5; T7.1"),
 "Balaya/Kelawalla": ("Skipjack tuna / Yellowfin tuna", "T4.5; T7.1 (component names)"),
 "Mora": ("Sharks", "T7.1"), "Mora/Keelan": ("Sharks (Mora)", "T7.1 (Mora only)"), "Maduwa": ("Skates (Mora/Maduwa = Sharks/Skates)", "T4.6"),
 "Thalapath": ("Sail fish (All bill fishes)", "T7.1; T4.5"), "Paraw": ("Travelly [sic, trevally]", "T4.5; T7.1 (as 'Para')"),
 "Seer": ("Seer (Thora)", "T4.5; T7.1"), "Hurulla": ("Herrings", "T7.1"), "Salaya": ("Sardinella", "T7.1"),
 "Salaya/ Sudaya": ("Sardinella (Salaya)", "T7.1 (Salaya only)"), "Kumbala": ("Indian mackerel", "T7.1 (as 'Kumbalawa')"),
 "Prawns": ("Prawns (Issa) / Shrimps", "T7.1; T4.5"), "Crabs": ("Crabs (Kakuluwa)", "T4.5"), "Thilapiya": ("Thilapia (Theppili)", "T7.1"),
}

YEARS4 = ["2009/2010", "2012/2013", "2016", "2019"]
HH = {"2009/2010": 4.0, "2012/2013": 3.9, "2016": 3.8, "2019": 3.7}

def hies_table(pdf_page, table_no, groups_fn):
    lines = page_text(pdf_page)
    start = next(i for i, l in enumerate(lines) if re.search(r"^\s*Species\s+Quantity", l)) + 1
    rows, order = [], 0
    for l in lines[start:]:
        if l.strip().startswith("Source"): break
        if not l.strip(): continue
        r = split_row(l)
        if not r: continue
        label, toks = r
        if label.startswith("Grams/Day/Person"):
            for y, t in zip(YEARS4, toks):
                rows.append(dict(row_label=label, survey_period=y, measure="grams_per_day_per_person", value=num(t), unit="g/day/person", value_flag="published"))
            continue
        # pad missing leading columns (blank cells are always the early survey years in this table)
        flags = ["published"] * 8
        if len(toks) < 8:
            pad = 8 - len(toks); toks = [None] * pad + toks; flags[:pad] = ["blank_not_reported"] * pad
        order += 1
        for k, y in enumerate(YEARS4):
            for j, (meas, unit) in enumerate([("quantity", "g/household/month"), ("percent_of_total", "%")]):
                t = toks[2 * k + j]; f = flags[2 * k + j]
                if t == "-": f = "dash_published"
                rows.append(dict(row_order=order, row_label=label, survey_period=y, measure=meas, value=num(t), unit=unit, value_flag=f))
    df = pd.DataFrame(rows)
    df["row_order"] = df["row_order"].astype("Int64")
    df["row_type"] = df["row_label"].map(lambda s: "total" if s == "Total" else "subtotal" if s.endswith("Total") else "derived" if s.startswith("Grams") else "item")
    df["group"] = groups_fn(df)
    df["household_size_persons"] = df["survey_period"].map(HH)
    df["survey_year_start"] = df["survey_period"].str[:4].astype(int)
    df["survey_year_end"] = df["survey_period"].map(lambda s: int(s.split("/")[1]) if "/" in s else int(s))
    df["english_name_in_bulletin"] = df["row_label"].map(lambda s: BULLETIN_EN.get(s, ("", ""))[0])
    df["english_name_bulletin_ref"] = df["row_label"].map(lambda s: BULLETIN_EN.get(s, ("", ""))[1])
    df["editor_english_hint"] = df["row_label"].map(lambda s: HINTS.get(s, ("", "", ""))[0])
    df["editor_scientific_hint"] = df["row_label"].map(lambda s: HINTS.get(s, ("", "", ""))[1])
    df["editor_hint_confidence"] = df["row_label"].map(lambda s: HINTS.get(s, ("", "", ""))[2])
    df["survey"] = "HIES (Household Income and Expenditure Survey), Dept. of Census & Statistics"
    df["source_table"] = table_no; df["source_pdf_page"] = pdf_page; df["source_printed_page"] = pdf_page - 14
    df = df.rename(columns={"row_label": "fish_type_as_published"})
    cols = ["source_table", "survey_period", "survey_year_start", "survey_year_end", "household_size_persons", "row_order",
            "group", "row_type", "fish_type_as_published", "english_name_in_bulletin", "english_name_bulletin_ref", "editor_english_hint", "editor_scientific_hint", "editor_hint_confidence",
            "measure", "value", "unit", "value_flag", "survey", "source_pdf_page", "source_printed_page"]
    return df[cols]

def groups_83(df):
    g, cur = [], None
    seq = {"Large Fish Total": "Marine large fish", "Small Fish Total": "Marine small fish", "Inland Fish Total": "Inland (freshwater) fish", "Crustacians Total": "Crustaceans & cephalopods"}
    # assign group by position: items before each subtotal belong to it
    labels = df.drop_duplicates("row_order").sort_values("row_order")
    mapping, bucket = {}, []
    for _, r in labels.iterrows():
        if pd.isna(r.row_order): continue
        bucket.append(r.row_order)
        if r.row_label in seq:
            for o in bucket: mapping[o] = seq[r.row_label]
            bucket = []
    for o in bucket: mapping[o] = "All"
    return df["row_order"].map(lambda o: mapping.get(o, "All") if pd.notna(o) else "All")

def groups_84(df):
    return "Dried fish"

out = {}
t83 = hies_table(84, "8.3", groups_83); out["bulletin2025_t8_3_household_fish_consumption"] = t83
t84 = hies_table(85, "8.4", groups_84); out["bulletin2025_t8_4_household_dried_fish_consumption"] = t84

# ---- Table 8.5 & 8.6 (page 86) ----
lines = page_text(86)
def wide_block(lines, start_pat, end_pat, years, table_no, unit_fn, section_rows=()):
    i0 = next(i for i, l in enumerate(lines) if re.search(start_pat, l)) + 1
    rows, section, order, pending = [], None, 0, ""
    for l in lines[i0:]:
        if re.search(end_pat, l): break
        if not l.strip(): continue
        r = split_row(l)
        label, toks = (r if r else (l.strip(), []))
        if not toks or len(toks) < len(years):
            # continuation / section header lines
            if label in section_rows: section = label; continue
            pending = (pending + " " + l.strip()).strip(); continue
        if pending and label in ("", None): label = pending
        elif pending: label = pending + " " + label if label[0].islower() or label.startswith("(") else label
        pending = ""
        order += 1
        for y, t in zip(years, toks[-len(years):]):
            rows.append(dict(source_table=table_no, row_order=order, section=section, item_as_published=label, survey_period=y, value=num(t), unit=unit_fn(label)))
    return rows

Y7 = ["1995/96", "2002/03", "2006/07", "2009/10", "2012/13", "2016", "2019"]
r85 = wide_block(lines, r"^\s*Item\s+1995/96", r"^Source", Y7, "8.5", lambda s: "kg/person/year", section_rows=("Fresh Fish", "Dried Fish"))
# section headers ("Fresh Fish", "Dried Fish") carry no numbers; assign by published row order (verified vs page render)
for r in r85:
    r["section"] = "Fresh Fish" if r["row_order"] <= 5 else "Dried Fish" if r["row_order"] <= 8 else "Canned Fish"
    r["row_type"] = "total" if r["item_as_published"] == "Total" else "item"
out["bulletin2025_t8_5_per_capita_fish_consumption"] = pd.DataFrame(r85)

# 8.6 has wrapped labels; parse explicitly from layout text
i0 = next(i for i, l in enumerate(lines) if re.search(r"^\s*Description\s+1995/96", l)) + 1
blk = [l for l in lines[i0:] if l.strip()]
blk = blk[:next(i for i, l in enumerate(blk) if l.strip().startswith("Source"))]
rows86, buf = [], []
for l in blk:
    toks = re.findall(NUM, l)
    text = re.sub(r"\s{2,}.*$", "", l.strip()) if len(toks) >= 7 else l.strip()
    if len(toks) >= 7:
        lab = text if not re.fullmatch(NUM, text.split()[0] if text else "-") else ""
        buf.append(("NUMS", toks[-7:], lab))
    else:
        buf.append(("TXT", None, l.strip()))
# merge: numeric line + surrounding text lines into a label
items, cur_lab, cur_nums = [], [], None
for kind, toks, txt in buf:
    if kind == "NUMS":
        if cur_nums is not None and txt:  # previous item complete, this line has own label
            items.append((" ".join(cur_lab), cur_nums)); cur_lab = []
        if txt: cur_lab.append(txt)
        cur_nums = toks
    else:
        if cur_nums is not None and cur_lab and not txt.startswith(("(", "for", "basket", "food")):
            items.append((" ".join(cur_lab), cur_nums)); cur_lab, cur_nums = [], None
        cur_lab.append(txt)
items.append((" ".join(cur_lab), cur_nums))
units86 = {"Average Household Size": "persons", "Avg. Household Expenditure (Rs) (1)": "Rs/household/month (current prices)",
           "Avg. Household Expenditure for Food Items (Rs) (1)": "Rs/household/month (current prices)",
           "Food Ratio (2) (%)": "%", "Contribution of fish to food basket (%)(3)": "%", "Contribution of dried fish to food basket (%)": "%"}
for o, (lab, toks) in enumerate(items, 1):
    for y, t in zip(Y7, toks):
        rows86.append(dict(source_table="8.6", row_order=o, item_as_published=lab, survey_period=y, value=num(t), unit=units86.get(lab, "?")))
t86 = pd.DataFrame(rows86)
t86["footnote"] = t86["item_as_published"].map(lambda s: "; ".join(n for k, n in [("(1)", "(1) At current price"), ("(2)", "(2) Proportion of expenditure on food and drink to total household expenditure"), ("(3)", "(3) Including canned fish")] if k in s))
out["bulletin2025_t8_6_household_fish_expenditure"] = t86

for name in ["bulletin2025_t8_5_per_capita_fish_consumption", "bulletin2025_t8_6_household_fish_expenditure"]:
    d = out[name]
    d["survey_year_start"] = d["survey_period"].str[:4].astype(int)
    d["survey"] = "HIES, Dept. of Census & Statistics" if name.endswith("expenditure") else "Statistics Division, Ministry of Fisheries (from HIES)"
    d["source_pdf_page"] = 86; d["source_printed_page"] = 72

# ---- Tables 8.1 / 8.2 GDP (page 83) ----
lines = page_text(83)
gdp = []
for tno, pat, basis in [("8.1", r"Table 8\.1", "current market prices"), ("8.2", r"Table 8\.2", "constant (2015) market prices")]:
    i0 = next(i for i, l in enumerate(lines) if re.search(pat, l))
    for l in lines[i0:]:
        m = re.match(r"^\s*(20\d\d)([†*]?)\s+(.*)$", l)
        if m:
            vals = re.findall(NUM, m.group(3))
            for col, v in zip(["GDP", "Agriculture sector", "Fishing - Marine", "Fishing - Inland", "Fishing - Total"], vals):
                gdp.append(dict(source_table=tno, price_basis=basis, year=int(m.group(1)),
                                estimate_status={"†": "revised (as at 17 Mar 2026)", "*": "provisional (as at 17 Mar 2026)", "": "final"}[m.group(2)],
                                indicator=col, value=num(v), unit="Rs. million"))
        if l.strip().startswith("Source") and gdp and gdp[-1]["source_table"] == tno: break
t81 = pd.DataFrame(gdp); t81["source"] = "National Accounts Reports, Dept. of Census & Statistics"; t81["source_pdf_page"] = 83; t81["source_printed_page"] = 69
out["bulletin2025_t8_1_8_2_gdp_fisheries"] = t81

# ---- Table 6.10 dried fish supply (page 72) ----
lines = page_text(72); s610 = []
for l in lines:
    m = re.match(r"^\s*((?:19|20)\d\d)(\*?)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s*$", l)
    if m:
        for col, v in zip(["Local production (1)", "Imported - Sprats (2)", "Imported - Other (2)", "Imported - Total (2)", "Total dried fish supply"], m.groups()[2:]):
            s610.append(dict(source_table="6.10", year=int(m.group(1)), estimate_status="provisional" if m.group(2) else "final", component=col, value=num(v), unit="tonnes (Mt as published)"))
t610 = pd.DataFrame(s610)
t610["footnote"] = t610["component"].map(lambda s: "(1) Annual estimates based on fish production, import/export quantity and canned fish production" if "(1)" in s else "(2) Customs returns" if "(2)" in s else "")
t610["source"] = "Statistics Unit, Ministry of Fisheries, Aquatic and Ocean Resources"; t610["source_pdf_page"] = 72; t610["source_printed_page"] = 58
out["bulletin2025_t6_10_dried_fish_supply"] = t610

for name, d in out.items():
    d.insert(0, "source_document", "Annual Fisheries Statistical Bulletin 2025 (Ministry of Fisheries, Sri Lanka)")
    d.to_csv(BASE / f"{name}.csv", index=False)
    d.to_parquet(BASE / f"{name}.parquet", index=False)
    print(name, len(d))
