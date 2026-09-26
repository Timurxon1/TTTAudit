# TTT Audit sayti: Node vidjetlarni yigʻadi, Python Django'ni xizmat qiladi.
FROM node:24-alpine AS widgets
WORKDIR /w
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.14-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 HOME=/home/app
# Standart prod rejimi: settings.py dagi xavfsizlik bloki (HSTS, xavfsiz cookie,
# CompressedManifestStaticFilesStorage) yoqiladi. `docker run -e DJANGO_DEBUG=...`
# bilan qayta yozish mumkin, lekin buni hech qachon 1 ga qoʻymang (README: Prod: muhim).
ENV DJANGO_DEBUG=0
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=widgets /backend/frontend ./frontend
# Statika build bosqichida yigʻiladi; bazasiz ishlashi uchun oʻrinbosar maxfiy kalit.
RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput
# Ilova root boʻlmagan `app` foydalanuvchisi bilan ishlaydi. Konteyner root sifatida boshlanadi:
# docker-entrypoint.sh faqat media volume egasini toʻgʻrilaydi va darhol `app` ga oʻtadi.
# `sed` — Windows'da CRLF bilan checkout qilingan boʻlsa ham skript ishlasin.
RUN useradd --create-home app && mkdir -p /app/media && chown -R app /app \
    && sed -i 's/\r$//' /app/docker-entrypoint.sh && chmod +x /app/docker-entrypoint.sh
CMD ["/app/docker-entrypoint.sh"]
