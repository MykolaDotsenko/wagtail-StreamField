from datetime import date

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

from household.models import Routine, RoutineEvent


class RoutineModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="routine-model-user",
            password="safe-test-password",
        )

    def test_monthly_routine_requires_anchor(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Routine.objects.create(
                user=self.user,
                title="Deep clean",
                frequency=Routine.Frequency.MONTHLY,
                due_on=date(2026, 1, 31),
            )

    def test_non_monthly_routine_rejects_anchor(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Routine.objects.create(
                user=self.user,
                title="Vacuum",
                frequency=Routine.Frequency.WEEKLY,
                due_on=date(2026, 9, 19),
                recurrence_anchor_day=19,
            )

    def test_postponement_must_be_after_schedule(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Routine.objects.create(
                user=self.user,
                title="Laundry",
                due_on=date(2026, 9, 19),
                postponed_until=date(2026, 9, 19),
            )

    def test_duration_must_be_positive(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            Routine.objects.create(
                user=self.user,
                title="Laundry",
                due_on=date(2026, 9, 19),
                expected_duration_minutes=0,
            )

    def test_terminal_event_cannot_have_postpone_target(self):
        routine = Routine.objects.create(
            user=self.user,
            title="Laundry",
            due_on=date(2026, 9, 19),
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            RoutineEvent.objects.create(
                routine=routine,
                scheduled_for=routine.due_on,
                outcome=RoutineEvent.Outcome.COMPLETED,
                postponed_to=date(2026, 9, 20),
            )

    def test_terminal_outcome_is_unique_per_scheduled_occurrence(self):
        routine = Routine.objects.create(
            user=self.user,
            title="Laundry",
            due_on=date(2026, 9, 19),
        )
        RoutineEvent.objects.create(
            routine=routine,
            scheduled_for=routine.due_on,
            outcome=RoutineEvent.Outcome.COMPLETED,
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            RoutineEvent.objects.create(
                routine=routine,
                scheduled_for=routine.due_on,
                outcome=RoutineEvent.Outcome.SKIPPED,
            )
