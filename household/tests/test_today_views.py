from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from household.models import PantryItem, Routine, ShoppingItem


class TodayViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="today-view-user",
            password="safe-test-password",
        )

    def test_today_requires_authentication(self):
        response = self.client.get(reverse("household:today"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_today_renders_actionable_cross_module_state(self):
        today = timezone.localdate()
        Routine.objects.create(
            user=self.user,
            title="Clean kitchen",
            frequency=Routine.Frequency.DAILY,
            due_on=today,
        )
        PantryItem.objects.create(
            user=self.user,
            name="Yoghurt",
            expires_on=today + timedelta(days=1),
        )
        ShoppingItem.objects.create(user=self.user, name="Bread")
        self.client.force_login(self.user)

        response = self.client.get(reverse("household:today"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Due today: Clean kitchen")
        self.assertContains(response, "Use Yoghurt soon")
        self.assertContains(response, "1 item to buy")
        self.assertContains(response, "Meal planning comes next")

    def test_authenticated_navigation_points_today_to_private_dashboard(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("household:today"))

        self.assertContains(response, f'href="{reverse("household:today")}"')
        self.assertContains(response, 'aria-current="page"')

    def test_empty_today_is_calm_not_error_state(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("household:today"))

        self.assertContains(response, "Nothing urgent needs your attention right now.")
        self.assertContains(response, "Home is in a calm state")
