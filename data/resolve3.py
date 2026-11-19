#!/usr/bin/env python3
"""Curated yer adlarını Türkçe Vikipedi koordinatlarıyla doğrular (toplu sorgu)."""
import json
import pathlib
import time
import urllib.parse
import urllib.request

import curated

RAW = pathlib.Path(__file__).parent / "raw"
UA = {"User-Agent": "TurkiyeKesifBot/1.0 (tourism demo; contact: demo@example.org)"}

LISTS = {
    "doga": curated.DOGA,
    "selale": curated.SELALE,
    "magara": curated.MAGARA,
    "vadi": curated.VADI,
    "plaj": curated.PLAJ,
    "termal": curated.TERMAL,
    "carsi": curated.CARSI,
}


def api(lang, params, retries=5):
    url = f"https://{lang}.wikipedia.org/w/api.php?" + urllib.parse.urlencode(params)
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(8 * (i + 1))
                continue
            raise
    return {}


def batch_coords(titles, lang="tr"):
    out = {}
    titles = [t for t in titles if t]
    for i in range(0, len(titles), 40):
        chunk = titles[i:i + 40]
        d = api(lang, {"action": "query", "prop": "coordinates", "titles": "|".join(chunk),
                       "format": "json", "redirects": 1, "colimit": "max"})
        q = d.get("query", {})
        # normalize/redirect eşlemesi
        alias = {}
        for n in q.get("normalized", []):
            alias[n["to"]] = n["from"]
        for r in q.get("redirects", []):
            alias[r["to"]] = alias.get(r["from"], r["from"])
        for page in q.get("pages", {}).values():
            if "coordinates" not in page:
                continue
            title = page["title"]
            src = alias.get(title, title)
            c = page["coordinates"][0]
            out[src] = (c["lat"], c["lon"])
            out.setdefault(title, (c["lat"], c["lon"]))
        time.sleep(1.2)
    return out


def search_title(name, lang="tr"):
    d = api(lang, {"action": "query", "list": "search", "srsearch": name,
                   "srlimit": 1, "format": "json"})
    hits = d.get("query", {}).get("search", [])
    return hits[0]["title"] if hits else None


if __name__ == "__main__":
    items = [(cat, n, il) for cat, lst in LISTS.items() for n, il in lst]
    names = list({n for _, n, _ in items})
    print("ad:", len(names))

    coords = batch_coords(names)
    missing = [n for n in names if n not in coords]
    print("ilk tur:", len(coords), "| eksik:", len(missing))

    # arama ile başlık bulup koordinat çek
    found_titles = {}
    for n in missing:
        t = search_title(n)
        if t and t.lower() != n.lower():
            found_titles[n] = t
        time.sleep(0.9)
    if found_titles:
        more = batch_coords(list(found_titles.values()))
        for name, title in found_titles.items():
            if title in more:
                coords[name] = more[title]
    missing = [n for n in names if n not in coords]
    print("ikinci tur sonrası eksik:", len(missing))

    rows = []
    for cat, n, il in items:
        c = coords.get(n)
        rows.append({"cat": cat, "name": n, "il": il,
                     "lat": c[0] if c else None, "lon": c[1] if c else None,
                     "src": "tr.wikipedia" if c else None})
    (RAW / "curated_wiki.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print("koordinatlı:", sum(1 for r in rows if r["lat"]), "/", len(rows))
    for r in rows:
        if not r["lat"]:
            print("  eksik:", r["cat"], r["name"], "|", r["il"])
