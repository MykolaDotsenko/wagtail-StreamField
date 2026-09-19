from datetime import date

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from household.models import Routine, RoutineEvent


class RoutineViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="routine-view-user",
            password="safe-test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="routine-view-other",
            password="safe-test-password",
        )

    def _routine(self, *, user=None, due_on=date(2026, 9, 19)):
        return Routine.objects.create(
            user=user or self.user,
            title="Clean bathroom",
            room=Routine.Room.BATHROOM,
            frequency=Routine.Frequency.WEEKLY,
            due_on=due_on,
        )

    def test_routines_require_authentication(self):
        response = self.client.get(reverse("household:routines"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_create_routine_from_minimal_form(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("household:routines"),
            {
                "title": "Water plants",
                "due_on": "2026-09-19",
            },
        )

        self.assertRedirects(response, reverse("household:routines"))
        routine = Routine.objects.get(user=self.user)
        self.assertEqual(routine.frequency, Routine.Frequency.WEEKLY)
        self.assertEqual(routine.room, Routine.Room.WHOLE_HOME)

    def test_complete_route_records_history(self):
        self.client.force_login(self.user)
        routine = self._routine()

        response = self.client.post(
            reverse("household:complete_routine", args=[routine.pk]),
            {"scheduled_for": "2026-09-19"},
        )

        self.assertRedirects(response, reverse("household:routines"))
        self.assertTrue(
            RoutineEvent.objects.filter(
                routine=routine,
                outcome=RoutineEvent.Outcome.COMPLETED,
            ).exists()
        )

    def test_stale_double_submit_does_not_complete_next_occurrence(self):
        self.client.force_login(self.user)
        routine = self._routine()
        url = reverse("household:complete_routine", args=[routine.pk])
        payload = {"scheduled_for": "2026-09-19"}

        self.client.post(url, payload)
        second = self.client.post(url, payload)

        self.assertRedirects(second, reverse("household:routines"))
        self.assertEqual(RoutineEvent.objects.filter(routine=routine).count(), 1)

    def test_cross_user_action_returns_404(self):
        self.client.force_login(self.user)
        routine = self._routine(user=self.other_user)

        response = self.client.post(
            reverse("household:complete_routine", args=[routine.pk]),
            {"scheduled_for": "2026-09-19"},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(RoutineEvent.objects.filter(routine=routine).exists())

    def test_postpone_records_history_and_effective_date(self):
        self.client.force_login(self.user)
        routine = self._routine()

        response = self.client.post(
            reverse("household:postpone_routine", args=[routine.pk]),
            {
                "scheduled_for": "2026-09-19",
                "expected_effective_due_on": "2026-09-19",
                "postponed_to": "2026-09-21",
            },
        )

        self.assertRedirects(response, reverse("household:routines"))
        routine.refresh_from_db()
        self.assertEqual(routine.postponed_until, date(2026, 9, 21))
        self.assertTrue(
            RoutineEvent.objects.filter(
                routine=routine,
                outcome=RoutineEvent.Outcome.POSTPONED,
            ).exists()
        )

    def test_routine_mutations_are_post_only(self):
        self.client.force_login(self.user)
        routine = self._routine()

        for route in (
            "complete_routine",
            "skip_routine",
            "postpone_routine",
            "archive_routine",
        ):
            response = self.client.get(reverse(f"household:{route}", args=[routine.pk]))
            self.assertEqual(response.status_code, 405)

    def test_csrf_protects_completion(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        routine = self._routine()

        response = client.post(
            reverse("household:complete_routine", args=[routine.pk]),
            {"scheduled_for": "2026-09-19"},
        )

        self.assertEqual(response.status_code, 403)

    def test_edit_and_archive_are_owner_scoped(self):
        self.client.force_login(self.user)
        routine = self._routine(user=self.other_user)

        self.assertEqual(
            self.client.get(reverse("household:edit_routine", args=[routine.pk])).status_code,
            404,
        )
        self.assertEqual(
            self.client.post(reverse("household:archive_routine", args=[routine.pk])).status_code,
            404,
        )
