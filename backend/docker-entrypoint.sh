#!/bin/sh
# Konteyner ishga tushishi: migratsiya, boshlangʻich maʼlumot, gunicorn.
#
# Railway (va boshqa platformalar) volume'ni root egaligida ulaydi — root boʻlmagan `app`
# foydalanuvchisi media/ ga yoza olmaydi. Shu sababli skript root sifatida boshlanadi, faqat
# media papkasining egasini toʻgʻrilaydi va qolgan hamma narsani `app` sifatida bajaradi.
set -e

MEDIA_DIR="${DJANGO_MEDIA_ROOT:-/app/media}"

if [ "$(id -u)" = "0" ]; then
    command -v setpriv >/dev/null || { echo "setpriv topilmadi (util-linux kerak)" >&2; exit 1; }
    mkdir -p "$MEDIA_DIR"
    if [ "$(stat -c %U "$MEDIA_DIR")" != "app" ]; then
        chown -R app:app "$MEDIA_DIR"
    fi
    exec setpriv --reuid=app --regid=app --init-groups "$0" "$@"
fi

python manage.py migrate --noinput
python manage.py createcachetable
# Uchalasi ham takroriy ishga tushishda admin tahrirlarini oʻchirmaydi (README: Boshlangʻich maʼlumot)
python manage.py seed_content
python manage.py import_tttaudit
python manage.py sync_site_content
# PostgreSQL yozuvlari saqlanib, yangi container media papkasi bo'sh kelganda
# repositorydagi nashr aktivlarini bazadagi mavjud yo'llar bo'yicha qayta tiklaydi.
python manage.py sync_media

# `exec` — gunicorn PID 1 boʻladi va SIGTERM'ni toʻgʻridan-toʻgʻri oladi
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-3}" \
    --timeout 120 \
    --access-logfile -
