from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from household.models import Routine
from household.selectors import routine_snapshot


class RoutineSelectorTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="routine-selector-user",
            password="safe-test-password",
        )

    def test_due_and_upcoming_are_partitioned_by_effective_date(self):
        today = date(2026, 9, 19)
        Routine.objects.create(
            user=self.user,
            title="Overdue",
            due_on=date(2026, 9, 18),
        )
        Routine.objects.create(
            user=self.user,
            title="Today",
            due_on=today,
        )
        Routine.objects.create(
            user=self.user,
            title="Later",
            due_on=date(2026, 9, 22),
        )

        snapshot = routine_snapshot(user=self.user, today=today)

        self.assertEqual(
            [entry.routine.title for entry in snapshot.due_items],
            ["Overdue", "Today"],
        )
        self.assertEqual(
            [entry.routine.title for entry in snapshot.upcoming_items],
            ["Later"],
        )

    def test_postponed_effective_date_moves_item_to_upcoming(self):
        today = date(2026, 9, 19)
        Routine.objects.create(
            user=self.user,
            title="Postponed",
            due_on=date(2026, 9, 18),
            postponed_until=date(2026, 9, 21),
        )

        snapshot = routine_snapshot(user=self.user, today=today)

        self.assertEqual(snapshot.due_items, ())
        self.assertEqual(snapshot.upcoming_items[0].effective_due_on, date(2026, 9, 21))
        self.assertTrue(snapshot.upcoming_items[0].is_postponed)

    def test_inactive_and_other_user_routines_are_excluded(self):
        other = get_user_model().objects.create_user(
            username="routine-selector-other",
            password="safe-test-password",
        )
        Routine.objects.create(
            user=self.user,
            title="Archived",
            due_on=date(2026, 9, 19),
            active=False,
        )
        Routine.objects.create(
            user=other,
            title="Private",
            due_on=date(2026, 9, 19),
        )

        snapshot = routine_snapshot(user=self.user, today=date(2026, 9, 19))

        self.assertEqual(snapshot.total_active, 0)
