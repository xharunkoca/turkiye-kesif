#!/usr/bin/env python3
"""Kategori/mekân verisini sınıf etiketiyle yeniden çeker (tip bilgisi için)."""
import sys

from fetch import cached
from fetch_places import CLASSES

TPL = """
SELECT ?x ?xLabel ?xDescription ?cls ?clsLabel ?coord ?il ?ilLabel ?parent ?parentLabel ?links WHERE {
  %s
  OPTIONAL { ?x wikibase:sitelinks ?links }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}"""

DISTRICT = """
  wd:Q43 wdt:P150 ?il .
  ?il wdt:P150 ?parent .
  ?x wdt:P131 ?parent ; wdt:P625 ?coord ; wdt:P31 ?cls .
  VALUES ?cls { %s }
"""

PROVINCE = """
  wd:Q43 wdt:P150 ?il .
  ?x wdt:P131 ?il ; wdt:P625 ?coord ; wdt:P31 ?cls .
  VALUES ?cls { %s }
  BIND(?il AS ?parent)
"""

GEO = """
SELECT ?x ?xLabel ?xDescription ?cls ?clsLabel ?coord ?links WHERE {
  ?x wdt:P17 wd:Q43 ; wdt:P625 ?coord ; wdt:P31 ?cls .
  VALUES ?cls { %s }
  OPTIONAL { ?x wikibase:sitelinks ?links }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}"""

if __name__ == "__main__":
    for cat in sys.argv[1:] or list(CLASSES):
        vals = " ".join(f"wd:{c}" for c in CLASSES[cat])
        cached(f"v2_{cat}_d", TPL % (DISTRICT % vals))
        cached(f"v2_{cat}_p", TPL % (PROVINCE % vals))
        cached(f"v2_{cat}_g", GEO % vals)
