FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 DJANGO_DEBUG=0
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput \
    && useradd --create-home app \
    && mkdir -p /app/media \
    && chown -R app:app /app \
    && sed -i 's/\r$//' /app/docker-entrypoint.sh \
    && chmod +x /app/docker-entrypoint.sh

CMD ["/app/docker-entrypoint.sh"]
