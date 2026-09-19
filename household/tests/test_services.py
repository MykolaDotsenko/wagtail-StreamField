from django.contrib.auth import get_user_model
from django.test import TestCase

from household.models import ShoppingItem
from household.services import (
    add_shopping_item,
    delete_shopping_item,
    restore_shopping_item,
    toggle_shopping_item,
)


class ShoppingServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="service-user",
            password="safe-test-password",
        )

    def test_add_name_only_uses_defaults_and_infers_category(self):
        result = add_shopping_item(user=self.user, name="Milk")

        self.assertTrue(result.created)
        self.assertEqual(result.item.quantity, 1)
        self.assertEqual(result.item.category, ShoppingItem.Category.DAIRY)

    def test_duplicate_open_item_merges_quantity(self):
        add_shopping_item(user=self.user, name="Milk", quantity=1)

        result = add_shopping_item(user=self.user, name=" milk ", quantity=2)

        self.assertFalse(result.created)
        self.assertEqual(result.item.quantity, 3)
        self.assertEqual(
            ShoppingItem.objects.filter(
                user=self.user,
                status=ShoppingItem.Status.OPEN,
                deleted_at__isnull=True,
            ).count(),
            1,
        )

    def test_explicit_category_is_respected(self):
        result = add_shopping_item(
            user=self.user,
            name="Special item",
            category=ShoppingItem.Category.PANTRY,
        )

        self.assertEqual(result.item.category, ShoppingItem.Category.PANTRY)

    def test_toggle_completes_and_reopens_item(self):
        item = add_shopping_item(user=self.user, name="Bread").item

        completed = toggle_shopping_item(user=self.user, item_id=item.pk).item
        self.assertTrue(completed.is_completed)
        self.assertIsNotNone(completed.completed_at)

        reopened = toggle_shopping_item(user=self.user, item_id=item.pk).item
        self.assertFalse(reopened.is_completed)
        self.assertIsNone(reopened.completed_at)

    def test_reopen_merges_when_equivalent_open_item_exists(self):
        completed_item = add_shopping_item(
            user=self.user,
            name="Bread",
            quantity=2,
        ).item
        toggle_shopping_item(user=self.user, item_id=completed_item.pk)
        open_item = add_shopping_item(
            user=self.user,
            name="bread",
            quantity=3,
        ).item

        result = toggle_shopping_item(user=self.user, item_id=completed_item.pk)

        self.assertTrue(result.merged)
        self.assertEqual(result.item.pk, open_item.pk)
        self.assertEqual(result.item.quantity, 5)

        completed_item.refresh_from_db()
        self.assertIsNotNone(completed_item.deleted_at)

    def test_delete_and_restore_round_trip(self):
        item = add_shopping_item(user=self.user, name="Eggs").item

        deleted = delete_shopping_item(user=self.user, item_id=item.pk)
        self.assertIsNotNone(deleted.deleted_at)

        restored = restore_shopping_item(user=self.user, item_id=item.pk)
        self.assertFalse(restored.merged)
        self.assertIsNone(restored.item.deleted_at)

    def test_restore_merges_if_same_open_item_was_added_after_delete(self):
        deleted_item = add_shopping_item(
            user=self.user,
            name="Eggs",
            quantity=2,
        ).item
        delete_shopping_item(user=self.user, item_id=deleted_item.pk)
        active_item = add_shopping_item(
            user=self.user,
            name="eggs",
            quantity=1,
        ).item

        result = restore_shopping_item(user=self.user, item_id=deleted_item.pk)

        self.assertTrue(result.merged)
        self.assertEqual(result.item.pk, active_item.pk)
        self.assertEqual(result.item.quantity, 3)

        self.assertFalse(ShoppingItem.objects.filter(pk=deleted_item.pk).exists())
