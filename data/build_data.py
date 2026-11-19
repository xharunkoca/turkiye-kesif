#!/usr/bin/env python3
"""Ham verilerden sitenin kullanacağı sıkıştırılmış veri setini üretir."""
import json
import math
import os
import pathlib
import re
from collections import defaultdict

import curated

RAW = pathlib.Path(__file__).parent / "raw"

OUT = pathlib.Path(__file__).parent / "turkiye-data.json"

REGIONS = {
    "Marmara": ["İstanbul", "Edirne", "Kırklareli", "Tekirdağ", "Çanakkale", "Balıkesir",
                "Bursa", "Yalova", "Kocaeli", "Sakarya", "Bilecik"],
    "Ege": ["İzmir", "Manisa", "Aydın", "Denizli", "Muğla", "Uşak", "Afyonkarahisar", "Kütahya"],
    "Akdeniz": ["Antalya", "Isparta", "Burdur", "Mersin", "Adana", "Osmaniye", "Hatay",
                "Kahramanmaraş"],
    "İç Anadolu": ["Ankara", "Konya", "Kayseri", "Sivas", "Yozgat", "Kırşehir", "Nevşehir",
                   "Niğde", "Aksaray", "Karaman", "Kırıkkale", "Çankırı", "Eskişehir"],
    "Karadeniz": ["Zonguldak", "Karabük", "Bartın", "Kastamonu", "Çorum", "Sinop", "Samsun",
                  "Tokat", "Amasya", "Ordu", "Giresun", "Trabzon", "Rize", "Artvin",
                  "Gümüşhane", "Bayburt", "Düzce", "Bolu"],
    "Doğu Anadolu": ["Erzurum", "Erzincan", "Ağrı", "Kars", "Iğdır", "Ardahan", "Van", "Muş",
                     "Bitlis", "Bingöl", "Elazığ", "Malatya", "Tunceli", "Hakkari"],
    "Güneydoğu Anadolu": ["Gaziantep", "Kilis", "Şanlıurfa", "Diyarbakır", "Mardin", "Batman", "Siirt",
                  "Şırnak", "Adıyaman"],
}
IL_REGION = {il: r for r, iller in REGIONS.items() for il in iller}

CATS = [
    ("antik", "Antik Kentler", "i-columns", "blue"),
    ("muze", "Müzeler", "i-museum", "orange"),
    ("doga", "Doğa ve Milli Parklar", "i-tree", "green"),
    ("tarih", "Tarihi Yapılar", "i-castle", "red"),
    ("gol", "Göller", "i-waves", "teal"),
    ("selale", "Şelaleler", "i-waterfall", "teal"),
    ("magara", "Mağaralar", "i-cave", "purple"),
    ("vadi", "Vadiler ve Kanyonlar", "i-canyon", "orange"),
    ("plaj", "Plajlar ve Kıyılar", "i-umbrella", "teal"),
    ("gastro", "Gastronomi ve Yöresel", "i-fork", "orange"),
    ("yayla", "Yaylalar ve Kamp", "i-tent", "green"),
    ("dini", "Dini Yapılar ve İnanç", "i-mosque", "purple"),
    ("kultur", "Kültür ve Sanat", "i-masks", "purple"),
    ("termal", "Kaplıcalar ve Termal", "i-spring", "blue"),
    ("carsi", "Çarşılar ve Pazarlar", "i-market", "red"),
]
CAT_IDS = [c[0] for c in CATS]

# kullanıcının verdiği resmî envanter sayıları (kartlarda "Türkiye geneli" olarak gösterilir)
ENVANTER = {
    # (değer, açıklama/kaynak) — kullanıcı referans listesi
    "antik": [("200", "genel kabul gören antik kent (2025)"),
              ("77", "medyada öne çıkan dar liste"),
              ("1.013", "antik kent ve kent kalıntısı (en geniş veri tabanı)"),
              ("148", "ziyarete açık arkeolojik ve tarihî sit")],
    "muze": [("664", "müze (2025 TÜİK): 220 bakanlığa bağlı, 426 özel")],
    "doga": [("50–51", "milli park (Tarım ve Orman Bak., 2025)"),
             ("271–274", "tabiat parkı"),
             ("54", "tabiatı koruma alanı"),
             ("113", "tabiat anıtı")],
    "tarih": [("130.633", "tescilli taşınmaz kültür varlığı (2025 KTB)")],
    "gol": [("200", "doğal göl (Çevre Bakanlığı raporu)"),
            ("320", "doğal göl (bakanlık belgesi)")],
    "selale": [("374", "haritalanmış şelale"),
               ("300+", "keşif rehberleri"),
               ("80", "seçkili liste"),
               ("53", "turistik veri tabanı kaydı")],
    "magara": [("40.000+", "keşfedilmiş yer altı mağarası"),
               ("400+", "yeraltı harikası (sınıflandırma)"),
               ("32", "turistik/rehberli mağara")],
    "vadi": [("150+", "kanyon (genel)"),
             ("113", "kanyon (turistik veri tabanı)"),
             ("100+", "kanyon (medya tahmini)"),
             ("11", "vadi (turistik veri tabanı)")],
    "plaj": [("580", "Mavi Bayraklı plaj (2026 FEE)")],
    "gastro": [("1.912", "coğrafi işaretli ürün (TÜRKPATENT, 2026)")],
    "yayla": [("389", "yayla (seyahat/yaşam medyası)"),
              ("387", "yayla (turistik veri tabanı)"),
              ("940", "yayla (akademik tespit)"),
              ("8.894", "yayla envanteri (2018)"),
              ("~30.000", "yayla tahmini (Tarım ve Orman Bak.)")],
    "dini": [("90.000+", "cami (Diyanet İşleri Başkanlığı)"),
             ("90.301 / 90.458 / 90.644", "farklı tarihli resmî açıklamalar")],
    "kultur": [("45.327", "kütüphane (2025 TÜİK; halk + üniversite + örgün)")],
    "termal": [("260", "termal tesis (Kültür ve Turizm Bak.)"),
               ("1.500+", "sıcak su kaynağı"),
               ("196", "kaplıca tesisi (46 ilde)")],
    "carsi": [("20+", "büyük kapalı çarşı"),
              ("10.000", "geleneksel pazar yeri (genel tahmin)")],
}

CAPS = {"antik": 6, "muze": 18, "doga": 45, "tarih": 8, "gol": 5, "selale": 4, "magara": 4,
        "vadi": 4, "plaj": 5, "gastro": 3, "yayla": 4, "dini": 6, "kultur": 4, "termal": 4,
        "carsi": 3}

ALIAS = {"Afyon": "Afyonkarahisar", "İçel": "Mersin", "Urfa": "Şanlıurfa", "Maraş": "Kahramanmaraş",
         "Antep": "Gaziantep", "Hakkâri": "Hakkari", "Şebinkarahisar": "Giresun"}


def load(name):
    return json.loads((RAW / f"{name}.json").read_text())


def qid(uri):
    return uri.rsplit("/", 1)[-1] if uri else None


def point(wkt):
    m = re.match(r"Point\(([-\d.]+) ([-\d.]+)\)", wkt or "")
    return (float(m.group(2)), float(m.group(1))) if m else None


def haversine(a, b):
    lat1, lon1 = a
    lat2, lon2 = b
    p = math.pi / 180
    dlat = (lat2 - lat1) * p
    dlon = (lon2 - lon1) * p
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin(dlon / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


SKIP_RE = re.compile(r"^Q\d+$")


def clean_district(name):
    if not name or SKIP_RE.match(name.strip()):
        return None
    n = re.sub(r"\s*\((ilçe|ilçesi|district[^)]*|[^)]*ilçe[^)]*)\)", "", name, flags=re.I)
    n = re.sub(r"\s+(ilçesi|İlçesi|district|District)$", "", n)
    n = n.strip()
    return n or None


def clean(name):
    if not name:
        return None
    n = name.strip()
    if len(n) < 2 or len(n) > 70:
        return None
    if n.lower() in {"türkiye", "turkey", "anadolu"}:
        return None
    return n


# ---------------------------------------------------------------- iller
def build_provinces():
    rows = load("provinces")
    provs = {}
    for r in rows:
        name = ALIAS.get(r.get("ilLabel", ""), r.get("ilLabel", ""))
        if name not in IL_REGION:
            continue
        c = point(r.get("coord"))
        provs[name] = {
            "n": name,
            "plate": int(r["plate"]) if r.get("plate", "").isdigit() else None,
            "q": qid(r["il"]),
            "lat": round(c[0], 4) if c else None,
            "lon": round(c[1], 4) if c else None,
            "r": IL_REGION[name],
        }
    # plaka kodu / koordinat eksiklerini tamamla
    for name, p in provs.items():
        if p["plate"] is None:
            p["plate"] = sorted(provs).index(name) + 1
    return provs


def build_districts(provs):
    rows = load("districts2") + load("districts")
    out = defaultdict(dict)
    for r in rows:
        il = ALIAS.get(r.get("ilLabel", ""), r.get("ilLabel", ""))
        dname = clean_district(r.get("dLabel"))
        if il not in provs or not dname:
            continue
        c = point(r.get("coord"))
        rec = out[il].setdefault(dname, {"n": dname, "lat": None, "lon": None, "q": qid(r.get("d")), "k": [], "m": []})
        if c and not rec["lat"]:
            rec["lat"], rec["lon"] = round(c[0], 4), round(c[1], 4)
    return out


def attach_villages(provs, dists):
    """Önce ilçe bağı verilmiş köyler, sonra koordinattan en yakın ilçeye atama."""
    rows = load("koy")
    seen = set()
    for r in rows:
        il = ALIAS.get(r.get("ilLabel", ""), r.get("ilLabel", ""))
        dn = clean_district(r.get("dLabel"))
        vn = clean(r.get("vLabel"))
        if il not in provs or not dn or not vn or vn == dn:
            continue
        key = (il, dn, vn)
        if key in seen:
            continue
        seen.add(key)
        d = dists[il].setdefault(dn, {"n": dn, "lat": None, "lon": None, "q": None, "k": [], "m": []})
        d["k"].append(vn)

    # koordinatlı köyler: en yakın ilçe merkezine ata
    geo = load("koy_geo")
    dist_pts = []
    for il, dd in dists.items():
        for dn, rec in dd.items():
            if rec["lat"] is not None:
                dist_pts.append((il, dn, rec["lat"], rec["lon"]))
    prov_pts = [(n, p["lat"], p["lon"]) for n, p in provs.items() if p["lat"] is not None]
    added = 0
    for r in geo:
        vn = clean(r.get("vLabel"))
        pt = point(r.get("coord"))
        if not vn or not pt:
            continue
        if not (35.0 <= pt[0] <= 42.6 and 25.2 <= pt[1] <= 45.0):
            continue
        if not dist_pts:
            continue
        best = min(dist_pts, key=lambda x: haversine(pt, (x[2], x[3])))
        dkm = haversine(pt, (best[2], best[3]))
        if dkm > 22:
            # ilçe merkezine çok uzak: ili üzerinden merkez ilçeye yaz
            il = min(prov_pts, key=lambda x: haversine(pt, (x[1], x[2])))[0]
            if il not in dists:
                continue
            dn = sorted(dists[il])[0]
        else:
            il, dn = best[0], best[1]
        key = (il, dn, vn)
        if key in seen:
            continue
        seen.add(key)
        d = dists[il].setdefault(dn, {"n": dn, "lat": None, "lon": None, "q": None, "k": [], "m": []})
        d["k"].append(vn)
        added += 1
    print(f"  + koordinattan eklenen köy: {added}")

    # büyükşehirlerde köyler 2012'den sonra mahalle statüsünde: mahalle kayıtlarını da bağla
    mah = load("mahalle")
    madd = 0
    for r in mah:
        vn = clean(r.get("vLabel"))
        pt = point(r.get("coord"))
        if not vn or not pt or not dist_pts:
            continue
        if not (35.0 <= pt[0] <= 42.6 and 25.2 <= pt[1] <= 45.0):
            continue
        best = min(dist_pts, key=lambda x: haversine(pt, (x[2], x[3])))
        if haversine(pt, (best[2], best[3])) > 22:
            continue
        il, dn = best[0], best[1]
        key = ("m", il, dn, vn)
        if key in seen:
            continue
        seen.add(key)
        d = dists[il].setdefault(dn, {"n": dn, "lat": None, "lon": None, "q": None, "k": [], "m": []})
        d.setdefault("m", []).append(vn)
        madd += 1
    print(f"  + eklenen mahalle: {madd}")


# ---------------------------------------------------------------- mekânlar
def collect_wikidata_places(provs, dists):
    """(cat, name, il, district, lat, lon, type, sitelinks, src)"""
    province_names = list(provs)
    centroids = {n: (provs[n]["lat"], provs[n]["lon"]) for n in province_names
                 if provs[n]["lat"] is not None}
    district_pts = defaultdict(list)
    for il, dd in dists.items():
        for dn, rec in dd.items():
            if rec["lat"]:
                district_pts[il].append((dn, (rec["lat"], rec["lon"])))

    def nearest_province(pt):
        return min(centroids.items(), key=lambda kv: haversine(pt, kv[1]))[0] if centroids else None

    def nearest_district(il, pt):
        pts = district_pts.get(il) or []
        if not pts:
            return None
        return min(pts, key=lambda kv: haversine(pt, kv[1]))[0]

    files = []
    for cat in CAT_IDS:
        if cat in ("gastro", "carsi", "tarih"):
            continue
        files += [(cat, f"v2_{cat}_{s}") for s in ("d", "p", "g")]
    # tarih parçalı çekildi
    for i in range(3):
        files += [("tarih", f"v2x_tarih{i}_{s}") for s in ("d", "p", "g")]

    best_by_qid = {}
    for cat, fname in files:
        path = RAW / f"{fname}.json"
        if not path.exists():
            print("  ! eksik dosya", fname)
            continue
        for r in json.loads(path.read_text()):
            x = qid(r.get("x"))
            pt = point(r.get("coord"))
            name = clean(r.get("xLabel"))
            if not x or not pt or not name:
                continue
            if not (35.0 <= pt[0] <= 42.6 and 25.2 <= pt[1] <= 45.0):
                continue
            links = int(r.get("links") or 0)
            il = ALIAS.get(r.get("ilLabel", ""), r.get("ilLabel", ""))
            if il not in provs:
                il = nearest_province(pt)
            if not il:
                continue
            dist = None
            parent = r.get("parentLabel")
            if parent and parent in dists.get(il, {}) and parent != il:
                dist = parent
            rec = {
                "cat": cat, "name": name, "il": il, "dist": dist,
                "lat": round(pt[0], 4), "lon": round(pt[1], 4),
                "type": r.get("clsLabel") or None, "links": links, "src": "wikidata",
            }
            old = best_by_qid.get(x)
            if old is None or links > old["links"]:
                best_by_qid[x] = rec
            # aynı mekân birden fazla kategoride olabilir; ilk (önce gelen) kategori korunur
    places = list(best_by_qid.values())
    cleaned = []
    for p in places:
        c = (provs[p["il"]]["lat"], provs[p["il"]]["lon"])
        if c[0] is not None and haversine((p["lat"], p["lon"]), c) > 220:
            continue  # koordinat il ile uyuşmuyor -> kaydı at
        if not p["dist"]:
            p["dist"] = nearest_district(p["il"], (p["lat"], p["lon"]))
        cleaned.append(p)
    print(f"  - koordinat aykırısı atılan: {len(places) - len(cleaned)}")
    return cleaned


def curated_places(provs, dists):
    rows = json.loads((RAW / "curated_wiki.json").read_text())
    out = []
    for r in rows:
        il = ALIAS.get(r["il"], r["il"])
        if il not in provs:
            continue
        lat, lon = r.get("lat"), r.get("lon")
        approx = False
        if not lat:
            lat, lon = provs[il]["lat"], provs[il]["lon"]
            approx = True
        if not lat:
            continue
        center = (provs[il]["lat"], provs[il]["lon"])
        if center[0] is not None and haversine((lat, lon), center) > 120:
            lat, lon, approx = center[0], center[1], True
        dist = None
        pts = [(dn, (rec["lat"], rec["lon"])) for dn, rec in dists.get(il, {}).items() if rec["lat"]]
        if pts:
            dist = min(pts, key=lambda kv: haversine((lat, lon), kv[1]))[0]
        out.append({"cat": r["cat"], "name": r["name"], "il": il, "dist": dist,
                    "lat": round(lat, 4), "lon": round(lon, 4),
                    "type": None, "links": 0, "src": "approx" if approx else "wikipedia"})
    # gastronomi: coğrafi işaretli ürünler (il merkezi)
    for name, il in curated.GASTRO:
        il = ALIAS.get(il, il)
        if il not in provs:
            continue
        out.append({"cat": "gastro", "name": name, "il": il, "dist": None,
                    "lat": provs[il]["lat"], "lon": provs[il]["lon"],
                    "type": "coğrafi işaretli ürün", "links": 0, "src": "approx"})
    return out


def extra_carsi(provs, dists):
    """Çarşı/bedesten/arasta/han kayıtlarını etiketten yakalar (Wikidata)."""
    rows = load("carsi_geo")
    keep_cls = {"bedesten", "arasta", "pasaj", "han", "çarşı", "pazar yeri", "dükkân", "tarihî bina"}
    drop_words = ("camii", "cami", "çeşme", "hamam", "köy", "mahalle", "sokak", "bulvar")
    prov_pts = [(n, p["lat"], p["lon"]) for n, p in provs.items() if p["lat"] is not None]
    dist_pts = {}
    for il, dd in dists.items():
        dist_pts[il] = [(dn, rec["lat"], rec["lon"]) for dn, rec in dd.items() if rec["lat"]]
    out, seen = [], set()
    for r in rows:
        name = clean(r.get("xLabel"))
        pt = point(r.get("coord"))
        if not name or not pt:
            continue
        if not (35.0 <= pt[0] <= 42.6 and 25.2 <= pt[1] <= 45.0):
            continue
        low = name.lower()
        if any(w in low for w in drop_words):
            continue
        if not any(k in low for k in ("çarşı", "bedesten", "arasta", "hanı", "pazarı", "pazar")):
            continue
        cls = (r.get("clsLabel") or "").lower()
        if cls and cls not in keep_cls:
            continue
        il = min(prov_pts, key=lambda x: haversine(pt, (x[1], x[2])))[0]
        center = (provs[il]["lat"], provs[il]["lon"])
        if haversine(pt, center) > 160:
            continue
        dist = None
        if dist_pts.get(il):
            dist = min(dist_pts[il], key=lambda x: haversine(pt, (x[1], x[2])))[0]
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"cat": "carsi", "name": name, "il": il, "dist": dist,
                    "lat": round(pt[0], 4), "lon": round(pt[1], 4),
                    "type": r.get("clsLabel") or "çarşı", "links": int(r.get("links") or 0),
                    "src": "wikidata"})
    print(f"  + çarşı/pazar kaydı: {len(out)}")
    return out


def nearest_district_in(dists, il, pt):
    """Verilen ilin ilçeleri arasından koordinata en yakın ilçe adı."""
    dd = dists.get(il, {})
    pts = [(dn, r["lat"], r["lon"]) for dn, r in dd.items() if r["lat"]]
    if not pts:
        return None
    return min(pts, key=lambda x: haversine(pt, (x[1], x[2])))[0]


def extra_wiki(provs, dists):
    """Vikipedi resmî listelerinden (millî park, tabiat parkı/anıtı, koruma alanı, müzeler)
    ad + il; koordinat bulunabildiyse konum. Koordinatı olmayanlar da korunur."""
    names_f = RAW / "wiki_lists_names.json"
    coords_f = RAW / "wiki_coords.json"
    if not names_f.exists():
        print("  ! wiki listeleri yok (fetch_wiki_lists.py names)")
        return []
    rows = json.loads(names_f.read_text())
    coords = json.loads(coords_f.read_text()) if coords_f.exists() else {}

    def type_of(name, cat):
        low = name.lower()
        if cat == "muze":
            return "Müze"
        if "millî parkı" in low or "milli parkı" in low:
            return "Millî park"
        if "tabiat parkı" in low:
            return "Tabiat parkı"
        if "tabiat anıtı" in low:
            return "Tabiat anıtı"
        return "Tabiatı koruma alanı"

    out, nocoord = [], 0
    for r in rows:
        il = None
        for cand in r.get("ils") or []:
            c2 = ALIAS.get(cand, cand)
            if c2 in provs:
                il = c2
                break
        if not il:
            continue
        lat = lon = dist = None
        c = coords.get(r["name"])
        if c:
            la, lo = c[0], c[1]
            if 35.0 <= la <= 42.6 and 25.2 <= lo <= 45.0:
                lat, lon = round(la, 4), round(lo, 4)
                dist = nearest_district_in(dists, il, (lat, lon))
        if lat is None:
            nocoord += 1
        out.append({"cat": r["cat"], "name": r["name"], "il": il, "dist": dist,
                    "lat": lat, "lon": lon, "type": type_of(r["name"], r["cat"]),
                    "links": 0, "src": "wikipedia"})
    print(f"  + wiki listesi: {len(out)} kayıt ({nocoord} koordinatsız)")
    return out


CITY_ALIAS = {"Afyon": "Afyonkarahisar"}


def _pip(lon, lat, ring):
    """Ray casting: nokta halka içinde mi?"""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if ((yi > lat) != (yj > lat)) and (lon < (xj - xi) * (lat - yi) / (yj - yi + 1e-12) + xi):
            inside = not inside
        j = i
    return inside


def load_city_geoms():
    """İl sınır poligonları (data/raw/tr-cities.json)."""
    path = os.path.join(RAW, "tr-cities.json")
    if not os.path.exists(path):
        return {}
    data = json.load(open(path, encoding="utf-8"))
    geoms = {}
    for f in data["features"]:
        name = CITY_ALIAS.get(f["properties"]["name"], f["properties"]["name"])
        polys = []
        g = f["geometry"]
        groups = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in groups:
            ring = [(float(x), float(y)) for x, y in poly[0]]
            xs = [c[0] for c in ring]
            ys = [c[1] for c in ring]
            polys.append((ring, min(xs), min(ys), max(xs), max(ys)))
        geoms[name] = polys
    return geoms


def _in_province(pt, polys, pad=0.0):
    lon, lat = pt[1], pt[0]
    for ring, x0, y0, x1, y1 in polys:
        if lon < x0 - pad or lon > x1 + pad or lat < y0 - pad or lat > y1 + pad:
            continue
        if _pip(lon, lat, ring):
            return True
    return False


def _nearest_prov(pt, geoms, max_deg=0.2):
    """Hiçbir il poligonu içinde değilse en yakın il sınırı (kıyı/ada tolerasyonu)."""
    lon, lat = pt[1], pt[0]
    best, bestd = None, None
    for name, polys in geoms.items():
        for ring, x0, y0, x1, y1 in polys:
            if lon < x0 - max_deg or lon > x1 + max_deg or lat < y0 - max_deg or lat > y1 + max_deg:
                continue
            for x, y in ring:
                d = (x - lon) ** 2 + (y - lat) ** 2
                if bestd is None or d < bestd:
                    bestd, best = d, name
    if bestd is not None and math.sqrt(bestd) <= max_deg:
        return best
    return None


def fix_province_by_geom(places, geoms, dists):
    """Koordinatı kendi ilinin sınırı dışına düşen kayıtları düzelt."""
    if not geoms:
        print("  - il sınırı denetimi: atlandı (tr-cities.json yok)")
        return places
    moved = dropped = 0
    for p in places:
        if p.get("lat") is None:
            continue
        pt = (p["lat"], p["lon"])
        cur = p["il"]
        own = geoms.get(cur)
        if own and _in_province(pt, own):
            continue
        hits = [n for n, polys in geoms.items() if n != cur and _in_province(pt, polys)]
        if len(hits) == 1:
            p["il"] = hits[0]
            nd = nearest_district_in(dists, hits[0], pt)
            if nd:
                p["dist"] = nd
            moved += 1
        else:
            near = _nearest_prov(pt, geoms)
            if near:
                if near != cur:
                    p["il"] = near
                    nd = nearest_district_in(dists, near, pt)
                    if nd:
                        p["dist"] = nd
                    moved += 1
            else:
                p["lat"] = p["lon"] = None
                dropped += 1
    print(f"  - il sınırı denetimi: {moved} kayıt doğru ile taşındı, {dropped} hatalı koordinat aranır duruma alındı")
    return places


def fix_districts(places, dists):
    """İlçe merkezinden 90 km'den uzak kayıtları en yakın ilçeye taşı (P131 hatası düzeltmesi)."""
    moved = 0
    for p in places:
        if p.get("lat") is None or not p.get("dist"):
            continue
        dd = dists.get(p["il"], {})
        rec = dd.get(p["dist"])
        if not rec or not rec.get("lat"):
            continue
        d0 = haversine((p["lat"], p["lon"]), (rec["lat"], rec["lon"]))
        if d0 <= 90:
            continue
        nd = nearest_district_in(dists, p["il"], (p["lat"], p["lon"]))
        if nd and nd != p["dist"]:
            nrec = dd.get(nd)
            if nrec and nrec.get("lat") and haversine((p["lat"], p["lon"]), (nrec["lat"], nrec["lon"])) < d0:
                p["dist"] = nd
                moved += 1
    print(f"  - ilçe düzeltmesi: {moved} kayıt en yakın ilçeye taşındı")
    return places


def select(places):
    """Her il + kategori için en iyi kayıtları seç."""
    grouped = defaultdict(list)
    for p in places:
        grouped[(p["il"], p["cat"])].append(p)
    chosen = []
    for (il, cat), items in grouped.items():
        items.sort(key=lambda p: (p["src"] != "wikipedia", p["src"] == "approx", -p["links"], p["name"]))
        chosen += items[:CAPS[cat]]
    return chosen


if __name__ == "__main__":
    provs = build_provinces()
    dists = build_districts(provs)
    attach_villages(provs, dists)
    print(f"il: {len(provs)} | ilçe: {sum(len(v) for v in dists.values())} | "
          f"köy: {sum(len(d['k']) for v in dists.values() for d in v.values())} | "
          f"mahalle: {sum(len(d.get('m', [])) for v in dists.values() for d in v.values())}")

    wik = collect_wikidata_places(provs, dists)
    cur = curated_places(provs, dists)
    print(f"wikidata mekân: {len(wik)} | curated: {len(cur)}")

    merged = wik + cur + extra_carsi(provs, dists) + extra_wiki(provs, dists)

    # ---- ad temizliği ve genel/jenerik kayıtların ayıklanması
    GENERIC = {"bedesten", "tarihî çarşı", "tarihî arasta", "tarihî bedesten", "tarihî taş han",
               "bedesten ve arasta", "bedesten çarşısı", "tarihî arasta çarşısı", "tümülüs",
               "harabe", "kale", "cami", "höyük", "mağara", "hamam", "han", "kilise", "türbe"}
    def tidy(name):
        n = re.sub(r"\s*\(\d+\)", "", name)
        n = re.sub(r"\s{2,}", " ", n).strip()
        return n

    seen_ids, by_name, uniq = set(), [], []
    for p in merged:
        name = tidy(p["name"])
        if re.match(r"^Q\d+$", name) or "yehud" in name.lower():
            continue
        if name.lower() in GENERIC or name.lower().startswith("tümülüs"):
            continue
        if name in seen_ids:
            continue
        # aynı ad + 3 km yakınlık = aynı yer
        dup = False
        for q_ in by_name:
            if q_["name"] != name:
                continue
            if q_.get("lat") is None or p.get("lat") is None:
                dup = True          # konumu olmayan aynı ad → yine tekrar say
                break
            if haversine((q_["lat"], q_["lon"]), (p["lat"], p["lon"])) < 3:
                dup = True
                break
        if dup:
            continue
        p["name"] = name
        by_name.append(p)
        seen_ids.add(name)
        uniq.append(p)

    # aynı il+kategori+ad tekrarını at
    seen, dedup = set(), []
    for p in uniq:
        k = (p["il"], p["cat"], p["name"].lower())
        if k in seen:
            continue
        seen.add(k)
        dedup.append(p)
    uniq = dedup

    CITY_GEOMS = load_city_geoms()
    places = fix_districts(fix_province_by_geom(select(uniq), CITY_GEOMS, dists), dists)
    print(f"seçilen mekân: {len(places)}")

    # il sıralaması: plaka koduna göre
    order = sorted(provs, key=lambda n: provs[n]["plate"])
    idx = {n: i for i, n in enumerate(order)}

    data = {
        "cats": [{"id": c, "label": l, "icon": ic, "color": co,
                  "env": [{"v": v, "l": d} for v, d in ENVANTER[c]]} for c, l, ic, co in CATS],
        "ils": [
            {"n": n, "p": provs[n]["plate"], "r": provs[n]["r"], "q": provs[n]["q"],
             "lat": provs[n]["lat"], "lon": provs[n]["lon"],
             "d": [
                 {"n": d["n"], "lat": d["lat"], "lon": d["lon"],
                  "k": sorted(set(d["k"])), "m": sorted(set(d.get("m", [])))}
                 for d in sorted(dists[n].values(), key=lambda x: x["n"])
             ]}
            for n in order
        ],
        "places": [
            [p["name"], CAT_IDS.index(p["cat"]), idx[p["il"]], p["dist"] or "",
             p["lat"], p["lon"], p["type"] or "", p["src"]]
            for p in sorted(places, key=lambda p: (idx[p["il"]], CAT_IDS.index(p["cat"]), p["name"]))
        ],
    }
    txt = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    OUT.write_text(txt)
    print(f"yazıldı: {OUT} ({len(txt) / 1024:.0f} KB)")

    per_cat = defaultdict(int)
    per_il = defaultdict(int)
    for p in places:
        per_cat[p["cat"]] += 1
        per_il[p["il"]] += 1
    print("kategori dağılımı:", dict(sorted(per_cat.items())))
    print("il başına ortalama:", round(len(places) / 81, 1),
          "| en az:", min(per_il.values()), min(per_il, key=per_il.get))
