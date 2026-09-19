from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from home.models import HomePage
from household.models import MealPlanEntry
from recipes.models import RecipeIndexPage, RecipePage


class MealPlanViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="meal-view-user",
            password="safe-test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="meal-view-other",
            password="safe-test-password",
        )
        self.today = timezone.localdate()
        home = HomePage.objects.first()
        index = RecipeIndexPage(title="Recipes", slug="meal-view-recipes", intro="")
        home.add_child(instance=index)
        self.recipe = RecipePage(
            title="Tomato pasta",
            slug="meal-view-pasta",
            intro="Fast dinner.",
            prep_minutes=10,
            cook_minutes=15,
            servings=2,
            instructions=[],
        )
        index.add_child(instance=self.recipe)

    def test_plan_requires_authentication(self):
        response = self.client.get(reverse("household:plan"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_plan_renders_seven_day_surface(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("household:plan"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dinner plan")
        self.assertEqual(len(response.context["week"].days), 7)

    def test_recipe_query_prefills_without_mutating(self):
        self.client.force_login(self.user)

        response = self.client.get(f"{reverse('household:plan')}?recipe={self.recipe.pk}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["form"]["recipe"].value(), str(self.recipe.pk))
        self.assertFalse(MealPlanEntry.objects.filter(user=self.user).exists())

    def test_custom_dinner_post_creates_plan(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("household:plan"),
            {
                "date": self.today.isoformat(),
                "recipe": "",
                "custom_name": "Soup and sandwiches",
            },
        )

        self.assertEqual(response.status_code, 302)
        entry = MealPlanEntry.objects.get(user=self.user, date=self.today)
        self.assertEqual(entry.name, "Soup and sandwiches")
        self.assertIsNone(entry.recipe_id)

    def test_recipe_post_uses_recipe_title_snapshot(self):
        self.client.force_login(self.user)

        self.client.post(
            reverse("household:plan"),
            {
                "date": self.today.isoformat(),
                "recipe": str(self.recipe.pk),
                "custom_name": "",
            },
        )

        entry = MealPlanEntry.objects.get(user=self.user, date=self.today)
        self.assertEqual(entry.recipe_id, self.recipe.pk)
        self.assertEqual(entry.name, self.recipe.title)

    def test_saving_same_date_replaces_existing_dinner(self):
        self.client.force_login(self.user)
        url = reverse("household:plan")
        self.client.post(
            url,
            {
                "date": self.today.isoformat(),
                "recipe": "",
                "custom_name": "Soup",
            },
        )
        self.client.post(
            url,
            {
                "date": self.today.isoformat(),
                "recipe": str(self.recipe.pk),
                "custom_name": "",
            },
        )

        self.assertEqual(
            MealPlanEntry.objects.filter(user=self.user, date=self.today).count(),
            1,
        )
        self.assertEqual(
            MealPlanEntry.objects.get(user=self.user, date=self.today).name,
            self.recipe.title,
        )

    def test_past_date_is_rejected_without_write(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("household:plan"),
            {
                "date": (self.today - timedelta(days=1)).isoformat(),
                "recipe": "",
                "custom_name": "Yesterday",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "future date")
        self.assertFalse(MealPlanEntry.objects.filter(user=self.user).exists())

    def test_remove_is_post_only_and_owner_scoped(self):
        self.client.force_login(self.user)
        private_entry = MealPlanEntry.objects.create(
            user=self.other_user,
            date=self.today,
            name="Private dinner",
        )
        url = reverse("household:remove_dinner", args=[private_entry.pk])

        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(self.client.post(url).status_code, 404)
        self.assertTrue(MealPlanEntry.objects.filter(pk=private_entry.pk).exists())

    def test_remove_is_csrf_protected(self):
        entry = MealPlanEntry.objects.create(
            user=self.user,
            date=self.today,
            name="Soup",
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        response = client.post(reverse("household:remove_dinner", args=[entry.pk]))

        self.assertEqual(response.status_code, 403)
        self.assertTrue(MealPlanEntry.objects.filter(pk=entry.pk).exists())

    def test_invalid_week_query_falls_back_safely(self):
        self.client.force_login(self.user)

        response = self.client.get(f"{reverse('household:plan')}?week=not-a-date")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["week"].days), 7)
