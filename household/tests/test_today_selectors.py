from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from household.models import MealPlanEntry, PantryItem, Routine, ShoppingItem
from household.selectors import today_snapshot


class TodaySelectorTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="today-selector-user",
            password="safe-test-password",
        )

    def test_priority_order_is_deterministic(self):
        today = date(2026, 9, 19)

        Routine.objects.create(
            user=self.user,
            title="Overdue bathroom",
            frequency=Routine.Frequency.WEEKLY,
            due_on=today - timedelta(days=2),
        )
        PantryItem.objects.create(
            user=self.user,
            name="Expired spinach",
            expires_on=today - timedelta(days=1),
        )
        Routine.objects.create(
            user=self.user,
            title="Due kitchen",
            frequency=Routine.Frequency.DAILY,
            due_on=today,
        )
        PantryItem.objects.create(
            user=self.user,
            name="Soon yoghurt",
            expires_on=today + timedelta(days=2),
        )
        PantryItem.objects.create(
            user=self.user,
            name="Low rice",
            approximate_level=PantryItem.ApproximateLevel.LOW,
        )
        ShoppingItem.objects.create(user=self.user, name="Bread")
        MealPlanEntry.objects.create(user=self.user, date=today, name="Soup")

        snapshot = today_snapshot(user=self.user, today=today)

        self.assertEqual(
            [signal.kind for signal in snapshot.signals],
            [
                "routine_overdue",
                "pantry_expired",
                "routine_today",
                "pantry_use_soon",
                "pantry_low",
                "shopping",
            ],
        )

    def test_pantry_item_emits_only_its_strongest_reason(self):
        today = date(2026, 9, 19)
        PantryItem.objects.create(
            user=self.user,
            name="Milk",
            approximate_level=PantryItem.ApproximateLevel.LOW,
            expires_on=today - timedelta(days=1),
        )
        MealPlanEntry.objects.create(user=self.user, date=today, name="Soup")

        snapshot = today_snapshot(user=self.user, today=today)

        self.assertEqual(len(snapshot.signals), 1)
        self.assertEqual(snapshot.signals[0].kind, "pantry_expired")

    def test_feed_is_capped_but_total_attention_is_preserved(self):
        today = date(2026, 9, 19)
        MealPlanEntry.objects.create(user=self.user, date=today, name="Soup")
        for index in range(8):
            Routine.objects.create(
                user=self.user,
                title=f"Routine {index}",
                frequency=Routine.Frequency.DAILY,
                due_on=today,
            )

        snapshot = today_snapshot(user=self.user, today=today, limit=6)

        self.assertEqual(len(snapshot.signals), 6)
        self.assertEqual(snapshot.total_action_count, 8)
        self.assertTrue(snapshot.has_more)

    def test_private_state_from_other_user_never_enters_today(self):
        other = get_user_model().objects.create_user(
            username="today-selector-other",
            password="safe-test-password",
        )
        today = date(2026, 9, 19)
        Routine.objects.create(
            user=other,
            title="Private routine",
            frequency=Routine.Frequency.DAILY,
            due_on=today,
        )
        PantryItem.objects.create(
            user=other,
            name="Private pantry",
            approximate_level=PantryItem.ApproximateLevel.LOW,
        )
        ShoppingItem.objects.create(user=other, name="Private shopping")
        MealPlanEntry.objects.create(user=self.user, date=today, name="Soup")

        snapshot = today_snapshot(user=self.user, today=today)

        self.assertEqual(snapshot.signals, ())
        self.assertEqual(snapshot.shopping_count, 0)

    def test_unplanned_dinner_is_attention_before_shopping(self):
        today = date(2026, 9, 19)
        ShoppingItem.objects.create(user=self.user, name="Bread")

        snapshot = today_snapshot(user=self.user, today=today)

        self.assertEqual(
            [signal.kind for signal in snapshot.signals],
            ["dinner_unplanned", "shopping"],
        )
        self.assertEqual(snapshot.dinner_name, None)

    def test_planned_custom_dinner_removes_unplanned_signal(self):
        today = date(2026, 9, 19)
        MealPlanEntry.objects.create(
            user=self.user,
            date=today,
            name="Soup and sandwiches",
        )

        snapshot = today_snapshot(user=self.user, today=today)

        self.assertFalse(any(signal.kind == "dinner_unplanned" for signal in snapshot.signals))
        self.assertEqual(snapshot.dinner_name, "Soup and sandwiches")
        self.assertEqual(snapshot.dinner_needed_count, 0)
        self.assertEqual(snapshot.dinner_unknown_count, 0)
