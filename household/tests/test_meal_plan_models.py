from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from home.models import HomePage
from household.models import MealPlanEntry
from recipes.models import RecipeIndexPage, RecipePage


class MealPlanEntryModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="meal-model-user",
            password="safe-test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="meal-model-other",
            password="safe-test-password",
        )
        self.day = date(2026, 9, 21)

    def test_name_snapshot_is_normalized(self):
        entry = MealPlanEntry.objects.create(
            user=self.user,
            date=self.day,
            name="  Soup   and   sandwiches ",
        )

        self.assertEqual(entry.name, "Soup and sandwiches")

    def test_empty_normalized_name_is_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            MealPlanEntry.objects.create(
                user=self.user,
                date=self.day,
                name="   ",
            )

    def test_only_one_dinner_per_user_and_date(self):
        MealPlanEntry.objects.create(
            user=self.user,
            date=self.day,
            name="Soup",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            MealPlanEntry.objects.create(
                user=self.user,
                date=self.day,
                name="Pasta",
            )

    def test_same_date_is_independent_between_users(self):
        first = MealPlanEntry.objects.create(
            user=self.user,
            date=self.day,
            name="Soup",
        )
        second = MealPlanEntry.objects.create(
            user=self.other_user,
            date=self.day,
            name="Pasta",
        )

        self.assertNotEqual(first.pk, second.pk)

    def test_recipe_deletion_preserves_private_dinner_snapshot(self):
        home = HomePage.objects.first()
        index = RecipeIndexPage(title="Recipes", slug="meal-model-recipes", intro="")
        home.add_child(instance=index)
        recipe = RecipePage(
            title="Tomato pasta",
            slug="meal-model-pasta",
            intro="Fast dinner.",
            prep_minutes=10,
            cook_minutes=15,
            servings=2,
            instructions=[],
        )
        index.add_child(instance=recipe)
        entry = MealPlanEntry.objects.create(
            user=self.user,
            date=self.day,
            recipe=recipe,
            name=recipe.title,
        )

        recipe.delete()
        entry.refresh_from_db()

        self.assertIsNone(entry.recipe_id)
        self.assertEqual(entry.name, "Tomato pasta")
