# BDR ve Finansal Tablolar Panosu

Türkiye'de faaliyet gösteren bankaların BDDK Bağımsız Denetim Raporları / finansal tablolar sayfalarına tek tıkla erişim sağlayan, tek dosyalık statik bir HTML panosu.

## Kullanım

`index.html` dosyasını bir tarayıcıda açmanız yeterli. Kurulum, sunucu veya internet bağlantısı gerektirmez (banka logoları dosyanın içine gömülüdür); bankaların rapor sayfalarına giden linkler için internet bağlantısı gerekir.

Canlı repo: [github.com/beligte10/bdr-kisayol](https://github.com/beligte10/bdr-kisayol)

## İçerik ve yapı

Pano dört **sekme** halinde düzenlenmiştir; tek seferde bir sekme görünür, üstteki sekme butonlarına tıklayarak geçiş yapılır:

- **İlk 20 Banka** (20) — mevduat + katılım bankaları arasında aktif büyüklüğe göre ilk 20 banka, **1'den 20'ye numaralandırılmış** olarak. Bu 20 bankanın tamamında Solo/Konsolide butonları son dönem raporunun PDF'ini doğrudan açar.
- **Katılım Bankaları** (3) — ilk 20'ye giremeyenler: Dünya Katılım, Hayat Finans, TOM Bank
- **Mevduat Bankaları** (22) — ilk 20'ye giremeyen mevduat bankaları
- **Kalkınma ve Yatırım Bankaları** (21) — Türk Eximbank, İller Bankası, TSKB, Takasbank, Kalkınma Bankası, Aktif Bank, Nurol Yatırım Bankası, Destek Yatırım Bankası, Golden Global Bank, Q Yatırım Bankası, PashaBank, Tera Bank, D Yatırım Bankası, Misyon Bank, Bank of America Yatırım Bank, Hedef Yatırım Bankası, GSD Yatırım Bankası, BankPozitif, Standard Chartered, Diler Yatırım Bankası, Aytemiz Yatırım Bankası

### "Tüm raporlar" linki

Doğrudan PDF'i olan 25 bankanın kartında, butonların altında geçmiş dönemlere erişim linki bulunur:

- Bankanın sitesinde Solo ve Konsolide raporlar **ayrı sayfalarda** yayımlanıyorsa iki ayrı link gösterilir — *Tüm raporlar: Solo · Konsolide* (6 banka: VakıfBank, Garanti BBVA, Akbank, Yapı Kredi, DenizBank, Kuveyt Türk).
- Tek sayfada yayımlanıyorsa tek link gösterilir — *Tüm raporlar ↗* (19 banka).

### PDF / banka sayfası ayrımı

Her kartın adının altındaki rozet, o bankada butonların ne yapacağını gösterir:

| Rozet | Anlamı |
|---|---|
| Yeşil dönem rozeti (ör. `2026/2Ç`) | Butonlar **doğrudan PDF** açar; rozet raporun dönemini belirtir |
| Gri **"Banka sayfası"** rozeti | Butonlar bankanın kendi rapor sayfasını açar |

Doğrudan PDF'i olan 25 bankanın 20'si "İlk 20 Banka" sekmesinde, kalan 5'i (Dünya Katılım, TSKB, İller Bankası, Türk Eximbank, Şekerbank) kendi gruplarındadır.

Toplam **66 banka** — BDDK'nın [Bağımsız Denetim Raporları portalında](https://www.bddk.org.tr/BdrUyg/) listelenen bankaların tamamı (bkz. aşağıdaki "BDDK entegrasyonu" bölümü). Son eklenenler: Birleşik Fon Bankası, Intesa Sanpaolo, JPMorgan Chase, Türk Ticaret Bankası (Mevduat grubu).

Sıralama, TBB kaynaklı 2025 3. çeyrek (30.09.2025) aktif büyüklük verilerine dayanır (Ağustos 2026 itibarıyla). Turkish Bank, Birleşik Fon Bankası, Intesa Sanpaolo ve JPMorgan Chase için güvenilir büyüklük verisi bulunamadığından bunlar Mevduat Bankaları listesinin sonuna eklenmiştir; Türk Ticaret Bankası için ~65 milyar TL'lik yaklaşık bir değerle (2026 ortası verisinden geri hesaplanan tahmini rakam) sıraya yerleştirilmiştir. Aktif büyüklükler her çeyrek değiştiğinden, sıralamanın periyodik olarak gözden geçirilmesi gerekir.

### Doğrudan PDF linkleri

Aşağıdaki **25 bankada** Solo/Konsolide butonları **son dönem raporunun PDF'ini doğrudan açar** (ara sayfa yok, zip yok). Kart üzerinde hangi döneme ait olduğu rozet olarak yazar (ör. `2026/2Ç`):

| Banka | Dönem | Banka | Dönem |
|---|---|---|---|
| Ziraat Bankası | 2026/1Ç | Kuveyt Türk | 2026/1Ç |
| VakıfBank | 2026/2Ç | Vakıf Katılım | 2026/1Ç |
| İş Bankası | 2026/2Ç | Ziraat Katılım | 2026/1Ç |
| Halkbank | 2026/2Ç | Albaraka | 2026/2Ç |
| Garanti BBVA | 2026/2Ç | Türkiye Finans | 2026/1Ç |
| Akbank | 2026/2Ç | Emlak Katılım | 2026/1Ç |
| Yapı Kredi | 2026/2Ç | Dünya Katılım | 2026/1Ç |
| QNB | 2026/2Ç | TSKB | 2026/2Ç |
| DenizBank | 2026/2Ç | İller Bankası | 2026/1Ç (yalnız Solo) |
| TEB | 2026/2Ç | Türk Eximbank | 2026/2Ç (yalnız Solo) |
| HSBC | 2026/1Ç | Enpara | 2026/2Ç (yalnız Solo) |
| ING | 2026/2Ç | Fibabanka | 2026/1Ç |
| Şekerbank | 2026/2Ç | | |

Bu linklerin tamamı HTTP 200 **ve** dosyanın ilk baytları (`%PDF` imzası) kontrol edilerek doğrulanmıştır.

Kaynak notları:
- **HSBC, QNB, DenizBank** dosyaları `.pdf` yerine `.vsf` uzantısıyla sunulur (aynı CMS); sunucu `application/pdf` döndürür ve içerik gerçek PDF'tir. QNB'de hangi dosyanın solo/konsolide olduğu PDF içeriğinden teyit edilmiştir.
- **İş Bankası ve VakıfBank** kendi sitelerinde raporları yalnızca `.zip` olarak yayımladığı için, resmi **KAP** (Kamuyu Aydınlatma Platformu) doğrudan indirme adresleri kullanılmıştır: `kap.org.tr/tr/api/file/download/{id}`. İş Bankası'nda solo/konsolide eşleşmesi, dosya boyutlarının bağımsız bir KAP yansımasıyla birebir tutması sayesinde çapraz doğrulanmıştır.
- **Şekerbank**'ın kendi sitesindeki 30.06.2026 linkleri hatalı biçimde bir *preprod* (test) sunucusuna işaret ediyor ve dışarıdan açılmıyor; panoda aynı dosyaların üretim (`www`) adresleri kullanılmıştır.

#### En büyük 20 bankada durum

Mevduat + katılım bankaları arasında aktif büyüklüğe göre **ilk 20 bankanın tamamında** (20/20) Solo ve Konsolide butonlarının ikisi de doğrudan PDF açar.

Top-20 dışında **TSKB, İller Bankası, Dünya Katılım, Türk Eximbank ve Şekerbank**'ta da doğrudan PDF vardır — toplam **25 banka**. Takasbank denendi ancak sitesi bot korumasıyla engellediği için eklenemedi; diğer küçük ölçekli bankalarda butonlar bankanın rapor sayfasını açar.

> **Önemli — bakım gerektirir:** Bu PDF adresleri döneme özeldir (içlerinde `31_03_2026` gibi tarihler ve bankaya özel ID'ler geçer) ve tahmin edilebilir bir kalıpları yoktur. Banka yeni çeyrek raporunu yayımladığında link eskiyip **eski çeyreğin PDF'ini göstermeye devam eder**. Bu yüzden çeyrek başlarında (Şubat / Mayıs / Ağustos / Kasım) linklerin yenilenmesi gerekir. Güncelleme sırasında ilgili raporlara [BDDK portalından](https://www.bddk.org.tr/BdrUyg/) veya bankanın kendi sitesinden ulaşılabilir.

### BDDK'nın rolü

Kartların altındaki eski "BDDK Kayıtları" linki kaldırılmıştır. BDDK'nın [Bağımsız Denetim Raporları portalı](https://www.bddk.org.tr/BdrUyg/) yine de bu panonun arka planındaki **referans kaynağıdır**: aşağıdaki solo/konsolide buton mantığı, bankaların kendi siteleri yerine mümkün olduğunca bu resmi BDDK verisiyle çapraz kontrol edilerek belirlenmiştir (Ağustos 2026; 2026 1. ve 2. çeyrek verileri). Bir bankanın tüm geçmiş dönemlerine ulaşmak gerekirse bu portaldan banka bazında sorgulanabilir.

### Arama

Üstteki arama kutusuna banka adı yazıldığında, hangi sekmede olursa olsun eşleşen bankalar (logo ve grup adıyla) açılır bir listede gösterilir. Bir sonuca tıklamak (veya Enter'a basmak) ilgili sekmeye geçer ve **yalnızca o bankanın kartını gösterir**; diğer kartlar gizlenir. Üstte "*&lt;Banka&gt; gösteriliyor — Tümünü göster ✕*" çubuğu çıkar; bu düğmeye veya herhangi bir sekmeye basmak filtreyi temizler.

### Solo / Konsolide butonları

Her banka kartında **Solo** ve (varsa) **Konsolide** butonları bulunur:

- Aşağıdaki 8 bankada bu iki buton, bankanın kendi yatırımcı ilişkileri sitesinde gerçekten ayrı yayımlanan sayfalara gider: **Kuveyt Türk, VakıfBank, Garanti BBVA, Akbank, Yapı Kredi, DenizBank, BankPozitif, Alternatif Bank**.
- Aşağıdaki 29 bankada yalnızca **Solo** butonu gösterilir; BDDK'nın resmi kayıtlarına göre bu bankalar 2026 yılı içinde yalnızca Solo rapor yüklemiştir (Konsolide yüklememiştir): **TOM Bank, Enpara, Turkland Bank, Colendi Bank, Société Générale, Bank Mellat, İller Bankası, PashaBank, Standard Chartered, Diler Yatırım Bankası, Aytemiz Yatırım Bankası, Odeabank, Citibank, MUFG Bank Turkey, Deutsche Bank, Bank of China Turkey, Ziraat Dinamik, Rabobank, Türk Eximbank, Hedef Yatırım Bankası, Bank of America Yatırım Bank, GSD Yatırım Bankası, Takasbank, Misyon Bank, Q Yatırım Bankası, Birleşik Fon Bankası, Intesa Sanpaolo, JPMorgan Chase, Türk Ticaret Bankası**. (Bank Mellat ve Société Générale Türkiye'de ayrı tüzel kişiliği olmayan "merkez şube" statüsünde faaliyet gösterdiğinden yapısal olarak konsolide raporu bulunmaz.)
- Diğer tüm bankalarda (İş Bankası dahil — BDDK kaydında hem Solo hem Konsolide mevcut) Solo ve Konsolide raporlar aynı sayfada (dönem bazlı liste halinde) yayımlandığı için iki buton da aynı sayfayı açar.
- Bu durum yalnızca **2026 1.-2. çeyrek** BDDK verisini yansıtır; bir bankanın konsolide yükümlülüğü (bağlı ortaklık yapısına göre) dönemden döneme değişebilir. Şüpheli bir durumda [BDDK portalından](https://www.bddk.org.tr/BdrUyg/) bankanın tüm geçmişi kontrol edilebilir.
- D Yatırım Bankası ve Turkish Bank'ın kurumsal logoları tamamen beyaz olduğundan (koyu zemin için tasarlanmış), beyaz kart zemininde görünür olmaları için CSS `invert` filtresiyle siyaha çevrilerek gösterilirler.
- Bank Mellat'ın sitesinde kullanılabilir kalitede bir logo bulunamadığından (yalnızca fotoğraflı reklam banner'ı mevcut), kart için sade bir metin logosu oluşturulmuştur. Birleşik Fon Bankası (TMSF bünyesinde tasfiye amaçlı özel bir kredi kuruluşu; genel kullanıma açık bir web sitesi/yatırımcı ilişkileri sayfası yoktur) için de aynı şekilde metin logosu kullanılmış, tek kaynak olarak doğrudan BDDK linki verilmiştir.

### Marka rengi ve logo

Üst başlıkta (topbar) ve etkin sekme rengi olarak Kuveyt Türk Strateji kurumsal yeşili kullanılır: `--navy: #016B4E` (koyu tonu `--navy-dark: #013d2c`). "STRATEJİ" logosu (`stratejilogo.png`'den gömülü) başlığın üstünde yer alır.

## Dosyalar

| Dosya | Açıklama |
|---|---|
| `index.html` | Güncel, kullanılan pano — hem doğrudan açmak hem statik hosting (Vercel/Netlify) için kök dosya |

## GitHub + Netlify / Vercel'de yayınlama

Bu klasör, herhangi bir kurulum/derleme gerektirmeyen statik bir sitedir ve [github.com/beligte10/bdr-kisayol](https://github.com/beligte10/bdr-kisayol) reposunda `main` branch'inde tutulur.

**Netlify:** Yeni site oluştururken bu repoyu seçin; Base directory, Build command, Publish directory, Functions directory alanlarının hepsini **boş** bırakın (derleme yok, `index.html` kökte). Branch olarak `main` yeterlidir.

**Vercel:** [vercel.com](https://vercel.com) üzerinden "Add New… → Project" ile bu GitHub reposunu (veya klasörü sürükle-bırak ile) içe aktarın; Vercel `index.html`'i otomatik olarak kök adreste (`/`) yayınlar.

Değişiklik yaptıktan sonra GitHub'a push edildiğinde her iki servis de otomatik olarak yeniden yayınlar (auto-deploy).

## Güncelleme

Yeni bir banka eklemek veya bir linki güncellemek için `index.html` içindeki ilgili `<div class="card ...">` bloğunu düzenlemeniz yeterlidir. Bankaların rapor URL'leri zaman zaman değişebildiğinden, linklerin periyodik olarak (örn. çeyreklik) kontrol edilmesi önerilir.

Son kapsamlı güncelleme: Ağustos 2026.
