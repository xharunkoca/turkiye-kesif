#!/usr/bin/env python3
"""Koordinatı bulunamayan adlar için başlık varyantlarıyla ikinci tur arama.

Örn. "Adana Etnografya Müzesi (Kuruköprü Anıt Müzesi ve Geleneksel Adana Evi)"
     → "Kuruköprü Anıt Müzesi ve Geleneksel Adana Evi"
     → "Adana Etnografya Müzesi"
Sonuç `wiki_coords.json` içine orijinal ad anahtarıyla yazılır.
"""
import json
import pathlib
import re
import time

from fetch_wiki_lists import RAW, api

CACHE = RAW / "wiki_coords.json"


def variants(name):
    out = []
    m = re.match(r"^(.*?)\s*\((.+?)\)\s*$", name)
    if m:
        base, inner = m.group(1).strip(), m.group(2).strip()
        out += [inner, base]
        # "X Müzesi ve Y" → "Y"
        if " ve " in inner:
            out.append(inner.split(" ve ", 1)[1].strip())
    else:
        out.append(re.sub(r"\s*\(.*?\)", "", name).strip())
    # "-Müzesi" ekini / "Müze" yazımını dene
    low = name.lower()
    if low.endswith("müzesi") or low.endswith("müze"):
        out.append(re.sub(r"\s*(müzesi|müze)$", "", name, flags=re.I).strip())
    else:
        out.append(f"{name} Müzesi")
    seen, res = {name}, []
    for v in out:
        v = v.strip()
        if len(v) > 3 and v not in seen:
            seen.add(v)
            res.append(v)
    return res[:3]


def main():
    rows = json.loads((RAW / "wiki_lists_names.json").read_text())
    names = sorted({r["name"] for r in rows})
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    missing = [n for n in names if not cache.get(n)]
    print(f"{len(missing)} koordinatsız ad için varyant taraması")
    alt = {}
    for n in missing:
        alt[n] = variants(n)
    queue = sorted({v for vs in alt.values() for v in vs if v not in cache})
    print(f"  {len(queue)} varyant başlık sorgulanacak")
    for i in range(0, len(queue), 20):
        chunk = queue[i:i + 20]
        try:
            d = api({"action": "query", "prop": "coordinates", "titles": "|".join(chunk),
                     "format": "json", "formatversion": "2", "redirects": "1"})
        except Exception as e:  # noqa: BLE001
            print("  ! atlandı:", e)
            time.sleep(8)
            continue
        norm = {x["from"]: x["to"] for x in d.get("query", {}).get("normalized", [])}
        red = {x["from"]: x["to"] for x in d.get("query", {}).get("redirects", [])}
        found = {}
        for pg in d.get("query", {}).get("pages", []):
            c = (pg.get("coordinates") or [None])[0]
            if c:
                found[pg["title"]] = [round(c["lat"], 5), round(c["lon"], 5)]
        for t in chunk:
            tt = red.get(norm.get(t, t), norm.get(t, t))
            cache[t] = found.get(tt)
        CACHE.write_text(json.dumps(cache, ensure_ascii=False))
        print(f"  {min(i + 20, len(queue))}/{len(queue)} · koordinatlı ad: {sum(1 for v in cache.values() if v)}")
        time.sleep(2.2)

    # orijinal adlara geri yaz
    gained = 0
    for n, vs in alt.items():
        if cache.get(n):
            continue
        for v in vs:
            if cache.get(v):
                cache[n] = cache[v]
                gained += 1
                break
    CACHE.write_text(json.dumps(cache, ensure_ascii=False))
    print(f"bitti: {gained} ada varyant üzerinden koordinat bulundu")


if __name__ == "__main__":
    main()
