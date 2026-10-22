import { Page, Section, Text, Grid, Metrics, Bars, Table, Select, Toggle, Input, Segmented, Callout, Rows, Properties, Legend, TableOfContents, Button, useGrokTheme, useState, useMemo } from "./canvas";

type TRow = [string, number, number, number, string, number, number | null, number | null, number, string | null, string | null, number, number, number, string, number];
type Zone = [string, string, string, string, number | null, number, string];
interface MapData { W: number; H: number; cell: number; land: string; zones: Zone[]; occ: number[]; gfw: number[]; gfwMax: number; gfwTotal: number; gfwCells: number; occN: number; gfwRange: string[]; ticks: number[][]; lticks: number[][] }
interface DataT { ds: string[]; th: string[]; ro: string[]; src: string[]; lic: string[]; licP: string[]; licC: string[]; t: TRow[]; nfiles: number; totalsize: number; ndocs: number; nraw: number; ntf: number; map: MapData }

import DATA from "../dashboard_data.json";
const D = DATA as unknown as DataT;

const REPO = "https://github.com/senesh2006/ocean_hackathon_data";

const DESC: Record<string, string> = {
  "fish-data": "v3 fish occurrences (OBIS + GBIF, WoRMS names), species list, env covariates, ML feature tables",
  "fish-factors": "Environmental drivers: SST, chl-a, currents, SLA, salinity, WOA23, winds, rainfall, climate indices, moon, monsoon, seabed, coral reefs",
  "species-niche": "Per-species niche and diet table, predator–prey links",
  "srilanka-fishing-restrictions": "Restriction zones, zone rules, species rules and the DFAR regulations register",
  "srilanka-banned-marine": "Banned and restricted marine species, gear and area rules",
  "srilanka-fish-genetics": "BOLD and GenBank barcode metadata and FASTA sequences",
  "srilanka-fish-morphology": "FishBase species traits and population tables",
  "srilanka-fish-movement-tagging": "Documentation of tagging sources only; no data downloaded",
  "srilanka-fisheries-official": "Ministry species list and Fisheries Statistical Bulletin 2025 tables",
  "updated data sets": "Superseded v2 partial upload; use fish-data v3 instead",
  "GFW fishing effort (root)": "Global Fishing Watch monthly fishing hours, 0.1° grid (Fishing_sl.csv)",
  "SplitWater RO log (root)": "RO unit sample log, 1 h at 5 s (splitwater_ro_log_1h_5s.csv)",
  "Repo metadata": "Machine-readable data library (data_library.csv / .parquet)",
};

const SOURCES: [string, string, string, string][] = [
  ["Global Fishing Watch", "Monthly fishing-effort grid, 2012–2024", "CC BY-NC 4.0", "Non-commercial"],
  ["OBIS", "Fish occurrences and checklist", "Per record: CC0 / CC BY / CC BY-NC", "Non-commercial"],
  ["GBIF", "Fish occurrences", "Per record: CC0 / CC BY / CC BY-NC", "Non-commercial"],
  ["WoRMS", "Accepted names and AphiaIDs", "CC BY 4.0", "Open"],
  ["FishBase v24.07", "Species list, traits, population tables, diet", "CC BY-NC 4.0", "Non-commercial"],
  ["AquaMaps HSPEN", "Species environmental envelopes", "CC BY-NC 4.0", "Non-commercial"],
  ["GloBI", "Predator–prey interactions", "Per underlying dataset, cite each", "Custom / no stated licence"],
  ["IOTC Secretariat", "Retained catch 1950–2025, resolutions", "Public, acknowledge source", "Custom / no stated licence"],
  ["ESA OC-CCI v6.0", "Chlorophyll-a", "CC BY 4.0", "Open"],
  ["NOAA Coral Reef Watch", "Sea-surface temperature", "Public domain (US Gov)", "Open"],
  ["NOAA NCEI ETOPO 2022", "Bathymetry", "Public domain (US Gov)", "Open"],
  ["NOAA NCEI World Ocean Atlas 2023", "Temperature, salinity, oxygen climatology; MLD", "Public domain (US Gov)", "Open"],
  ["NOAA CoastWatch blended products", "Surface currents, sea-surface height", "Public domain (US Gov)", "Open"],
  ["NOAA NCEI Blended Sea Winds", "Winds and wind stress", "Public domain (US Gov)", "Open"],
  ["NASA/NOAA SMAP", "Sea-surface salinity", "Public domain (US Gov)", "Open"],
  ["GPCP v2.3 (NOAA PSL)", "Rainfall, 2.5° grid", "Public domain (US Gov)", "Open"],
  ["CHIRPS v2 (UCSB CHC)", "Rainfall over land, 0.05° grid", "Public domain", "Open"],
  ["NOAA PSL and CPC", "DMI and ONI climate indices", "Public domain (US Gov)", "Open"],
  ["UNEP-WCMC Coral Reefs v4.1", "Coral reef polygons (avoid layer)", "Non-commercial", "Non-commercial"],
  ["BOLD Systems", "DNA barcodes", "CC BY-SA 4.0", "Share-alike"],
  ["NCBI GenBank", "DNA sequences", "NCBI terms", "Custom / no stated licence"],
  ["Ministry of Fisheries Sri Lanka", "Bulletin 2025 tables, species list", "No stated licence", "Custom / no stated licence"],
  ["Sri Lanka Govt Gazettes and Acts", "Rules, regulations register", "Govt legal texts, cite gazette", "Custom / no stated licence"],
  ["Marine Regions v12", "EEZ, 12/24 NM, India boundary lines", "CC BY 4.0", "Open"],
  ["OpenStreetMap (Nominatim)", "Protected-area and lagoon shapes", "ODbL 1.0", "Share-alike"],
  ["geoBoundaries LKA ADM2", "District boundaries for coastal bands", "ODbL 1.0", "Share-alike"],
  ["Natural Earth", "Land mask", "Public domain", "Open"],
  ["Wikidata", "Protected-area reference points", "CC0", "Open"],
  ["CITES / IUCN", "Species listings", "Public documents, cite", "Custom / no stated licence"],
  ["Dept. of Meteorology; de Vos et al. 2014", "Monsoon calendar", "Compiled, CC BY 4.0", "Open"],
  ["PyEphem (computed)", "Daily moon phase 2000–2027", "Computed, CC BY 4.0", "Open"],
];

const LIC_CLASSES = ["Open", "Share-alike", "Non-commercial", "Custom / no stated licence", "Unknown"];

interface Item { id: string; name: string; ds: string; th: string; role: string; fmt: string; files: number; rows: number | null; cols: number | null; size: number; t0: string | null; t1: string | null; sp: boolean; src: string; licP: string; licC: string; date: string; sup: boolean; url: string }

function ghUrl(id: string): string {
  if (id.endsWith(" (raw files)")) return `${REPO}/tree/main/${encodeURI(id.replace("/ (raw files)", ""))}`;
  if (!id.includes("/")) return `${REPO}/blob/main/${encodeURI(id)}.csv`;
  const dir = id.substring(0, id.lastIndexOf("/"));
  return `${REPO}/tree/main/${encodeURI(dir)}`;
}

const ITEMS: Item[] = D.t.map((r: TRow): Item => {
  const id = r[0];
  const raw = id.endsWith(" (raw files)");
  const parts = id.replace("/ (raw files)", "").split("/");
  const name = raw ? `${parts[parts.length - 1]}/ (${r[5]} raw files)` : parts[parts.length - 1];
  return { id, name, ds: D.ds[r[1]], th: D.th[r[2]], role: D.ro[r[3]], fmt: r[4], files: r[5], rows: r[6], cols: r[7], size: r[8], t0: r[9], t1: r[10], sp: r[11] === 1, src: D.src[r[12]], licP: D.licP[r[13]], licC: D.licC[r[13]], date: r[14], sup: r[15] === 1, url: ghUrl(id) };
});

function fmtN(n: number): string { return n.toLocaleString("en-US"); }
function fmtB(b: number): string {
  if (b >= 1e6) return `${(b / 1e6).toFixed(1)} MB`;
  if (b >= 1e3) return `${Math.round(b / 1e3)} KB`;
  return `${b} B`;
}
function fmtShort(n: number): string {
  if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
  if (n >= 1e4) return `${Math.round(n / 1e3)}K`;
  return fmtN(n);
}
function yearOf(s: string): number {
  const y = parseInt(s.substring(0, 4), 10);
  const m = s.length >= 7 ? parseInt(s.substring(5, 7), 10) : 1;
  return y + (m - 1) / 12;
}
function licTone(c: string): "warning" | "danger" | undefined {
  if (c === "Unknown") return "danger";
  if (c === "Non-commercial" || c === "Custom / no stated licence") return "warning";
  return undefined;
}
function zoneGroup(t: string): number {
  if (t === "maritime_zone" || t === "boundary_line") return -1;
  if (t === "marine_protected_area" || t === "coastal_protected_area") return 0;
  if (t === "coastal_gear_band" || t === "gear_restricted_area") return 1;
  return 2;
}

type Metric = "rows" | "size" | "tables";

export default function App() {
  const theme = useGrokTheme();
  const cat = theme.dataviz.categorical;
  const [fTheme, setFTheme] = useState<string>("all");
  const [fLic, setFLic] = useState<string>("all");
  const [fDs, setFDs] = useState<string>("all");
  const [aux, setAux] = useState<boolean>(true);
  const [sup, setSup] = useState<boolean>(false);
  const [q, setQ] = useState<string>("");
  const [metric, setMetric] = useState<Metric>("rows");
  const [range, setRange] = useState<string>("1950");
  const [layer, setLayer] = useState<string>("zones");
  const [hover, setHover] = useState<string>("");
  const [cols, setCols] = useState<string>("overview");
  const [sort, setSort] = useState<string>("size");

  const items = useMemo((): Item[] => ITEMS.filter((x: Item) =>
    (fTheme === "all" || x.th === fTheme) &&
    (fLic === "all" || x.licC === fLic) &&
    (fDs === "all" || x.ds === fDs) &&
    (aux || x.role === "Data") &&
    (sup || !x.sup) &&
    (q === "" || (x.id + " " + x.src + " " + x.licP).toLowerCase().includes(q.toLowerCase()))
  ), [fTheme, fLic, fDs, aux, sup, q]);

  const tot = useMemo(() => {
    const dsSet = new Set<string>();
    let files = 0, tables = 0, rows = 0, size = 0;
    items.forEach((x: Item) => { dsSet.add(x.ds); files += x.files; size += x.size; if (x.rows !== null) { tables += 1; rows += x.rows; } });
    return { ds: dsSet.size, files, tables, rows, size };
  }, [items]);

  function group(key: (x: Item) => string): { label: string; value: number; display: string; meta: string }[] {
    const m = new Map<string, { rows: number; size: number; tables: number }>();
    items.forEach((x: Item) => {
      const k = key(x);
      const g = m.get(k) || { rows: 0, size: 0, tables: 0 };
      g.rows += x.rows || 0; g.size += x.size; if (x.rows !== null) g.tables += 1;
      m.set(k, g);
    });
    const out: { label: string; value: number; display: string; meta: string }[] = [];
    m.forEach((g, k) => {
      const v = metric === "rows" ? g.rows : metric === "size" ? g.size : g.tables;
      const display = metric === "rows" ? fmtShort(v) : metric === "size" ? fmtB(v) : fmtN(v);
      const meta = metric === "tables" ? fmtB(g.size) : `${g.tables} tables`;
      if (v > 0) out.push({ label: k, value: v, display, meta });
    });
    return out.sort((a, b) => b.value - a.value);
  }
  const byDs = group((x: Item) => x.ds);
  const byTheme = group((x: Item) => x.th);
  const byLic = group((x: Item) => x.licC);

  const licTable = useMemo(() => {
    const m = new Map<string, { c: string; tables: number; rows: number; size: number }>();
    items.forEach((x: Item) => {
      const g = m.get(x.licP) || { c: x.licC, tables: 0, rows: 0, size: 0 };
      if (x.rows !== null) g.tables += 1; g.rows += x.rows || 0; g.size += x.size;
      m.set(x.licP, g);
    });
    const arr: [string, { c: string; tables: number; rows: number; size: number }][] = [];
    m.forEach((g, k) => arr.push([k, g]));
    return arr.sort((a, b) => b[1].size - a[1].size);
  }, [items]);

  const dsTable = useMemo(() => {
    const m = new Map<string, { tables: number; files: number; rows: number; size: number; date: string; lic: Set<string>; th: Set<string> }>();
    items.forEach((x: Item) => {
      const g = m.get(x.ds) || { tables: 0, files: 0, rows: 0, size: 0, date: "", lic: new Set<string>(), th: new Set<string>() };
      if (x.rows !== null) g.tables += 1; g.files += x.files; g.rows += x.rows || 0; g.size += x.size;
      if (x.date > g.date) g.date = x.date; g.lic.add(x.licC); if (x.th !== "Catalog & metadata") g.th.add(x.th);
      m.set(x.ds, g);
    });
    const arr: [string, { tables: number; files: number; rows: number; size: number; date: string; lic: Set<string>; th: Set<string> }][] = [];
    m.forEach((g, k) => arr.push([k, g]));
    return arr.sort((a, b) => b[1].size - a[1].size);
  }, [items]);

  const timeline = useMemo((): Item[] => items.filter((x: Item) => x.t0 !== null && x.t1 !== null && x.role !== "Metadata")
    .sort((a: Item, b: Item) => yearOf(a.t0 || "") - yearOf(b.t0 || "")), [items]);

  const inv = useMemo((): Item[] => {
    const a = items.slice();
    if (sort === "size") a.sort((x: Item, y: Item) => y.size - x.size);
    else if (sort === "rows") a.sort((x: Item, y: Item) => (y.rows || 0) - (x.rows || 0));
    else if (sort === "updated") a.sort((x: Item, y: Item) => y.date.localeCompare(x.date));
    else a.sort((x: Item, y: Item) => x.id.localeCompare(y.id));
    return a;
  }, [items, sort]);

  const linkStyle = { color: theme.text.primary, textDecoration: "underline", textDecorationColor: theme.border.strong };
  const link = (href: string, text: string) => <a href={href} target="_blank" rel="noreferrer" style={linkStyle}>{text}</a>;

  const themeOpts = [{ value: "all", label: "All themes" }, ...D.th.map((t: string) => ({ value: t, label: t }))];
  const licOpts = [{ value: "all", label: "All licence types" }, ...LIC_CLASSES.map((t: string) => ({ value: t, label: t }))];
  const dsOpts = [{ value: "all", label: "All datasets" }, ...D.ds.map((t: string) => ({ value: t, label: t }))];
  const reset = () => { setFTheme("all"); setFLic("all"); setFDs("all"); setAux(true); setSup(false); setQ(""); };

  // timeline geometry
  const start = parseInt(range, 10);
  const end = 2028;
  const TW = 1200, LW = 420, RH = 18, TP = 26;
  const TH = TP + timeline.length * RH + 10;
  const tx = (y: number) => LW + (Math.max(start, Math.min(end, y)) - start) / (end - start) * (TW - LW - 20);
  const span = end - start;
  const step = span > 200 ? 50 : span > 60 ? 15 : 5;
  const ticks: number[] = [];
  for (let y = Math.ceil(start / step) * step; y <= end; y += step) ticks.push(y);

  // map
  const M = D.map;
  const hz = M.zones.find((z: Zone) => z[0] === hover);
  const seq = theme.dataviz.sequential;
  const zonesSorted = M.zones.slice().sort((a: Zone, b: Zone) => {
    const ga = zoneGroup(a[2]), gb = zoneGroup(b[2]);
    const oa = ga === -1 ? -1 : ga === 0 ? 3 : ga;
    const ob = gb === -1 ? -1 : gb === 0 ? 3 : gb;
    return oa - ob;
  });
  const occPts: number[][] = [];
  for (let i = 0; i < M.occ.length; i += 2) occPts.push([M.occ[i], M.occ[i + 1]]);
  const gfwCells: number[][] = [];
  for (let i = 0; i < M.gfw.length; i += 3) gfwCells.push([M.gfw[i], M.gfw[i + 1], M.gfw[i + 2]]);
  const zoneCount = (g: number) => M.zones.filter((z: Zone) => zoneGroup(z[2]) === g).length;

  const dataTables = ITEMS.filter((x: Item) => x.rows !== null && !x.sup && x.role === "Data");
  const dataRows = dataTables.reduce((s: number, x: Item) => s + (x.rows || 0), 0);
  const allTables = ITEMS.filter((x: Item) => x.rows !== null);

  return (
    <Page title="SplitWater data repo dashboard" width="full"
      summary={`Everything in senesh2006/ocean_hackathon_data on main (commit 01a1d48, 21 Oct 2026): ${fmtN(D.nfiles)} tracked files, ${fmtB(D.totalsize)}, ${allTables.length} tables across ${D.ds.length} datasets, from ${SOURCES.length} upstream sources. Every figure was computed from the files themselves.`}>
      <TableOfContents items={[
        { label: "Filters and headline numbers", id: "filters" },
        { label: "Rows and size by dataset", id: "bydataset" },
        { label: "Themes and licence types", id: "themes" },
        { label: "Map of spatial data", id: "map" },
        { label: "Time coverage", id: "timeline" },
        { label: "Datasets", id: "datasets" },
        { label: "File inventory", id: "inventory" },
        { label: "Licences", id: "licences" },
        { label: "Licence flags and caveats", id: "caveats" },
        { label: "Upstream sources", id: "sources" },
      ]} />

      <Section heading="Filters and headline numbers" id="filters">
        <Grid columns={4} plain>
          <Select label="Theme" options={themeOpts} value={fTheme} onChange={(v: string) => setFTheme(v)} />
          <Select label="Licence type" options={licOpts} value={fLic} onChange={(v: string) => setFLic(v)} />
          <Select label="Dataset" options={dsOpts} value={fDs} onChange={(v: string) => setFDs(v)} />
          <Input label="Search path, source or licence" value={q} onChange={(v: string) => setQ(v)} placeholder="e.g. sst, FishBase, NC" />
        </Grid>
        <Grid columns={3} plain>
          <Toggle label="Include QC, metadata and raw files" value={aux} onChange={(v: boolean) => setAux(v)} />
          <Toggle label="Include superseded v2 folder" value={sup} onChange={(v: boolean) => setSup(v)} />
          <Button label="Reset filters" onClick={reset} />
        </Grid>
        <Text>{`Current data tables, without QC, metadata or superseded copies: ${dataTables.length} tables and ${fmtN(dataRows)} rows. The figures below follow the filters. A CSV and its Parquet copy count as one table.`}</Text>
        <Metrics metrics={[
          { value: fmtN(tot.ds), label: "Datasets", detail: `of ${D.ds.length} in the repo` },
          { value: fmtN(tot.tables), label: "Tables", detail: `${fmtN(tot.files)} files` },
          { value: fmtShort(tot.rows), label: "Rows", detail: fmtN(tot.rows) },
          { value: fmtB(tot.size), label: "Size", detail: `of ${fmtB(D.totalsize)} total` },
        ]} />
      </Section>

      <Section heading="Rows and size by dataset" id="bydataset" actions={<Segmented options={[{ value: "rows", label: "Rows" }, { value: "size", label: "Size" }, { value: "tables", label: "Tables" }]} value={metric} onChange={(v: Metric) => setMetric(v)} />}>
        <Bars bars={byDs} />
      </Section>

      <Section heading="Themes and licence types" id="themes" caption="Same measure as the chart above.">
        <Grid columns={2}>
          <Section heading="By theme">
            <Bars bars={byTheme} />
          </Section>
          <Section heading="By licence type">
            <Bars bars={byLic} />
          </Section>
        </Grid>
      </Section>

      <Section heading="Map of spatial data" id="map" actions={<Segmented options={[{ value: "zones", label: "Restriction zones" }, { value: "occ", label: "Fish occurrences" }, { value: "gfw", label: "Fishing effort" }]} value={layer} onChange={(v: string) => setLayer(v)} />}>
        <Grid columns={2}>
          <div>
            {layer === "zones" && <Legend names={["Protected areas", "Gear-restriction bands", "Management areas"]} />}
            {layer === "occ" && <Legend names={[`Sampled occurrences (800 of ${fmtN(M.occN)})`]} />}
            <svg viewBox={`0 0 ${M.W} ${M.H}`} width="100%" style={{ display: "block" }}>
              {layer === "gfw" && gfwCells.map((c: number[], i: number) => (
                <rect key={i} x={c[0]} y={c[1]} width={M.cell + 0.6} height={M.cell + 0.6} fill={seq[Math.min(seq.length - 1, Math.round((c[2] / 9) * (seq.length - 1)))]} />
              ))}
              <path d={M.land} fill={theme.bg.subtle} stroke={theme.border.strong} strokeWidth={0.8} />
              {zonesSorted.map((z: Zone) => {
                const g = zoneGroup(z[2]);
                if (z[6] === "") return null;
                if (g === -1) {
                  return <path key={z[0]} d={z[6]} fill="none" stroke={theme.dataviz.other} strokeWidth={hover === z[0] ? 2 : 1} strokeDasharray={z[2] === "boundary_line" ? "" : "4 3"} onMouseEnter={() => setHover(z[0])} onClick={() => setHover(z[0])} style={{ cursor: "pointer" }} />;
                }
                if (layer !== "zones") return null;
                const col = cat[g];
                return <path key={z[0]} d={z[6]} fill={col + (hover === z[0] ? "99" : theme.dataviz.areaAlpha)} stroke={col} strokeWidth={hover === z[0] ? 2 : 0.8} onMouseEnter={() => setHover(z[0])} onClick={() => setHover(z[0])} style={{ cursor: "pointer" }} />;
              })}
              {layer === "occ" && occPts.map((p: number[], i: number) => (
                <circle key={i} cx={p[0]} cy={p[1]} r={2.4} fill={cat[0]} fillOpacity={0.55} />
              ))}
              {M.ticks.map((t: number[]) => (
                <text key={"x" + t[0]} x={t[1]} y={M.H - 6} textAnchor="middle" fill={theme.text.tertiary} style={{ fontSize: theme.font.label.fontSize }}>{`${t[0]}°E`}</text>
              ))}
              {M.lticks.map((t: number[]) => (
                <text key={"y" + t[0]} x={6} y={t[1]} fill={theme.text.tertiary} style={{ fontSize: theme.font.label.fontSize }}>{`${t[0]}°N`}</text>
              ))}
              {layer === "gfw" && seq.map((c: string, i: number) => (
                <rect key={"lg" + i} x={430 + i * 16} y={M.H - 40} width={16} height={10} fill={c} />
              ))}
              {layer === "gfw" && <text x={430} y={M.H - 46} fill={theme.text.secondary} style={{ fontSize: theme.font.label.fontSize }}>Fishing hours, log scale: low to high</text>}
            </svg>
          </div>
          <div>
            {layer === "zones" && (
              <Properties items={hz ? [
                { label: "Zone", value: hz[1] },
                { label: "ID", value: `\`${hz[0]}\`` },
                { label: "Type", value: hz[2].split("_").join(" ") },
                { label: "Geometry quality", value: hz[3].split("_").join(" ") },
                { label: "Area", value: hz[4] === null ? "Line feature" : `${fmtN(hz[4])} km²` },
                { label: "Rules linked", value: fmtN(hz[5]) },
              ] : [
                { label: "Zones in zones.csv", value: "40" },
                { label: "Drawn here", value: `${M.zones.filter((z: Zone) => z[6] !== "").length} (EEZ, 12 NM sea and 4 IMBL lines as outlines)` },
                { label: "Protected areas", value: fmtN(zoneCount(0)) },
                { label: "Gear-restriction bands", value: fmtN(zoneCount(1)) },
                { label: "Management areas", value: fmtN(zoneCount(2)) },
                { label: "Not mappable", value: "12 zones with no geometry, plus the combined Sri Lanka Waters polygon left out as it overlaps the EEZ" },
                { label: "Selected zone", value: "Hover over or tap a zone" },
              ]} />
            )}
            {layer === "occ" && (
              <Properties items={[
                { label: "File", value: "`fish-data/merged/srilanka_fish_occurrences_clean`" },
                { label: "Records", value: `${fmtN(M.occN)} clean marine fish occurrences, 1900–2026` },
                { label: "Shown", value: "800 sampled at random (seed 7)" },
                { label: "Sources", value: "OBIS + GBIF, names resolved with WoRMS" },
                { label: "Licence", value: "Per record: 1,497 CC0, 2,385 CC BY, 2,097 CC BY-NC, 25 unknown" },
              ]} />
            )}
            {layer === "gfw" && (
              <Properties items={[
                { label: "File", value: "`Fishing_sl.csv`" },
                { label: "Period", value: `${M.gfwRange[0]} to ${M.gfwRange[1]}, monthly` },
                { label: "Total fishing hours", value: fmtN(M.gfwTotal) },
                { label: "Cells shown", value: `${fmtN(M.gfwCells)} cells, the 0.1° grid summed into 0.2° cells` },
                { label: "Busiest cell", value: `${fmtN(M.gfwMax)} hours` },
                { label: "Caveat", value: "Only AIS-equipped vessels, and coverage jumps around 2022" },
                { label: "Licence", value: "CC BY-NC 4.0 (Global Fishing Watch)" },
              ]} />
            )}
          </div>
        </Grid>
      </Section>

      <Section heading="Time coverage" id="timeline" caption="Observation time range per table, from its own date or year columns. Climatologies and static layers have none and are left out." actions={<Segmented options={[{ value: "1750", label: "Since 1750" }, { value: "1950", label: "Since 1950" }, { value: "2000", label: "Since 2000" }]} value={range} onChange={(v: string) => setRange(v)} />}>
        {timeline.length > 0 && (
          <svg viewBox={`0 0 ${TW} ${TH}`} width="100%" style={{ display: "block" }}>
            {ticks.map((y: number) => (
              <g key={y}>
                <line x1={tx(y)} x2={tx(y)} y1={TP - 6} y2={TH - 6} stroke={theme.border.subtle} />
                <text x={tx(y)} y={TP - 10} textAnchor="middle" fill={theme.text.tertiary} style={{ fontSize: theme.font.label.fontSize }}>{y}</text>
              </g>
            ))}
            {timeline.map((x: Item, i: number) => {
              const a = yearOf(x.t0 || ""), b = yearOf(x.t1 || "") + (x.t1 && x.t1.length === 4 ? 1 : 1 / 12);
              const y = TP + i * RH;
              const clipped = a < start;
              const label = x.name.length > 54 ? x.name.substring(0, 53) + "…" : x.name;
              return (
                <g key={x.id}>
                  <text x={0} y={y + 12} fill={theme.text.secondary} style={{ fontSize: theme.font.label.fontSize }}>{`${label}  ${x.t0}–${x.t1}`}</text>
                  <rect x={tx(a)} y={y + 4} width={Math.max(3, tx(b) - tx(a))} height={RH - 8} rx={2} fill={x.role === "Data" ? cat[0] : theme.dataviz.singleSeriesRest} />
                  {clipped && <text x={LW - 4} y={y + 12} textAnchor="end" fill={theme.text.tertiary} style={{ fontSize: theme.font.label.fontSize }}>◂</text>}
                </g>
              );
            })}
          </svg>
        )}
      </Section>

      <Section heading="Datasets" id="datasets">
        <Table columns={["Dataset", "What it holds", "Tables", "Files", "Rows", "Size", "Licence types", "Last commit"]}
          rows={dsTable.map(([k, g]) => [
            k.includes("(root)") || k === "Repo metadata" ? link(REPO, k) : link(`${REPO}/tree/main/${encodeURI(k)}`, k),
            DESC[k] || "",
            fmtN(g.tables), fmtN(g.files), fmtN(g.rows), fmtB(g.size),
            Array.from(g.lic).join(", "), g.date,
          ])} />
      </Section>

      <Section heading="File inventory" id="inventory" caption={`${inv.length} entries. Each name links to its folder on GitHub; raw text, JSON and PDF files are grouped per folder.`}
        actions={<Segmented options={[{ value: "overview", label: "Overview" }, { value: "prov", label: "Provenance" }]} value={cols} onChange={(v: string) => setCols(v)} />}>
        <Segmented options={[{ value: "size", label: "Largest" }, { value: "rows", label: "Most rows" }, { value: "updated", label: "Recently updated" }, { value: "name", label: "Path A–Z" }]} value={sort} onChange={(v: string) => setSort(v)} />
        {cols === "overview" ? (
          <Table columns={["Table", "Dataset", "Theme", "Role", "Format", "Rows", "Cols", "Size", "Updated"]}
            rows={inv.map((x: Item) => [link(x.url, x.name), x.ds, x.th, x.sup ? { text: "Superseded", tone: "warning" } : x.role, x.fmt, x.rows === null ? "–" : fmtN(x.rows), x.cols === null ? "–" : fmtN(x.cols), fmtB(x.size), x.date])} />
        ) : (
          <Table columns={["Table", "Time coverage", "Spatial", "Source", "Licence"]}
            rows={inv.map((x: Item) => [link(x.url, x.name), x.t0 ? `${x.t0} to ${x.t1}` : "–", x.sp ? "Lat/lon" : "–", x.src, licTone(x.licC) ? { text: x.licP, tone: licTone(x.licC) } : x.licP])} />
        )}
      </Section>

      <Section heading="Licences" id="licences" caption="Licence as recorded in data_library.csv, or in the folder catalog for species-niche and srilanka-fishing-restrictions.">
        <Table columns={["Licence", "Type", "Tables", "Rows", "Size"]}
          rows={licTable.map(([k, g]) => [k, licTone(g.c) ? { text: g.c, tone: licTone(g.c) } : g.c, fmtN(g.tables), fmtN(g.rows), fmtB(g.size)])} />
      </Section>

      <Section heading="Licence flags and caveats" id="caveats">
        <Callout tone="warning" lead="Non-commercial data runs through the core model inputs.">
          <Text>The GFW effort grid, FishBase and AquaMaps-derived tables (species list, traits, species-niche) and the coral reef layer are all non-commercial. SplitWater can use them for the hackathon with credit, but a commercial launch would need them replaced or licensed.</Text>
        </Callout>
        <Rows rows={[
          { title: "Global Fishing Watch effort grid", detail: "CC BY-NC 4.0. Owner to confirm the BigQuery export terms. AIS vessels only.", status: { label: "Non-commercial", tone: "warning" } },
          { title: "FishBase v24.07 and AquaMaps", detail: "CC BY-NC 4.0. Covers species_list, morphology traits and population tables, trawl flags and all of species-niche.", status: { label: "Non-commercial", tone: "warning" } },
          { title: "UNEP-WCMC coral reefs v4.1", detail: "Non-commercial. The seabed shelf habitat grid is derived from it as well.", status: { label: "Non-commercial", tone: "warning" } },
          { title: "OBIS and GBIF occurrences", detail: "Licence varies by record. Of 6,004 clean records: 1,497 CC0, 2,385 CC BY, 2,097 CC BY-NC and 25 unknown. Treat unknown rows as all rights reserved.", status: { label: "Mixed", tone: "warning" } },
          { title: "Ministry of Fisheries Bulletin 2025", detail: "No licence stated, so all rights are reserved by default. 2025 values are provisional. Two source PDFs are re-hosted in raw/.", status: { label: "All rights reserved", tone: "danger" } },
          { title: "Gazette and Act text extracts", detail: "88 gazette text files plus Act extracts in raw/. Government legal texts with unclear copyright status. The PDFs are linked, not re-hosted.", status: { label: "Unclear", tone: "warning" } },
          { title: "OSM and geoBoundaries geometries", detail: "ODbL 1.0 share-alike applies to the OSM-derived zones and the district coastal bands.", status: { label: "Share-alike" } },
          { title: "BOLD barcodes", detail: "CC BY-SA 4.0 share-alike.", status: { label: "Share-alike" } },
          { title: "SplitWater RO log", detail: "Provenance unknown. Its timestamps fall after the commit time, so it looks like a synthetic sample.", status: { label: "Unknown", tone: "danger" } },
          { title: "updated data sets/ folder", detail: "Superseded v2 partial upload. Use fish-data v3. Hidden unless the superseded toggle is on.", status: { label: "Superseded", tone: "warning" } },
          { title: "Restriction zone geometry", detail: "Approximate shapes (point buffers, coarse coastline bands) are not legal boundaries, and 12 of 40 zones have no geometry.", status: { label: "Approximate" } },
          { title: "srilanka-fish-movement-tagging", detail: "Documentation only. No tagging data was downloaded.", status: { label: "No data" } },
          { title: "Not in this repo", detail: "There are no groundwater, river salt-front, drinking-water or flood-risk datasets here. Only the RO log touches water." },
        ]} />
      </Section>

      <Section heading="Upstream sources" id="sources" caption={`${SOURCES.length} upstream sources, including one computed (moon phase).`}>
        <Table columns={["Source", "Provides", "Licence", "Type"]}
          rows={SOURCES.map((s: [string, string, string, string]) => [s[0], s[1], s[2], licTone(s[3]) ? { text: s[3], tone: licTone(s[3]) } : s[3]])} />
      </Section>
    </Page>
  );
}
