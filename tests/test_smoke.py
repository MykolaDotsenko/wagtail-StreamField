from django.contrib.auth import get_user_model
from django.test import TestCase


class ApplicationSmokeTests(TestCase):
    def test_homepage_renders_domnest_shell(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="skip-link"')
        self.assertContains(response, "Less to remember. More room to live.")
        self.assertContains(response, 'class="mobile-nav"')
        self.assertContains(response, 'aria-label="Primary"')

    def test_search_page_renders_accessible_search_form(self):
        response = self.client.get("/search/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'role="search"')
        self.assertContains(response, 'for="search-query"')
        self.assertContains(response, 'type="search"')
        self.assertContains(response, "Start with a household question")

    def test_login_page_uses_deliberate_form_markup(self):
        response = self.client.get("/accounts/login/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign in to DomoNest")
        self.assertContains(response, 'autocomplete="username"')
        self.assertContains(response, 'autocomplete="current-password"')

    def test_authenticated_shell_exposes_post_logout(self):
        user = get_user_model().objects.create_user(
            username="shell-user",
            password="safe-test-password",
        )
        self.client.force_login(user)

        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'action="/accounts/logout/"')
        self.assertContains(response, 'method="post"')

    def test_wagtail_admin_login_renders(self):
        response = self.client.get("/admin/login/")

        self.assertEqual(response.status_code, 200)
