#!/usr/bin/env python3
"""Bakım scriptlerinin ortak yolları.

Arşivin kendisi (~15 GB, 6400 dosya) depoya girmez; scriptler depoda durur,
veriyi dışarıdan bulur. Varsayılan konum ~/Desktop/BDR-Arsiv; başka bir diske
taşınırsa BDR_ARSIV ortam değişkeniyle gösterilebilir:

    BDR_ARSIV=/Volumes/Yedek/BDR-Arsiv python3 bakim/ceyrek_guncelle.py
"""
import os

DEPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARSIV_KOK = os.path.expanduser(os.environ.get("BDR_ARSIV", "~/Desktop/BDR-Arsiv"))

RAPORLAR = os.path.join(ARSIV_KOK, "raporlar")
MANIFEST = os.path.join(ARSIV_KOK, "manifest.json")
MANIFEST_MIN = os.path.join(ARSIV_KOK, "arsiv_manifest_min.json")
PANO = os.path.join(DEPO, "index.html")
