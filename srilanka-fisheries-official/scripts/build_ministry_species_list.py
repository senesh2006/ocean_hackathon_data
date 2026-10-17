"""Build ministry_fish_species_list.csv/.parquet from the MFAR PDF (transcribed + checked visually), validate names with WoRMS."""
import re, json, time, datetime, requests, pandas as pd
from pathlib import Path
OUT = Path("/workspace/srilanka-fisheries-official")

# (page, group, english_as_published, scientific_as_published, sinhala_as_published, query_name, note)
# query_name = name sent to WoRMS (typo-fixed); None => use published as-is
R = [
(1,"Seer","Spanish mackerel","Scomberomorus commersoni","Thora","Scomberomorus commerson","Spelling: epithet is 'commerson'."),
(1,"Seer","Wahoo","Acanthocybium commersoni","Sawara","Acanthocybium solandri","Not a typo but an error: wahoo is Acanthocybium solandri; 'commersoni' copied from row above. Matched on A. solandri."),
(1,"Paraw","Jack, Trevallies","Carangoides gymnostethus","Vattiya",None,"English name is a merged cell spanning 4 rows."),
(1,"Paraw","Jack, Trevallies","Carangoides fulvoguttatus","Thumba parawa",None,"English name is a merged cell spanning 4 rows."),
(1,"Paraw","Jack, Trevallies","Caranx ignobilis","Atanagul Parawa",None,"English name is a merged cell spanning 4 rows."),
(1,"Paraw","Jack, Trevallies","Caranx hebiri","Guru parawa","Caranx heberi","Typo: hebiri -> heberi."),
(1,"Balaya","Skipjack tuna","Katsuwonus pelamis","Balaya",None,""),
(1,"Kelawalla","yellowfin tuna","Thunnus albacares","Kelawalla",None,""),
(1,"Other Blood fish","Sail fish","Istiophorus platypterus","Thalapath",None,""),
(1,"Other Blood fish","Marlins","Makariya indika","Kalu koppara","Makaira indica","Typo: Makariya indika -> Makaira indica (black marlin; now Istiompax indica). English 'Marlins' is a merged cell spanning 3 rows."),
(1,"Other Blood fish","Marlins","Makariya mazara","Nil koppara","Makaira mazara","Typo: Makariya -> Makaira (Indo-Pacific blue marlin). English merged cell."),
(1,"Other Blood fish","Marlins","Tetrapturus audax","Iri koppara",None,"Striped marlin; old genus. English merged cell."),
(1,"Other Blood fish","Sword fish","Xiphias gladius","Sappara",None,""),
(1,"Other Blood fish","Big eye tuna","Thunnus abesus","Esgedi kelawalla/Kenda","Thunnus obesus","Typo: abesus -> obesus."),
(1,"Other Blood fish","Bullet tuna","Auxis rochei","Ragodu/kombaya",None,""),
(1,"Other Blood fish","Frigate tuna","Auxis thazard","Alagoduwa",None,""),
(1,"Other Blood fish","Kawakawa","Euthynnus affinis","Attawalla",None,""),
(1,"Sharks","Mackerel shark","Isurus sp.","Mee mora","Isurus","Genus-level."),
(1,"Sharks","Thresher shark","Alopias sp.","Kasa mora","Alopias","Genus-level."),
(1,"Sharks","Requiem sharks-silky shark","Carcharhinus Falciformis","Honda mora/Bala maora","Carcharhinus falciformis","Capitalised epithet fixed. Sinhala 'Bala maora' probably 'Bala mora' (left as published)."),
(1,"Sharks","Ocean white strip shark","Carcharhinus Longimanus","Polkola mora","Carcharhinus longimanus","Capitalised epithet fixed. English = oceanic whitetip shark."),
(1,"Sharks","Blue shark","prionace gluaca","Seeni mora/Hudja Mora","Prionace glauca","Typo: prionace gluaca -> Prionace glauca."),
(1,"Sharks","Hammerhead shark","Sphyrna sp.","Udalu mora","Sphyrna","Genus-level."),
(1,"Skate","Batoid Fisher- shovelnose rays","Rhinobatos sp.","Baloliya","Rhinobatos","Genus-level. English likely 'Batoid fishes - shovelnose rays'."),
(1,"Skate","String rays","Dasyatis sp.","Welli maduwa","Dasyatis","Genus-level. English = stingrays."),
(1,"Skate","Spotted eagle rays","Aetobatus narinari","Vavoi maduwa",None,"Indo-Pacific population now often treated as Aetobatus ocellatus."),
(1,"Skate","Javanees cownose rays","Rhinoptera javanica","valuvadi cownose ray",None,"English typo 'Javanees' (Javanese). Sinhala column holds a mixed Tamil/English name."),
(1,"Skate","Numbfishers","Narcine sp.","Electric ray","Narcine","Genus-level. Sinhala column holds an English name, no Sinhala given."),
(1,"Skate","Manta and devil rays","Mobula sp.","Ali maduwa and Anga maduwa","Mobula","Genus-level."),
(1,"Rock Fish/Galmalu","Spangled emperor","Lethrinus nebulosus","Meewetiya/Atissa",None,""),
(1,"Rock Fish/Galmalu","Longface emperor","Lethrinus olivaceus","Uru hota",None,""),
(1,"Rock Fish/Galmalu","Sharptooth jobfish","Pristipomoides typus","Kalamee",None,""),
(1,"Rock Fish/Galmalu","Blubberlip snapper","Lutjanus rivulatus","Badawa",None,""),
(1,"Rock Fish/Galmalu","Mangrove red snapper","Lutjanus argentimaculatus","Thabalaya",None,""),
(1,"Rock Fish/Galmalu","Blackspot snapper","Lutjanus fulviflamma","Ranna",None,""),
(1,"Rock Fish/Galmalu","Malabar grouper","Epinephelus malabaricus","Gas bola/Gal kossa",None,""),
(2,"Rock Fish/Galmalu","Wavylined grouper","Epinephelus undulosus","Lawaya",None,""),
(2,"Rock Fish/Galmalu","Coral hind","Cephalopholis miniata","Thabuwa",None,""),
(2,"Rock Fish/Galmalu","Sri Lanka sweetlips","Plectorhinchus ceylonensis","Boraluwa",None,""),
(2,"Rock Fish/Galmalu","Threadfin breams","Nemipterus sp.","Suddaha","Nemipterus","Genus-level."),
(2,"Rock Fish/Galmalu","Parrotfishes","Scarus sp.","Girawa","Scarus","Genus-level."),
(2,"Rock Fish/Galmalu","Rabbitfsh","Siganus so.","Orawa","Siganus","Genus-level; typo 'so.' -> 'sp.'; English typo 'Rabbitfsh'."),
(2,"Rock Fish/Galmalu","Barracudas","Sphyraena sp.","Jeelawa","Sphyraena","Genus-level."),
(2,"","Mullets","Liza sp.","Godaya","Liza","Commercial group cell is blank in the PDF (own empty cell between Rock Fish and Shore Seine). Genus-level."),
(2,"Shore Seine","Trenched sardinella","Amblygaster sirm","Hurulla",None,""),
(2,"Shore Seine","Bleeker's smooth belly","Amblygaster clupeoides","Gal Hurulla",None,"Same scientific name as next row."),
(2,"Shore Seine","Smoothbelly Sardinells","Amblygaster clupeoides","Keeramin",None,"Duplicate of previous row's name; 'Smoothbelly sardinella' is usually Amblygaster leiogaster, so this row may be a mistake. Matched as published."),
(2,"Shore Seine","Rainbow sardine","Dussumieria acuta","Thondaya",None,""),
(2,"Shore Seine","White sardine","Escualosa thoracata","Wella sudaya",None,""),
(2,"Shore Seine","Shad","Nematalosa nasus","Koiya",None,"PDF shows a double space in 'Nematalosa  nasus' (normalised here)."),
(2,"Shore Seine","Goldstripe sardinella","Sardinella gibbosa","Kalawenna/Salaya",None,""),
(2,"Shore Seine","White sardinella","Sardinella albella","Sudaya",None,""),
(2,"Shore Seine","Bigeye scade","Selar crumenophtthalamus","Bolla","Selar crumenophthalmus","Typo: crumenophtthalamus -> crumenophthalmus."),
(2,"Shore Seine","Indian mackerel","Rastrelliger kanagurta","Kumbala",None,""),
(2,"Shore Seine","Anchovy","Stolephorus sp.","Halmessa","Stolephorus","Genus-level."),
(2,"Shore Seine","Ribbon fish","Lepturacanthus savalaa","Savalaya","Lepturacanthus savala","Typo: savalaa -> savala."),
(2,"Shore Seine","Gar fisher","Belonidae","Habarali","Belonidae","Family-level. English = garfishes/needlefishes."),
(2,"Shore Seine","Thryssa","Thryssa sp.","Lagga","Thryssa","Genus-level."),
(2,"Shore Seine","Silverbiddies","Gerres sp.","Thirali","Gerres","Genus-level."),
(2,"Shore Seine","Pony fish","Leiognathus sp.","Karalla","Leiognathus","Genus-level."),
(2,"Shore Seine","Ilishas","Ilish sp.","Puvali","Ilisha","Typo: 'Ilish' -> genus Ilisha (could also mean hilsa, Tenualosa ilisha). Genus-level."),
(2,"Shore Seine","Half beaks","Hemiramphus sp.","Moralla","Hemiramphus","Genus-level."),
(2,"Shore Seine","Flying fish","Cheilopogon sp.","Piyamessa","Cheilopogon","Genus-level."),
(2,"Prawns","Giant river prawn","Macrobrachium rosenbergii","Karadu issa",None,"Freshwater/brackish prawn in a 'marine' list."),
(2,"Prawns","Indian white shrimp","Penaeus indicus","Kiri issa",None,""),
(2,"Prawns","Giant tiger prawn","Penaeus monodon","Karawandu issa",None,""),
(2,"Prawns","Green tiger prawns","Penaeus semesulsctus","kurutu issa","Penaeus semisulcatus","Typo: semesulsctus -> semisulcatus."),
(2,"Lobster","Scalloped spiny lobster","Panulirus homorus","Weli issa","Panulirus homarus","Typo: homorus -> homarus."),
(2,"Lobster","Ornate spiny lobster","Panulirus ornatus","Devi issa",None,""),
(2,"Lobster","Pronghorn spiny lobster","Panulirus penicillatus","Gal issa",None,""),
(2,"Lobster","Painted spiny lobster","Panulirus versicolor","Bathik issa/Raga issa",None,""),
(2,"Lobster","Slipper lobster","Panulirus polyphagus","Mada issa",None,"English cell 'Slipper lobster' is a merged cell covering this row and Scyllarus; P. polyphagus is actually the mud spiny lobster (Sinhala 'Mada issa'), not a slipper lobster."),
(2,"Lobster","Slipper lobster","Scyllarus sp.","Sapathuwa","Scyllarus","Genus-level."),
(2,"Other","Squids","Loligo singhalensis","Bothal della",None,"Old genus; now Uroteuthis. English merged cell."),
(2,"Other","Squids","Loligo duvauceli","Ahin della","Loligo duvaucelii","Spelling: duvauceli -> duvaucelii; old genus (now Uroteuthis). English merged cell."),
(2,"Other","Cuttle fish","Sepia pharaonis","Gebi della/Pothu della",None,"English 'Cuttle fish' is a merged cell covering this and next row."),
(2,"Other","Cuttle fish","Sepia aculeata","Pothu della",None,"English merged cell."),
(2,"Other","Octopus","Octopus sp.","Buwalla","Octopus","Genus-level."),
(3,"Other","Sea Cucumber (Beach de mer)","Holothuria fucogilva","Ham attaya/White tearfish","Holothuria fuscogilva","Typo: fucogilva -> fuscogilva. 'Beach de mer' = beche-de-mer; 'tearfish' = teatfish."),
(3,"Other","Sea Cucumber (Beach de mer)","Holothuria scabra","Welli attaya/Sand fish",None,""),
(3,"Other","Sea Cucumber (Beach de mer)","Holothuria nobilis","Polon attaya/Black teatfish",None,""),
(3,"Other","Sea Cucumber (Beach de mer)","Bohadschia marmorata","Nul attaya/Chalky fish",None,""),
(3,"Other","Sea Cucumber (Beach de mer)","Actinopygs miliaris","Kalu attaya /Black fish","Actinopyga miliaris","Typo: Actinopygs -> Actinopyga."),
(3,"Other","Sea Cucumber (Beach de mer)","Holothuria edulis","Rathu attaya/Pinkfish",None,""),
(3,"Other","Sea Cucumber (Beach de mer)","Holothuria atra","Nari attaya/Lolyfish",None,"'Lolyfish' = lollyfish."),
(3,"Other","Sea Cucumber (Beach de mer)","Theienota ananas","Annasi attaya/Prickly redfish","Thelenota ananas","Typo: Theienota -> Thelenota."),
(3,"Other","Sea Cucumber (Beach de mer)","Thelenota anax","Punattaya/Amberfish",None,"Text layer reads 'Thelenota' (image looks like 'Thelenota'/'Theienota'); correct genus either way."),
(3,"Other","Sea Cucumber (Beach de mer)","Srichopus chloronotus","Dabalaya/Green fish","Stichopus chloronotus","Typo: Srichopus -> Stichopus."),
(3,"Other","Crabs","Portunus pelagicus","Seenakali/Blue swimming crab",None,""),
(3,"Other","Crabs","Scylla serrata","Kalapu kakuluwa/mangrove crab",None,""),
(3,"Other","Crabs","Portunus spp.","Mudu kakuluwa","Portunus","Genus-level."),
]

ENGLISHISH = {"White tearfish","Sand fish","Black teatfish","Chalky fish","Black fish","Pinkfish","Lolyfish",
  "Prickly redfish","Amberfish","Green fish","Blue swimming crab","mangrove crab"}

def split_sinhala(s):
    parts = [p.strip() for p in s.replace(" and ", "/").split("/") if p.strip()]
    si = [p for p in parts if p not in ENGLISHISH]
    en = [p for p in parts if p in ENGLISHISH]
    if s == "Electric ray": si, en = [], ["Electric ray"]
    return "; ".join(si), "; ".join(en)

def worms_match(names):
    out = {}
    for i in range(0, len(names), 40):
        chunk = names[i:i+40]
        r = requests.get("https://www.marinespecies.org/rest/AphiaRecordsByMatchNames",
                         params=[("scientificnames[]", n) for n in chunk] + [("marine_only", "false")], timeout=60)
        r.raise_for_status()
        for n, recs in zip(chunk, r.json()):
            out[n] = recs or []
        time.sleep(0.5)
    return out

rows = []
for i, (pg, grp, en, sci, si, q, note) in enumerate(R, 1):
    rows.append(dict(row_id=i, pdf_page=pg, commercial_group=grp, english_name=en,
                     scientific_name_as_published=sci, sinhala_name_as_published=si, query_name=q or sci, notes=note))
names = sorted({r["query_name"] for r in rows})
M = worms_match(names)
json.dump(M, open(OUT/"raw/worms_match_responses.json","w"), indent=1)

for r in rows:
    r["sinhala_name_romanised"], r["english_alt_name_in_sinhala_col"] = split_sinhala(r["sinhala_name_as_published"])
    recs = M.get(r["query_name"], [])
    if not recs:
        r.update(match_status="no_match", aphia_id=None, scientific_name_accepted=None, accepted_aphia_id=None,
                 correction_type=None, rank=None, taxonomic_status=None, family=None, class_=None, worms_match_type=None)
        continue
    rec = next((x for x in recs if x.get("status") == "accepted"), recs[0])
    exact = rec["match_type"].startswith("exact")
    pub=" ".join(r["scientific_name_as_published"].split()); q=r["query_name"]
    if q == pub: ct="none"
    elif re.sub(r"\s+(sp|spp|so)\.$","",pub) == q and not pub.endswith("so."): ct="sp_suffix_removed"
    elif pub.lower() == q.lower(): ct="capitalisation"
    elif "misidentif" in r["notes"].lower() or "Not a typo" in r["notes"]: ct="wrong_name_replaced"
    else: ct="spelling_fixed"
    r["correction_type"]=ct
    st = ("exact" if ct in ("none","sp_suffix_removed") else "exact_after_correction") if exact else "fuzzy"
    if len(recs) > 1: st += "_ambiguous"
    r.update(match_status=st, aphia_id=rec["AphiaID"], scientific_name_accepted=rec.get("valid_name"),
             accepted_aphia_id=rec.get("valid_AphiaID"), rank=rec.get("rank"), taxonomic_status=rec.get("status"),
             family=rec.get("family"), class_=rec.get("class"), worms_match_type=rec["match_type"])
    if rec.get("valid_name") and rec["valid_name"] != rec["scientificname"]:
        r["notes"] = (r["notes"] + " " if r["notes"] else "") + f"WoRMS: '{rec['scientificname']}' is {rec.get('status')}; accepted name {rec['valid_name']}."

df = pd.DataFrame(rows).rename(columns={"class_":"class"})
df["worms_query_name"] = df.pop("query_name")
df["is_fish"] = df["class"].isin(["Teleostei","Actinopteri","Elasmobranchii","Chondrichthyes"])
df["retrieved_utc"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
cols = ["row_id","pdf_page","commercial_group","english_name","scientific_name_as_published","sinhala_name_as_published",
        "sinhala_name_romanised","english_alt_name_in_sinhala_col","worms_query_name","correction_type","scientific_name_accepted","aphia_id",
        "accepted_aphia_id","rank","taxonomic_status","family","class","is_fish","match_status","worms_match_type","notes","retrieved_utc"]
df = df[cols]
for c in ["aphia_id","accepted_aphia_id"]: df[c] = df[c].astype("Int64")
df.to_csv(OUT/"ministry_fish_species_list.csv", index=False, encoding="utf-8-sig")
df.to_parquet(OUT/"ministry_fish_species_list.parquet", index=False)
print(df.match_status.value_counts()); print(df[["scientific_name_as_published","worms_query_name","correction_type","scientific_name_accepted","aphia_id","match_status","rank"]].to_string())
