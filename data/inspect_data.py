#!/usr/bin/env python3
"""Ham Wikidata verisini sadeleştirir ve istatistik çıkarır."""
import json
import pathlib
import re

RAW = pathlib.Path(__file__).parent / "raw"
CATS = ["antik", "muze", "doga", "tarih", "gol", "selale", "magara", "vadi",
        "plaj", "yayla", "dini", "kultur", "termal"]


def load(name):
    return json.loads((RAW / f"{name}.json").read_text())


def qid(uri):
    return uri.rsplit("/", 1)[-1] if uri else None


def coord(wkt):
    m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", wkt or "")
    return (float(m.group(2)), float(m.group(1))) if m else None


def norm_places(cat):
    rows = load(f"places_{cat}_d") + load(f"places_{cat}_p")
    best = {}
    for r in rows:
        x = qid(r["x"])
        links = int(r.get("links") or 0)
        if x not in best or links > best[x]["links"]:
            best[x] = {
                "id": x,
                "name": r.get("xLabel"),
                "desc": r.get("xDescription"),
                "lat": coord(r.get("coord"))[0] if coord(r.get("coord")) else None,
                "lon": coord(r.get("coord"))[1] if coord(r.get("coord")) else None,
                "il": r.get("ilLabel"),
                "parent": r.get("parentLabel"),
                "links": links,
            }
    return [v for v in best.values() if v["name"] and v["lat"]]


if __name__ == "__main__":
    prov = load("provinces")
    dist = load("districts")
    koy = load("koy")
    print("iller:", len({qid(p['il']) for p in prov}), "ilçe satırı:", len(dist),
          "köy:", len({qid(k['v']) for k in koy}))
    total = 0
    for cat in CATS:
        ps = norm_places(cat)
        total += len(ps)
        provinces = {p["il"] for p in ps}
        print(f"{cat:8s} {len(ps):6d} benzersiz | il kapsaması {len(provinces):2d}/81")
    print("TOPLAM", total)
