#!/usr/bin/env python3
"""Etiket tabanlı ek kayıt toplayıcı.

Koordinatı olmayan ama gerçek/resmî adı bulunan yerleri de getirir
(milli park, tabiat parkı, tabiat anıtı, koruma alanı, müze, kaplıca, plaj…).
"""
import sys

from fetch import cached

Q = """
SELECT ?x ?xLabel ?coord ?p131 ?p131Label ?il ?ilLabel ?links WHERE {
  ?x wdt:P17 wd:Q43 ; rdfs:label ?lbl .
  FILTER(LANG(?lbl) = "tr")
  FILTER(CONTAINS(?lbl, "%s"))
  OPTIONAL { ?x wdt:P625 ?coord }
  OPTIONAL {
    ?x wdt:P131 ?p131 .
    OPTIONAL { ?p131 wdt:P131 ?il . }
  }
  OPTIONAL { ?x wikibase:sitelinks ?links }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}
LIMIT 3000
"""

KEYWORDS = {
    "mp": "Milli Parkı",
    "tp": "Tabiat Parkı",
    "ta": "Tabiat Anıtı",
    "kka": "Koruma Alanı",
    "muze": "Müzesi",
    "kaplica": "Kaplacası|Kaplıcası",
    "plaj": "Plajı",
    "yayla": "Yaylası",
    "selale": "Şelalesi",
    "kanyon": "Kanyonu",
}

if __name__ == "__main__":
    keys = sys.argv[1:] or list(KEYWORDS)
    for k in keys:
        kw = KEYWORDS[k]
        if "|" in kw:
            # iki yazım: ikisini ayrı ayrı çek, aynı önbelleğe yaz
            rows = []
            for part in kw.split("|"):
                rows += cached(f"x_{k}_{part[:4]}", Q % part)
            import json, pathlib
            f = pathlib.Path(__file__).parent / "raw" / f"x_{k}.json"
            f.write_text(json.dumps(rows, ensure_ascii=False))
            print(f"+ x_{k}: {len(rows)} satır")
            continue
        rows = cached(f"x_{k}", Q % kw)
        nocoord = sum(1 for r in rows if not r.get("coord"))
        print(f"  {k}: {len(rows)} kayıt, {nocoord} tanesi koordinatsız")
