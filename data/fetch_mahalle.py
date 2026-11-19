import json
from fetch import cached, RAW

provs = json.loads((RAW / "provinces.json").read_text())
META = ["Adana","Ankara","Antalya","Aydın","Balıkesir","Bursa","Denizli","Diyarbakır","Erzurum",
        "Eskişehir","Gaziantep","Hatay","İstanbul","İzmir","Kahramanmaraş","Kayseri","Kocaeli",
        "Konya","Malatya","Manisa","Mardin","Mersin","Muğla","Ordu","Sakarya","Samsun","Şanlıurfa",
        "Tekirdağ","Trabzon","Van"]
qids = [p["il"].rsplit("/",1)[-1] for p in provs if p.get("ilLabel") in META]
print("büyükşehir:", len(qids))
vals = " ".join(f"wd:{q}" for q in qids)
Q = f"""
SELECT ?v ?vLabel ?coord ?ilLabel WHERE {{
  VALUES ?il {{ {vals} }}
  ?v wdt:P31 wd:Q17051044 ; wdt:P625 ?coord ; wdt:P131 ?p .
  ?p wdt:P131 ?il .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "tr,en". }}
}}"""
cached("mahalle", Q)
