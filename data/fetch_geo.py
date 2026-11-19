#!/usr/bin/env python3
"""İlçe bağı olmayan mekânlar için geniş çekim (koordinattan il/ilçe atanır)."""
import sys

from fetch import cached
from fetch_places import CLASSES

Q = """
SELECT ?x ?xLabel ?xDescription ?coord ?links WHERE {
  ?x wdt:P17 wd:Q43 ; wdt:P625 ?coord ; wdt:P31 ?cls .
  VALUES ?cls { %s }
  OPTIONAL { ?x wikibase:sitelinks ?links }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}"""

if __name__ == "__main__":
    for cat in sys.argv[1:] or list(CLASSES):
        vals = " ".join(f"wd:{c}" for c in CLASSES[cat])
        cached(f"geo_{cat}", Q % vals)
