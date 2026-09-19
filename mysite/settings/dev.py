from contextlib import suppress

from .base import *

DEBUG = True
SECRET_KEY = "django-insecure-local-development-only"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]"]
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

with suppress(ImportError):
    from .local import *
