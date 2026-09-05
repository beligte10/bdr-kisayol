#!/usr/bin/env python3
"""R2'ye bakan kart butonlarını arşivdeki en yeni döneme ilerletir.

BDDK katmanı arşivi büyütür, ama kartın ön yüzü (dönem rozeti ve Solo/Konsolide
butonlarının adresi) ayrı bir bilgidir. Butonu bankanın kendi sitesine bakan
kartlar elle güncellenmek zorunda; buna karşılık butonu R2'ye bakan her buton
tamamen manifestten türetilebilir, dolayısıyla otomatik ilerletilebilir.

Kartların bir kısmı karma: örneğin Solo bankanın sitesinden, Konsolide R2'den
gelir. Bu durum, BDDK o dönemde yalnızca birini yayımladığında ortaya çıkıyor
ve R2 butonu eski dönemde takılı kalıyor. Bu yüzden ilerletme kart bazında
değil **buton bazında** yapılır.

Dönem rozeti yalnızca kartın bütün butonları R2'ye bakıyorsa ve hepsi aynı yeni
döneme taşınmışsa güncellenir; karma kartlarda rozet zaten banka sitesindeki
güncel dönemi gösterdiği için ona dokunulmaz.
"""
from __future__ import annotations

import argparse
import json
import re

from ayarlar import PANO

ONEK = "https://bdr-arsiv.bdr-arsiv-worker.workers.dev/raporlar/"


def rozet(donem: str) -> str:
    yil, ce = donem.split("-")
    return f"{yil}/{ce.replace('C', 'Ç')}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uygula", action="store_true", help="index.html'i gerçekten yaz")
    args = ap.parse_args()

    sayfa = open(PANO, encoding="utf-8").read()
    veri = json.loads(re.search(r'id="arsivManifest">(.*?)</script>', sayfa, re.S).group(1))

    def en_yeni_donem(banka: str, tip: str, sonra: str) -> str | None:
        harf = "s" if tip == "solo" else "k"
        uygun = [d for d, kod in veri["a"].get(banka, {}).items()
                 if harf in kod and d > sonra]
        return max(uygun) if uygun else None

    ilerleyen, rozet_degisen = [], []
    parcalar, son = [], 0

    for m in re.finditer(r'data-bank="([^"]+)"(.*?)(?=<div class="card|\Z)', sayfa, re.S):
        ad, govde = m.group(1), m.group(2)
        if ad not in veri["a"]:
            continue

        butonlar = [t.group(0) for t in re.finditer(r"<a\b[^>]*>", govde)
                    if 'class="pill' in t.group(0)]
        r2_butonlar = [b for b in butonlar if ONEK in b]
        if not r2_butonlar:
            continue

        yeni_govde, tasinan = govde, {}
        for buton in r2_butonlar:
            url = re.search(r'href="([^"]+)"', buton).group(1)
            kuyruk = url[len(ONEK):]
            donem, dosya = kuyruk.split("/", 1)
            tip = "konsolide" if "-konsolide." in dosya else "solo"
            hedef = en_yeni_donem(ad, tip, donem)
            if not hedef:
                continue
            anahtar = f"{hedef}/{veri['slug'][ad]}-{tip}"
            yeni_url = ONEK + anahtar + "." + veri["ext"].get(anahtar, "pdf")
            yeni_govde = yeni_govde.replace(url, yeni_url)
            tasinan[tip] = (donem, hedef)
            ilerleyen.append((ad, tip, donem, hedef))

        if not tasinan:
            continue

        # rozet: yalnızca bütün butonlar R2'de ve hepsi aynı yeni dönemdeyse
        if len(r2_butonlar) == len(butonlar) and len(tasinan) == len(butonlar):
            hedefler = {h for _, h in tasinan.values()}
            rz = re.search(r'class="donem-badge">([^<]+)<', yeni_govde)
            if len(hedefler) == 1 and rz:
                yeni = rozet(hedefler.pop())
                if rz.group(1) != yeni:
                    yeni_govde = yeni_govde.replace(
                        f'class="donem-badge">{rz.group(1)}<',
                        f'class="donem-badge">{yeni}<')
                    rozet_degisen.append((ad, rz.group(1), yeni))

        parcalar.append(sayfa[son:m.start(2)])
        parcalar.append(yeni_govde)
        son = m.end(2)

    parcalar.append(sayfa[son:])

    for ad, tip, e, y in ilerleyen:
        print(f"  ^ {ad} {tip}: {e} -> {y}")
    for ad, e, y in rozet_degisen:
        print(f"  * {ad} rozeti: {e} -> {y}")
    print(f"\nilerletilen buton: {len(ilerleyen)} | rozet: {len(rozet_degisen)}")

    if ilerleyen and args.uygula:
        open(PANO, "w", encoding="utf-8").write("".join(parcalar))
        print("index.html güncellendi")
    elif ilerleyen:
        print("(kuru çalıştırma — yazmak için --uygula)")


if __name__ == "__main__":
    main()
