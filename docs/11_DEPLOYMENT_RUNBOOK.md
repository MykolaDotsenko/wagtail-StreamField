# Deployment Runbook

This runbook defines the production baseline implemented by PR12.

## Runtime

- Python 3.12–3.14 are exercised in the main CI matrix.
- Django 5.2.17.
- Wagtail 7.4.3.
- Gunicorn is the WSGI process server.
- PostgreSQL is the production database target.
- WhiteNoise serves fingerprinted static assets only.
- Wagtail media must live on persistent/shared storage; WhiteNoise is not a media storage solution.

## Required production environment

```text
DJANGO_SETTINGS_MODULE=mysite.settings.production
DJANGO_SECRET_KEY=<strong-random-secret>
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
WAGTAILADMIN_BASE_URL=https://example.com

POSTGRES_DB=domonest
POSTGRES_USER=domonest
POSTGRES_PASSWORD=<database-password>
POSTGRES_HOST=<database-host>
POSTGRES_PORT=5432
POSTGRES_CONN_MAX_AGE=60
```

Optional hardening:

```text
DJANGO_TRUST_X_FORWARDED_PROTO=true
DJANGO_MEDIA_ROOT=/persistent/media
DJANGO_SECURE_HSTS_SECONDS=3600
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=false
DJANGO_SECURE_HSTS_PRELOAD=false
```

Only enable `DJANGO_TRUST_X_FORWARDED_PROTO` when the application is behind a trusted proxy that correctly overwrites `X-Forwarded-Proto`.

## Build / release sequence

```bash
python -m pip install -r requirements.txt
python manage.py check --deploy
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

Application start:

```bash
gunicorn mysite.wsgi:application --bind 0.0.0.0:${PORT:-8000}
```

## Health / readiness

`GET /health/` performs a minimal database round trip.

Healthy:

```json
{"status":"ok"}
```

Database unavailable:

```json
{"status":"unavailable"}
```

The endpoint intentionally does not expose exception text, database names or connection details and sends `Cache-Control: no-store`.

## Static files

Production uses:

```text
whitenoise.storage.CompressedManifestStaticFilesStorage
```

WhiteNoise middleware runs directly after Django `SecurityMiddleware`.

Official reference:
- https://whitenoise.readthedocs.io/en/stable/django.html

## Media files

Wagtail images/documents are user/editor-generated media and must be persistent.

Single-instance deployment:
- a durable mounted volume may back `MEDIA_ROOT`.

Multiple instances / ephemeral hosts:
- configure a shared provider-backed Django storage backend.

Do not serve uploaded media through WhiteNoise.

Wagtail storage reference:
- https://docs.wagtail.org/en/stable/advanced_topics/images/image_file_formats.html
- https://docs.djangoproject.com/en/5.2/ref/files/storage/

## PostgreSQL

The application switches from SQLite to PostgreSQL when `POSTGRES_DB` is present. PR12 CI runs the full Django test suite against PostgreSQL in addition to the regular SQLite/Python matrix.

Django database reference:
- https://docs.djangoproject.com/en/5.2/ref/databases/#postgresql-notes

## Browser quality gate

The Chromium golden journey runs:

1. login;
2. Discover a recipe;
3. compare Recipe ↔ Pantry;
4. add missing ingredients to Shopping;
5. plan dinner;
6. Quick Add Shopping;
7. add Pantry state;
8. private Discover;
9. Today.

Axe scans key pages against WCAG 2.x A/AA tags including WCAG 2.2 AA.

Playwright screenshots/traces are uploaded as the `domonest-browser-evidence` CI artifact.

## Demo seed

Create deterministic local content and a non-privileged demo account:

```bash
python manage.py migrate
python manage.py seed_demo --reset --username demo --password domonest-demo
python manage.py runserver
```

The seed resets only private state owned by the selected demo user. It does not delete other accounts.

## Release checklist

- [ ] CI green on Python 3.12 / 3.13 / 3.14.
- [ ] PostgreSQL integration job green.
- [ ] Chromium + Axe golden journey green.
- [ ] `makemigrations --check --dry-run` reports no drift.
- [ ] `check --deploy` is clean.
- [ ] `collectstatic` succeeds.
- [ ] Python dependency audit is clean.
- [ ] Browser dependency audit has no high/critical finding.
- [ ] `/health/` returns 200 against the target database.
- [ ] TLS and trusted-proxy behavior verified.
- [ ] Media storage is persistent before editors upload content.
- [ ] Backup/restore policy exists for the selected PostgreSQL/media providers.
