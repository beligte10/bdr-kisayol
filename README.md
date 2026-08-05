# BDR ve Finansal Tablolar Panosu

Türkiye'de faaliyet gösteren bankaların BDDK Bağımsız Denetim Raporları / finansal tablolar sayfalarına tek tıkla erişim sağlayan, tek dosyalık statik bir HTML panosu.

## Kullanım

`index.html` dosyasını bir tarayıcıda açmanız yeterli. Kurulum, sunucu veya internet bağlantısı gerektirmez (banka logoları dosyanın içine gömülüdür); bankaların rapor sayfalarına giden linkler için internet bağlantısı gerekir.

Canlı repo: [github.com/beligte10/bdr-kisayol](https://github.com/beligte10/bdr-kisayol)

## İçerik ve yapı

Pano üç **sekme** halinde düzenlenmiştir (Katılım / Mevduat / Kalkınma ve Yatırım Bankaları); tek seferde bir sekme görünür, üstteki sekme butonlarına tıklayarak geçiş yapılır. Her sekme içinde bankalar **aktif büyüklüklerine göre (büyükten küçüğe)** sıralanmıştır:

- **Katılım Bankaları** (9) — Kuveyt Türk (Bankamız, panoda vurgulanmıştır), Vakıf Katılım, Ziraat Katılım, Albaraka, Türkiye Finans, Emlak Katılım, Dünya Katılım, Hayat Finans, TOM Bank
- **Mevduat Bankaları** (32) — kamu, özel, yabancı sermayeli ve dijital mevduat bankalarının tamamı, Ziraat Bankası'ndan Turkish Bank'a kadar
- **Kalkınma ve Yatırım Bankaları** (21) — Türk Eximbank, İller Bankası, TSKB, Takasbank, Kalkınma Bankası, Aktif Bank, Nurol Yatırım Bankası, Destek Yatırım Bankası, Golden Global Bank, Q Yatırım Bankası, PashaBank, Tera Bank, D Yatırım Bankası, Misyon Bank, Bank of America Yatırım Bank, Hedef Yatırım Bankası, GSD Yatırım Bankası, BankPozitif, Standard Chartered, Diler Yatırım Bankası, Aytemiz Yatırım Bankası

BDDK'nın resmi 21 kalkınma/yatırım bankası listesinin tamamı bu grupta yer almaktadır. Mevduat Bankaları grubunda ise BDDK'nın 36 bankalık resmi listesine göre 4 banka henüz eksiktir (FUPS Bank, Intesa Sanpaolo, JPMorgan Chase, Türk Ticaret Bankası).

Sıralama, TBB kaynaklı 2025 3. çeyrek (30.09.2025) aktif büyüklük verilerine dayanır (Ağustos 2026 itibarıyla); sonradan eklenen Turkish Bank için ayrıca bir büyüklük sıralaması yapılmamış, Mevduat Bankaları listesinin sonuna eklenmiştir. Aktif büyüklükler her çeyrek değiştiğinden, sıralamanın periyodik olarak gözden geçirilmesi gerekir.

### Arama

Üstteki arama kutusuna banka adı yazıldığında, hangi sekmede olursa olsun eşleşen bankalar (logo ve grup adıyla) açılır bir listede gösterilir. Bir sonuca tıklamak (veya Enter'a basmak) ilgili sekmeye otomatik geçer, o bankanın kartına kaydırır ve kartı kısa süreliğine altın rengiyle vurgular.

### Solo / Konsolide butonları

Her banka kartında **Solo** ve (varsa) **Konsolide** butonları bulunur:

- Aşağıdaki 8 bankada bu iki buton, bankanın kendi yatırımcı ilişkileri sitesinde gerçekten ayrı yayımlanan sayfalara gider: **Kuveyt Türk, VakıfBank, Garanti BBVA, Akbank, Yapı Kredi, DenizBank, BankPozitif, Alternatif Bank**.
- Aşağıdaki 21 bankada yalnızca **Solo** butonu gösterilir; bu bankaların sitelerinde ayrı bir Konsolide raporu yayımlanmadığı doğrulanmıştır: **TOM Bank, Enpara, Turkland Bank, Colendi Bank, Société Générale, Bank Mellat, İller Bankası, PashaBank, Standard Chartered, Diler Yatırım Bankası, Aytemiz Yatırım Bankası, Anadolubank, Odeabank, Citibank, MUFG Bank Turkey, Deutsche Bank, Bank of China Turkey, Ziraat Dinamik, Rabobank, Türk Eximbank, Hedef Yatırım Bankası**. (Bank Mellat ve Société Générale Türkiye'de ayrı tüzel kişiliği olmayan "merkez şube" statüsünde faaliyet gösterdiğinden yapısal olarak konsolide raporu bulunmaz.)
- Diğer tüm bankalarda Solo ve Konsolide raporlar aynı sayfada (dönem bazlı liste halinde) yayımlandığı için iki buton da aynı sayfayı açar. Kalan birkaç banka için (İş Bankası, Takasbank, Golden Global Bank, Misyon Bank, GSD Yatırım Bankası) sonuç hâlâ belirsizdi — büyük/orta ölçekli olup muhtemelen konsolide raporu da bulunduğundan Konsolide butonu temkinli biçimde korunmuştur; kesinleşirse güncellenmelidir.
- D Yatırım Bankası ve Turkish Bank'ın kurumsal logoları tamamen beyaz olduğundan (koyu zemin için tasarlanmış), beyaz kart zemininde görünür olmaları için CSS `invert` filtresiyle siyaha çevrilerek gösterilirler.
- Bank Mellat'ın sitesinde kullanılabilir kalitede bir logo bulunamadığından (yalnızca fotoğraflı reklam banner'ı mevcut), kart için sade bir metin logosu ("Bank Mellat") oluşturulmuştur.

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
