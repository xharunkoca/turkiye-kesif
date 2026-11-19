from fetch import cached
Q = """
SELECT ?v ?vLabel ?d ?dLabel ?il ?ilLabel WHERE {
  wd:Q43 wdt:P150 ?il .
  ?il wdt:P150 ?d .
  ?v wdt:P31 wd:Q1529096 ; wdt:P131 ?d .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "tr,en". }
}"""
cached("koy", Q)
