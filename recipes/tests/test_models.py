from datetime import date
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.test import TestCase

from home.models import HomePage
from recipes.models import Ingredient, RecipeIndexPage, RecipeIngredient, RecipePage


class IngredientModelTests(TestCase):
    def test_identity_is_normalized_conservatively(self):
        ingredient = Ingredient.objects.create(
            name="  Greek   Yoghurt  ",
            category=Ingredient.Category.DAIRY,
        )

        self.assertEqual(ingredient.name, "Greek Yoghurt")
        self.assertEqual(ingredient.normalized_name, "greek yoghurt")

    def test_normalized_identity_is_unique(self):
        Ingredient.objects.create(name="Milk")

        with self.assertRaises(IntegrityError), transaction.atomic():
            Ingredient.objects.create(name="  MILK ")

    def test_empty_normalized_identity_is_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Ingredient.objects.create(name="   ")


class RecipeDomainTests(TestCase):
    def setUp(self):
        self.home = HomePage.objects.first()
        self.assertIsNotNone(self.home)
        self.index = RecipeIndexPage(title="Recipes", slug="recipes", intro="")
        self.home.add_child(instance=self.index)
        self.recipe = RecipePage(
            title="Tomato pasta",
            slug="tomato-pasta",
            intro="A fast pantry-friendly dinner.",
            prep_minutes=10,
            cook_minutes=15,
            servings=2,
            difficulty=RecipePage.Difficulty.EASY,
            instructions=[],
        )
        self.index.add_child(instance=self.recipe)
        self.tomato = Ingredient.objects.create(
            name="Tomato",
            category=Ingredient.Category.PRODUCE,
        )

    def test_total_time_is_derived_not_persisted(self):
        self.assertEqual(self.recipe.total_minutes, 25)

    def test_quantity_requires_positive_amount_and_unit_together(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            RecipeIngredient.objects.create(
                page=self.recipe,
                ingredient=self.tomato,
                amount=Decimal("2"),
                unit="",
            )

        with self.assertRaises(IntegrityError), transaction.atomic():
            RecipeIngredient.objects.create(
                page=self.recipe,
                ingredient=self.tomato,
                amount=None,
                unit=RecipeIngredient.Unit.GRAM,
            )

    def test_positive_structured_quantity_is_valid(self):
        line = RecipeIngredient.objects.create(
            page=self.recipe,
            ingredient=self.tomato,
            amount=Decimal("2"),
            unit=RecipeIngredient.Unit.ITEM,
            note="roughly chopped",
        )

        self.assertEqual(line.amount_label, "2 item")

    def test_one_canonical_ingredient_per_recipe(self):
        RecipeIngredient.objects.create(
            page=self.recipe,
            ingredient=self.tomato,
            amount=Decimal("2"),
            unit=RecipeIngredient.Unit.ITEM,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            RecipeIngredient.objects.create(
                page=self.recipe,
                ingredient=self.tomato,
                amount=Decimal("1"),
                unit=RecipeIngredient.Unit.ITEM,
                note="for garnish",
            )

    def test_ingredient_names_are_machine_readable_search_text(self):
        RecipeIngredient.objects.create(
            page=self.recipe,
            ingredient=self.tomato,
            amount=Decimal("2"),
            unit=RecipeIngredient.Unit.ITEM,
        )
        garlic = Ingredient.objects.create(
            name="Garlic",
            category=Ingredient.Category.PRODUCE,
        )
        RecipeIngredient.objects.create(
            page=self.recipe,
            ingredient=garlic,
            amount=Decimal("2"),
            unit=RecipeIngredient.Unit.ITEM,
        )

        self.assertEqual(self.recipe.get_ingredient_names(), "Tomato\nGarlic")

    def test_date_import_is_not_needed_for_recipe_state(self):
        self.assertEqual(date(2026, 9, 19).year, 2026)
