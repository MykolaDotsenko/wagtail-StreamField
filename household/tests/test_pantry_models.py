from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from household.models import PantryItem, ShoppingItem


class PantryItemModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="pantry-model-user",
            password="safe-test-password",
        )

    def test_approximate_item_is_low_maintenance_by_default(self):
        item = PantryItem.objects.create(
            user=self.user,
            name="Rice",
        )

        self.assertEqual(item.quantity_mode, PantryItem.QuantityMode.APPROXIMATE)
        self.assertEqual(item.approximate_level, PantryItem.ApproximateLevel.FULL)
        self.assertEqual(item.quantity_label, "Full")
        self.assertIsNone(item.amount)
        self.assertEqual(item.unit, "")

    def test_precise_quantity_label(self):
        item = PantryItem.objects.create(
            user=self.user,
            name="Flour",
            quantity_mode=PantryItem.QuantityMode.PRECISE,
            approximate_level="",
            amount=Decimal("1.50"),
            unit=PantryItem.Unit.KILOGRAM,
        )

        self.assertEqual(item.quantity_label, "1.5 kg")

    def test_duplicate_normalized_name_is_rejected_per_user(self):
        PantryItem.objects.create(user=self.user, name="Milk")

        with self.assertRaises(IntegrityError), transaction.atomic():
            PantryItem.objects.create(user=self.user, name="  MILK ")

    def test_same_normalized_name_is_allowed_for_different_user(self):
        other = get_user_model().objects.create_user(
            username="pantry-other-user",
            password="safe-test-password",
        )
        PantryItem.objects.create(user=self.user, name="Milk")
        second = PantryItem.objects.create(user=other, name="milk")

        self.assertIsNotNone(second.pk)

    def test_precise_mode_requires_amount_and_unit(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            PantryItem.objects.create(
                user=self.user,
                name="Flour",
                quantity_mode=PantryItem.QuantityMode.PRECISE,
                approximate_level="",
            )

    def test_approximate_mode_rejects_precise_amount(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            PantryItem.objects.create(
                user=self.user,
                name="Flour",
                amount=Decimal("1.00"),
            )

    def test_negative_precise_amount_is_rejected(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            PantryItem.objects.create(
                user=self.user,
                name="Flour",
                quantity_mode=PantryItem.QuantityMode.PRECISE,
                approximate_level="",
                amount=Decimal("-1"),
                unit=PantryItem.Unit.KILOGRAM,
            )

    def test_low_stock_is_derived_for_both_tracking_modes(self):
        approximate = PantryItem.objects.create(
            user=self.user,
            name="Milk",
            approximate_level=PantryItem.ApproximateLevel.LOW,
        )
        precise = PantryItem.objects.create(
            user=self.user,
            name="Coffee",
            quantity_mode=PantryItem.QuantityMode.PRECISE,
            approximate_level="",
            amount=Decimal("100"),
            unit=PantryItem.Unit.GRAM,
            low_stock_threshold=Decimal("150"),
        )

        self.assertTrue(approximate.is_low_stock)
        self.assertTrue(precise.is_low_stock)

    def test_expiry_states_are_derived_and_unknown_remains_unknown(self):
        today = date(2026, 9, 19)
        unknown = PantryItem.objects.create(user=self.user, name="Rice")
        soon = PantryItem.objects.create(
            user=self.user,
            name="Yoghurt",
            expires_on=today + timedelta(days=3),
            category=ShoppingItem.Category.DAIRY,
        )
        expired = PantryItem.objects.create(
            user=self.user,
            name="Spinach",
            expires_on=today - timedelta(days=1),
            category=ShoppingItem.Category.PRODUCE,
        )

        self.assertTrue(unknown.has_unknown_expiry)
        self.assertTrue(soon.expires_soon(today=today))
        self.assertFalse(soon.is_expired(today=today))
        self.assertTrue(expired.is_expired(today=today))
        self.assertFalse(expired.expires_soon(today=today))
