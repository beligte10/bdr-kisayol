#!/usr/bin/env python3
"""Kart butonlarını arşivdeki en yeni döneme ilerletir, bekleme rozetlerini yönetir.

BDDK katmanı arşivi büyütür, ama kartın ön yüzü (dönem rozeti ve Solo/Konsolide
butonlarının adresi) ayrı bir bilgidir. Bu script onu manifestten türetir:

* Buton R2'ye bakıyorsa dönemi URL'den okunur; bankanın kendi sitesine
  bakıyorsa kartın rozetindeki dönemde sayılır. Arşivde o tip için daha yeni
  bir dönem varsa buton R2'deki kopyaya çevrilir. Böylece bankanın sitesine
  bakan kartlar da BDDK yayımlar yayımlamaz ilerler; aksi halde elle
  güncellenene kadar eski çeyrekte takılı kalıyorlardı.
* İlerletme kart bazında değil **buton bazında** yapılır: BDDK bir dönemde
  yalnızca Solo'yu yayımladıysa Konsolide eski dönemde kalır.
* Dönem rozeti, kartın bütün butonları aynı yeni döneme ulaştığında güncellenir.
* Güncel dönem manifestteki en yeni dönemdir. Rozeti bunun gerisinde kalan
  kartlara "⏳ NÇ bekleniyor" rozeti konur, yetişen karttan kaldırılır; sayfanın
  üstündeki kapsam şeridi bu rozeti sayar.
"""
from __future__ import annotations

import argparse
import json
import re

from ayarlar import PANO

ONEK = "https://bdr-arsiv.bdr-arsiv-worker.workers.dev/raporlar/"
AY = {"1C": "Mart", "2C": "Haziran", "3C": "Eylül", "4C": "Aralık"}


def rozet(donem: str) -> str:
    yil, ce = donem.split("-")
    return f"{yil}/{ce.replace('C', 'Ç')}"


def rozetten(metin: str) -> str:
    yil, ce = metin.strip().split("/")
    return f"{yil}-{ce.replace('Ç', 'C')}"


def bekleme_rozeti(donem: str) -> str:
    yil, ce = donem.split("-")
    return (f'<span class="pending-badge" title="{rozet(donem)} ({AY[ce]} {yil}) raporu '
            f'henüz yayınlanmadı">⏳ {ce.replace("C", "Ç")} bekleniyor</span>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uygula", action="store_true", help="index.html'i gerçekten yaz")
    args = ap.parse_args()

    sayfa = open(PANO, encoding="utf-8").read()
    veri = json.loads(re.search(r'id="arsivManifest">(.*?)</script>', sayfa, re.S).group(1))
    guncel = max(d for v in veri["a"].values() for d in v)

    def en_yeni_donem(banka: str, tip: str, sonra: str) -> str | None:
        harf = "s" if tip == "solo" else "k"
        uygun = [d for d, kod in veri["a"].get(banka, {}).items()
                 if harf in kod and d > sonra]
        return max(uygun) if uygun else None

    ilerleyen, rozet_degisen, bekleme = [], [], {"eklenen": 0, "kaldirilan": 0}
    parcalar, son = [], 0

    for m in re.finditer(r'data-bank="([^"]+)"(.*?)(?=<div class="card|\Z)', sayfa, re.S):
        ad, govde = m.group(1), m.group(2)
        rz = re.search(r'class="donem-badge">([^<]+)</span>', govde)
        if ad not in veri["a"] or not rz:
            continue
        kart_donemi = rozetten(rz.group(1))

        yeni_govde, buton_donemleri = govde, []
        for a in re.finditer(r'<a\b[^>]*class="pill[^"]*"[^>]*>(.*?)</a>', govde, re.S):
            etiket, yazi = a.group(0), re.sub(r"<[^>]+>", "", a.group(1)).strip().lower()
            url = re.search(r'href="([^"]+)"', etiket).group(1)
            if url.startswith(ONEK):
                donem, dosya = url[len(ONEK):].split("/", 1)
                tip = "konsolide" if "-konsolide." in dosya else "solo"
            else:
                donem = kart_donemi
                tip = ("konsolide" if yazi.startswith("konsolide") or "pill-alt" in etiket
                       else "solo")
            hedef = en_yeni_donem(ad, tip, donem)
            if hedef:
                anahtar = f"{hedef}/{veri['slug'][ad]}-{tip}"
                yeni_url = ONEK + anahtar + "." + veri["ext"].get(anahtar, "pdf")
                yeni_govde = yeni_govde.replace(f'href="{url}"', f'href="{yeni_url}"', 1)
                ilerleyen.append((ad, tip, donem, hedef))
                donem = hedef
            buton_donemleri.append(donem)

        # rozet: bütün butonlar aynı, daha yeni döneme ulaştıysa
        yeni_donem = kart_donemi
        if buton_donemleri and len(set(buton_donemleri)) == 1 and buton_donemleri[0] > kart_donemi:
            yeni_donem = buton_donemleri[0]
            yeni_govde = yeni_govde.replace(rz.group(0),
                                            f'class="donem-badge">{rozet(yeni_donem)}</span>', 1)
            rozet_degisen.append((ad, rz.group(1), rozet(yeni_donem)))

        # bekleme rozeti: güncel dönemin gerisindeki kartlarda olmalı, diğerlerinde olmamalı
        bekleyen = re.search(r'\s*<span class="pending-badge".*?</span>', yeni_govde, re.S)
        if yeni_donem < guncel:
            dogru = bekleme_rozeti(guncel)
            if not bekleyen:
                yer = re.search(r'class="donem-badge">[^<]+</span>', yeni_govde)
                yeni_govde = yeni_govde[:yer.end()] + dogru + yeni_govde[yer.end():]
                bekleme["eklenen"] += 1
            elif bekleyen.group(0).strip() != dogru:
                yeni_govde = yeni_govde.replace(bekleyen.group(0), dogru, 1)
                bekleme["eklenen"] += 1
        elif bekleyen:
            yeni_govde = yeni_govde.replace(bekleyen.group(0), "", 1)
            bekleme["kaldirilan"] += 1

        if yeni_govde != govde:
            parcalar.append(sayfa[son:m.start(2)])
            parcalar.append(yeni_govde)
            son = m.end(2)

    parcalar.append(sayfa[son:])

    for ad, tip, e, y in ilerleyen:
        print(f"  ^ {ad} {tip}: {e} -> {y}")
    for ad, e, y in rozet_degisen:
        print(f"  * {ad} rozeti: {e} -> {y}")
    print(f"\ngüncel dönem: {rozet(guncel)}")
    print(f"ilerletilen buton: {len(ilerleyen)} | rozet: {len(rozet_degisen)} | "
          f"bekleme rozeti eklenen/düzeltilen: {bekleme['eklenen']}, kaldırılan: {bekleme['kaldirilan']}")

    yeni_sayfa = "".join(parcalar)
    if yeni_sayfa != sayfa and args.uygula:
        open(PANO, "w", encoding="utf-8").write(yeni_sayfa)
        print("index.html güncellendi")
    elif yeni_sayfa != sayfa:
        print("(kuru çalıştırma — yazmak için --uygula)")


if __name__ == "__main__":
    main()
