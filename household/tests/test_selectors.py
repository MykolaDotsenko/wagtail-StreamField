from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from household.models import ShoppingItem
from household.selectors import shopping_snapshot


class ShoppingSelectorTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="selector-user",
            password="safe-test-password",
        )

    def test_snapshot_groups_open_items_and_separates_completed(self):
        ShoppingItem.objects.create(
            user=self.user,
            name="Milk",
            category=ShoppingItem.Category.DAIRY,
        )
        ShoppingItem.objects.create(
            user=self.user,
            name="Tomatoes",
            category=ShoppingItem.Category.PRODUCE,
        )
        ShoppingItem.objects.create(
            user=self.user,
            name="Bread",
            category=ShoppingItem.Category.BAKERY,
            status=ShoppingItem.Status.COMPLETED,
            completed_at=timezone.now(),
        )
        ShoppingItem.objects.create(
            user=self.user,
            name="Deleted",
            deleted_at=timezone.now(),
        )

        snapshot = shopping_snapshot(user=self.user)

        self.assertEqual(snapshot.open_count, 2)
        self.assertEqual(snapshot.completed_count, 1)
        self.assertEqual(
            [group.key for group in snapshot.open_groups],
            [ShoppingItem.Category.PRODUCE, ShoppingItem.Category.DAIRY],
        )
        self.assertEqual(snapshot.completed_items[0].name, "Bread")
