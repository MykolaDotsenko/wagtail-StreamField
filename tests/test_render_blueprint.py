from pathlib import Path

import yaml
from django.test import SimpleTestCase

BASE_DIR = Path(__file__).resolve().parents[1]


class RenderBlueprintTests(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.blueprint = yaml.safe_load((BASE_DIR / "render.yaml").read_text(encoding="utf-8"))

    def test_blueprint_defines_ci_gated_web_service_and_postgres(self):
        service = self.blueprint["services"][0]
        database = self.blueprint["databases"][0]

        self.assertEqual(service["type"], "web")
        self.assertEqual(service["runtime"], "python")
        self.assertEqual(service["region"], "frankfurt")
        self.assertEqual(service["autoDeployTrigger"], "checksPass")
        self.assertEqual(service["healthCheckPath"], "/health/")
        self.assertEqual(service["startCommand"], "bash scripts/render-start.sh")
        self.assertIn("collectstatic", service["buildCommand"])

        self.assertEqual(database["name"], "domonest-db")
        self.assertEqual(database["region"], "frankfurt")
        self.assertEqual(database["postgresMajorVersion"], "17")
        self.assertEqual(database["ipAllowList"], [])

    def test_blueprint_generates_secret_and_wires_database_without_plaintext_credentials(self):
        service = self.blueprint["services"][0]
        env = {item["key"]: item for item in service["envVars"]}

        self.assertTrue(env["DJANGO_SECRET_KEY"]["generateValue"])
        self.assertNotIn("value", env["DJANGO_SECRET_KEY"])

        for key, property_name in (
            ("POSTGRES_DB", "database"),
            ("POSTGRES_USER", "user"),
            ("POSTGRES_PASSWORD", "password"),
            ("POSTGRES_HOST", "host"),
            ("POSTGRES_PORT", "port"),
        ):
            self.assertEqual(
                env[key]["fromDatabase"],
                {"name": "domonest-db", "property": property_name},
            )

    def test_public_demo_seed_is_explicit_and_non_admin_by_design(self):
        service = self.blueprint["services"][0]
        env = {item["key"]: item for item in service["envVars"]}

        self.assertEqual(env["DOMONEST_AUTO_SEED_DEMO"]["value"], "true")
        self.assertEqual(env["DOMONEST_RUN_MIGRATIONS_ON_START"]["value"], "true")
        self.assertEqual(env["DOMONEST_DEMO_USERNAME"]["value"], "demo")
