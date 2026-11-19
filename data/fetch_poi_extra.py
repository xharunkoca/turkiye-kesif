#!/usr/bin/env python3
"""Wikidata sınıf taraması: koordinatlı ek POI'ler (kale, köprü, mağara, ibadet yeri…).

Çıktı: data/raw/poi_<slug>.json  →  [{i, label, lat, lon, type}]
"""
import json
import re
import sys

from fetch import RAW, sparql

CLASSES = {
    "kale": "Q23413",
    "kopru": "Q12280",
    "magara": "Q35509",
    "manastir": "Q44613",
    "kilise": "Q16970",
    "turbe": "Q381885",
    "cami": "Q32815",
    "muze": "Q33506",
    "antik": "Q15661340",
    "gol": "Q23397",
    "selale": "Q34038",
    "baraj": "Q131681",
    "plaj": "Q40080",
    "kaplica": "Q177380",
}
PAGE = 1200
MAX = 3000


def fetch(slug, qid):
    out = RAW / f"poi_{slug}.json"
    if out.exists():
        rows = json.loads(out.read_text())
        print(f"= {slug}: önbellekten {len(rows)}")
        return rows
    rows, seen, off = [], set(), 0
    while off < MAX:
        q = f"""
SELECT ?i ?iLabel ?coord ?typeLabel WHERE {{
  ?i wdt:P31/wdt:P279* wd:{qid} ; wdt:P625 ?coord ; wdt:P17 wd:Q43 .
  OPTIONAL {{ ?i wdt:P31 ?type }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "tr,en". }}
}} LIMIT {PAGE} OFFSET {off}"""
        try:
            batch = sparql(q, retries=3)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {slug} offset {off}: {e}", file=sys.stderr)
            break
        for r in batch:
            if r["i"] in seen:
                continue
            seen.add(r["i"])
            m = re.search(r"Point\(([-\d.]+) ([-\d.]+)\)", r["coord"] or "")
            if not m:
                continue
            lon, lat = float(m.group(1)), float(m.group(2))
            rows.append({"i": r["i"], "label": r["iLabel"], "lat": lat, "lon": lon,
                         "type": r.get("typeLabel", "")})
        print(f"  {slug}: {len(rows)} (+{len(batch)})")
        if len(batch) < PAGE:
            break
        off += PAGE
    out.write_text(json.dumps(rows, ensure_ascii=False))
    return rows


def main():
    todo = sys.argv[1:] or list(CLASSES)
    for slug in todo:
        if slug not in CLASSES:
            print("bilinmeyen:", slug)
            continue
        fetch(slug, CLASSES[slug])


if __name__ == "__main__":
    main()
