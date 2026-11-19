import urllib.parse, urllib.request, json, time
def run(q, label):
    url="https://query.wikidata.org/sparql?"+urllib.parse.urlencode({"query":q,"format":"json"})
    req=urllib.request.Request(url, headers={"User-Agent":"TurkiyeKesif/1.0"})
    t=time.time()
    try:
        with urllib.request.urlopen(req, timeout=200) as r: d=json.load(r)
        rows=[{k:v.get("value") for k,v in b.items()} for b in d["results"]["bindings"]]
        print(label, len(rows), f"{time.time()-t:.0f}s", rows[:2])
    except Exception as e:
        print(label, "FAIL", e)

run("""
SELECT ?v ?vLabel ?d ?dLabel WHERE {
  wd:Q43 wdt:P150 ?il . ?il wdt:P150 ?d .
  ?v wdt:P31 wd:Q1529096 ; wdt:P131 ?d .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
} LIMIT 3""", "koy-district-sample")
