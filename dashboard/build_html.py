#!/usr/bin/env python3
"""Bundle src/*.tsx + dashboard_data.json into one self-contained index.html.

Usage (from the dashboard/ folder):
    npm install          # once: react, react-dom, esbuild
    python build_html.py
"""
import os, subprocess, json, html
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
js = subprocess.check_output([
    "npx", "esbuild", "src/main.tsx", "--bundle", "--minify", "--format=iife",
    "--loader:.json=json", "--jsx=automatic", "--define:process.env.NODE_ENV=\"production\"", "--legal-comments=none",
]).decode()
css = open("src/styles.css").read()
snap = json.load(open("dashboard_data.json")).get("snapshot", "")
js = js.replace("</script", "<\\/script")
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
<div id="root"><p style="padding:24px">Loading dashboard&hellip; (JavaScript must be enabled)</p></div>
<script>{js}</script>
</body>
</html>
"""
open("index.html", "w").write(page)
print("index.html", os.path.getsize("index.html"), "bytes")
