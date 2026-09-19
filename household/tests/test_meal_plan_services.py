from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from home.models import HomePage
from household.models import MealPlanEntry
from household.services import delete_dinner, set_dinner
from recipes.models import RecipeIndexPage, RecipePage


class MealPlanServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="meal-service-user",
            password="safe-test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="meal-service-other",
            password="safe-test-password",
        )
        self.day = date(2026, 9, 21)
        home = HomePage.objects.first()
        index = RecipeIndexPage(title="Recipes", slug="meal-service-recipes", intro="")
        home.add_child(instance=index)
        self.recipe = RecipePage(
            title="Tomato pasta",
            slug="meal-service-pasta",
            intro="Fast dinner.",
            prep_minutes=10,
            cook_minutes=15,
            servings=2,
            instructions=[],
        )
        index.add_child(instance=self.recipe)

    def test_setting_same_date_updates_instead_of_duplicating(self):
        first = set_dinner(
            user=self.user,
            dinner_date=self.day,
            custom_name="Soup",
        )
        second = set_dinner(
            user=self.user,
            dinner_date=self.day,
            recipe=self.recipe,
            custom_name="Ignored caller text",
        )

        self.assertEqual(first.pk, second.pk)
        self.assertEqual(MealPlanEntry.objects.filter(user=self.user).count(), 1)
        self.assertEqual(second.recipe_id, self.recipe.pk)
        self.assertEqual(second.name, self.recipe.title)

    def test_non_live_recipe_is_rejected_by_service(self):
        self.recipe.live = False
        self.recipe.save()

        with self.assertRaises(ValueError):
            set_dinner(
                user=self.user,
                dinner_date=self.day,
                recipe=self.recipe,
            )

    def test_custom_dinner_is_normalized(self):
        entry = set_dinner(
            user=self.user,
            dinner_date=self.day,
            custom_name="  Soup   and toast ",
        )

        self.assertEqual(entry.name, "Soup and toast")
        self.assertIsNone(entry.recipe_id)

    def test_empty_custom_dinner_is_rejected(self):
        with self.assertRaises(ValueError):
            set_dinner(
                user=self.user,
                dinner_date=self.day,
                custom_name="   ",
            )

    def test_delete_is_owner_scoped(self):
        entry = set_dinner(
            user=self.other_user,
            dinner_date=self.day,
            custom_name="Private dinner",
        )

        with self.assertRaises(MealPlanEntry.DoesNotExist):
            delete_dinner(user=self.user, entry_id=entry.pk)

        self.assertTrue(MealPlanEntry.objects.filter(pk=entry.pk).exists())
