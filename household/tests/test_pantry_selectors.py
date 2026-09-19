from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from household.models import PantryItem
from household.selectors import pantry_snapshot


class PantrySelectorTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="pantry-selector-user",
            password="safe-test-password",
        )

    def test_attention_prioritizes_expired_then_use_soon_then_low(self):
        today = date(2026, 9, 19)
        PantryItem.objects.create(
            user=self.user,
            name="Low rice",
            approximate_level=PantryItem.ApproximateLevel.LOW,
        )
        PantryItem.objects.create(
            user=self.user,
            name="Soon yoghurt",
            expires_on=today + timedelta(days=2),
        )
        PantryItem.objects.create(
            user=self.user,
            name="Expired spinach",
            expires_on=today - timedelta(days=1),
        )

        snapshot = pantry_snapshot(user=self.user, today=today)

        self.assertEqual(
            [entry.item.name for entry in snapshot.attention_items],
            ["Expired spinach", "Soon yoghurt", "Low rice"],
        )

    def test_unknown_expiry_is_explicit_but_not_false_attention(self):
        today = date(2026, 9, 19)
        PantryItem.objects.create(
            user=self.user,
            name="Rice",
        )

        snapshot = pantry_snapshot(user=self.user, today=today)

        self.assertEqual(snapshot.attention_items, ())
        self.assertEqual(len(snapshot.other_items), 1)
        self.assertTrue(snapshot.other_items[0].expiry_unknown)

    def test_other_users_pantry_never_enters_snapshot(self):
        other = get_user_model().objects.create_user(
            username="pantry-selector-other",
            password="safe-test-password",
        )
        PantryItem.objects.create(user=other, name="Private rice")

        snapshot = pantry_snapshot(user=self.user, today=date(2026, 9, 19))

        self.assertEqual(snapshot.total_count, 0)
