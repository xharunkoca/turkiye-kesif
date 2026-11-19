from fetch import cached
Q = """
SELECT ?v ?vLabel ?coord ?ilLabel WHERE {
  ?v wdt:P31 wd:Q1529096 ; wdt:P625 ?coord .
  ?v wdt:P131 ?p . ?p wdt:P131 ?il . wd:Q43 wdt:P150 ?il .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}"""
cached("koy_geo", Q)
