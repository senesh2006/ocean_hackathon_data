#!/usr/bin/env python3
"""Bundle src/*.tsx + dashboard_data.json into one self-contained index.html.

Usage (from the dashboard/ folder):
    npm install          # once: react, react-dom, esbuild
    python build_html.py
"""
import os, re, subprocess, json, html
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
js = subprocess.check_output([
    "npx", "esbuild", "src/main.tsx", "--bundle", "--minify", "--format=iife",
    "--loader:.json=json", "--jsx=automatic", "--define:process.env.NODE_ENV=\"production\"", "--legal-comments=none",
]).decode()
css = open("src/styles.css").read()
snap = json.load(open("dashboard_data.json")).get("snapshot", "")
# No literal "<script" / "</script" may appear inside the bundle: an inline
# </script> would end the tag early, and htmlpreview.github.io rewrites every
# "<script" in the page with a regex (React has the string "<script><\/script>"),
# which broke the bundle there. \x3c is the same character inside JS strings.
js = re.sub(r"<(\\?/?)(script)", lambda m: "\\x3c" + m.group(1) + m.group(2), js, flags=re.I)
assert not re.search(r"<\\?/?script", js, re.I)
page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SplitWater data repo dashboard</title>
<meta name="description" content="Inventory, licences, coverage and map of every dataset in senesh2006/ocean_hackathon_data (snapshot {html.escape(snap)}).">
<style>{css}</style>
</head>
<body>
<div id="root"><p id="__loading" style="padding:24px">Loading dashboard&hellip; (JavaScript must be enabled)</p></div>
<script>
window.__dashErr = function (msg) {{
  var r = document.getElementById("root");
  if (r) r.innerHTML = '<div style="margin:24px;padding:16px;border:1px solid #d33;border-radius:8px;background:#fdecee;color:#8a1020;font:14px sans-serif">' +
    "<strong>The dashboard failed to load.</strong><br>" + String(msg).replace(/[&<>]/g, function (c) {{ return {{"&":"&amp;","<":"&lt;",">":"&gt;"}}[c]; }}) +
    "<br><br>Try downloading index.html and opening it in Chrome, Edge or Firefox.</div>";
}};
window.onerror = function (m, s, l, c, e) {{ window.__dashErr((e && e.message) || m); }};
</script>
<script>{js}</script>
<script>
setTimeout(function () {{
  var r = document.getElementById("root");
  if (r && r.querySelector("#__loading")) window.__dashErr("The script did not start (no error was reported). Your browser may be blocking JavaScript for this page.");
}}, 8000);
</script>
</body>
</html>
"""
open("index.html", "w").write(page)
print("index.html", os.path.getsize("index.html"), "bytes")
