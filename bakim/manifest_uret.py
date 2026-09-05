#!/usr/bin/env python3
"""Panonun gömülü arşiv manifestini üretir.

Kaynak: BDR-Arsiv/manifest.json (indirici tarafından yazılır)
Çıktı : arsiv_manifest_min.json — panoya gömülecek sıkıştırılmış biçim

Sıkıştırma gerekçesi: dönem sayısı 2005'e açılınca 86'ya çıkıyor. Düz biçimde
her kayıt kendi yolunu tekrar yazdığı için manifest yüz binlerce bayta çıkıyordu.
Yol zaten "<donem>/<slug>-<tip>.<uzanti>" kalıbından türetilebildiği için yalnızca
hangi tiplerin bulunduğu ("s"=solo, "k"=konsolide) saklanıyor; uzantı varsayılan
"pdf", istisnalar (2005-2008 dönemindeki doc/xls/tif/mdi/rar) ayrı listede.

Çıktı biçimi:
  {"slug": {"Banka Adı": "banka-slug", ...},
   "a":    {"Banka Adı": {"2021-1C": "sk", ...}, ...},
   "ext":  {"2005-1C/ziraat-bankasi-solo": "doc", ...}}
"""
import argparse
import json
import os
import subprocess
import sys

from ayarlar import ARSIV_KOK as KOK, MANIFEST_MIN

AD_ESLESTIRME = {
    "kuveyt-turk": "Kuveyt Türk", "vakif-katilim": "Vakıf Katılım",
    "ziraat-katilim": "Ziraat Katılım", "albaraka": "Albaraka",
    "turkiye-finans": "Türkiye Finans", "emlak-katilim": "Emlak Katılım",
    "dunya-katilim": "Dünya Katılım", "hayat-finans": "Hayat Finans",
    "tom-bank": "TOM Bank", "ziraat-bankasi": "Ziraat Bankası",
    "vakifbank": "VakıfBank", "is-bankasi": "İş Bankası", "halkbank": "Halkbank",
    "garanti-bbva": "Garanti BBVA", "yapi-kredi": "Yapı Kredi", "akbank": "Akbank",
    "qnb": "QNB", "denizbank": "DenizBank", "teb": "TEB", "hsbc": "HSBC",
    "ing": "ING", "enpara": "Enpara", "sekerbank": "Şekerbank",
    "fibabanka": "Fibabanka", "anadolubank": "Anadolubank",
    "burgan-bank": "Burgan Bank", "odeabank": "Odeabank",
    "alternatif-bank": "Alternatif Bank", "citibank": "Citibank",
    "icbc-turkey": "ICBC Turkey", "mufg-bank-turkey": "MUFG Bank Turkey",
    "deutsche-bank": "Deutsche Bank", "arap-turk-bankasi": "Arap Türk Bankası",
    "turkland-bank": "Turkland Bank", "bank-of-china-turkey": "Bank of China Turkey",
    "ziraat-dinamik": "Ziraat Dinamik", "colendi-bank": "Colendi Bank",
    "rabobank": "Rabobank", "bank-mellat": "Bank Mellat",
    "societe-generale": "Société Générale", "turkish-bank": "Turkish Bank",
    "turk-eximbank": "Türk Eximbank", "iller-bankasi": "İller Bankası",
    "tskb": "TSKB", "takasbank": "Takasbank", "kalkinma-bankasi": "Kalkınma Bankası",
    "aktif-bank": "Aktif Bank", "nurol-yatirim-bankasi": "Nurol Yatırım Bankası",
    "destek-yatirim-bankasi": "Destek Yatırım Bankası",
    "golden-global-bank": "Golden Global Bank", "q-yatirim-bankasi": "Q Yatırım Bankası",
    "pashabank": "PashaBank", "tera-bank": "Tera Bank",
    "d-yatirim-bankasi": "D Yatırım Bankası", "misyon-bank": "Misyon Bank",
    "bank-of-america-yatirim-bank": "Bank of America Yatırım Bank",
    "hedef-yatirim-bankasi": "Hedef Yatırım Bankası",
    "gsd-yatirim-bankasi": "GSD Yatırım Bankası", "bankpozitif": "BankPozitif",
    "standard-chartered": "Standard Chartered",
    "diler-yatirim-bankasi": "Diler Yatırım Bankası",
    "aytemiz-yatirim-bankasi": "Aytemiz Yatırım Bankası",
    "birlesik-fon-bankasi": "Birleşik Fon Bankası",
    "intesa-sanpaolo": "Intesa Sanpaolo", "jpmorgan-chase": "JPMorgan Chase",
    "turk-ticaret-bankasi": "Türk Ticaret Bankası",
}

TIP_KISA = {"solo": "s", "konsolide": "k"}

# Yayımdaki pencere: en yeni dönemin yılı dahil son PENCERE_YIL takvim yılı.
# Sabit bir başlangıç yılı yazılmıyor; yeni çeyrek eklendiğinde pencere
# kendiliğinden kayıyor, böylece site her çeyrek elle güncellenmeden "son 10 yıl"
# kalıyor ve R2 ücretsiz kotası (10 GB) aşılmıyor. Disk 2005'e kadar dolu, ancak
# pencere dışı bir dönem manifeste girerse R2'de karşılığı olmadığı için sitede
# kırık link oluşur — bu yüzden pencere hem manifesti hem yüklemeyi belirler.
PENCERE_YIL = 10


def pencere_alt_siniri(donemler) -> int:
    """Manifestteki en yeni yılı baz alarak pencerenin ilk yılını verir."""
    en_yeni = max(int(d.split("-")[0]) for d in donemler)
    return en_yeni - PENCERE_YIL + 1


def _diskten() -> dict[str, str]:
    """Yerel manifest.json'dan 'dönem/slug/tip' -> göreli yol sözlüğü."""
    manifest = json.load(open(os.path.join(KOK, "manifest.json"), encoding="utf-8"))
    return {k: v for k, v in manifest.items()
            if os.path.exists(os.path.join(KOK, v))}


def _r2den() -> dict[str, str]:
    """R2 nesne listesinden aynı sözlüğü kurar.

    Site R2'den beslendiği için gerçeğin kaynağı R2'dir; manifesti oradan
    üretmek hem yerel diske bağımlılığı kaldırır (GitHub Actions'ta disk yok)
    hem de manifestin sitede karşılığı olmayan bir kayıt taşımasını imkânsız
    kılar. Nesne anahtarı zaten 'raporlar/<dönem>/<slug>-<tip>.<uzantı>'.
    """
    sonuc = subprocess.run(
        ["rclone", "lsf", "r2:bdr-arsiv/raporlar", "--recursive", "--files-only"],
        capture_output=True, text=True)
    if sonuc.returncode != 0:
        sys.exit(f"rclone listesi alınamadı:\n{sonuc.stderr.strip()}")
    kayitlar = {}
    for satir in sonuc.stdout.splitlines():
        satir = satir.strip()
        if not satir or "/" not in satir:
            continue
        donem, dosya = satir.split("/", 1)
        govde = dosya.rsplit(".", 1)[0]
        if govde.endswith("-solo"):
            slug, tip = govde[:-5], "solo"
        elif govde.endswith("-konsolide"):
            slug, tip = govde[:-10], "konsolide"
        else:
            continue
        kayitlar[f"{donem}/{slug}/{tip}"] = "raporlar/" + satir
    return kayitlar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kaynak", choices=("r2", "disk"), default="r2",
                    help="manifestin üretileceği kaynak (varsayılan: r2)")
    args = ap.parse_args()

    manifest = _r2den() if args.kaynak == "r2" else _diskten()
    if not manifest:
        sys.exit("kaynak boş — manifest üretilemedi")

    slug_map, a, ext = {}, {}, {}
    eslesmeyen = set()

    min_yil = pencere_alt_siniri(k.split("/")[0] for k in manifest)

    for anahtar, yol in manifest.items():
        donem, slug, tip = anahtar.split("/")
        if int(donem.split("-")[0]) < min_yil:
            continue
        ad = AD_ESLESTIRME.get(slug)
        if not ad:
            eslesmeyen.add(slug)
            continue
        slug_map[ad] = slug
        uzanti = yol.rsplit(".", 1)[-1].lower()
        if uzanti != "pdf":
            ext[f"{donem}/{slug}-{tip}"] = uzanti
        a.setdefault(ad, {})
        a[ad][donem] = a[ad].get(donem, "") + TIP_KISA[tip]

    # tip harflerini sabit sıraya sok — deterministik çıktı
    for ad in a:
        for d in a[ad]:
            a[ad][d] = "".join(ch for ch in "sk" if ch in a[ad][d])

    hedef = MANIFEST_MIN
    os.makedirs(os.path.dirname(hedef), exist_ok=True)
    with open(hedef, "w", encoding="utf-8") as f:
        json.dump({"slug": slug_map, "a": a, "ext": ext}, f,
                  ensure_ascii=False, separators=(",", ":"))

    print(f"kaynak          : {args.kaynak}")
    donemler = sorted({d for v in a.values() for d in v})
    print(f"pencere         : son {PENCERE_YIL} yıl (>= {min_yil})")
    print(f"eşleşmeyen slug : {eslesmeyen or 'yok'}")
    print(f"banka           : {len(a)}")
    print(f"dönem           : {len(donemler)}  ({donemler[0]} .. {donemler[-1]})")
    print(f"pdf olmayan     : {len(ext)}")
    print(f"boyut           : {os.path.getsize(hedef)/1024:.0f} KB")


if __name__ == "__main__":
    main()
