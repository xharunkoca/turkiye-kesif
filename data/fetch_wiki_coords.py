#!/usr/bin/env python3
"""wiki_lists_names.json içindeki adlar için koordinat toplar (kaldığı yerden devam eder)."""
import json
import pathlib
import time

from fetch_wiki_lists import RAW, api

CACHE = RAW / "wiki_coords.json"


def main():
    rows = json.loads((RAW / "wiki_lists_names.json").read_text())
    names = sorted({r["name"] for r in rows})
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    todo = [n for n in names if n not in cache]
    print(f"toplam {len(names)} ad, {len(todo)} tanesi eksik")
    for i in range(0, len(todo), 20):
        chunk = todo[i:i + 20]
        try:
            d = api({"action": "query", "prop": "coordinates", "titles": "|".join(chunk),
                     "format": "json", "formatversion": "2", "redirects": "1"})
        except Exception as e:  # noqa: BLE001
            print("  ! atlandı:", e)
            continue
        norm = {x["from"]: x["to"] for x in d.get("query", {}).get("normalized", [])}
        red = {x["from"]: x["to"] for x in d.get("query", {}).get("redirects", [])}
        by_title = {}
        for pg in d.get("query", {}).get("pages", []):
            c = (pg.get("coordinates") or [None])[0]
            if c:
                by_title[pg["title"]] = [round(c["lat"], 5), round(c["lon"], 5)]
        for t in chunk:
            tt = red.get(norm.get(t, t), norm.get(t, t))
            cache[t] = by_title.get(tt)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False))
        done = min(i + 20, len(todo))
        print(f"  {done}/{len(todo)} · bulunan: {sum(1 for v in cache.values() if v)}")
        time.sleep(2.5)
    hit = sum(1 for v in cache.values() if v)
    print(f"bitti: {hit}/{len(cache)} koordinatlı")


if __name__ == "__main__":
    main()
