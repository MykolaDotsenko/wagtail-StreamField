from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from household.models import MealPlanEntry, PantryItem, Routine, ShoppingItem


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
        MealPlanEntry.objects.create(user=self.user, date=today, name="Soup")
        self.client.force_login(self.user)

        response = self.client.get(reverse("household:today"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Due today: Clean kitchen")
        self.assertContains(response, "Use Yoghurt soon")
        self.assertContains(response, "1 item to buy")
        self.assertContains(response, "Soup")

    def test_authenticated_navigation_points_today_to_private_dashboard(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("household:today"))

        self.assertContains(response, f'href="{reverse("household:today")}"')
        self.assertContains(response, 'aria-current="page"')

    def test_empty_today_is_calm_when_dinner_is_already_decided(self):
        MealPlanEntry.objects.create(
            user=self.user,
            date=timezone.localdate(),
            name="Soup",
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("household:today"))

        self.assertContains(response, "Nothing urgent needs your attention right now.")
        self.assertContains(response, "Home is in a calm state")

    def test_unplanned_dinner_is_rendered_as_attention(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("household:today"))

        self.assertContains(response, "Dinner is not planned yet")
        self.assertContains(response, "Dinner</span>")
        self.assertContains(response, reverse("household:plan"))
