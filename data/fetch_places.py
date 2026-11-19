#!/usr/bin/env python3
"""Kategori bazlı gerçek mekân çekimi (Wikidata, koordinatlı).

Her kategori için iki desen denenir:
  1) mekân -> ilçe -> il
  2) mekân -> il (doğrudan)
"""
import json
import pathlib
import sys

from fetch import cached

TEMPLATE = """
SELECT ?x ?xLabel ?xDescription ?coord ?il ?ilLabel ?parent ?parentLabel ?links WHERE {
  %s
  OPTIONAL { ?x wikibase:sitelinks ?links }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}"""

DISTRICT_PATTERN = """
  wd:Q43 wdt:P150 ?il .
  ?il wdt:P150 ?parent .
  ?x wdt:P131 ?parent ; wdt:P625 ?coord ; wdt:P31 ?cls .
  VALUES ?cls { %s }
"""

PROVINCE_PATTERN = """
  wd:Q43 wdt:P150 ?il .
  ?x wdt:P131 ?il ; wdt:P625 ?coord ; wdt:P31 ?cls .
  VALUES ?cls { %s }
  BIND(?il AS ?parent)
"""

CLASSES = {
    "antik": ["Q15661340", "Q839954", "Q755017", "Q109607", "Q162875", "Q34023"],
    "muze": ["Q33506", "Q207694", "Q17431399", "Q1007870"],
    "doga": ["Q46169", "Q473972", "Q19683138"],
    "tarih": ["Q35112127", "Q23413", "Q57831", "Q12280", "Q522124", "Q186347",
              "Q28077", "Q57346", "Q838858", "Q132834"],
    "gol": ["Q23397", "Q12323"],
    "selale": ["Q34038"],
    "magara": ["Q35509"],
    "vadi": ["Q150784", "Q2231510"],
    "plaj": ["Q40080", "Q23442"],
    "yayla": ["Q8050526", "Q832778"],
    "dini": ["Q32815", "Q16970", "Q44613", "Q838159", "Q44539", "Q833913", "Q1238457"],
    "kultur": ["Q7075", "Q24354", "Q41253", "Q4989906", "Q179700", "Q1329623", "Q97495053"],
    "termal": ["Q177380", "Q1341387"],
}


def query_for(classes, pattern):
    vals = " ".join(f"wd:{c}" for c in classes)
    return TEMPLATE % (pattern % vals)


if __name__ == "__main__":
    cats = sys.argv[1:] or list(CLASSES)
    for cat in cats:
        classes = CLASSES[cat]
        cached(f"places_{cat}_d", query_for(classes, DISTRICT_PATTERN))
        cached(f"places_{cat}_p", query_for(classes, PROVINCE_PATTERN))
