import os

from django.core.exceptions import ImproperlyConfigured

from .base import *
from .utils import env_bool, env_int, env_list

DEBUG = False

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required in production.")

render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
render_origin = f"https://{render_hostname}" if render_hostname else ""

ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS")
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "DJANGO_ALLOWED_HOSTS is required in production unless "
        "RENDER_EXTERNAL_HOSTNAME is available."
    )

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")
if render_origin and render_origin not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append(render_origin)

WAGTAILADMIN_BASE_URL = os.environ.get("WAGTAILADMIN_BASE_URL")
if not WAGTAILADMIN_BASE_URL and render_origin:
    WAGTAILADMIN_BASE_URL = render_origin
if not WAGTAILADMIN_BASE_URL:
    raise ImproperlyConfigured(
        "WAGTAILADMIN_BASE_URL is required in production unless "
        "RENDER_EXTERNAL_HOSTNAME is available."
    )

STORAGES["staticfiles"] = {
    "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
}

# Local filesystem media remains useful for single-instance deployments with a
# durable mounted volume. On ephemeral/multi-instance platforms, setting
# AWS_STORAGE_BUCKET_NAME activates the S3-compatible backend instead.
MEDIA_ROOT = os.environ.get("DJANGO_MEDIA_ROOT", MEDIA_ROOT)

s3_media_bucket = os.environ.get("AWS_STORAGE_BUCKET_NAME", "").strip()
if s3_media_bucket:
    s3_options = {
        "bucket_name": s3_media_bucket,
        "file_overwrite": False,
    }

    optional_s3_options = {
        "AWS_S3_ENDPOINT_URL": "endpoint_url",
        "AWS_S3_REGION_NAME": "region_name",
        "AWS_ACCESS_KEY_ID": "access_key",
        "AWS_SECRET_ACCESS_KEY": "secret_key",
        "AWS_SESSION_TOKEN": "security_token",
        "AWS_S3_CUSTOM_DOMAIN": "custom_domain",
        "AWS_S3_PUBLIC_DOMAIN": "public_domain",
        "AWS_S3_ADDRESSING_STYLE": "addressing_style",
    }
    for environment_name, option_name in optional_s3_options.items():
        value = os.environ.get(environment_name, "").strip()
        if value:
            s3_options[option_name] = value

    if "AWS_QUERYSTRING_AUTH" in os.environ:
        s3_options["querystring_auth"] = env_bool("AWS_QUERYSTRING_AUTH")
    if "AWS_S3_USE_SSL" in os.environ:
        s3_options["use_ssl"] = env_bool("AWS_S3_USE_SSL")

    STORAGES["default"] = {
        "BACKEND": "storages.s3.S3Storage",
        "OPTIONS": s3_options,
    }
    WAGTAILIMAGES_RENDITION_STORAGE = "default"

WHITENOISE_KEEP_ONLY_HASHED_FILES = True

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = env_int("DJANGO_SECURE_HSTS_SECONDS", default=3600)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS")
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD")
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SESSION_COOKIE_HTTPONLY = True

if env_bool("DJANGO_TRUST_X_FORWARDED_PROTO"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
