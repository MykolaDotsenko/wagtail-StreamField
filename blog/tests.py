from django.test import TestCase

from .models import RecipePage


class RecipePageTests(TestCase):
    def test_total_minutes_combines_prep_and_cook_time(self):
        page = RecipePage(
            title="Weeknight soup",
            prep_minutes=12,
            cook_minutes=28,
        )
        self.assertEqual(page.total_minutes, 40)
