/* ============================================================================
   Türkiye Keşif v2 — 81 il • 1.004 ilçe • 17.738 köy • 3.218 doğrulanmış yer
   Veri: Wikidata (koordinatlı mekânlar), Türkçe Vikipedi, TÜRKPATENT/TÜİK envanter sayıları
   ========================================================================== */
(function () {
  "use strict";

  const D = window.__DATA__;
  const ILS = D.ils;
  const CATS = D.cats;
  const PLACES = D.places;
  const N_IL = ILS.length;

  const $ = (s, r = document) => r.querySelector(s);
  const on = (sel, ev, fn) => { const el = typeof sel === "string" ? $(sel) : sel; if (el) el.addEventListener(ev, fn); return el; };
  const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
  const icon = (id, cls) => `<svg width="16" height="16" aria-hidden="true"${cls ? ` class="${cls}"` : ""}><use href="#${id}"/></svg>`;
  const nf = (n) => Number(n).toLocaleString("tr-TR");
  const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  /* ---------------------------------------------------------------- indeksler */
  const byIl = ILS.map(() => []);
  const byIlCat = ILS.map(() => CATS.map(() => []));
  const ilByName = {};
  ILS.forEach((il, i) => { ilByName[il.n] = i; });

  PLACES.forEach((p, idx) => {
    p.idx = idx;
    byIl[p[2]].push(p);
    byIlCat[p[2]][p[1]].push(p);
  });

  const VILLAGES = [];
  ILS.forEach((il, i) => il.d.forEach((d) => {
    d.k.forEach((k) => VILLAGES.push({ n: k, il: i, d: d.n, t: "köy" }));
    (d.m || []).forEach((m) => VILLAGES.push({ n: m, il: i, d: d.n, t: "mahalle" }));
  }));

  // tek geçişli Türkçe sadeleştirme (8 ayrı regex yerine) — 45 bin yerleşim adında fark eder
  const TR_MAP = { "ı": "i", "ş": "s", "ğ": "g", "ü": "u", "ö": "o", "ç": "c", "â": "a", "î": "i", "û": "u" };
  const TR_RE = /[ışğüöçâîû]/g;
  const norm = (s) => String(s || "").toLocaleLowerCase("tr").replace(TR_RE, (c) => TR_MAP[c]);

  const IL_SEARCH = ILS.map((il, i) => ({ i, k: norm(il.n) }));
  const DIST_SEARCH = [];
  ILS.forEach((il, i) => il.d.forEach((d) => DIST_SEARCH.push({ i, d: d.n, k: norm(d.n) })));
  const VILLAGE_SEARCH = VILLAGES.map((v) => ({ ...v, k: norm(v.n) }));
  const PLACE_SEARCH = PLACES.map((p) => ({ p, k: norm(p[0] + " " + (p[6] || "")) }));

  const villCount = (il) => il.d.reduce((a, d) => a + d.k.length + (d.m ? d.m.length : 0), 0);
  const distCount = (il) => il.d.length;

  // Wikidata sınıf etiketlerini okunur Türkçe rozetlere çevir
  const TYPE_LABELS = {
    "harabe": "Ören yeri", "höyük": "Höyük", "antik kent": "Antik kent", "ören yeri": "Ören yeri",
    "kale": "Kale", "kule": "Kule", "sur": "Sur", "köprü": "Köprü", "su kemeri": "Su kemeri",
    "sarnıç": "Sarnıç", "tiyatro": "Antik tiyatro", "tapınak": "Tapınak", "bazilika": "Bazilika",
    "anıt mezar": "Anıt mezar", "tümülüs": "Tümülüs", "nekropol": "Nekropol",
    "kervansaray": "Kervansaray", "han": "Han", "bedesten": "Bedesten", "arasta": "Arasta",
    "çarşı": "Çarşı", "pazar": "Pazar", "pazar yeri": "Pazar yeri", "pasaj": "Pasaj",
    "hamam": "Hamam", "kaplıca": "Kaplıca", "medrese": "Medrese", "konak": "Konak",
    "cami": "Cami", "mescit": "Mescit", "kilise": "Kilise", "manastır": "Manastır",
    "sinagog": "Sinagog", "türbe": "Türbe", "ziyaret yeri": "Ziyaret yeri",
    "müze": "Müze", "millî park": "Millî park", "tabiat parkı": "Tabiat parkı",
    "tabiat anıtı": "Tabiat anıtı", "göl": "Göl", "baraj": "Baraj", "baraj gölü": "Baraj gölü",
    "şelale": "Şelale", "mağara": "Mağara", "kanyon": "Kanyon", "vadi": "Vadi",
    "plaj": "Plaj", "koy": "Koy", "yayla": "Yayla", "kamp alanı": "Kamp alanı",
    "orman": "Orman", "ada": "Ada", "tepe": "Tepe", "dağ": "Dağ", "anıt": "Anıt",
    "tarihî bina": "Tarihî bina", "arkeolojik sit": "Arkeolojik sit", "dükkân": "Dükkân"
  };
  const typeLabel = (t) => {
    if (!t) return "";
    const k = norm(String(t)).trim();
    if (TYPE_LABELS[k]) return TYPE_LABELS[k];
    return String(t).charAt(0).toLocaleUpperCase("tr") + String(t).slice(1);
  };

  // konumu doğrulanmış kayıtlar listede önce gelir
  const byCoordFirst = (list) => list.slice().sort((x, y) => (y[4] != null) - (x[4] != null));

  const dedupeByName = (list) => {
    const seen = new Set();
    return list.filter((p) => { const k = norm(p[0]); if (seen.has(k)) return false; seen.add(k); return true; });
  };

  // aynı yerin iki kategoride görünmesi sayıları şişirmesin: gösterimde tekilleştirilmiş listeler
  const byIlUniq = byIl.map((l) => dedupeByName(l));
  const PLACE_COUNT = byIlUniq.reduce((a, l) => a + l.length, 0);
  const PLACE_VERIFIED = byIlUniq.reduce((a, l) => a + l.filter((p) => p[4] != null).length, 0);

  const slug = (s) => norm(s).replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
  const IL_SLUG = ILS.map((il) => slug(il.n));
  // ilçe slug haritası: ilSlug -> { ilceSlug: ilçe indeksi }
  const DIST_SLUG = ILS.map((il) => {
    const m = {};
    il.d.forEach((d, di) => { m[slug(d.n)] = di; });
    return m;
  });
  const ilBySlug = {};
  IL_SLUG.forEach((s, i) => { ilBySlug[s] = i; });

  const catById = {};
  CATS.forEach((c, i) => { catById[c.id] = i; });

  // mevsim profilleri: her mevsim öne çıkan kategoriler + önerilen rota teması
  const SEASONS = [
    {
      id: "ilkbahar", n: "İlkbahar", months: "Mart – Mayıs", color: "#2f8f63", img: "assets/img/ilkbahar-420.webp",
      desc: "Badem ve kiraz çiçekleri, yürüyüşe en uygun sıcaklıklar. Vadiler, şelaleler ve yaylalar bu mevsimde zirvede.",
      cats: ["doga", "yayla", "gol", "selale", "vadi", "antik"], theme: "doga"
    },
    {
      id: "yaz", n: "Yaz", months: "Haziran – Ağustos", color: "#1a6fa8", img: "assets/img/yaz-420.webp",
      desc: "Koylar, Mavi Bayraklı plajlar ve yayla serinliği. Kıyı illerinde deniz, iç bölgelerde yüksek yaylalar öne çıkar.",
      cats: ["plaj", "gol", "yayla", "doga", "termal"], theme: "deniz"
    },
    {
      id: "sonbahar", n: "Sonbahar", months: "Eylül – Kasım", color: "#b8641c", img: "assets/img/sonbahar-420.webp",
      desc: "Orman yürüyüşleri, hasat ve gastronomi zamanı; kalabalık azalır, antik kentler ve tarihî çarşılar keyifli olur.",
      cats: ["doga", "yayla", "tarih", "kultur", "gastro"], theme: "tarih"
    },
    {
      id: "kis", n: "Kış", months: "Aralık – Şubat", color: "#275d8f", img: "assets/img/kis-420.webp",
      desc: "Termal kaplıcalar, müzeler, mağaralar ve inanç mirası. Kapalı mekân ve şifa odaklı bir kış programı.",
      cats: ["termal", "muze", "kultur", "tarih", "magara", "dini"], theme: "inanc"
    }
  ];
  const seasonById = {};
  SEASONS.forEach((x) => { seasonById[x.id] = x; });

  // kategori kısa açıklamaları (kategori sayfası ve kart başlıklarında)
  const CAT_DESC = {
    antik: "Antik kentler, höyükler ve arkeolojik sitler — Anadolu'nun Tunç Çağı'ndan Roma'ya uzanan yerleşim izleri.",
    muze: "Bakanlığa bağlı ve özel müzeler; arkeoloji, etnografya ve sanat koleksiyonları.",
    doga: "Millî parklar, tabiat parkları, tabiat anıtları ve korunan doğal alanlar.",
    tarih: "Kale, han, kervansaray, köprü ve tescilli sivil mimarlık örnekleri.",
    gol: "Doğal göller, set ve krater gölleri, sulak alanlar.",
    selale: "Şelaleler ve çağlayanlar; kaynak sularının basamaklı döküldüğü vadiler.",
    magara: "Turizme açık mağaralar; damlataş oluşumları ve karstik boşluklar.",
    vadi: "Kanyonlar ve vadiler; akarsu aşındırmasıyla oluşan derin geçitler.",
    plaj: "Mavi Bayraklı plajlar, koylar ve kıyı şeritleri.",
    gastro: "Yöresel mutfak, coğrafi işaretli ürünler ve yerel lezzet durakları.",
    yayla: "Yaylalar, kamp ve karavan alanları, doğa yürüyüşü başlangıç noktaları.",
    dini: "Cami, kilise, manastır, türbe ve ziyaret yerleri.",
    kultur: "Anıtlar, kütüphaneler ve kültür-sanat mekânları.",
    termal: "Kaplıca ve termal tesisler; jeotermal kaynakların bulunduğu ilçeler.",
    carsi: "Tarihî çarşılar, bedestenler, arastalar ve haftalık pazarlar."
  };

  const CAT_COLORS = ["#2f6fbe", "#c97716", "#2f9b52", "#c0392b", "#12869b", "#1f9fae",
    "#7a48c7", "#d97706", "#0f87a8", "#b4500f", "#3f8f3f", "#7749b8", "#8a56c9",
    "#2b6f9e", "#b3303a"];

  // koordinat varsa doğrudan nokta; yoksa ad + ilçe + il ile arama (her zaman doğru sonuç)
  const maps = (lat, lon) => `https://www.google.com/maps/search/?api=1&query=${lat},${lon}`;
  const mapsPlace = (p) => {
    if (p[4] != null && p[5] != null) return maps(p[4], p[5]);
    const q = [p[0], p[3], ILS[p[2]].n, "Türkiye"].filter(Boolean).join(", ");
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}`;
  };
  const hasCoord = (p) => p[4] != null && p[5] != null;
  // iki durak arası yol tarifi
  const dirUrl = (a, b) =>
    `https://www.google.com/maps/dir/?api=1&origin=${a[4]},${a[5]}&destination=${b[4]},${b[5]}&travelmode=driving`;
  // rotanın tamamı: ilk durak → son durak, aradakiler ara durak (waypoints)
  function routeDirUrl(r) {
    const st = r.stops.filter(hasCoord);
    if (st.length === 0) return "#";
    if (st.length === 1) return maps(st[0][4], st[0][5]);
    const o = st[0], d = st[st.length - 1];
    const w = st.slice(1, -1).map((p) => `${p[4]},${p[5]}`).join("|");
    return `https://www.google.com/maps/dir/?api=1&origin=${o[4]},${o[5]}&destination=${d[4]},${d[5]}` +
      (w ? `&waypoints=${encodeURIComponent(w)}` : "") + "&travelmode=driving";
  }
  const wdUrl = (name) => `https://www.wikidata.org/w/index.php?search=${encodeURIComponent(name)}`;
  const wikiUrl = (name) => `https://tr.wikipedia.org/w/index.php?search=${encodeURIComponent(name)}`;

  function haversine(a, b) {
    const R = 6371, p = Math.PI / 180;
    const dLat = (b[0] - a[0]) * p, dLon = (b[1] - a[1]) * p;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[0] * p) * Math.cos(b[0] * p) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  }

  /* ---------------------------------------------------------------- favoriler */
  const FAV_KEY = "tk-favs-v2";
  let favs = [];
  try { favs = JSON.parse(localStorage.getItem(FAV_KEY) || "[]"); } catch (e) { favs = []; }
  const favId = (p) => `${p[2]}|${p[0]}`;
  const isFav = (p) => favs.includes(favId(p));
  function toggleFav(p) {
    const id = favId(p);
    if (favs.includes(id)) { favs = favs.filter((f) => f !== id); toast(`"${p[0]}" favorilerden çıkarıldı`); }
    else { favs = [...favs, id]; toast(`"${p[0]}" favorilere eklendi`); }
    try { localStorage.setItem(FAV_KEY, JSON.stringify(favs)); } catch (e) { /* yoksay */ }
    $$(`[data-fav="${CSS.escape(id)}"]`).forEach((b) => b.classList.toggle("on", favs.includes(id)));
    updateFavCount();
    if (auth) {
      if (favs.includes(id)) syncFavorites(); else removeRemoteFav(id);
    }
  }
  function updateFavCount() {
    $$("[data-fav-count]").forEach((el) => {
      el.textContent = favs.length ? `(${favs.length})` : "";
      el.style.fontSize = "11px"; el.style.opacity = ".8";
    });
  }

  /* ---------------------------------------------------------------- toast */
  let toastTimer;
  function toast(msg) {
    const t = $("#toast");
    $("#toastText").textContent = msg;
    t.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove("show"), 2800);
  }

  /* ---------------------------------------------------------------- harita */
  const MB = { lon0: 26.043351, lon1: 44.79399, lat0: 35.821535, lat1: 42.141485, W: 1000, pad: 8 };
  (function () {
    MB.sx = (MB.W - 2 * MB.pad) / (MB.lon1 - MB.lon0);
    MB.sy = MB.sx / Math.cos(((MB.lat0 + MB.lat1) / 2) * Math.PI / 180);
  })();
  const project = (lat, lon) => [MB.pad + (lon - MB.lon0) * MB.sx, MB.pad + (MB.lat1 - lat) * MB.sy];

  const PROV = (window.TR_PROVINCES || []);
  const IL_BY_NAME = {};
  ILS.forEach((il, i) => { IL_BY_NAME[il.n] = i; });

  function provColor(i) {
    const h = (i * 0.61803398875) % 1;
    const s = 0.58 + ((i * 7) % 5) * 0.038;
    const l = 0.825 + ((i * 3) % 4) * 0.014;
    const f = (n) => {
      const k = (n + h * 12) % 12;
      const a = s * Math.min(l, 1 - l);
      const c = (x) => l - a * Math.max(-1, Math.min(k - 3, 9 - k, 1));
      return Math.round(255 * c(n));
    };
    return `rgb(${f(0)},${f(8)},${f(4)})`;
  }

  function provPaths() {
    return PROV.map((p, i) => {
      const idx = IL_BY_NAME[p.n];
      const label = idx == null ? p.n : ILS[idx].n;
      return `<path class="prov" d="${p.d}" fill="${provColor(i)}"${idx == null ? "" : ` data-il="${idx}"`}
        tabindex="${idx == null ? "-1" : "0"}" role="button" aria-label="${esc(label)}"><title>${esc(label)}</title></path>`;
    }).join("");
  }

  /* ------------------------------------------ harita: il adı / baş harf katmanı */
  function mountMapLabels(wrap, svg) {
    if (!wrap || !svg || !PROV.length) return;
    wrap.classList.add("has-labels");
    let layer = wrap.querySelector(".map-labels");
    if (!layer) { layer = document.createElement("div"); layer.className = "map-labels"; wrap.appendChild(layer); }
    const canvas = mountMapLabels._c || (mountMapLabels._c = document.createElement("canvas"));
    const ctx = canvas.getContext("2d");
    const place = () => {
      layer.innerHTML = "";
      const ctm = svg.getScreenCTM && svg.getScreenCTM();
      const wr = wrap.getBoundingClientRect();
      if (!ctm || wr.width < 60) return;
      const names = wr.width >= 600;                 // geniş haritada il adı, dar haritada baş harf
      const base = names ? (wr.width >= 900 ? 10.5 : 9.5) : (wr.width < 420 ? 8.5 : 9.5);
      const pt = svg.createSVGPoint ? svg.createSVGPoint() : null;
      const used = [];
      const spots = PROV.map((p) => p).sort((a, b) => b.a - a.a);
      const cands = [[0, 0], [0, -3], [0, 3], [-3, 0], [3, 0], [0, -6], [0, 6], [-6, 0], [6, 0], [0, -9], [0, 9], [-9, 0], [9, 0]];
      const done = new Set();
      // iki geçiş: önce normal boy, sığmayanlar biraz küçük yazıyla
      for (const fs of [base, Math.max(6.8, base * 0.82), Math.max(6.2, base * 0.70)]) {
        ctx.font = `600 ${fs}px -apple-system, "SF Pro Text", system-ui, sans-serif`;
        const h = fs + 1;
        for (const p of spots) {
          if (done.has(p.n)) continue;
          let sx, sy;
          try { pt.x = p.x; pt.y = p.y; const sc = pt.matrixTransform(ctm); sx = sc.x; sy = sc.y; }
          catch (e) { continue; }
          const cx = sx - wr.left, cy = sy - wr.top;
          if (cx < 0 || cy < 0 || cx > wr.width || cy > wr.height) continue;
          const text = names ? p.n : p.n.charAt(0).toLocaleUpperCase("tr");
          const tw = ctx.measureText(text).width;
          let pick = null;
          for (const [dx, dy] of cands) {
            const r = { x: cx + dx - tw / 2 - 1, y: cy + dy - h / 2, w: tw + 2, h };
            if (r.x < 1 || r.y < 1 || r.x + r.w > wr.width - 1 || r.y + r.h > wr.height - 1) continue;
            const hit = used.some((u) => !(r.x + r.w + 1.5 < u.x || r.x > u.x + u.w + 1.5 || r.y + r.h + 1 < u.y || r.y > u.y + u.h + 1));
            if (!hit) { pick = r; break; }
          }
          if (!pick) continue;
          used.push(pick);
          done.add(p.n);
          const sp = document.createElement("span");
          sp.className = "map-label" + (names ? "" : " initial");
          sp.textContent = text;
          sp.style.left = (pick.x + pick.w / 2).toFixed(1) + "px";
          sp.style.top = (pick.y + pick.h / 2).toFixed(1) + "px";
          sp.style.fontSize = fs + "px";
          layer.appendChild(sp);
        }
      }
    };
    place();
    if (wrap._labelResize) window.removeEventListener("resize", wrap._labelResize);
    let t = 0;
    wrap._labelResize = () => { clearTimeout(t); t = setTimeout(place, 140); };
    window.addEventListener("resize", wrap._labelResize, { passive: true });
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => setTimeout(place, 80));
  }

  /* ---------------------------------------------------------------- rotalar */
  const THEMES = [
    { key: "tarih", label: "Tarih ve Kültür Rotası", cats: ["antik", "tarih", "muze", "kultur"], color: "#b3261e" },
    { key: "doga", label: "Doğa ve Manzara Rotası", cats: ["doga", "gol", "selale", "vadi", "yayla"], color: "#1f7a4d" },
    { key: "inanc", label: "İnanç ve Miras Rotası", cats: ["dini", "carsi", "muze"], color: "#5b3fa8" },
    { key: "lezzet", label: "Lezzet Durakları Rotası", cats: ["gastro", "carsi"], color: "#c76a00" },
    { key: "deniz", label: "Deniz ve Şifa Rotası", cats: ["plaj", "termal", "gol", "doga"], color: "#0e6f86" },
  ];

  // aynı yerin iki kaydı mı? (aynı ad ya da biri diğerini kapsıyor + 5 km)
  function sameSpot(a, b, il) {
    const nm = (x) => norm(x[0]).replace(/\b(milli|milli parki|milli park)\b/g, "milli park")
      .replace(new RegExp("\\b" + norm(il.n) + "\\b", "g"), "").trim();
    const na = nm(a), nb = nm(b);
    const d = haversine([a[4], a[5]], [b[4], b[5]]);
    if (d > 5) return false;
    if (na === nb) return true;
    if (na.length > 6 && nb.length > 6 && (na.includes(nb) || nb.includes(na))) return true;
    return d < 0.6;
  }

  function nearestPath(stops, start) {
    const rest = stops.slice();
    const path = [];
    let cur = start;
    while (rest.length) {
      let bi = 0, bd = Infinity;
      rest.forEach((p, i) => {
        const d = haversine(cur, [p[4], p[5]]);
        if (d < bd) { bd = d; bi = i; }
      });
      const next = rest.splice(bi, 1)[0];
      path.push(next);
      cur = [next[4], next[5]];
    }
    return path;
  }

  // 2-opt: güzergâh üzerindeki kesişmeleri kaldırır
  function twoOpt(path, start) {
    const pts = [start, ...path.map((p) => [p[4], p[5]])];
    const seq = pts.map((_, i) => i);
    const d = (a, b) => haversine(pts[a], pts[b]);
    let improved = true, guard = 0;
    while (improved && guard++ < 40) {
      improved = false;
      for (let i = 1; i < seq.length - 1; i++) {
        for (let k = i + 1; k < seq.length; k++) {
          const a = seq[i - 1], b = seq[i], c = seq[k], e = seq[k + 1] ?? null;
          const before = d(a, b) + (e !== null ? d(c, e) : 0);
          const after = d(a, c) + (e !== null ? d(b, e) : 0);
          if (after + 1e-9 < before) {
            const seg = seq.slice(i, k + 1).reverse();
            seq.splice(i, k - i + 1, ...seg);
            improved = true;
          }
        }
      }
    }
    const out = seq.slice(1).map((i) => path[i - 1]);
    return out;
  }

  function routeStats(stops, il) {
    let km = 0;
    for (let i = 1; i < stops.length; i++) km += haversine([stops[i - 1][4], stops[i - 1][5]], [stops[i][4], stops[i][5]]);
    km = Math.max(1, Math.round(km));
    const days = Math.min(4, Math.max(1, Math.round(km / 70) || 1));
    const level = km < 45 ? "Kolay" : km < 110 ? "Orta" : "Zor";
    return { km, days, level };
  }

  const routeCache = {};
  function routesFor(ilIdx) {
    if (routeCache[ilIdx]) return routeCache[ilIdx];
    const il = ILS[ilIdx];
    const pool = byIl[ilIdx].filter(hasCoord);   // rota yalnızca konumu doğrulanmış duraklarla kurulur
    const center = [il.lat, il.lon];
    const used = new Set();
    const seeds = [];   // her rotanın çekirdek noktası: rotalar il geneline yayılır
    const routes = THEMES.map((th, ti) => {
      let items = pool.filter((p) => th.cats.includes(CATS[p[1]].id) && !used.has(p.idx));
      if (items.length < 2) items = pool.filter((p) => !used.has(p.idx));

      // 1) çekirdek durak: ilk rota il merkezine en yakın, sonrakiler önceki çekirdeklere en uzak
      let seed = null, best = -Infinity;
      items.forEach((p) => {
        const pt = [p[4], p[5]];
        const score = seeds.length
          ? Math.min(...seeds.map((s2) => haversine(s2, pt)))
          : -haversine(center, pt);
        if (score > best) { best = score; seed = p; }
      });
      const chosen = seed ? [seed] : [];

      // 2) çekirdeğin çevresinde kompakt küme: her adımda kümeye en yakın durak eklenir
      const tmp = items.filter((p) => p !== seed && !chosen.some((c) => sameSpot(c, p, il)));
      while (tmp.length && chosen.length < 5) {
        let bi = -1, bd = Infinity;
        tmp.forEach((p, i) => {
          if (chosen.some((c) => sameSpot(c, p, il))) return;
          const d = Math.min(...chosen.map((c) => haversine([c[4], c[5]], [p[4], p[5]])));
          // çok yakın duraklar (aynı avlu) yerine 2 km'den uzak en yakın durağı tercih et
          const w = d < 2 ? d + 40 : d;
          if (w < bd) { bd = w; bi = i; }
        });
        if (bi < 0) break;
        chosen.push(tmp.splice(bi, 1)[0]);
      }
      // rota en az 4 durak olsun: kullanılmayan yerlerden tamamla
      if (chosen.length < 4) {
        pool.filter((p) => !used.has(p.idx) && !chosen.includes(p) &&
            !chosen.some((c) => sameSpot(c, p, il)))
          .sort((a, b) => haversine(center, [a[4], a[5]]) - haversine(center, [b[4], b[5]]))
          .forEach((p) => { if (chosen.length < 4) chosen.push(p); });
      }
      if (chosen.length < 3) {
        pool.forEach((p) => { if (chosen.length < 3 && !chosen.includes(p)) chosen.push(p); });
      }
      chosen.forEach((p) => used.add(p.idx));
      if (seed) seeds.push([seed[4], seed[5]]);

      // 3) sıralama: il merkezinden en yakın komşu + 2-opt ile kısaltma
      const stops = twoOpt(nearestPath(chosen, center), center);
      const st = routeStats(stops, il);
      return { id: `${ilIdx}-${ti}`, ilIdx, theme: th, stops, ...st };
    });
    routeCache[ilIdx] = routes;
    return routes;
  }

  // Rotalar tembel üretilir: ana sayfa yalnız 3 örnek rota ister; 81 il × 5 temayı
  // baştan kurmak (en yakın komşu + 2-opt) mobilde ≈1 sn CPU harcıyordu.
  const ALL_ROUTES = [];
  const ROUTE_COUNT = N_IL * THEMES.length;
  let routesBuilt = false;
  function allRoutes() {
    if (!routesBuilt) {
      routesBuilt = true;
      ILS.forEach((il, i) => routesFor(i).forEach((r) => ALL_ROUTES.push(r)));
    }
    return ALL_ROUTES;
  }

  /* ---------------------------------------------------------------- parçalar */
  function catIcon(catIdx, size) {
    const c = CATS[catIdx];
    return `<svg width="${size || 18}" height="${size || 18}" aria-hidden="true"><use href="#${c.icon}"/></svg>`;
  }

  function placeCard(p) {
    const cat = CATS[p[1]];
    const color = CAT_COLORS[p[1]];
    const il = ILS[p[2]];
    const fav = isFav(p) ? " on" : "";
    return `<article class="p-card">
      <div class="p-head" style="--c:${color}">
        <span class="p-ic">${catIcon(p[1], 22)}</span>
        <span class="p-type">${esc(p[6] ? typeLabel(p[6]) : cat.label)}</span>
        <button class="fav-btn${fav}" data-fav="${esc(favId(p))}" aria-label="${esc(p[0])} favorilere ekle">${icon("i-heart", "i14")}</button>
      </div>
      <div class="p-body">
        <h3><button class="p-title" data-place="${p.idx}">${esc(p[0])}</button></h3>
        <p class="p-loc">${icon("i-pin")}<span>${esc(p[3] || il.n)}${p[3] ? ", " + esc(il.n) : ""}</span></p>
        <div class="p-foot">
          <a class="goto" href="${mapsPlace(p)}" target="_blank" rel="noopener noreferrer"${hasCoord(p) ? "" : ' title="Koordinat doğrulanmadı — haritada ada göre aranır"'}>${icon("i-nav")}${hasCoord(p) ? "Konuma git" : "Ada göre ara"}</a>
          <span class="p-src${hasCoord(p) ? "" : " p-src-nc"}" title="${hasCoord(p) ? "Kaynak: " + (p[7] === "approx" ? "il merkezi (yaklaşık)" : p[7] === "wikipedia" ? "Türkçe Vikipedi koordinatı" : "Wikidata") : "Koordinat doğrulanamadı; adres/arama ile bulunur"}">${hasCoord(p) ? (p[7] === "approx" ? "≈ konum" : "✓ doğrulandı") : "konum yok"}</span>
        </div>
      </div>
    </article>`;
  }

  function routeCard(r, opts) {
    const o = opts || {};
    const il = ILS[r.ilIdx];
    const stops = r.stops.slice(0, 4).map((s) => esc(s[0]));
    return `<article class="route-item" data-route="${r.id}">
      <div class="ri-top" style="--c:${r.theme.color}">
        <span class="ri-badge">${esc(r.theme.label.replace(" Rotası", ""))}</span>
        <span class="ri-il">${esc(il.n)}</span>
      </div>
      <h3>${esc(il.n)} — ${esc(r.theme.label)}</h3>
      <p class="ri-stops">${stops.join(" → ")}${r.stops.length > 4 ? " …" : ""}</p>
      <div class="ri-meta">
        <span>${icon("i-clock")}${r.days} gün</span>
        <span>${icon("i-ruler")}${nf(r.km)} km</span>
        <span>${icon("i-level")}${r.level}</span>
        <span>${icon("i-pin")}${r.stops.length} durak</span>
      </div>
      <div class="ri-actions">
        <button class="btn btn-red ri-btn" data-live-start="${r.id}">${icon("i-nav")}Başlat</button>
        <button class="btn btn-ghost ri-btn2" data-route="${r.id}">İncele ${icon("i-arrow-right")}</button>
      </div>
    </article>`;
  }

  function ilCard(i, opts) {
    const il = ILS[i];
    const count = byIlUniq[i].length;
    const villages = villCount(il);
    const o = opts || {};
    return `<a class="il-card" href="#/il/${IL_SLUG[i]}">
      <span class="il-plate">${String(il.p).padStart(2, "0")}</span>
      <span class="il-name">${esc(il.n)}</span>
      <span class="il-region">${esc(il.r)} Bölgesi</span>
      <span class="il-stats">
        <span>${icon("i-pin")}${nf(count)} yer</span>
        <span>${icon("i-building")}${nf(il.d.length)} ilçe</span>
        ${o.villages === false ? "" : `<span>${icon("i-village")}${nf(villages)} köy/mahalle</span>`}
      </span>
    </a>`;
  }

  /* ---------------------------------------------------------------- arama */
  function searchAll(q, limit) {
    const k = norm(q);
    const lim = limit || 6;
    if (!k) {
      return { ils: ILS.map((il, i) => i).slice(0, lim).map((i) => ({ i })), dists: [], villages: [], places: [] };
    }
    const ils = IL_SEARCH.filter((x) => x.k.includes(k)).map((x) => ({ i: x.i })).slice(0, lim);
    const dists = DIST_SEARCH.filter((x) => x.k.includes(k)).slice(0, lim);
    const villages = VILLAGE_SEARCH.filter((x) => x.k.startsWith(k)).slice(0, lim);
    const seen = new Set();
    const places = PLACE_SEARCH.filter((x) => x.k.includes(k)).map((x) => x.p)
      .filter((p) => { const key = p[0].toLowerCase(); if (seen.has(key)) return false; seen.add(key); return true; })
      .slice(0, lim * 2);
    return { ils, dists, villages, places };
  }

  function renderSuggest(q) {
    const r = searchAll(q, 5);
    const box = $("#suggest");
    const parts = [];
    if (r.ils.length) {
      parts.push(`<div class="suggest-head">İller</div>` + r.ils.map((x) =>
        `<a class="suggest-item" href="#/il/${IL_SLUG[x.i]}"><span class="suggest-ic">${icon("i-building")}</span>
          <span><span class="suggest-t">${esc(ILS[x.i].n)}</span><span class="suggest-m">${esc(ILS[x.i].r)} Bölgesi • ${nf(byIlUniq[x.i].length)} keşif noktası</span></span></a>`).join(""));
    }
    if (r.dists.length) {
      parts.push(`<div class="suggest-head">İlçeler</div>` + r.dists.map((x) =>
        `<a class="suggest-item" href="#/ilce/${IL_SLUG[x.i]}/${slug(x.d)}"><span class="suggest-ic">${icon("i-pin")}</span>
          <span><span class="suggest-t">${esc(x.d)}</span><span class="suggest-m">${esc(ILS[x.i].n)}</span></span></a>`).join(""));
    }
    if (r.villages.length) {
      parts.push(`<div class="suggest-head">Köy ve mahalleler</div>` + r.villages.map((x) =>
        `<a class="suggest-item" href="#/kesfet?il=${x.il}&ilce=${encodeURIComponent(x.d)}"><span class="suggest-ic">${icon("i-village")}</span>
          <span><span class="suggest-t">${esc(x.n)}</span><span class="suggest-m">${esc(x.t)} • ${esc(x.d)}, ${esc(ILS[x.il].n)}</span></span></a>`).join(""));
    }
    if (r.places.length) {
      parts.push(`<div class="suggest-head">Gezilecek yerler</div>` + r.places.map((p) =>
        `<button class="suggest-item" data-place="${p.idx}"><span class="suggest-ic">${catIcon(p[1])}</span>
          <span><span class="suggest-t">${esc(p[0])}</span><span class="suggest-m">${esc(CATS[p[1]].label)} • ${esc(p[3] || ILS[p[2]].n)}, ${esc(ILS[p[2]].n)}</span></span></button>`).join(""));
    }
    if (!parts.length) {
      box.innerHTML = `<div class="suggest-empty">"${esc(q)}" için sonuç bulunamadı. Bir il, ilçe, köy veya yer adı deneyin.</div>`;
    } else {
      box.innerHTML = parts.join("") +
        `<a class="suggest-all" href="#/kesfet?q=${encodeURIComponent(q)}">Tüm sonuçları gör ${icon("i-arrow-right")}</a>`;
    }
    box.classList.add("show");
  }

  /* ---------------------------------------------------------------- modal */
  const modal = $("#modal");
  const modalContent = $("#modalContent");
  let lastFocus = null;

  function openModal(html, cls) {
    lastFocus = document.activeElement;
    modalContent.innerHTML = html;
    $("#modalCard").className = "modal-card " + (cls || "");
    modal.classList.add("open");
    document.body.style.overflow = "hidden";
    trapStart();
    const c = $(".modal-close");
    if (c) requestAnimationFrame(() => c.focus());
  }
  function closeModal() {
    const mm = document.querySelector(".modal-map");
    if (mm && mm._labelResize) { window.removeEventListener("resize", mm._labelResize); mm._labelResize = null; }
    modal.classList.remove("open");
    document.body.style.overflow = "";
    trapEnd();
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  function openPlace(idx) {
    const p = PLACES[idx];
    if (!p) return;
    const il = ILS[p[2]];
    const cat = CATS[p[1]];
    const nearby = (hasCoord(p)
      ? byIl[p[2]].filter((q) => q.idx !== p.idx && hasCoord(q))
          .sort((a, b) => haversine([p[4], p[5]], [a[4], a[5]]) - haversine([p[4], p[5]], [b[4], b[5]]))
      : byIl[p[2]].filter((q) => q.idx !== p.idx && norm(q[3]) === norm(p[3])))
      .slice(0, 4);
    openModal(`
      <div class="modal-hero" style="background:linear-gradient(135deg,${CAT_COLORS[p[1]]},#0a2c52)">
        <span class="mh-ic">${catIcon(p[1], 40)}</span>
        <span class="mh-cat">${esc(cat.label)}</span>
      </div>
      <div class="modal-body">
        <h3 id="modalTitle">${esc(p[0])}</h3>
        <p class="sub">${p[3] ? esc(p[3]) + ", " + esc(il.n) : esc(il.n)} • ${esc(il.r)} Bölgesi</p>
        <div class="modal-tags">
          ${p[6] ? `<span class="tag">${esc(typeLabel(p[6]))}</span>` : ""}
          <span class="tag">${esc(cat.label)}</span>
          <span class="tag${hasCoord(p) ? "" : " tag-nc"}">${hasCoord(p) ? (p[7] === "approx" ? "≈ yaklaşık konum" : "✓ doğrulanmış konum") : "konum doğrulanmadı"}</span>
        </div>
        <div class="modal-stats">
          ${hasCoord(p)
            ? `<div class="stat"><b>${p[4].toFixed(4)}</b><span>Enlem</span></div>
               <div class="stat"><b>${p[5].toFixed(4)}</b><span>Boylam</span></div>
               <div class="stat"><b>${esc(il.p)}</b><span>Plaka</span></div>`
            : `<div class="stat"><b>${esc(il.p)}</b><span>Plaka</span></div>
               <div class="stat"><b>${esc(p[3] || il.n)}</b><span>İlçe</span></div>
               <div class="stat"><b>—</b><span>Koordinat</span></div>`}
        </div>
        <p style="font-size:12.5px;color:#5b6f82;line-height:1.6">
          ${esc(p[0])}, ${esc(il.n)} ilinin ${p[3] ? esc(p[3]) + " ilçesinde" : "merkezinde"} yer alıyor.
          ${hasCoord(p)
            ? `Konum bilgisi ${p[7] === "approx" ? "il merkezi referans alınarak yaklaşık olarak" : p[7] === "wikipedia" ? "Türkçe Vikipedi koordinatlarından" : "Wikidata'dan"} alınmıştır.`
            : "Koordinatı doğrulanamadığı için harita bağlantısı ad ve ilçe bilgisiyle arama yapar; konum yanlış gösterilmez."}
        </p>
        <div class="nearby">
          <div class="nearby-title">Yakındaki keşifler</div>
          <div class="nearby-list">
            ${nearby.map((q) => `<button class="nearby-item" data-place="${q.idx}">${catIcon(q[1], 15)}<span>${esc(q[0])}</span></button>`).join("")}
          </div>
        </div>
        <div class="modal-actions">
          <a class="btn btn-red" href="${mapsPlace(p)}" target="_blank" rel="noopener noreferrer" title="${hasCoord(p) ? "Google Maps'te konumu açar" : "Koordinat doğrulanmadı — haritada ada göre aranır"}">${icon("i-nav")}${hasCoord(p) ? "Konuma git" : "Ada göre ara"}</a>
          <button class="btn btn-ghost" data-fav="${esc(favId(p))}">${icon("i-heart")}Favorilere ekle</button>
          <a class="btn btn-ghost" href="#/kesfet?il=${p[2]}&kat=${cat.id}" data-close-nav>${icon("i-compass")}Benzer yerler</a>
          <a class="btn btn-ghost" href="${(p[7] === "approx" || p[7] === "wikipedia") ? wikiUrl(p[0]) : wdUrl(p[0])}" target="_blank" rel="noopener noreferrer">${icon("i-external")}Kaynağa git</a>
        </div>
      </div>`);
  }

  // rotanın duraklarını yerel ölçekli bir mini haritada çizer
  function routeMapSvg(r, il) {
    const pts = r.stops.map((st, i) => ({ n: st[0], lat: st[4], lon: st[5], i }));
    if (pts.length < 2) return "";
    const lats = pts.map((p) => p.lat), lons = pts.map((p) => p.lon);
    const midLat = (Math.min(...lats) + Math.max(...lats)) / 2;
    const k = Math.cos((midLat * Math.PI) / 180);
    let x0 = Math.min(...lons), x1 = Math.max(...lons);
    let y0 = Math.min(...lats), y1 = Math.max(...lats);
    const padLon = Math.max((x1 - x0) * 0.18, 0.02), padLat = Math.max((y1 - y0) * 0.18, 0.02);
    x0 -= padLon; x1 += padLon; y0 -= padLat; y1 += padLat;
    const spanX = (x1 - x0) * k, spanY = y1 - y0;
    const H = 220;
    const W = Math.round(Math.min(Math.max((spanX / spanY) * H, 300), 900));
    const sc = Math.min((W - 34) / spanX, (H - 40) / spanY);
    const ox = (W - spanX * sc) / 2, oy = (H - spanY * sc) / 2;
    const px = (lon) => +(ox + (lon - x0) * k * sc).toFixed(1);
    const py = (lat) => +(oy + (y1 - lat) * sc).toFixed(1);
    const line = pts.map((p) => `${px(p.lon)},${py(p.lat)}`).join(" ");
    return `<div class="route-map">
      <svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(il.n)} rota güzergâhı">
        <rect x="0" y="0" width="${W}" height="${H}" fill="#eef5fb"/>
        <g stroke="#d6e6f3" stroke-width="1" stroke-dasharray="3 6">
          ${Array.from({ length: 7 }, (_, i) => `<line x1="${(W / 7) * (i + 1)}" y1="0" x2="${(W / 7) * (i + 1)}" y2="${H}"/>`).join("")}
          ${Array.from({ length: 4 }, (_, i) => `<line x1="0" y1="${(H / 4) * (i + 1)}" x2="${W}" y2="${(H / 4) * (i + 1)}"/>`).join("")}
        </g>
        <polyline points="${line}" fill="none" stroke="${r.theme.color}" stroke-width="2.4"
          stroke-dasharray="7 5" stroke-linecap="round" stroke-opacity=".75"/>
        ${pts.map((p, i) => `<g>
          <title>${esc(i + 1 + ". " + p.n)}</title>
          <circle cx="${px(p.lon)}" cy="${py(p.lat)}" r="12" fill="rgba(10,44,82,.10)"/>
          <circle cx="${px(p.lon)}" cy="${py(p.lat)}" r="11" fill="#fff" stroke="${r.theme.color}" stroke-width="2.6"/>
          <text x="${px(p.lon)}" y="${py(p.lat) + 4}" text-anchor="middle"
            font-size="11" font-weight="800" fill="${r.theme.color}">${i + 1}</text>
        </g>`).join("")}
      </svg>
      <span class="route-map-cap">${icon("i-pin")}${esc(il.n)} • ${nf(r.km)} km güzergâh</span>
    </div>`;
  }

  function mountWxLine(ilIdx) {
    if (!wxAllowed()) {
      const box0 = $("#wxLine");
      if (box0) box0.innerHTML = wxAskHtml();
      return;
    }
    const box = $("#wxLine");
    if (!box) return;
    const paint = (d) => {
      if (!box.isConnected) return;
      const i = 0;
      const tmax = Math.round(d.daily.temperature_2m_max[i]);
      const tmin = Math.round(d.daily.temperature_2m_min[i]);
      const rain = d.daily.precipitation_probability_max[i];
      const s = travelScore(tmax, tmin, rain, d.daily.wind_speed_10m_max[i], d.daily.weather_code[i]);
      const lb = scoreLabel(s.sc);
      const m = wxMeta(d.daily.weather_code[i]);
      box.innerHTML = `${wxIcon(m.k)} <b>${esc(m.l)}</b> · ${tmax}° / ${tmin}° · yağış ${rain != null ? "%" + Math.round(rain) : "—"}
        <span class="wx-pill" style="--sc:${lb.c}">Seyahat puanı ${s.sc}/100 · ${esc(lb.t)}</span>`;
    };
    const c = wxCached(ilIdx);
    if (c) { paint(c); return; }
    box.innerHTML = `<span class="wx-loading">Hava durumu yükleniyor…</span>`;
    wxLoad(ilIdx).then(paint).catch(() => { if (box.isConnected) box.innerHTML = `<span class="wx-off">Hava durumu alınamadı</span>`; });
  }


  /* ---------------------------------------------------- rota başlatma (canlı mod) */
  let liveRoute = null;   // { rid, i }

  function liveHtml() {
    const r = allRoutes().find((x) => x.id === liveRoute.rid);
    if (!r) return "";
    const il = ILS[r.ilIdx];
    const stops = r.stops;
    const i = Math.max(0, Math.min(liveRoute.i, stops.length - 1));
    const cur = stops[i];
    const prev = i > 0 ? stops[i - 1] : null;
    const next = stops[i + 1] || null;
    const from = prev ? [prev[4], prev[5]] : [il.lat, il.lon];
    const legKm = Math.round(haversine(from, [cur[4], cur[5]]));
    const nextKm = next ? Math.round(haversine([cur[4], cur[5]], [next[4], next[5]])) : 0;
    const pct = Math.round((i / Math.max(1, stops.length - 1)) * 100);
    const done = i === stops.length - 1;
    return `
      <div class="modal-hero" style="background:linear-gradient(135deg,${r.theme.color},#0a2c52)">
        <span class="mh-ic">${icon("i-nav", "i24")}</span>
        <span class="mh-cat">${esc(il.n)} • rota başlatıldı</span>
      </div>
      <div class="modal-body">
        <h3 id="modalTitle">${esc(il.n)} — ${esc(r.theme.label)}</h3>
        <p class="sub">${nf(r.km)} km • ${r.days} gün • ${stops.length} durak</p>
        <div class="live-bar"><span style="width:${pct}%"></span></div>
        <p class="live-step">Durak <b>${i + 1}</b> / ${stops.length}${done ? " • rota tamamlandı" : ""}</p>
        <div class="live-card">
          <span class="live-no">${i + 1}</span>
          <div>
            <h4>${esc(cur[0])}</h4>
            <p class="live-meta">${esc(CATS[cur[1]].label)} • ${esc(cur[3] || il.n)}</p>
            <p class="live-leg">${prev ? `Önceki duraktan <b>${nf(legKm)} km</b>` : `İl merkezinden <b>${nf(legKm)} km</b>`}${next ? ` • sonraki durak <b>${nf(nextKm)} km</b>` : ""}</p>
          </div>
        </div>
        <div class="live-actions">
          <a class="btn btn-red" href="${prev ? dirUrl(prev, cur) : maps(cur[4], cur[5])}" target="_blank" rel="noopener noreferrer">${icon("i-nav")}${prev ? "Yol tarifi al" : "Konuma git"}</a>
          <a class="btn btn-ghost" href="${mapsPlace(cur)}" target="_blank" rel="noopener noreferrer">${icon("i-pin")}Haritada göster</a>
        </div>
        <div class="live-actions">
          <button class="btn btn-ghost" data-live-prev ${i === 0 ? "disabled" : ""}>${icon("i-back")}Önceki</button>
          ${done
            ? `<button class="btn btn-red" data-live-end>${icon("i-check")}Rotayı bitir</button>`
            : `<button class="btn btn-red" data-live-next>Sonraki durak ${icon("i-arrow-right")}</button>`}
        </div>
        <p class="live-next">${next ? `Sıradaki: <b>${esc(next[0])}</b> — ${esc(next[3] || il.n)}` : "Son duraktasınız."}</p>
        <ol class="live-list">
          ${stops.map((sp, k) => `<li class="${k < i ? "done" : k === i ? "now" : ""}">
            <span class="stop-no">${k < i ? "✓" : k + 1}</span>
            <span class="live-li-name">${esc(sp[0])}</span>
            <span class="live-li-meta">${esc(sp[3] || il.n)}</span>
          </li>`).join("")}
        </ol>
        <div class="modal-actions">
          <a class="btn btn-ghost" href="${routeDirUrl(r)}" target="_blank" rel="noopener noreferrer">${icon("i-external")}Google'da tüm rota</a>
          <button class="btn btn-ghost" data-live-close>${icon("i-close")}Paneli kapat</button>
        </div>
      </div>`;
  }

  function startRoute(rid, i) {
    liveRoute = { rid, i: i || 0 };
    openModal(liveHtml(), "modal-live");
    if (typeof progPush === "function") progPush(rid, liveRoute.i);
  }
  function liveGo(delta) {
    if (!liveRoute) return;
    const r = allRoutes().find((x) => x.id === liveRoute.rid);
    liveRoute.i = Math.max(0, Math.min(liveRoute.i + delta, r.stops.length - 1));
    if (typeof progPush === "function") progPush(liveRoute.rid, liveRoute.i);
    modalContent.innerHTML = liveHtml();
    window.scrollTo({ top: 0 });
  }

  function openRoute(routeId) {
    const r = allRoutes().find((x) => x.id === routeId);
    if (!r) return;
    const il = ILS[r.ilIdx];
    openModal(`
      <div class="modal-hero" style="background:linear-gradient(135deg,${r.theme.color},#0a2c52)">
        <span class="mh-ic">${icon("i-route", "i24")}</span>
        <span class="mh-cat">${esc(il.n)} • ${r.stops.length} durak</span>
      </div>
      <div class="modal-body">
        <h3 id="modalTitle">${esc(il.n)} — ${esc(r.theme.label)}</h3>
        <p class="sub">${esc(il.r)} Bölgesi • ${nf(r.km)} km • ${r.days} gün • ${r.level}</p>
        <div class="wx-line" id="wxLine" data-il="${r.ilIdx}"></div>
        ${routeMapSvg(r, il)}
        <ol class="stop-list">
          ${r.stops.map((s, i) => `<li>
            <span class="stop-no">${i + 1}</span>
            <span class="stop-main">
              <button class="stop-name" data-place="${s.idx}">${esc(s[0])}</button>
              <span class="stop-meta">${esc(CATS[s[1]].label)} • ${esc(s[3] || il.n)}</span>
            </span>
            <a class="goto small" href="${maps(s[4], s[5])}" target="_blank" rel="noopener noreferrer">${icon("i-nav")}Konuma git</a>
          </li>`).join("")}
        </ol>
        <div class="modal-actions">
          <button class="btn btn-red" data-live-start="${r.id}">${icon("i-nav")}Rotayı başlat</button>
          <a class="btn btn-ghost" href="${routeDirUrl(r)}" target="_blank" rel="noopener noreferrer">${icon("i-external")}Google'da başlat</a>
        </div>
        <div class="modal-actions">
          <a class="btn btn-ghost" href="#/il/${IL_SLUG[r.ilIdx]}" data-close-nav>${icon("i-pin")}İl sayfası</a>
          <button class="btn btn-ghost" data-share-route="${r.id}">${icon("i-link")}Rotayı paylaş</button>
          <button class="btn btn-ghost" data-ics-route="${r.id}">${icon("i-clock")}Takvime ekle</button>
        </div>
      </div>`);
    mountWxLine(r.ilIdx);
  }

  function openMapModal() {
    openModal(`
      <div class="modal-body" style="padding-top:26px">
        <h3 id="modalTitle">Türkiye Haritası — 81 İl</h3>
        <p class="sub">İl işaretine dokunarak o ilin keşif sayfasına gidin</p>
        <div class="modal-map">
          <svg class="map-svg" viewBox="0 0 1000 438" role="img" aria-label="81 il haritası">
            <defs>
              <linearGradient id="trGrad2" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#3f9fd6"/><stop offset="100%" stop-color="#1c6fae"/>
              </linearGradient>
            </defs>
            <g>${provPaths()}</g>
          </svg>
        </div>
        <div class="region-grid">
          ${["Marmara", "Ege", "Akdeniz", "İç Anadolu", "Karadeniz", "Doğu Anadolu", "Güneydoğu Anadolu"].map((reg) => {
            const list = ILS.map((il, i) => ({ il, i })).filter((x) => x.il.r === reg);
            return `<div class="region-box">
              <h4>${reg} <span>${list.length} il</span></h4>
              <div class="region-ils">${list.map((x) => `<a href="#/il/${IL_SLUG[x.i]}" data-close-nav>${esc(x.il.n)}</a>`).join("")}</div>
            </div>`;
          }).join("")}
        </div>
      </div>`, "map-modal");
    requestAnimationFrame(() => mountMapLabels(document.querySelector(".modal-map"), document.querySelector(".modal-map .map-svg")));
  }

  function openFavs() {
    const items = favs.map((id) => {
      const [ilIdx, name] = id.split("|");
      const p = PLACES.find((x) => x[2] === Number(ilIdx) && x[0] === name);
      return p ? p : null;
    }).filter(Boolean);
    openModal(`
      <div class="modal-hero" style="height:132px;background:linear-gradient(135deg,#0a2c52,#2a6fa8)">
        <span class="mh-ic">${icon("i-heart", "i24")}</span>
        <span class="mh-cat">Kişisel keşif alanınız</span>
      </div>
      <div class="modal-body">
        <h3 id="modalTitle">Kişisel Keşif Alanınız</h3>
        <p class="sub">${items.length} favori • ${nf(PLACE_COUNT)} keşif kaydı • ${nf(ROUTE_COUNT)} rota</p>
        ${items.length ? `<div class="fav-list">${items.map((p) => `
          <button class="suggest-item" data-place="${p.idx}">
            <span class="suggest-ic">${catIcon(p[1])}</span>
            <span><span class="suggest-t">${esc(p[0])}</span><span class="suggest-m">${esc(CATS[p[1]].label)} • ${esc(ILS[p[2]].n)}</span></span>
          </button>`).join("")}</div>`
        : `<div class="suggest-empty">Henüz favori eklemediniz. Kartlardaki kalp ikonuna dokunarak keşiflerinizi kaydedebilirsiniz.</div>`}
      </div>`, "fav-modal");
  }

  /* ---------------------------------------------------------------- ANA SAYFA */
  const CITY_PHOTOS = {
    Antalya: "assets/img/antalya-720.webp", "İstanbul": "assets/img/istanbul-720.webp", "İzmir": "assets/img/izmir-720.webp",
    "Muğla": "assets/img/mugla-720.webp", "Nevşehir": "assets/img/nevsehir-720.webp"
  };
  const POPULAR = ["Antalya", "İstanbul", "İzmir", "Muğla", "Nevşehir"];

  function renderHome() {
    // kategori şeridi
    $("#catCard").innerHTML = CATS.map((c, i) => {
      const total = PLACES.filter((p) => p[1] === i).length;
      return `<a class="cat-item" data-color="${c.color}" href="#/kategori/${c.id}" title="${esc(c.label)}">
        ${catIcon(i, 26)}<span>${esc(c.label)}</span><em>${nf(total)}</em></a>`;
    }).join("");

    // popüler şehirler
    $("#cityGrid").innerHTML = POPULAR.map((name) => {
      const i = ilByName[name];
      const il = ILS[i];
      const villages = il.d.reduce((a, d) => a + d.k.length, 0);
      return `<a class="city-card" href="#/il/${IL_SLUG[i]}">
        <img src="${CITY_PHOTOS[name]}" alt="${esc(name)}" width="720" height="480" loading="lazy" decoding="async" fetchpriority="low">
        <div class="city-body">
          <div class="city-name">${esc(name)}</div>
          <div class="city-meta">${icon("i-pin")}${nf(byIlUniq[i].length)} keşif • ${nf(il.d.length)} ilçe</div>
        </div>
        <span class="city-plate">${String(il.p).padStart(2, "0")}</span>
      </a>`;
    }).join("");

    // rotalar (Antalya + İstanbul + Nevşehir örnekleri)
    const picks = [[ilByName.Antalya, 0], [ilByName["İstanbul"], 1], [ilByName["Nevşehir"], 3]];
    $("#routeList").innerHTML = picks.map(([i, t]) => routeCard(routesFor(i)[t], { home: true })).join("");

    // mevsimler
    const seasons = SEASONS;
    $("#seasonGrid").innerHTML = seasons.map((s) => `
      <button class="season-card ${s.img ? "" : "winter"}" data-season="${esc(s.id)}" aria-label="${esc(s.n)} mevsiminde keşfet">
        ${s.img ? `<img src="${s.img}" alt="${esc(s.n)} mevsiminde Türkiye" width="420" height="320" loading="lazy" decoding="async" fetchpriority="low">` : `<svg class="winter-scene" viewBox="0 0 200 120" preserveAspectRatio="none" aria-hidden="true">
            <path d="M-6 96 34 46 62 74 96 38 132 76 158 54 206 92V124H-6Z" fill="#eaf3fb"/>
            <path d="M34 46 46 60 34 70 22 60Z" fill="#ffffff"/>
            <path d="M96 38 110 54 96 64 82 54Z" fill="#ffffff"/>
            <path d="M-6 108 44 92 88 104 132 90 174 104 206 94V124H-6Z" fill="#ffffff"/>
          </svg><span class="snow">${Array.from({ length: 16 }, (_, i) => `<i style="left:${(i * 6.4 + 4).toFixed(1)}%;animation-duration:${3 + (i % 5)}s;animation-delay:${(i * 0.4).toFixed(1)}s;width:${i % 3 === 0 ? 5 : 3}px;height:${i % 3 === 0 ? 5 : 3}px"></i>`).join("")}</span>`}
        <span><span class="sc-name">${esc(s.n)}</span><span class="sc-link">${esc(s.months)} ${icon("i-arrow-right", "i10")}</span></span>
      </button>`).join("");

    // istatistik bandı
    const villages = ILS.reduce((a, il) => a + villCount(il), 0);
    const koy = ILS.reduce((a, il) => a + il.d.reduce((x, d) => x + d.k.length, 0), 0);
    const mah = villages - koy;
    const dists = ILS.reduce((a, il) => a + il.d.length, 0);
    $("#statsBand").innerHTML = `
      <div class="stat-cell"><b>${nf(N_IL)}</b><span>il</span></div>
      <div class="stat-cell"><b>${nf(dists)}</b><span>ilçe / belde</span></div>
      <div class="stat-cell"><b>${nf(villages)}</b><span>köy ${nf(koy)} • mahalle ${nf(mah)}</span></div>
      <div class="stat-cell"><b>${nf(PLACE_COUNT)}</b><span>keşif kaydı</span></div>
      <div class="stat-cell"><b>${nf(ROUTE_COUNT)}</b><span>hazır rota</span></div>
      <div class="stat-cell"><b>15</b><span>turizm kategorisi</span></div>`;

    // hızlı çipler
    const chips = [["Yakınımdaki Yerler", "nearby"], ["Antalya", "#/il/antalya"], ["İstanbul", "#/il/istanbul"],
      ["Kapadokya", "#/kesfet?q=Kapadokya"], ["İzmir", "#/il/izmir"], ["Muğla", "#/il/mugla"]];
    $("#quickChips").innerHTML = chips.map(([label, target], i) =>
      target === "nearby"
        ? `<button class="chip primary" data-nearby><svg width="13" height="13"><use href="#i-pin"/></svg>${label}</button>`
        : `<a class="chip" href="${target}">${esc(label)}</a>`).join("");

    // harita iğneleri (81 il)
    const pl = $("#provLayer");
    if (pl) pl.innerHTML = provPaths();
    mountMapLabels(document.querySelector(".map-stage"), document.querySelector(".map-stage .map-svg"));

    // menü + footer kategori listeleri
    $("#ddCats").innerHTML = `<div class="dd-title">15 kategori</div>` +
      CATS.map((c, i) => `<a href="#/kategori/${c.id}"><svg width="16" height="16"><use href="#${c.icon}"/></svg>${esc(c.label)}
        <span class="dd-count">${nf(PLACES.filter((p) => p[1] === i).length)}</span></a>`).join("") +
      `<a href="#/kesfet" class="dd-all">Tüm keşifleri gör ${icon("i-arrow-right")}</a>`;
    $("#footerCats").innerHTML = CATS.slice(0, 6).map((c) => `<a href="#/kategori/${c.id}">${esc(c.label)}</a>`).join("");

    observeReveal();
  }

  /* ---------------------------------------------------------------- KEŞFET */
  function renderKesfet(params) {
    const q = params.get("q") || "";
    const kat = params.get("kat") || "";
    const ilP = params.get("il");
    const ilce = params.get("ilce") || "";
    const ilIdx = ilP !== null && ilP !== "" ? Number(ilP) : null;

    const view = $("#view-page");
    view.innerHTML = `
      <div class="page-head">
        <div class="container">
          <nav class="crumb"><a href="#/">Ana Sayfa</a><span>/</span><b>Keşfet</b></nav>
          <h1>${q ? `“${esc(q)}” için sonuçlar` : kat ? esc(CATS[catById[kat]].label) : "Tüm Keşif Noktaları"}</h1>
          <p class="page-sub">${nf(PLACE_COUNT)} keşif kaydı • 15 kategori • 81 il</p>
        </div>
      </div>
      <div class="container">
        <div class="filter-bar">
          <div class="f-search">${icon("i-search")}
            <input id="fq" type="search" placeholder="Yer, il, ilçe veya köy ara…" value="${esc(q)}">
          </div>
          <select id="fkat" aria-label="Kategori">
            <option value="">Tüm kategoriler</option>
            ${CATS.map((c) => `<option value="${c.id}"${c.id === kat ? " selected" : ""}>${esc(c.label)}</option>`).join("")}
          </select>
          <select id="fil" aria-label="İl">
            <option value="">Tüm iller</option>
            ${ILS.map((il, i) => `<option value="${i}"${i === ilIdx ? " selected" : ""}>${String(il.p).padStart(2, "0")} ${esc(il.n)}</option>`).join("")}
          </select>
          <select id="filce" aria-label="İlçe" ${ilIdx === null ? "disabled" : ""}>
            <option value="">Tüm ilçeler</option>
            ${(ilIdx !== null ? ILS[ilIdx].d : []).map((d) => `<option value="${esc(d.n)}"${d.n === ilce ? " selected" : ""}>${esc(d.n)}</option>`).join("")}
          </select>
          <button class="btn btn-ghost" id="fclear">Temizle</button>
        </div>
        <div class="cat-chips" id="catChips"></div>
        <div id="kesfetInfo" class="result-info"></div>
        <div class="p-grid" id="pGrid"></div>
        <div class="load-more-wrap"><button class="btn btn-navy" id="loadMore" hidden>Daha fazla göster</button></div>
      </div>`;

    const state = { q, kat, il: ilIdx, ilce, page: 0 };
    const PER = 48;

    function filtered() {
      let list = PLACES;
      if (state.il !== null) list = list.filter((p) => p[2] === state.il);
      if (state.kat) list = list.filter((p) => CATS[p[1]].id === state.kat);
      if (state.ilce) list = list.filter((p) => p[3] === state.ilce);
      if (state.q) {
        const k = norm(state.q);
        list = list.filter((p) => norm(p[0] + " " + (p[6] || "") + " " + typeLabel(p[6]) + " " + p[3] + " " + ILS[p[2]].n).includes(k));
      }
      return byCoordFirst(list);
    }

    function paint() {
      const list = filtered();
      const shown = list.slice(0, (state.page + 1) * PER);
      $("#pGrid").innerHTML = shown.map(placeCard).join("") ||
        `<div class="empty">Bu filtrelerde sonuç bulunamadı. Filtreleri temizlemeyi deneyin.</div>`;
      $("#kesfetInfo").textContent = `${nf(list.length)} sonuçtan ${nf(shown.length)} tanesi gösteriliyor`;
      $("#loadMore").hidden = shown.length >= list.length;
      $("#catChips").innerHTML = CATS.map((c, i) => {
        const active = state.kat === c.id;
        const n = (state.il !== null ? byIlCat[state.il][i] : PLACES.filter((p) => p[1] === i)).length;
        return `<a class="cat-chip${active ? " active" : ""}" href="#" data-chip-cat="${c.id}">${catIcon(i, 14)}${esc(c.label)} <em>${nf(n)}</em></a>`;
      }).join("");
      observeReveal();
    }

    function push() {
      const p = new URLSearchParams();
      if (state.q) p.set("q", state.q);
      if (state.kat) p.set("kat", state.kat);
      if (state.il !== null) p.set("il", state.il);
      if (state.ilce) p.set("ilce", state.ilce);
      const qs = p.toString();
      history.replaceState(null, "", `#/kesfet${qs ? "?" + qs : ""}`);
    }

    $("#fq").addEventListener("input", (e) => {
      state.q = e.target.value.trim(); state.page = 0; push(); paint();
      const box = $("#suggest");
      if (state.q.length > 1) {
        box.innerHTML = "";
        renderSuggest(state.q);
      } else box.classList.remove("show");
    });
    $("#fkat").addEventListener("change", (e) => { state.kat = e.target.value; state.page = 0; push(); paint(); });
    $("#fil").addEventListener("change", (e) => {
      state.il = e.target.value === "" ? null : Number(e.target.value);
      state.ilce = ""; state.page = 0; push();
      renderKesfet(new URLSearchParams(`q=${encodeURIComponent(state.q)}&kat=${state.kat}${state.il !== null ? "&il=" + state.il : ""}`));
    });
    $("#filce").addEventListener("change", (e) => { state.ilce = e.target.value; state.page = 0; push(); paint(); });
    $("#fclear").addEventListener("click", () => { location.hash = "#/kesfet"; });
    $("#loadMore").addEventListener("click", () => { state.page++; paint(); });
    $("#catChips").addEventListener("click", (e) => {
      const a = e.target.closest("[data-chip-cat]");
      if (!a) return;
      e.preventDefault();
      state.kat = state.kat === a.dataset.chipCat ? "" : a.dataset.chipCat;
      state.page = 0; push(); paint();
      $("#fkat").value = state.kat;
    });

    paint();
  }

  /* ---------------------------------------------------------------- İLLER */
  function renderIller() {
    const view = $("#view-page");
    const villages = ILS.reduce((a, il) => a + villCount(il), 0);
    view.innerHTML = `
      <div class="page-head">
        <div class="container">
          <nav class="crumb"><a href="#/">Ana Sayfa</a><span>/</span><b>81 İl</b></nav>
          <h1>Türkiye'nin 81 İli</h1>
          <p class="page-sub">${nf(ILS.reduce((a, il) => a + il.d.length, 0))} ilçe • ${nf(villages)} köy/mahalle • ${nf(PLACE_COUNT)} keşif kaydı (${nf(PLACE_VERIFIED)} konumlu)</p>
        </div>
      </div>
      <div class="container">
        <div class="filter-bar">
          <div class="f-search">${icon("i-search")}<input id="ilSearch" type="search" placeholder="İl ara…"></div>
          <select id="regionSel" aria-label="Bölge">
            <option value="">Tüm bölgeler</option>
            ${["Marmara", "Ege", "Akdeniz", "İç Anadolu", "Karadeniz", "Doğu Anadolu", "Güneydoğu Anadolu"].map((r) => `<option>${r}</option>`).join("")}
          </select>
        </div>
        <div class="il-grid" id="ilGrid"></div>
      </div>`;

    function paint() {
      const q = ($("#ilSearch").value || "").trim();
      const reg = $("#regionSel").value;
      const list = ILS.map((il, i) => ({ il, i }))
        .filter((x) => (!q || norm(x.il.n).includes(norm(q))) && (!reg || x.il.r === reg))
        .sort((a, b) => a.il.p - b.il.p);
      $("#ilGrid").innerHTML = list.map((x) => ilCard(x.i)).join("") || `<div class="empty">İl bulunamadı.</div>`;
    }
    $("#ilSearch").addEventListener("input", paint);
    $("#regionSel").addEventListener("change", paint);
    paint();
  }

  /* ---------------------------------------------------------------- İL SAYFASI */
  function renderIl(ilIdx, tab) {
    const il = ILS[ilIdx];
    const routes = routesFor(ilIdx);
    const cats = CATS.map((c, i) => ({ c, i, n: byIlCat[ilIdx][i].length })).filter((x) => x.n > 0);
    const activeTab = tab && catById[tab] !== undefined ? catById[tab] : -1;
    const list = activeTab >= 0 ? byIlCat[ilIdx][activeTab] : byIl[ilIdx];
    const villages = villCount(il);
    const koyN = il.d.reduce((a, d) => a + d.k.length, 0);
    const mahN = villages - koyN;
    const view = $("#view-page");

    view.innerHTML = `
      <div class="il-hero" style="background-image:${CITY_PHOTOS[il.n] ? `url('${CITY_PHOTOS[il.n]}')` : "linear-gradient(120deg,#0a2c52,#1c6fae)"}">
        <div class="container">
          <nav class="crumb light"><a href="#/">Ana Sayfa</a><span>/</span><a href="#/iller">81 İl</a><span>/</span><b>${esc(il.n)}</b></nav>
          <div class="il-hero-inner">
            <span class="il-plate big">${String(il.p).padStart(2, "0")}</span>
            <div>
              <h1>${esc(il.n)}</h1>
              <p>${esc(il.r)} Bölgesi • ${nf(byIlUniq[ilIdx].length)} keşif noktası • ${nf(il.d.length)} ilçe • ${nf(koyN)} köy • ${nf(mahN)} mahalle</p>
            </div>
            <button class="btn btn-red" data-open-map>${icon("i-map")}Haritada gör</button>
          </div>
        </div>
      </div>

      <div class="container">
        ${wxPanelHtml(ilIdx)}
        <h2 class="block-title"><svg><use href="#i-route"/></svg>${esc(il.n)} için 5 gezi rotası</h2>
        <div class="route-grid">${routes.map((r) => routeCard(r)).join("")}</div>

        <h2 class="block-title"><svg><use href="#i-compass"/></svg>Kategorilere göre keşfet</h2>
        <div class="cat-chips">
          <a class="cat-chip${activeTab < 0 ? " active" : ""}" href="#/il/${IL_SLUG[ilIdx]}">Tümü <em>${nf(byIlUniq[ilIdx].length)}</em></a>
          ${cats.map((x) => `<a class="cat-chip${activeTab === x.i ? " active" : ""}" href="#/il/${IL_SLUG[ilIdx]}?kat=${x.c.id}">
            ${catIcon(x.i, 14)}${esc(x.c.label)} <em>${nf(x.n)}</em></a>`).join("")}
        </div>
        <div class="p-grid">${byCoordFirst(activeTab < 0 ? dedupeByName(list) : list).map(placeCard).join("") || `<div class="empty">Bu kategoride kayıt yok.</div>`}</div>

        <h2 class="block-title"><svg><use href="#i-building"/></svg>İlçeler ve köyler</h2>
        <p class="block-sub">${nf(il.d.length)} ilçe/belde, ${nf(koyN)} köy ve ${nf(mahN)} mahalle. İlçeye tıklayarak yerleşim birimlerini görün.</p>
        <div class="district-list">
          ${il.d.map((d, di) => `
            <details class="district">
              <summary>
                <a class="dist-name" href="#/ilce/${IL_SLUG[ilIdx]}/${slug(d.n)}">${esc(d.n)}</a>
                <span class="dist-meta">${nf(d.k.length)} köy${(d.m && d.m.length) ? ` • ${nf(d.m.length)} mahalle` : ""}</span>
                <span class="dist-places">${[...new Set(byIl[ilIdx].filter((p) => norm(p[3]) === norm(d.n)).map((p) => p[0]))].slice(0, 3).map(esc).join(" · ")}</span>
                <span class="dist-actions">
                  <a class="mini-link" href="#/kesfet?il=${ilIdx}&ilce=${encodeURIComponent(d.n)}">Yerleri gör</a>
                </span>
              </summary>
              <div class="village-chips">
                ${d.k.length ? `<span class="chip-label">Köyler (${d.k.length})</span>${d.k.map((k) => `<span class="village-chip">${icon("i-village", "i12")}${esc(k)}</span>`).join("")}` : ""}
                ${(d.m && d.m.length) ? `<span class="chip-label">Mahalleler (${d.m.length})</span>${d.m.map((k) => `<span class="village-chip mahalle">${esc(k)}</span>`).join("")}` : ""}
                ${(!d.k.length && !(d.m && d.m.length)) ? `<span class="muted">Kayıtlı yerleşim bilgisi yok.</span>` : ""}
              </div>
            </details>`).join("")}
        </div>
      </div>`;
    mountWx(ilIdx);
  }

  /* ---------------------------------------------------------------- ROTALAR */
  function renderRotalar(params) {
    const ilP = params.get("il");
    const ilIdx = ilP !== null && ilP !== "" ? Number(ilP) : null;
    const view = $("#view-page");
    view.innerHTML = `
      <div class="page-head">
        <div class="container">
          <nav class="crumb"><a href="#/">Ana Sayfa</a><span>/</span><b>Rotalar</b></nav>
          <h1>${ilIdx !== null ? esc(ILS[ilIdx].n) + " Rotaları" : "Türkiye Rota Rehberi"}</h1>
          <p class="page-sub">${nf(ROUTE_COUNT)} rota • her il için 5 tema • durak durak konum bağlantılı</p>
        </div>
      </div>
      <div class="container">
        <div class="filter-bar">
          <select id="ril" aria-label="İl">
            <option value="">Tüm iller (${nf(ROUTE_COUNT)} rota)</option>
            ${ILS.map((il, i) => `<option value="${i}"${i === ilIdx ? " selected" : ""}>${String(il.p).padStart(2, "0")} ${esc(il.n)}</option>`).join("")}
          </select>
          <select id="rtheme" aria-label="Tema">
            <option value="">Tüm temalar</option>
            ${THEMES.map((t) => `<option value="${t.key}">${esc(t.label)}</option>`).join("")}
          </select>
        </div>
        <div class="result-info" id="rInfo"></div>
        <div class="route-grid" id="routeGrid"></div>
        <div class="load-more-wrap">
          <button class="btn btn-navy" id="rMore" hidden>Daha fazla rota</button>
          <button class="btn btn-ghost" id="rAll" hidden>Tümünü göster</button>
        </div>
      </div>`;
    let page = 0;
    const PER = 12;
    function paint() {
      const selIl = $("#ril").value;
      const selTheme = $("#rtheme").value;
      let list = allRoutes();
      if (selIl !== "") list = list.filter((r) => r.ilIdx === Number(selIl));
      if (selTheme) list = list.filter((r) => r.theme.key === selTheme);
      const shown = list.slice(0, (page + 1) * PER);
      $("#routeGrid").innerHTML = shown.map((r) => routeCard(r)).join("") || `<div class="empty">Rota bulunamadı.</div>`;
      $("#rMore").hidden = shown.length >= list.length;
      $("#rAll").hidden = list.length - shown.length <= PER;
      $("#rInfo").textContent = `${nf(list.length)} rotadan ${nf(shown.length)} tanesi gösteriliyor`;
    }
    $("#ril").addEventListener("change", () => { page = 0; paint(); });
    $("#rtheme").addEventListener("change", () => { page = 0; paint(); });
    $("#rMore").addEventListener("click", () => { page++; paint(); });
    $("#rAll").addEventListener("click", () => { page = Math.ceil(ROUTE_COUNT / PER); paint(); });
    paint();
  }

  /* ---------------------------------------------------------------- KATEGORİ */
  /* ---------------------------------------------------------------- HAVA DURUMU (Open-Meteo) */
  const WX_KEY = "tk-weather-v2";
  const WX_TTL = 3 * 60 * 60 * 1000;   // 3 saat önbellek
  const wxMem = {};

  function wxCached(ilIdx) {
    if (wxMem[ilIdx]) return wxMem[ilIdx];
    try {
      const c = JSON.parse(localStorage.getItem(WX_KEY) || "{}")[ilIdx];
      if (c && Date.now() - c.t < WX_TTL) { wxMem[ilIdx] = c.d; return c.d; }
    } catch (e) { /* yoksay */ }
    return null;
  }
  function wxStore(ilIdx, d) {
    wxMem[ilIdx] = d;
    try {
      const c = JSON.parse(localStorage.getItem(WX_KEY) || "{}");
      c[ilIdx] = { t: Date.now(), d };
      localStorage.setItem(WX_KEY, JSON.stringify(c));
    } catch (e) { /* kota dolu olabilir */ }
  }
  function wxLoad(ilIdx) {
    const il = ILS[ilIdx];
    const hit = wxCached(ilIdx);
    if (hit) return Promise.resolve(hit);
    const url = "https://api.open-meteo.com/v1/forecast"
      + `?latitude=${il.lat.toFixed(3)}&longitude=${il.lon.toFixed(3)}`
      + "&current=temperature_2m,weather_code"
      + "&daily=weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,wind_speed_10m_max"
      + "&timezone=auto&forecast_days=5";
    const ctrl = new AbortController();
    const to = setTimeout(() => ctrl.abort(), 8000);
    return fetch(url, { signal: ctrl.signal })
      .then((r) => { if (!r.ok) throw new Error("HTTP " + r.status); return r.json(); })
      .then((j) => { wxStore(ilIdx, j); return j; })
      .finally(() => clearTimeout(to));
  }

  // WMO hava kodu → ikon + etiket
  function wxMeta(code) {
    const c = Number(code);
    if (c === 0) return { k: "sun", l: "Açık" };
    if (c === 1) return { k: "sun", l: "Az bulutlu" };
    if (c === 2) return { k: "partly", l: "Parçalı bulutlu" };
    if (c === 3) return { k: "cloud", l: "Kapalı" };
    if (c === 45 || c === 48) return { k: "fog", l: "Puslu" };
    if (c >= 51 && c <= 57) return { k: "rain", l: "Çisenti" };
    if (c >= 61 && c <= 67) return { k: "rain", l: "Yağmurlu" };
    if (c >= 71 && c <= 77) return { k: "snow", l: "Kar yağışlı" };
    if (c >= 80 && c <= 82) return { k: "rain", l: "Sağanak" };
    if (c === 85 || c === 86) return { k: "snow", l: "Kar sağanağı" };
    if (c >= 95) return { k: "storm", l: "Fırtına" };
    return { k: "cloud", l: "Bulutlu" };
  }

  const WX_ICONS = {
    sun: '<circle cx="12" cy="12" r="4.4"/><path d="M12 2.6v2.4M12 19v2.4M2.6 12H5M19 12h2.4M5.2 5.2l1.7 1.7M17.1 17.1l1.7 1.7M18.8 5.2l-1.7 1.7M6.9 17.1l-1.7 1.7"/>',
    partly: '<circle cx="9" cy="9.4" r="3.4"/><path d="M9 3.2v1.6M3.2 9.4h1.6M4.9 5.3l1.1 1.1M13.1 5.3l-1.1 1.1"/><path d="M8 19.5h8.6a3.4 3.4 0 0 0 .3-6.8 4.6 4.6 0 0 0-8.8 1.1A2.9 2.9 0 0 0 8 19.5z"/>',
    cloud: '<path d="M6.4 18.5h10.9a3.6 3.6 0 0 0 .4-7.2 4.9 4.9 0 0 0-9.4 1.2 3.1 3.1 0 0 0-1.9 6z"/>',
    rain: '<path d="M6.4 15.4h10.9a3.6 3.6 0 0 0 .4-7.2 4.9 4.9 0 0 0-9.4 1.2 3.1 3.1 0 0 0-1.9 6z"/><path d="M8.4 18.4l-.9 2.3M12 18.4l-.9 2.3M15.6 18.4l-.9 2.3"/>',
    snow: '<path d="M6.4 14.6h10.9a3.6 3.6 0 0 0 .4-7.2 4.9 4.9 0 0 0-9.4 1.2 3.1 3.1 0 0 0-1.9 6z"/><path d="M8.6 18.2v2.6M7.4 18.9l2.4 1.2M9.8 18.9l-2.4 1.2M15.4 18.2v2.6M14.2 18.9l2.4 1.2M16.6 18.9l-2.4 1.2"/>',
    storm: '<path d="M6.4 14.6h10.9a3.6 3.6 0 0 0 .4-7.2 4.9 4.9 0 0 0-9.4 1.2 3.1 3.1 0 0 0-1.9 6z"/><path d="M12.6 15.6l-2 3.4h2.6l-1.4 3"/>',
    fog: '<path d="M6.4 13.4h10.9a3.6 3.6 0 0 0 .4-7.2 4.9 4.9 0 0 0-9.4 1.2 3.1 3.1 0 0 0-1.9 6z"/><path d="M4.6 17.4h14.8M6.6 20.2h10.8"/>'
  };
  const wxIcon = (kind, size) =>
    `<svg class="wx-ic ${size || ""}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${WX_ICONS[kind] || WX_ICONS.cloud}</svg>`;

  // seyahat uygunluğu puanı (0–100)
  function travelScore(tmax, tmin, rain, wind, code) {
    let sc = 100;
    const why = [];
    const isSnow = (code >= 71 && code <= 77) || code === 85 || code === 86;
    const isStorm = code >= 95;
    const isWet = code >= 51 && !isSnow && !isStorm;

    if (isStorm) { sc -= 40; why.push("fırtına riski"); }
    else if (isSnow) { sc -= 24; why.push("kar yağışı"); }

    if (rain != null) {
      if (rain >= 70) { sc -= 26; why.push(`yağış %${Math.round(rain)}`); }
      else if (rain >= 40) { sc -= 12; why.push(`yağış %${Math.round(rain)}`); }
      else if (isWet) { sc -= 6; }
    } else if (isWet) { sc -= 12; why.push("yağış ihtimali"); }

    if (tmax >= 36) { sc -= 22; why.push("aşırı sıcak"); }
    else if (tmax >= 32) { sc -= 10; why.push("sıcak"); }
    if (tmin <= -2) { sc -= 16; why.push("don riski"); }
    else if (tmax <= 4) { sc -= 10; why.push("soğuk"); }
    if (wind != null && wind >= 55) { sc -= 12; why.push("kuvvetli rüzgâr"); }

    const mid = (tmax + tmin) / 2;
    if (mid >= 13 && mid <= 25) sc = Math.min(100, sc + 6);
    return { sc: Math.max(5, Math.min(100, Math.round(sc))), why };
  }

  const scoreLabel = (sc) =>
    sc >= 85 ? { t: "Harika", c: "#1f8a53" } :
    sc >= 70 ? { t: "Uygun", c: "#2f8f63" } :
    sc >= 55 ? { t: "Orta", c: "#b8781c" } :
    sc >= 40 ? { t: "Şartlı", c: "#c2673a" } : { t: "Ertelenebilir", c: "#b3312f" };

  const DAY_NAMES = ["Paz", "Pzt", "Sal", "Çar", "Per", "Cum", "Cmt"];

  function wxPanelHtml(ilIdx) {
    return `<section class="wx-panel" id="wxPanel" data-il="${ilIdx}">
      <div class="wx-head">
        <h2 class="block-title" style="margin:0"><svg><use href="#i-sun"/></svg>Hava durumu ve seyahat uygunluğu</h2>
        <span class="wx-src">Open-Meteo</span>
      </div>
      <div class="wx-body" id="wxBody"><span class="wx-loading">Hava durumu yükleniyor…</span></div>
    </section>`;
  }

  function paintWx(ilIdx, data) {
    const box = $("#wxBody");
    if (!box || !box.closest("[data-il]") || Number(box.closest("[data-il]").dataset.il) !== ilIdx) return;
    const d = data.daily, cur = data.current || {};
    const days = d.time.map((t, i) => ({
      t, code: d.weather_code[i], tmax: d.temperature_2m_max[i], tmin: d.temperature_2m_min[i],
      rain: d.precipitation_probability_max[i], wind: d.wind_speed_10m_max[i]
    }));
    const scores = days.map((x) => travelScore(x.tmax, x.tmin, x.rain, x.wind, x.code));
    const bestI = scores.reduce((bi, s, i) => (s.sc > scores[bi].sc ? i : bi), 0);
    const today = scores[0], best = scores[bestI];
    const lb = scoreLabel(today.sc);
    const bestX = days[bestI];
    const bestDayName = bestI === 0 ? "bugün" : bestI === 1 ? "yarın" : DAY_NAMES[new Date(bestX.t + "T12:00").getDay()];

    box.innerHTML = `
      <div class="wx-score" style="--sc:${lb.c}">
        <div class="wx-num">${today.sc}<span>/100</span></div>
        <div class="wx-lbl">${esc(lb.t)}</div>
        <div class="wx-bar"><i style="width:${today.sc}%"></i></div>
        <p class="wx-why">${today.why.length ? esc(today.why.join(" · ")) : "Hava koşulları gezi için elverişli"}</p>
        ${bestI > 0 ? `<p class="wx-best">En uygun gün: <b>${esc(bestDayName)}</b> (${best.sc}/100)</p>` : ""}
      </div>
      <div class="wx-days">
        ${days.map((x, i) => {
          const m = wxMeta(x.code);
          return `<div class="wx-day${i === 0 ? " today" : ""}">
            <span class="wd-name">${i === 0 ? "Bugün" : i === 1 ? "Yarın" : DAY_NAMES[new Date(x.t + "T12:00").getDay()]}</span>
            ${wxIcon(m.k)}
            <span class="wd-temp"><b>${Math.round(x.tmax)}°</b> / ${Math.round(x.tmin)}°</span>
            <span class="wd-rain">${x.rain != null ? `%${Math.round(x.rain)}` : "—"}</span>
            <span class="wd-score" style="--sc:${scoreLabel(scores[i].sc).c}">${scores[i].sc}</span>
          </div>`;
        }).join("")}
      </div>`;

    // başlıktaki hava rozetini de güncelle
    const w = $(".weather");
    if (w && cur.temperature_2m != null) {
      const m = wxMeta(cur.weather_code);
      w.innerHTML = `<svg class="hdr-wx"><use href="#i-sun"/></svg>
        <span><span class="temp">${Math.round(cur.temperature_2m)}°C</span><span class="city">${esc(ILS[ilIdx].n)}</span></span>`;
      w.title = `${ILS[ilIdx].n}: ${m.l}, ${Math.round(cur.temperature_2m)}°C`;
      w.dataset.kind = m.k;
      w.classList.remove("kind-sun", "kind-partly", "kind-cloud", "kind-rain", "kind-snow", "kind-storm", "kind-fog");
      w.classList.add("kind-" + m.k);
    }
  }

  // başlıktaki hava rozeti: ana sayfada Ankara
  function wxAskHtml() {
    return `<button class="wx-ask" data-wx-enable title="Hava durumu Open-Meteo'dan alınır">Hava durumunu göster</button>`;
  }
  function mountHeaderWx() {
    const w0 = $(".weather");
    if (!wxAllowed()) { if (w0) w0.innerHTML = wxAskHtml(); return; }
    const idx = ilByName["Ankara"];
    if (idx === undefined) return;
    const w = $(".weather");
    if (!w) return;
    const paint = (d) => {
      const cur = d.current || {};
      if (cur.temperature_2m == null) return;
      const m = wxMeta(cur.weather_code);
      w.title = `Ankara: ${m.l}, ${Math.round(cur.temperature_2m)}°C (Open-Meteo)`;
      w.innerHTML = `<svg><use href="#i-sun"/></svg>
        <span><span class="temp">${Math.round(cur.temperature_2m)}°C</span><span class="city">Ankara</span></span>`;
      w.dataset.kind = m.k;
      w.classList.add("kind-" + m.k);
    };
    const c = wxCached(idx);
    if (c) { paint(c); return; }
    wxLoad(idx).then(paint).catch(() => {});
  }

  function mountWx(ilIdx) {
    const panel = $("#wxPanel");
    if (!panel) return;
    if (!wxAllowed()) {
      const body0 = $("#wxBody");
      if (body0) body0.innerHTML = wxAskHtml() + ` <span class="wx-off">Hava durumu ve seyahat puanı için izin verin.</span>`;
      return;
    }
    const cached = wxCached(ilIdx);
    if (cached) { paintWx(ilIdx, cached); return; }
    const offline = location.protocol === "file:";
    wxLoad(ilIdx)
      .then((d) => paintWx(ilIdx, d))
      .catch(() => {
        if (!panel.isConnected) return;
        const body = $("#wxBody");
        if (body) body.innerHTML = `<span class="wx-off">Hava durumu alınamadı${offline ? " (çevrimdışı görüntüleniyor)" : ""} — bağlantı kurulunca puan otomatik gelir.</span>`;
      });
  }

  /* ---------------------------------------------------------------- MEVSİM SAYFASI */
  function renderMevsim(sid) {
    const se = seasonById[sid];
    const catIdx = se.cats.map((id) => catById[id]);
    const pool = [];
    ILS.forEach((il, i) => catIdx.forEach((ci) => byIlCat[i][ci].forEach((p) => pool.push(p))));
    const uniq = byCoordFirst(dedupeByName(pool));
    uniq.sort((x, y) => ((y[4] != null) - (x[4] != null)) || (y.links - x.links));

    // mevsime en uygun iller: sezon kategorilerindeki kayıt sayısı
    const ilScore = ILS.map((il, i) => ({
      i, il, n: catIdx.reduce((a, ci) => a + byIlCat[i][ci].length, 0)
    })).filter((x) => x.n > 0).sort((a, b) => b.n - a.n).slice(0, 8);

    // sezonun önerilen rotaları: en uygun illerin ilgili temalı rotası
    const seasonRoutes = ilScore.slice(0, 4).map((x) => {
      const rs = routesFor(x.i);
      return rs.find((r) => r.theme.key === se.theme) || rs[0];
    }).filter(Boolean);

    const view = $("#view-page");
    view.innerHTML = `
      <div class="season-hero" style="--sc:${se.color}">
        ${se.img ? `<img src="${se.img}" alt="${esc(se.n)} mevsiminde Türkiye" width="420" height="320" loading="lazy" decoding="async" fetchpriority="low">` : `<svg class="winter-scene" viewBox="0 0 200 120" preserveAspectRatio="none" aria-hidden="true">
          <path d="M-6 96 34 46 62 74 96 38 132 76 158 54 206 92V124H-6Z" fill="#dbe9f6"/>
          <path d="M34 46 46 60 34 70 22 60Z" fill="#fff"/><path d="M96 38 110 54 96 64 82 54Z" fill="#fff"/>
          <path d="M-6 108 44 92 88 104 132 90 174 104 206 94V124H-6Z" fill="#fff"/></svg>`}
        <div class="container season-hero-in">
          <nav class="crumb"><a href="#/">Ana Sayfa</a><span>/</span><span>Mevsim</span><span>/</span><b>${esc(se.n)}</b></nav>
          <h1>${esc(se.n)} <span>${esc(se.months)}</span></h1>
          <p class="page-sub">${esc(se.desc)}</p>
          <div class="season-facts">
            <span class="sf"><b>${nf(uniq.length)}</b> uygun keşif</span>
            <span class="sf"><b>${nf(ilScore.length ? ILS.filter((il, i) => catIdx.some((ci) => byIlCat[i][ci].length)).length : 0)}</b> il</span>
            <span class="sf"><b>${se.cats.length}</b> kategori</span>
          </div>
        </div>
      </div>
      <div class="container">
        <p class="wx-season-note">${icon("i-sun")} Bu sayfadaki keşifler ${esc(se.n.toLowerCase())} mevsimi için seçildi; bir ilin güncel hava durumu ve seyahat puanı il sayfasında görünür.</p>
        <h2 class="block-title"><svg><use href="#i-pin"/></svg>Bu mevsimin en uygun illeri</h2>
        <div class="district-chips">
          ${ilScore.map((x) => `<a class="district-chip" href="#/il/${IL_SLUG[x.i]}">
            ${esc(x.il.n)}<em>${nf(x.n)}</em></a>`).join("")}
        </div>

        <h2 class="block-title"><svg><use href="#i-route"/></svg>${esc(se.n)} için önerilen rotalar</h2>
        <div class="route-grid">${seasonRoutes.map((r) => routeCard(r)).join("")}</div>

        <h2 class="block-title"><svg><use href="#i-compass"/></svg>${esc(se.n)} keşifleri</h2>
        <div class="filter-bar">
          <select id="mil" aria-label="İl">
            <option value="">Tüm iller (${nf(uniq.length)})</option>
            ${ILS.map((il, i) => {
              const n = catIdx.reduce((a, ci) => a + byIlCat[i][ci].length, 0);
              return n ? `<option value="${i}">${String(il.p).padStart(2, "0")} ${esc(il.n)} (${n})</option>` : "";
            }).join("")}
          </select>
          <select id="mcat" aria-label="Kategori">
            <option value="">Tüm kategoriler</option>
            ${catIdx.map((ci) => `<option value="${ci}">${esc(CATS[ci].label)}</option>`).join("")}
          </select>
        </div>
        <div class="result-info" id="mInfo"></div>
        <div class="p-grid" id="mGrid"></div>
        <div class="load-more-wrap"><button class="btn btn-navy" id="mMore" hidden>Daha fazla göster</button></div>
      </div>`;

    let page = 0;
    const PER = 24;
    function paint() {
      const ilSel = $("#mil").value, catSel = $("#mcat").value;
      let list = uniq;
      if (ilSel !== "") list = list.filter((p) => p[2] === Number(ilSel));
      if (catSel !== "") list = list.filter((p) => p[1] === Number(catSel));
      const shown = list.slice(0, (page + 1) * PER);
      $("#mGrid").innerHTML = shown.map(placeCard).join("") || `<div class="empty">Bu filtrede keşif yok.</div>`;
      $("#mMore").hidden = shown.length >= list.length;
      $("#mInfo").textContent = `${nf(list.length)} keşiften ${nf(shown.length)} tanesi gösteriliyor`;
    }
    $("#mil").addEventListener("change", () => { page = 0; paint(); });
    $("#mcat").addEventListener("change", () => { page = 0; paint(); });
    $("#mMore").addEventListener("click", () => { page++; paint(); });
    paint();
  }

  /* ---------------------------------------------------------------- İLÇE SAYFASI */
  function renderIlce(i, di) {
    const il = ILS[i];
    const d = il.d[di];
    if (!d) { location.hash = `#/il/${IL_SLUG[i]}`; return; }
    const list = byCoordFirst(dedupeByName(byIl[i].filter((p) => norm(p[3]) === norm(d.n))));
    const koy = d.k || [], mah = d.m || [];
    const ilceSlug = slug(d.n);
    const others = il.d.map((x, xi) => ({ x, xi })).filter((o) => o.xi !== di).slice(0, 12);
    const view = $("#view-page");
    view.innerHTML = `
      <div class="page-head">
        <div class="container">
          <nav class="crumb">
            <a href="#/">Ana Sayfa</a><span>/</span>
            <a href="#/iller">81 İl</a><span>/</span>
            <a href="#/il/${IL_SLUG[i]}">${esc(il.n)}</a><span>/</span>
            <b>${esc(d.n)}</b>
          </nav>
          <h1>${esc(d.n)}</h1>
          <p class="page-sub">${esc(il.n)} • ${esc(il.r)} Bölgesi${koy.length ? ` • ${nf(koy.length)} köy` : ""}${mah.length ? ` • ${nf(mah.length)} mahalle` : ""} • ${nf(list.length)} keşif noktası</p>
        </div>
      </div>
      <div class="container">
        <div class="stats-band">
          ${[
            [String(il.p).padStart(2, "0"), "Plaka"],
            [nf(koy.length), "Köy"],
            [nf(mah.length), "Mahalle"],
            [nf(list.length), "Keşif noktası"],
            [nf(il.d.length), esc(il.n) + " ilçesi"]
          ].filter((c, ci) => ci === 0 || c[0] !== "0")
            .map((c) => `<div class="stat-cell"><b>${c[0]}</b><span>${c[1]}</span></div>`).join("")}
        </div>

        <h2 class="block-title"><svg><use href="#i-village"/></svg>Yerleşim birimleri</h2>
        <p class="block-sub">${esc(d.n)} ilçesine bağlı ${nf(koy.length + mah.length)} yerleşim birimi.</p>
        <div class="ilce-settle">
          ${koy.length ? `<div class="settle-block"><span class="chip-label">Köyler (${nf(koy.length)})</span>
            <div class="village-chips">${koy.map((k) => `<span class="village-chip">${icon("i-village", "i12")}${esc(k)}</span>`).join("")}</div></div>` : ""}
          ${mah.length ? `<div class="settle-block"><span class="chip-label">Mahalleler (${nf(mah.length)})</span>
            <div class="village-chips">${mah.map((k) => `<span class="village-chip mahalle">${esc(k)}</span>`).join("")}</div></div>` : ""}
          ${(!koy.length && !mah.length) ? `<p class="muted">Bu ilçe için kayıtlı yerleşim birimi bulunmuyor.</p>` : ""}
        </div>

        <h2 class="block-title"><svg><use href="#i-compass"/></svg>${esc(d.n)} içindeki keşif noktaları</h2>
        ${list.length
          ? `<div class="p-grid">${list.map(placeCard).join("")}</div>`
          : `<div class="empty">Bu ilçede kayıtlı keşif noktası yok. <a href="#/kesfet?il=${i}&ilce=${encodeURIComponent(d.n)}">Tüm Türkiye'de ara →</a></div>`}

        <h2 class="block-title"><svg><use href="#i-map"/></svg>${esc(il.n)} ilinin diğer ilçeleri</h2>
        <div class="district-chips">
          ${others.map((o) => `<a class="district-chip" href="#/ilce/${IL_SLUG[i]}/${slug(o.x.n)}">
            ${esc(o.x.n)}<em>${nf(o.x.k.length + (o.x.m ? o.x.m.length : 0))}</em></a>`).join("")}
          ${il.d.length > others.length + 1 ? `<a class="district-chip more" href="#/il/${IL_SLUG[i]}">Tümü (${nf(il.d.length)}) →</a>` : ""}
        </div>

        <div class="modal-actions" style="margin:22px 0 8px">
          <a class="btn btn-red" href="#/il/${IL_SLUG[i]}">${icon("i-arrow-right")}${esc(il.n)} il sayfası</a>
          <a class="btn btn-ghost" href="#/kesfet?il=${i}&ilce=${encodeURIComponent(d.n)}">${icon("i-search")}Keşfet'te filtrele</a>
        </div>
      </div>`;
    void ilceSlug;
  }

  function renderKategori(catId, params) {
    const ci = catById[catId];
    if (ci === undefined) { location.hash = "#/kesfet"; return; }
    const cat = CATS[ci];
    const list = byCoordFirst(PLACES.filter((p) => p[1] === ci));
    const perIl = ILS.map((il, i) => ({ il, i, n: byIlCat[i][ci].length })).filter((x) => x.n > 0);
    const view = $("#view-page");
    view.innerHTML = `
      <div class="page-head">
        <div class="container">
          <nav class="crumb"><a href="#/">Ana Sayfa</a><span>/</span><a href="#/kesfet">Keşfet</a><span>/</span><b>${esc(cat.label)}</b></nav>
          <h1><span class="cat-h-ic" style="--c:${CAT_COLORS[ci]}">${catIcon(ci, 26)}</span>${esc(cat.label)}</h1>
          <p class="page-sub">${esc(CAT_DESC[cat.id] || "")}</p>
          <p class="page-sub" style="margin-top:2px">Bu kategoride ${nf(list.length)} kayıt (${nf(list.filter(hasCoord).length)} konumlu), ${perIl.length} ilde</p>
          <div class="env-row">
            ${cat.env.map((e) => `<div class="env-chip"><b>${esc(e.v)}</b><span>${esc(e.l)}</span></div>`).join("")}
          </div>
          <p class="env-note">Envanter rakamları resmî/derleme toplamlardır. Kayıtların bir kısmının koordinatı doğrulanamadığı için bunlar listede "konum yok" etiketiyle görünür ve "Haritada ara" ile ada göre aranır.</p>
        </div>
      </div>
      <div class="container">
        <div class="filter-bar">
          <select id="kil" aria-label="İl">
            <option value="">Tüm iller</option>
            ${perIl.map((x) => `<option value="${x.i}">${String(x.il.p).padStart(2, "0")} ${esc(x.il.n)} (${x.n})</option>`).join("")}
          </select>
          <div class="f-search">${icon("i-search")}<input id="kq" type="search" placeholder="${esc(cat.label)} içinde ara…"></div>
        </div>
        <div class="result-info" id="kInfo"></div>
        <div class="p-grid" id="kGrid"></div>
        <div class="load-more-wrap"><button class="btn btn-navy" id="kMore" hidden>Daha fazla göster</button></div>
      </div>`;
    let page = 0;
    const PER = 48;
    function paint() {
      const ilSel = $("#kil").value;
      const q = $("#kq").value.trim();
      let items = list;
      if (ilSel !== "") items = items.filter((p) => p[2] === Number(ilSel));
      if (q) items = items.filter((p) => norm(p[0] + " " + (p[6] || "") + " " + p[3]).includes(norm(q)));
      const shown = items.slice(0, (page + 1) * PER);
      $("#kGrid").innerHTML = shown.map(placeCard).join("") || `<div class="empty">Sonuç bulunamadı.</div>`;
      $("#kInfo").textContent = `${nf(items.length)} sonuçtan ${nf(shown.length)} tanesi gösteriliyor`;
      $("#kMore").hidden = shown.length >= items.length;
    }
    $("#kil").addEventListener("change", () => { page = 0; paint(); });
    $("#kq").addEventListener("input", debounce(() => { page = 0; paint(); }, 180));
    $("#kMore").addEventListener("click", () => { page++; paint(); });
    paint();
  }

  function debounce(fn, ms) {
    let t;
    return function () { clearTimeout(t); t = setTimeout(fn, ms); };
  }

  /* ---------------------------------------------------------------- router */
  function parseHash() {
    const h = location.hash.replace(/^#/, "") || "/";
    const [path, qs] = h.split("?");
    return { path, params: new URLSearchParams(qs || "") };
  }

  function router() {
    if (location.hash.includes("access_token=")) {
      adoptTokens(location.hash);
      if (location.hash !== "#/" && location.hash !== "") return;
    }
    const { path, params } = parseHash();
    const home = $("#view-home");
    const page = $("#view-page");
    const seg = path.split("/").filter(Boolean);

    document.body.classList.toggle("is-home", seg.length === 0);
    $$(".main-nav .nav-link").forEach((a) => a.classList.remove("active"));

    if (seg.length === 0) {
      home.hidden = false; page.hidden = true;
      if (!$("#catCard").childElementCount) renderHome();
      const nav = $('[data-nav="home"]'); if (nav) nav.classList.add("active");
    } else {
      home.hidden = true; page.hidden = false;
      if (seg[0] === "kesfet") { renderKesfet(params); }
      else if (seg[0] === "iller") { renderIller(); const a = $('[data-nav="iller"]'); if (a) a.classList.add("active"); }
      else if (seg[0] === "rotalar") { renderRotalar(params); const a = $('[data-nav="rotalar"]'); if (a) a.classList.add("active"); }
      else if (seg[0] === "il" && seg[1]) {
        const i = ilBySlug[seg[1]];
        if (i === undefined) { location.hash = "#/iller"; return; }
        renderIl(i, params.get("kat"));
      } else if (seg[0] === "kategori" && seg[1]) { renderKategori(seg[1], params); }
      else if (seg[0] === "mevsim" && seg[1]) {
        if (!seasonById[seg[1]]) { location.hash = "#/"; return; }
        renderMevsim(seg[1]);
      }
      else if (seg[0] === "ara") { renderKesfet(params); }
      else if (seg[0] === "hesabim") { renderHesabim(); }
      else if (seg[0] === "rota" && seg[1]) {
        // statik rota sayfasına devret (önceden oluşturulmuş, hızlı)
        location.replace("rota/" + encodeURIComponent(seg[1]) + "/");
        return;
      }
      else if (seg[0] === "ilce" && seg[1] && seg[2]) {
        const i = ilBySlug[seg[1]];
        const di = i === undefined ? undefined : DIST_SLUG[i][seg[2]];
        if (i === undefined || di === undefined) { location.hash = "#/iller"; return; }
        renderIlce(i, di);
      }
      else { location.hash = "#/"; return; }
      window.scrollTo({ top: 0, behavior: "instant" in window ? "instant" : "auto" });
      onScroll();
    }
    updateFavCount();
    applyMeta(seg, params);
  }

  /* ---------------------------------------------------------------- dinamik olaylar */
  // Kartlar her sayfa geçişinde yeniden üretildiği için olaylar delege edilir.
  function bindDynamic() { /* delege edildi: aşağıdaki global click dinleyicisi */ }

  /* ---------------------------------------------------------------- global olaylar */
  document.addEventListener("click", (e) => {
    // --- delege edilmiş kart olayları
    const favEl = e.target.closest("[data-fav]");
    if (favEl) {
      e.preventDefault(); e.stopPropagation();
      const [ilIdx, name] = favEl.dataset.fav.split("|");
      const p = PLACES.find((x) => x[2] === Number(ilIdx) && x[0] === name);
      if (p) toggleFav(p);
      return;
    }
    const placeEl = e.target.closest("[data-place]");
    if (placeEl) { e.preventDefault(); openPlace(Number(placeEl.dataset.place)); return; }
    if (e.target.closest("[data-wx-enable]")) {
      e.preventDefault();
      setConsent("all");
      toast("Hava durumu açıldı (Open-Meteo)");
      mountHeaderWx();
      const act = location.hash.split("?")[0];
      if (act.startsWith("#/il/") && ilBySlug[act.split("/")[2]]) mountWx(ilBySlug[act.split("/")[2]]);
      return;
    }
    if (e.target.closest("[data-auth-open]")) {
      e.preventDefault();
      if (auth) { location.hash = "#/hesabim"; } else openAuthModal();
      return;
    }
    if (e.target.closest("[data-resume]")) {
      e.preventDefault();
      const b = e.target.closest("[data-resume]");
      startRoute(b.dataset.resume, Number(b.dataset.resumeAt) || 0);
      return;
    }
    if (e.target.closest("[data-account-done]")) {
      e.preventDefault();
      progDone(e.target.closest("[data-account-done]").dataset.accountDone);
      renderHesabim();
      toast("Rota tamamlandı olarak işaretlendi");
      return;
    }
    if (e.target.closest("[data-account-unfav]")) {
      e.preventDefault();
      const key = e.target.closest("[data-account-unfav]").dataset.accountUnfav;
      favs = favs.filter((f) => f !== key);
      writeJSON(FAV_KEY, favs);
      updateFavCount();
      if (auth) removeRemoteFav(key);
      renderHesabim();
      toast("Favorilerden çıkarıldı");
      return;
    }
    if (e.target.closest("[data-account-sync]")) {
      e.preventDefault();
      Promise.all([syncFavorites(), progPull()]).then(() => { renderHesabim(); toast("Favoriler ve ilerleme eşitlendi"); });
      return;
    }
    if (e.target.closest("[data-account-export]")) { e.preventDefault(); exportData(); return; }
    if (e.target.closest("[data-account-purge]")) {
      e.preventDefault();
      openModal(`
        <div class="modal-hero" style="height:120px;background:linear-gradient(135deg,#b3261e,#0a2c52)">
          <span class="mh-ic">${icon("i-close", "i24")}</span>
          <span class="mh-cat">Geri alınamaz işlem</span>
        </div>
        <div class="modal-body">
          <h3 id="modalTitle">Hesap verilerimi sil</h3>
          <p class="sub">Favoriler, rota ilerlemesi ve bu cihazdaki kayıtlar silinecek; oturumunuz kapanacak.</p>
          <p class="auth-fine">E-posta kaydınızın da silinmesini isterseniz <a href="iletisim/">iletişim</a> sayfasından yazın (KVKK m.11).</p>
          <div class="modal-actions">
            <button class="btn btn-red" data-purge-confirm>${icon("i-close")}Evet, sil</button>
            <button class="btn btn-ghost" data-close-modal>Vazgeç</button>
          </div>
        </div>`);
      return;
    }
    if (e.target.closest("[data-purge-confirm]")) { e.preventDefault(); closeModal(); purgeAccount(); return; }
    if (e.target.closest("[data-auth-signout]")) { e.preventDefault(); signOut(); return; }
    if (e.target.closest("[data-fav-sync]")) { e.preventDefault(); syncFavorites().then(() => toast("Favoriler eşitlendi")); return; }
    const shareBtn = e.target.closest("[data-share-route]");
    if (shareBtn) { e.preventDefault(); shareRoute(shareBtn.dataset.shareRoute); return; }
    const icsBtn = e.target.closest("[data-ics-route]");
    if (icsBtn) { e.preventDefault(); downloadIcs(icsBtn.dataset.icsRoute); return; }
    const liveStart = e.target.closest("[data-live-start]");
    if (liveStart) { e.preventDefault(); e.stopPropagation(); startRoute(liveStart.dataset.liveStart, 0); return; }
    if (e.target.closest("[data-live-next]")) { e.preventDefault(); liveGo(1); return; }
    if (e.target.closest("[data-live-prev]") && !e.target.closest("[data-live-prev]").disabled) { e.preventDefault(); liveGo(-1); return; }
    if (e.target.closest("[data-live-end]")) {
      e.preventDefault();
      const biten = liveRoute && liveRoute.rid;
      closeModal(); liveRoute = null;
      if (biten && typeof progDone === "function") progDone(biten);
      toast("Rota tamamlandı 🎉");
      return;
    }
    if (e.target.closest("[data-live-close]")) { e.preventDefault(); closeModal(); liveRoute = null; return; }
    const routeEl = e.target.closest("[data-route]");
    if (routeEl) { e.preventDefault(); openRoute(routeEl.dataset.route); return; }
    const ilEl = e.target.closest("[data-il]");
    if (ilEl) { location.hash = `#/il/${IL_SLUG[Number(ilEl.dataset.il)]}`; closeModal(); return; }

    const closeNav = e.target.closest("[data-close-nav]");
    if (closeNav) closeModal();

    const toastEl = e.target.closest("[data-toast]");
    if (toastEl && !toastEl.closest("#modal")?.contains(toastEl)) {
      // modal dışındaki toast butonları
      if (!e.target.closest("#modal")) { e.preventDefault(); toast(toastEl.dataset.toast); return; }
    }

    if (e.target.closest("[data-open-map]")) { openMapModal(); return; }
    if (e.target.closest("[data-open-favs]")) { openFavs(); return; }
    if (e.target.closest("[data-nearby]")) {
      toast("Konum izni demo sürümde kullanılmıyor — Antalya yakınındaki keşifler listelendi");
      location.hash = "#/il/antalya";
      return;
    }
    const season = e.target.closest("[data-season]");
    if (season) { location.hash = `#/mevsim/${season.dataset.season}`; return; }
    if (e.target.closest("[data-close-modal]")) { closeModal(); return; }
  });

  // hero arama
  function initHeroSearch() {
    const input = $("#searchInput");
    const suggest = $("#suggest");
    input.addEventListener("input", () => {
      if (input.value.trim().length > 0) renderSuggest(input.value.trim());
      else suggest.classList.remove("show");
    });
    input.addEventListener("focus", () => { if (input.value.trim()) renderSuggest(input.value.trim()); });
    document.addEventListener("click", (e) => {
      if (!e.target.closest(".search-wrap")) suggest.classList.remove("show");
    });
    $("#searchForm").addEventListener("submit", (e) => {
      e.preventDefault();
      const q = input.value.trim();
      location.hash = q ? `#/kesfet?q=${encodeURIComponent(q)}` : "#/kesfet";
      suggest.classList.remove("show");
    });
    const SCOPES = ["Tüm Türkiye", "Yakınımdaki Yerler", "Sadece şehir merkezleri"];
    let si = 0;
    $("#scopeBtn").addEventListener("click", () => {
      si = (si + 1) % SCOPES.length;
      $("#scopeLabel").textContent = SCOPES[si];
      toast(`Arama kapsamı: ${SCOPES[si]}`);
    });
  }

  // dropdown menüler
  $$("[data-dropdown]").forEach((item) => {
    const btn = $(".nav-link", item);
    btn.addEventListener("click", (e) => {
      e.stopPropagation();
      const wasOpen = item.classList.contains("open");
      $$("[data-dropdown]").forEach((d) => { d.classList.remove("open"); $(".nav-link", d).setAttribute("aria-expanded", "false"); });
      item.classList.toggle("open", !wasOpen);
      btn.setAttribute("aria-expanded", String(!wasOpen));
    });
  });
  document.addEventListener("click", (e) => {
    if (!e.target.closest("[data-dropdown]")) {
      $$("[data-dropdown]").forEach((d) => { d.classList.remove("open"); $(".nav-link", d).setAttribute("aria-expanded", "false"); });
    }
  });

  // sticky header
  const header = $("#siteHeader");
  function onScroll() {
    const solid = !document.body.classList.contains("is-home") || window.scrollY > 40;
    header.classList.toggle("scrolled", solid);
  }
  window.addEventListener("scroll", onScroll, { passive: true });

  // v19: mobil/tablette aşağı kaydırırken başlığı gizle, yukarı kaydırınca geri getir
  let lastY = window.scrollY;
  window.addEventListener("scroll", () => {
    if (window.innerWidth > 899) {
      if (header.classList.contains("is-hidden")) header.classList.remove("is-hidden");
      lastY = window.scrollY; return;
    }
    const y = window.scrollY, d = y - lastY;
    if (Math.abs(d) < 6) return;
    if (d > 0 && y > 140 && !document.body.classList.contains("nav-open")) header.classList.add("is-hidden");
    else if (d < 0) header.classList.remove("is-hidden");
    lastY = y;
  }, { passive: true });

  // mobil menü
  const burger = $("#burger");
  const mobileMenu = $("#mobileMenu");
  burger.addEventListener("click", () => {
    const open = mobileMenu.classList.toggle("open");
    burger.setAttribute("aria-expanded", String(open));
    document.body.classList.toggle("nav-open", open);
    header.classList.remove("is-hidden");
  });
  mobileMenu.addEventListener("click", (e) => {
    if (e.target.closest("a")) { mobileMenu.classList.remove("open"); document.body.classList.remove("nav-open"); burger.setAttribute("aria-expanded", "false"); }
  });


  // klavye
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { closeModal(); $("#suggest")?.classList.remove("show"); }
    if ((e.key === "Enter" || e.key === " ") && e.target.closest && e.target.closest("[data-il]")) {
      e.preventDefault();
      location.hash = `#/il/${IL_SLUG[Number(e.target.closest("[data-il]").dataset.il)]}`;
      closeModal();
    }
  });

  // reveal
  let io = null;
  function observeReveal() {
    if (!("IntersectionObserver" in window)) { $$(".reveal").forEach((el) => el.classList.add("in")); return; }
    if (!io) {
      io = new IntersectionObserver((entries) => entries.forEach((en) => {
        if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
      }), { threshold: 0.1 });
    }
    $$(".reveal:not(.in)").forEach((el) => io.observe(el));
  }


  /* ================================================================ v12
     Kimlik (Supabase), favori senkronu, onay şeridi, paylaşım, erişilebilirlik
     ================================================================ */
  const SITE = "https://xharunkoca.github.io/turkiye-kesif/";
  const SB_URL = "https://laqmoghxnwsavulkmzls.supabase.co";
  const SB_KEY = "sb_publishable_m9-WvY1Bb8OXg_P2qAY-tg_irpa44G5";
  const AUTH_KEY = "tk-auth-v1";
  const CONSENT_KEY = "tk-consent-v1";

  /* ---------------------------------------------------- onay / aydınlatma şeridi */
  const consentState = () => { try { return localStorage.getItem(CONSENT_KEY); } catch (e) { return null; } };
  const wxAllowed = () => consentState() === "all";
  function setConsent(v) {
    try { localStorage.setItem(CONSENT_KEY, v); } catch (e) { /* yoksay */ }
    const el = $("#consent"); if (el) el.hidden = true;
    if (v === "essential") $$(".wx-line, .wx-panel, #headerWx").forEach((x) => { x.innerHTML = ""; });
    else mountHeaderWx();
  }
  function mountConsent() {
    const el = $("#consent");
    if (!el) return;
    if (consentState()) { el.hidden = true; return; }
    el.hidden = false;
    const ok = $("#consentOk"), no = $("#consentNo");
    if (ok) ok.addEventListener("click", () => setConsent("all"));
    if (no) no.addEventListener("click", () => setConsent("essential"));
  }

  /* ---------------------------------------------------- Supabase oturumu (fetch, sıfır bağımlılık) */
  let auth = null;
  try { auth = JSON.parse(localStorage.getItem(AUTH_KEY) || "null"); } catch (e) { auth = null; }

  function jwtEmail(tok) {
    try {
      const payload = JSON.parse(atob(tok.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
      return { email: payload.email || null, uid: payload.sub || null };
    } catch (e) { return { email: null, uid: null }; }
  }
  function saveAuth(v) {
    auth = v;
    try { v ? localStorage.setItem(AUTH_KEY, JSON.stringify(v)) : localStorage.removeItem(AUTH_KEY); } catch (e) { /* yoksay */ }
    renderAuthUI();
  }

  async function sbAuth(path, body) {
    const r = await fetch(`${SB_URL}/auth/v1/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", apikey: SB_KEY },
      body: JSON.stringify(body || {})
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.msg || data.error_description || data.message || `HTTP ${r.status}`);
    return data;
  }

  async function sendLoginLink(email) {
    return sbAuth("otp", { email, create_user: true, options: { email_redirect_to: SITE } });
  }

  function adoptTokens(fragment) {
    const p = new URLSearchParams(String(fragment || "").replace(/^#/, ""));
    const at = p.get("access_token"), rt = p.get("refresh_token");
    if (!at) return false;
    const info = jwtEmail(at);
    saveAuth({
      access_token: at, refresh_token: rt, uid: info.uid, email: info.email,
      exp: Date.now() + (Number(p.get("expires_in") || 3600) * 1000)
    });
    history.replaceState(null, "", location.pathname + location.search + "#/");
    toast(info.email ? `Giriş yapıldı — ${info.email}` : "Giriş yapıldı");
    syncFavorites();
    progPull().then(() => { if (location.hash.startsWith("#/hesabim")) renderHesabim(); });
    return true;
  }

  async function ensureSession() {
    if (!auth) return null;
    if (auth.exp && Date.now() < auth.exp - 90000) return auth;
    if (!auth.refresh_token) return null;
    try {
      const d = await sbAuth("token?grant_type=refresh_token", { refresh_token: auth.refresh_token });
      saveAuth({ ...auth, access_token: d.access_token, refresh_token: d.refresh_token, exp: Date.now() + (d.expires_in || 3600) * 1000 });
      return auth;
    } catch (e) { saveAuth(null); return null; }
  }

  async function sbRest(path, opts) {
    const s2 = await ensureSession();
    if (!s2) throw new Error("oturum yok");
    const r = await fetch(`${SB_URL}/rest/v1/${path}`, {
      ...(opts || {}),
      headers: {
        apikey: SB_KEY,
        Authorization: `Bearer ${s2.access_token}`,
        "Content-Type": "application/json",
        ...((opts && opts.headers) || {})
      }
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.status === 204 ? null : r.json();
  }

  async function syncFavorites() {
    const s2 = await ensureSession();
    if (!s2) return;
    try {
      const rows = (await sbRest("favorites?select=place_key")) || [];
      const remote = new Set(rows.map((r) => r.place_key));
      const missing = favs.filter((k) => !remote.has(k));
      if (missing.length) {
        const body = missing.map((k) => {
          const cut = k.indexOf("|");
          const ilIdx = Number(k.slice(0, cut)), name = k.slice(cut + 1);
          const p = PLACES.find((x) => x[2] === ilIdx && x[0] === name);
          return { place_key: k, name, il: p ? ILS[p[2]].n : null, cat: p ? CATS[p[1]].id : null };
        });
        await sbRest("favorites", {
          method: "POST",
          headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
          body: JSON.stringify(body)
        });
      }
      favs = [...new Set([...favs, ...remote])];
      try { localStorage.setItem(FAV_KEY, JSON.stringify(favs)); } catch (e) { /* yoksay */ }
      updateFavCount();
    } catch (e) { /* sessiz: yerel modda devam */ }
  }

  async function removeRemoteFav(key) {
    if (!auth) return;
    try { await sbRest(`favorites?place_key=eq.${encodeURIComponent(key)}`, { method: "DELETE" }); } catch (e) { /* yoksay */ }
  }

  /* ---------------------------------------------------- kimlik arayüzü */
  function renderAuthUI() {
    const btn = $(".btn-auth");
    if (btn) {
      btn.innerHTML = auth
        ? `<svg width="16" height="16" aria-hidden="true"><use href="#i-user"/></svg><span>${esc((auth.email || "Hesabım").split("@")[0])}</span>`
        : `<svg width="16" height="16" aria-hidden="true"><use href="#i-user"/></svg><span>Giriş · Üye Ol</span>`;
    }
    const mm = $(".mm-cta.btn");
    if (mm) mm.textContent = auth ? "Hesabım" : "Giriş · Üye Ol";
  }

  function openAuthModal() {
    if (auth) {
      openModal(`
        <div class="modal-hero" style="background:linear-gradient(135deg,#1c6fae,#0a2c52)">
          <span class="mh-ic">${icon("i-user", "i24")}</span>
          <span class="mh-cat">Hesabım</span>
        </div>
        <div class="modal-body">
          <h3 id="modalTitle">${esc(auth.email || "Giriş yapıldı")}</h3>
          <p class="sub">${nf(favs.length)} favori bu hesaba bağlı</p>
          <p class="auth-fine">Favorileriniz ve rota ilerlemeniz Supabase üzerinden tüm cihazlarınızda eşitlenir.
            Verileriniz yalnızca size görünür (satır düzeyi güvenlik). Ayrıntı: <a href="kvkk-aydinlatma/">KVKK Aydınlatma</a>.</p>
          <div class="modal-actions">
            <button class="btn btn-red" data-fav-sync>${icon("i-heart")}Favorileri eşitle</button>
            <button class="btn btn-ghost" data-auth-signout>${icon("i-close")}Çıkış yap</button>
          </div>
        </div>`);
      return;
    }
    openModal(`
      <div class="modal-hero" style="background:linear-gradient(135deg,#b3261e,#0a2c52)">
        <span class="mh-ic">${icon("i-user", "i24")}</span>
        <span class="mh-cat">Giriş / Üyelik</span>
      </div>
      <div class="modal-body">
        <h3 id="modalTitle">E-posta ile giriş</h3>
        <p class="sub">Şifre yok — tek kullanımlık giriş bağlantısı gönderilir.</p>
        <form class="auth-form" id="authForm" novalidate>
          <label for="authEmail">E-posta adresiniz</label>
          <input id="authEmail" type="email" autocomplete="email" inputmode="email" placeholder="ornek@eposta.com" required>
          <button class="btn btn-red" type="submit">Giriş bağlantısı gönder</button>
        </form>
        <p class="form-note" id="authNote" role="status" aria-live="polite">Favorileriniz giriş sonrası bu hesaba bağlanır ve tüm cihazlarınızda görünür.</p>
        <p class="auth-fine">Kişisel verileriniz yalnızca kimlik doğrulama ve favori listesi için işlenir.
          Ayrıntı: <a href="kvkk-aydinlatma/">KVKK Aydınlatma</a> · <a href="gizlilik/">Gizlilik</a></p>
      </div>`);
  }

  async function doSignIn(email, noteEl) {
    const note = noteEl || $("#authNote") || $("#loginNote");
    const setNote = (t) => { if (note) note.textContent = t; };
    if (!email || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(email)) { setNote("Geçerli bir e-posta adresi girin."); return; }
    setNote("Gönderiliyor…");
    try {
      await sendLoginLink(email);
      setNote(`Bağlantı gönderildi: ${email}. Gelen kutunuza (ve spam klasörüne) bakın; bağlantı 1 saat geçerli.`);
    } catch (e) {
      setNote(`Gönderilemedi: ${String(e.message || e).slice(0, 90)} — birkaç dakika sonra tekrar deneyin.`);
    }
  }

  function signOut() {
    saveAuth(null);
    closeModal();
    toast("Çıkış yapıldı — favoriler bu cihazda kaldı");
  }

  /* ---------------------------------------------------- paylaşım / takvim */
  function routeShareText(r) {
    const il = ILS[r.ilIdx];
    return `${il.n} — ${r.theme.label} · ${nf(r.km)} km · ${r.stops.length} durak\n` +
      r.stops.map((s, i) => `${i + 1}. ${s[0]} (${s[3] || il.n})`).join("\n") +
      `\n\nHarita: ${routeDirUrl(r)}\nTürkiye Keşif: ${SITE}#/il/${IL_SLUG[r.ilIdx]}`;
  }

  function copyText(t, okMsg) {
    const done = () => toast(okMsg || "Panoya kopyalandı");
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(t).then(done, () => legacyCopy(t, done));
    } else legacyCopy(t, done);
  }
  function legacyCopy(t, done) {
    const ta = document.createElement("textarea");
    ta.value = t; ta.setAttribute("readonly", "");
    ta.style.position = "fixed"; ta.style.opacity = "0";
    document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); done(); } catch (e) { toast("Kopyalanamadı — bağlantı yeni sekmede açıldı"); window.open(routeDirUrlish(t), "_blank"); }
    ta.remove();
  }
  const routeDirUrlish = () => SITE;

  async function shareRoute(id) {
    const r = allRoutes().find((x) => x.id === id);
    if (!r) return;
    const text = routeShareText(r);
    if (navigator.share) {
      try { await navigator.share({ title: `${ILS[r.ilIdx].n} — ${r.theme.label}`, text }); return; } catch (e) { /* iptal → kopyala */ }
    }
    copyText(text, "Rota metni panoya kopyalandı");
  }

  function downloadIcs(id) {
    const r = allRoutes().find((x) => x.id === id);
    if (!r) return;
    const pad = (n) => String(n).padStart(2, "0");
    const stamp = (d) => `${d.getUTCFullYear()}${pad(d.getUTCMonth() + 1)}${pad(d.getUTCDate())}T${pad(d.getUTCHours())}${pad(d.getUTCMinutes())}00Z`;
    const start = new Date(); start.setUTCHours(6, 0, 0, 0);
    const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Turkiye Kesif//ROTA//TR", "CALSCALE:GREGORIAN"];
    r.stops.forEach((s, i) => {
      const s0 = new Date(start.getTime() + i * 3 * 3600 * 1000);
      const s1 = new Date(s0.getTime() + 90 * 60 * 1000);
      lines.push("BEGIN:VEVENT",
        `UID:${r.id}-${i}@turkiye-kesif`,
        `DTSTAMP:${stamp(new Date())}`,
        `DTSTART:${stamp(s0)}`, `DTEND:${stamp(s1)}`,
        `SUMMARY:${ILS[r.ilIdx].n} · ${i + 1}. durak: ${s[0]}`.replace(/[\n,;]/g, " "),
        `DESCRIPTION:${r.theme.label} · ${CATS[s[1]].label} · https://www.google.com/maps/search/?api=1&query=${s[4]},${s[5]}`,
        `GEO:${s[4]};${s[5]}`,
        `LOCATION:${(s[3] || ILS[r.ilIdx].n)} / ${ILS[r.ilIdx].n}`,
        "END:VEVENT");
    });
    lines.push("END:VCALENDAR");
    const blob = new Blob([lines.join("\r\n")], { type: "text/calendar;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `turkiye-kesif-${r.id}.ics`;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    toast("Takvim dosyası indirildi (.ics)");
  }

  /* ---------------------------------------------------- erişilebilirlik: modal odak tuzağı */
  const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select, textarea, [tabindex]:not([tabindex="-1"])';
  function trapStart() {
    if (!("inert" in HTMLElement.prototype)) return;
    Array.from(document.body.children).forEach((el) => {
      if (el.id === "modal" || el.tagName === "SCRIPT" || el.tagName === "NOSCRIPT" || el.id === "toast") return;
      el.setAttribute("inert", "");
    });
  }
  function trapEnd() {
    Array.from(document.body.children).forEach((el) => el.removeAttribute("inert"));
  }
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    if (!modal || !modal.classList.contains("open")) return;
    const f = $$(FOCUSABLE, $("#modalCard")).filter((el) => el.offsetParent !== null);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  /* ---------------------------------------------------- sayfa başlığı / meta (paylaşım + arama) */
  function setMeta(sel, attr, val) {
    const el = document.querySelector(sel);
    if (el) el.setAttribute(attr, val);
  }
  function applyMeta(seg, params) {
    const base = "Türkiye Keşif";
    let title = `${base} — 81 İl · 15 Kategori · ${nf(ROUTE_COUNT)} Hazır Rota`;
    let desc = `81 il, 1.004 ilçe, 45.060 köy/mahalle; 15 kategoride ${nf(PLACE_COUNT)} keşif kaydı ve her il için 5 gezi rotası. Haritada doğrulanmış konumlar, tek dokunuşla rota başlatma.`;
    let path = "";
    if (seg[0] === "il" && seg[1] && ilBySlug[seg[1]] !== undefined) {
      const i = ilBySlug[seg[1]], il = ILS[i];
      const n = byIl[i].length;
      title = `${il.n} Gezilecek Yerler — ${n} Nokta ve 5 Rota | ${base}`;
      desc = `${il.n} ilinde ${n} keşif kaydı, ${il.d.length} ilçe, ${nf(villCount(il))} köy/mahalle ve 5 hazır gezi rotası. Konumlar haritada doğrulanmış.`;
      path = `il/${IL_SLUG[i]}/`;
    } else if (seg[0] === "kategori" && seg[1]) {
      const ci = CATS.findIndex((c) => c.id === seg[1]);
      if (ci >= 0) {
        const list = PLACES.filter((p) => p[1] === ci);
        title = `${CATS[ci].label} — ${nf(list.length)} Kayıt | ${base}`;
        desc = `Türkiye genelinde ${nf(list.length)} ${CATS[ci].label.toLowerCase()} kaydı; ${list.filter(hasCoord).length} tanesi haritada doğrulanmış koordinatla.`;
        path = `kategori/${CATS[ci].id}/`;
      }
    } else if (seg[0] === "kesfet") {
      title = `Keşfet — ${nf(PLACE_COUNT)} Kayıt, 15 Kategori | ${base}`;
      desc = `Arama ve filtrelerle ${nf(PLACE_COUNT)} keşif kaydı: antik kentler, müzeler, doğa, göller, plajlar ve daha fazlası.`;
      path = "kesfet/";
    } else if (seg[0] === "iller") {
      title = `81 İl ve İlçeler — Gezi Rehberi | ${base}`;
      desc = "Türkiye'nin 81 ili, 1.004 ilçesi: her il için keşif noktaları, rota ve hava durumu.";
      path = "iller/";
    } else if (seg[0] === "rotalar") {
      title = `${nf(ROUTE_COUNT)} Hazır Gezi Rotası — 5 Tema | ${base}`;
      desc = `81 il için ${nf(ROUTE_COUNT)} hazır rota: tarih, doğa, inanç, lezzet ve deniz temaları; her durak tek dokunuşla navigasyona bağlı.`;
      path = "rotalar/";
    } else if (seg[0] === "hesabim") {
      title = `Hesabım — Favoriler ve Rota İlerlemesi | ${base}`;
      desc = "Giriş yaparak favorilerinizi ve rota ilerlemenizi tüm cihazlarınızda eşitleyin; verilerinizi tek tuşla indirin veya silin.";
      path = "hesabim/";
    } else if (seg[0] === "mevsim" && seg[1] && seasonById[seg[1]]) {
      const se = seasonById[seg[1]];
      title = `${se.n} Rotası — Mevsime Göre Keşif | ${base}`;
      desc = `${se.n} ayı için seçilmiş keşif noktaları ve rotalar (${se.months}).`;
      path = `mevsim/${se.id}/`;
    }
    document.title = title;
    setMeta('meta[name="description"]', "content", desc);
    setMeta('meta[property="og:title"]', "content", title);
    setMeta('meta[property="og:description"]', "content", desc);
    setMeta('meta[name="twitter:title"]', "content", title);
    setMeta('meta[name="twitter:description"]', "content", desc);
    const canon = document.querySelector('link[rel="canonical"]');
    if (canon) canon.setAttribute("href", SITE + path);
    setMeta('meta[property="og:url"]', "content", SITE + path);
  }

  document.addEventListener("submit", (e) => {
    const authForm = e.target.closest("#authForm");
    if (authForm) { e.preventDefault(); doSignIn(($("#authEmail") || {}).value, $("#authNote")); return; }
    const loginForm = e.target.closest("#loginForm");
    if (loginForm) { e.preventDefault(); doSignIn(($("#loginEmail") || {}).value, $("#loginNote")); return; }
  });


  /* ================================================================ v14
     Rota ilerlemesi (Supabase route_progress) + "Hesabım" sayfası
     ================================================================ */
  const PROG_KEY = "tk-progress-v1";
  const DONE_KEY = "tk-done-v1";

  const readJSON = (k, dflt) => {
    try { const v = JSON.parse(localStorage.getItem(k) || "null"); return v == null ? dflt : v; } catch (e) { return dflt; }
  };
  const writeJSON = (k, v) => { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* yoksay */ } };

  const progAll = () => readJSON(PROG_KEY, {});
  const doneAll = () => readJSON(DONE_KEY, []);

  // "34-1" → { ilIdx: 34, ti: 1 } → routesFor(34)[1]
  function routeByKey(id) {
    const parts = String(id || "").split("-");
    if (parts.length !== 2) return null;
    const ilIdx = Number(parts[0]), ti = Number(parts[1]);
    if (!Number.isInteger(ilIdx) || !Number.isInteger(ti)) return null;
    if (ilIdx < 0 || ilIdx >= ILS.length) return null;
    const list = routesFor(ilIdx);
    return (list && list[ti]) || null;
  }

  function progSet(id, i) {
    const m = progAll();
    if (i == null) delete m[id]; else m[id] = i;
    writeJSON(PROG_KEY, m);
  }

  let progTimer = null;
  function progPush(id, i) {
    progSet(id, i);
    if (!auth) return;
    clearTimeout(progTimer);
    progTimer = setTimeout(() => {
      sbRest("route_progress", {
        method: "POST",
        headers: { Prefer: "resolution=merge-duplicates,return=minimal" },
        body: JSON.stringify([{ route_id: id, stop_index: i, updated_at: new Date().toISOString() }])
      }).catch(() => { /* sessiz */ });
    }, 700);
  }

  function progDone(id) {
    progSet(id, null);
    const l = doneAll();
    if (!l.includes(id)) l.push(id);
    writeJSON(DONE_KEY, l);
    if (auth) sbRest(`route_progress?route_id=eq.${encodeURIComponent(id)}`, { method: "DELETE" }).catch(() => { /* sessiz */ });
  }

  async function progPull() {
    if (!auth) return;
    try {
      const rows = (await sbRest("route_progress?select=route_id,stop_index")) || [];
      const m = progAll();
      rows.forEach((r) => { if (typeof r.stop_index === "number") m[r.route_id] = r.stop_index; });
      writeJSON(PROG_KEY, m);
    } catch (e) { /* sessiz: yerel modda devam */ }
  }

  /* ---------------------------------------------------- Hesabım sayfası */
  function progressBar(i, n) {
    const pct = Math.max(6, Math.round(((i + 1) / Math.max(1, n)) * 100));
    return `<span class="prog-bar" role="img" aria-label="${i + 1}/${n} durak tamamlandı"><i style="width:${pct}%"></i></span>`;
  }

  function renderHesabim() {
    const view = $("#view-page");
    const m = progAll(), done = doneAll();
    const progIds = Object.keys(m).filter((id) => routeByKey(id));
    const doneIds = done.filter((id) => routeByKey(id));
    const favItems = favs.map((id) => {
      const cut = id.indexOf("|");
      const ilIdx = Number(id.slice(0, cut)), name = id.slice(cut + 1);
      const p = PLACES.find((x) => x[2] === ilIdx && x[0] === name);
      // kayıt bulunamazsa (veri güncellenmiş olabilir) yine de adıyla göster
      return p ? { p, id } : { p: null, id, name, il: ILS[ilIdx] ? ILS[ilIdx].n : "" };
    });

    const head = `
      <div class="page-head">
        <div class="container">
          <nav class="crumb"><a href="#/">Ana Sayfa</a><span>/</span><b>Hesabım</b></nav>
          <h1>Hesabım</h1>
          <p class="page-sub">Favorileriniz ve rota ilerlemeniz — giriş yaptığınızda tüm cihazlarınızda aynı.</p>
        </div>
      </div>`;

    if (!auth) {
      view.innerHTML = `${head}
        <div class="container">
          <section class="acc-grid">
            <div class="acc-card">
              <h2>E-posta ile giriş</h2>
              <p class="acc-sub">Şifre yok: tek kullanımlık giriş bağlantısı gönderilir, bağlantı 1 saat geçerlidir.</p>
              <form class="auth-form" id="accForm" novalidate>
                <label for="accEmail">E-posta adresiniz</label>
                <input id="accEmail" type="email" autocomplete="email" inputmode="email" placeholder="ornek@eposta.com" required>
                <button class="btn btn-red" type="submit">${icon("i-user")}Giriş bağlantısı gönder</button>
              </form>
              <p class="form-note" id="accNote" role="status" aria-live="polite">Giriş yapmadan da her şey çalışır; favoriler bu tarayıcıda saklanır.</p>
            </div>
            <div class="acc-card acc-quiet">
              <h2>Hesap ne değiştirir?</h2>
              <ul class="acc-list">
                <li>${icon("i-heart")}Favoriler telefon, tablet ve bilgisayarda aynı listede</li>
                <li>${icon("i-route")}Başladığınız rota kaldığı duraktan devam eder</li>
                <li>${icon("i-close")}Verilerinizi tek tuşla indirir veya silersiniz</li>
              </ul>
              <p class="acc-fine">Yalnızca e-posta adresiniz işlenir; reklam, izleme veya üçüncü taraf analitik yok.
                Ayrıntı: <a href="kvkk-aydinlatma/">KVKK Aydınlatma</a> · <a href="gizlilik/">Gizlilik</a></p>
            </div>
          </section>
          ${progIds.length ? `<section class="acc-section">
            <h2>Bu cihazdaki ilerleme</h2>
            <p class="acc-sub">Giriş yaparsanız bu ilerleme hesabınıza bağlanır.</p>
            <div class="acc-list-rows">${progIds.slice(0, 6).map((id) => resumeRow(id, m[id], false)).join("")}</div>
          </section>` : ""}
        </div>`;
      const f = $("#accForm");
      if (f) f.addEventListener("submit", (e) => { e.preventDefault(); doSignIn($("#accEmail").value.trim(), $("#accNote")); });
      return;
    }

    view.innerHTML = `${head}
      <div class="container">
        <section class="acc-card acc-status">
          <div>
            <span class="acc-label">Giriş yapıldı</span>
            <h2 class="acc-mail">${esc(auth.email || "hesabınız")}</h2>
            <p class="acc-sub">Favoriler ve rota ilerlemesi Supabase (AB/Frankfurt) üzerinde tutulur ve yalnızca sizin hesabınıza görünür.</p>
          </div>
          <div class="acc-actions">
            <button class="btn btn-red" data-account-sync>${icon("i-heart")}Eşitle</button>
            <button class="btn btn-ghost" data-account-export>${icon("i-clock")}Verilerimi indir</button>
            <button class="btn btn-ghost" data-auth-signout>${icon("i-close")}Çıkış yap</button>
          </div>
        </section>

        <section class="acc-section">
          <h2>Devam eden rotalar <em>${progIds.length}</em></h2>
          ${progIds.length
            ? `<div class="acc-list-rows">${progIds.map((id) => resumeRow(id, m[id], true)).join("")}</div>`
            : `<p class="acc-empty">Başladığınız bir rota yok. <a href="#/rotalar">${nf(ROUTE_COUNT)} hazır rotaya</a> göz atın.</p>`}
        </section>

        <section class="acc-section">
          <h2>Favorileriniz <em>${favItems.length}</em></h2>
          ${favItems.length
            ? `<div class="acc-fav-grid">${favItems.map(({ p, id, name, il }) => `
                <article class="acc-fav">
                  ${p ? `<button class="acc-fav-open" data-place="${p.idx}">
                    <span class="suggest-ic">${catIcon(p[1])}</span>
                    <span><span class="suggest-t">${esc(p[0])}</span><span class="suggest-m">${esc(CATS[p[1]].label)} • ${esc(ILS[p[2]].n)}</span></span>
                  </button>` : `<span class="acc-fav-open">
                    <span class="suggest-ic">${icon("i-heart")}</span>
                    <span><span class="suggest-t">${esc(name)}</span><span class="suggest-m">${esc(il)} · kayıt güncellenmiş olabilir</span></span>
                  </span>`}
                  <button class="acc-fav-x" data-account-unfav="${esc(id)}" aria-label="${esc(p ? p[0] : name)} favorilerden çıkar">${icon("i-close")}</button>
                </article>`).join("")}</div>`
            : `<p class="acc-empty">Henüz favori yok. Kartlardaki kalp ikonuna dokunarak ekleyin.</p>`}
        </section>

        ${doneIds.length ? `<section class="acc-section">
          <h2>Tamamlanan rotalar <em>${doneIds.length}</em></h2>
          <div class="acc-done">${doneIds.map((id) => {
            const r = routeByKey(id), il = ILS[r.ilIdx];
            return `<a class="chip" href="#/il/${IL_SLUG[r.ilIdx]}">${icon("i-check")}${esc(il.n)} · ${esc(r.theme.label)}</a>`;
          }).join("")}</div>
        </section>` : ""}

        <section class="acc-section acc-danger">
          <h2>Verilerimi sil</h2>
          <p class="acc-sub">Favorileriniz, rota ilerlemeniz ve bu cihazdaki kayıtlar silinir. İşlem geri alınamaz.</p>
          <button class="btn btn-ghost danger" data-account-purge>${icon("i-close")}Hesap verilerimi sil</button>
        </section>
      </div>`;
  }

  function resumeRow(id, i, withActions) {
    const r = routeByKey(id);
    if (!r) return "";
    const il = ILS[r.ilIdx];
    const n = r.stops.length;
    const idx = Math.max(0, Math.min(i, n - 1));
    return `<article class="acc-row">
      <div class="acc-row-main">
        <span class="acc-row-t">${esc(il.n)} — ${esc(r.theme.label)}</span>
        <span class="acc-row-m">${idx + 1}/${n} durak • ${nf(r.km)} km • sıradaki: ${esc(r.stops[idx][0])}</span>
        ${progressBar(idx, n)}
      </div>
      ${withActions ? `<div class="acc-row-actions">
        <button class="btn btn-red" data-resume="${esc(id)}" data-resume-at="${idx}">${icon("i-nav")}Devam et</button>
        <button class="btn btn-ghost" data-account-done="${esc(id)}">${icon("i-check")}Bitir</button>
      </div>` : `<span class="acc-row-m">%${Math.round(((idx + 1) / n) * 100)}</span>`}
    </article>`;
  }

  function exportData() {
    const payload = {
      olusturma: new Date().toISOString(),
      hesap: auth ? auth.email : null,
      favoriler: favs.map((id) => {
        const cut = id.indexOf("|");
        const ilIdx = Number(id.slice(0, cut)), name = id.slice(cut + 1);
        const p = PLACES.find((x) => x[2] === ilIdx && x[0] === name);
        return { ad: name, il: ILS[ilIdx] ? ILS[ilIdx].n : null, kategori: p ? CATS[p[1]].label : null };
      }),
      rota_ilerlemesi: Object.entries(progAll()).map(([id, i]) => {
        const r = routeByKey(id);
        return { rota: r ? `${ILS[r.ilIdx].n} — ${r.theme.label}` : id, durak: i + 1, toplam_durak: r ? r.stops.length : null };
      }),
      tamamlanan_rotalar: doneAll().map((id) => {
        const r = routeByKey(id);
        return r ? `${ILS[r.ilIdx].n} — ${r.theme.label}` : id;
      })
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "turkiye-kesif-verilerim.json";
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
    toast("Verileriniz JSON olarak indirildi");
  }

  async function purgeAccount() {
    if (auth) {
      try { await sbRest("favorites?id=not.is.null", { method: "DELETE" }); } catch (e) { /* yoksay */ }
      try { await sbRest("route_progress?route_id=not.is.null", { method: "DELETE" }); } catch (e) { /* yoksay */ }
    }
    favs = [];
    writeJSON(FAV_KEY, []);
    writeJSON(PROG_KEY, {});
    writeJSON(DONE_KEY, []);
    saveAuth(null);
    updateFavCount();
    toast("Verileriniz silindi");
    renderHesabim();
  }

  /* ---------------------------------------------------------------- başlat */
  window.addEventListener("hashchange", router);
  mountConsent();
  renderAuthUI();
  if (auth) ensureSession().then((s) => {
    if (!s) return;
    syncFavorites();
    progPull().then(() => {
      if (location.hash.startsWith("#/hesabim")) renderHesabim();
    });
  });
  initHeroSearch();
  renderHome();
  mountHeaderWx();
  router();
  onScroll();
})();
