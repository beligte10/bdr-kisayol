#!/usr/bin/env python3
"""Çeyreklik bakımın tamamını tek komutta yürütür.

Adımlar:
  1. BDDK'dan yeni raporları indir
  2. R2'yi kayan pencereyle eşitle (yeniyi yükle, pencereden düşeni sil)
  3. Sıkıştırılmış manifesti üret
  4. Manifesti index.html'e göm
  5. Doğrula: div dengesi, manifest ile R2 örtüşmesi, örnek link kontrolü

Manifesti elle kopyalayıp yapıştırma adımı sistemdeki en hata açık yerdi;
4. adım onu ortadan kaldırıyor. Yazma ve silme yapan adımlar --uygula
verilmedikçe çalışmaz, öncesinde yalnızca ne olacağı yazdırılır.

Kullanım:
  python3 bakim/ceyrek_guncelle.py --yil 2026            # kuru çalıştırma
  python3 bakim/ceyrek_guncelle.py --yil 2026 --uygula
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request

from ayarlar import DEPO, MANIFEST_MIN, PANO

BAKIM = os.path.dirname(os.path.abspath(__file__))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0"


def baslik(n: int, metin: str) -> None:
    print(f"\n{'='*60}\n{n}. {metin}\n{'='*60}", flush=True)


def adim(*argv: str) -> None:
    subprocess.run([sys.executable, os.path.join(BAKIM, argv[0]), *argv[1:]], check=True)


def manifesti_göm() -> tuple[int, int]:
    """Üretilen manifesti index.html'deki JSON bloğuyla değiştirir."""
    yeni = open(MANIFEST_MIN, encoding="utf-8").read()
    sayfa = open(PANO, encoding="utf-8").read()
    kalip = re.compile(r'(<script type="application/json" id="arsivManifest">)(.*?)(</script>)', re.S)
    m = kalip.search(sayfa)
    if not m:
        sys.exit("index.html içinde #arsivManifest bloğu bulunamadı")
    eski = len(m.group(2))
    sayfa = sayfa[:m.start(2)] + yeni + sayfa[m.end(2):]
    open(PANO, "w", encoding="utf-8").write(sayfa)
    return eski, len(yeni)


def dogrula() -> bool:
    sayfa = open(PANO, encoding="utf-8").read()
    sorun = []

    ac, kap = len(re.findall(r"<div\b", sayfa)), sayfa.count("</div>")
    print(f"div dengesi        : {ac}/{kap}")
    if ac != kap:
        sorun.append("div dengesi bozuk")

    veri = json.loads(re.search(r'id="arsivManifest">(.*?)</script>', sayfa, re.S).group(1))
    donemler = sorted({d for v in veri["a"].values() for d in v})
    print(f"manifest           : {len(veri['a'])} banka, {len(donemler)} dönem "
          f"({donemler[0]} .. {donemler[-1]})")

    # yıl seçenekleri manifestten üretiliyor; sabit <option> kalmamalı
    if re.search(r'<option value="20\d\d">', sayfa):
        sorun.append("index.html'de sabit yıl <option> kalmış")

    # her linkin R2'de karşılığı var mı
    beklenen = set()
    for ad, v in veri["a"].items():
        for donem, kod in v.items():
            for harf, tip in (("s", "solo"), ("k", "konsolide")):
                if harf in kod:
                    k = f"{donem}/{veri['slug'][ad]}-{tip}"
                    beklenen.add("raporlar/" + k + "." + veri["ext"].get(k, "pdf"))
    cikti = subprocess.run(["rclone", "lsf", "r2:bdr-arsiv", "--recursive", "--files-only"],
                           capture_output=True, text=True)
    r2 = {s.strip() for s in cikti.stdout.splitlines() if s.strip()}
    eksik = beklenen - r2
    print(f"arşiv linki        : {len(beklenen)}  |  R2'de bulunmayan: {len(eksik)}")
    if eksik:
        sorun.append(f"{len(eksik)} link R2'de yok, ör. {sorted(eksik)[:3]}")

    # sayfadaki doğrudan R2 linkleri gerçekten açılıyor mu
    dogrudan = sorted(set(re.findall(r'href="(https://bdr-arsiv[^"]+)"', sayfa)))
    kirik = []
    for u in dogrudan:
        istek = urllib.request.Request(u, method="HEAD", headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(istek, timeout=30) as y:
                if y.status != 200:
                    kirik.append(u)
        except Exception:
            kirik.append(u)
    print(f"doğrudan R2 linki  : {len(dogrudan)}  |  açılmayan: {len(kirik)}")
    if kirik:
        sorun.append(f"{len(kirik)} doğrudan link açılmıyor, ör. {kirik[:2]}")

    if sorun:
        print("\nSORUN:")
        for s in sorun:
            print("  -", s)
        return False
    print("\nTüm kontroller geçti.")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yil", nargs="+", type=int, required=True,
                    help="indirilecek yıl(lar), ör. --yil 2026")
    ap.add_argument("--uygula", action="store_true",
                    help="indir/yükle/sil/göm adımlarını gerçekten çalıştır")
    args = ap.parse_args()
    yillar = [str(y) for y in args.yil]

    if not args.uygula:
        print("KURU ÇALIŞTIRMA — hiçbir şey değiştirilmeyecek\n")
        baslik(1, "BDDK indirmesi (atlandı)")
        print(f"  çalıştırılacak: bdr_indir.py --yil {' '.join(yillar)}")
        baslik(2, "R2 eşitleme planı")
        adim("r2_esitle.py")
        baslik(3, "Manifest üretimi")
        adim("manifest_uret.py")
        print("\nUygulamak için: python3 bakim/ceyrek_guncelle.py "
              f"--yil {' '.join(yillar)} --uygula")
        return

    baslik(1, "BDDK'dan yeni raporları indir")
    adim("bdr_indir.py", "--yil", *yillar)

    baslik(2, "R2'yi kayan pencereyle eşitle")
    adim("r2_esitle.py", "--uygula")

    baslik(3, "Manifesti üret")
    adim("manifest_uret.py")

    baslik(4, "Manifesti index.html'e göm")
    eski, yeni = manifesti_göm()
    print(f"gömülü manifest: {eski/1024:.0f} KB -> {yeni/1024:.0f} KB")

    baslik(5, "Doğrula")
    if not dogrula():
        sys.exit("\nDoğrulama başarısız — commit etmeyin, önce sorunları giderin.")

    print(f"\nHazır. Değişiklikleri gözden geçirip commit'leyin:\n"
          f"  cd {DEPO!r} && git diff --stat && git add -A && git commit && git push")


if __name__ == "__main__":
    main()
