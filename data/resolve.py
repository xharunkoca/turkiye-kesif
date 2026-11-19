#!/usr/bin/env python3
"""Curated listelerdeki yer adlarını Wikidata'da doğrular, koordinat/QID çeker."""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

import curated

OUT = pathlib.Path(__file__).parent / "raw" / "curated_resolved.json"
UA = {"User-Agent": "TurkiyeKesif/1.0 (tourism demo)"}

LISTS = {
    "doga": curated.DOGA,
    "selale": curated.SELALE,
    "magara": curated.MAGARA,
    "vadi": curated.VADI,
    "plaj": curated.PLAJ,
    "termal": curated.TERMAL,
    "carsi": curated.CARSI,
}


def api_search(name):
    url = "https://www.wikidata.org/w/api.php?" + urllib.parse.urlencode({
        "action": "wbsearchentities", "search": name, "language": "tr",
        "uselang": "tr", "limit": 5, "format": "json",
    })
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        d = json.load(r)
    return [x["id"] for x in d.get("search", [])]


def coords_for(ids):
    if not ids:
        return {}
    vals = " ".join(f"wd:{i}" for i in ids)
    q = f"""SELECT ?x ?xLabel ?coord WHERE {{
      VALUES ?x {{ {vals} }}
      OPTIONAL {{ ?x wdt:P625 ?coord }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "tr,en". }}
    }}"""
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"})
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.load(r)
    out = {}
    for b in d["results"]["bindings"]:
        x = b["x"]["value"].rsplit("/", 1)[-1]
        c = b.get("coord", {}).get("value")
        m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", c or "")
        if m:
            out[x] = (float(m.group(2)), float(m.group(1)), b.get("xLabel", {}).get("value"))
    return out


if __name__ == "__main__":
    resolved = []
    unresolved = []
    for cat, items in LISTS.items():
        print(f"=== {cat}: {len(items)}")
        cache = {}
        for name, il in items:
            if name in cache:
                continue
            try:
                ids = api_search(name)
            except Exception as e:  # noqa: BLE001
                print("  search fail", name, e)
                ids = []
            cache[name] = ids
            time.sleep(0.06)
        all_ids = [i for ids in cache.values() for i in ids]
        coord_map = {}
        for i in range(0, len(all_ids), 45):
            coord_map.update(coords_for(all_ids[i:i + 45]))
        for name, il in items:
            hit = None
            for qid in cache.get(name, []):
                if qid in coord_map:
                    hit = (qid, *coord_map[qid])
                    break
            if hit:
                resolved.append({"cat": cat, "name": name, "il": il,
                                 "qid": hit[0], "lat": hit[1], "lon": hit[2]})
            else:
                unresolved.append({"cat": cat, "name": name, "il": il})
                resolved.append({"cat": cat, "name": name, "il": il,
                                 "qid": None, "lat": None, "lon": None})
    OUT.write_text(json.dumps(resolved, ensure_ascii=False, indent=1))
    print(f"\nçözülen: {len(resolved) - len(unresolved)} / {len(resolved)}")
    print("koordinatsız:", len(unresolved))
    for u in unresolved[:40]:
        print("  -", u["cat"], u["name"], "|", u["il"])
