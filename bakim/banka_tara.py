#!/usr/bin/env python3
"""Bankaların kendi sitelerinde yeni yayımlanan BDR'leri arar ve rapor eder.

BDDK, bankaların kendi sitelerinden günler hatta haftalar geç yayımlıyor. Bu
script panodaki her kartın gösterdiği dönemi bankanın rapor sayfasıyla
karşılaştırır ve daha yeni bir dönem yayımlanmışsa bildirir.

Bilerek hiçbir dosyayı değiştirmez. Geçmişte bu eşleştirme iki tür hata verdi:
Vakıf Katılım'da Solo/Konsolide etiketleri karıştı, ICBC ve Turkland'da site
HTTP 200 ile HTML hata sayfası döndürdü. Bu yüzden aday linkler yalnızca
"görüldü" değil; durum kodu, content-type ve %PDF sihirli baytı ile doğrulanır
ve son kararı yine insan verir.

Kullanım:
  python3 bakim/banka_tara.py                 # ekrana rapor
  python3 bakim/banka_tara.py --markdown x.md # issue gövdesi olarak yaz
"""
from __future__ import annotations

import argparse
import concurrent.futures
import html
import re
import sys
import urllib.parse
import urllib.request

from ayarlar import PANO

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

CEYREK_SONU = {"1C": ("31", "03", "Mart"), "2C": ("30", "06", "Haziran"),
               "3C": ("30", "09", "Eylül"), "4C": ("31", "12", "Aralık")}
SIRA = ["1C", "2C", "3C", "4C"]


def sonraki_donem(donem: str) -> str:
    yil, ce = donem.split("-")
    i = SIRA.index(ce)
    return f"{int(yil) + 1}-1C" if i == 3 else f"{yil}-{SIRA[i + 1]}"


def isaretler(donem: str) -> list[re.Pattern]:
    """Bir dönemin sayfada geçebileceği yazım biçimleri.

    Tek bir kalıba güvenilemiyor: bankalar '30.06.2026', '30 06 2026',
    '30 Haziran 2026', '2026 2. Dönem', 'Q2 2026' gibi birbirinden bağımsız
    biçimler kullanıyor. Dar bir tarih regex'i daha önce Türkiye Finans ve
    Dünya Katılım'ı gözden kaçırmıştı.
    """
    yil, ce = donem.split("-")
    gun, ay, ayadi = CEYREK_SONU[ce]
    n = SIRA.index(ce) + 1
    return [re.compile(k, re.I) for k in (
        rf"{gun}\s*[._\-/]?\s*{ay}\s*[._\-/]?\s*{yil}",
        rf"{yil}\s*[._\-/]\s*{ay}\s*[._\-/]\s*{gun}",
        rf"{gun}\s+{ayadi}\s+{yil}",
        rf"{yil}[^<>]{{0,40}}\b{n}\s*\.?\s*(dönem|çeyrek)",
        rf"\b{n}\s*\.?\s*(dönem|çeyrek)[^<>]{{0,40}}{yil}",
        rf"\bq{n}[\s_\-]*{yil}\b",
        rf"\b{yil}[\s_\-]*q{n}\b",
        rf"\b{n}c{yil}\b",
    )]


AY_ADI = {"1C": "Mart", "2C": "Haziran", "3C": "Eylül", "4C": "Aralık"}
AY_SADE = {"1C": "mart", "2C": "haziran", "3C": "eylul", "4C": "aralik"}
CEYREK_ARALIK = {"1C": "ocak-mart", "2C": "nisan-haziran",
                 "3C": "temmuz-eylul", "4C": "ekim-aralik"}


def _token_ciftleri(kaynak: str, hedef: str) -> list[tuple[str, str]]:
    """İki dönemin URL'lerde geçen yazım biçimlerini eşler."""
    ky, kc = kaynak.split("-"); hy, hc = hedef.split("-")
    kg, ka, _ = CEYREK_SONU[kc]; hg, ha, _ = CEYREK_SONU[hc]
    kn, hn = kc[0], hc[0]
    ciftler = []
    for ayr in (".", "_", "-", "/", "%20", ""):
        ciftler.append((f"{kg}{ayr}{ka}{ayr}{ky}", f"{hg}{ayr}{ha}{ayr}{hy}"))   # 30.06.2026
        ciftler.append((f"{ky}{ayr}{ka}{ayr}{kg}", f"{hy}{ayr}{ha}{ayr}{hg}"))   # 2026-06-30
    for ayr in ("_", "-", ".", "%20", " "):
        ciftler.append((f"{kg}{ayr}{AY_ADI[kc]}{ayr}{ky}", f"{hg}{ayr}{AY_ADI[hc]}{ayr}{hy}"))
        ciftler.append((f"{kg}{ayr}{AY_SADE[kc]}{ayr}{ky}", f"{hg}{ayr}{AY_SADE[hc]}{ayr}{hy}"))
    ciftler += [
        (f"{kn}c{ky}", f"{hn}c{hy}"), (f"{ky}q{kn}", f"{hy}q{hn}"),
        (f"q{kn}{ky}", f"q{hn}{hy}"), (f"{ky}_{kn}", f"{hy}_{hn}"),
        (f"{ky}-{kn}", f"{hy}-{hn}"), (CEYREK_ARALIK[kc], CEYREK_ARALIK[hc]),
    ]
    return [(e, y) for e, y in ciftler if e]


def donem_degistir(url: str, kaynak: str, hedef: str) -> str | None:
    """URL'deki dönem işaretlerini hedef döneme çevirir; işaret yoksa None.

    Bankaların rapor sayfaları çoğunlukla JS ile üretildiği için kazıma tek
    başına yetmiyor. Buna karşılık dosya adları dönemi neredeyse her zaman
    açıkça taşıyor (`..._30.06.2026.pdf`, `2c2026_...`, `30_Haziran_2026`).
    Elde duran güncel linkten bir sonraki çeyreğin adresini türetip var mı
    diye bakmak, kazımadan daha güvenilir bir sinyal veriyor.
    """
    yeni = url
    for eski, hedef_tok in _token_ciftleri(kaynak, hedef):
        for bicim in (eski, eski.lower(), eski.upper(), eski.capitalize()):
            if bicim and bicim in yeni:
                y = (hedef_tok.upper() if bicim.isupper()
                     else hedef_tok.capitalize() if bicim[:1].isupper() else hedef_tok)
                yeni = yeni.replace(bicim, y)
    return yeni if yeni != url else None


def sayfa_getir(url: str, timeout: int = 30) -> str | None:
    try:
        istek = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(istek, timeout=timeout) as y:
            return y.read(3_000_000).decode("utf-8", "replace")
    except Exception:
        return None


def pdf_mi(url: str) -> tuple[bool, str]:
    """Linkin gerçekten PDF döndürdüğünü durum + tip + sihirli baytla doğrular."""
    try:
        istek = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(istek, timeout=40) as y:
            if y.status != 200:
                return False, f"HTTP {y.status}"
            tip = (y.headers.get("content-type") or "").lower()
            bas = y.read(5)
            if bas != b"%PDF-":
                return False, f"PDF değil ({tip.split(';')[0] or 'tip yok'})"
            return True, "PDF"
    except Exception as e:
        return False, type(e).__name__


def kartlari_oku(sayfa: str) -> dict[str, dict]:
    """index.html'den banka -> {donem, rapor sayfaları} çıkarır."""
    kartlar = {}
    for m in re.finditer(r'data-bank="([^"]+)"(.*?)(?=<div class="card|\Z)', sayfa, re.S):
        ad, govde = m.group(1), m.group(2)
        d = re.search(r'class="donem-badge">([^<]+)<', govde)
        if not d:
            continue
        yil, ce = d.group(1).split("/")
        donem = f"{yil}-{ce.replace('Ç', 'C')}"
        # nitelik sırası kartlar arasında değişiyor (href kimi yerde class'tan
        # önce geliyor); bu yüzden <a> etiketinin tamamı alınıp sınıfına bakılır
        linkler = []
        for etiket in re.findall(r"<a\b[^>]*>", govde):
            if "all-reports" not in etiket:
                continue
            u = re.search(r'href="([^"]+)"', etiket)
            if u:
                linkler.append(u.group(1))
        blok = re.search(r'class="all-reports-split".*?</div>', govde, re.S)
        if blok:
            linkler += re.findall(r'href="([^"]+)"', blok.group(0))
        dogrudan = []
        for etiket in re.findall(r"<a\b[^>]*>", govde):
            if 'class="pill' not in etiket:
                continue
            u = re.search(r'href="([^"]+)"', etiket)
            if u and u.group(1).startswith("http") and "bdr-arsiv" not in u.group(1):
                dogrudan.append(html.unescape(u.group(1)))
        mevcut = kartlar.setdefault(ad, {"donem": donem, "sayfalar": [], "dogrudan": []})
        for u in dogrudan:
            if u not in mevcut["dogrudan"]:
                mevcut["dogrudan"].append(u)
        # aynı banka birden çok sekmede geçebilir; en yeni dönemi tut
        if donem > mevcut["donem"]:
            mevcut["donem"] = donem
        for u in linkler:
            u = html.unescape(u)
            if u.startswith("http") and u not in mevcut["sayfalar"]:
                mevcut["sayfalar"].append(u)
    return kartlar


def bankayi_tara(ad: str, bilgi: dict) -> dict | None:
    hedef = sonraki_donem(bilgi["donem"])

    # Yöntem A — elde duran linkten bir sonraki çeyreğin adresini türet.
    # Kazımadan daha güvenilir; banka dosyayı aynı kalıpla yayımlıyorsa bulur.
    for u in bilgi.get("dogrudan", []):
        aday = donem_degistir(u, bilgi["donem"], hedef)
        if not aday:
            continue
        tamam, _ = pdf_mi(aday)
        if tamam:
            return {"banka": ad, "mevcut": bilgi["donem"], "bulunan": hedef,
                    "url": aday, "etiket": "(link kalıbından türetildi)",
                    "sayfa": u, "yontem": "kalıp"}

    # Yöntem B — bankanın rapor sayfasını tara
    kaliplar = isaretler(hedef)
    for sayfa_url in bilgi["sayfalar"]:
        icerik = sayfa_getir(sayfa_url)
        if not icerik:
            continue
        # sayfadaki her linki etiketiyle birlikte al; dar tarih regex'i yerine
        # etiket metni üzerinden eşleştirmek daha güvenilir çıktı verdi
        for m in re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', icerik, re.S):
            ham_url, etiket = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
            etiket = html.unescape(" ".join(etiket.split()))
            tam = urllib.parse.urljoin(sayfa_url, html.unescape(ham_url))
            # Dönem bilgisi çoğu sitede linkin içinde değil, satırın başında ya
            # da sonunda duruyor (tablo hücresi, başlık, kardeş <span>). Bu
            # yüzden linkin çevresindeki metin de taranıyor. Geniş pencere yanlış
            # satırın tarihini yakalayabilir; bu yüzden script yalnızca bildirir,
            # Solo/Konsolide kararını insana bırakır.
            cevre = re.sub(r"<[^>]+>", " ", icerik[max(0, m.start() - 300):m.end() + 300])
            metin = f"{tam} {etiket} {html.unescape(' '.join(cevre.split()))}"
            if not any(k.search(metin) for k in kaliplar):
                continue
            if not re.search(r"\.pdf(\?|$)", tam, re.I):
                continue
            tamam, not_ = pdf_mi(tam)
            if tamam:
                return {"banka": ad, "mevcut": bilgi["donem"], "bulunan": hedef,
                        "url": tam, "etiket": etiket[:90], "sayfa": sayfa_url,
                        "yontem": "sayfa"}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--markdown", help="raporu bu dosyaya markdown olarak yaz")
    ap.add_argument("--is-parcaciği", type=int, default=8, dest="isci",
                    help="eşzamanlı istek sayısı")
    args = ap.parse_args()

    kartlar = kartlari_oku(open(PANO, encoding="utf-8").read())
    if not kartlar:
        sys.exit("index.html'den kart okunamadı")
    print(f"taranacak banka: {len(kartlar)}", flush=True)

    bulgular = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.isci) as h:
        isler = {h.submit(bankayi_tara, ad, b): ad for ad, b in kartlar.items()}
        for i, is_ in enumerate(concurrent.futures.as_completed(isler), 1):
            sonuc = is_.result()
            if sonuc:
                bulgular.append(sonuc)
                print(f"  + {sonuc['banka']}: {sonuc['bulunan']} yayımlanmış", flush=True)
            if i % 20 == 0:
                print(f"  ... {i}/{len(kartlar)}", flush=True)

    bulgular.sort(key=lambda x: x["banka"])
    print(f"\nyeni yayım bulunan banka: {len(bulgular)}")

    if args.markdown:
        satirlar = []
        if bulgular:
            satirlar.append(f"{len(bulgular)} bankanın sitesinde, panodaki dönemden "
                            "daha yeni bir rapor yayımlanmış görünüyor. Aşağıdaki "
                            "linkler HTTP durumu, content-type ve `%PDF` baytıyla "
                            "doğrulandı; **Solo/Konsolide eşleşmesi doğrulanmadı** — "
                            "panoya işlemeden önce etiketi kontrol edin.\n")
            satirlar.append("| Banka | Panoda | Sitede | Yöntem | Etiket | Link |")
            satirlar.append("|---|---|---|---|---|---|")
            for b in bulgular:
                satirlar.append(f"| {b['banka']} | {b['mevcut']} | {b['bulunan']} | "
                                f"{b['yontem']} | {b['etiket']} | [PDF]({b['url']}) |")
        else:
            satirlar.append("Bankaların sitelerinde panodakinden yeni bir rapor bulunamadı.")
        open(args.markdown, "w", encoding="utf-8").write("\n".join(satirlar) + "\n")
        print(f"markdown yazıldı: {args.markdown}")


if __name__ == "__main__":
    main()
