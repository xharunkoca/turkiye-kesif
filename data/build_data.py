#!/usr/bin/env python3
"""Ham verilerden sitenin kullanacağı sıkıştırılmış veri setini üretir."""
import json
import math
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
    "antik": [("200", "genel kabul gören antik kent sayısı"),
              ("1.013", "antik kent ve kent kalıntısı (en geniş veri tabanı)"),
              ("148", "ziyarete açık arkeolojik sit alanı")],
    "muze": [("664", "müze (2025 TÜİK) — 220 bakanlığa bağlı, 426 özel")],
    "doga": [("50", "milli park"), ("271", "tabiat parkı"),
             ("54", "tabiatı koruma alanı"), ("113", "tabiat anıtı")],
    "tarih": [("130.633", "tescilli taşınmaz kültür varlığı (2025)")],
    "gol": [("200–320", "doğal göl (bakanlık raporları)")],
    "selale": [("374", "haritalanmış şelale"), ("53", "turistik veri tabanı kaydı")],
    "magara": [("40.000+", "keşfedilmiş yer altı mağarası"), ("32", "turistik mağara")],
    "vadi": [("150+", "kanyon"), ("113", "turistik veri tabanı kaydı"), ("11", "vadi")],
    "plaj": [("580", "Mavi Bayraklı plaj (2026 FEE)")],
    "gastro": [("1.912", "coğrafi işaretli ürün (TÜRKPATENT)")],
    "yayla": [("8.894", "yayla envanteri (2018)"), ("30.000", "yayla tahmini")],
    "dini": [("90.000+", "cami (Diyanet)")],
    "kultur": [("45.327", "kütüphane (2025 TÜİK)")],
    "termal": [("260", "termal tesis"), ("1.500+", "sıcak su kaynağı")],
    "carsi": [("20+", "büyük kapalı çarşı"), ("10.000", "geleneksel pazar yeri")],
}

CAPS = {"antik": 6, "muze": 4, "doga": 4, "tarih": 8, "gol": 5, "selale": 4, "magara": 4,
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

    merged = wik + cur + extra_carsi(provs, dists)

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
            if q_["name"] == name and haversine((q_["lat"], q_["lon"]), (p["lat"], p["lon"])) < 3:
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

    places = select(uniq)
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
