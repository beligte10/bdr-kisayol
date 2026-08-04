# BDR ve Finansal Tablolar Panosu

Türkiye'de faaliyet gösteren bankaların BDDK Bağımsız Denetim Raporları / finansal tablolar sayfalarına tek tıkla erişim sağlayan, tek dosyalık statik bir HTML panosu.

## Kullanım

`BDR Kısayol.html` dosyasını bir tarayıcıda açmanız yeterli. Kurulum, sunucu veya internet bağlantısı gerektirmez (banka logoları dosyanın içine gömülüdür); bankaların rapor sayfalarına giden linkler için internet bağlantısı gerekir.

## İçerik ve yapı

Pano üç gruba ayrılmıştır; her grup içinde bankalar **aktif büyüklüklerine göre (büyükten küçüğe)** sıralanmıştır:

- **Katılım Bankaları** (9) — Kuveyt Türk (Bankamız, panoda vurgulanmıştır), Vakıf Katılım, Ziraat Katılım, Albaraka, Türkiye Finans, Emlak Katılım, Dünya Katılım, Hayat Finans, TOM Bank
- **Mevduat Bankaları** (22) — kamu, özel, yabancı sermayeli ve dijital mevduat bankalarının tamamı, Ziraat Bankası'ndan Turkish Bank'a kadar
- **Kalkınma ve Yatırım Bankaları** (20) — Türk Eximbank, TSKB, Takasbank, Kalkınma Bankası, Aktif Bank, Nurol Yatırım Bankası, Destek Yatırım Bankası, Golden Global Bank, Q Yatırım Bankası, PashaBank, Tera Bank, D Yatırım Bankası, Misyon Bank, Bank of America Yatırım Bank, Hedef Yatırım Bankası, GSD Yatırım Bankası, BankPozitif, Standard Chartered, Diler Yatırım Bankası, Aytemiz Yatırım Bankası
  - BDDK'nın resmi 21 kalkınma/yatırım bankası listesinde yalnızca **İller Bankası** eksik (henüz link sağlanmadı).

Sıralama, TBB kaynaklı 2025 3. çeyrek (30.09.2025) aktif büyüklük verilerine dayanır (Ağustos 2026 itibarıyla); sonradan eklenen Turkish Bank için ayrıca bir büyüklük sıralaması yapılmamış, Mevduat Bankaları listesinin sonuna eklenmiştir. Aktif büyüklükler her çeyrek değiştiğinden, sıralamanın periyodik olarak gözden geçirilmesi gerekir.

Her banka kartında **Solo** ve **Konsolide** butonları bulunur:

- Aşağıdaki 7 bankada bu iki buton, bankanın kendi yatırımcı ilişkileri sitesinde gerçekten ayrı yayımlanan sayfalara gider: **Kuveyt Türk, VakıfBank, Garanti BBVA, Akbank, Yapı Kredi, DenizBank, BankPozitif**.
- Diğer tüm bankalarda Solo ve Konsolide raporlar aynı sayfada (dönem bazlı liste halinde) yayımlandığı için iki buton da aynı sayfayı açar.
- D Yatırım Bankası ve Turkish Bank'ın kurumsal logoları tamamen beyaz olduğundan (koyu zemin için tasarlanmış), beyaz kart zemininde görünür olmaları için CSS `invert` filtresiyle siyaha çevrilerek gösterilirler.

## Dosyalar

| Dosya | Açıklama |
|---|---|
| `BDR Kısayol.html` | Güncel, kullanılan pano |
| `index.html` | `BDR Kısayol.html` ile birebir aynı içerik; Vercel gibi statik hosting servisleri kök adrese (`/`) bu dosyayı otomatik sunduğu için eklenmiştir — her güncellemede `BDR Kısayol.html` ile senkron tutulmalıdır |

## Vercel'de yayınlama

Bu klasör, herhangi bir kurulum/derleme gerektirmeyen statik bir sitedir.

1. [vercel.com](https://vercel.com) üzerinden bir hesap açın/giriş yapın.
2. "Add New… → Project" deyip bu klasörü (`BDR Kısayol`) sürükle-bırak ile yükleyin (Git deposu gerekmez).
3. Vercel otomatik olarak `index.html` dosyasını kök adreste (`/`) yayınlar; birkaç saniye içinde size özel bir URL verir (ör. `bdr-kisayol.vercel.app`).
4. `BDR Kısayol.html` içinde bir değişiklik yaptığınızda, aynı değişikliği `index.html`'e de yansıtıp (veya dosyayı yeniden kopyalayıp) projeyi tekrar yükleyerek güncelleyebilirsiniz.

Alternatif olarak, bilgisayarınızda Node.js kuruluysa Vercel CLI ile de yayınlayabilirsiniz:

```bash
npx vercel
```

komutunu bu klasörün içinde çalıştırıp ekrandaki adımları (giriş yapma, proje adı vb.) takip etmeniz yeterlidir. Sonraki güncellemeler için `npx vercel --prod` komutu kullanılır.

## Güncelleme

Yeni bir banka eklemek veya bir linki güncellemek için `BDR Kısayol.html` içindeki ilgili `<div class="card ...">` bloğunu düzenlemeniz yeterlidir. Bankaların rapor URL'leri zaman zaman değişebildiğinden, linklerin periyodik olarak (örn. çeyreklik) kontrol edilmesi önerilir.

Son kapsamlı güncelleme: Ağustos 2026.
