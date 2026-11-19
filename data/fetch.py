#!/usr/bin/env python3
"""Wikidata'dan gerçek/doğrulanabilir coğrafi veriyi çeker (önbellekli).

Kullanım:  python3 fetch.py provinces|districts|settlements|places|all
"""
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

RAW = pathlib.Path(__file__).parent / "raw"
RAW.mkdir(parents=True, exist_ok=True)
UA = {"User-Agent": "TurkiyeKesif/1.0 (tourism demo; educational)"}
ENDPOINT = "https://query.wikidata.org/sparql"


def sparql(q, retries=4):
    url = ENDPOINT + "?" + urllib.parse.urlencode({"query": q, "format": "json"})
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.loads(r.read().decode("utf-8", "replace"), strict=False)
            return [{k: v.get("value") for k, v in b.items()} for b in d["results"]["bindings"]]
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"  ! retry {i + 1}: {type(e).__name__} {e}", file=sys.stderr)
            time.sleep(5 * (i + 1))
    raise RuntimeError(f"SPARQL failed: {last}")


def cached(name, query):
    f = RAW / f"{name}.json"
    if f.exists():
        print(f"= {name}: önbellekten ({f.stat().st_size // 1024} KB)")
        return json.loads(f.read_text())
    t0 = time.time()
    rows = sparql(query)
    f.write_text(json.dumps(rows, ensure_ascii=False))
    print(f"+ {name}: {len(rows)} satır ({time.time() - t0:.0f}s)")
    return rows


PROVINCES = """
SELECT ?il ?ilLabel ?plate ?coord WHERE {
  wd:Q43 wdt:P150 ?il .
  OPTIONAL { ?il wdt:P395 ?plate }
  OPTIONAL { ?il wdt:P625 ?coord }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}"""

DISTRICTS = """
SELECT ?il ?d ?dLabel ?coord WHERE {
  wd:Q43 wdt:P150 ?il .
  ?il wdt:P150 ?d .
  OPTIONAL { ?d wdt:P625 ?coord }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}"""

SETTLEMENTS = """
SELECT ?d ?v ?vLabel ?vType ?vTypeLabel ?coord WHERE {
  wd:Q43 wdt:P150 ?il .
  ?il wdt:P150 ?d .
  ?d wdt:P150 ?v .
  ?v wdt:P31 ?vType .
  VALUES ?vType { wd:Q1529096 wd:Q17051044 wd:Q3957 wd:Q532 }
  OPTIONAL { ?v wdt:P625 ?coord }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}"""

# 15 kategoriye karşılık gelen Wikidata sınıfları
PLACES = """
SELECT ?x ?xLabel ?xDescription ?cls ?clsLabel ?coord ?il ?ilLabel ?d ?dLabel ?links WHERE {
  wd:Q43 wdt:P150 ?il .
  ?il wdt:P150 ?d .
  ?x wdt:P131 ?d ;
     wdt:P625 ?coord ;
     wdt:P31 ?cls .
  VALUES ?cls { %s }
  OPTIONAL { ?x wikibase:sitelinks ?links }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}"""

CLASSES = {
    # 1. Antik Kentler
    "antik": ["Q15661340", "Q839954", "Q755017", "Q109607", "Q34023", "Q162875"],
    # 2. Müzeler
    "muze": ["Q33506", "Q207694", "Q1007870", "Q17431399"],
    # 3. Doğa & Milli Parklar
    "doga": ["Q46169", "Q473972", "Q1770297", "Q3362943", "Q19683138", "Q1509934"],
    # 4. Tarihi Yapılar
    "tarih": ["Q35112127", "Q23413", "Q57831", "Q12280", "Q522124", "Q186347",
              "Q28077", "Q57346", "Q838858", "Q132834", "Q811979"],
    # 5. Göller
    "gol": ["Q23397", "Q12323"],
    # 6. Şelaleler
    "selale": ["Q34038"],
    # 7. Mağaralar
    "magara": ["Q35509", "Q35509"],
    # 8. Vadiler & Kanyonlar
    "vadi": ["Q150784", "Q17007263", "Q2231510"],
    # 9. Plajlar & Kıyılar
    "plaj": ["Q40080", "Q24529780", "Q23442"],
    # 11. Yaylalar & Kamp
    "yayla": ["Q8050526", "Q55075651", "Q832778", "Q1485160"],
    # 12. Dini Yapılar
    "dini": ["Q32815", "Q16970", "Q44613", "Q838159", "Q44539", "Q833913", "Q1238457"],
    # 13. Kültür & Sanat
    "kultur": ["Q7075", "Q24354", "Q41253", "Q4989906", "Q179700"],
    # 14. Kaplıcalar & Termal
    "termal": ["Q177380", "Q1341387", "Q1051355"],
    # 15. Çarşılar & Pazarlar
    "carsi": ["Q1162608", "Q1329623", "Q97495053", "Q213441"],
}


def places_query():
    parts = []
    for cat, classes in CLASSES.items():
        vals = " ".join(f"wd:{c}" for c in dict.fromkeys(classes))
        parts.append(f'{{ VALUES ?cls {{ {vals} }} }}')
    return PLACES % " ".join(parts)


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    if which in ("all", "provinces"):
        cached("provinces", PROVINCES)
    if which in ("all", "districts"):
        cached("districts", DISTRICTS)
    if which in ("all", "places"):
        cached("places", places_query())
    if which in ("all", "settlements"):
        cached("settlements", SETTLEMENTS)
