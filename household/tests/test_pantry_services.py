from django.contrib.auth import get_user_model
from django.test import TestCase

from household.models import PantryItem, ShoppingItem
from household.services import (
    add_pantry_item_to_shopping,
    create_pantry_item,
    delete_pantry_item,
    update_pantry_item,
)


def pantry_data(**overrides):
    data = {
        "name": "Rice",
        "category": ShoppingItem.Category.PANTRY,
        "quantity_mode": PantryItem.QuantityMode.APPROXIMATE,
        "approximate_level": PantryItem.ApproximateLevel.FULL,
        "amount": None,
        "unit": "",
        "low_stock_threshold": None,
        "expires_on": None,
    }
    data.update(overrides)
    return data


class PantryServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="pantry-service-user",
            password="safe-test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="pantry-service-other",
            password="safe-test-password",
        )

    def test_create_and_update_are_explicit_commands(self):
        item = create_pantry_item(
            user=self.user,
            data=pantry_data(),
        )

        updated = update_pantry_item(
            user=self.user,
            item_id=item.pk,
            data=pantry_data(
                approximate_level=PantryItem.ApproximateLevel.LOW,
            ),
        )

        self.assertEqual(updated.approximate_level, PantryItem.ApproximateLevel.LOW)

    def test_update_is_owner_scoped(self):
        item = create_pantry_item(
            user=self.other_user,
            data=pantry_data(),
        )

        with self.assertRaises(PantryItem.DoesNotExist):
            update_pantry_item(
                user=self.user,
                item_id=item.pk,
                data=pantry_data(name="Changed"),
            )

    def test_delete_is_owner_scoped(self):
        item = create_pantry_item(
            user=self.other_user,
            data=pantry_data(),
        )

        with self.assertRaises(PantryItem.DoesNotExist):
            delete_pantry_item(user=self.user, item_id=item.pk)

        self.assertTrue(PantryItem.objects.filter(pk=item.pk).exists())

    def test_add_to_shopping_uses_existing_command_boundary(self):
        item = create_pantry_item(
            user=self.user,
            data=pantry_data(
                name="Milk",
                category=ShoppingItem.Category.DAIRY,
                approximate_level=PantryItem.ApproximateLevel.LOW,
            ),
        )

        result = add_pantry_item_to_shopping(user=self.user, item_id=item.pk)

        self.assertTrue(result.created)
        shopping = ShoppingItem.objects.get(user=self.user)
        self.assertEqual(shopping.name, "Milk")
        self.assertEqual(shopping.category, ShoppingItem.Category.DAIRY)
        self.assertEqual(shopping.quantity, 1)

    def test_add_to_shopping_is_idempotent(self):
        item = create_pantry_item(
            user=self.user,
            data=pantry_data(
                name="Milk",
                category=ShoppingItem.Category.DAIRY,
                approximate_level=PantryItem.ApproximateLevel.LOW,
            ),
        )

        first = add_pantry_item_to_shopping(user=self.user, item_id=item.pk)
        second = add_pantry_item_to_shopping(user=self.user, item_id=item.pk)

        self.assertTrue(first.created)
        self.assertFalse(second.created)
        shopping = ShoppingItem.objects.get(user=self.user)
        self.assertEqual(shopping.quantity, 1)

    def test_add_to_shopping_is_owner_scoped(self):
        item = create_pantry_item(
            user=self.other_user,
            data=pantry_data(),
        )

        with self.assertRaises(PantryItem.DoesNotExist):
            add_pantry_item_to_shopping(user=self.user, item_id=item.pk)
