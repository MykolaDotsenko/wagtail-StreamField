from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from home.models import HomePage
from household.models import MealPlanEntry, PantryItem
from household.selectors import meal_plan_week, meal_recipe_options, today_snapshot, week_start
from recipes.models import Ingredient, RecipeIndexPage, RecipeIngredient, RecipePage


class HouseholdQueryBudgetTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="query-budget-user",
            password="safe-test-password",
        )
        self.today = timezone.localdate()
        home = HomePage.objects.first()
        self.index = RecipeIndexPage(
            title="Performance recipes",
            slug="performance-recipes",
            intro="",
        )
        home.add_child(instance=self.index)

        self.flour = Ingredient.objects.create(
            name="Query flour",
            category=Ingredient.Category.PANTRY,
        )
        PantryItem.objects.create(
            user=self.user,
            ingredient=self.flour,
            name=self.flour.name,
            quantity_mode=PantryItem.QuantityMode.PRECISE,
            approximate_level="",
            amount=Decimal("2"),
            unit=PantryItem.Unit.KILOGRAM,
        )

    def create_recipe(self, number):
        recipe = RecipePage(
            title=f"Query dinner {number}",
            slug=f"query-dinner-{number}",
            intro="Performance fixture.",
            prep_minutes=5,
            cook_minutes=10,
            servings=2,
            instructions=[],
        )
        self.index.add_child(instance=recipe)
        RecipeIngredient.objects.create(
            page=recipe,
            ingredient=self.flour,
            amount=Decimal("200"),
            unit=RecipeIngredient.Unit.GRAM,
        )
        return recipe

    def test_recipe_picker_query_count_does_not_scale_with_recipe_count(self):
        for number in range(8):
            self.create_recipe(number)

        with CaptureQueriesContext(connection) as queries:
            options = meal_recipe_options(user=self.user, today=self.today)
            self.assertEqual(len(options), 8)
            self.assertTrue(all(option.readiness.available_count == 1 for option in options))

        self.assertLessEqual(
            len(queries),
            4,
            f"Recipe picker exceeded query budget: {len(queries)} queries",
        )

    def test_weekly_plan_query_count_does_not_scale_per_planned_recipe(self):
        start = week_start(self.today)
        for offset in range(7):
            recipe = self.create_recipe(offset)
            MealPlanEntry.objects.create(
                user=self.user,
                date=start + timedelta(days=offset),
                recipe=recipe,
                name=recipe.title,
            )

        with CaptureQueriesContext(connection) as queries:
            week = meal_plan_week(
                user=self.user,
                anchor=start,
                today=self.today,
            )
            self.assertEqual(
                sum(day.readiness is not None for day in week.days),
                7,
            )

        self.assertLessEqual(
            len(queries),
            5,
            f"Weekly plan exceeded query budget: {len(queries)} queries",
        )

    def test_today_reuses_loaded_pantry_for_dinner_readiness(self):
        recipe = self.create_recipe(1)
        MealPlanEntry.objects.create(
            user=self.user,
            date=self.today,
            recipe=recipe,
            name=recipe.title,
        )

        with CaptureQueriesContext(connection) as queries:
            snapshot = today_snapshot(user=self.user, today=self.today)
            self.assertEqual(snapshot.dinner_name, recipe.title)

        self.assertLessEqual(
            len(queries),
            7,
            f"Today exceeded query budget: {len(queries)} queries",
        )
