#!/usr/bin/env python3
"""Türkiye Keşif — tek dosyalık site derleyicisi.

Girdi : src/template.html, src/style.css, src/app.js, src/tr-path.txt,
        data/turkiye-data.json, assets/img/*.jpg
Çıktı : index.html  (CSS, JS, veri ve görseller gömülü; çevrimdışı çalışır)

Kullanım: python3 build.py
"""
import base64
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "src"
IMG = ROOT / "assets" / "img"
DATA = ROOT / "data" / "turkiye-data.json"

IMAGES = {
    "__IMG_HERO__": "hero.jpg",
    "__IMG_ANTALYA__": "antalya.jpg",
    "__IMG_ISTANBUL__": "istanbul.jpg",
    "__IMG_IZMIR__": "izmir.jpg",
    "__IMG_MUGLA__": "mugla.jpg",
    "__IMG_NEVSEHIR__": "nevsehir.jpg",
    "__IMG_ROTA__": "rota.jpg",
    "__IMG_ILKBAHAR__": "ilkbahar.jpg",
    "__IMG_YAZ__": "yaz.jpg",
    "__IMG_SONBAHAR__": "sonbahar.jpg",
}


def data_uri(name: str) -> str:
    raw = (IMG / name).read_bytes()
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")


def main() -> None:
    html = (SRC / "template.html").read_text(encoding="utf-8")
    css = (SRC / "style.css").read_text(encoding="utf-8")
    js = (SRC / "app.js").read_text(encoding="utf-8")
    tr_path = (SRC / "tr-path.txt").read_text(encoding="utf-8").strip()
    data = json.loads(DATA.read_text(encoding="utf-8"))

    # veriyi JS'e gömülecek biçimde sıkıştır
    data_json = json.dumps(data, ensure_ascii=False, separators=(",", ":"))

    html = html.replace("__CSS__", css).replace("__JS__", js)
    html = html.replace("__DATAJSON__", data_json)
    html = html.replace("__TRPATH__", tr_path)
    html = html.replace("__TR_PATH__", tr_path)

    cache = {k: data_uri(v) for k, v in IMAGES.items()}
    for token, uri in cache.items():
        html = html.replace(token, uri)

    left = set(re.findall(r"__(?:IMG_[A-Z]+|CSS|JS|DATAJSON|TRPATH)__", html))
    if left:
        raise SystemExit(f"Değiştirilmeyen yer tutucusu kaldı: {left}")

    out = ROOT / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"index.html yazıldı — {out.stat().st_size / 1024 / 1024:.2f} MB "
          f"(veri {len(data_json) / 1024:.0f} KB, {len(data['places'])} mekân)")


if __name__ == "__main__":
    main()
