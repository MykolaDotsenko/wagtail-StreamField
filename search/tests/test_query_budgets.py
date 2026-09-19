from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from household.models import MealPlanEntry, PantryItem, Routine, ShoppingItem
from search.selectors import discover_snapshot


class DiscoverQueryBudgetTests(TestCase):
    def test_private_home_search_uses_one_bounded_query_per_domain(self):
        user = get_user_model().objects.create_user(
            username="discover-query-user",
            password="safe-test-password",
        )
        today = timezone.localdate()

        for number in range(5):
            ShoppingItem.objects.create(user=user, name=f"Find item {number}")
            PantryItem.objects.create(user=user, name=f"Find pantry {number}")
            Routine.objects.create(
                user=user,
                title=f"Find routine {number}",
                due_on=today,
            )
            MealPlanEntry.objects.create(
                user=user,
                date=today + timedelta(days=number),
                name=f"Find dinner {number}",
            )

        with CaptureQueriesContext(connection) as queries:
            snapshot = discover_snapshot(
                query="Find",
                kind="home",
                user=user,
                today=today,
            )
            self.assertEqual(len(snapshot.home_results), 8)

        self.assertLessEqual(
            len(queries),
            4,
            f"Private Discover exceeded query budget: {len(queries)} queries",
        )
