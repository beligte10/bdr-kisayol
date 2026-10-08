# BDR ve Finansal Tablolar Panosu

Türkiye'de faaliyet gösteren bankaların BDDK Bağımsız Denetim Raporları / finansal tablolar sayfalarına tek tıkla erişim sağlayan, tek dosyalık statik bir HTML panosu.

## Kullanım

`index.html` dosyasını bir tarayıcıda açmanız yeterli. Kurulum, sunucu veya internet bağlantısı gerektirmez (banka logoları dosyanın içine gömülüdür); bankaların rapor sayfalarına giden linkler için internet bağlantısı gerekir.

Canlı repo: [github.com/beligte10/bdr-kisayol](https://github.com/beligte10/bdr-kisayol)

## İçerik ve yapı

Pano dört **sekme** halinde düzenlenmiştir; tek seferde bir sekme görünür, üstteki sekme butonlarına tıklayarak geçiş yapılır:

- **İlk 20 Banka** (20) — mevduat + katılım bankaları arasında aktif büyüklüğe göre ilk 20 banka, **1'den 20'ye numaralandırılmış** olarak. Bu 20 bankanın tamamında Solo/Konsolide butonları son dönem raporunun PDF'ini doğrudan açar.
- **Katılım Bankaları** (9) — katılım bankalarının tamamı, aktif büyüklük sırasıyla
- **Mevduat Bankaları** (36) — mevduat bankalarının tamamı, aktif büyüklük sırasıyla
- **Kalkınma ve Yatırım Bankaları** (21) — Türk Eximbank, İller Bankası, TSKB, Takasbank, Kalkınma Bankası, Aktif Bank, Nurol Yatırım Bankası, Destek Yatırım Bankası, Golden Global Bank, Q Yatırım Bankası, PashaBank, Tera Bank, D Yatırım Bankası, Misyon Bank, Bank of America Yatırım Bank, Hedef Yatırım Bankası, GSD Yatırım Bankası, BankPozitif, Standard Chartered, Diler Yatırım Bankası, Aytemiz Yatırım Bankası

İlk 20'de yer alan bankalar **kendi kategori sekmelerinde de** gösterilir; yani "İlk 20 Banka" sekmesi bir kısayol/özet niteliğindedir. Bu nedenle toplam kart sayısı 86'dır (66 benzersiz banka, 20'si iki sekmede birden). Aramada her banka **yalnızca bir kez** listelenir.

### "Tüm raporlar" linki

Her kartta, butonların altında geçmiş dönemlere erişim linki bulunur:

- Bankanın sitesinde Solo ve Konsolide raporlar **ayrı sayfalarda** yayımlanıyorsa iki ayrı link gösterilir — *Tüm raporlar: Solo · Konsolide* (6 banka: VakıfBank, Garanti BBVA, Akbank, Yapı Kredi, DenizBank, Kuveyt Türk).
- Tek sayfada yayımlanıyorsa tek link gösterilir — *Tüm raporlar ↗*.

### Solo / Konsolide butonları

**66 bankanın tamamında** Solo ve Konsolide butonları son dönem raporunun **PDF'ini doğrudan açar** (ara sayfa yok, zip yok). Kart adının altındaki yeşil rozet (ör. `2026/2Ç`) o PDF'in dönemini belirtir. Butonların tamamı (102 adet) HTTP isteğiyle ve `%PDF` imzası kontrol edilerek doğrulanmıştır.

PDF'lerin kaynağı iki türlüdür:

| Kaynak | Banka sayısı | Açıklama |
|---|---|---|
| Bankanın kendi sitesi | 43 | Butonlar bankanın yayımladığı PDF adresine gider; banka yeni rapor yayımladığında link eskir, dönemsel güncelleme gerekir |
| Depoda barındırılan BDDK kopyası (`raporlar/`) | 23 | BDDK'dan indirilip depoya konulmuştur; site tarafında sabit PDF adresi bulunamayan bankalar için |

İkinci grup, raporları JavaScript ile yükleyen, bot koruması olan veya dosya adları dönem bilgisi taşımayan bankalardır: Hayat Finans, Burgan Bank, Odeabank, Citibank, MUFG Bank Turkey, Türk Ticaret Bankası, Arap Türk Bankası, Bank Mellat, Société Générale, JPMorgan Chase, Intesa Sanpaolo, Birleşik Fon Bankası, Turkish Bank, Takasbank, Kalkınma Bankası, Golden Global Bank, Misyon Bank, GSD Yatırım Bankası, BankPozitif — ayrıca Anadolubank, ICBC Turkey, Aktif Bank ve Tera Bank'ın yalnızca Konsolide raporları.

**Tek butonlu kartlar (17 banka):** BDDK'nın resmi kayıtlarına göre bu bankalar konsolide rapor yüklememiştir (çoğu bağlı ortaklığı olmayan, ayrı tüzel kişiliği olmayan "merkez şube" statüsündeki kuruluşlardır), bu yüzden yalnızca Solo butonu gösterilir: TOM Bank, Enpara, Turkland Bank, Colendi Bank, Société Générale, Bank Mellat, İller Bankası, PashaBank, Standard Chartered, Diler Yatırım Bankası, Aytemiz Yatırım Bankası, Odeabank, Citibank, MUFG Bank Turkey, Deutsche Bank, Bank of China Turkey, Ziraat Dinamik, Rabobank, Türk Eximbank, Hedef Yatırım Bankası, Bank of America Yatırım Bank, GSD Yatırım Bankası, Takasbank, Misyon Bank, Q Yatırım Bankası, Birleşik Fon Bankası, Intesa Sanpaolo, JPMorgan Chase, Türk Ticaret Bankası.

Bu durum yalnızca **2026 1.-2. çeyrek** BDDK verisini yansıtır; bir bankanın konsolide yükümlülüğü (bağlı ortaklık yapısına göre) dönemden döneme değişebilir. Şüpheli bir durumda [BDDK portalından](https://www.bddk.org.tr/BdrUyg/) bankanın tüm geçmişi kontrol edilebilir.

**"2Ç bekleniyor" rozeti:** Bir bankanın en son PDF'i henüz 2026/2Ç (Haziran 2026) dönemine ait değilse (yani banka bu çeyreğin raporunu henüz yayımlamamışsa), rozetin yanında ⏳ **"2Ç bekleniyor"** ibaresi gösterilir. Bu bir hata değildir — banka raporunu yayımladığında link güncellenip rozet kalkar.

**Logo notları:**
- D Yatırım Bankası ve Turkish Bank'ın kurumsal logoları tamamen beyaz olduğundan (koyu zemin için tasarlanmış), beyaz kart zemininde görünür olmaları için CSS `invert` filtresiyle siyaha çevrilerek gösterilirler.
- Bank Mellat'ın sitesinde kullanılabilir kalitede bir logo bulunamadığından (yalnızca fotoğraflı reklam banner'ı mevcut), kart için sade bir metin logosu oluşturulmuştur. Birleşik Fon Bankası (TMSF bünyesinde tasfiye amaçlı özel bir kredi kuruluşu; genel kullanıma açık bir web sitesi/yatırımcı ilişkileri sayfası yoktur) için de aynı şekilde metin logosu kullanılmış, tek kaynak olarak doğrudan BDDK linki verilmiştir.
- Tüm banka logoları dosyanın içine gömülüdür (base64); hiçbiri sayfa açılırken dış bir servisten (ör. Google favicon) çekilmez, bu yüzden kurumsal ağ/cihaz kısıtlamalarından etkilenmezler.

**Güncelleme:** Yeni çeyrek yayımlandığında `BDR-Arsiv/bdr_indir.py --yil <yıl> --bankalar "<banka adları>"` çalıştırılıp yeni PDF'ler `raporlar/` altına kopyalanmalı ve `index.html` içindeki yollar güncellenmelidir.

> **Önemli — bakım gerektirir:** Kendi sitesinden çekilen 43 bankanın PDF adresleri döneme özeldir (içlerinde `31_03_2026` gibi tarihler ve bankaya özel ID'ler geçer) ve tahmin edilebilir bir kalıpları yoktur. Banka yeni çeyrek raporunu yayımladığında link eskiyip **eski çeyreğin PDF'ini göstermeye devam eder**. Bu yüzden çeyrek başlarında (Şubat / Mayıs / Ağustos / Kasım) linklerin yenilenmesi gerekir. Güncelleme sırasında ilgili raporlara [BDDK portalından](https://www.bddk.org.tr/BdrUyg/) veya bankanın kendi sitesinden ulaşılabilir.

### Arşiv scripti (`bakim/bdr_indir.py`)

BDDK'nın düzenli dosya adı kalıbını (`BDREki-{bankakodu}-{SOLO|KONSOLIDE}-{yıl}-{ay}.zip`) kullanarak seçilen dönemlerin tüm raporlarını indirir, zip içinden PDF'i çıkarır ve `raporlar/<yıl>-<çeyrek>/<banka>-<tip>.pdf` şeklinde diziler; ayrıca `manifest.json` üretir. 66 bankanın BDDK kodları script içinde gömülüdür. Yeniden çalıştırıldığında mevcut dosyaları atlar (kesintiden devam eder) ve BDDK'yı yormamak için istekler arasında bekler.

```bash
python3 bdr_indir.py --yil 2026                  # tek yıl, tüm bankalar
python3 bdr_indir.py --yil 2022 2023 2024 2025 2026
python3 bdr_indir.py --yil 2026 --sadece-ilk20   # yalnız ilk 20 banka
python3 bdr_indir.py --yil 2026 --bankalar "Takasbank" "Odeabank"   # seçili bankalar
```

Ölçülen boyutlar: ortalama ~2,3 MB/PDF. Bu boyutlar GitHub deposu için uygun değildir (GitHub 1 GB üzerini önermez), bu yüzden arşiv **Cloudflare R2**'de barındırılır (10 GB ücretsiz, indirme trafiği ücretsiz). Panoda kullanılan son dönem PDF'leri (23 banka, ~62 MB) ayrıca `raporlar/` klasöründe depoda tutulur — bu boyut GitHub için sorun değildir.

### Geçmiş dönem arşivi (R2)

Yayımdaki kapsam **kayan bir penceredir: son 10 takvim yılı.** Şu an **2017-1Ç – 2026-2Ç**, 38 dönem, 66 banka. Diskteki `BDR-Arsiv/raporlar/` klasörü 2005'e kadar iner ve hiç budanmaz; siteye yalnızca pencere içindeki dönemler yüklenir. Pencere sabit bir başlangıç yılına değil, arşivdeki en yeni döneme bağlıdır — yeni çeyrek eklendiğinde en eski yıl kendiliğinden düşer, böylece site elle güncellenmeden hep son 10 yılı gösterir ve R2 ücretsiz kotası (10 GB) aşılmaz.

Pencere genişliği `manifest_uret.py` içindeki `PENCERE_YIL` sabitiyle belirlenir; `index.html`'deki yıl seçicisi de sabit liste değil, gömülü manifestten üretilir, dolayısıyla ayrıca güncellenmesi gerekmez.

Dosyaların çoğu PDF'tir; 130 kayıt BDDK arşivinde `.docx`/`.xls`/`.tif` gibi başka formatlardadır ve olduğu gibi sunulur.

R2 nesneleri `*.r2.dev` üzerinden değil, bir **Cloudflare Worker** (`bdr-arsiv.bdr-arsiv-worker.workers.dev`) üzerinden servis edilir; `*.r2.dev` alan adları kurumsal ağda TLS el sıkışmasında engelleniyor.

### Otomatik güncelleme (GitHub Actions)

`.github/workflows/bdr-otomatik.yml` iki katmanlı çalışır. Takvim: raporların yayımlandığı aylarda (Şubat/Mayıs/Ağustos/Kasım) her gün 09:00 TR, diğer aylarda pazartesileri. `workflow_dispatch` ile elle de tetiklenebilir (`kuru: true` hiçbir şey yazmadan denemek için).

**Katman 1 — BDDK arşivi (tam otomatik).** `otomatik_tara.py` R2'deki en yeni dönemi ve onu izleyen iki çeyreği tarar; yayımlanmış ama R2'de olmayan her raporu indirip yükler. Ardından manifest R2 listesinden üretilir, `index.html`'e gömülür, `kart_ilerlet.py` R2'ye bakan kart butonlarını yeni döneme taşır ve doğrulama çalışır. Doğrulama geçerse commit + push edilir, Netlify kendiliğinden yayına alır. Bu katman deterministiktir: kaynak BDDK'nın kendi arşivi, dosya adı kalıbı sabit, her belge içerik olarak doğrulanıyor.

**Katman 2 — Banka siteleri (erken yakalama).** BDDK, bankaların kendi sitelerinden günler hatta haftalar geç yayımlıyor. `banka_tara.py` bu aralığı kapatır. İki yöntem dener: (a) elde duran linkten bir sonraki çeyreğin adresini türetir (`..._30.06.2026.pdf` → `..._30.09.2026.pdf`) — buradaki Solo/Konsolide bilgisi butonun kendi etiketinden geldiği için kesindir; (b) rapor sayfasını tarar. Her aday HTTP durumu, content-type ve `%PDF` baytıyla doğrulanır.

Bulunan rapor **indirilir**, sonra tipine göre ayrışır:

- **Solo/Konsolide ayrımı etiketten kesin okunabiliyorsa** dosya `raporlar/<dönem>/<slug>-<tip>.pdf` olarak R2'ye yüklenir; manifest yenilenir, pano güncellenir, doğrulama geçerse commit edilir.
- **Okunamıyorsa** dosya `karantina/` altına konur, siteye **girmez** ve issue ile bildirilir.

Ayrım şu kurala göre yapılır: Türk bankacılığında *"Konsolide Olmayan Finansal Rapor"* **solo** demektir; metinde `konsolide` geçiyor diye konsolide saymak bu işin klasik hatasıdır ve panoda bir kez yaşandı. Sınıflandırıcı önce olumsuzlamayı arar, okuyamazsa bilerek `None` döner — yanlış tip, eksik tipten kötüdür.

Banka sitesinden gelen kopyalar `kaynak_banka.json` içinde işaretlenir. `otomatik_tara.py` bu anahtarları "zaten var" diye atlamaz; BDDK aynı raporu yayımlayınca kendi kopyasıyla değiştirir, böylece arşivin gövdesi tek kaynaklı kalır.

Ölçülen kapsam: bilinen-yayımda bir çeyrekte 66 bankanın 28'inde toplam 49 rapor bulundu; 38'inin tipi kesin, 11'i karantinaya düştü. Kapsam sınırlıdır (çoğu rapor sayfası JavaScript ile üretiliyor), ama eksiksizliği Katman 1 garanti eder — bu katman yalnızca **erkenlik** kazandırır.

**Gereken GitHub Secrets:** `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT`. rclone bulutta dosya yerine ortam değişkenleriyle yapılandırılır; kimlik bilgileri diske yazılmaz.

**Çeyreklik bakım — elle, tek komut:**

```bash
python3 bakim/ceyrek_guncelle.py --yil 2026            # ne olacağını göster
python3 bakim/ceyrek_guncelle.py --yil 2026 --uygula   # uygula
```

Sırasıyla: BDDK'dan indirir → R2'yi pencereyle eşitler → manifesti üretir → **`index.html`'e gömer** → doğrular (div dengesi, sabit yıl seçeneği kalmamış mı, 3.166 arşiv linkinin R2 karşılığı, 26 doğrudan linkin açılıp açılmadığı). Doğrulama düşerse commit önerilmez. Manifesti elle kopyalayıp yapıştırma adımı sistemdeki en hata açık yerdi; 4. adım onu ortadan kaldırır.

Alt scriptler ayrı ayrı da çalıştırılabilir (`bakim/bdr_indir.py`, `bakim/r2_esitle.py`, `bakim/manifest_uret.py`). `r2_esitle.py` iki yönde de çalışır: pencere içinde olup R2'de bulunmayan dönemleri yükler, pencereden düşmüş dönemleri R2'den siler (yerel kopyalar korunur). Silme geri alınamaz olduğu için `--uygula` verilmedikçe yalnızca planı yazdırır. `rclone` çağrılarında `--s3-no-check-bucket` gerekir; API token'ı yalnızca bu bucket'a yetkili olduğundan bucket varlık kontrolü 403 döner.

Üretilen JSON, `index.html` içindeki `<script type="application/json" id="arsivManifest">` bloğuna gömülür (`ceyrek_guncelle.py` bunu kendisi yapar). Yol tekrarını önlemek için sıkıştırılmış biçimdedir: yol `<dönem>/<banka-slug>-<tip>.<uzantı>` kalıbından türetilir, yalnızca hangi tiplerin bulunduğu (`s`/`k`) ve PDF olmayan istisnalar saklanır (46 KB).

Bilinen boşluklar: HSBC 2008-4Ç / 2020-3Ç ve Bank of America 2016-1Ç arşivleri Deflate64 ile sıkıştırılmıştır (Python `zipfile`, `unzip` ve `ditto` desteklemez); BankPozitif 2025-4Ç dosyası BDDK tarafında bozuk CRC ile gelmektedir.

Toplam **66 banka** — BDDK'nın [Bağımsız Denetim Raporları portalında](https://www.bddk.org.tr/BdrUyg/) listelenen bankaların tamamı.

### Sıralama

Sıralama, TBB kaynaklı 2025 3. çeyrek (30.09.2025) aktif büyüklük verilerine dayanır (Ağustos 2026 itibarıyla). Turkish Bank, Birleşik Fon Bankası, Intesa Sanpaolo ve JPMorgan Chase için güvenilir büyüklük verisi bulunamadığından bunlar Mevduat Bankaları listesinin sonuna eklenmiştir; Türk Ticaret Bankası için ~65 milyar TL'lik yaklaşık bir değerle (2026 ortası verisinden geri hesaplanan tahmini rakam) sıraya yerleştirilmiştir. Aktif büyüklükler her çeyrek değiştiğinden, sıralamanın periyodik olarak gözden geçirilmesi gerekir.

### BDDK'nın rolü

Kartların altındaki eski "BDDK Kayıtları" linki kaldırılmıştır. BDDK'nın [Bağımsız Denetim Raporları portalı](https://www.bddk.org.tr/BdrUyg/) yine de bu panonun arka planındaki **referans kaynağıdır**: solo/konsolide buton mantığı, bankaların kendi siteleri yerine mümkün olduğunca bu resmi BDDK verisiyle çapraz kontrol edilerek belirlenmiştir (Ağustos 2026; 2026 1. ve 2. çeyrek verileri). Bir bankanın tüm geçmiş dönemlerine ulaşmak gerekirse bu portaldan banka bazında sorgulanabilir.

Kaynak notları:
- **HSBC, QNB, DenizBank** dosyaları `.pdf` yerine `.vsf` uzantısıyla sunulur (aynı CMS); sunucu `application/pdf` döndürür ve içerik gerçek PDF'tir. QNB'de hangi dosyanın solo/konsolide olduğu PDF içeriğinden teyit edilmiştir.
- **İş Bankası ve VakıfBank** kendi sitelerinde raporları yalnızca `.zip` olarak yayımladığı için, resmi **KAP** (Kamuyu Aydınlatma Platformu) doğrudan indirme adresleri kullanılmıştır: `kap.org.tr/tr/api/file/download/{id}`. İş Bankası'nda solo/konsolide eşleşmesi, dosya boyutlarının bağımsız bir KAP yansımasıyla birebir tutması sayesinde çapraz doğrulanmıştır.
- **Şekerbank**'ın kendi sitesindeki 30.06.2026 linkleri hatalı biçimde bir *preprod* (test) sunucusuna işaret ediyor ve dışarıdan açılmıyor; panoda aynı dosyaların üretim (`www`) adresleri kullanılmıştır.

### Arama

Üstteki arama kutusuna banka adı yazıldığında, hangi sekmede olursa olsun eşleşen bankalar (logo ve grup adıyla) açılır bir listede gösterilir. Bir sonuca tıklamak (veya Enter'a basmak) ilgili sekmeye geçer ve **yalnızca o bankanın kartını gösterir**; diğer kartlar gizlenir. Üstte "*&lt;Banka&gt; gösteriliyor — Tümünü göster ✕*" çubuğu çıkar; bu düğmeye veya herhangi bir sekmeye basmak filtreyi temizler.

### Tema ve görsel dil

Arayüz, Kuveyt Türk **Rakip Analizi** panosunun (KT Strategic Cockpit) görsel diline göre düzenlenmiştir: marka yeşili `--navy: #62AE41` (koyusu `--navy-dark: #457A2E`, açığı `#A1CE8D`), `#e8eef1` zemin, beyaz paneller üzerinde `#d4dde3` ince kenarlık ve 6 px köşe, 60 px düz üst çubuk, segment (hap) biçiminde sekme kontrolü. Üst çubukta **TEMA** düğmesiyle açık/koyu mod değiştirilir; sayfa her zaman açık temayla başlar; kullanıcı koyu moda geçerse seçim tarayıcıda (`localStorage`) saklanır. "STRATEJİ" logosu (`stratejilogo.png`'den gömülü) üst çubuktadır.

Sekmelerin üstündeki **kapsam şeridi** dört grubun banka sayısını ve güncel dönem rozeti taşıyan kartların oranını çubukla gösterir (açık renk bölüm "2Ç bekleniyor" olanlardır); karta tıklamak ilgili sekmeye geçirir. Değerler sayfa açılırken kartlardan hesaplanır, elle güncelleme gerekmez.

## Dosyalar

| Dosya | Açıklama |
|---|---|
| `index.html` | Panonun tamamı — HTML, CSS, JS, logolar ve arşiv manifesti tek dosyada (~1,2 MB) |
| `.github/workflows/bdr-otomatik.yml` | Otomatik güncelleme akışı (takvimli) |
| `bakim/ceyrek_guncelle.py` | Bakımın tek komutu; `--otomatik` bulut modu, `--yil` elle mod |
| `bakim/otomatik_tara.py` | BDDK'da yeni rapor arar, doğrudan R2'ye yazar (yerel disk gerekmez) |
| `bakim/banka_tara.py` | Banka sitelerinde erken yayım arar; tipi kesinse arşive, değilse karantinaya koyar |
| `bakim/kart_ilerlet.py` | R2'ye bakan kart butonlarını yeni döneme taşır |
| `bakim/bdr_indir.py` | BDDK arşiv indiricisi |
| `bakim/r2_esitle.py` | R2'yi kayan pencereyle eşitler |
| `bakim/manifest_uret.py` | Sıkıştırılmış manifesti üretir; `PENCERE_YIL` burada |
| `bakim/ayarlar.py` | Ortak yollar; arşivin diskteki yerini `BDR_ARSIV` ile değiştirebilirsiniz |
| `worker/` | R2 nesnelerini servis eden Cloudflare Worker (`wrangler deploy`) |
| `stratejilogo.png` | Başlıktaki logonun kaynağı (sayfaya base64 gömülü) |

Rapor PDF'leri depoda tutulmaz; tamamı R2'den servis edilir. 15 GB'lık ham arşiv `~/Desktop/BDR-Arsiv/raporlar/` altındadır ve `.gitignore` ile dışarıda bırakılmıştır.

**Logolar:** 87 kart görselinin 67'si benzersizdir ("İlk 20 Banka" sekmesi 20 kartı tekrarlar). Her görsel `#logoHarita` JSON bloğunda bir kez saklanır, `<img data-lg="...">` etiketlerine çalışma anında bağlanır. Tekilleştirme + kayıpsız PNG yeniden sıkıştırma dosyayı 1.747 KB'dan 1.200 KB'a indirdi; görseller piksel piksel aynıdır.

## GitHub + Netlify / Vercel'de yayınlama

Bu klasör, herhangi bir kurulum/derleme gerektirmeyen statik bir sitedir ve [github.com/beligte10/bdr-kisayol](https://github.com/beligte10/bdr-kisayol) reposunda `main` branch'inde tutulur.

**Netlify:** Yeni site oluştururken bu repoyu seçin; Base directory, Build command, Publish directory, Functions directory alanlarının hepsini **boş** bırakın (derleme yok, `index.html` kökte). Branch olarak `main` yeterlidir.

**Vercel:** [vercel.com](https://vercel.com) üzerinden "Add New… → Project" ile bu GitHub reposunu (veya klasörü sürükle-bırak ile) içe aktarın; Vercel `index.html`'i otomatik olarak kök adreste (`/`) yayınlar.

Değişiklik yaptıktan sonra GitHub'a push edildiğinde her iki servis de otomatik olarak yeniden yayınlar (auto-deploy).

## Güncelleme

Yeni bir banka eklemek veya bir linki güncellemek için `index.html` içindeki ilgili `<div class="card ...">` bloğunu düzenlemeniz yeterlidir. Bankaların rapor URL'leri zaman zaman değişebildiğinden, linklerin periyodik olarak (örn. çeyreklik) kontrol edilmesi önerilir.

Son kapsamlı güncelleme: Ağustos 2026.
