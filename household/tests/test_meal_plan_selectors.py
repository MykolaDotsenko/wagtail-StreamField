from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from home.models import HomePage
from household.models import MealPlanEntry, PantryItem
from household.selectors import meal_plan_week, meal_recipe_options, week_start
from recipes.models import Ingredient, RecipeIndexPage, RecipeIngredient, RecipePage


class MealPlanSelectorTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="meal-selector-user",
            password="safe-test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="meal-selector-other",
            password="safe-test-password",
        )
        self.today = date(2026, 9, 19)
        home = HomePage.objects.first()
        self.index = RecipeIndexPage(title="Recipes", slug="meal-selector-recipes", intro="")
        home.add_child(instance=self.index)

    def recipe(self, title, slug, *, minutes=20):
        recipe = RecipePage(
            title=title,
            slug=slug,
            intro="Dinner.",
            prep_minutes=5,
            cook_minutes=minutes - 5,
            servings=2,
            instructions=[],
        )
        self.index.add_child(instance=recipe)
        return recipe

    def add_line(self, recipe, ingredient, *, amount=None, unit=""):
        return RecipeIngredient.objects.create(
            page=recipe,
            ingredient=ingredient,
            amount=amount,
            unit=unit,
        )

    def test_week_is_monday_through_sunday(self):
        week = meal_plan_week(
            user=self.user,
            anchor=self.today,
            today=self.today,
        )

        self.assertEqual(week_start(self.today), date(2026, 9, 14))
        self.assertEqual(week.start, date(2026, 9, 14))
        self.assertEqual(week.end, date(2026, 9, 20))
        self.assertEqual(len(week.days), 7)
        self.assertEqual(
            [day.date for day in week.days],
            [date(2026, 9, 14) + timedelta(days=offset) for offset in range(7)],
        )

    def test_week_is_owner_scoped(self):
        MealPlanEntry.objects.create(
            user=self.other_user,
            date=self.today,
            name="Private dinner",
        )

        week = meal_plan_week(
            user=self.user,
            anchor=self.today,
            today=self.today,
        )

        self.assertTrue(all(day.entry is None for day in week.days))

    def test_future_recipe_readiness_uses_planned_date(self):
        recipe = self.recipe("Yoghurt bowl", "meal-selector-yoghurt")
        yoghurt = Ingredient.objects.create(
            name="Yoghurt",
            category=Ingredient.Category.DAIRY,
        )
        self.add_line(recipe, yoghurt)
        planned_date = self.today + timedelta(days=3)
        PantryItem.objects.create(
            user=self.user,
            ingredient=yoghurt,
            name="Yoghurt",
            approximate_level=PantryItem.ApproximateLevel.FULL,
            expires_on=self.today + timedelta(days=1),
        )
        MealPlanEntry.objects.create(
            user=self.user,
            date=planned_date,
            recipe=recipe,
            name=recipe.title,
        )

        week = meal_plan_week(
            user=self.user,
            anchor=planned_date,
            today=self.today,
        )
        day = next(day for day in week.days if day.date == planned_date)

        self.assertIsNotNone(day.readiness)
        self.assertEqual(day.readiness.unknown_count, 1)
        self.assertEqual(day.readiness.needed_count, 0)

    def test_custom_dinner_has_no_recipe_readiness(self):
        MealPlanEntry.objects.create(
            user=self.user,
            date=self.today,
            name="Soup and sandwiches",
        )

        week = meal_plan_week(
            user=self.user,
            anchor=self.today,
            today=self.today,
        )
        day = next(day for day in week.days if day.date == self.today)

        self.assertIsNone(day.readiness)
        self.assertFalse(day.recipe_available)

    def test_recipe_options_rank_ready_then_known_shortage_then_uncertain(self):
        milk = Ingredient.objects.create(
            name="Milk",
            category=Ingredient.Category.DAIRY,
        )
        flour = Ingredient.objects.create(
            name="Flour",
            category=Ingredient.Category.PANTRY,
        )
        oil = Ingredient.objects.create(
            name="Oil",
            category=Ingredient.Category.PANTRY,
        )

        ready = self.recipe("Ready dinner", "meal-selector-ready", minutes=30)
        missing = self.recipe("Missing dinner", "meal-selector-missing", minutes=15)
        uncertain = self.recipe("Uncertain dinner", "meal-selector-uncertain", minutes=10)

        self.add_line(ready, milk)
        self.add_line(
            missing,
            flour,
            amount=Decimal("500"),
            unit=RecipeIngredient.Unit.GRAM,
        )
        self.add_line(
            uncertain,
            oil,
            amount=Decimal("2"),
            unit=RecipeIngredient.Unit.TABLESPOON,
        )

        PantryItem.objects.create(
            user=self.user,
            ingredient=milk,
            name="Milk",
            approximate_level=PantryItem.ApproximateLevel.FULL,
        )
        PantryItem.objects.create(
            user=self.user,
            ingredient=oil,
            name="Oil",
            quantity_mode=PantryItem.QuantityMode.PRECISE,
            approximate_level="",
            amount=Decimal("500"),
            unit=PantryItem.Unit.MILLILITRE,
        )

        options = meal_recipe_options(user=self.user, today=self.today)

        self.assertEqual(
            [option.recipe.title for option in options],
            ["Ready dinner", "Missing dinner", "Uncertain dinner"],
        )
        self.assertIn("Pantry ready", options[0].selection_label)
        self.assertIn("Shopping", options[1].selection_label)
        self.assertIn("check stock", options[2].selection_label)
