from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from household.models import Routine, RoutineEvent
from household.services import (
    StaleRoutineAction,
    archive_routine,
    complete_routine,
    create_routine,
    next_routine_due_date,
    postpone_routine,
    skip_routine,
)


def routine_data(**overrides):
    data = {
        "title": "Clean bathroom",
        "room": Routine.Room.BATHROOM,
        "frequency": Routine.Frequency.WEEKLY,
        "due_on": date(2026, 9, 19),
        "expected_duration_minutes": 20,
    }
    data.update(overrides)
    return data


class RecurrenceCalculationTests(TestCase):
    def test_daily_overdue_collapses_backlog_to_next_day(self):
        next_due = next_routine_due_date(
            frequency=Routine.Frequency.DAILY,
            current_due=date(2026, 9, 10),
            anchor_day=None,
            after_date=date(2026, 9, 19),
        )

        self.assertEqual(next_due, date(2026, 9, 20))

    def test_weekly_overdue_advances_to_first_future_cadence(self):
        next_due = next_routine_due_date(
            frequency=Routine.Frequency.WEEKLY,
            current_due=date(2026, 9, 1),
            anchor_day=None,
            after_date=date(2026, 9, 19),
        )

        self.assertEqual(next_due, date(2026, 9, 22))

    def test_monthly_anchor_survives_short_february(self):
        february = next_routine_due_date(
            frequency=Routine.Frequency.MONTHLY,
            current_due=date(2027, 1, 31),
            anchor_day=31,
            after_date=date(2027, 2, 1),
        )
        march = next_routine_due_date(
            frequency=Routine.Frequency.MONTHLY,
            current_due=february,
            anchor_day=31,
            after_date=february,
        )

        self.assertEqual(february, date(2027, 2, 28))
        self.assertEqual(march, date(2027, 3, 31))

    def test_monthly_anchor_handles_leap_year(self):
        next_due = next_routine_due_date(
            frequency=Routine.Frequency.MONTHLY,
            current_due=date(2028, 1, 31),
            anchor_day=31,
            after_date=date(2028, 2, 1),
        )

        self.assertEqual(next_due, date(2028, 2, 29))


class RoutineServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="routine-service-user",
            password="safe-test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="routine-service-other",
            password="safe-test-password",
        )

    def test_create_monthly_routine_sets_anchor_from_due_date(self):
        routine = create_routine(
            user=self.user,
            data=routine_data(
                frequency=Routine.Frequency.MONTHLY,
                due_on=date(2026, 1, 31),
            ),
        )

        self.assertEqual(routine.recurrence_anchor_day, 31)

    def test_complete_records_history_and_advances_schedule(self):
        routine = create_routine(user=self.user, data=routine_data())

        updated = complete_routine(
            user=self.user,
            routine_id=routine.pk,
            expected_scheduled_for=routine.due_on,
            today=date(2026, 9, 19),
        )

        self.assertEqual(updated.due_on, date(2026, 9, 26))
        event = RoutineEvent.objects.get(routine=routine)
        self.assertEqual(event.outcome, RoutineEvent.Outcome.COMPLETED)
        self.assertEqual(event.scheduled_for, date(2026, 9, 19))

    def test_skip_is_distinct_history_outcome(self):
        routine = create_routine(user=self.user, data=routine_data())

        skip_routine(
            user=self.user,
            routine_id=routine.pk,
            expected_scheduled_for=routine.due_on,
            today=date(2026, 9, 19),
        )

        event = RoutineEvent.objects.get(routine=routine)
        self.assertEqual(event.outcome, RoutineEvent.Outcome.SKIPPED)

    def test_one_time_completion_deactivates_but_preserves_history(self):
        routine = create_routine(
            user=self.user,
            data=routine_data(frequency=Routine.Frequency.ONE_TIME),
        )

        updated = complete_routine(
            user=self.user,
            routine_id=routine.pk,
            expected_scheduled_for=routine.due_on,
            today=date(2026, 9, 19),
        )

        self.assertFalse(updated.active)
        self.assertTrue(RoutineEvent.objects.filter(routine=routine).exists())

    def test_postpone_does_not_change_monthly_cadence(self):
        routine = create_routine(
            user=self.user,
            data=routine_data(
                frequency=Routine.Frequency.MONTHLY,
                due_on=date(2027, 1, 31),
            ),
        )

        postponed = postpone_routine(
            user=self.user,
            routine_id=routine.pk,
            expected_scheduled_for=date(2027, 1, 31),
            expected_effective_due_on=date(2027, 1, 31),
            postponed_to=date(2027, 2, 2),
        )
        completed = complete_routine(
            user=self.user,
            routine_id=postponed.pk,
            expected_scheduled_for=date(2027, 1, 31),
            today=date(2027, 2, 2),
        )

        self.assertEqual(completed.due_on, date(2027, 2, 28))
        self.assertEqual(completed.recurrence_anchor_day, 31)
        self.assertIsNone(completed.postponed_until)

    def test_double_terminal_submission_is_stale_not_next_occurrence(self):
        routine = create_routine(user=self.user, data=routine_data())
        expected = routine.due_on

        complete_routine(
            user=self.user,
            routine_id=routine.pk,
            expected_scheduled_for=expected,
            today=date(2026, 9, 19),
        )

        with self.assertRaises(StaleRoutineAction):
            complete_routine(
                user=self.user,
                routine_id=routine.pk,
                expected_scheduled_for=expected,
                today=date(2026, 9, 19),
            )

        self.assertEqual(RoutineEvent.objects.filter(routine=routine).count(), 1)

    def test_double_postpone_submission_is_stale(self):
        routine = create_routine(user=self.user, data=routine_data())

        postpone_routine(
            user=self.user,
            routine_id=routine.pk,
            expected_scheduled_for=routine.due_on,
            expected_effective_due_on=routine.due_on,
            postponed_to=date(2026, 9, 20),
        )

        with self.assertRaises(StaleRoutineAction):
            postpone_routine(
                user=self.user,
                routine_id=routine.pk,
                expected_scheduled_for=routine.due_on,
                expected_effective_due_on=date(2026, 9, 19),
                postponed_to=date(2026, 9, 21),
            )

    def test_cross_user_completion_is_blocked(self):
        routine = create_routine(user=self.other_user, data=routine_data())

        with self.assertRaises(Routine.DoesNotExist):
            complete_routine(
                user=self.user,
                routine_id=routine.pk,
                expected_scheduled_for=routine.due_on,
                today=date(2026, 9, 19),
            )

    def test_archive_preserves_history(self):
        routine = create_routine(user=self.user, data=routine_data())
        complete_routine(
            user=self.user,
            routine_id=routine.pk,
            expected_scheduled_for=routine.due_on,
            today=date(2026, 9, 19),
        )

        archived = archive_routine(user=self.user, routine_id=routine.pk)

        self.assertFalse(archived.active)
        self.assertEqual(RoutineEvent.objects.filter(routine=routine).count(), 1)
