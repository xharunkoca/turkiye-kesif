#!/usr/bin/env python3
"""Curated yer adlarını tek SPARQL sorgusuyla Wikidata'da etiket eşlemesiyle doğrular."""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

import curated

RAW = pathlib.Path(__file__).parent / "raw"
UA = {"User-Agent": "TurkiyeKesifBot/1.0 (https://example.org; demo project)"}

LISTS = {
    "doga": curated.DOGA,
    "selale": curated.SELALE,
    "magara": curated.MAGARA,
    "vadi": curated.VADI,
    "plaj": curated.PLAJ,
    "termal": curated.TERMAL,
    "carsi": curated.CARSI,
}


def sparql(q, retries=5):
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"})
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=180) as r:
                d = json.load(r)
            return [{k: v.get("value") for k, v in b.items()} for b in d["results"]["bindings"]]
        except Exception as e:  # noqa: BLE001
            print("   retry", i + 1, type(e).__name__, e)
            time.sleep(10 * (i + 1))
    return []


def resolve(names):
    vals = " ".join('"%s"@tr' % n.replace('"', '') for n in names)
    q = f"""
    SELECT ?x ?label ?coord WHERE {{
      VALUES ?label {{ {vals} }}
      ?x rdfs:label ?label ; wdt:P625 ?coord .
    }}"""
    rows = sparql(q)
    out = {}
    for r in rows:
        m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", r["coord"])
        if m and r["label"] not in out:
            out[r["label"]] = {"qid": r["x"].rsplit("/", 1)[-1],
                               "lat": float(m.group(2)), "lon": float(m.group(1))}
    return out


def resolve_alt(names):
    """Etiket bulunamayanlar için alternatif etiket (altLabel) denemesi."""
    vals = " ".join('"%s"@tr' % n.replace('"', '') for n in names)
    q = f"""
    SELECT ?x ?alt ?coord WHERE {{
      VALUES ?alt {{ {vals} }}
      ?x skos:altLabel ?alt ; wdt:P625 ?coord .
    }}"""
    rows = sparql(q)
    out = {}
    for r in rows:
        m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", r["coord"])
        if m and r["alt"] not in out:
            out[r["alt"]] = {"qid": r["x"].rsplit("/", 1)[-1],
                             "lat": float(m.group(2)), "lon": float(m.group(1))}
    return out


if __name__ == "__main__":
    all_items = [(cat, n, il) for cat, items in LISTS.items() for n, il in items]
    names = list({n for _, n, _ in all_items})
    print("toplam ad:", len(names))

    found = {}
    for i in range(0, len(names), 60):
        chunk = names[i:i + 60]
        found.update(resolve(chunk))
        time.sleep(1.5)
    missing = [n for n in names if n not in found]
    print("etiketle bulunan:", len(found), "| eksik:", len(missing))
    if missing:
        time.sleep(2)
        found.update(resolve_alt(missing))
        missing = [n for n in names if n not in found]
        print("alt etiket sonrası eksik:", len(missing))

    rows = []
    for cat, n, il in all_items:
        hit = found.get(n, {})
        rows.append({"cat": cat, "name": n, "il": il,
                     "qid": hit.get("qid"), "lat": hit.get("lat"), "lon": hit.get("lon")})
    (RAW / "curated_resolved.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print("koordinatlı:", sum(1 for r in rows if r["lat"]), "/", len(rows))
    for r in rows:
        if not r["lat"]:
            print("  eksik:", r["cat"], r["name"], "|", r["il"])
