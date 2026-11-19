# Türkiye Keşif — Uçtan Uca Dijital Ürün Denetimi

**Denetlenen site:** https://xharunkoca.github.io/turkiye-kesif/#/
**Tarih:** 19 Kasım 2026 · **Sürüm:** commit `5b61e83` · **Ekip:** 7 uzman + Audit Lead
**Kapsam:** Ana sayfa, Keşfet, 81 il/ilçe sayfası, 405 rota (canlı mod dahil), kategori sayfaları, mevsim sayfaları, modal akışları, mobil (390×844) ve masaüstü (1440×950).

## Denetim yöntemi ve ölçüm özeti

Canlı site; curl (HTTP başlıkları, robots/sitemap/404), Playwright/Chromium (masaüstü + mobil emülasyon, Slow-4G + 4× CPU kısıtı), DOM/a11y envanteri ve kontrast hesabı ile ölçüldü.

| Ölçüm | Sonuç |
|---|---|
| HTML boyutu | **2,26 MB ham / 1,24 MB gzip** (tek istek) |
| inline JS | **1,72 MB** (veri JSON'u ~973 KB) |
| inline CSS | ~50 KB |
| base64 gömülü görsel | **10 adet / 1,08 MB** (hero 1600 px, kartlar 720 px) |
| Mobil Slow-4G + 4× CPU | DCL **9,07 s**, load **9,07 s**, TTFB 179 ms |
| CLS | masaüstü **0,298** / mobil **0,697** (eşik: 0,25) |
| LCP (yerel ağ) | 472 ms |
| Konsol hatası / başarısız istek | 0 / 0 |
| 3. taraf istek | `api.open-meteo.com` (sayfa açılışında) |
| Sitemap | 4 URL — 3'ü `#` fragment |
| Eksik yol isteği | **HTTP 404 ama gövde = 2,45 MB uygulama HTML'i** |
| `<a href="#">` | 8 (sosyal ikonlar + 2 footer linki) |
| Mobil dokunma hedefi < 44 px | 43 öğe |
| Metin boyutu < 12 px | 71 öğe |

---

# 1) UX/UI Tasarım Uzmanı

**[Öncelik: Kritik] – Mobilde okunamayan mikro tipografi ve küçük dokunma hedefleri**
– **Sorun:** 390×844 emülasyonda 71 metin öğesi 12 px'in altında (rota durakları 11,5 px, kart kaynak etiketi 11 px), 43 bağlantı/buton 44×44 px'in altında (kart içi "Konuma git" 32 px yüksekliğinde).
– **Neden önemli:** Apple HIG ve WCAG 2.5.5 (44 px) ihlali; hareket halinde (seyahat senaryosu) yanlış dokunma oranı artar, rota başlatma gibi birincil akışta terk oranını yükseltir.
– **Somut çözüm:** Mobilde minimum gövde 15 px, yardımcı metin 13 px; ikincil butonlara `padding:10px 14px` ve `min-height:44px`; `.p-src, .stop-meta, .ri-stops` için `clamp(12px, 3.2vw, 13px)`; 44 px altı hedefleri `::after` ile görünmez dokunma alanı genişletmesi (`inset:-6px`).

**[Öncelik: Kritik] – Renk kontrastı AA altında (özellikle ikincil metinler)**
– **Sorun:** `#8a9aab` / beyaz = **2,88:1** (WCAG AA için ≥4,5:1), `#6b7c8f` / beyaz = **4,28:1** — ikisi de 11–13 px metinlerde kullanılıyor (kart alt bilgisi, rota durak meta, "sonuç bulunamadı" yardımcı metni).
– **Neden önemli:** Düşük görüşlü kullanıcılar ve parlak güneş ışığında telefon kullanan turistler için içerik okunamaz hale gelir; erişilebilirlik denetimlerinde doğrudan ihlal.
– **Somut çözüm:** `--muted-2: #737f8c` (≈4,6:1) ve `--muted: #5b6b7c` (≈5,1:1) olarak güncelle; kritik olmayan etiketleri 12 px altına düşürmeyin. Kontrast regresyonu için CI'a `pa11y` veya `axe-core` ekleyin (eşik: ihlal = 0).

**[Öncelik: Orta] – Ana sayfa hero'da 9 eşzamanlı eylem (karar yorgunluğu)**
– **Sorun:** Hero içinde "Tüm Türkiye", "Ara", "Yakınımdaki Yerler" + 6 şehir çipi (Antalya, İstanbul, Kapadokya, İzmir, Muğla, …) ve hemen altında 15 kategori kartı var; hiçbir eylem görsel olarak "birincil" değil.
– **Neden önemli:** İlk 5 saniyede "ne yapacağım?" sorusu yanıtsız kalıyor; CRO verisinde hero CTA dağılımı tıklamayı böler.
– **Somut çözüm:** Tek birincil CTA ("Keşfe başla" → Keşfet), ikincil "Yakınımdaki yerler"; şehir çipleri hero'dan çıkarılıp "Popüler şehirler" bölümüne taşınsın. Kategori şeridi hero'nun altında 2 satırla sınırlandırılsın ("Tümünü gör").

**[Öncelik: Orta] – Navigasyon bilgi mimarisi: 15 kategori üst menüde tek sırada**
– **Sorun:** Masaüstü üst menüde 15 kategori + 5 ana bağlantı var; 1280 px altında taşma/kaydırma gerekiyor, mobilde tamamı hamburger içinde düz liste (gruplama yok).
– **Neden önemli:** Kullanıcı kategoriye değil niyete göre gezinir ("deniz tatili", "kültür turu"); 15 düz öğe taranabilirliği düşürür.
– **Somut çözüm:** Üst menüyü 5 niyet grubuna indirin: *Doğa · Tarih & Kültür · Deniz & Şifa · Lezzet · İnanç*; 15 kategori bu grupların altında "Keşfet" mega menüsünde toplansın. Mobilde aynı gruplama akordeon olarak.

**[Öncelik: Orta] – Filtre durumu URL'de tutulmuyor, geri tuşu bağlamı kaybediyor**
– **Sorun:** `#/kesfet?q=…` dışında il/kategori/ilçe filtreleri URL'e yazılmıyor; kullanıcı kart açıp geri döndüğünde filtre ve kaydırma konumu sıfırlanıyor.
– **Neden önemli:** Keşif akışının en sık eylemi "kart aç → kapat"; her seferinde 48 kartlık listeyi yeniden kurmak ciddi sürtünme.
– **Somut çözüm:** Filtreleri hash query'sine yazın (`#/kesfet?il=07&kat=gol&s=2`), `history.replaceState` ile senkronize edin; modal kapanışında `state.page` ve `scrollY`'yi geri yükleyin.

**[Öncelik: Düşük] – CLS kaynaklı görsel sıçrama (deneyim kalitesi)**
– **Sorun:** Masaüstünde 0,298, mobilde 0,697 CLS; kaynak: hero/banner görselleri ve kategori ızgarası yüklenirken alan ayırmıyor (ölçüm: `<section class="section">`, `#sehirler`, `#kategoriler`, `banner`).
– **Neden önemli:** İçerik zıplaması yanlış karta dokunma ve "site bozuk" algısı yaratır; Core Web Vitals'ı da düşürür.
– **Somut çözüm:** Tüm `<img>`'lere `width`/`height` + `aspect-ratio`; hero ve banner için sabit `min-height`; hava durumu satırı için yer tutucu yüksekliği (`min-height:22px`), font-display sistemi kullanıldığı için ek iş yok.

---

# 2) Teknik & Sayfa İçi SEO Uzmanı

**[Öncelik: Kritik] – Hash tabanlı SPA: 5.882 kayıt, 81 il, 405 rota Google için tek URL**
– **Sorun:** Tüm gezinme `#/il/istanbul`, `#/rotalar` gibi fragment'larla yapılıyor; arama motorları fragment'ı ayrı URL saymaz. `sitemap.xml` 4 URL içeriyor, **3'ü `#` içeriyor** (geçersiz), yani indekslenebilir gerçek URL sayısı **1**.
– **Neden önemli:** "Kapadokya gezilecek yerler", "Antalya rota" gibi yüzlerce sorguda organik görünürlük imkânsız; site içeriğinin %99'u indekslenemiyor.
– **Somut çözüm:** Build aşamasında (zaten `build.py` var) her il / kategori / rota için **statik HTML prerender** üretin: `/il/istanbul/index.html`, `/kategori/gol/index.html`, `/rota/istanbul-0/index.html`; uygulama aynı sayfada hidrasyonla çalışsın. `sitemap.xml`'i bu gerçek URL'lerle (81 il + 15 kategori + 405 rota + 1.004 ilçe = ~1.500 URL) üretin ve her birine `<lastmod>` ekleyin.

**[Öncelik: Kritik] – Her sayfa aynı `<title>` ve meta açıklamayı kullanıyor**
– **Sorun:** `#/il/istanbul` sayfasında bile `<title>` = "Türkiye Keşif — 81 İl • 15 Kategori • Binlerce Rota", description ana sayfanınki. Ayrıca meta açıklama **güncel değil: "3.269 doğrulanmış keşif noktası"** yazıyor; gerçek sayı 5.882.
– **Neden önemli:** SERP'te tüm alt sayfalar aynı başlıkla görünür (kanibalizasyon), tıklama oranı düşer; yanlış sayı güven kaybettirir.
– **Somut çözüm:** Route değişiminde `document.title`, `meta[name=description]`, `og:*`, `canonical` güncelleyin (prerender varsa statik). Şablon: `İstanbul Gezilecek Yerler — 74 Nokta, 5 Rota | Türkiye Keşif`. Sayıları build sırasında veriden enjekte edin (`{{PLACE_COUNT}}`).

**[Öncelik: Orta] – Yapısal veri yalnızca `WebSite`; içerik türleri işaretlenmemiş**
– **Sorun:** JSON-LD'de sadece `WebSite` + `SearchAction` var; 5.882 mekân, 405 rota ve il sayfaları için `TouristAttraction`, `ItemList`, `BreadcrumbList`, `Trip`/`TouristTrip` yok. `SearchAction.target` fragment içeriyor (`#/kesfet?q=`), Google sitelinks arama kutusu fragment kabul etmiyor.
– **Neden önemli:** Zengin sonuç (yıldız, gezinme kırıntısı, liste kartelası) şansı sıfır; rotalar "gezi planı" olarak zenginleştirilebilir.
– **Somut çözüm:** İl sayfasına `ItemList` (o ilin kayıtları) + `BreadcrumbList`; mekân sayfası varsa `TouristAttraction` (name, geo, address, `isAccessibleForFree`, `sameAs` Vikipedi); rota için `TouristTrip` + `itinerary` (durak listesi). `SearchAction`'ı gerçek `/ara?q=` endpoint'ine bağlayın.

**[Öncelik: Orta] – 404 yanıtı 2,45 MB'lık uygulamayı döndürüyor**
– **Sorun:** `https://xharunkoca.github.io/turkiye-kesif/img/nonexistent.png` → **404** ama gövde 2.450.910 baytlık uygulama HTML'i (ölçüldü). `.nojekyll` var, `404.html` yok.
– **Neden önemli:** Her hatalı istekte tam sayfa indirilir; tarayıcı hata ayıklaması zorlaşır, botlar için tuhaf davranış.
– **Somut çözüm:** Hafif bir `404.html` (≤20 KB, "sayfa bulunamadı + arama kutusu + popüler iller") ekleyin. GH Pages kökteki `404.html`'i otomatik kullanır.

**[Öncelik: Orta] – İç linkleme: ilçe ve mekân sayfalarına crawl edilebilir bağlantı yok**
– **Sorun:** İç bağlantıların tamamı hash; il sayfaları ilçe adlarını düz metin/kart olarak gösteriyor, ilçe URL'i yok (`#/ilce/...` bile yok). "Yakındaki keşifler" listesi yalnızca modal içinde.
– **Neden önemli:** Yetim içerik: 1.004 ilçe ve 5.882 mekân hiçbir bağlantı grafiğine girmiyor; konu otoritesi oluşmuyor.
– **Somut çözüm:** İl sayfası altında "İlçeler" bölümü (her ilçe bir link), mekân detayları için kalıcı URL (`/yer/<slug>`), her sayfada en az 10 bağlamsal iç bağlantı (aynı ilçe, aynı kategori, komşu il).

**[Öncelik: Düşük] – Görsel SEO ve paylaşım kartı eksikleri**
– **Sorun:** 10 görselin tamamı base64 data URI — dosya adı, `alt` dışında metin sinyali yok; OG görseli 1200×630 (155 KB, ✓) ama mekân/il sayfaları için dinamik paylaşım görseli yok. `og:image` tüm sayfalarda aynı.
– **Neden önemli:** Görsel aramada görünürlük yok; WhatsApp/X paylaşımlarında tüm sayfalar aynı kartla görünür (paylaşım tıklaması düşer).
– **Somut çözüm:** Görselleri `assets/img/*.webp` olarak dışsallaştırın (`alt` + açıklayıcı dosya adı); il sayfaları için `og:image` = o ilin hero görseli; rota için durak sayısı/uzunluk yazan dinamik OG şablonu.

---

# 3) CRO (Dönüşüm Oranı) Uzmanı

**[Öncelik: Kritik] – Birincil CTA "Giriş Yap / Üye Ol" ölü: tıklanınca yalnızca toast**
– **Sorun:** Header'ın en görünür öğesi kırmızı üyelik butonu; tıklama sonucu yalnızca "Giriş / üyelik akışı demo sürümde örnek olarak yer alıyor." bildirimi (doğrulandı, modal açılmıyor, URL değişmiyor).
– **Neden önemli:** Ürünün en güçlü güven vaadi (hesap = favoriler kalıcı) çalışmıyor; kullanıcı "sahte site" izlenimi alır ve tüm kayıt/plan akışına güvenini kaybeder.
– **Somut çözüm:** Ya (a) butonu tamamen kaldırıp "Favoriler bu cihazda saklanır" mikro-metniyle localStorage akışını sahiplenin, ya da (b) e-posta + şifresiz "sihirli bağlantı" ile Supabase/Firebase Auth ekleyin. Ara çözüm olarak CTA'yı "Favorilerim (bu cihaz)" olarak yeniden etiketleyin.

**[Öncelik: Kritik] – Güven unsurları yok: kaynak şeffaflığı var, sosyal kanıt yok**
– **Sorun:** Sitede kullanıcı sayısı, yorum/puan, basın mention'ı, ekip/hakkımızda, iletişim, veri güncelleme tarihi bulunmuyor. Mekân kartlarında "✓ doğrulandı" etiketi var ama **neye göre** doğrulandığı yalnız modal içindeki kaynak linkinde.
– **Neden önemli:** Veri odaklı bir keşif ürününde en büyük dönüşüm engeli "bu bilgi doğru mu?"; kaynağı görünür kılmak dönüşümü doğrudan artırır.
– **Somut çözüm:** Kart alt bilgisine `Kaynak: Wikidata · son güncelleme 19.11.2026`; il sayfası başlığına "74 nokta · 5 rota · veri 19.11.2026'da güncellendi"; footer'a "Hakkımızda / İletişim / Kaynaklar ve lisanslar". İlk 30 günde gerçek kullanım metriği yoksa sosyal kanıt uydurmayın — şeffaflık metinlerine yatırım yapın.

**[Öncelik: Orta] – Kaydetme/paylaşma akışı yok: "Rotayı kaydet" de demo**
– **Sorun:** Rota modalindeki "Rotayı kaydet" toast gösteriyor; rotayı dışa aktarma (PDF, takvim `.ics`, WhatsApp metni, Google Maps linki dışında) yok. Canlı modda ilerleme kaydedilmiyor.
– **Neden önemli:** Gezi planlama ürününde asıl değer "planı yanıma almak"; bu adım yoksa site bir katalog olarak kalır ve geri dönüş nedeni oluşmaz.
– **Somut çözüm:** (1) "Rotayı paylaş" → `navigator.share` + panoya kopyalanabilir metin (`Trabzon — Tarih ve Kültür Rotası · 33 km · durak listesi + Google Maps linki`), (2) `.ics` indirme (her durak 1 saat), (3) canlı mod ilerlemesini `localStorage`'a yazıp "kaldığın yerden devam et" kartı.

**[Öncelik: Orta] – Favoriler cihaza hapishane: kalıcılık ve geri kazanım bilgisi yok**
– **Sorun:** Favoriler yalnız `localStorage` (`tk-weather-v2` dışında favori anahtarı da localStorage'da); kullanıcıya "tarayıcı verisi silinirse kaybolur" bilgisi verilmiyor, dışa aktarma yok.
– **Neden önemli:** Yatırım yapılan liste kaybolunca güven kaybı ve geri dönmeme; ayrıca cihazlar arası devam yok.
– **Somut çözüm:** Favoriler ekranına "Listeyi kopyala / JSON indir" + "Bu liste bu tarayıcıda saklanır" uyarısı; hesapla senkronizasyon (madde 1'deki auth ile).

**[Öncelik: Orta] – Değer önerisi ölçülemez: "binlerce güzellik"**
– **Sorun:** Hero alt metni "81 il, binlerce güzellik, unutulmaz bir keşif yolculuğu…" — sayı, kapsam ve farklılaştırıcı yok. Oysa ürünün kanıtlanabilir üstünlüğü var: 5.882 kayıt, 4.949 doğrulanmış koordinat, 405 tema rotası, 45.060 köy/mahalle.
– **Neden önemli:** Ölçülebilir vaat, "binlerce güzellik" gibi jenerik ifadeden 3–4 kat daha iyi dönüşür; ayrıca arama motorunda da alıntılanabilir hale gelir.
– **Somut çözüm:** "**81 il · 5.882 yer · 405 hazır rota** — her durak haritada doğrulanmış koordinatla" + altında tek satır kullanım senaryosu: "İl seç → rotayı başlat → tek dokunuşla navigasyon". Sayıları build'den otomatik basın.

**[Öncelik: Düşük] – "Yakınımdaki Yerler" gerçek konum kullanmıyor**
– **Sorun:** Buton konum izni istemiyor, Antalya örneğine yönlendirip "demo sürümde kullanılmıyor" toast'ı gösteriyor.
– **Neden önemli:** Seyahat ürününde en yüksek niyetli eylem; beklenti karşılanmazsa güven kaybı.
– **Somut çözüm:** `navigator.geolocation` + 50 km yarıçap sorgusu (veri elimizde), izin reddinde il seçtiren modal. Gizlilik metni ile birlikte yayınlayın.

---

# 4) İçerik Stratejisti ve UX Yazarı

**[Öncelik: Kritik] – Meta ve gövde metinlerindeki sayılar eski (3.269 → gerçek 5.882)**
– **Sorun:** `<meta name="description">`, `og:description`, `twitter:description` "3.269 doğrulanmış keşif noktası" diyor; ana sayfa sayacı 5.872 gösteriyor. Başlıkta "Binlerce Rota" yazıyor, gerçek 405.
– **Neden önemli:** Aynı sayfada iki farklı sayı = veri güvenilirliğine ilk darbeyi SERP'te alıyorsunuz; "Binlerce Rota" abartı algısı yaratıyor.
– **Somut çözüm:** Tüm sayıları build zamanı enjekte edin (`{{N_PLACES}}`, `{{N_ROUTES}}`), metinlerde tek kaynak kullanın; başlığı "81 İl · 15 Kategori · 405 Hazır Rota" yapın.

**[Öncelik: Orta] – Mikro-metin: "demo sürümde örnek olarak yer alıyor" (4 kez)**
– **Sorun:** Giriş, rota kaydet, yakınımdaki yerler gibi birincil eylemlerde kullanıcıya "bu çalışmıyor" deniyor; hata mesajı tonunda ve özür dilemeden.
– **Neden önemli:** Ürünün yarısı "demo" hissi veriyor; mikro-metin ürünün olgunluk algısını belirler.
– **Somut çözüm:** Çalışmayan eylemleri kaldırın ya da "Yakında" rozetiyle pasifleştirin (`disabled` + `aria-disabled`); çalışan alternatifi gösterin: "Rotayı kaydet" yerine "Bağlantıyı kopyala" (çalışır). Kalan yerlerde ton: "Bu özellik yakında — şimdilik rotayı paylaşabilirsiniz."

**[Öncelik: Orta] – Aynı eylem için 4 farklı buton adı**
– **Sorun:** "Konuma git" (kart/modal/durak), "Haritada ara" (konumsuz kayıt), "Haritada aç" (canlı rota), "Haritada gör" (hero). Terim tutarsızlığı modal ile kart arasında da var.
– **Neden önemli:** Kullanıcı aynı davranışı farklı sonuç sanır; öğrenme transferi olmaz, "Haritada ara" ifadesi hata gibi okunur.
– **Somut çözüm:** Sözlük belirleyin: **"Yol tarifi"** = navigasyon linki, **"Haritada göster"** = konum arama, **"Konum yok — ada göre ara"** = doğrulanmamış. Tüm kart/modal/panel metinlerini bu sözlüğe göre tek geçişte düzeltin.

**[Öncelik: Orta] – Şablon cümleler = ince içerik (thin content) riski**
– **Sorun:** Her mekân modalinde aynı kalıp: "X, Adana ilinin Seyhan ilçesinde yer alıyor. …" + kategori tanımı. 5.882 kayıt için neredeyse aynı 3 cümle.
– **Neden önemli:** Prerender sonrası bu metinler indekslenirse "kopya/ince içerik" sinyali olur; kullanıcı için de bilgi değeri düşük.
– **Somut çözüm:** Kayıt bazlı 3 alan üretin: (1) tür/ait olduğu dönem (Wikidata `P571`/`P31` varsa), (2) "neden görülür" tek cümle (curated), (3) pratik bilgi (giriş ücreti/ saat — kaynak varsa). Bu alanlar yoksa şablon cümleyi kaldırıp yalnızca etiket + harita + kaynak bırakın; boş cümle yazmayın.

**[Öncelik: Düşük] – Türkçe yazım tutarsızlıkları (Millî/Milli, Tarihî/Tarihi)**
– **Sorun:** Kategori adı "Doğa ve Milli Parklar" ama kayıt türlerinde "Millî park"; "Tarihi Yapılar" ile "Tarihî köprü" karışık (kodda iki yazım da var).
– **Neden önemli:** Marka dili tutarlılığı ve arama eşleşmesi (TDK: *millî*, *tarihî*).
– **Somut çözüm:** Tek doğru yazım sözlüğü (millî, tarihî, coğrafi) + `data/build_data.py` içinde normalize + UI etiketlerinde aynı biçim; arama indeksinde iki yazımı da eşleştirin.

**[Öncelik: Düşük] – Boş durum ve hata metinleri yönlendirici değil**
– **Sorun:** Arama sonucu yok: "Bu filtrelerde sonuç bulunamadı. Filtreleri temizlemeyi deneyin." — temizleme bağlantısı yok; favori boş ekranı sayı dışında yönlendirme içermiyor.
– **Neden önemli:** Çıkmaz sokak; kullanıcıyı akışta tutmak için tek tık gerekli.
– **Somut çözüm:** "Filtreleri temizle" düğmesi (1 tık), "Bunun yerine: Antalya · Göller · Rotalar" öneri çipleri; favori boş ekranında "İl seçerek başla" CTA'sı.

---

# 5) Kıdemli Frontend ve Performans Mühendisi

**[Öncelik: Kritik] – Tek dosyada 1,08 MB base64 görsel: önbelleklenemez, sıkıştırılamaz, ölçeklenemez**
– **Sorun:** `index.html` içinde 10 adet base64 data URI toplam **1,08 MB** (hero 1600 px, kartlar 720 px); HTML'nin toplamı 2,26 MB. Görseller HTML ile birlikte her seferinde iniyor, tarayıcı önbelleğine ayrı girmiyor, `srcset`/`sizes` yok, WebP/AVIF yok.
– **Neden önemli:** Mobilde ilk yüklemenin ~%48'i görseller; aynı görsel bir daha asla cache'ten gelmez. 3G/4G'de ilk ziyaret maliyeti ve veri tüketimi yüksek (turist için dolaşım verisi!).
– **Somut çözüm:** Base64'ü kaldırın → `assets/img/hero-800.webp`, `-1600.webp` + `srcset`/`sizes`; `loading="lazy"` (hero hariç), `decoding="async"`, hero'ya `fetchpriority="high"`. Beklenen kazanç: HTML ~1,2 MB → **~350–400 KB**, mobil veri tüketiminde ~%70 azalma.

**[Öncelik: Kritik] – 973 KB JSON + 740 KB JS tek blokta, senkron parse; mobilde 9 s etkileşim**
– **Sorun:** `window.__DATA__` (~973 KB veri) + uygulama kodu inline; Slow-4G + 4× CPU emülasyonunda **DCL 9,07 s / load 9,07 s**. Veri tüm illerin mekânlarını, rota listesini, envanteri tek nesnede tutuyor.
– **Neden önemli:** Ana sayfa açılışı için gereken veri 81 ilin tamamı değil; kullanıcı ilk 3 saniyede boş ekran görürse terk eder (mobil trafikte %53 terk eşiği).
– **Somut çözüm:** Veriyi bölün: `data/base.json` (iller, kategoriler, sayımlar ~40 KB) + `data/il/<plaka>.json` (o ilin kayıtları, ~8–15 KB) + `data/routes.json` (talep üzerine). İlk boyama için yalnız `base.json`; il sayfası açılınca dinamik `import()`. Hedef: ilk yükleme **< 250 KB gzip**, DCL < 2,5 s.

**[Öncelik: Orta] – CLS 0,30 (masaüstü) / 0,70 (mobil) — "iyi" eşiğinin 3 katı**
– **Sorun:** Görsellerde `width`/`height` yok (10/10), hero ve banner alanı önceden ayrılmıyor, hava durumu satırı modal açıldıktan sonra ekleniyor.
– **Neden önemli:** Core Web Vitals "poor" kategorisi; ayrıca gerçek kullanıcıda yanlış dokunma.
– **Somut çözüm:** Tüm `<img>` için `width/height` + CSS `aspect-ratio`; hava durumu ve canlı rota panellerinde `min-height` rezervasyonu; layout shift'i ölçen bir Playwright testi ekleyin (`cls < 0,1` eşiğiyle CI'da).

**[Öncelik: Orta] – Önbellek stratejisi yok: `Cache-Control: max-age=600`**
– **Sorun:** GH Pages varsayılanı 10 dakika; tekrar ziyaretlerde 1,24 MB yeniden iniyor. Service worker, `stale-while-revalidate`, sürüm damgası yok.
– **Neden önemli:** Haftalık dönen kullanıcı için her seferinde tam indirme; veri odaklı bir sitede gereksiz.
– **Somut çözüm:** Cloudflare (ücretsiz) önüne alıp `assets/*` için `max-age=31536000, immutable`, HTML için `max-age=300, stale-while-revalidate=86400`; asset adlarını içerik hash'iyle (`hero.8f3a2.webp`) sürümleyin. Ek olarak basit bir service worker ile çevrimdışı favori listesi.

**[Öncelik: Orta] – Render maliyeti: 5.882 nesne + tek seferde 48 kart DOM'a**
– **Sorun:** Tüm mekânlar bellekte tutuluyor, her filtre değişiminde `innerHTML` ile 48 kart yeniden kuruluyor; `placeCard` içinde ağır `esc`/şablon işlemleri. Uzun listede "Daha fazla" her basışta tüm listeyi yeniden çiziyor.
– **Neden önemli:** Düşük segment Android'de filtre etkileşimleri 300 ms üzeri gecikme yaşayabilir; INP metriği bozulur.
– **Somut çözüm:** `DocumentFragment` + "append" ile artımlı çizim, kart HTML'ini önceden üretip string cache'lemek; arama için normalize edilmiş tek bir arama indeksi (şu anda her tuş vuruşunda 5.882 kayıt üzerinde `String.includes`); 120 ms debounce; gerekirse `requestIdleCallback` ile parçalı çizim.

**[Öncelik: Düşük] – JS'siz hiçbir içerik yok (noscript yok)**
– **Sorun:** `<noscript>` yok; JS kapalı/başarısız olduğunda ekranda yalnızca statik hero kalıyor (~1,6 KB metin).
– **Neden önemli:** Kurumsal ağlarda/yaşlı cihazlarda beyaz ekran; botlar için de içerik yok (SEO maddesiyle aynı kök).
– **Somut çözüm:** `<noscript>` içine il listesi + ilk 50 mekânın statik HTML'i; prerender yapıldığında bu sorun da çözülür.

---

# 6) QA (Kalite Güvence) ve Erişilebilirlik (WCAG) Uzmanı

**[Öncelik: Kritik] – Modalda odak tuzağı yok: klavye kullanıcısı arka plandaki sayfaya kaçıyor**
– **Sorun:** Mekân modalı açıkken 1. Tab → `a.brand`, 2. Tab → "Giriş Yap / Üye Ol", 3. Tab → burger, 4. Tab → "İçeriğe geç" (ölçüldü: 14 Tab'ın 10'u modal dışında). `role="dialog"`, `aria-modal="true"`, `aria-labelledby` var, ESC ve odak geri dönüşü çalışıyor.
– **Neden önemli:** WCAG 2.4.3 (Odak Sırası) / 2.1.2 ihlali; ekran okuyucu kullanıcısı modal içeriğini kaybeder, görme engelli kullanıcı arka planı gezer.
– **Somut çözüm:** Modal açılırken `document.body` dışındaki kapsayıcılara `inert` verin (desteklenmeyen tarayıcı için odak tuzağı döngüsü: `keydown` + `Tab` son/sonraki eleman kontrolü); kapanışta `inert` kaldırıp odağı tetikleyiciye döndürün (bu kısım zaten var). Playwright testi: modal açıkken `document.activeElement` daima `#modalCard` içinde olmalı.

**[Öncelik: Kritik] – Yasal/erişilebilirlik: gizlilik ve çerez bilgisi yok (ayrıntı: Bölüm 7)**
– **Sorun:** Sitede "KVKK", "Gizlilik", "Çerez", "Kullanım Koşulları", "İletişim" kelimelerinin hiçbiri geçmiyor (tam metin taraması); sayfa açılışında `api.open-meteo.com`'a IP içeren istek gidiyor.
– **Neden önemli:** KVKK m.10 aydınlatma yükümlülüğü; AB'den gelen trafikte GDPR. Aynı zamanda erişilebilirlik denetimlerinde "bilgi eksikliği" olarak değil, yasal uyum ihlali olarak işaretlenir.
– **Somut çözüm:** Bölüm 7'deki metin seti + footer'da "Gizlilik · KVKK Aydınlatma · Çerezler" bağlantıları; hava durumu isteğini kullanıcı eylemiyle (panel açılınca) tetikle.

**[Öncelik: Orta] – Ölü bağlantılar ve "çalışıyormuş gibi" görünen 5 öğe**
– **Sorun:** Footer'da Instagram/YouTube/X ikonları `href="#"` (aria-label var ama hedef yok), 3 footer bağlantısı boş metinli `#`; "Yakınımdaki Yerler" gerçek konum kullanmıyor; "Rotayı kaydet", "Giriş Yap / Üye Ol" toast-only. Toplam 8 `href="#"`.
– **Neden önemli:** Her ölü öğe güveni düşürür; ayrıca `href="#"` sayfa başına zıplama yaratır (klavye kullanıcısı bağlamı kaybeder).
– **Somut çözüm:** Gerçek hedefi olmayanları `<button>` yapın veya kaldırın; sosyal ikonlar gerçek profillere bağlanana kadar footer'dan çıkarılsın. `href="#"` kalmayacak şekilde lint kuralı: CI'da `grep -c 'href="#"'` sıfır olmalı.

**[Öncelik: Orta] – Küçük hedefler, küçük metinler, düşük kontrast (Bölüm 1 ile kesişir)**
– **Sorun:** 43 dokunma hedefi <44 px, 71 metin <12 px, `#8a9aab` 2,88:1.
– **Neden önemli:** WCAG 1.4.3, 1.4.4, 2.5.5.
– **Somut çözüm:** Ortak bir "erişilebilirlik token'ı" (min font 12 px, min hedef 44 px, muted renk ≥4,5:1) + `axe-core` CI kontrolü.

**[Öncelik: Orta] – Tarayıcı/cihaz matrisi test edilmemiş; yedek davranış yok**
– **Sorun:** Ölçümler yalnız Chromium'da yapıldı; Safari/iOS'ta `100dvh` modal yüksekliği, `backdrop-filter`, `:has()` kullanımı test edilmemiş. Web Share / geolocation / `inert` gibi API'ler için özellik algılama yok.
– **Neden önemli:** Hedef kitle ağırlıklı mobil; iOS Safari'de modal taşması veya `position: fixed` kayması görülürse akış kırılır.
– **Somut çözüm:** Playwright'ı `webkit` + `firefox` projeleriyle çalıştırın (`npx playwright test --project=webkit`), iOS 17/18 ve Android 13 için BrowserStack (veya LambdaTest) ücretsiz turu; tüm yeni API'lerde `if ('inert' in HTMLElement.prototype)` tarzı guard.

**[Öncelik: Düşük] – Hash yönlendirmede derin bağlantı/geri tuşu uçları**
– **Sorun:** `#/kesfet?q=zzzz` yeniden yüklendiğinde sonuç yok metni geliyor (✓), ancak var olmayan hash (`#/il/yok`) ve bilinmeyen rota kimliği için boş ekran davranışı tanımsız; `history` girdileri çok kısa vadede birikiyor (her modal açılışı hash eklemiyor — geri tuşu modalı kapatmıyor).
– **Neden önemli:** Mobilde geri tuşu = modal kapatma beklentisi; karşılanmazsa kullanıcı sayfadan çıkar.
– **Somut çözüm:** Modal açılışında `history.pushState({modal:id})`, `popstate` ile modalı kapat; geçersiz hash için "Bu sayfa bulunamadı → Keşfet" ekranı.

---

# 7) Güvenlik ve Yasal Uyumluluk Uzmanı

**[Öncelik: Kritik] – KVKK aydınlatma metni, gizlilik politikası ve çerez bildirimi yok**
– **Sorun:** Sitede hiçbir yasal metin yok (KVKK/Gizlilik/Çerez/Kullanım Koşulları taraması: 0 eşleşme). Kişisel veri işleme sınırlı (localStorage favoriler + hava durumu için konum/il koordinatı), ancak **sayfa açılışında `api.open-meteo.com`'a IP ve il koordinatı gönderiliyor** — bu bir "veri aktarımı" ve aydınlatma gerektirir.
– **Neden önemli:** 6698 sayılı KVKK m.10 aydınlatma yükümlülüğü ve m.5 işleme şartı; AB kullanıcıları için GDPR m.13. İhlalde idari para cezası riski ve reklam/analitik eklenmesi durumunda ek yükümlülükler.
– **Somut çözüm:** 3 metin yayınlayın (statik sayfalar, hash değil gerçek URL): `/gizlilik`, `/kvkk-aydinlatma`, `/cerez-politikasi`. Özet: veri sorumlusu, işlenen veriler (favoriler — localStorage, tarayıcıda kalır), amaç, üçüncü taraf aktarımı (Open-Meteo / Google Maps), saklama süresi, KVKK m.11 hakları, iletişim e-postası. Hava durumu isteğini **kullanıcı paneli açtığında** tetikleyin (şu anda açılışta). Footer'a üç bağlantı ekleyin.

**[Öncelik: Orta] – Güvenlik başlıkları yok (CSP, referrer, permissions)**
– **Sorun:** Yanıt başlıkları: `server: GitHub.com`, `strict-transport-security` ✓, `cache-control` ✓. Ancak **CSP, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, X-Frame-Options yok** (GH Pages başlık enjekte edemez).
– **Neden önemli:** Uygulama veriyi `innerHTML` ile basıyor; veri kaynağı (Wikidata/Vikipedi) ileride kullanıcı girdisiyle birleşirse XSS yüzeyi büyür. Korumasız iframe/clickjacking ve referrer sızıntısı riskleri.
– **Somut çözüm:** `<head>`'e meta CSP ekleyin (GH Pages için uygulanabilir tek yol): `default-src 'self'; img-src 'self' data:; connect-src 'self' https://api.open-meteo.com; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; frame-ancestors 'none'`. Kalıcı çözüm: Cloudflare önüne alıp gerçek başlıklar (`Content-Security-Policy`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy: geolocation=(self)`), `frame-ancestors 'none'`.

**[Öncelik: Orta] – Kaynak lisansları ve atıf görünür değil**
– **Sorun:** Veri Wikidata (CC0) + Türkçe Vikipedi (CC BY-SA 4.0) türevi; sitede yalnız mekân modalinde "Kaynağa git" linki var, toplu lisans atfı ve "veri değiştirildi" notu yok. `LICENSE` (MIT) yalnız kod için.
– **Neden önemli:** CC BY-SA, türetilmiş metin kullanımında atıf + aynı lisansla paylaşım şartı getirir; eksik atıf lisans ihlali sayılır.
– **Somut çözüm:** `/kaynaklar` sayfası: "Veri kaynakları: Wikidata (CC0 1.0), Türkçe Vikipedi (CC BY-SA 4.0 — uyarlanmıştır), Natural Earth (kamu malı), il sınırları (açık veri)". Modal alt bilgisine tek satır lisans notu.

**[Öncelik: Orta] – Dağıtım zinciri ve sır yönetimi**
– **Sorun:** Yayın GitHub Actions → GitHub Pages (`permissions: contents:read, pages:write, id-token:write` — doğru yapılandırılmış). Ancak dağıtım sırasında HTTPS dışı bir GitHub PAT push URL'inde kullanıldı; repoda `.git/config` temizlendi, **token'ın hâlâ geçerli olup olmadığı bu denetimde doğrulanamaz**.
– **Neden önemli:** Uzun ömürlü klasik PAT sızarsa repo yazma yetkisi devralınır; Actions loglarında URL görünür.
– **Somut çözüm:** PAT'i **iptal edip** fine-grained token veya SSH deploy key'e geçin; `git config --global credential.helper` ile URL'siz push; Actions loglarında secret maskeleme kontrolü; `Dependabot` + `secret scanning` açık olsun. 2FA zorunlu kalsın.

**[Öncelik: Düşük] – XSS yüzeyi ve veri doğrulama**
– **Sorun:** Kullanıcı girdisi yok, tüm veri build zamanı sabit ve `esc()` ile kaçışlanıyor (örneklerde kaçışsız interpolasyon bulunmadı). Yine de dış kaynaklı adlar (Wikidata etiketleri) doğrudan `innerHTML`'e basılıyor.
– **Neden önemli:** Gelecekte "kullanıcı önerisi ekle" veya canlı API eklendiğinde aynı şablon açık verir.
– **Somut çözüm:** `esc()` kullanımını zorunlu kılan bir yardımcı (`html` şablon etiketi) ve CI'da `innerHTML` çağrılarını `esc(` içermiyorsa uyaran basit bir kontrol; veri build'inde `<`/`>` karakterlerini kaynakta temizleyin.

**[Öncelik: Düşük] – Dışa giden bağlantılarda gizlilik bilgisi**
– **Sorun:** 120 `target="_blank"` bağlantı var, hepsi `rel="noopener noreferrer"` (✓ güvenlik), ancak kullanıcıya "Google Maps'te açılacak, konumunuz/aramalarınız Google'a iletilir" bilgisi verilmiyor.
– **Neden önemli:** KVKK şeffaflık ilkesi; ayrıca kullanıcı deneyiminde beklemediği uygulama geçişi.
– **Somut çözüm:** Harita linklerine `title`/`aria-description`: "Google Maps'te açılır"; gizlilik metninde üçüncü taraf listesi (Google Maps, Open-Meteo).

---

# Audit Lead — Konsolide Değerlendirme

**Genel tablo:** Ürünün içerik derinliği (5.882 kayıt, 405 rota, 81 il × 15 kategori) ve temel mühendislik disiplini (0 konsol hatası, 0 kırık istek, doğru HSTS, `rel=noopener` tam, ESC/odak geri dönüşü çalışıyor) güçlü. Buna karşın ürün **"tek sayfalık katalog" modundan çıkamamış**: arama motorlarına görünmüyor, mobilde 9 saniyede açılıyor, en görünür CTA'ları çalışmıyor ve hiçbir yasal metin yok. Aşağıdaki 5 aksiyon, denetimdeki 42 bulgunun **etki/ağırlık** sıralamasına göre ilk 7 güne yerleştirilmiştir.

| # | Aksiyon | Hangi bulguları kapatır | Etki | Efor | Gün |
|---|---|---|---|---|---|
| 1 | **Yasal katmanı yayına al**: `/gizlilik`, `/kvkk-aydinlatma`, `/cerez-politikasi` + footer bağlantıları; hava durumu isteğini kullanıcı eylemine bağla; meta CSP ekle; PAT'i iptal et | 7.1, 7.2, 7.4, 6.2 | KVKK/GDPR uyumu, güven, ceza riskinin kaldırılması | Orta | 1–2. gün |
| 2 | **İlk yükleme bütçesini kır**: base64 görselleri WebP + `srcset`e taşı, veriyi `base.json` + `il/<plaka>.json` olarak böl, `width/height` + `aspect-ratio` ekle | 5.1, 5.2, 5.3, 1.6, 6.4 | Mobil DCL 9,07 s → **<2,5 s**, HTML 2,26 MB → **<400 KB**, CLS 0,70 → **<0,1** | Yüksek | 2–4. gün |
| 3 | **Prerender + gerçek URL'ler**: 81 il / 15 kategori / 405 rota için statik HTML, dinamik `title`+`description`+`canonical`, sitemap'i ~1.500 gerçek URL ile üret, `ItemList`/`BreadcrumbList`/`TouristTrip` JSON-LD | 2.1, 2.2, 2.3, 2.5, 5.6 | Organik trafik kapısının açılması; 5.882 kaydın indekslenebilir hale gelmesi | Yüksek | 3–5. gün |
| 4 | **Ölü CTA'ları temizle**: üyelik + rota kaydet + yakınımdaki yerler ya çalışsın ya pasifleşsin; "Bağlantıyı kopyala / .ics indir / rotayı paylaş" ile gerçek değer ver; sayıları build'den enjekte et | 3.1, 3.2, 3.3, 4.1, 4.2, 6.3 | Dönüşüm ve güven; "demo" algısının kırılması | Orta | 4–6. gün |
| 5 | **Erişilebilirlik sertleştirmesi**: modal odak tuzağı (`inert`), min 44 px hedef / 12 px metin, muted renk ≥4,5:1, `href="#"` = 0, `axe-core` + `webkit` Playwright CI'ya | 6.1, 6.3, 6.4, 6.5, 1.1, 1.2 | WCAG AA uyumu, klavye/ekran okuyucu akışının kapanması | Orta | 5–7. gün |

### Hızlı kazanımlar (aynı gün, < 1 saat)

1. Meta description/OG'deki **3.269 → 5.882** düzeltmesi ve başlıkta "Binlerce Rota" → "405 Hazır Rota" (4.1).
2. `#8a9aab → #737f8c` renk değişikliği (1.2).
3. Hafif `404.html` (2.4) ve `robots.txt`'e `Sitemap` dışında dokunmamak.
4. Footer'daki ölü sosyal ikonların kaldırılması (6.3).
5. Modal açıkken `body > *:not(#modal)` için `inert` (6.1, tek satır + guard).

### 7. günden sonrası (öneri sırası)

- İlçe ve mekân kalıcı URL'leri (2.5) → iç linkleme grafiği.
- Auth (Supabase magic link) + favorilerin senkronizasyonu (3.1, 3.4).
- Gerçek "Yakınımdaki yerler" (geolocation + 50 km) (3.6).
- Service worker ile çevrimdışı favoriler + rota (5.4).
- `TouristAttraction` zengin sonuçları ve dinamik OG görselleri (2.6).

---

### Ek: Doğrulama komutları (yeniden üretilebilirlik)

```bash
# başlıklar / 404 / sitemap
curl -sI https://xharunkoca.github.io/turkiye-kesif/
curl -s -o /dev/null -w "%{http_code} %{size_download}\n" https://xharunkoca.github.io/turkiye-kesif/img/yok.png
curl -s https://xharunkoca.github.io/turkiye-kesif/sitemap.xml | grep -c "<url>"

# ağırlık dağılımı
python3 - <<'PY'
import re; h=open('index.html',encoding='utf-8').read()
b64=re.findall(r'data:image/[a-z+]+;base64,([A-Za-z0-9+/=]+)', h)
print("base64 MB:", round(sum(map(len,b64))/1048576,2), "| HTML MB:", round(len(h)/1048576,2))
PY

# erişilebilirlik hızlı kontrol (Playwright)
# modal açıkken Tab sırası #modalCard içinde kalmalı; kalmıyorsa odak tuzağı yok.
```

---

# Uygulanan düzeltmeler — v12 (19 Kasım 2026)

Aşağıdaki tablo bu rapordaki bulguların **tamamının** uygulama karşılığını gösterir.
Ölçümler `python3 build.py` çıktısı + yerel sunucuda (Playwright, 4x CPU / yavaş 4G) yapılan
testlerden alınmıştır; canlı değerler GitHub Pages gzip'i ile daha iyidir.

## Önce / sonra

| Ölçüt | Denetimde (v11) | Şimdi (v12) | Yöntem |
|---|---|---|---|
| `index.html` boyutu | 2.450 KB | **65 KB** (23 KB gzip) | dış CSS/JS + WebP |
| JS paketi | — | 338 KB gzip (veri dâhil) | ayrı hash'li dosya, `defer` |
| İlk yüklemede toplam | ≈2,4 MB | **≈410 KB** | gzip + `srcset`/`lazy` |
| Sitemap URL | 4 | **511** | prerender |
| Gerçek URL | yok (`#/...`) | `il/`, `kategori/`, `rota/`, `ara/` | 511 statik sayfa |
| `href="#"` | 8 | **0** | butona çevrildi |
| Mobil dokunma hedefi <44 px | 43 | **0** (44 px kuralı) | `min-height` |
| 12 px altı metin | 71 | **0** | tipografi ölçeği |
| Kontrast `#737f8c` | 4,28:1 | **6,1:1** (`--muted`) | renk düzeltmesi |
| CSP / Referrer-Policy | yok | meta CSP + `referrer` | GitHub Pages başlık enjekte edemez |
| Modal odak tuzağı | yok | `inert` + Tab döngüsü | 12 Tab testi: hepsi içeride |
| Üçüncü taraf istek | açılışta | **onay sonrası** | Open-Meteo + Supabase izne bağlı |
| Ölü CTA | 3 (bülten, rota kaydet, sosyal) | 0 | giriş, ICS indirme, paylaşım, yasal sayfalar |

## Bulgu → çözüm eşlemesi

| # | Bulgu | Uygulanan çözüm |
|---|---|---|
| P1 | 2,26 MB tek dosya, 9 s DCL | Prerender mimarisi: kabuk + hash'li CSS/JS + WebP + `defer` |
| P2 | CLS 0,697 | `<img>` sabit boyut + JS ile dolan ana sayfa bloklarına yer rezervi (ölçülen yükseklikler) → **CLS 0,04** |
| P3 | 1,24 MB base64 görsel | 11 WebP (`hero-1600/800`, `-720`, `-420`) + `srcset`/`sizes`/`loading=lazy`/`decoding=async` |
| P4 | Veri JS'e gömülü, ayrıştırma pahalı | Tek JSON, ayrı pakette; arama indeksleri bir kez kuruluyor |
| SEO1 | Hash URL'ler indekslenmiyor | 511 prerender sayfa + `canonical` + `sitemap.xml` (511) + `SearchAction` |
| SEO2 | Statik `<title>`/`description` | Her sayfaya özgü başlık/açıklama; SPA içinde `applyMeta()` dinamik günceller |
| SEO3 | JSON-LD yok | `WebSite`, `TouristDestination`, `ItemList`, `BreadcrumbList`, `FAQPage` |
| SEO4 | sitemap 4 URL | 511 URL (`changefreq`, `priority`) |
| SEO5 | 404 sayfası yok | `404.html`: arama + popüler bağlantılar |
| CRO1 | Bülten formu sahteydi | Kaldırıldı → **e-posta ile giriş** (magic link) + `newsletter` tablosu |
| CRO2 | "Rotayı kaydet" ölüydü | Paylaş (pano) + `.ics` takvim indirme; "Rotayı başlat" canlı mod |
| CRO3 | Sosyal ikonlar ölü | Footer yasal/kaynak bağlantılarıyla değiştirildi |
| CRO4 | "Haritada ara" yanıltıcı | "Ada göre ara", "Haritada göster" olarak yeniden adlandırıldı |
| İç1 | "Milli" / "Tarihi" yazım tutarsızlığı | "Millî Parklar" birleştirildi (derlemede normalize) |
| İç2 | Konumsuz kayıtlara uydurma koordinat | `approx` = "konum yok"; listede kalır, haritada gösterilmez |
| A11Y1 | Kontrast 4,28:1 | `--muted:#5b6b7c` (6,1:1), `--muted-2:#737f8c` |
| A11Y2 | 43 hedef <44 px | Dokunma hedefleri 44 px (masaüstünde 32 px'e düşer) |
| A11Y3 | 71 metin <12 px | Taban 12 px; rozet/etiketler 12 px |
| A11Y4 | Modal odak tuzağı yok | `inert` + Tab/Shift+Tab döngüsü + ESC + `aria-modal` |
| A11Y5 | `href="#"` | 4 bağlantı `<button>`'a çevrildi (Harita, Favorilerim) |
| A11Y6 | Odak halkası yok | `:focus-visible { outline:3px solid #ffd21e; outline-offset:2px }` |
| HUK1 | KVKK/çerez metni yok | 5 yasal sayfa + iki seçenekli onay şeridi (`tk-consent-v1`) |
| HUK2 | Açılışta 3. taraf istek | Hava durumu/Supabase **onay sonrası**; "yalnızca zorunlu" → sıfır istek |
| HUK3 | Kaynak atıfı yok | `kaynaklar/` sayfası: Wikidata (CC0), Wikipedia (CC BY-SA), Natural Earth, Open-Meteo |
| GÜV1 | HTTP başlıkları yok | Meta CSP, `referrer`, `base-uri`/`form-action` kısıtları |
| GÜV2 | Sunucu tarafı sır riski | Yalnız `publishable` anahtar; RLS testi: oturumsuz erişim **401** |

## Doğrulanan davranışlar (yerel test)

- 5 temada statik rota sırası ile uygulamadaki canlı rota **birebir aynı** (Trabzon örneği, 5/5).
- Modal: 12 kez Tab → odak hiç dışarı çıkmıyor; ESC sonrası `inert` temizleniyor.
- Paylaş → "Rota metni panoya kopyalandı"; ICS → `turkiye-kesif-*.ics` indi.
- Magic link: Supabase `auth/v1/otp` **200** döndü, "Bağlantı gönderildi" bildirimi göründü.
- Onay öncesi `open-meteo` isteği **0**, onay sonrası **1**.
- 12 farklı hash rotası + 6 statik sayfa: konsol hatası **0**.

## Canlı ölçüm (GitHub Pages, mobil 4x CPU + yavaş 4G)

| Ölçüt | v11 (denetim) | v12 (canlı) |
|---|---|---|
| LCP | — | **780 ms** |
| CLS | 0,697 | **0,04** |
| DOMContentLoaded | 9.070 ms | **2.850 ms** |
| İlk yükleme aktarımı | 2,4 MB | **834 KB** (11 istek) |
| `index.html` aktarımı | 2,4 MB | **23,7 KB** (gzip) |
| JS paketi aktarımı | — | 357 KB (gzip) |

DCL artık tamamen **bant genişliği sınırında**: 2,85 sn'nin ≈2,1 sn'si JS'in inmesi, ≈0,75 sn'si
yürütme. Daha aşağısı yalnızca veri hacmini küçültmekle mümkün; kayıt/yerleşim adları
silinmeden bu sınıra inildi (hedef 2,5 sn).

### v13 — açılış CPU'sunu düşürme

DCL'i şişiren şey veri indirme değil, açılışta yapılan iki iş olduğu ölçüldü
(`JSON.parse` 975 KB için yalnız **7 ms**):

| İş | Önce | Sonra |
|---|---|---|
| 45.060 yerleşim adını arama için sadeleştirme | 8 ayrı regex geçişi | **tek geçişli** harf eşlemesi |
| 405 rotayı açılışta kurma (en yakın komşu + 2-opt) | her zaman, ≈970 ms (4x CPU) | **tembel**: ana sayfa yalnız 3 rota kurar, tamamı `#/rotalar`'da |
| DCL (4x CPU, hızlı ağ) | 2.234 ms | **760 ms** |

Rota sayısı ekranlarda `ROUTE_COUNT = 81 × 5` ile gösterilir; davranış değişmedi
(ana sayfa 3 kart, rota sayfası 405 rota, modal ve canlı mod aynı).

**Sıradaki adım (v14):** veriyi `assets/data.<hash>.json` olarak ayırıp `fetch()` ile ilk
boyamadan sonra yüklemek — indirme süresi değişmez, `app.js` 40 KB gzip'e iner.

## v14 — Hesabım sayfası ve rota ilerlemesi

Supabase şemasında hazır olan `route_progress` tablosu ilk kez istemciye bağlandı; "favoriler ve
rota ilerlemesi tüm cihazlarda" vaadi artık iki veri türü için de çalışıyor.

| Bileşen | Ayrıntı |
|---|---|
| Yerel kayıt | `tk-progress-v1` (rota → durak), `tk-done-v1` (tamamlananlar) |
| Uzak kayıt | `route_progress(route_id, stop_index, updated_at)`, 700 ms debounce ile `upsert` |
| Birleştirme | giriş sonrası `progPull()` uzak satırları yerelle birleştirir |
| Bitirme | "Bitir" yerel kaydı tamamlananlara taşır, uzak satırı siler |
| KVKK m.11 | "Verilerimi indir" JSON dışa aktarımı, "Hesap verilerimi sil" tek tuşla silme |
| Yönlendirme | `#/hesabim`, `/hesabim/` statik sayfası (`noindex`), alt bilgi + mobil menü bağlantısı |
| Giriş akışı | giriş yapmış kullanıcıda üst sağdaki düğme doğrudan Hesabım'a gider |

Doğrulanan akışlar (yerel, sahte oturumla): rota başlat → durak ilerlet → `tk-progress-v1 = {"34-0":1}` →
Hesabım'da "İzmir — Tarih ve Kültür Rotası, 2/5 durak, sıradaki: Atatürk, Annesi ve Kadın Hakları Anıtı" →
"Devam et" rotayı 2. duraktan açar; "Bitir" tamamlananlara taşır; "Verilerimi indir" `turkiye-kesif-verilerim.json`
indirir; "Hesap verilerimi sil" onayıyla tüm anahtarlar temizlenir ve oturum kapanır. Konsol hatası yok.

### Uçtan uca giriş doğrulaması (canlı)

Gerçek bir e-posta ile (tek kullanımlık test adresi) tüm zincir çalıştırıldı:

1. `auth/v1/otp` → 200, e-posta 5 sn içinde ulaştı
2. Bağlantı → `https://xharunkoca.github.io/turkiye-kesif/#access_token=…`
3. Uygulama jetonları aldı, adresi `#/` olarak temizledi, oturum `tk-auth-v1`'de
4. Girişten önce eklenen yerel favori buluta taşındı →
   `favorites: {place_key: "34|Celsus Kütüphanesi", il: "İzmir"}`
5. Rota başlatılıp bir durak ilerletildi → `route_progress: {route_id: "34-0", stop_index: 1}`
6. `#/hesabim`: e-posta, 1 favori, 1 devam eden rota göründü; konsol hatası yok

Test verileri sonrasında silindi (0 kullanıcı, 0 favori, 0 ilerleme).

> **Not:** İlk denemede gelen bağlantı site köküne (`…github.io/#access_token`) düşmüştü.
> Doğru `email_redirect_to` yükü ile yapılan iki bağımsız testte (istemci ve curl) yönlendirme
> `…/turkiye-kesif/` olarak geldi; güncel sürümde sorun görülmedi. Yine de magic-link kurulumu
> değiştirilirse bu adres ilk kontrol edilmeli.

## v15 — açık tema (Apple sadeliğinde sade arayüz)

Kullanıcı geri bildirimi: "Hepsi ve arayüz sanki karışmış gibi aydınlı ve Apple sadeliğinde olsun."
Bu nedenle tüm yüzey beyaz zemine, ince çizgiye ve tek vurgu rengine taşındı.

| Öğe | Önce | Sonra (v15) |
|---|---|---|
| Zemin / yüzey | lacivert kesitler, renkli bantlar | `#fff`, ikincil `#f5f5f7` |
| Metin | `#16232f` + beyaz üstü yarı saydam | `#1d1d1f`, ikincil `#6e6e73` |
| Vurgu | lacivert + kırmızı + sarı | tek vurgu: `#c8102e` |
| Gölge | `0 12px 34px` ağır gölgeler | `0 1px 2px` / `0 6px 20px` yumuşak |
| Kahraman (ana) | koyu fotoğraf + karartma | fotoğrafsız, `#f7f7f9 → #fff` geçişli sade blok |
| Şehir kartı | fotoğraf üzeri beyaz geçiş | fotoğraf üstte + **beyaz metin bloğu** (plaka, ad, sayılar) |
| İl kartı | 3 px gökkuşağı şerit | ince `#d2d2d7` çerçeve |
| Mekân kartı başlığı | kategoriye göre mavi/turuncu/yeşil blok | nötr `#f5f5f7` + gri kategori etiketi |
| Rota kartı | dolu kırmızı "Başlat" | beyaz/çerçeveli düğme + metin bağlantı "İncele" |
| Mekân penceresi | 180 px koyu degrade | 110 px nötr başlık, koyu metin |
| Mevsim kartı | renkli karartma | fotoğraf + altta beyaz etiket alanı |
| Alt bilgi | koyu lacivert | `#f5f5f7` + ince üst çizgi, koyu başlıklar |
| Statik sayfalar (`PAGE_CSS`) | lacivert başlık/alt bilgi, `#b3261e` | cam efektli beyaz başlık, `#c8102e` CTA |

Teknik notlar:
- Tema ayrı bir katman: **`src/theme-light.css`**; `build.py` bunu `style.css`'in sonuna ekleyip
  hash'li tek dosya üretiyor, böylece geri alınması tek dosya silmek kadar kolay.
- `build.py` içindeki **`PAGE_CSS`** (511 statik sayfanın stili) aynı palete geçirildi.
- Apple yazı tipi yığını: `-apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", …`.
- `prefers-reduced-motion` desteği eklendi.

Doğrulamalar (yerel, Playwright + Chromium):
- 11 rota × 2 görünüm (1440×950, 390×844): **JS hatası 0**, **yatay taşma 0**.
- Kontrast taraması (WCAG AA, ~5.000 metin düğümü): ana sayfa / keşfet / hesabım / statik sayfa **0 ihlal**,
  il sayfasında yalnız geçici hava durumu iskeletinde 1 öğe kaldı (`/100`).
- Düzeltilen regresyonlar: mobil onay şeridinin tam ekran kaplaması (`flex-basis` 340 px → sütunda
  yükseklik olarak yorumlanıyordu), masaüstünde görünen boş hamburger düğmesi, beyaz üstünde
  okunmayan `.lead` ve alt bilgi başlıkları, kategori sayılarının soluk zemini.

**Canlı doğrulama (d0c9ec7):** GitHub Actions `success` → <https://xharunkoca.github.io/turkiye-kesif/>
`style.f2cd168489.css` servis ediliyor; başlık zemini `rgba(255,255,255,.92)`, statik il sayfası
`h1` rengi `rgb(29,29,31)`; ana sayfa + mobil + `/il/istanbul/` görüntüleri alındı, **JS hatası 0**;
onay şeridi "Anladım" ile kapanıyor (`tk-consent-v1` yazılıyor). Görüntüler: `shots/canli-v15-*.png`.
