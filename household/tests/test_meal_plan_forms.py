from datetime import date, timedelta
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase

from home.models import HomePage
from household.forms import MealPlanForm
from recipes.models import RecipeIndexPage, RecipePage


class MealPlanFormTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="meal-form-user",
            password="safe-test-password",
        )
        self.today = date(2026, 9, 19)
        home = HomePage.objects.first()
        index = RecipeIndexPage(title="Recipes", slug="meal-form-recipes", intro="")
        home.add_child(instance=index)
        self.recipe = RecipePage(
            title="Tomato pasta",
            slug="meal-form-pasta",
            intro="Fast dinner.",
            prep_minutes=10,
            cook_minutes=15,
            servings=2,
            instructions=[],
        )
        index.add_child(instance=self.recipe)
        self.options = (
            SimpleNamespace(
                recipe=self.recipe,
                selection_label="Tomato pasta — 25 min · Pantry ready",
            ),
        )

    def make_form(self, data):
        return MealPlanForm(
            data,
            recipe_options=self.options,
            today=self.today,
        )

    def test_custom_dinner_is_valid_and_normalized(self):
        form = self.make_form(
            {
                "date": self.today.isoformat(),
                "recipe": "",
                "custom_name": "  Soup   and sandwiches ",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["recipe_obj"])
        self.assertEqual(form.cleaned_data["meal_name"], "Soup and sandwiches")

    def test_live_recipe_is_valid(self):
        form = self.make_form(
            {
                "date": self.today.isoformat(),
                "recipe": str(self.recipe.pk),
                "custom_name": "",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["recipe_obj"], self.recipe)
        self.assertEqual(form.cleaned_data["meal_name"], "Tomato pasta")

    def test_recipe_and_custom_name_are_mutually_exclusive(self):
        form = self.make_form(
            {
                "date": self.today.isoformat(),
                "recipe": str(self.recipe.pk),
                "custom_name": "Soup",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("not both", form.non_field_errors()[0])

    def test_one_dinner_source_is_required(self):
        form = self.make_form(
            {
                "date": self.today.isoformat(),
                "recipe": "",
                "custom_name": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("Choose a recipe", form.non_field_errors()[0])

    def test_past_date_is_rejected(self):
        form = self.make_form(
            {
                "date": (self.today - timedelta(days=1)).isoformat(),
                "recipe": "",
                "custom_name": "Soup",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("future date", form.errors["date"][0])

    def test_recipe_is_revalidated_as_live_on_submit(self):
        self.recipe.live = False
        self.recipe.save()

        form = self.make_form(
            {
                "date": self.today.isoformat(),
                "recipe": str(self.recipe.pk),
                "custom_name": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("available recipe", form.errors["recipe"][0])
