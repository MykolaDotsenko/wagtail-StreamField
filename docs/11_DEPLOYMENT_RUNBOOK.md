# Deployment Runbook

This runbook defines the production baseline for DomoNest and the supported Render portfolio deployment.

## Runtime contract

- Python 3.12–3.14 are exercised in CI.
- Render is pinned to Python 3.13 through `.python-version`.
- Django 5.2.17.
- Wagtail 7.4.3.
- Gunicorn is the WSGI process server.
- PostgreSQL is the production database target.
- WhiteNoise serves fingerprinted static assets only.
- Wagtail media must live on durable filesystem storage or an S3-compatible shared backend.

## Production environment

Generic production configuration:

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

On Render, `RENDER_EXTERNAL_HOSTNAME` is injected by the platform. Production settings use it to add the Render hostname to `ALLOWED_HOSTS`, add the matching HTTPS CSRF origin, and provide the default `WAGTAILADMIN_BASE_URL`. Explicit custom-domain settings still take precedence.

Optional hardening:

```text
DJANGO_TRUST_X_FORWARDED_PROTO=true
DJANGO_SECURE_HSTS_SECONDS=3600
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=false
DJANGO_SECURE_HSTS_PRELOAD=false
```

Only enable `DJANGO_TRUST_X_FORWARDED_PROTO` behind a trusted reverse proxy that overwrites `X-Forwarded-Proto`. Render's managed proxy satisfies that contract.

## Render Blueprint

The root `render.yaml` provisions:

- one Python web service;
- one PostgreSQL 17 database;
- Frankfurt region for both resources;
- CI-gated automatic deploys;
- a generated Django secret key;
- database credentials through `fromDatabase` references;
- `/health/` as the Render health check;
- one Gunicorn worker for the 512 MB free preview service;
- deterministic demo seeding for the public portfolio configuration.

The Blueprint intentionally uses the free plans as an evaluation / portfolio baseline.

### Create the deployment

1. Merge the deployment branch to `master`.
2. In Render, choose **New → Blueprint**.
3. Select this repository.
4. Review the resources defined by `render.yaml`.
5. Create the Blueprint instance.
6. Wait for GitHub CI to pass and for Render's `/health/` check to turn healthy.

The web service follows `master` and uses `autoDeployTrigger: checksPass`, so a commit is not released until linked CI checks pass.

## Build lifecycle

Render build command:

```text
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py collectstatic --noinput --clear
```

The Blueprint supplies build-only placeholder host/admin values to the `collectstatic` command. Runtime secrets are not written into the repository.

## Free-plan release lifecycle

Render's pre-deploy command is a paid-web-service feature. For the free portfolio deployment, `scripts/render-start.sh` owns the startup sequence:

```text
check --deploy
    ↓
migrate --noinput
    ↓
optional deterministic demo reset
    ↓
exec gunicorn
```

The behavior is explicit:

```text
DOMONEST_RUN_MIGRATIONS_ON_START=true
DOMONEST_AUTO_SEED_DEMO=true
DOMONEST_DEMO_USERNAME=demo
DOMONEST_DEMO_PASSWORD=domonest-demo
```

The public demo password is deliberately not a privileged credential. `seed_demo` always forces the selected demo account to:

- `is_active=True`;
- `is_staff=False`;
- `is_superuser=False`.

The reset is scoped to private household state owned by that account and leaves other users untouched.

This arrangement is appropriate for the public portfolio preview because free services can restart or spin down. A fresh start also restores the demo user to deterministic state.

## Paid Render release lifecycle

For a durable paid deployment:

1. set `DOMONEST_AUTO_SEED_DEMO=false` unless this is intentionally a public demo;
2. add the following service field to `render.yaml` or the Render dashboard:

```yaml
preDeployCommand: >-
  python manage.py check --deploy &&
  python manage.py migrate --noinput
```

3. set:

```text
DOMONEST_RUN_MIGRATIONS_ON_START=false
```

This moves schema changes into Render's release phase instead of performing them when an application process starts.

For scaled/multi-instance deployments, migrations must not be owned independently by every application instance.

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

The endpoint intentionally:

- does not expose exception text or connection details;
- returns `Cache-Control: no-store`;
- is configured as Render's deployment health check.

Render only promotes a new deploy after the configured HTTP health check succeeds.

## Post-deploy smoke verification

Run:

```bash
python scripts/deployment_smoke.py https://YOUR-SERVICE.onrender.com
```

The smoke check uses only the Python standard library and verifies:

1. HTTPS for non-local targets;
2. `/health/` returns HTTP 200;
3. the exact `{"status":"ok"}` payload;
4. `Cache-Control: no-store`;
5. the root application is reachable;
6. `X-Content-Type-Options: nosniff`;
7. `Referrer-Policy: strict-origin-when-cross-origin`;
8. HSTS is present.

## Static files

Production uses:

```text
whitenoise.storage.CompressedManifestStaticFilesStorage
```

WhiteNoise middleware runs directly after Django `SecurityMiddleware`.

Static files are built with `collectstatic`; user/editor uploads are never delegated to WhiteNoise.

## Media files

### Filesystem mode

Without `AWS_STORAGE_BUCKET_NAME`, the default Django `FileSystemStorage` remains active.

This is valid only when `DJANGO_MEDIA_ROOT` points to durable storage, such as a paid Render persistent disk on a single-instance deployment.

Do not rely on the Render Free filesystem for uploaded content.

### S3-compatible shared mode

Set:

```text
AWS_STORAGE_BUCKET_NAME=<bucket>
AWS_ACCESS_KEY_ID=<access-key>
AWS_SECRET_ACCESS_KEY=<secret-key>
```

Optional provider settings:

```text
AWS_S3_ENDPOINT_URL=https://...
AWS_S3_REGION_NAME=...
AWS_SESSION_TOKEN=...
AWS_S3_CUSTOM_DOMAIN=...
AWS_S3_PUBLIC_DOMAIN=...
AWS_S3_ADDRESSING_STYLE=...
AWS_QUERYSTRING_AUTH=true
AWS_S3_USE_SSL=true
```

When `AWS_STORAGE_BUCKET_NAME` is present:

- Django default file storage becomes `storages.s3.S3Storage`;
- Wagtail image renditions use the same `default` storage alias;
- static assets remain on WhiteNoise.

This supports AWS S3 and compatible object stores such as Cloudflare R2 or DigitalOcean Spaces.

Do not commit bucket credentials.

## PostgreSQL

The application switches from SQLite to PostgreSQL whenever `POSTGRES_DB` is present.

The Render Blueprint obtains each connection field from the database resource instead of embedding credentials in source control.

The CI PostgreSQL integration job uses PostgreSQL 17, matching the Blueprint major version.

For Render, the application and database are placed in the same region so private database networking can be used.

## Custom domain

After adding a custom domain in Render, configure:

```text
DJANGO_ALLOWED_HOSTS=domonest.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://domonest.example.com
WAGTAILADMIN_BASE_URL=https://domonest.example.com
```

The Render `.onrender.com` hostname is still appended automatically while it remains enabled.

Do not enable HSTS preload until HTTPS is intentionally correct for the complete intended domain/subdomain surface.

## Docker

The Docker image remains deployment-platform neutral.

Its Gunicorn command now reads:

- `PORT`, default `8000`;
- `WEB_CONCURRENCY`, default `2`;
- `GUNICORN_TIMEOUT`, default `30`.

Docker builds run `collectstatic` with a build-only placeholder secret and host. Runtime secrets are still required by `mysite.settings.production`.

## Render Free limitations

The free configuration is for portfolio evaluation, not durable production:

- the web service can spin down after inactivity;
- its filesystem is ephemeral;
- persistent disks are unavailable on free web services;
- free PostgreSQL databases expire after the provider's current free retention period.

Use a paid database or another durable PostgreSQL provider before treating the deployment as persistent.

The public demo intentionally avoids dependence on uploaded media, so the app can still demonstrate its core workflows on the free baseline.

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

## Deployment artifact validation

CI additionally verifies:

- `render.yaml` is valid YAML;
- the Blueprint infrastructure contract has regression tests;
- `scripts/render-start.sh` passes Bash syntax validation;
- `scripts/deployment_smoke.py` compiles;
- Render-derived production settings are tested in isolated subprocesses;
- S3 media activation is tested;
- the demo seed cannot leave the public demo user privileged.

## Release checklist

- [ ] CI green on Python 3.12 / 3.13 / 3.14.
- [ ] PostgreSQL integration job green.
- [ ] Chromium + Axe golden journey green.
- [ ] Render Blueprint tests green.
- [ ] `makemigrations --check --dry-run` reports no drift.
- [ ] `check --deploy` is clean.
- [ ] `collectstatic` succeeds.
- [ ] Python dependency audit is clean.
- [ ] Browser dependency audit has no high/critical finding.
- [ ] Render `/health/` check is healthy.
- [ ] Post-deploy smoke script passes against the public URL.
- [ ] TLS and trusted-proxy behavior verified.
- [ ] Demo credentials remain non-privileged.
- [ ] Durable media storage exists before editor uploads are enabled.
- [ ] Backup/restore policy exists for PostgreSQL and media.
- [ ] Paid/multi-instance deployments move migrations into a dedicated release step.

## References

- Render Blueprint specification: https://render.com/docs/blueprint-spec
- Render health checks: https://render.com/docs/health-checks
- Render deploy lifecycle: https://render.com/docs/deploys
- Render free-plan limitations: https://render.com/docs/free
- Render Python version selection: https://render.com/docs/python-version
- Render persistent disks: https://render.com/docs/disks
- Wagtail settings: https://docs.wagtail.org/en/7.4/reference/settings.html
- Django file storage: https://docs.djangoproject.com/en/5.2/ref/files/storage/
- WhiteNoise + Django: https://whitenoise.readthedocs.io/en/stable/django.html
