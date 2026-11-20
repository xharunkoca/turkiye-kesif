#!/usr/bin/env python3
"""GeoJSON (81 il) -> src/tr-provinces.json  (1000x438 viewBox, projeksiyonlu)"""
import json, math, unicodedata, sys, pathlib

SRC = pathlib.Path("/tmp/t.json")
OUT = pathlib.Path(__file__).resolve().parent.parent / "src" / "tr-provinces.json"
DATA = pathlib.Path(__file__).resolve().parent.parent / "data" / "turkiye-data.json"

ALIAS = {
    "afyon": "Afyonkarahisar", "icel": "Mersin", "mersin": "Mersin",
    "kahramanmaras": "Kahramanmaraş", "sanliurfa": "Şanlıurfa",
    "gumushane": "Gümüşhane", "hakkari": "Hakkari", "kirklareli": "Kırklareli",
}

def norm(s):
    s = s.replace("İ", "i").replace("I", "i").replace("ı", "i")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().replace("ş", "s").replace("ğ", "g").replace("ç", "c").replace("ö", "o").replace("ü", "u").strip()

def main():
    geo = json.loads(SRC.read_text(encoding="utf-8"))
    canon = {norm(il["n"]): il["n"] for il in json.loads(DATA.read_text(encoding="utf-8"))["ils"]}

    # projeksiyon: eşdikdörtgen, orta enleme göre ölçek
    lats, lons = [], []
    for f in geo["features"]:
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for p in polys:
            for ring in p:
                for lon, lat in ring:
                    lons.append(lon); lats.append(lat)
    lon0, lon1, lat0, lat1 = min(lons), max(lons), min(lats), max(lats)
    mid = (lat0 + lat1) / 2
    kx = math.cos(math.radians(mid))
    W, H, PAD = 1000.0, 438.0, 6.0
    sx = (W - 2 * PAD) / ((lon1 - lon0) * kx)   # 1 derece boylam = kaç piksel
    sy = sx                                      # 1 derece enlem = kaç piksel (kosinüs yalnız yatayda)
    sheight = (lat1 - lat0) * sy
    if sheight > H - 2 * PAD:
        f = (H - 2 * PAD) / sheight
        sx *= f; sy *= f
    ox = (W - (lon1 - lon0) * kx * sx) / 2
    oy = (H - (lat1 - lat0) * sy) / 2

    def proj(lon, lat):
        return ox + (lon - lon0) * kx * sx, oy + (lat1 - lat) * sy

    def ring_area(pts):
        a = 0.0
        for i in range(len(pts)):
            x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
            a += x1 * y2 - x2 * y1
        return abs(a) / 2

    def centroid(pts):
        a = cx = cy = 0.0
        for i in range(len(pts)):
            x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % len(pts)]
            f = x1 * y2 - x2 * y1
            a += f; cx += (x1 + x2) * f; cy += (y1 + y2) * f
        a *= 0.5
        if abs(a) < 1e-9: 
            return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)
        return cx / (6 * a), cy / (6 * a)

    def inside(pt, pts):
        x, y = pt; c = False
        j = len(pts) - 1
        for i in range(len(pts)):
            xi, yi = pts[i]; xj, yj = pts[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi):
                c = not c
            j = i
        return c

    out = []
    for f in geo["features"]:
        nm = f["properties"]["name"]
        key = norm(nm)
        name = canon.get(key) or ALIAS.get(key) or nm
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        rings, best, best_a = [], None, -1
        for p in polys:
            for ring in p:
                pts = [proj(lon, lat) for lon, lat in ring]
                if len(pts) < 4: continue
                a = ring_area(pts)
                if a < 0.6: continue  # ada/parazit
                if a > best_a: best_a, best = a, pts
                rings.append(pts)
        if not rings: continue
        d = " ".join("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z" for pts in rings)
        c = centroid(best)
        if not inside(c, best):
            xs = [p[0] for p in best]; ys = [p[1] for p in best]
            c = ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)
        out.append({"n": name, "d": d, "x": round(c[0], 1), "y": round(c[1], 1), "a": round(best_a, 1)})
    out.sort(key=lambda o: -o["a"])
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{len(out)} il · {OUT.stat().st_size/1024:.0f} KB")
    missing = set(canon.values()) - {o["n"] for o in out}
    if missing: print("EŞLEŞMEYEN:", missing)

if __name__ == "__main__":
    main()
