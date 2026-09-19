#!/usr/bin/env bash
set -Eeuo pipefail

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-mysite.settings.production}"

is_truthy() {
  case "${1:-}" in
    1|true|TRUE|True|yes|YES|Yes|on|ON|On) return 0 ;;
    *) return 1 ;;
  esac
}

echo "==> Validating Django production configuration"
python manage.py check --deploy

if is_truthy "${DOMONEST_RUN_MIGRATIONS_ON_START:-true}"; then
  echo "==> Applying database migrations"
  python manage.py migrate --noinput
else
  echo "==> Skipping startup migrations; deployment platform owns the release step"
fi

if is_truthy "${DOMONEST_AUTO_SEED_DEMO:-false}"; then
  demo_username="${DOMONEST_DEMO_USERNAME:-demo}"
  demo_password="${DOMONEST_DEMO_PASSWORD:-}"

  if [[ -z "${demo_password}" ]]; then
    echo "DOMONEST_DEMO_PASSWORD must be set when DOMONEST_AUTO_SEED_DEMO is enabled." >&2
    exit 1
  fi

  echo "==> Restoring deterministic non-privileged demo state for ${demo_username}"
  python manage.py seed_demo \
    --reset \
    --username "${demo_username}" \
    --password "${demo_password}"
fi

workers="${WEB_CONCURRENCY:-1}"
timeout="${GUNICORN_TIMEOUT:-30}"

echo "==> Starting Gunicorn on port ${PORT:-8000} with ${workers} worker(s)"
exec gunicorn mysite.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${workers}" \
  --timeout "${timeout}" \
  --graceful-timeout 30 \
  --access-logfile - \
  --error-logfile -
