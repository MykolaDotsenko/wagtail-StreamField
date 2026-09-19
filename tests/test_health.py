from unittest.mock import patch

from django.db import DatabaseError
from django.test import TestCase


class HealthEndpointTests(TestCase):
    def test_health_reports_database_readiness_without_sensitive_details(self):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    @patch("mysite.health.connection.cursor", side_effect=DatabaseError)
    def test_health_returns_503_when_database_is_unavailable(self, _cursor):
        response = self.client.get("/health/")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"status": "unavailable"})
        self.assertNotContains(response, "DatabaseError", status_code=503)

    def test_health_is_safe_method_only(self):
        response = self.client.post("/health/")

        self.assertEqual(response.status_code, 405)
