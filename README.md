# Türkiye Keşif

**81 il · 15 turizm kategorisi · 3.269 doğrulanmış keşif noktası · 45.060 köy/mahalle · 405 gezi rotası**

🔗 **Canlı site:** <https://xharunkoca.github.io/turkiye-kesif/>

Tek dosyalık (bağımlılıksız) keşif rehberi. `index.html` içinde CSS, JavaScript, veri ve
tüm görseller base64 olarak gömülüdür — dosyayı çift tıklayıp açmak yeterlidir, internet
bağlantısı gerekmez (harici harita/kaynak bağlantıları hariç).

![Ana sayfa](docs/screenshots/01-ana-sayfa.jpg)

## Kapsam

| Öğe | Adet |
|---|---|
| İl | **81** |
| İlçe / belde | **1.004** |
| Köy | **25.206** |
| Mahalle | **19.854** |
| Toplam kırsal yerleşim | **45.060** |
| Doğrulanmış turistik nokta | **3.271** kayıt / **3.269** tekil yer |
| Turizm kategorisi | **15** |
| Gezi rotası | **405** (her ile 5 tema) |

### 15 kategori ve envanterdeki kayıt sayısı

| # | Kategori | Kayıt |
|---|---|---|
| 1 | Antik Kentler | 455 |
| 2 | Müzeler | 235 |
| 3 | Doğa ve Milli Parklar | 72 |
| 4 | Tarihi Yapılar | 643 |
| 5 | Göller | 336 |
| 6 | Şelaleler | 59 |
| 7 | Mağaralar | 155 |
| 8 | Vadiler ve Kanyonlar | 186 |
| 9 | Plajlar ve Kıyılar | 67 |
| 10 | Gastronomi ve Yöresel | 123 |
| 11 | Yaylalar ve Kamp | 104 |
| 12 | Dini Yapılar ve İnanç | 486 |
| 13 | Kültür ve Sanat | 192 |
| 14 | Kaplıcalar ve Termal | 56 |
| 15 | Çarşılar ve Pazarlar | 102 |

Her kategori kartında referans istatistikleri ("genel kabul gören antik kent sayısı",
"Mavi Bayraklı plaj sayısı", "tescilli taşınmaz sayısı" vb.) `env` alanında tutulur ve
kategori sayfasında envanter şeridi olarak gösterilir.

## Ekranlar

| Adres | İçerik |
|---|---|
| `#/` | Ana sayfa: arama, 15 kategori şeridi, popüler şehirler, harita paneli, rotalar, mevsim kartları, istatistik bandı |
| `#/kesfet` | Tüm mekânlar: il / kategori / metin filtreleri, sayfalama |
| `#/iller` | 81 ilin plaka kodlu kart ızgarası |
| `#/il/<slug>` | İl sayfası: 5 rota, kategori çipleri, mekân kartları, ilçe akordeonu (köy + mahalle listeleri) |
| `#/ilce/<il-slug>/<ilce-slug>` | İlçe sayfası: yerleşim birimleri, ilçedeki keşif noktaları, komşu ilçe bağlantıları |
| `#/rotalar` | 405 rota; il ve tema filtreli |
| `#/kategori/<id>` | Kategori sayfası: açıklama, envanter şeridi, tüm Türkiye sonuçları |

Mekân kartlarında ad, tür, ilçe/il, "doğrulandı" işareti ve **"Konuma git"** butonu
(kartın altında, Google Maps'e koordinatla gider) bulunur. Karta tıklayınca detay
penceresi açılır: koordinat, plaka, yakındaki keşifler, favori ve kaynak bağlantısı.
Rota penceresinde duraklar numaralı bir **mini güzergâh haritası** üzerinde gösterilir.

<p align="center">
  <img src="docs/screenshots/02-rota.jpg" width="49%" alt="Rota penceresi ve mini güzergâh haritası">
  <img src="docs/screenshots/03-harita.jpg" width="49%" alt="81 il haritası">
</p>
<p align="center">
  <img src="docs/screenshots/04-ilce.jpg" width="98%" alt="İlçe sayfası">
</p>

## Kurulum

Depoyu klonlayıp `index.html`'i tarayıcıda açmanız yeterli:

```bash
git clone https://github.com/xharunkoca/turkiye-kesif.git
cd turkiye-kesif
open index.html          # macOS   (Windows: start index.html / Linux: xdg-open index.html)
```

Yerel sunucu tercih edilirse:

```bash
python3 -m http.server 8000
# http://localhost:8000
```

## Derleme

`index.html` kaynaklardan üretilir. Yeniden derlemek için:

```bash
cd data && python3 build_data.py     # ≈40 sn → data/turkiye-data.json
cd .. && python3 build.py            # → index.html
```

- `build_data.py` ham Wikidata kayıtlarını (`data/raw/`) işler; bu klasör depoya
  eklenmez (≈45 MB). Sıfırdan veri toplamak için `data/fetch*.py` betikleri çalıştırılır.
- `build.py` yer tutucuları doldurur: `__CSS__`, `__JS__`, `__DATAJSON__`, `__TRPATH__`
  ve görseller için `__IMG_*__`. Doldurulmamış yer tutucu kalırsa uyarı verir.

## Dosya düzeni

```
turkiye-kesif/
├── index.html          # ÜRETİLEN tek dosya (≈2,2 MB, her şey gömülü)
├── build.py            # derleyici: şablon + css + js + veri + görseller → index.html
├── src/
│   ├── template.html   # işaretleme + ikon sprite + yer tutucular
│   ├── style.css       # tema (referans görsel dil + v2/v3 bileşenleri)
│   ├── app.js          # yönlendirici, arama, rotalar, modaller, favoriler
│   └── tr-path.txt     # Türkiye silueti (Natural Earth 10m, projeksiyona çevrilmiş)
├── data/
│   ├── build_data.py   # ham Wikidata kayıtları → turkiye-data.json
│   ├── turkiye-data.json
│   └── fetch*.py       # Wikidata SPARQL toplayıcıları (önbellekli)
├── assets/img/         # 10 JPEG (hero, 5 şehir, rota, 3 mevsim)
├── docs/screenshots/   # README görselleri
└── .github/workflows/pages.yml  # GitHub Pages dağıtımı
```

## GitHub Pages

Depoya her `push` sonrası site otomatik yayınlanır:

1. **Settings → Pages → Build and deployment → Source: GitHub Actions**
2. `main` dalına push edin (veya Actions sekmesinden *GitHub Pages'e yayınla* iş akışını çalıştırın)
3. Site adresi: `https://xharunkoca.github.io/turkiye-kesif/`

İş akışı yayından önce veriyi doğrular (81 il / 15 kategori), ardından `index.html`
kaynaklarla güncel mi diye `build.py` çıktısını karşılaştırır.

## Veri kaynakları ve doğrulama

- **Wikidata** (CC0): il/ilçe/köy/mahalle ilişkileri ve koordinatlı turistik noktalar
  (SPARQL, sonuçlar `data/raw/` içinde önbelleklenir). Sınıf eşlemeleri: antik kent,
  höyük, kale, müze, millî park, göl, şelale, mağara, kanyon, plaj, cami/külliye,
  hamam, kervansaray, bedesten/çarşı…
- **Natural Earth 10m** (kamu malı): Türkiye sınır geometrisi.
- Kategori envanter sayıları resmî/derleme istatistiklerdir (TÜİK, Kültür ve Turizm
  Bakanlığı, TÜRÇEV, TÜRKPATENT vb.).

Kalite kuralları: yalnızca koordinatı Türkiye sınır kutusunda olan kayıtlar; il
merkezine 220 km'den uzak aykırı koordinatlar atılır; aynı ad + 3 km yakınlık
yinelenen kayıt sayılır; jenerik adlar ("Bedesten", "Tarihî Çarşı"…) elenir; köy ve
mahalleler en yakın ilçeye (≤22 km) bağlanır.

## Notlar

- Arayüz tamamen Türkçedir; tipografi ve renk paleti referans tasarımdan gelir
  (lacivert `#0a2c52`, kırmızı `#e11d2e`, sarı `#ffd21e`).
- Favoriler `localStorage` (`tk-favs-v2`), rota kayıtları `tk-routes-v2` anahtarında.
- Dosya `file://` ile açıldığında da çalışır; GitHub Pages'te harici bağlantılar
  (Google Maps, Wikidata) normal şekilde açılır.

## Lisans

Kod ve üretilen görseller [MIT](LICENSE). Veri: Wikidata (CC0 1.0), Natural Earth (kamu malı).
