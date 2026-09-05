#!/usr/bin/env python3
"""
BDDK Bağımsız Denetim Raporu arşivleyici.

BDDK'nın düzenli dosya adı kalıbını kullanarak seçilen dönemlerin
Solo/Konsolide raporlarını indirir, zip içinden PDF'i çıkarır ve
  raporlar/<yil>-<ceyrek>/<banka-slug>-<solo|konsolide>.pdf
şeklinde diziler. Ayrıca panonun okuyabileceği manifest.json üretir.

Kullanım:
  python3 bdr_indir.py --yil 2026                # tek yıl
  python3 bdr_indir.py --yil 2022 2023 2024 2025 2026
  python3 bdr_indir.py --yil 2026 --sadece-ilk20 # yalnız ilk 20 banka

Yeniden çalıştırılabilir: mevcut dosyalar atlanır (resume).
"""
from __future__ import annotations

import argparse, glob, io, json, os, re, sys, time, unicodedata, zipfile
import urllib.parse, urllib.request

from ayarlar import ARSIV_KOK as KOK, RAPORLAR as CIKTI
BDDK = "https://www.bddk.org.tr/BdrUyg/Home/DosyaIndir?raporUrl=~%2FDosya%2F"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# banka adı -> BDDK EFT kodu (BDDK portalından alındı)
BANKALAR = {
    "Kuveyt Türk":"205","Vakıf Katılım":"210","Ziraat Katılım":"209","Albaraka":"203",
    "Türkiye Finans":"206","Emlak Katılım":"211","Dünya Katılım":"214","Hayat Finans":"212",
    "TOM Bank":"213","Ziraat Bankası":"010","VakıfBank":"015","İş Bankası":"064",
    "Halkbank":"012","Garanti BBVA":"062","Yapı Kredi":"067","Akbank":"046","QNB":"111",
    "DenizBank":"134","TEB":"032","HSBC":"123","ING":"099","Enpara":"157","Şekerbank":"059",
    "Fibabanka":"103","Anadolubank":"135","Burgan Bank":"125","Odeabank":"146",
    "Alternatif Bank":"124","Citibank":"092","ICBC Turkey":"109","MUFG Bank Turkey":"147",
    "Deutsche Bank":"115","Arap Türk Bankası":"091","Turkland Bank":"108",
    "Bank of China Turkey":"149","Ziraat Dinamik":"160","Colendi Bank":"158","Rabobank":"137",
    "Bank Mellat":"094","Société Générale":"122","Turkish Bank":"096","Türk Eximbank":"016",
    "İller Bankası":"004","TSKB":"014","Takasbank":"132","Kalkınma Bankası":"017",
    "Aktif Bank":"143","Nurol Yatırım Bankası":"141","Destek Yatırım Bankası":"152",
    "Golden Global Bank":"150","Q Yatırım Bankası":"155","PashaBank":"116","Tera Bank":"154",
    "D Yatırım Bankası":"151","Misyon Bank":"153","Bank of America Yatırım Bank":"129",
    "Hedef Yatırım Bankası":"156","GSD Yatırım Bankası":"139","BankPozitif":"142",
    "Standard Chartered":"121","Diler Yatırım Bankası":"138","Aytemiz Yatırım Bankası":"161",
    "Birleşik Fon Bankası":"029","Intesa Sanpaolo":"148","JPMorgan Chase":"098",
    "Türk Ticaret Bankası":"060",
}

ILK20 = ["Ziraat Bankası","VakıfBank","Halkbank","İş Bankası","Garanti BBVA","Akbank",
         "Yapı Kredi","DenizBank","QNB","Kuveyt Türk","Vakıf Katılım","Ziraat Katılım",
         "TEB","Emlak Katılım","Albaraka","Türkiye Finans","Enpara","HSBC","ING","Fibabanka"]

AYLAR = [3, 6, 9, 12]          # çeyrek sonları
CEYREK = {3: "1C", 6: "2C", 9: "3C", 12: "4C"}


def slug(s: str) -> str:
    d = {"ı":"i","İ":"i","ş":"s","Ş":"s","ğ":"g","Ğ":"g","ü":"u","Ü":"u",
         "ö":"o","Ö":"o","ç":"c","Ç":"c","é":"e","è":"e"}
    s = "".join(d.get(ch, ch) for ch in s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def indir(url: str, timeout=120) -> bytes | None:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA, "Referer": "https://www.bddk.org.tr/BdrUyg/"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def _pdf_kirp(veri: bytes) -> bytes | None:
    """Baştaki olası dolgu baytlarını atarak PDF'i döndürür.

    Bazı ağ katmanları (vekil sunucular) yanıtın başına birkaç bayt ekleyebiliyor;
    bu durumda dosya %PDF yerine başka baytlarla başlar.
    """
    if veri[:4] == b"%PDF":
        return veri
    i = veri.find(b"%PDF", 0, 512)
    return veri[i:] if i > 0 else None


def belge_cikar(ham: bytes, derinlik: int = 0) -> tuple[bytes, str] | tuple[None, None]:
    """Zip içinden rapor belgesini çıkarır.

    PDF varsa PDF döner. Eski dönem (2005-2008) arşivlerinde rapor PDF
    değil Word/Excel/taranmış görüntü (.doc/.xls/.tif/.mdi) hatta .rar
    gibi farklı formatlarda olabilir; banka banka değişiyor. Bu yüzden
    PDF ve iç içe zip aramasından sonra, kalan dosyalar arasında en
    büyüğü (küçük dosyalar genelde ek/dizin bilgisi olur) formatı ne
    olursa olsun kendi uzantısıyla olduğu gibi kaydedilir.
    """
    if derinlik > 3:
        return None, None
    i = ham.find(b"PK\x03\x04")
    if i < 0:
        pdf = _pdf_kirp(ham)
        return (pdf, "pdf") if pdf else (None, None)
    try:
        z = zipfile.ZipFile(io.BytesIO(ham[i:]))
    except Exception:
        return None, None
    isimler = [n for n in z.namelist() if not n.endswith("/")]
    if not isimler:
        return None, None

    pdf_adaylar = [n for n in isimler if n.lower().endswith(".pdf")]
    if pdf_adaylar:
        ad = max(pdf_adaylar, key=lambda n: z.getinfo(n).file_size)
        try:
            return _pdf_kirp(z.read(ad)), "pdf"
        except Exception:
            pass

    # PDF bulunamadıysa iç içe zip olabilir (2005-2007 dönemi arşivlerinde görülüyor)
    zip_adaylar = [n for n in isimler if n.lower().endswith(".zip")]
    for ad in sorted(zip_adaylar, key=lambda n: -z.getinfo(n).file_size):
        try:
            ic_ham = z.read(ad)
        except Exception:
            continue
        veri, uzanti = belge_cikar(ic_ham, derinlik + 1)
        if veri:
            return veri, uzanti

    # Hâlâ yoksa: kalan en büyük dosyayı formatı ne olursa olsun olduğu gibi al
    diger = [n for n in isimler if not n.lower().endswith(".zip")]
    if diger:
        ad = max(diger, key=lambda n: z.getinfo(n).file_size)
        uzanti = re.sub(r"[^a-z0-9]", "", ad.rsplit(".", 1)[-1].lower()) if "." in ad else ""
        uzanti = uzanti or "bin"
        try:
            return z.read(ad), uzanti
        except Exception:
            pass
    return None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yil", nargs="+", type=int, required=True)
    ap.add_argument("--sadece-ilk20", action="store_true")
    ap.add_argument("--bankalar", nargs="+", help="yalnız bu bankalar (tam ad)")
    ap.add_argument("--bekleme", type=float, default=0.6, help="istekler arası saniye")
    args = ap.parse_args()

    bankalar = {k: v for k, v in BANKALAR.items() if not args.sadece_ilk20 or k in ILK20}
    if args.bankalar:
        eksik = [b for b in args.bankalar if b not in BANKALAR]
        if eksik:
            sys.exit(f"Tanınmayan banka: {eksik}")
        bankalar = {k: v for k, v in BANKALAR.items() if k in args.bankalar}
    manifest_yolu = os.path.join(KOK, "manifest.json")
    manifest = json.load(open(manifest_yolu, encoding="utf-8")) if os.path.exists(manifest_yolu) else {}

    ind = atla = yok = hata = 0
    toplam_bayt = 0
    t0 = time.time()

    for yil in args.yil:
        for ay in sorted(AYLAR, reverse=True):
            donem = f"{yil}-{CEYREK[ay]}"
            klasor = os.path.join(CIKTI, donem)
            for ad, kod in bankalar.items():
                for tip in ("SOLO", "KONSOLIDE"):
                    taban = os.path.join(klasor, f"{slug(ad)}-{tip.lower()}")
                    anahtar = f"{donem}/{slug(ad)}/{tip.lower()}"
                    mevcut = glob.glob(taban + ".*")
                    mevcut = [p for p in mevcut if os.path.getsize(p) > 1000]
                    if mevcut:
                        manifest[anahtar] = os.path.relpath(mevcut[0], KOK)
                        atla += 1
                        continue
                    dosya = f"BDREki-{kod}-{tip}-{yil}-{ay:02d}.zip"
                    ham = indir(BDDK + urllib.parse.quote(dosya))
                    time.sleep(args.bekleme)          # BDDK'yı yormamak için
                    if not ham or len(ham) < 1000 or b"PK\x03\x04" not in ham[:4096]:
                        yok += 1        # o dönem/tip için rapor yayımlanmamış (BDDK hata sayfası döner)
                        continue
                    belge, uzanti = belge_cikar(ham)
                    if not belge:
                        hata += 1
                        print(f"  ! Belge çıkarılamadı: {ad} {donem} {tip}", file=sys.stderr)
                        continue
                    hedef = f"{taban}.{uzanti}"
                    os.makedirs(klasor, exist_ok=True)
                    with open(hedef, "wb") as f:
                        f.write(belge)
                    manifest[anahtar] = os.path.relpath(hedef, KOK)
                    ind += 1
                    toplam_bayt += len(belge)
            print(f"{donem}: indirilen={ind} atlanan={atla} yok={yok} hata={hata} "
                  f"boyut={toplam_bayt/1048576:.0f} MB  ({time.time()-t0:.0f} sn)", flush=True)
            json.dump(manifest, open(manifest_yolu, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1, sort_keys=True)

    print(f"\nBitti. indirilen={ind} atlanan={atla} bulunamayan={yok} hata={hata}")
    print(f"Toplam yeni veri: {toplam_bayt/1048576:.1f} MB | manifest: {manifest_yolu}")


if __name__ == "__main__":
    main()
