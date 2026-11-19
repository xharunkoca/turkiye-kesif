from fetch import cached
Q = """
SELECT ?il ?ilLabel ?d ?dLabel ?coord WHERE {
  ?d wdt:P31/wdt:P279* wd:Q1147395 .
  ?d wdt:P131 ?il .
  wd:Q43 wdt:P150 ?il .
  OPTIONAL { ?d wdt:P625 ?coord }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}"""
cached("districts2", Q)
