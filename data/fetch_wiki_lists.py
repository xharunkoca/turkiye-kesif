#!/usr/bin/env python3
"""Vikipedi'nin resmî listelerinden yer adları + (varsa) koordinat toplar.

Kaynak sayfalar:
  - Türkiye'deki millî parklar listesi
  - Türkiye'deki tabiat parkları listesi
  - Türkiye'deki tabiat anıtları listesi
  - Türkiye'deki tabiat koruma alanları listesi
  - Türkiye'deki müzeler listesi (illere göre bölümler)
"""
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request

from bs4 import BeautifulSoup

RAW = pathlib.Path(__file__).parent / "raw"
RAW.mkdir(exist_ok=True)
UA = {"User-Agent": "TurkiyeKesif/1.0 (tourism demo; educational)"}
API = "https://tr.wikipedia.org/w/api.php"

ALIAS = {"Afyon": "Afyonkarahisar", "İçel": "Mersin", "Urfa": "Şanlıurfa",
         "Maraş": "Kahramanmaraş", "Antep": "Gaziantep", "Hakkâri": "Hakkari"}


def api(params, tries=4):
    url = API + "?" + urllib.parse.urlencode(params)
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            body = urllib.request.urlopen(req, timeout=90).read().decode("utf-8", "replace")
            time.sleep(1.2)
            return json.loads(body)
        except Exception as e:  # noqa: BLE001
            last = e
            wait = 6 * (i + 1)
            print(f"  ! {type(e).__name__} → {wait}s bekleniyor")
            time.sleep(wait)
    raise RuntimeError(f"wiki api hatası: {last}")


def page_html(title):
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower())[:60]
    f = RAW / f"wiki_{slug}.html"
    if f.exists():
        print(f"= {title}: önbellek")
        return f.read_text()
    d = api({"action": "parse", "page": title, "prop": "text", "format": "json", "formatversion": "2"})
    f.write_text(d["parse"]["text"])
    return d["parse"]["text"]


def clean(s):
    s = re.sub(r"\[[^\]]*\]", "", s or "")
    s = s.replace("\u00a0", " ").strip(" ,;.")
    return re.sub(r"\s{2,}", " ", s).strip()


def split_ils(cell):
    """'Ağrı, Iğdır' → ['Ağrı', 'Iğdır']"""
    parts = re.split(r"\s*,\s*|\s+ve\s+", clean(cell))
    out = []
    for p in parts:
        p = ALIAS.get(p, p)
        if p:
            out.append(p)
    return out


NATURE = [
    ("Türkiye'deki millî parklar listesi", 1, 1, 2),   # (sayfa, tablo no, ad sütunu, il sütunu)
    ("Türkiye'deki tabiat parkları listesi", 1, 0, 1),
    ("Türkiye'deki tabiat anıtları listesi", 1, 0, 1),
    ("Türkiye'deki tabiat koruma alanları listesi", 1, 1, 2),
]

MUSEUM_PAGE = "Türkiye'deki müzeler listesi"


def parse_nature():
    out = []
    for title, tno, ni, ii in NATURE:
        soup = BeautifulSoup(page_html(title), "html.parser")
        tables = soup.find_all("table", class_="wikitable")
        if len(tables) <= tno:
            print(f"  ! tablo yok: {title}")
            continue
        tb = tables[tno]
        n = 0
        for tr in tb.find_all("tr")[1:]:
            cells = [clean(c.get_text(" ", strip=True)) for c in tr.find_all(["td", "th"])]
            if len(cells) <= max(ni, ii):
                continue
            name = cells[ni]
            if not name or name.lower().startswith(("toplam", "kaynak", "no")):
                continue
            ils = split_ils(cells[ii])
            if not ils:
                continue
            out.append({"name": name, "ils": ils, "cat": "doga", "src": "wikipedia"})
            n += 1
        print(f"  {title}: {n}")
    return out


def parse_museums():
    soup = BeautifulSoup(page_html(MUSEUM_PAGE), "html.parser")
    out, seen = [], set()
    heads = soup.find_all(["h2", "h3"])
    for h in heads:
        cur = clean(h.get_text(" ", strip=True))
        cur = ALIAS.get(cur, cur) if cur else None
        if not cur:
            continue
        for el in h.find_all_next():
            if el.name in ("h2", "h3"):
                break                              # sonraki bölüm
            if el.name != "li":
                continue
            if el.find_parent("ol", class_="references") or el.find_parent("ul", class_="gallery"):
                continue
            name = clean(el.get_text(" ", strip=True))
            if not name or len(name) < 4 or len(name) > 95:
                continue
            if name.lower().startswith(("kaynak", "ayrıca", "dış bağlantı")):
                continue
            k = name.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append({"name": name, "ils": [cur], "cat": "muze", "src": "wikipedia"})
    print(f"  müzeler: {len(out)}")
    return out


def coords_for(titles):
    """Başlık listesi → {title: (lat, lon)} (50'lik gruplar)."""
    res = {}
    uniq = sorted(set(titles))
    for i in range(0, len(uniq), 50):
        chunk = uniq[i:i + 50]
        d = api({"action": "query", "prop": "coordinates", "titles": "|".join(chunk),
                 "format": "json", "formatversion": "2", "redirects": "1"})
        time.sleep(0.8)
        norm = {x["from"]: x["to"] for x in d.get("query", {}).get("normalized", [])}
        red = {x["from"]: x["to"] for x in d.get("query", {}).get("redirects", [])}
        by_title = {}
        for pg in d.get("query", {}).get("pages", []):
            c = (pg.get("coordinates") or [None])[0]
            if c:
                by_title[pg["title"]] = (c["lat"], c["lon"])
        for t in chunk:
            tt = norm.get(t, t)
            tt = red.get(tt, tt)
            if tt in by_title:
                res[t] = by_title[tt]
    print(f"  koordinat bulunan: {len(res)}/{len(set(titles))}")
    return res


def names_only():
    rows = parse_nature() + parse_museums()
    (RAW / "wiki_lists_names.json").write_text(json.dumps(rows, ensure_ascii=False))
    print(f"adlar yazıldı: {len(rows)}")
    return rows


if __name__ == "__main__":
    import sys
    if sys.argv[1:] and sys.argv[1] == "names":
        names_only()
        raise SystemExit
    rows = json.loads((RAW / "wiki_lists_names.json").read_text())
    coords = coords_for([r["name"] for r in rows])
    hit = 0
    for r in rows:
        c = coords.get(r["name"])
        if c:
            r["lat"], r["lon"] = round(c[0], 5), round(c[1], 5)
            hit += 1
    (RAW / "wiki_lists.json").write_text(json.dumps(rows, ensure_ascii=False))
    nocoord = len(rows) - hit
    print(f"toplam {len(rows)} kayıt → {hit} koordinatlı, {nocoord} koordinatsız")
