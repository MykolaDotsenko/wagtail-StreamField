FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

RUN useradd --create-home app
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN DJANGO_SETTINGS_MODULE=mysite.settings.production \
    DJANGO_SECRET_KEY=build-only-static-assets-secret-key-please-replace-at-runtime-2026 \
    DJANGO_ALLOWED_HOSTS=localhost \
    DJANGO_CSRF_TRUSTED_ORIGINS=https://localhost \
    python manage.py collectstatic --noinput \
    && chown -R app:app /app

USER app
EXPOSE 8000

CMD ["sh", "-c", "exec gunicorn mysite.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --access-logfile - --error-logfile -"]
