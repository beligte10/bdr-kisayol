#!/usr/bin/env bash
# index.html değiştiyse commit + push eder, ardından Pages yayınını ister.
#
# BDDK ve banka işleri GitHub Actions'ta aynı anda çalışır; ikisi de main'e
# push edebilir. Sonra gelen push reddedilirse en güncel main alınır ve pano
# R2'den yeniden üretilir. Her iki işin yüklemeleri de R2'de olduğundan yeniden
# üretilen sayfa ikisini de içerir; elle birleştirme (merge) gerekmez.
#
# Kullanım: bash bakim/yayinla.sh "<commit mesajı>"
set -euo pipefail

mesaj="$1"
git config user.name  "bdr-bot"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"

for deneme in 1 2 3 4 5; do
  if git diff --quiet -- index.html; then
    echo "index.html değişmedi — yayınlanacak bir şey yok."
    exit 0
  fi
  git add index.html
  git commit -q -m "$mesaj"
  if git push origin HEAD:main; then
    # GITHUB_TOKEN ile yapılan push'un Pages yayınını başlatacağına
    # güvenmiyoruz; yayını açıkça istiyoruz.
    gh api -X POST "repos/$GITHUB_REPOSITORY/pages/builds" >/dev/null \
      && echo "Pages yayını istendi" \
      || echo "::warning::Pages yayını API ile istenemedi"
    exit 0
  fi
  echo "push reddedildi (deneme $deneme) — diğer iş önce yayınlamış, main yenileniyor"
  git fetch -q origin main
  git reset -q --hard origin/main
  python3 bakim/ceyrek_guncelle.py --sadece-yayinla
done

echo "::error::push 5 denemede başarısız"
exit 1
