import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import MealPlanEntryForm
from .models import Chore, PantryItem, ShoppingItem


class PlannerModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="demo", password="strong-pass-123"
        )

    def test_pantry_item_needs_attention_for_low_stock(self):
        item = PantryItem(user=self.user, name="Rice", low_stock=True)
        self.assertTrue(item.needs_attention)

    def test_pantry_item_needs_attention_near_expiry(self):
        item = PantryItem(
            user=self.user,
            name="Yoghurt",
            expires_on=datetime.date.today() + datetime.timedelta(days=2),
        )
        self.assertTrue(item.needs_attention)

    def test_meal_form_requires_recipe_or_custom_meal(self):
        form = MealPlanEntryForm(
            data={
                "date": datetime.date.today(),
                "meal_type": "dinner",
                "recipe": "",
                "custom_meal": "",
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("Choose a recipe", str(form.non_field_errors()))


class PlannerViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="owner", password="strong-pass-123"
        )
        self.other = user_model.objects.create_user(
            username="other", password="strong-pass-123"
        )
        self.client.force_login(self.user)

    def test_dashboard_requires_authentication(self):
        self.client.logout()
        response = self.client.get(reverse("planner:dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_shopping_toggle_only_changes_owned_item(self):
        item = ShoppingItem.objects.create(user=self.user, name="Milk")
        response = self.client.post(
            reverse("planner:toggle_item", args=["shopping", item.pk])
        )
        self.assertRedirects(response, reverse("planner:dashboard"))
        item.refresh_from_db()
        self.assertTrue(item.is_done)

    def test_cannot_delete_another_users_item(self):
        item = Chore.objects.create(user=self.other, title="Private chore")
        response = self.client.post(
            reverse("planner:delete_item", args=["chore", item.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Chore.objects.filter(pk=item.pk).exists())
