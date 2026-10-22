// Minimal stand-ins for the Cursor canvas components ("grok/canvas"),
// so the dashboard source (App.tsx) runs as a plain React app.
import React, { useState, useMemo, ReactNode } from "react";
export { useState, useMemo };

type Tone = "warning" | "danger" | "success" | "info" | undefined;

const THEME = {
  text: { primary: "#16181d", secondary: "#4a5060", tertiary: "#7a8090" },
  border: { strong: "#9aa1b0", subtle: "#e3e6ec" },
  bg: { subtle: "#eef0f4", page: "#ffffff" },
  font: { label: { fontSize: 11 } },
  dataviz: {
    categorical: ["#2f6fdb", "#e0782f", "#2a9d78", "#a54fc4", "#c9a227", "#d64570", "#4bb3c9", "#7d8a2e"],
    sequential: ["#e8f0fb", "#cbdcf6", "#a7c4ef", "#80a9e6", "#5a8cdb", "#3a6fcb", "#2655b0", "#1a3f8c", "#112b63"],
    other: "#7a8090",
    areaAlpha: "40",
    singleSeriesRest: "#b8bfcc",
  },
};
export function useGrokTheme() { return THEME; }

const toneColor = (t: Tone): { fg: string; bg: string } =>
  t === "danger" ? { fg: "#a11d2e", bg: "#fbe5e8" } :
  t === "warning" ? { fg: "#8a5a00", bg: "#fdf1d8" } :
  t === "success" ? { fg: "#1d6b48", bg: "#e1f4ea" } :
  { fg: THEME.text.secondary, bg: THEME.bg.subtle };

function Pill({ text, tone }: { text: string; tone?: Tone }) {
  const c = toneColor(tone);
  return <span className="pill" style={{ color: c.fg, background: c.bg }}>{text}</span>;
}

// Inline `code` rendering for Properties values
function md(s: ReactNode): ReactNode {
  if (typeof s !== "string" || s.indexOf("`") < 0) return s;
  return s.split("`").map((p, i) => (i % 2 ? <code key={i}>{p}</code> : <React.Fragment key={i}>{p}</React.Fragment>));
}

export function Page(props: { title: string; summary?: string; width?: string; children?: ReactNode }) {
  return (
    <div className="page">
      <header><h1>{props.title}</h1>{props.summary && <p className="summary">{props.summary}</p>}</header>
      {props.children}
    </div>
  );
}
export function Section(props: { heading?: string; id?: string; caption?: string; actions?: ReactNode; children?: ReactNode }) {
  return (
    <section id={props.id} className="section">
      {(props.heading || props.actions) && (
        <div className="sec-head"><h2>{props.heading}</h2>{props.actions && <div className="actions">{props.actions}</div>}</div>
      )}
      {props.caption && <p className="caption">{props.caption}</p>}
      <div className="sec-body">{props.children}</div>
    </section>
  );
}
export function Text(props: { children?: ReactNode }) { return <p className="text">{props.children}</p>; }
export function Grid(props: { columns?: number; plain?: boolean; children?: ReactNode }) {
  return <div className={"grid" + (props.plain ? " plain" : "")} style={{ ["--cols" as any]: props.columns || 2 }}>{props.children}</div>;
}
export function Metrics(props: { metrics: { value: string; label: string; detail?: string }[] }) {
  return (
    <div className="metrics">
      {props.metrics.map((m, i) => (
        <div key={i} className="metric"><div className="m-label">{m.label}</div><div className="m-value">{m.value}</div>{m.detail && <div className="m-detail">{m.detail}</div>}</div>
      ))}
    </div>
  );
}
export function Bars(props: { bars: { label: string; value: number; display?: string; meta?: string }[] }) {
  const max = Math.max(1, ...props.bars.map(b => b.value));
  if (props.bars.length === 0) return <p className="caption">Nothing matches the filters.</p>;
  return (
    <div className="bars">
      {props.bars.map((b, i) => (
        <div key={i} className="bar-row">
          <div className="bar-label" title={b.label}>{b.label}</div>
          <div className="bar-track"><div className="bar-fill" style={{ width: `${(b.value / max) * 100}%` }} /></div>
          <div className="bar-val">{b.display ?? b.value}{b.meta && <span className="bar-meta">{b.meta}</span>}</div>
        </div>
      ))}
    </div>
  );
}
type Cell = ReactNode | { text: string; tone?: Tone };
const isToneCell = (c: any): c is { text: string; tone?: Tone } => c && typeof c === "object" && !React.isValidElement(c) && "text" in c;
export function Table(props: { columns: string[]; rows: Cell[][] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead><tr>{props.columns.map((c, i) => <th key={i}>{c}</th>)}</tr></thead>
        <tbody>
          {props.rows.map((r, i) => (
            <tr key={i}>{r.map((c, j) => <td key={j}>{isToneCell(c) ? <Pill text={c.text} tone={c.tone} /> : (c as ReactNode)}</td>)}</tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export function Select(props: { label?: string; options: { value: string; label: string }[]; value: string; onChange: (v: string) => void }) {
  return (
    <label className="field"><span>{props.label}</span>
      <select value={props.value} onChange={e => props.onChange(e.target.value)}>
        {props.options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  );
}
export function Input(props: { label?: string; value: string; onChange: (v: string) => void; placeholder?: string }) {
  return (
    <label className="field"><span>{props.label}</span>
      <input type="search" value={props.value} placeholder={props.placeholder} onChange={e => props.onChange(e.target.value)} />
    </label>
  );
}
export function Toggle(props: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="toggle">
      <input type="checkbox" checked={props.value} onChange={e => props.onChange(e.target.checked)} />
      <span className="switch" /><span>{props.label}</span>
    </label>
  );
}
export function Button(props: { label: string; onClick: () => void }) {
  return <button className="btn" onClick={props.onClick}>{props.label}</button>;
}
export function Segmented(props: { options: { value: string; label: string }[]; value: string; onChange: (v: string) => void }) {
  return (
    <div className="seg" role="tablist">
      {props.options.map(o => (
        <button key={o.value} role="tab" aria-selected={o.value === props.value} className={o.value === props.value ? "on" : ""} onClick={() => props.onChange(o.value)}>{o.label}</button>
      ))}
    </div>
  );
}
export function Callout(props: { tone?: Tone; lead?: string; children?: ReactNode }) {
  const c = toneColor(props.tone);
  return <div className="callout" style={{ background: c.bg, borderColor: c.fg }}>{props.lead && <strong style={{ color: c.fg }}>{props.lead}</strong>}{props.children}</div>;
}
export function Rows(props: { rows: { title: string; detail?: string; status?: { label: string; tone?: Tone } }[] }) {
  return (
    <div className="rows">
      {props.rows.map((r, i) => (
        <div key={i} className="row-item">
          <div><div className="row-title">{r.title}</div>{r.detail && <div className="row-detail">{r.detail}</div>}</div>
          {r.status && <Pill text={r.status.label} tone={r.status.tone} />}
        </div>
      ))}
    </div>
  );
}
export function Properties(props: { items: { label: string; value: ReactNode }[] }) {
  return (
    <dl className="props">
      {props.items.map((it, i) => (<React.Fragment key={i}><dt>{it.label}</dt><dd>{md(it.value)}</dd></React.Fragment>))}
    </dl>
  );
}
export function Legend(props: { names: string[] }) {
  return (
    <div className="legend">
      {props.names.map((n, i) => (<span key={i}><i style={{ background: THEME.dataviz.categorical[i] }} />{n}</span>))}
    </div>
  );
}
export function TableOfContents(props: { items: { label: string; id: string }[] }) {
  return (
    <nav className="toc">
      {props.items.map(it => <a key={it.id} href={"#" + it.id}>{it.label}</a>)}
    </nav>
  );
}
