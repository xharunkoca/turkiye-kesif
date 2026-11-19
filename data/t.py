import urllib.parse, urllib.request, json
q = """
SELECT ?x ?xLabel ?coord ?ilLabel ?dLabel WHERE {
  wd:Q43 wdt:P150 ?il .
  ?il wdt:P150 ?d .
  ?x wdt:P131 ?d ; wdt:P625 ?coord ; wdt:P31 wd:Q15661340 .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
} LIMIT 5"""
url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"})
req = urllib.request.Request(url, headers={"User-Agent":"TurkiyeKesif/1.0"})
try:
    with urllib.request.urlopen(req, timeout=120) as r:
        d=json.load(r); print(len(d["results"]["bindings"]), d["results"]["bindings"][:2])
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read()[:600])
