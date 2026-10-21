"""Fetch GloBI prey interactions (eats, preysOn) for every species in the repo species list.
includeObservations=true so each row carries its study citation (study_title). Caches one JSON per queried name in raw/globi/. Polite: 3 workers, retry with backoff."""
import json, os, time, urllib.parse, requests, pandas as pd
from concurrent.futures import ThreadPoolExecutor
SL = "/workspace/ocean_hackathon_data/fish-data/species_list.csv"
OUT = "/workspace/species_niche/raw/globi_obs"
FIELDS = "source_taxon_name,interaction_type,target_taxon_name,target_taxon_path,target_taxon_path_ranks,target_specimen_life_stage,source_specimen_life_stage,latitude,longitude,study_title"
sl = pd.read_csv(SL)
names = set(sl.scientific_name.dropna()) | set(sl.fishbase_name.dropna())
def fn(n): return os.path.join(OUT, n.replace(" ", "_").replace("/", "_") + ".json")
S = requests.Session(); S.headers["User-Agent"] = "species-niche-builder (research, contact via github senesh2006)"
def get(n):
    p = fn(n)
    if os.path.exists(p): return
    rows, off = [], 0
    while True:
        q = {"sourceTaxon": n, "interactionType": ["eats", "preysOn"], "limit": 4096, "offset": off, "fields": FIELDS, "exactNameMatchOnly": "true", "includeObservations": "true"}
        for a in range(5):
            try:
                r = S.get("https://api.globalbioticinteractions.org/interaction", params=q, timeout=120)
                if r.status_code == 200: break
            except Exception as e: pass
            time.sleep(2 ** a * 2)
        else:
            print("FAIL", n); return
        d = r.json(); rows += d["data"]
        if len(d["data"]) < 4096: break
        off += 4096
    json.dump({"columns": d["columns"], "data": rows, "query_name": n}, open(p, "w"))
    time.sleep(0.3)
with ThreadPoolExecutor(3) as ex: list(ex.map(get, sorted(names)))
print("done", len(names))
