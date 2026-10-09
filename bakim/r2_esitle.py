#!/usr/bin/env python3
"""R2'deki yayımlanmış arşivi kayan pencereye eşitler.

Pencere kuralı manifest_uret.py ile aynıdır: en yeni dönemin yılı dahil son
PENCERE_YIL takvim yılı. Script iki yönde de çalışır:

  * pencere içinde olup R2'de olmayan dosyaları yükler (dönem değil, DOSYA
    bazında: bir dönem R2'de var diye içindeki eksik dosyalar atlanmaz)
  * pencereden düşmüş dönemleri R2'den siler (yerel kopyalar korunur)

Böylece her çeyrek yeni raporlar indirildiğinde site elle güncellenmeden
"son N yıl" kalır ve R2 ücretsiz kotası (10 GB) aşılmaz.

Varsayılan olarak yalnızca planı yazdırır; uygulamak için --uygula gerekir.
Silme geri alınamaz olduğundan bilinçli bir onay adımı bırakılmıştır.

Kullanım:
  python3 r2_esitle.py              # ne yapılacağını göster
  python3 r2_esitle.py --uygula     # yükle + sil
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile

from manifest_uret import PENCERE_YIL, pencere_alt_siniri

from ayarlar import RAPORLAR as YEREL
UZAK = "r2:bdr-arsiv/raporlar"


def calistir(komut: list[str]) -> str:
    sonuc = subprocess.run(komut, capture_output=True, text=True)
    if sonuc.returncode != 0:
        sys.exit(f"komut başarısız: {' '.join(komut)}\n{sonuc.stderr.strip()}")
    return sonuc.stdout


def uzak_donemler() -> set[str]:
    cikti = calistir(["rclone", "lsf", UZAK, "--dirs-only"])
    return {s.strip("/ ") for s in cikti.splitlines() if s.strip()}


def yerel_donemler() -> set[str]:
    return {d for d in os.listdir(YEREL) if os.path.isdir(os.path.join(YEREL, d))}


# Arşive yalnızca <banka-slug>-<solo|konsolide>.<uzantı> adlı dosyalar girer;
# .DS_Store ve bankanın özgün dosya adıyla kalmış kopyalar yüklenmez.
ARSIV_ADI = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-(?:solo|konsolide)\.[a-z0-9]+$")
MIN_BOYUT = 1000


def uzak_dosyalar() -> set[str]:
    cikti = calistir(["rclone", "lsf", UZAK, "--recursive", "--files-only",
                      "--s3-no-check-bucket"])
    return {s.strip() for s in cikti.splitlines() if s.strip()}


def yerel_dosyalar(donemler: set[str]) -> tuple[set[str], list[str]]:
    """(arşive girecek dosyalar, adı kalıba uymayıp atlananlar)"""
    uygun, atlanan = set(), []
    for d in sorted(donemler):
        for ad in sorted(os.listdir(os.path.join(YEREL, d))):
            yol = os.path.join(YEREL, d, ad)
            if not os.path.isfile(yol) or ad.startswith("."):
                continue
            if ARSIV_ADI.match(ad) and os.path.getsize(yol) >= MIN_BOYUT:
                uygun.add(f"{d}/{ad}")
            else:
                atlanan.append(f"{d}/{ad}")
    return uygun, atlanan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uygula", action="store_true",
                    help="planı yazdırmakla kalmayıp gerçekten yükle ve sil")
    args = ap.parse_args()

    yerel = yerel_donemler()
    uzak = uzak_donemler()
    if not yerel:
        sys.exit(f"yerel arşiv boş: {YEREL}")

    min_yil = pencere_alt_siniri(yerel)
    pencere = {d for d in yerel if int(d.split("-")[0]) >= min_yil}

    yuklenecek = sorted(pencere - uzak)
    silinecek = sorted(uzak - pencere)

    yerel_dos, atlanan = yerel_dosyalar(pencere)
    eksik_dosya = sorted(yerel_dos - uzak_dosyalar())

    print(f"pencere      : son {PENCERE_YIL} yıl (>= {min_yil})")
    print(f"yerel dönem  : {len(yerel)}  |  pencere içi: {len(pencere)}  |  R2'de: {len(uzak)}")
    print(f"yüklenecek   : {yuklenecek or 'yok'}")
    print(f"silinecek    : {silinecek or 'yok'}")
    print(f"eksik dosya  : {len(eksik_dosya)}  (pencere içi dönemlerde yerelde olup R2'de olmayan)")
    for f in eksik_dosya:
        print(f"    + {f}")
    if atlanan:
        print(f"atlanan      : {len(atlanan)} dosya kalıba uymuyor (yüklenmez), ör. {atlanan[:3]}")

    if not args.uygula:
        if yuklenecek or silinecek or eksik_dosya:
            print("\n(yalnızca plan — uygulamak için: python3 r2_esitle.py --uygula)")
        return

    if eksik_dosya:
        print(f"\n{len(eksik_dosya)} eksik dosya yükleniyor")
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                         encoding="utf-8") as liste:
            liste.write("\n".join(eksik_dosya) + "\n")
        try:
            subprocess.run(["rclone", "copy", YEREL, UZAK, "--files-from", liste.name,
                            "--ignore-existing", "--s3-no-check-bucket", "--progress"],
                           check=True)
        finally:
            os.unlink(liste.name)

    for donem in silinecek:
        print(f"\nsiliniyor: {donem}  (yerel kopya {os.path.join(YEREL, donem)} korunur)")
        subprocess.run(["rclone", "purge", f"{UZAK}/{donem}",
                        "--s3-no-check-bucket"], check=True)

    print("\nR2 eşitlendi. Sırada: python3 manifest_uret.py "
          "ve üretilen JSON'u index.html içindeki #arsivManifest bloğuna göm.")


if __name__ == "__main__":
    main()
