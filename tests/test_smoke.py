from django.test import TestCase


class ApplicationSmokeTests(TestCase):
    def test_wagtail_admin_login_renders(self):
        response = self.client.get("/admin/login/")

        self.assertEqual(response.status_code, 200)

    def test_search_page_renders_without_query(self):
        response = self.client.get("/search/")

        self.assertEqual(response.status_code, 200)
