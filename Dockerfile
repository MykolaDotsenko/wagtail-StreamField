FROM python:3.13-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --system domonest \
    && useradd --system --gid domonest --create-home domonest

WORKDIR /app

RUN apt-get update --yes --quiet \
    && apt-get install --yes --quiet --no-install-recommends \
        libjpeg62-turbo \
        libwebp7 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY --chown=domonest:domonest . .

RUN DJANGO_SETTINGS_MODULE=mysite.settings.dev \
    python manage.py collectstatic --noinput --clear

USER domonest

EXPOSE 8000

CMD ["gunicorn", "mysite.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-"]
