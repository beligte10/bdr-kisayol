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
import hashlib
import html
import json
import os
import subprocess
import tempfile
import re
import sys
import urllib.parse
import unicodedata
import urllib.request

from ayarlar import PANO

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

CEYREK_SONU = {"1C": ("31", "03", "Mart"), "2C": ("30", "06", "Haziran"),
               "3C": ("30", "09", "Eylül"), "4C": ("31", "12", "Aralık")}
SIRA = ["1C", "2C", "3C", "4C"]


def onceki_donem(donem: str) -> str:
    yil, ce = donem.split("-")
    i = SIRA.index(ce)
    return f"{int(yil) - 1}-4C" if i == 0 else f"{yil}-{SIRA[i - 1]}"


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


SOLO_IZ = ("konsolide olmayan", "konsolide olmyan", "non consolidated",
           "unconsolidated", "solo", "bireysel")
KONS_IZ = ("konsolide", "consolidated")


def _sade(s: str) -> str:
    d = {"ı": "i", "İ": "i", "ş": "s", "Ş": "s", "ğ": "g", "Ğ": "g",
         "ü": "u", "Ü": "u", "ö": "o", "Ö": "o", "ç": "c", "Ç": "c"}
    s = "".join(d.get(ch, ch) for ch in s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s)


def tip_belirle(*metinler: str) -> str | None:
    """'solo' | 'konsolide' | None (belirsiz).

    Türk bankacılığında "Konsolide Olmayan Finansal Rapor" SOLO demektir;
    metinde 'konsolide' geçiyor diye konsolide saymak bu işin en klasik
    hatası ve panoda bir kez yaşandı. Bu yüzden önce olumsuzlama aranır.
    Ayrım okunamıyorsa bilerek None döner: yanlış tip, eksik tipten kötüdür.
    """
    m = _sade(" ".join(x for x in metinler if x))
    if any(iz in m for iz in SOLO_IZ):
        return "solo"
    if any(iz in m for iz in KONS_IZ):
        return "konsolide"
    return None


def sayfa_getir(url: str, timeout: int = 30) -> str | None:
    try:
        istek = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(istek, timeout=timeout) as y:
            return y.read(3_000_000).decode("utf-8", "replace")
    except Exception:
        return None


def sayfa_ham(url: str, timeout: int = 90) -> bytes | None:
    try:
        istek = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(istek, timeout=timeout) as y:
            return y.read(80_000_000)
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
        for a in re.finditer(r'<a\b[^>]*class="pill[^"]*"[^>]*>(.*?)</a>', govde, re.S):
            tam = a.group(0)
            u = re.search(r'href="([^"]+)"', tam)
            if not (u and u.group(1).startswith("http")) or "bdr-arsiv" in u.group(1):
                continue
            yazi = html.unescape(" ".join(re.sub(r"<[^>]+>", " ", a.group(1)).split()))
            dogrudan.append((html.unescape(u.group(1)), yazi))
        mevcut = kartlar.setdefault(ad, {"donem": donem, "sayfalar": [], "dogrudan": []})
        for cift in dogrudan:
            if cift not in mevcut["dogrudan"]:
                mevcut["dogrudan"].append(cift)
        # aynı banka birden çok sekmede geçebilir; en yeni dönemi tut
        if donem > mevcut["donem"]:
            mevcut["donem"] = donem
        for u in linkler:
            u = html.unescape(u)
            if u.startswith("http") and u not in mevcut["sayfalar"]:
                mevcut["sayfalar"].append(u)
    return kartlar


def bankayi_tara(ad: str, bilgi: dict) -> list[dict]:
    """Bankanın sitesinde bir sonraki döneme ait raporları arar.

    İki yöntem denenir. Yöntem A elde duran linkten sonraki çeyreğin adresini
    türetir; buradaki tip bilgisi kesindir, çünkü butonun kendi etiketinden
    ("Solo"/"Konsolide") gelir ve URL'de yalnızca dönem değişmiştir. Yöntem B
    rapor sayfasını tarar; orada tip yalnızca metinden okunabildiği için
    belirsiz kalabilir.
    """
    hedef = sonraki_donem(bilgi["donem"])
    bulgular: dict[str, dict] = {}

    # Yöntem A — link kalıbından türet (tip kesin)
    for url, buton in bilgi.get("dogrudan", []):
        aday = donem_degistir(url, bilgi["donem"], hedef)
        if not aday:
            continue
        tamam, _ = pdf_mi(aday)
        if not tamam:
            continue
        tip = tip_belirle(buton) or tip_belirle(url)
        anahtar = tip or f"?{len(bulgular)}"
        bulgular.setdefault(anahtar, {
            "banka": ad, "mevcut": bilgi["donem"], "bulunan": hedef, "url": aday,
            "etiket": f"(buton: {buton} — link kalıbından türetildi)",
            "sayfa": url, "yontem": "kalıp", "tip": tip})

    if all(t in bulgular for t in ("solo", "konsolide")):
        return list(bulgular.values())

    # Yöntem B — rapor sayfasını tara
    kaliplar = isaretler(hedef)
    yabanci = []
    komsu = hedef
    for _ in range(4):
        komsu = onceki_donem(komsu)
        yabanci += isaretler(komsu)
    yabanci += isaretler(sonraki_donem(hedef))
    for sayfa_url in bilgi["sayfalar"]:
        icerik = sayfa_getir(sayfa_url)
        if not icerik:
            continue
        for m in re.finditer(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', icerik, re.S):
            ham_url, etiket = m.group(1), re.sub(r"<[^>]+>", " ", m.group(2))
            etiket = html.unescape(" ".join(etiket.split()))
            tam = urllib.parse.urljoin(sayfa_url, html.unescape(ham_url))
            # Dönem bilgisi çoğu sitede linkin içinde değil, satırın başında ya
            # da sonunda duruyor (tablo hücresi, başlık, kardeş <span>).
            cevre = re.sub(r"<[^>]+>", " ", icerik[max(0, m.start() - 300):m.end() + 300])
            cevre = html.unescape(" ".join(cevre.split()))
            if not any(k.search(f"{tam} {etiket} {cevre}") for k in kaliplar):
                continue
            if not re.search(r"\.pdf(\?|$)", tam, re.I):
                continue
            # Bağlam penceresi komşu satırın tarihine taşabiliyor: linkin kendi
            # adı/etiketi başka bir dönemi işaret ediyorsa bu aday hedef döneme
            # ait değildir. (Enpara'nın listesinde 31.03.2026 böyle yakalandı.)
            kendi = f"{tam} {etiket}"
            if any(k.search(kendi) for k in yabanci):
                continue
            tip = tip_belirle(etiket) or tip_belirle(tam)
            if tip and tip in bulgular:
                continue
            tamam, _ = pdf_mi(tam)
            if not tamam:
                continue
            anahtar = tip or f"?{len(bulgular)}"
            bulgular.setdefault(anahtar, {
                "banka": ad, "mevcut": bilgi["donem"], "bulunan": hedef, "url": tam,
                "etiket": etiket[:90], "sayfa": sayfa_url, "yontem": "sayfa", "tip": tip})
            if all(t in bulgular for t in ("solo", "konsolide")):
                return list(bulgular.values())
    return list(bulgular.values())


UZAK = "r2:bdr-arsiv"
KAYNAK_DOSYA = "kaynak_banka.json"   # banka sitesinden gelen nesnelerin listesi


def r2_nesneleri(onek: str) -> set[str]:
    c = subprocess.run(["rclone", "lsf", f"{UZAK}/{onek}", "--recursive", "--files-only"],
                       capture_output=True, text=True)
    return {x.strip() for x in c.stdout.splitlines() if x.strip()} if c.returncode == 0 else set()


def r2_yaz(yerel: str, anahtar: str) -> None:
    subprocess.run(["rclone", "copyto", yerel, f"{UZAK}/{anahtar}",
                    "--s3-no-check-bucket"], check=True)


def kaynak_listesi_guncelle(yeni_anahtarlar: list[str], gecici: str) -> None:
    """Banka sitesinden gelen nesneleri işaretler.

    Arşivin gövdesi BDDK'dan gelir; banka sitesinden erken alınan kopya geçici
    bir vekildir. Bu liste sayesinde otomatik_tara.py o anahtarları "zaten var"
    diye atlamaz, BDDK yayımlayınca kendi kopyasıyla değiştirir.
    """
    yol = os.path.join(gecici, KAYNAK_DOSYA)
    mevcut = []
    c = subprocess.run(["rclone", "copyto", f"{UZAK}/{KAYNAK_DOSYA}", yol],
                       capture_output=True, text=True)
    if c.returncode == 0 and os.path.exists(yol):
        try:
            mevcut = json.load(open(yol, encoding="utf-8"))
        except Exception:
            mevcut = []
    birlesik = sorted(set(mevcut) | set(yeni_anahtarlar))
    json.dump(birlesik, open(yol, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    r2_yaz(yol, KAYNAK_DOSYA)


def indir_ve_yukle(bulgular: list[dict], slug_map: dict, gecici: str) -> tuple[list, list]:
    """Tipi kesin olanları arşive, belirsizleri karantinaya koyar."""
    arsive, karantinaya = [], []
    mevcut = r2_nesneleri("raporlar")
    for b in bulgular:
        slug = slug_map.get(b["banka"])
        if not slug:
            continue
        ham = sayfa_ham(b["url"])
        if not ham or ham[:5] != b"%PDF-":
            continue
        if b["tip"]:
            anahtar = f"raporlar/{b['bulunan']}/{slug}-{b['tip']}.pdf"
            if anahtar[len("raporlar/"):] in mevcut:
                continue                    # BDDK zaten yayımlamış, dokunma
            hedef = "arşiv"
        else:
            # Solo/Konsolide okunamadı: dosya saklanır ama arşive girmez,
            # çünkü yanlış tipe yazmak sitede sessizce hatalı link üretir
            damga = hashlib.sha1(b["url"].encode()).hexdigest()[:8]
            anahtar = f"karantina/{b['bulunan']}/{slug}-{damga}.pdf"
            hedef = "karantina"
        yerel = os.path.join(gecici, os.path.basename(anahtar))
        with open(yerel, "wb") as f:
            f.write(ham)
        r2_yaz(yerel, anahtar)
        b["anahtar"] = anahtar
        (arsive if hedef == "arşiv" else karantinaya).append(b)
    return arsive, karantinaya


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--markdown", help="raporu bu dosyaya markdown olarak yaz")
    ap.add_argument("--uygula", action="store_true",
                    help="bulunan raporları indirip R2'ye koy")
    ap.add_argument("--isci", type=int, default=8, help="eşzamanlı istek sayısı")
    args = ap.parse_args()

    sayfa = open(PANO, encoding="utf-8").read()
    slug_map = json.loads(re.search(r'id="arsivManifest">(.*?)</script>',
                                    sayfa, re.S).group(1))["slug"]
    kartlar = kartlari_oku(sayfa)
    if not kartlar:
        sys.exit("index.html'den kart okunamadı")
    print(f"taranacak banka: {len(kartlar)}", flush=True)

    bulgular = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.isci) as h:
        isler = {h.submit(bankayi_tara, ad, b): ad for ad, b in kartlar.items()}
        for i, is_ in enumerate(concurrent.futures.as_completed(isler), 1):
            for s in is_.result():
                bulgular.append(s)
                print(f"  + {s['banka']} {s['tip'] or '(tip belirsiz)'}: "
                      f"{s['bulunan']} [{s['yontem']}]", flush=True)
            if i % 20 == 0:
                print(f"  ... {i}/{len(kartlar)}", flush=True)

    bulgular.sort(key=lambda x: (x["banka"], x["tip"] or "z"))
    kesin = [b for b in bulgular if b["tip"]]
    print(f"\nbulgu: {len(bulgular)} (tipi kesin {len(kesin)}, "
          f"belirsiz {len(bulgular) - len(kesin)})")

    arsive, karantinaya = [], []
    if bulgular and args.uygula:
        with tempfile.TemporaryDirectory() as gecici:
            arsive, karantinaya = indir_ve_yukle(bulgular, slug_map, gecici)
            if arsive:
                kaynak_listesi_guncelle([b["anahtar"] for b in arsive], gecici)
        print(f"arşive eklenen: {len(arsive)} | karantinaya alınan: {len(karantinaya)}")
    elif bulgular:
        print("(kuru çalıştırma — indirmek için --uygula)")

    if args.markdown:
        yaz_markdown(args.markdown, bulgular, arsive, karantinaya, args.uygula)
        print(f"markdown yazıldı: {args.markdown}")


def yaz_markdown(yol, bulgular, arsive, karantinaya, uygulandi):
    s = []
    if not bulgular:
        s.append("Bankaların sitelerinde panodakinden yeni bir rapor bulunamadı.")
    else:
        s.append(f"Banka sitelerinde **{len(bulgular)}** yeni rapor bulundu. "
                 "Linkler HTTP durumu, content-type ve `%PDF` baytıyla doğrulandı.\n")
        if uygulandi:
            s.append(f"- Arşive eklenen (Solo/Konsolide ayrımı kesin): **{len(arsive)}**")
            s.append(f"- Karantinaya alınan (ayrım okunamadı): **{len(karantinaya)}**\n")
            if karantinaya:
                s.append("Karantinadakiler siteye **girmedi**. Aşağıdaki tabloda tipini "
                         "belirleyip `rclone copyto` ile `raporlar/<dönem>/<slug>-<tip>.pdf` "
                         "olarak taşıyabilirsiniz.\n")
        s.append("| Banka | Panoda | Bulunan | Tip | Yöntem | Etiket | Link |")
        s.append("|---|---|---|---|---|---|---|")
        for b in bulgular:
            tip = b["tip"] or "**belirsiz**"
            s.append(f"| {b['banka']} | {b['mevcut']} | {b['bulunan']} | {tip} | "
                     f"{b['yontem']} | {b['etiket']} | [PDF]({b['url']}) |")
    open(yol, "w", encoding="utf-8").write("\n".join(s) + "\n")


if __name__ == "__main__":
    main()
