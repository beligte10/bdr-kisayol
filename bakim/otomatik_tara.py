#!/usr/bin/env python3
"""BDDK'da yeni yayımlanan raporları bulup doğrudan R2'ye ekler.

GitHub Actions içinde çalışmak üzere yazıldı: yerel 15 GB arşive ihtiyaç
duymaz, neyin zaten yayımda olduğunu R2 nesne listesinden öğrenir. İndirdiği
belgeyi geçici dizine yazıp rclone ile R2'ye kopyalar.

Taranan dönemler: R2'deki en yeni dönem ve onu izleyen iki çeyrek. Böylece
hem o dönemi geç yayımlayan bankalar hem de yeni açılan çeyrek yakalanır.

Kullanım:
  python3 bakim/otomatik_tara.py            # yalnızca ne bulunduğunu yazdır
  python3 bakim/otomatik_tara.py --uygula   # bulduklarını R2'ye yükle
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

from bdr_indir import BANKALAR, CEYREK, belge_cikar, indir, slug, BDDK
from kota import Kota
import urllib.parse

CEYREK_AY = {"1C": 3, "2C": 6, "3C": 9, "4C": 12}
UZAK = "r2:bdr-arsiv/raporlar"
KAYNAK_DOSYA = "r2:bdr-arsiv/kaynak_banka.json"


def banka_kaynakli(gecici: str) -> tuple[list[str], str]:
    """Banka sitesinden erken alınmış nesnelerin listesi.

    Bu kopyalar geçici vekildir; BDDK aynı raporu yayımlayınca kendi
    kopyasıyla değiştirilir, böylece arşivin gövdesi tek kaynaklı kalır.
    """
    yol = os.path.join(gecici, "kaynak_banka.json")
    c = subprocess.run(["rclone", "copyto", KAYNAK_DOSYA, yol],
                       capture_output=True, text=True)
    if c.returncode != 0 or not os.path.exists(yol):
        return [], yol
    try:
        return json.load(open(yol, encoding="utf-8")), yol
    except Exception:
        return [], yol


def sonraki_donem(donem: str) -> str:
    yil, ce = donem.split("-")
    sira = ["1C", "2C", "3C", "4C"]
    i = sira.index(ce)
    return f"{int(yil) + 1}-1C" if i == 3 else f"{yil}-{sira[i + 1]}"


def onceki_donem(donem: str) -> str:
    yil, ce = donem.split("-")
    sira = ["1C", "2C", "3C", "4C"]
    i = sira.index(ce)
    return f"{int(yil) - 1}-4C" if i == 0 else f"{yil}-{sira[i - 1]}"


# Yeni dosya, önceki çeyrekteki karşılığının bu oranından küçükse "kısa" sayılır.
# (BDDK bazen yalnızca mali tabloları yayımlıyor: Ziraat 3Ç 7 sayfa, 2Ç 114 sayfa.)
KISA_ORAN = 0.35


def r2_envanteri() -> tuple[set[str], set[str], dict[str, int]]:
    """(nesne anahtarları, dönem klasörleri, anahtar -> bayt) döndürür."""
    s = subprocess.run(["rclone", "lsf", UZAK, "--recursive", "--files-only",
                        "--format", "ps", "--separator", ";"],
                       capture_output=True, text=True)
    if s.returncode != 0:
        sys.exit(f"rclone listesi alınamadı:\n{s.stderr.strip()}")
    boyutlar = {}
    for satir in s.stdout.splitlines():
        yol, _, boyut = satir.strip().rpartition(";")
        if yol and boyut.isdigit():
            boyutlar[yol] = int(boyut)
    nesneler = set(boyutlar)
    donemler = {n.split("/")[0] for n in nesneler if "/" in n}
    return nesneler, donemler, boyutlar


def kisa_mi(taban: str, donem: str, boyut: int, boyutlar: dict[str, int]) -> int | None:
    """Önceki çeyrekteki aynı rapor çok daha büyükse onun boyutunu döndürür."""
    once = onceki_donem(donem)
    onceki = taban.replace(donem + "/", once + "/", 1)
    for anahtar, b in boyutlar.items():
        if anahtar.startswith(onceki + ".") and b > 0 and boyut < b * KISA_ORAN:
            return b
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uygula", action="store_true", help="bulunanları R2'ye yükle")
    ap.add_argument("--bekleme", type=float, default=0.6,
                    help="her işçinin istekleri arasındaki saniye")
    ap.add_argument("--isci", type=int, default=6, help="eşzamanlı istek sayısı")
    args = ap.parse_args()

    nesneler, donemler, boyutlar = r2_envanteri()
    if not donemler:
        sys.exit("R2 boş görünüyor — otomatik tarama güvenli değil, elle bakın")

    en_yeni = max(donemler)
    hedefler = [en_yeni]
    for _ in range(2):
        hedefler.append(sonraki_donem(hedefler[-1]))

    print(f"R2'deki en yeni dönem : {en_yeni}")
    print(f"taranacak dönemler    : {', '.join(hedefler)}")
    print(f"mevcut nesne          : {len(nesneler)}\n", flush=True)

    eklenen = []
    kisalar = []
    kota = Kota(args.uygula)
    with tempfile.TemporaryDirectory() as gecici:
        vekiller, vekil_yolu = banka_kaynakli(gecici)
        ilk_vekiller = list(vekiller)
        if vekiller:
            print(f"banka sitesinden gelen vekil kopya: {len(vekiller)}\n", flush=True)
        # 1) Denenecek kombinasyonlar (zaten yayımda olanlar atlanır)
        isler = []
        for donem in hedefler:
            yil, ce = donem.split("-")
            ay = CEYREK_AY[ce]
            for ad, kod in BANKALAR.items():
                for tip in ("SOLO", "KONSOLIDE"):
                    taban = f"{donem}/{slug(ad)}-{tip.lower()}"
                    vekil = [k for k in vekiller if k.startswith("raporlar/" + taban + ".")]
                    if any(n.startswith(taban + ".") for n in nesneler) and not vekil:
                        continue                     # BDDK kopyası zaten yayımda
                    dosya = f"BDREki-{kod}-{tip}-{yil}-{ay:02d}.zip"
                    isler.append((donem, ad, tip, taban, vekil, dosya))
        denenen = len(isler)

        # 2) İstekler paralel atılır (sürenin neredeyse tamamı ağ gecikmesiydi);
        #    her işçi istekler arasında bekler, BDDK'ya saniyede en çok
        #    isci/bekleme istek gider. Sonuçlar gönderim sırasıyla işlenir.
        def getir(is_):
            ham = indir(BDDK + urllib.parse.quote(is_[5]))
            time.sleep(args.bekleme)                 # BDDK'yı yormamak için
            return ham

        # 3) İşleme sıralı kalır: kota, yükleme ve vekil listesi tek akışta
        with ThreadPoolExecutor(max_workers=args.isci) as havuz:
            for (donem, ad, tip, taban, vekil, _), ham in zip(isler, havuz.map(getir, isler)):
                if not ham or len(ham) < 1000 or b"PK\x03\x04" not in ham[:4096]:
                    continue                         # o dönem/tip için yayın yok
                belge, uzanti = belge_cikar(ham)
                if not belge:
                    print(f"  ! belge çıkarılamadı: {ad} {donem} {tip}", file=sys.stderr)
                    continue
                anahtar = f"{taban}.{uzanti}"
                yerel = os.path.join(gecici, os.path.basename(anahtar))
                with open(yerel, "wb") as f:
                    f.write(belge)
                # yer yoksa en eski çeyreği bütünüyle sil (yüklenen dönem korunur)
                kota.yer_ac(len(belge), korunan={donem})
                if args.uygula:
                    subprocess.run(["rclone", "copyto", yerel, f"{UZAK}/{anahtar}",
                                    "--s3-no-check-bucket"], check=True)
                    for k in vekil:
                        vekiller.remove(k)           # artık BDDK kopyası duruyor
                kota.eklendi(len(belge))
                eklenen.append((anahtar, len(belge)))
                isaret = " (banka kopyasının yerine)" if vekil else ""
                onceki_b = kisa_mi(taban, donem, len(belge), boyutlar)
                if onceki_b:
                    kisalar.append((anahtar, len(belge), onceki_b))
                    isaret += "  !! KISA"
                    print(f"::warning title=BDDK dosyası kısa::{anahtar} {len(belge)/1048576:.1f} MB; "
                          f"önceki çeyrek {onceki_b/1048576:.1f} MB — yalnızca mali tablo olabilir, "
                          f"denetim raporunu banka sitesinden kontrol edin")
                print(f"  + {anahtar}  ({len(belge)/1048576:.1f} MB){isaret}", flush=True)

        # liste değişmediyse R2'ye boşuna yazma (her çalıştırmada bir yazma işlemi)
        if args.uygula and vekiller != ilk_vekiller:
            json.dump(vekiller, open(vekil_yolu, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            subprocess.run(["rclone", "copyto", vekil_yolu, KAYNAK_DOSYA,
                            "--s3-no-check-bucket"], check=True)

    print(f"\ndenenen kombinasyon : {denenen}")
    print(f"yeni rapor          : {len(eklenen)}")
    print(f"R2 doluluk          : {kota.dolu/1e9:.2f} GB"
          + (f"  (kota için silinen çeyrek: {', '.join(kota.silinen)})" if kota.silinen else ""))
    if kisalar:
        print(f"kısa kalan dosya    : {len(kisalar)} (denetim raporu eksik olabilir)")
        with open(os.environ.get("KISA_RAPOR", "/tmp/kisa.md"), "w", encoding="utf-8") as f:
            f.write("BDDK'dan gelen aşağıdaki dosyalar önceki çeyreğe göre çok küçük; "
                    "büyük olasılıkla yalnızca mali tablo içeriyor. Bankanın sitesinden "
                    "denetim raporunu indirip R2'deki dosyanın üzerine yazın "
                    "(`kaynak_banka.json`'a eklemeyin).\n\n| Dosya | Yeni | Önceki çeyrek |\n|---|---|---|\n")
            for a, b, o in kisalar:
                f.write(f"| {a} | {b/1048576:.1f} MB | {o/1048576:.1f} MB |\n")
    if eklenen and not args.uygula:
        print("\n(kuru çalıştırma — R2'ye yazmak için --uygula)")

    # GitHub Actions adımları arasında karar için
    ozet = os.environ.get("GITHUB_OUTPUT")
    if ozet:
        with open(ozet, "a") as f:
            f.write(f"yeni={len(eklenen)}\n")
            f.write("liste=" + "; ".join(a for a, _ in eklenen[:20]) + "\n")
            f.write(f"kisa={len(kisalar)}\n")


if __name__ == "__main__":
    main()
