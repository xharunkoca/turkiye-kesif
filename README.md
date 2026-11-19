# Türkiye Keşif

**81 il · 15 turizm kategorisi · 5.882 keşif kaydı (4.949 konumlu) · 45.060 köy/mahalle · 405 gezi rotası · 511 statik sayfa**

🔗 **Canlı site:** <https://xharunkoca.github.io/turkiye-kesif/>

Bağımlılıksız keşif rehberi. Site **511 önceden oluşturulmuş (prerender) statik sayfadan** ve
tek sayfalık uygulamadan (`index.html` + hash yönlendirici) oluşur; sunucu tarafı yoktur,
GitHub Pages üzerinde yayınlanır.

- **İlk yükleme ≈ 23 KB HTML + 12 KB CSS + 357 KB gzip JS** (v11'de 2,26 MB tek dosyaydı)
- Mobil (4x CPU + yavaş 4G): **LCP 780 ms · CLS 0,04 · DCL 2,85 sn** (v11: 9,07 sn)
- Görseller WebP, `srcset` + `loading="lazy"` + sabit boyut (CLS ≈ 0)
- Her il / kategori / rota için **gerçek URL** (`/il/istanbul/`, `/kategori/gol/`, `/rota/istanbul-tarih/`)
  ve `sitemap.xml`'de 511 adres → arama motorları ve paylaşım önizlemeleri çalışır
- Favoriler ve rota ilerlemesi **Supabase** ile cihazlar arası eşitlenir (e-posta bağlantısıyla giriş)

![Ana sayfa](docs/screenshots/01-ana-sayfa.jpg)

## Kapsam

| Öğe | Adet |
|---|---|
| İl | **81** |
| İlçe / belde | **1.004** |
| Köy | **25.206** |
| Mahalle | **19.854** |
| Toplam kırsal yerleşim | **45.060** |
| Keşif kaydı | **5.882** kayıt |
| — konumu doğrulanmış | **4.949** |
| — konumu doğrulanmamış (adresle aranır) | **880** |
| Turizm kategorisi | **15** |
| Gezi rotası | **405** (her ile 5 tema) |

### 15 kategori ve envanterdeki kayıt sayısı

| # | Kategori | Kayıt |
|---|---|---|
| 1 | Antik Kentler | 838 |
| 2 | Müzeler | 927 |
| 3 | Doğa ve Milli Parklar | 476 |
| 4 | Tarihi Yapılar | 1.084 |
| 5 | Göller | 490 |
| 6 | Şelaleler | 64 |
| 7 | Mağaralar | 203 |
| 8 | Vadiler ve Kanyonlar | 185 |
| 9 | Plajlar ve Kıyılar | 75 |
| 10 | Gastronomi ve Yöresel | 123 |
| 11 | Yaylalar ve Kamp | 104 |
| 12 | Dini Yapılar ve İnanç | 955 |
| 13 | Kültür ve Sanat | 192 |
| 14 | Kaplıcalar ve Termal | 63 |
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
| `#/mevsim/<sezon>` | Mevsim sayfası: `ilkbahar` · `yaz` · `sonbahar` · `kis` — uygun iller, önerilen rotalar, filtreli keşifler |

Mekân kartlarında ad, tür, ilçe/il, "doğrulandı" işareti ve **"Konuma git"** butonu
(kartın altında, Google Maps'e koordinatla gider) bulunur. Karta tıklayınca detay
penceresi açılır: koordinat, plaka, yakındaki keşifler, favori ve kaynak bağlantısı.
Rota penceresinde duraklar numaralı bir **mini güzergâh haritası** üzerinde gösterilir.

### Canlı hava durumu ve seyahat puanı

İl sayfalarında [Open-Meteo](https://open-meteo.com) (anahtarsız) verisiyle 5 günlük tahmin
gösterilir: günlük ikon, en yüksek/en düşük sıcaklık, yağış olasılığı ve her gün için
**0–100 seyahat uygunluğu puanı**. Puan; fırtına/kar/yağış, aşırı sıcak-soğuk, rüzgâr ve
konfor aralığına (13–25 °C) göre hesaplanır; "en uygun gün" önerilir ve rota penceresinde
tek satır özet olarak görünür. Veriler 3 saat `localStorage`'da önbelleklenir, istek 8 saniye
içinde yanıt vermezse sessizce devre dışı kalır (site çevrimdışı da çalışır).

### Mevsim katmanı

`#/mevsim/<sezon>` sayfaları her mevsim için kategori setini, uygun illeri ve temalı
rotaları bir araya getirir; ana sayfadaki mevsim kartları bu sayfalara gider.

<p align="center">
  <img src="docs/screenshots/02-rota.jpg" width="49%" alt="Rota penceresi ve mini güzergâh haritası">
  <img src="docs/screenshots/03-harita.jpg" width="49%" alt="81 il haritası">
</p>
<p align="center">
  <img src="docs/screenshots/04-ilce.jpg" width="98%" alt="İlçe sayfası">
</p>
<p align="center">
  <img src="docs/screenshots/05-mevsim.jpg" width="49%" alt="Mevsim sayfası">
  <img src="docs/screenshots/06-hava.jpg" width="49%" alt="Hava durumu ve seyahat puanı">
</p>

## Kurulum

```bash
git clone https://github.com/xharunkoca/turkiye-kesif.git
cd turkiye-kesif
python3 build.py                 # önceden oluşturulmuş sayfaları üretir
python3 -m http.server 8000      # http://localhost:8000
```

> `index.html`'i doğrudan dosya olarak (`file://`) açmak artık önerilmez: dış CSS/JS ve
> Supabase çağrıları için bir sunucu gerekir. `python3 -m http.server` yeterlidir.

## Derleme

```bash
cd data && python3 build_data.py   # ≈40 sn → data/turkiye-data.json  (veri değiştiyse)
cd .. && python3 build.py          # → 511 sayfa + hash'li paketler + sitemap.xml
```

`build.py` çıktıları:

| Çıktı | Açıklama |
|---|---|
| `index.html` | SPA kabuğu (≈65 KB) — `<link>`/`<script src>` ile dış paketler |
| `assets/style.<hash>.css`, `assets/app.<hash>.js` | İçerik hash'li, uzun ömürlü önbellek |
| `iller/`, `kategori/<id>/`, `rotalar/`, `rota/<il>-<tema>/`, `il/<slug>/`, `ara/` | Prerender statik sayfalar |
| `gizlilik/`, `kvkk-aydinlatma/`, `cerez-politikasi/`, `kaynaklar/`, `iletisim/` | Yasal metinler |
| `hesabim/` | Hesap sayfası (noindex; giriş formu SPA'da çalışır) |
| `sitemap.xml`, `404.html` | 511 URL; 404 sayfası arama kutusu + popüler bağlantılar |

- Rota sırası (en yakın komşu + 2-opt) **hem** `build.py` **hem** `src/app.js` içinde aynı
  algoritmayla üretilir; statik rota sayfası ile uygulamadaki canlı rota birebir aynıdır.
- Yer tutucu doldurulmazsa derleme hata verir (`__CSSURL__`, `__JSURL__`, `__TR_PATH__` …).

## Dosya düzeni

```
turkiye-kesif/
├── index.html            # ÜRETİLEN SPA kabuğu
├── build.py              # derleyici: paketler + 511 prerender sayfa + sitemap
├── src/
│   ├── template.html     # işaretleme, ikon sprite, meta/CSP, onay şeridi
│   ├── style.css         # tema (v12: kontrast, 44 px hedefler, 12 px taban metin)
│   ├── app.js            # yönlendirici, arama, rotalar, modaller, Supabase istemcisi
│   └── tr-path.txt       # Türkiye silueti (Natural Earth 10m)
├── data/
│   ├── build_data.py     # ham Wikidata kayıtları → turkiye-data.json
│   ├── turkiye-data.json
│   └── fetch*.py         # Wikidata SPARQL toplayıcıları (önbellekli)
├── assets/img/           # 11 WebP (hero 1600/800, 5 şehir, rota, 3 mevsim)
├── docs/                 # denetim raporu + ekran görüntüleri
├── .env.local            # Supabase anahtarları (depoya girmez)
└── .github/workflows/pages.yml  # GitHub Pages dağıtımı
```

## Hesap ve bulut eşitleme (Supabase)

| Bileşen | Değer |
|---|---|
| Proje | `laqmoghxnwsavulkmzls` (eu-central-1) |
| Giriş yöntemi | e-posta **magic link** (şifre yok) |
| Tablolar | `favorites`, `route_progress`, `newsletter` |
| Güvenlik | RLS: `auth.uid() = user_id`; anon anahtarla tabloya doğrudan erişim **reddedilir** (HTTP 401) |
| İstemcide bulunan anahtar | yalnız `publishable` anahtar — `service_role` asla koda girmez |

Giriş yapılmadan favoriler `localStorage`'ta (`tk-favs-v2`) tutulur; giriş yapılınca yerel
favoriler buluta taşınır (`merge-duplicates`), ikinci cihazda aynı hesapla açıldığında geri gelir.

### Hesabım sayfası ve rota ilerlemesi

`/hesabim/` (uygulama içinde `#/hesabim`) tek ekranda şunları toplar:

| Bölüm | İçerik |
|---|---|
| Hesap | e-posta, eşitle / verilerimi indir (JSON) / çıkış |
| Devam eden rotalar | kaldığınız durak, ilerleme çubuğu, "Devam et" ve "Bitir" |
| Favoriler | hesaba bağlı liste, tek tek kaldırma |
| Tamamlanan rotalar | bitirdiğiniz rotalar |
| Verilerimi sil | favoriler + ilerleme + cihaz kayıtları silinir, oturum kapanır |

Rota ilerlemesi üç yerde tutulur: `localStorage` (`tk-progress-v1`, `tk-done-v1`) ve giriş yapıldıysa
Supabase `route_progress` tablosu. Durak değiştikçe 700 ms debounce ile `upsert` edilir; ikinci cihazda
giriş yapınca `progPull()` ile geri gelir. "Bitir" yerel kaydı tamamlananlara taşır ve uzak satırı siler.

KVKK m.11 hakları ürün içinde: **verilerimi indir** (JSON dışa aktarım) ve **hesap verilerimi sil**.

### KVKK / çerez davranışı

- İlk ziyarette alt şerit çıkar: **Anladım** / **Yalnızca zorunlu**.
- Hava durumu (Open-Meteo) ve Supabase istekleri **yalnızca izin verildikten sonra** yapılır;
  "yalnızca zorunlu" seçilirse hiçbir üçüncü taraf çağrısı olmaz, hava durumu yerine
  "Hava durumunu göster" düğmesi görünür.
- Meta CSP: `default-src 'self'; script-src 'self'; connect-src 'self' https://api.open-meteo.com https://laqmoghxnwsavulkmzls.supabase.co`.

## GitHub Pages

Depoya her `push` sonrası site otomatik yayınlanır:

1. **Settings → Pages → Build and deployment → Source: GitHub Actions**
2. `main` dalına push edin (veya Actions sekmesinden *GitHub Pages'e yayınla* iş akışını çalıştırın)
3. Site adresi: `https://xharunkoca.github.io/turkiye-kesif/`

İş akışı yayından önce veriyi doğrular (81 il / 15 kategori), `build.py`'yi çalıştırır ve
**tüm siteyi** (`index.html`, `assets/`, `il/`, `kategori/`, `rota/`, yasal sayfalar,
`sitemap.xml`, `404.html`) `_site/` klasörüne kopyalayıp yayınlar.

## Veri kaynakları ve doğrulama

- **Wikidata** (CC0): il/ilçe/köy/mahalle ilişkileri ve koordinatlı turistik noktalar
  (SPARQL, sonuçlar `data/raw/` içinde önbelleklenir). Sınıf eşlemeleri: antik kent,
  höyük, kale, müze, millî park, göl, şelale, mağara, kanyon, plaj, cami/külliye,
  hamam, kervansaray, bedesten/çarşı…
- **Türkçe Vikipedi resmî listeleri**: *Türkiye'deki millî parklar* (53), *tabiat parkları* (259),
  *tabiat anıtları* (117), *tabiat koruma alanları* (32) ve *illere göre müzeler* (~1.600 ad).
  Bu kayıtlarda koordinat varsa Vikipedi koordinat API'sinden alınır; yoksa kayıt yine listelenir.
- **Wikidata sınıf taraması**: kale, tarihî köprü, mağara, manastır, kilise, türbe, cami, müze,
  antik kent, göl, şelale, baraj, plaj ve kaplıca sınıflarında koordinatlı 11.474 aday toplandı.
- **İl sınırı poligonları** (`tr-cities.json`, 81 il): koordinat → doğru il/ilçe ataması.
- **Natural Earth 10m** (kamu malı): Türkiye sınır geometrisi.
- **Open-Meteo** (ücretsiz, anahtarsız): canlı hava durumu ve seyahat puanı.
- Kategori envanter sayıları resmî/derleme istatistiklerdir (TÜİK, Kültür ve Turizm
  Bakanlığı, TÜRÇEV, TÜRKPATENT vb.).

### Rotayı başlat (canlı mod)

Her rota kartında **Başlat**, rota detayında **Rotayı başlat** düğmesi vardır:

- Adım adım panel: *Durak 2 / 5*, ilerleme çubuğu, o anki durak, önceki duraktan ve
  sonraki durağa mesafe, "Yol tarifi al" (Google Maps'te o bacağın sürüş tarifi),
  "Haritada aç", **Sonraki durak / Önceki**, son durakta **Rotayı bitir**.
- **Google'da başlat / Google'da tüm rota**: rotanın tamamını tek linkte açar
  (`maps/dir/?api=1&origin=…&destination=…&waypoints=…&travelmode=driving`).

### Konum doğruluğu

- Koordinatı olan kayıtlar **"Konuma git"** ile doğrudan noktaya gider (`maps?query=lat,lon`).
- Koordinatı doğrulanamayan **871 kayıt** da listede görünür; kartında *"konum yok"* etiketi
  ve **"Haritada ara"** düğmesi bulunur → Google Maps'te *ad + ilçe + il* ile arama yapar
  (yanlış bir koordinata göndermek yerine doğru sonucu bulur).
- İlçe merkezinden 90 km'den uzak koordinatlar en yakın ilçeye taşınır (9 kayıt düzeltildi).
- İl merkezine sabitlenmiş yaklaşık koordinatlar (175 kayıt) doğrulanmamış sayılır;
  bunlar da "Haritada ara" ile ada göre aranır (gastronomi kayıtları bölgesel olduğu için il merkezi kabul edilir).
- **Hazır rotalar yalnızca konumu doğrulanmış duraklarla kurulur**; konumsuz kayıtlar rota
  üretimine hiç girmez. Rotalar kompakt kümeleme (çekirdek durak + çevresindeki en yakın
  duraklar), en yakın komşu sıralaması ve 2-opt kısaltmasıyla kurulur; aynı yerin iki kaydı
  (ör. "X Millî Parkı" / "X Milli Parkı") rotaya iki kez girmez.
- İl merkezine 220 km'den uzak aykırı koordinatlar, aynı ad + 3 km yinelenen kayıtlar ve
  jenerik adlar ("Bedesten", "Tarihî Çarşı"…) ayıklanır; köy/mahalleler en yakın ilçeye bağlanır.

## Notlar

- Arayüz tamamen Türkçedir; tipografi ve renk paleti referans tasarımdan gelir
  (lacivert `#0a2c52`, kırmızı `#e11d2e`, sarı `#ffd21e`).
- Favoriler `localStorage` (`tk-favs-v2`), rota kayıtları `tk-routes-v2` anahtarında.
- Dosya `file://` ile açıldığında da çalışır; GitHub Pages'te harici bağlantılar
  (Google Maps, Wikidata) normal şekilde açılır.

## Lisans

Kod ve üretilen görseller [MIT](LICENSE). Veri: Wikidata (CC0 1.0), Natural Earth (kamu malı).
