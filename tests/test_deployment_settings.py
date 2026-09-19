import json
import os
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

BASE_DIR = Path(__file__).resolve().parents[1]

PRODUCTION_ENV_KEYS = {
    "AWS_STORAGE_BUCKET_NAME",
    "DJANGO_ALLOWED_HOSTS",
    "DJANGO_CSRF_TRUSTED_ORIGINS",
    "DJANGO_SETTINGS_MODULE",
    "DJANGO_TRUST_X_FORWARDED_PROTO",
    "RENDER_EXTERNAL_HOSTNAME",
    "WAGTAILADMIN_BASE_URL",
}


class ProductionSettingsTests(SimpleTestCase):
    def _load_settings(self, **extra_env):
        env = os.environ.copy()
        for key in PRODUCTION_ENV_KEYS:
            env.pop(key, None)

        env.update(
            {
                "DJANGO_SETTINGS_MODULE": "mysite.settings.production",
                "DJANGO_SECRET_KEY": (
                    "test-only-super-long-production-secret-with-sufficient-entropy-0123456789"
                ),
            }
        )
        env.update(extra_env)

        script = """
import json
from django.conf import settings

print(json.dumps({
    "allowed_hosts": settings.ALLOWED_HOSTS,
    "csrf_origins": settings.CSRF_TRUSTED_ORIGINS,
    "wagtail_admin_url": settings.WAGTAILADMIN_BASE_URL,
    "default_storage": settings.STORAGES["default"]["BACKEND"],
    "rendition_storage": getattr(settings, "WAGTAILIMAGES_RENDITION_STORAGE", None),
}))
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=BASE_DIR,
            env=env,
            capture_output=True,
            check=True,
            text=True,
        )
        return json.loads(result.stdout)

    def test_render_hostname_supplies_safe_platform_defaults(self):
        settings = self._load_settings(
            RENDER_EXTERNAL_HOSTNAME="domonest-test.onrender.com",
        )

        self.assertEqual(settings["allowed_hosts"], ["domonest-test.onrender.com"])
        self.assertEqual(
            settings["csrf_origins"],
            ["https://domonest-test.onrender.com"],
        )
        self.assertEqual(
            settings["wagtail_admin_url"],
            "https://domonest-test.onrender.com",
        )

    def test_explicit_custom_domain_is_preserved_alongside_render_hostname(self):
        settings = self._load_settings(
            DJANGO_ALLOWED_HOSTS="domonest.example.com",
            DJANGO_CSRF_TRUSTED_ORIGINS="https://domonest.example.com",
            WAGTAILADMIN_BASE_URL="https://domonest.example.com",
            RENDER_EXTERNAL_HOSTNAME="domonest-test.onrender.com",
        )

        self.assertEqual(
            settings["allowed_hosts"],
            ["domonest.example.com", "domonest-test.onrender.com"],
        )
        self.assertEqual(
            settings["csrf_origins"],
            [
                "https://domonest.example.com",
                "https://domonest-test.onrender.com",
            ],
        )
        self.assertEqual(
            settings["wagtail_admin_url"],
            "https://domonest.example.com",
        )

    def test_s3_bucket_activates_shared_media_storage(self):
        settings = self._load_settings(
            RENDER_EXTERNAL_HOSTNAME="domonest-test.onrender.com",
            AWS_STORAGE_BUCKET_NAME="domonest-media",
        )

        self.assertEqual(settings["default_storage"], "storages.s3.S3Storage")
        self.assertEqual(settings["rendition_storage"], "default")
