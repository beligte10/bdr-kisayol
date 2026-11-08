#!/usr/bin/env python3
"""R2 kotasını korur: yer yoksa en eski çeyreği bütünüyle siler.

Otomatik mod (GitHub Actions) yalnızca yükleme yapar; yerel arşivi olmadığı
için r2_esitle.py'nin kayan pencere silmesini çalıştıramaz. Bu modül olmadan
R2 her çeyrek büyür ve ücretsiz kota (10 GB) eninde sonunda aşılır.

Kural: yeni dosya kotayı aşacaksa en eski dönemin klasörü (o çeyreğin TÜM
bankaları) silinir, yer açılana kadar tekrarlanır. Tek tek dosya silinmez;
yarım kalmış bir çeyrek, arşiv seçicide bazı bankalarda kırık görünürdü.
En yeni dönem ve o an yükleme yapılan dönem hiçbir zaman silinmez. Silinen
çeyrekler yerel arşivde (~/Desktop/BDR-Arsiv) durmaya devam eder.

Kullanım:
  python3 bakim/kota.py            # doluluk ve ne silineceğini göster
  python3 bakim/kota.py --uygula   # gerekirse sil
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys

KOK = "r2:bdr-arsiv"
# Cloudflare R2 ücretsiz kotası 10 GB; ölçüm farklarına karşı pay bırakılır.
KOTA = 9_500_000_000


def _rclone(*argv: str) -> str:
    c = subprocess.run(["rclone", *argv], capture_output=True, text=True)
    if c.returncode != 0:
        sys.exit(f"rclone {' '.join(argv)} başarısız:\n{c.stderr.strip()}")
    return c.stdout


def toplam_boyut() -> int:
    return json.loads(_rclone("size", KOK, "--json"))["bytes"]


def donem_boyutu(donem: str) -> int:
    return json.loads(_rclone("size", f"{KOK}/raporlar/{donem}", "--json"))["bytes"]


def donemler() -> list[str]:
    return sorted(d.strip().rstrip("/") for d in
                  _rclone("lsf", f"{KOK}/raporlar", "--dirs-only").splitlines() if d.strip())


class Kota:
    """Bir çalıştırma boyunca doluluğu bellekte izler (her dosyada rclone size yok)."""

    def __init__(self, uygula: bool):
        self.uygula = uygula
        self.dolu = toplam_boyut()
        self.silinen: list[str] = []

    def yer_ac(self, gereken: int, korunan: set[str] = frozenset()) -> None:
        """`gereken` bayt sığana kadar en eski çeyrekleri siler."""
        while self.dolu + gereken > KOTA:
            liste = [d for d in donemler() if d not in self.silinen]
            adaylar = [d for d in liste[:-1] if d not in korunan]   # en yeni hep kalır
            if not adaylar:
                sys.exit("R2 kotası dolu ve silinebilecek eski çeyrek kalmadı — elle bakın")
            en_eski = adaylar[0]
            boyut = donem_boyutu(en_eski)
            print(f"  - kota: {en_eski} çeyreği siliniyor ({boyut/1e6:.0f} MB) "
                  f"[dolu {self.dolu/1e9:.2f} GB + gereken {gereken/1e6:.1f} MB > "
                  f"{KOTA/1e9:.1f} GB]", flush=True)
            if self.uygula:
                _rclone("purge", f"{KOK}/raporlar/{en_eski}")
            self.silinen.append(en_eski)
            self.dolu -= boyut

    def eklendi(self, boyut: int) -> None:
        self.dolu += boyut


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uygula", action="store_true", help="gerekirse gerçekten sil")
    ap.add_argument("--gereken", type=int, default=0, help="açılacak ek yer (bayt)")
    args = ap.parse_args()
    k = Kota(args.uygula)
    print(f"R2 doluluk : {k.dolu/1e9:.2f} GB / {KOTA/1e9:.1f} GB "
          f"(boş: {(KOTA - k.dolu)/1e6:.0f} MB)")
    k.yer_ac(args.gereken)
    if not k.silinen:
        print("silinecek çeyrek yok")
    elif not args.uygula:
        print("(kuru çalıştırma — silmek için --uygula)")


if __name__ == "__main__":
    main()
