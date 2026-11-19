import urllib.parse, urllib.request, json
ids = ["Q46169","Q473972","Q1770297","Q3362943","Q19683138","Q1509934","Q150784","Q17007263","Q2231510",
       "Q40080","Q24529780","Q23442","Q8050526","Q55075651","Q832778","Q1485160","Q177380","Q1341387","Q1051355",
       "Q1162608","Q1329623","Q97495053","Q213441","Q207694","Q1007870","Q17431399","Q24354","Q41253","Q4989906",
       "Q179700","Q7075","Q44539","Q833913","Q1238457","Q162875","Q109607","Q755017","Q35112127","Q522124","Q186347"]
vals = " ".join(f"wd:{i}" for i in ids)
q = f"""SELECT ?c ?cLabel ?cDescription WHERE {{ VALUES ?c {{ {vals} }}
SERVICE wikibase:label {{ bd:serviceParam wikibase:language "tr,en". }} }}"""
url="https://query.wikidata.org/sparql?"+urllib.parse.urlencode({"query":q,"format":"json"})
req=urllib.request.Request(url, headers={"User-Agent":"TurkiyeKesif/1.0"})
with urllib.request.urlopen(req, timeout=60) as r: d=json.load(r)
for b in d["results"]["bindings"]:
    print(b["c"]["value"].split("/")[-1], "|", b.get("cLabel",{}).get("value"), "|", (b.get("cDescription",{}) or {}).get("value",""))
