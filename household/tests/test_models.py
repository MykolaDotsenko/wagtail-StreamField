from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from household.models import ShoppingItem


class ShoppingItemModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="model-user",
            password="safe-test-password",
        )

    def test_name_is_normalized_for_display_and_identity(self):
        item = ShoppingItem.objects.create(
            user=self.user,
            name="  Ｍilk   2%  ",
        )

        self.assertEqual(item.name, "Milk 2%")
        self.assertEqual(item.normalized_name, "milk 2%")

    def test_database_prevents_duplicate_open_identity_for_same_user(self):
        ShoppingItem.objects.create(user=self.user, name="Milk")

        with self.assertRaises(IntegrityError), transaction.atomic():
            ShoppingItem.objects.create(user=self.user, name="  MILK  ")

    def test_same_identity_can_exist_as_completed_and_open(self):
        from django.utils import timezone

        completed = ShoppingItem.objects.create(
            user=self.user,
            name="Milk",
            status=ShoppingItem.Status.COMPLETED,
            completed_at=timezone.now(),
        )
        open_item = ShoppingItem.objects.create(user=self.user, name="milk")

        self.assertNotEqual(completed.pk, open_item.pk)

    def test_empty_normalized_identity_is_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ShoppingItem.objects.create(
                user=self.user,
                name="   ",
            )

    def test_completed_state_requires_completed_timestamp(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ShoppingItem.objects.create(
                user=self.user,
                name="Bread",
                status=ShoppingItem.Status.COMPLETED,
            )

    def test_quantity_must_be_at_least_one(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            ShoppingItem.objects.create(
                user=self.user,
                name="Milk",
                quantity=0,
            )
