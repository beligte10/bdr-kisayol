#!/usr/bin/env python3
"""R2'deki yayımlanmış arşivi kayan pencereye eşitler.

Pencere kuralı manifest_uret.py ile aynıdır: en yeni dönemin yılı dahil son
PENCERE_YIL takvim yılı. Script iki yönde de çalışır:

  * pencere içinde olup R2'de olmayan dönemleri yükler
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
import subprocess
import sys

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

    print(f"pencere      : son {PENCERE_YIL} yıl (>= {min_yil})")
    print(f"yerel dönem  : {len(yerel)}  |  pencere içi: {len(pencere)}  |  R2'de: {len(uzak)}")
    print(f"yüklenecek   : {yuklenecek or 'yok'}")
    print(f"silinecek    : {silinecek or 'yok'}")

    if not args.uygula:
        if yuklenecek or silinecek:
            print("\n(yalnızca plan — uygulamak için: python3 r2_esitle.py --uygula)")
        return

    for donem in yuklenecek:
        print(f"\nyükleniyor: {donem}")
        subprocess.run(["rclone", "copy", os.path.join(YEREL, donem),
                        f"{UZAK}/{donem}", "--s3-no-check-bucket", "--progress"],
                       check=True)

    for donem in silinecek:
        print(f"\nsiliniyor: {donem}  (yerel kopya {os.path.join(YEREL, donem)} korunur)")
        subprocess.run(["rclone", "purge", f"{UZAK}/{donem}",
                        "--s3-no-check-bucket"], check=True)

    print("\nR2 eşitlendi. Sırada: python3 manifest_uret.py "
          "ve üretilen JSON'u index.html içindeki #arsivManifest bloğuna göm.")


if __name__ == "__main__":
    main()
