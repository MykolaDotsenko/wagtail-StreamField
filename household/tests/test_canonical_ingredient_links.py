from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from household.models import PantryItem, ShoppingItem
from recipes.models import Ingredient


class CanonicalIngredientLinkTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="canonical-link-user",
            password="safe-test-password",
        )
        self.ingredient = Ingredient.objects.create(
            name="Milk",
            category=Ingredient.Category.DAIRY,
        )

    def test_pantry_allows_only_one_row_per_canonical_ingredient(self):
        PantryItem.objects.create(
            user=self.user,
            ingredient=self.ingredient,
            name="Milk",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            PantryItem.objects.create(
                user=self.user,
                ingredient=self.ingredient,
                name="Whole milk",
            )

    def test_shopping_allows_only_one_open_demand_per_canonical_ingredient(self):
        ShoppingItem.objects.create(
            user=self.user,
            ingredient=self.ingredient,
            name="Milk",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            ShoppingItem.objects.create(
                user=self.user,
                ingredient=self.ingredient,
                name="Whole milk",
            )

    def test_completed_canonical_shopping_history_does_not_block_new_open_demand(self):
        completed = ShoppingItem.objects.create(
            user=self.user,
            ingredient=self.ingredient,
            name="Milk",
        )
        completed.complete()
        completed.save()

        current = ShoppingItem.objects.create(
            user=self.user,
            ingredient=self.ingredient,
            name="Whole milk",
        )

        self.assertIsNotNone(current.pk)
