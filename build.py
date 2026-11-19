#!/usr/bin/env python3
"""Türkiye Keşif — derleyici (SPA + statik/prerender sayfalar).

Girdi : src/template.html, src/style.css, src/app.js, src/tr-path.txt,
        data/turkiye-data.json, assets/img/*.webp
Çıktı : index.html (SPA kabuğu, dış CSS/JS), assets/style.<hash>.css, assets/app.<hash>.js,
        il/<slug>/, kategori/<id>/, rota/<slug>/ statik sayfaları, yasal sayfalar,
        404.html, sitemap.xml

Kullanım: python3 build.py
"""
import datetime
import hashlib
import json
import math
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src"
DATA = ROOT / "data" / "turkiye-data.json"
SITE = "https://xharunkoca.github.io/turkiye-kesif"
TODAY = datetime.date.today().isoformat()

THEMES = [
    ("tarih", "Tarih ve Kültür Rotası", ["antik", "tarih", "muze", "kultur"]),
    ("doga", "Doğa ve Manzara Rotası", ["doga", "gol", "selale", "vadi", "yayla"]),
    ("inanc", "İnanç ve Miras Rotası", ["dini", "carsi", "muze"]),
    ("lezzet", "Lezzet Durakları Rotası", ["gastro", "carsi"]),
    ("deniz", "Deniz ve Şifa Rotası", ["plaj", "termal", "gol", "doga"]),
]


# ---------------------------------------------------------------- yardımcılar
def esc(s):
    return (str(s if s is not None else "")
            .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;").replace("'", "&#39;"))


def slugify(s):
    tr = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosucgiosu")
    s = str(s).translate(tr).lower()
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s


def nf(n):
    return f"{int(n):,}".replace(",", ".")


def haversine(a, b):
    R, p = 6371.0, math.pi / 180
    dlat, dlon = (b[0] - a[0]) * p, (b[1] - a[1]) * p
    h = math.sin(dlat / 2) ** 2 + math.cos(a[0] * p) * math.cos(b[0] * p) * math.sin(dlon / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def norm_name(s):
    tr = str.maketrans("çğıöşüîâû", "cgiosuiau")
    s = str(s).translate(tr).lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    s = re.sub(r"\b(milli|milli)\b", "milli", s)
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------- rota üretimi (app.js ile aynı)
def same_spot(a, b, il_name):
    na = norm_name(a[0]).replace(norm_name(il_name), "").strip()
    nb = norm_name(b[0]).replace(norm_name(il_name), "").strip()
    d = haversine((a[4], a[5]), (b[4], b[5]))
    if d > 5:
        return False
    if na == nb:
        return True
    if len(na) > 6 and len(nb) > 6 and (na in nb or nb in na):
        return True
    return d < 0.6


def nearest_path(stops, start):
    rest, path, cur = list(stops), [], start
    while rest:
        i = min(range(len(rest)), key=lambda k: haversine(cur, (rest[k][4], rest[k][5])))
        nxt = rest.pop(i)
        path.append(nxt)
        cur = (nxt[4], nxt[5])
    return path


def two_opt(path, start):
    pts = [start] + [(p[4], p[5]) for p in path]
    seq = list(range(len(pts)))

    def d(a, b):
        return haversine(pts[a], pts[b])

    improved, guard = True, 0
    while improved and guard < 40:
        improved, guard = False, guard + 1
        for i in range(1, len(seq) - 1):
            for k in range(i + 1, len(seq)):
                a, b = seq[i - 1], seq[i]
                c = seq[k]
                e = seq[k + 1] if k + 1 < len(seq) else None
                before = d(a, b) + (d(c, e) if e is not None else 0)
                after = d(a, c) + (d(b, e) if e is not None else 0)
                if after + 1e-9 < before:
                    seq[i:k + 1] = reversed(seq[i:k + 1])
                    improved = True
    return [path[i - 1] for i in seq[1:]]


def build_routes(il, pool, cat_ids):
    center = (il["lat"], il["lon"])
    used, seeds, routes = set(), [], []
    il_name = il["n"]
    for ti, (key, label, cats) in enumerate(THEMES):
        items = [p for p in pool if cat_ids[p[1]] in cats and id(p) not in used]
        if len(items) < 2:
            items = [p for p in pool if id(p) not in used]
        chosen, seed = [], None
        best = -1e18
        for p in items:
            pt = (p[4], p[5])
            score = (min(haversine(s, pt) for s in seeds) if seeds else -haversine(center, pt))
            if score > best:
                best, seed = score, p
        if seed:
            chosen.append(seed)
        tmp = [p for p in items if p is not seed and not any(same_spot(c, p, il_name) for c in chosen)]
        while tmp and len(chosen) < 5:
            bestw, bi = 1e18, None
            for k, p in enumerate(tmp):
                if any(same_spot(c, p, il_name) for c in chosen):
                    continue
                d = min(haversine((c[4], c[5]), (p[4], p[5])) for c in chosen)
                w = d + 40 if d < 2 else d
                if w < bestw:
                    bestw, bi = w, k
            if bi is None:
                break
            chosen.append(tmp.pop(bi))
        if len(chosen) < 4:
            extra = sorted((p for p in pool if id(p) not in used and p not in chosen
                            and not any(same_spot(c, p, il_name) for c in chosen)),
                           key=lambda p: haversine(center, (p[4], p[5])))
            for p in extra:
                if len(chosen) >= 4:
                    break
                chosen.append(p)
        if len(chosen) < 3:
            for p in pool:
                if len(chosen) >= 3:
                    break
                if p not in chosen:
                    chosen.append(p)
        for p in chosen:
            used.add(id(p))
        if seed:
            seeds.append((seed[4], seed[5]))
        stops = two_opt(nearest_path(chosen, center), center)
        km = max(1, round(sum(haversine((stops[i - 1][4], stops[i - 1][5]),
                                        (stops[i][4], stops[i][5])) for i in range(1, len(stops)))))
        days = min(4, max(1, round(km / 70) or 1))
        level = "Kolay" if km < 45 else ("Orta" if km < 110 else "Zor")
        routes.append({"id": f"{il['_idx']}-{ti}", "key": key, "label": label,
                       "slug": f"{il['_slug']}-{key}", "stops": stops,
                       "km": km, "days": days, "level": level})
    return routes


# ---------------------------------------------------------------- statik sayfa iskeleti
PAGE_CSS = """
:root{--ink:#1d1d1f;--ink-2:#58585d;--muted:#6e6e73;--line:#e6e6eb;--line-2:#d2d2d7;--bg:#fafafc;--accent:#c8102e;
--font:-apple-system,BlinkMacSystemFont,"SF Pro Text","Segoe UI",system-ui,Roboto,"Helvetica Neue",Arial,sans-serif}
*{box-sizing:border-box}
body{margin:0;font-family:var(--font);color:var(--ink);background:#fff;line-height:1.62;
-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
header.site{position:sticky;top:0;z-index:10;background:rgba(255,255,255,.86);
-webkit-backdrop-filter:saturate(180%) blur(20px);backdrop-filter:saturate(180%) blur(20px);
border-bottom:1px solid #e8e8ed;padding:14px 0}
.wrap{max-width:980px;margin:0 auto;padding:0 20px}
header.site .row{display:flex;align-items:center;gap:22px;flex-wrap:wrap}
header.site a{color:var(--ink);text-decoration:none;font-weight:600;letter-spacing:-.01em}
header.site nav{display:flex;gap:20px;flex-wrap:wrap;font-size:.9rem;font-weight:500}
header.site nav a{color:var(--muted)}
header.site nav a:hover{color:var(--ink)}
h1{font-size:clamp(1.6rem,3.2vw,2.15rem);line-height:1.15;letter-spacing:-.03em;margin:26px 0 10px;color:var(--ink);font-weight:700}
h2{font-size:1.12rem;margin:34px 0 10px;color:var(--ink);letter-spacing:-.01em;font-weight:650}
.crumbs{font-size:.82rem;color:var(--muted);margin-top:20px;letter-spacing:.01em}
.crumbs a{color:var(--ink-2)}
.crumbs{color:var(--muted)}
.lead{color:var(--ink-2);margin:0 0 18px;font-size:1.02rem}
.cta{display:inline-block;background:var(--accent);color:#fff;padding:12px 20px;border-radius:12px;
text-decoration:none;font-weight:600;letter-spacing:-.01em;margin:10px 0 6px}
.cta:hover{background:#a80d27;text-decoration:none}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin:14px 0 0;padding:0;list-style:none}
.grid li{background:#fff;border:1px solid var(--line);border-radius:14px;padding:12px 14px;font-size:.92rem}
.grid li b{display:block;color:var(--ink);font-weight:600}
.grid li span{color:var(--muted);font-size:.82rem}
table{border-collapse:collapse;width:100%;font-size:.92rem;margin-top:6px}
th,td{text-align:left;padding:11px 10px;border-bottom:1px solid #ececef;vertical-align:top}
th{color:var(--muted);font-weight:600;font-size:.78rem;letter-spacing:.04em;text-transform:uppercase;border-bottom:1px solid var(--line)}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0 0;padding:0;list-style:none}
.chips a{display:inline-block;background:#fff;border:1px solid var(--line);border-radius:999px;
padding:8px 14px;font-size:.86rem;text-decoration:none;color:var(--ink);font-weight:500}
.chips a:hover{border-color:var(--accent);color:var(--accent);text-decoration:none}
footer.site{background:var(--bg);color:var(--muted);margin-top:56px;padding:26px 0;font-size:.86rem;
border-top:1px solid #e8e8ed}
footer.site a{color:var(--ink)}
.legal p,.legal li{color:#3a3a3c}
.note{background:var(--bg);border:1px solid var(--line);border-radius:14px;padding:12px 14px;font-size:.88rem;color:var(--muted)}
img,table,pre{max-width:100%}

/* ---- statik sayfalar: mobil / tablet uyumu ---- */
@media (max-width:700px){
  .wrap{padding:0 14px}
  body{font-size:15.5px;line-height:1.6}
  header.site{padding:10px 0}
  header.site .row{gap:8px 16px}
  header.site .row>a{font-size:1rem}
  header.site nav{gap:12px;font-size:.82rem;flex-wrap:wrap}
  header.site nav a{padding:6px 0}
  .crumbs{font-size:.78rem;margin-top:14px}
  .lead{font-size:.95rem}
  .cta{display:block;text-align:center;padding:14px 16px;margin:14px 0}
  table{display:block;width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;white-space:nowrap;font-size:.86rem}
  th,td{padding:9px 8px}
  .grid{grid-template-columns:1fr;gap:10px}
  .chips{gap:6px}
  .chips a{font-size:.82rem;padding:9px 12px;min-height:40px;display:inline-flex;align-items:center}
  footer.site{margin-top:32px;padding:18px 0;font-size:.82rem}
  .legal p,.legal li{font-size:.92rem}
  .note{font-size:.84rem}
}
@media (min-width:701px) and (max-width:1100px){
  .wrap{max-width:94%;padding:0 20px}
  h1{font-size:1.65rem}
  .grid{grid-template-columns:repeat(2,minmax(0,1fr))}
  table{font-size:.9rem}
}
"""



def page_shell(title, desc, canonical, body, rel, jsonld=None, robots="index,follow"):
    ld = f'\n<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!DOCTYPE html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="robots" content="{robots}">
<link rel="canonical" href="{canonical}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Türkiye Keşif">
<meta property="og:locale" content="tr_TR">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{SITE}/og-image.jpg">
<meta name="twitter:card" content="summary_large_image">
<link rel="stylesheet" href="{rel}assets/pages.css">{ld}
</head>
<body>
<header class="site"><div class="wrap row">
  <a href="{rel}">Türkiye Keşif</a>
  <nav aria-label="Ana menü">
    <a href="{rel}iller/">81 İl</a>
    <a href="{rel}kategori/">Kategoriler</a>
    <a href="{rel}rotalar/">Rotalar</a>
    <a href="{rel}ara/">Ara</a>
  </nav>
</div></header>
<main class="wrap">
{body}
</main>
<footer class="site"><div class="wrap">
  <p>© 2026 Türkiye Keşif — Veri: Wikidata (CC0), Türkçe Vikipedi (CC BY-SA 4.0), Natural Earth.
  <a href="{rel}gizlilik/">Gizlilik</a> · <a href="{rel}kvkk-aydinlatma/">KVKK</a> ·
  <a href="{rel}cerez-politikasi/">Çerezler</a> · <a href="{rel}kaynaklar/">Kaynaklar</a> ·
  <a href="{rel}iletisim/">İletişim</a></p>
</div></footer>
</body>
</html>"""


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------- ana akış
def main():
    template = (SRC / "template.html").read_text(encoding="utf-8")
    css = (SRC / "style.css").read_text(encoding="utf-8")
    theme = SRC / "theme-light.css"
    if theme.exists():
        css += "\n" + theme.read_text(encoding="utf-8")
    js = (SRC / "app.js").read_text(encoding="utf-8")
    tr_path = (SRC / "tr-path.txt").read_text(encoding="utf-8").strip()
    data = json.loads(DATA.read_text(encoding="utf-8"))

    ils, cats, places = data["ils"], data["cats"], data["places"]
    for c in cats:  # yazım birliği (TDK: millî)
        c["label"] = c["label"].replace("Milli Parklar", "Millî Parklar")
    cat_ids = [c["id"] for c in cats]
    n_places = len(places)

    # --- indeksler
    for i, il in enumerate(ils):
        il["_idx"] = i
        il["_slug"] = slugify(il["n"])
    by_il = {i: [] for i in range(len(ils))}
    for p in places:
        by_il[p[2]].append(p)
    pool_by_il = {i: [p for p in by_il[i] if p[4] is not None] for i in by_il}

    routes = []
    for i, il in enumerate(ils):
        routes.extend(build_routes(il, pool_by_il[i], cat_ids))
    n_routes = len(routes)

    # --- 1) SPA paketleri (dış dosya, hash'li ad → önbelleklenebilir)
    bundle = ("window.TR_PATH=" + json.dumps(tr_path) + ";\n"
              + "window.__DATA__=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
              + js)
    css_hash = hashlib.sha1(css.encode()).hexdigest()[:10]
    js_hash = hashlib.sha1(bundle.encode()).hexdigest()[:10]
    write(ROOT / "assets" / f"style.{css_hash}.css", css)
    write(ROOT / "assets" / f"app.{js_hash}.js", bundle)
    # eski paketleri temizle
    for f in (ROOT / "assets").glob("app.*.js"):
        if f.name != f"app.{js_hash}.js":
            f.unlink()
    for f in (ROOT / "assets").glob("style.*.css"):
        if f.name != f"style.{css_hash}.css":
            f.unlink()

    html = (template
            .replace("__CSSURL__", f"assets/style.{css_hash}.css")
            .replace("__JSURL__", f"assets/app.{js_hash}.js")
            .replace("__TR_PATH__", tr_path)
            .replace("__N_PLACES__", nf(n_places))
            .replace("__N_ROUTES__", nf(n_routes)))
    left = set(re.findall(r"__[A-Z_]+__", html))
    if left:
        raise SystemExit(f"Değiştirilmeyen yer tutucusu: {left}")
    write(ROOT / "index.html", html)

    # --- 2) statik sayfalar
    write(ROOT / "assets" / "pages.css", PAGE_CSS)

    il_links = "".join(
        f'<li><a href="../il/{il["_slug"]}/"><b>{esc(il["n"])}</b></a>'
        f'<span>{len(by_il[i])} kayıt · {len(il["d"])} ilçe</span></li>'
        for i, il in enumerate(ils))

    # 2a) /iller/
    body = f"""<p class="crumbs"><a href="../">Ana sayfa</a> › 81 İl</p>
<h1>Türkiye'nin 81 İli — Gezilecek Yerler ve Rotalar</h1>
<p class="lead">{len(ils)} il, {nf(sum(len(il['d']) for il in ils))} ilçe, {nf(n_places)} keşif kaydı ve {nf(n_routes)} hazır rota.</p>
<ul class="grid">{il_links}</ul>"""
    write(ROOT / "iller" / "index.html",
          page_shell("81 İl Gezi Rehberi — İlçeler, Yerler ve Rotalar | Türkiye Keşif",
                     f"Türkiye'nin 81 ili için gezilecek yerler, ilçeler, hazır rotalar ve hava durumu. {nf(n_places)} keşif kaydı.",
                     f"{SITE}/iller/", body, "../",
                     {"@context": "https://schema.org", "@type": "ItemList", "name": "Türkiye'nin 81 ili",
                      "itemListElement": [{"@type": "ListItem", "position": k + 1, "name": il["n"],
                                           "url": f"{SITE}/il/{il['_slug']}/"} for k, il in enumerate(ils)]}))

    # 2b) /kategori/ ve kategori sayfaları
    cat_cards = "".join(
        f'<li><a href="../kategori/{c["id"]}/"><b>{esc(c["label"])}</b></a>'
        f'<span>{sum(1 for p in places if p[1] == k)} kayıt</span></li>'
        for k, c in enumerate(cats))
    write(ROOT / "kategori" / "index.html",
          page_shell("Turizm Kategorileri — 15 Başlıkta Keşif | Türkiye Keşif",
                     "Antik kentler, müzeler, doğa, göller, şelaleler, mağaralar, plajlar, gastronomi ve daha fazlası.",
                     f"{SITE}/kategori/",
                     f"""<p class="crumbs"><a href="../">Ana sayfa</a> › Kategoriler</p>
<h1>15 Turizm Kategorisi</h1>
<p class="lead">Türkiye genelinde {nf(n_places)} kayıt; her kategori için il il listelenmiş statik sayfalar.</p>
<ul class="grid">{cat_cards}</ul>""", "../"))

    for k, c in enumerate(cats):
        lst = sorted([p for p in places if p[1] == k], key=lambda p: (-(p[4] is not None), p[0]))
        rows = "".join(
            f'<tr><td><a href="../il/{ils[p[2]]["_slug"]}/">{esc(ils[p[2]]["n"])}</a></td>'
            f'<td>{esc(p[3] or "—")}</td><td>{esc(p[0])}</td>'
            f'<td>{"<a href=\"" + str(f"https://www.google.com/maps/search/?api=1&query={p[4]},{p[5]}") + "\" target=\"_blank\" rel=\"noopener noreferrer\">Harita</a>" if p[4] is not None else "konum yok"}</td></tr>'
            for p in lst[:150])
        body = f"""<p class="crumbs"><a href="../../">Ana sayfa</a> › <a href="../">Kategoriler</a> › {esc(c["label"])}</p>
<h1>{esc(c["label"])} — {nf(len(lst))} Kayıt</h1>
<p class="lead">Türkiye genelinde {nf(len(lst))} {esc(c["label"].lower())} kaydı; {nf(sum(1 for p in lst if p[4] is not None))} tanesi haritada doğrulanmış koordinatla listeleniyor.</p>
<p><a class="cta" href="../../#/kategori/{c["id"]}">Uygulamada keşfet</a></p>
<table><thead><tr><th>İl</th><th>İlçe</th><th>Ad</th><th>Konum</th></tr></thead><tbody>{rows}</tbody></table>
<p class="note">Listede ilk 150 kayıt gösteriliyor. Tümü ve filtreler uygulamada.</p>"""
        write(ROOT / "kategori" / c["id"] / "index.html",
              page_shell(f"{c['label']} — {nf(len(lst))} Kayıt, İl İl Liste | Türkiye Keşif",
                         f"{nf(len(lst))} {c['label'].lower()} kaydı; il, ilçe ve harita bağlantılarıyla.",
                         f"{SITE}/kategori/{c['id']}/", body, "../../",
                         {"@context": "https://schema.org", "@type": "ItemList", "name": c["label"],
                          "numberOfItems": len(lst)}))

    # 2c) /rotalar/ ve rota sayfaları
    route_rows = ""
    for r in routes:
        il = ils[int(r["id"].split("-")[0])]
        route_rows += (f'<tr><td><a href="../il/{il["_slug"]}/">{esc(il["n"])}</a></td>'
                       f'<td><a href="../rota/{r["slug"]}/">{esc(r["label"])}</a></td>'
                       f'<td>{r["km"]} km</td><td>{r["days"]} gün</td><td>{r["level"]}</td>'
                       f'<td>{len(r["stops"])}</td></tr>')
    write(ROOT / "rotalar" / "index.html",
          page_shell(f"{nf(n_routes)} Hazır Gezi Rotası — 81 İl, 5 Tema | Türkiye Keşif",
                     f"Her il için 5 tema: tarih, doğa, inanç, lezzet, deniz. {nf(n_routes)} rota, durak durak harita bağlantılı.",
                     f"{SITE}/rotalar/",
                     f"""<p class="crumbs"><a href="../">Ana sayfa</a> › Rotalar</p>
<h1>{nf(n_routes)} Hazır Gezi Rotası</h1>
<p class="lead">81 ilin her biri için 5 tema: Tarih ve Kültür, Doğa ve Manzara, İnanç ve Miras, Lezzet Durakları, Deniz ve Şifa.</p>
<table><thead><tr><th>İl</th><th>Rota</th><th>Mesafe</th><th>Süre</th><th>Zorluk</th><th>Durak</th></tr></thead><tbody>{route_rows}</tbody></table>""",
                     "../"))

    cat_label = {c["id"]: c["label"] for c in cats}
    for r in routes:
        idx = int(r["id"].split("-")[0])
        il = ils[idx]
        stops = "".join(
            f'<tr><td>{n + 1}</td><td>{esc(s[0])}</td><td>{esc(cat_label.get(cat_ids[s[1]], ""))}</td>'
            f'<td>{esc(s[3] or il["n"])}</td>'
            f'<td><a href="https://www.google.com/maps/search/?api=1&query={s[4]},{s[5]}" target="_blank" rel="noopener noreferrer">Haritada</a></td></tr>'
            for n, s in enumerate(r["stops"]))
        body = f"""<p class="crumbs"><a href="../../">Ana sayfa</a> › <a href="../">Rotalar</a> › <a href="../../il/{il["_slug"]}/">{esc(il["n"])}</a> › {esc(r["label"])}</p>
<h1>{esc(il["n"])} — {esc(r["label"])}</h1>
<p class="lead">{esc(il["r"])} Bölgesi · {r["km"]} km · {r["days"]} gün · {r["level"]} · {len(r["stops"])} durak</p>
<p><a class="cta" href="../../#/il/{il["_slug"]}">Rotayı uygulamada başlat</a></p>
<h2>Duraklar</h2>
<table><thead><tr><th>#</th><th>Durak</th><th>Kategori</th><th>İlçe</th><th>Konum</th></tr></thead><tbody>{stops}</tbody></table>
<h2>Bu ildeki diğer rotalar</h2>
<ul class="chips">{"".join(f'<li><a href="../{o["slug"]}/">{esc(o["label"])}</a></li>' for o in routes if o["id"].split("-")[0] == str(idx) and o["slug"] != r["slug"])}</ul>"""
        write(ROOT / "rota" / r["slug"] / "index.html",
              page_shell(f"{il['n']} {r['label']} — {r['km']} km, {len(r['stops'])} Durak | Türkiye Keşif",
                         f"{il['n']} için {r['label'].lower()}: {', '.join(s[0] for s in r['stops'][:4])}. {r['km']} km, {r['days']} gün.",
                         f"{SITE}/rota/{r['slug']}/", body, "../../",
                         {"@context": "https://schema.org", "@type": "TouristTrip",
                          "name": f"{il['n']} — {r['label']}",
                          "touristType": "Kültür ve doğa gezisi",
                          "itinerary": {"@type": "ItemList", "itemListElement": [
                              {"@type": "ListItem", "position": n + 1, "item":
                               {"@type": "TouristAttraction", "name": s[0],
                                "geo": {"@type": "GeoCoordinates", "latitude": s[4], "longitude": s[5]},
                                "address": {"@type": "PostalAddress", "addressLocality": s[3] or il["n"],
                                            "addressRegion": il["n"], "addressCountry": "TR"}}}
                              for n, s in enumerate(r["stops"])]}}))

    # 2d) il sayfaları
    for i, il in enumerate(ils):
        lst = sorted(by_il[i], key=lambda p: (-(p[4] is not None), p[0]))
        il_routes = [r for r in routes if r["id"].split("-")[0] == str(i)]
        cat_counts = {}
        for p in by_il[i]:
            cat_counts[p[1]] = cat_counts.get(p[1], 0) + 1
        chips = "".join(f'<li><a href="../../kategori/{cat_ids[k]}/">{esc(cats[k]["label"])} ({v})</a></li>'
                        for k, v in sorted(cat_counts.items(), key=lambda kv: -kv[1]))
        route_chips = "".join(f'<li><a href="../../rota/{r["slug"]}/">{esc(r["label"])} · {r["km"]} km</a></li>'
                              for r in il_routes)
        rows = "".join(
            f'<tr><td>{esc(p[0])}</td><td>{esc(cat_label.get(cat_ids[p[1]], ""))}</td>'
            f'<td>{esc(p[3] or "—")}</td>'
            f'<td>{"<a href=\"" + str(f"https://www.google.com/maps/search/?api=1&query={p[4]},{p[5]}") + "\" target=\"_blank\" rel=\"noopener noreferrer\">Haritada</a>" if p[4] is not None else "<span>konum yok</span>"}</td></tr>'
            for p in lst[:120])
        districts = "".join(f'<li><b>{esc(d["n"])}</b><span>{nf(len(d.get("k", [])))} köy · {nf(len(d.get("m", [])))} mahalle</span></li>'
                            for d in il["d"][:40])
        body = f"""<p class="crumbs"><a href="../../">Ana sayfa</a> › <a href="../">81 İl</a> › {esc(il["n"])}</p>
<h1>{esc(il["n"])} Gezilecek Yerler — {nf(len(by_il[i]))} Nokta</h1>
<p class="lead">{esc(il["r"])} Bölgesi · {len(il["d"])} ilçe · {nf(sum(len(d.get("k", [])) + len(d.get("m", [])) for d in il["d"]))} köy/mahalle ·
{nf(sum(1 for p in by_il[i] if p[4] is not None))} konumu doğrulanmış keşif noktası · {len(il_routes)} hazır rota.</p>
<p><a class="cta" href="../../#/il/{il["_slug"]}">{esc(il["n"])} keşif sayfasını aç</a></p>

<h2>Kategoriler</h2>
<ul class="chips">{chips}</ul>

<h2>Hazır rotalar</h2>
<ul class="chips">{route_chips}</ul>

<h2>Keşif noktaları</h2>
<table><thead><tr><th>Ad</th><th>Kategori</th><th>İlçe</th><th>Konum</th></tr></thead><tbody>{rows}</tbody></table>
<p class="note">Listede ilk 120 kayıt var ({nf(len(lst))} kaydın tamamı uygulamada, filtrelerle).</p>

<h2>İlçeler</h2>
<ul class="grid">{districts}</ul>

<h2>Diğer iller</h2>
<ul class="grid">{il_links}</ul>"""
        write(ROOT / "il" / il["_slug"] / "index.html",
              page_shell(f"{il['n']} Gezilecek Yerler — {len(by_il[i])} Nokta ve {len(il_routes)} Rota | Türkiye Keşif",
                         f"{il['n']} ilinde {len(by_il[i])} keşif kaydı, {len(il['d'])} ilçe ve {len(il_routes)} hazır gezi rotası. Haritada doğrulanmış konumlar.",
                         f"{SITE}/il/{il['_slug']}/", body, "../../",
                         {"@context": "https://schema.org", "@type": "ItemList",
                          "name": f"{il['n']} gezilecek yerler",
                          "itemListElement": [{"@type": "ListItem", "position": n + 1, "name": p[0]}
                                              for n, p in enumerate(lst[:50])]}))

    # 2e) arama sayfası (statik)
    write(ROOT / "ara" / "index.html",
          page_shell("Ara — 5.882 Keşif Kaydı İçinde | Türkiye Keşif",
                     "İl, ilçe, köy veya gezilecek yer ara. Arama uygulamada filtrelerle çalışır.",
                     f"{SITE}/ara/",
                     """<p class="crumbs"><a href="../">Ana sayfa</a> › Ara</p>
<h1>Ara</h1>
<p class="lead">İl, ilçe, köy veya gezilecek yer adı yazın.</p>
<form action="../index.html" method="get" onsubmit="location.href='../#/kesfet?q='+encodeURIComponent(this.q.value);return false">
  <label for="q">Arama</label><br>
  <input id="q" name="q" type="search" placeholder="ör. Sümela, Göbeklitepe, Kaş" style="height:44px;width:min(420px,100%);border:1px solid #cbd8e6;border-radius:10px;padding:0 12px">
  <button class="cta" type="submit">Ara</button>
</form>""", "../"))

    # 2f) yasal sayfalar
    legal = {
        "kvkk-aydinlatma": ("KVKK Aydınlatma Metni", """<p class="crumbs"><a href="../">Ana sayfa</a> › KVKK Aydınlatma</p>
<h1>KVKK Aydınlatma Metni</h1>
<p class="lead">6698 sayılı Kişisel Verilerin Korunması Kanunu m.10 kapsamında bilgilendirme.</p>
<div class="legal">
<h2>Veri sorumlusu</h2>
<p>Türkiye Keşif (kişisel, ticari olmayan açık kaynak proje). İletişim: <a href="../iletisim/">iletişim sayfası</a>.</p>
<h2>İşlenen veriler</h2>
<ul>
<li><b>Favori listesi:</b> Tarayıcınızın localStorage alanında saklanır; sunucuya gönderilmez. Giriş yaparsanız (isteğe bağlı) e-posta adresiniz ve favori kayıtlarınız Supabase üzerinde saklanır.</li>
<li><b>E-posta adresi:</b> Yalnızca giriş/üyelik tercih edildiğinde, tek kullanımlık giriş bağlantısı göndermek ve favorilerinizi hesabınıza bağlamak için işlenir.</li>
<li><b>Teknik veriler:</b> Barındırma sağlayıcısı GitHub Pages, erişim loglarını kendi politikasına göre tutar. Site kendi çerezini kullanmaz.</li>
</ul>
<h2>Aktarımlar (üçüncü taraflar)</h2>
<ul>
<li><b>Open-Meteo</b> (İsviçre): hava durumu için il koordinatı ve IP adresiniz iletilir.</li>
<li><b>Google Maps</b>: "Konuma git / Yol tarifi" bağlantılarına tıkladığınızda Google'a yönlendirilirsiniz.</li>
<li><b>Supabase</b> (AB — Frankfurt): yalnızca giriş yaparsanız e-posta ve favori kaydınız.</li>
</ul>
<h2>Amaç ve hukuki sebep</h2>
<p>Veriler, hizmetin sunulması (KVKK m.5/2-c, sözleşmenin ifası) ve açık rızanız (giriş tercihi) hukuki sebeplerine dayanır. Pazarlama amacıyla işlenmez, üçüncü kişilerle paylaşılmaz.</p>
<h2>Saklama süresi</h2>
<p>Yerel favoriler siz silene kadar tarayıcınızda kalır. Hesap verileri, hesabınızı silmeniz hâlinde en geç 30 gün içinde silinir.</p>
<h2>Haklarınız (KVKK m.11)</h2>
<p>Verilerinize erişme, düzeltme, silme, işlemeye itiraz etme ve zararın giderilmesini talep etme haklarınız vardır.
Erişme ve taşınabilirlik hakkınızı <b>Hesabım</b> sayfasındaki <a href="../hesabim/">“Verilerimi indir”</a> düğmesiyle (JSON),
silme hakkınızı “Hesap verilerimi sil” düğmesiyle beklemeden kullanabilirsiniz. E-posta kaydının silinmesi için
iletişim sayfasından yazmanız yeterlidir (en geç 30 gün).</p>
<h2>Çerezler</h2>
<p>Site zorunlu olmayan çerez kullanmaz; ayrıntı için <a href="../cerez-politikasi/">Çerez Politikası</a>.</p>
</div>"""),
        "gizlilik": ("Gizlilik Politikası", """<p class="crumbs"><a href="../">Ana sayfa</a> › Gizlilik</p>
<h1>Gizlilik Politikası</h1>
<p class="lead">Hangi veriyi, neden ve ne kadar süreyle işlediğimizin özeti.</p>
<div class="legal">
<h2>Kısa özet</h2>
<ul>
<li>Hesap açmadan da tüm keşif kayıtları, rotalar ve harita bağlantıları çalışır.</li>
<li>Favoriler varsayılan olarak <b>yalnızca tarayıcınızda</b> tutulur.</li>
<li>Reklam, izleme pikseli veya üçüncü taraf analitik kullanılmaz.</li>
<li>Hava durumu özelliği Open-Meteo'ya il koordinatı gönderir.</li>
</ul>
<h2>Hesap (isteğe bağlı)</h2>
<p>E-posta ile giriş yaparsanız Supabase (AB/Frankfurt) üzerinde bir kullanıcı kaydı oluşur. Favorileriniz satır düzeyi güvenlik (RLS) ile yalnızca sizin hesabınıza görünür; başka kullanıcılar okuyamaz.</p>
<h2>Veri silme</h2>
<p>Hesabınızı ve verilerinizi silmek için iletişim sayfasından yazın; 30 gün içinde silinir. Yerel favorileri tarayıcı ayarlarından temizleyebilirsiniz.</p>
<h2>Çocuklar</h2>
<p>Site 13 yaş altındaki kullanıcılara yönelik değildir; bu yaş grubundan bilerek veri toplanmaz.</p>
<h2>Değişiklikler</h2>
<p>Politika güncellendiğinde bu sayfada yayımlanır. Son güncelleme: """ + TODAY + """</p>
</div>"""),
        "cerez-politikasi": ("Çerez Politikası", """<p class="crumbs"><a href="../">Ana sayfa</a> › Çerezler</p>
<h1>Çerez ve Yerel Depolama Politikası</h1>
<p class="lead">Site çerez kullanmaz; tarayıcıda yalnızca işlevsel yerel kayıtlar tutar.</p>
<div class="legal">
<table>
<thead><tr><th>Ad</th><th>Tür</th><th>Amaç</th><th>Süre</th></tr></thead>
<tbody>
<tr><td>tk-favs-v2</td><td>localStorage</td><td>Favori yerlerin listesi</td><td>Siz silene kadar</td></tr>
<tr><td>tk-weather-v2</td><td>localStorage</td><td>Hava durumu yanıtını 3 saat önbelleğe alır (istek sayısını azaltır)</td><td>3 saat</td></tr>
<tr><td>tk-consent-v1</td><td>localStorage</td><td>Bu bilgilendirmeyi gördüğünüzü hatırlar</td><td>Kalıcı</td></tr>
<tr><td>tk-auth-v1</td><td>localStorage</td><td>Giriş yaptıysanız oturum jetonu</td><td>Oturum / 1 saat (yenilenir)</td></tr>
<tr><td>tk-progress-v1</td><td>localStorage</td><td>Başlattığınız rotalarda kaldığınız durak</td><td>Siz silene kadar</td></tr>
<tr><td>tk-done-v1</td><td>localStorage</td><td>Tamamladığınız rotaların listesi</td><td>Siz silene kadar</td></tr>
</tbody></table>
<p>Bunlar "çerez" değil, tarayıcı yerel depolama kayıtlarıdır ve sunucuya gönderilmez. Zorunlu olmadıkları için onay şeridinde
"Yalnızca zorunlu" seçeneğiyle hava durumu isteklerini kapatabilirsiniz.</p>
<h2>Üçüncü taraf</h2>
<p>Hava durumu verisi Open-Meteo'dan alınır (istek sırasında IP ve koordinat iletilir). Harita bağlantıları Google Maps'te açılır.</p>
</div>"""),
        "kaynaklar": ("Kaynaklar ve Lisanslar", """<p class="crumbs"><a href="../">Ana sayfa</a> › Kaynaklar</p>
<h1>Veri Kaynakları ve Lisanslar</h1>
<p class="lead">Sitedeki kayıtların nereden geldiği ve hangi lisansla kullanıldığı.</p>
<div class="legal">
<ul>
<li><b>Wikidata</b> — CC0 1.0 (kamu malı). Mekân adları, koordinatlar, tür bilgileri.</li>
<li><b>Türkçe Vikipedi</b> — CC BY-SA 4.0. Millî park, tabiat parkı/anıtı, koruma alanı ve müze listeleri; metinler uyarlanmıştır.</li>
<li><b>Natural Earth</b> — kamu malı. Türkiye sınır geometrisi.</li>
<li><b>İl sınırı poligonları</b> — açık veri (il/ilçe ataması için).</li>
<li><b>Open-Meteo</b> — hava durumu API'si (CC BY 4.0 veri).</li>
<li><b>Envanter rakamları</b> — TÜİK, TÜRKPATENT, Kültür ve Turizm Bakanlığı derlemeleri.</li>
</ul>
<h2>Yazılım</h2>
<p>Site kodu MIT lisansı ile yayımlanır: <a href="https://github.com/xharunkoca/turkiye-kesif" target="_blank" rel="noopener noreferrer">github.com/xharunkoca/turkiye-kesif</a>.</p>
<h2>Doğruluk</h2>
<p>Koordinatı doğrulanamayan kayıtlar "konum yok" etiketiyle gösterilir ve harita bağlantısı ada göre arama yapar.
Hatalı gördüğünüz bir kaydı iletişim sayfasından bildirebilirsiniz.</p>
</div>"""),
        "iletisim": ("İletişim", """<p class="crumbs"><a href="../">Ana sayfa</a> › İletişim</p>
<h1>İletişim</h1>
<p class="lead">Hatalı kayıt bildirimi, veri talebi veya KVKK başvurusu için.</p>
<div class="legal">
<p>E-posta: <b>turkiyekesif [at] example.com</b> (adres, proje deposunda güncel tutulmaktadır).</p>
<p>Konu başlıkları: <i>Hatalı kayıt</i>, <i>Veri talebi</i>, <i>KVKK başvurusu</i>, <i>İş birliği</i>.</p>
<h2>Hatalı kayıt bildirimi</h2>
<p>Kaydın adını, ilini ve doğru konumu (varsa Google Maps bağlantısı) yazmanız yeterli. Doğrulanan düzeltmeler bir sonraki veri
güncellemesinde yayına alınır.</p>
<h2>Kaynak kod</h2>
<p><a href="https://github.com/xharunkoca/turkiye-kesif/issues" target="_blank" rel="noopener noreferrer">GitHub Issues</a> üzerinden de bildirim yapabilirsiniz.</p>
</div>"""),
    }
    for slug, (title, body) in legal.items():
        write(ROOT / slug / "index.html",
              page_shell(f"{title} | Türkiye Keşif", f"{title} — Türkiye Keşif.",
                         f"{SITE}/{slug}/", body, "../"))

    # 2f-2) hesap sayfası (kişisel — indekslenmez, SPA'ya devreder)
    write(ROOT / "hesabim" / "index.html",
          page_shell("Hesabım — Favoriler ve Rota İlerlemesi | Türkiye Keşif",
                     "Giriş yaparak favorilerinizi ve rota ilerlemenizi tüm cihazlarınızda eşitleyin.",
                     f"{SITE}/hesabim/",
                     """<p class="crumbs"><a href="../">Ana sayfa</a> › Hesabım</p>
<h1>Hesabım</h1>
<p class="lead">Favorileriniz ve rota ilerlemeniz giriş yaptığınızda tüm cihazlarınızda aynı olur.</p>
<div class="legal">
<ul>
<li><b>Şifre yok:</b> e-posta adresinize tek kullanımlık giriş bağlantısı gönderilir (1 saat geçerli).</li>
<li><b>Favoriler:</b> giriş yapmadan da çalışır; giriş yapınca hesabınıza bağlanır.</li>
<li><b>Rota ilerlemesi:</b> başladığınız rota kaldığı duraktan devam eder.</li>
<li><b>Haklarınız:</b> verilerinizi JSON olarak indirebilir, tek tuşla silebilirsiniz (KVKK m.11).</li>
</ul>
<p>Hesap ekranı uygulama içinde açılır:</p>
<p><a class="cta" href="../#/hesabim">Hesabıma git</a></p>
<h2>Ayrıntılı bilgi</h2>
<ul>
<li><a href="../kvkk-aydinlatma/">KVKK Aydınlatma Metni</a></li>
<li><a href="../gizlilik/">Gizlilik Politikası</a></li>
<li><a href="../cerez-politikasi/">Çerez ve Yerel Depolama Politikası</a></li>
</ul>
</div>""", "../", robots="noindex,follow"))

    # 2g) 404
    write(ROOT / "404.html", f"""<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Sayfa bulunamadı — Türkiye Keşif</title>
<meta name="robots" content="noindex"><link rel="stylesheet" href="/turkiye-kesif/assets/pages.css"></head>
<body><main class="wrap"><h1>Sayfa bulunamadı</h1>
<p class="lead">Aradığınız sayfa taşınmış olabilir. Aşağıdan devam edebilirsiniz:</p>
<ul class="chips">
<li><a href="/turkiye-kesif/">Ana sayfa</a></li>
<li><a href="/turkiye-kesif/iller/">81 İl</a></li>
<li><a href="/turkiye-kesif/rotalar/">Rotalar</a></li>
<li><a href="/turkiye-kesif/kategori/">Kategoriler</a></li>
<li><a href="/turkiye-kesif/ara/">Ara</a></li>
</ul></main></body></html>""")

    # --- 3) sitemap
    urls = [(f"{SITE}/", "1.0"), (f"{SITE}/iller/", "0.9"), (f"{SITE}/kategori/", "0.9"),
            (f"{SITE}/rotalar/", "0.9"), (f"{SITE}/ara/", "0.5")]
    urls += [(f"{SITE}/il/{il['_slug']}/", "0.8") for il in ils]
    urls += [(f"{SITE}/kategori/{c['id']}/", "0.7") for c in cats]
    urls += [(f"{SITE}/rota/{r['slug']}/", "0.6") for r in routes]
    urls += [(f"{SITE}/{slug}/", "0.3") for slug in legal]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, pri in urls:
        sm.append(f"  <url><loc>{u}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>{pri}</priority></url>")
    sm.append("</urlset>")
    write(ROOT / "sitemap.xml", "\n".join(sm) + "\n")

    total_kb = sum(f.stat().st_size for f in ROOT.rglob("*.html")) / 1024
    print(f"index.html {len(html) / 1024:.0f} KB · app bundle {len(bundle) / 1024:.0f} KB · "
          f"css {len(css) / 1024:.0f} KB")
    print(f"statik sayfa: {len(ils)} il + {len(cats)} kategori + {len(routes)} rota + "
          f"{len(legal)} yasal + {5} dizin = {len(ils) + len(cats) + len(routes) + len(legal) + 5} sayfa, "
          f"toplam {total_kb / 1024:.1f} MB")
    print(f"sitemap: {len(urls)} URL · {n_places} kayıt · {n_routes} rota")


if __name__ == "__main__":
    main()
