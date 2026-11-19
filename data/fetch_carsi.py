from fetch import cached
Q = """
SELECT ?x ?xLabel ?coord ?clsLabel ?ilLabel ?links WHERE {
  ?x wdt:P17 wd:Q43 ; wdt:P625 ?coord ; rdfs:label ?lbl .
  FILTER(LANG(?lbl) = "tr")
  FILTER(CONTAINS(?lbl, "Çarşı") || CONTAINS(?lbl, "çarşı") || CONTAINS(?lbl, "Bedesten")
      || CONTAINS(?lbl, "Arasta") || CONTAINS(?lbl, "Hanı") || CONTAINS(?lbl, "Pazarı")
      || CONTAINS(?lbl, "Pazar"))
  OPTIONAL { ?x wdt:P31 ?cls }
  OPTIONAL { ?x wdt:P131 ?p . ?p wdt:P131 ?il0 . ?il0 wdt:P131 ?il1 . }
  OPTIONAL { ?x wikibase:sitelinks ?links }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}"""
cached("carsi_geo", Q)
