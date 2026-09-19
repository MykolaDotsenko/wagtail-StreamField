from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from home.models import HomePage
from household.models import PantryItem, ShoppingItem
from household.recipe_reconciliation import (
    RecipeReadinessState,
    add_needed_recipe_ingredients,
    recipe_readiness,
)
from recipes.models import Ingredient, RecipeIndexPage, RecipeIngredient, RecipePage


class RecipeReconciliationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="recipe-readiness-user",
            password="safe-test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="recipe-readiness-other",
            password="safe-test-password",
        )
        home = HomePage.objects.first()
        self.index = RecipeIndexPage(title="Recipes", slug="recipes-pr9", intro="")
        home.add_child(instance=self.index)
        self.recipe = RecipePage(
            title="Reliable dinner",
            slug="reliable-dinner",
            intro="Structured test recipe.",
            prep_minutes=5,
            cook_minutes=10,
            servings=2,
            instructions=[],
        )
        self.index.add_child(instance=self.recipe)
        self.today = date(2026, 9, 19)

    def add_line(
        self,
        name,
        *,
        amount=None,
        unit="",
        optional=False,
        category=Ingredient.Category.PANTRY,
    ):
        ingredient = Ingredient.objects.create(name=name, category=category)
        line = RecipeIngredient.objects.create(
            page=self.recipe,
            ingredient=ingredient,
            amount=amount,
            unit=unit,
            optional=optional,
        )
        return ingredient, line

    def state_for(self, ingredient):
        snapshot = recipe_readiness(
            recipe=self.recipe,
            user=self.user,
            today=self.today,
        )
        return next(
            item
            for item in snapshot.items
            if item.line.ingredient_id == ingredient.pk
        )

    def test_missing_when_no_owner_scoped_pantry_match_exists(self):
        ingredient, _ = self.add_line(
            "Tomato",
            amount=Decimal("2"),
            unit=RecipeIngredient.Unit.ITEM,
        )

        entry = self.state_for(ingredient)

        self.assertEqual(entry.state, RecipeReadinessState.MISSING)
        self.assertTrue(entry.needs_shopping)

    def test_exact_normalized_name_fallback_supports_legacy_free_text(self):
        ingredient, _ = self.add_line("Rice")
        PantryItem.objects.create(
            user=self.user,
            name="  RICE  ",
            approximate_level=PantryItem.ApproximateLevel.FULL,
        )

        entry = self.state_for(ingredient)

        self.assertEqual(entry.state, RecipeReadinessState.AVAILABLE)
        self.assertIsNone(entry.pantry_item.ingredient_id)

    def test_other_users_pantry_never_counts_as_available(self):
        ingredient, _ = self.add_line("Milk")
        PantryItem.objects.create(
            user=self.other_user,
            ingredient=ingredient,
            name="Milk",
            approximate_level=PantryItem.ApproximateLevel.FULL,
        )

        entry = self.state_for(ingredient)

        self.assertEqual(entry.state, RecipeReadinessState.MISSING)

    def test_expired_stock_degrades_to_unknown(self):
        ingredient, _ = self.add_line("Yoghurt")
        PantryItem.objects.create(
            user=self.user,
            ingredient=ingredient,
            name="Yoghurt",
            approximate_level=PantryItem.ApproximateLevel.FULL,
            expires_on=self.today - timedelta(days=1),
        )

        entry = self.state_for(ingredient)

        self.assertEqual(entry.state, RecipeReadinessState.UNKNOWN)
        self.assertFalse(entry.needs_shopping)

    def test_approximate_required_quantity_preserves_uncertainty(self):
        ingredient, _ = self.add_line(
            "Flour",
            amount=Decimal("500"),
            unit=RecipeIngredient.Unit.GRAM,
        )
        PantryItem.objects.create(
            user=self.user,
            ingredient=ingredient,
            name="Flour",
            approximate_level=PantryItem.ApproximateLevel.FULL,
        )

        entry = self.state_for(ingredient)

        self.assertEqual(entry.state, RecipeReadinessState.UNKNOWN)

    def test_approximate_low_is_actionable_low(self):
        ingredient, _ = self.add_line(
            "Flour",
            amount=Decimal("500"),
            unit=RecipeIngredient.Unit.GRAM,
        )
        PantryItem.objects.create(
            user=self.user,
            ingredient=ingredient,
            name="Flour",
            approximate_level=PantryItem.ApproximateLevel.LOW,
        )

        entry = self.state_for(ingredient)

        self.assertEqual(entry.state, RecipeReadinessState.LOW)
        self.assertTrue(entry.needs_shopping)

    def test_safe_mass_conversion_can_prove_availability(self):
        ingredient, _ = self.add_line(
            "Flour",
            amount=Decimal("500"),
            unit=RecipeIngredient.Unit.GRAM,
        )
        PantryItem.objects.create(
            user=self.user,
            ingredient=ingredient,
            name="Flour",
            quantity_mode=PantryItem.QuantityMode.PRECISE,
            approximate_level="",
            amount=Decimal("1"),
            unit=PantryItem.Unit.KILOGRAM,
        )

        entry = self.state_for(ingredient)

        self.assertEqual(entry.state, RecipeReadinessState.AVAILABLE)

    def test_safe_mass_conversion_detects_insufficient_stock(self):
        ingredient, _ = self.add_line(
            "Flour",
            amount=Decimal("500"),
            unit=RecipeIngredient.Unit.GRAM,
        )
        PantryItem.objects.create(
            user=self.user,
            ingredient=ingredient,
            name="Flour",
            quantity_mode=PantryItem.QuantityMode.PRECISE,
            approximate_level="",
            amount=Decimal("0.25"),
            unit=PantryItem.Unit.KILOGRAM,
        )

        entry = self.state_for(ingredient)

        self.assertEqual(entry.state, RecipeReadinessState.LOW)

    def test_unsupported_recipe_unit_degrades_to_unknown(self):
        ingredient, _ = self.add_line(
            "Oil",
            amount=Decimal("2"),
            unit=RecipeIngredient.Unit.TABLESPOON,
        )
        PantryItem.objects.create(
            user=self.user,
            ingredient=ingredient,
            name="Oil",
            quantity_mode=PantryItem.QuantityMode.PRECISE,
            approximate_level="",
            amount=Decimal("500"),
            unit=PantryItem.Unit.MILLILITRE,
        )

        entry = self.state_for(ingredient)

        self.assertEqual(entry.state, RecipeReadinessState.UNKNOWN)

    def test_optional_missing_ingredient_is_not_auto_shopping_demand(self):
        ingredient, _ = self.add_line(
            "Parsley",
            optional=True,
            category=Ingredient.Category.PRODUCE,
        )

        entry = self.state_for(ingredient)
        snapshot = recipe_readiness(
            recipe=self.recipe,
            user=self.user,
            today=self.today,
        )

        self.assertEqual(entry.state, RecipeReadinessState.MISSING)
        self.assertFalse(entry.needs_shopping)
        self.assertEqual(snapshot.needed_count, 0)

    def test_add_needed_items_is_idempotent_and_excludes_unknown(self):
        tomato, _ = self.add_line(
            "Tomato",
            amount=Decimal("2"),
            unit=RecipeIngredient.Unit.ITEM,
            category=Ingredient.Category.PRODUCE,
        )
        salt, _ = self.add_line(
            "Salt",
            category=Ingredient.Category.PANTRY,
        )
        oil, _ = self.add_line(
            "Oil",
            amount=Decimal("2"),
            unit=RecipeIngredient.Unit.TABLESPOON,
            category=Ingredient.Category.PANTRY,
        )
        parsley, _ = self.add_line(
            "Parsley",
            optional=True,
            category=Ingredient.Category.PRODUCE,
        )
        PantryItem.objects.create(
            user=self.user,
            ingredient=salt,
            name="Salt",
            approximate_level=PantryItem.ApproximateLevel.LOW,
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

        first = add_needed_recipe_ingredients(recipe=self.recipe, user=self.user)
        second = add_needed_recipe_ingredients(recipe=self.recipe, user=self.user)

        self.assertEqual(first.added_count, 2)
        self.assertEqual(first.existing_count, 0)
        self.assertEqual(first.considered_count, 2)
        self.assertEqual(second.added_count, 0)
        self.assertEqual(second.existing_count, 2)
        self.assertEqual(ShoppingItem.objects.filter(user=self.user).count(), 2)
        self.assertEqual(
            set(
                ShoppingItem.objects.filter(user=self.user).values_list(
                    "ingredient_id",
                    flat=True,
                )
            ),
            {tomato.pk, salt.pk},
        )
        self.assertFalse(
            ShoppingItem.objects.filter(user=self.user, ingredient=oil).exists()
        )
        self.assertFalse(
            ShoppingItem.objects.filter(user=self.user, ingredient=parsley).exists()
        )
        self.assertTrue(
            all(
                quantity == 1
                for quantity in ShoppingItem.objects.filter(user=self.user).values_list(
                    "quantity",
                    flat=True,
                )
            )
        )

    def test_existing_free_text_shopping_row_is_reused_and_canonicalized(self):
        tomato, _ = self.add_line(
            "Tomato",
            amount=Decimal("2"),
            unit=RecipeIngredient.Unit.ITEM,
            category=Ingredient.Category.PRODUCE,
        )
        existing = ShoppingItem.objects.create(
            user=self.user,
            name="tomato",
            quantity=1,
            category=ShoppingItem.Category.OTHER,
        )

        result = add_needed_recipe_ingredients(recipe=self.recipe, user=self.user)

        existing.refresh_from_db()
        self.assertEqual(result.added_count, 0)
        self.assertEqual(result.existing_count, 1)
        self.assertEqual(existing.quantity, 1)
        self.assertEqual(existing.ingredient_id, tomato.pk)
        self.assertEqual(existing.category, ShoppingItem.Category.PRODUCE)
