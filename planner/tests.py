import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import MealPlanEntryForm
from .models import Chore, MealPlanEntry, PantryItem, ShoppingItem


class PlannerModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="demo", password="strong-pass-123"
        )

    def test_pantry_item_attention_signals(self):
        low_stock = PantryItem(user=self.user, name="Rice", low_stock=True)
        near_expiry = PantryItem(
            user=self.user,
            name="Yoghurt",
            expires_on=datetime.date.today() + datetime.timedelta(days=2),
        )
        stable = PantryItem(
            user=self.user,
            name="Pasta",
            expires_on=datetime.date.today() + datetime.timedelta(days=30),
        )

        self.assertTrue(low_stock.needs_attention)
        self.assertTrue(near_expiry.needs_attention)
        self.assertFalse(stable.needs_attention)

    def test_model_labels_are_human_readable(self):
        shopping = ShoppingItem(user=self.user, name="Milk")
        pantry = PantryItem(user=self.user, name="Rice")
        chore = Chore(user=self.user, title="Clean fridge")
        meal = MealPlanEntry(
            user=self.user,
            date=datetime.date.today(),
            meal_type=MealPlanEntry.MealType.DINNER,
            custom_meal="Soup",
        )

        self.assertEqual(str(shopping), "Milk")
        self.assertEqual(str(pantry), "Rice")
        self.assertEqual(str(chore), "Clean fridge")
        self.assertEqual(meal.label, "Soup")
        self.assertIn("Soup", str(meal))

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

    def test_dashboard_renders_for_authenticated_user(self):
        response = self.client.get(reverse("planner:dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your home, at a glance")
        self.assertContains(response, "Meal plan")

    def test_dashboard_adds_shopping_item(self):
        response = self.client.post(
            reverse("planner:dashboard"),
            {
                "action": "shopping",
                "shopping-name": "Apples",
                "shopping-quantity": "6",
                "shopping-category": "produce",
            },
        )
        self.assertRedirects(response, reverse("planner:dashboard"))
        self.assertTrue(
            ShoppingItem.objects.filter(user=self.user, name="Apples").exists()
        )

    def test_dashboard_upserts_custom_meal_slot(self):
        today = datetime.date.today()
        payload = {
            "action": "meal",
            "meal-date": today.isoformat(),
            "meal-meal_type": "dinner",
            "meal-recipe": "",
            "meal-custom_meal": "Vegetable soup",
        }
        self.client.post(reverse("planner:dashboard"), payload)
        payload["meal-custom_meal"] = "Pasta"
        response = self.client.post(reverse("planner:dashboard"), payload)

        self.assertRedirects(response, reverse("planner:dashboard"))
        meals = MealPlanEntry.objects.filter(
            user=self.user,
            date=today,
            meal_type=MealPlanEntry.MealType.DINNER,
        )
        self.assertEqual(meals.count(), 1)
        self.assertEqual(meals.get().custom_meal, "Pasta")

    def test_shopping_toggle_only_changes_owned_item(self):
        item = ShoppingItem.objects.create(user=self.user, name="Milk")
        response = self.client.post(
            reverse("planner:toggle_item", args=["shopping", item.pk])
        )
        self.assertRedirects(response, reverse("planner:dashboard"))
        item.refresh_from_db()
        self.assertTrue(item.is_done)

    def test_invalid_toggle_kind_fails_closed(self):
        response = self.client.post(
            reverse("planner:toggle_item", args=["unknown", 123])
        )
        self.assertRedirects(response, reverse("planner:dashboard"))

    def test_owned_item_can_be_deleted(self):
        item = PantryItem.objects.create(user=self.user, name="Flour")
        response = self.client.post(
            reverse("planner:delete_item", args=["pantry", item.pk])
        )
        self.assertRedirects(response, reverse("planner:dashboard"))
        self.assertFalse(PantryItem.objects.filter(pk=item.pk).exists())

    def test_cannot_delete_another_users_item(self):
        item = Chore.objects.create(user=self.other, title="Private chore")
        response = self.client.post(
            reverse("planner:delete_item", args=["chore", item.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Chore.objects.filter(pk=item.pk).exists())

    def test_invalid_delete_kind_fails_closed(self):
        response = self.client.post(
            reverse("planner:delete_item", args=["unknown", 123])
        )
        self.assertRedirects(response, reverse("planner:dashboard"))

    def test_signup_creates_user_and_logs_them_in(self):
        self.client.logout()
        response = self.client.post(
            reverse("signup"),
            {
                "username": "new-home",
                "password1": "VeryStrongHomePass-462!",
                "password2": "VeryStrongHomePass-462!",
            },
        )

        self.assertRedirects(response, reverse("planner:dashboard"))
        self.assertTrue(get_user_model().objects.filter(username="new-home").exists())
