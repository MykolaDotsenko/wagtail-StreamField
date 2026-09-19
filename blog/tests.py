from django.core.management import call_command
from django.test import TestCase

from .models import Author, HouseholdTopic, RecipePage


class RecipePageTests(TestCase):
    def test_total_minutes_combines_prep_and_cook_time(self):
        page = RecipePage(
            title="Weeknight soup",
            prep_minutes=12,
            cook_minutes=28,
        )
        self.assertEqual(page.total_minutes, 40)

    def test_snippet_labels_are_readable(self):
        topic = HouseholdTopic(name="Kitchen", slug="kitchen")
        author = Author(name="DomoNest editor")
        self.assertEqual(str(topic), "Kitchen")
        self.assertEqual(str(author), "DomoNest editor")


class EditorialLibraryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("bootstrap_demo", verbosity=0)

    def test_guide_filters_apply_query_and_topic(self):
        response = self.client.get(
            "/guides/",
            {"q": "fridge", "topic": "kitchen"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The 15-minute fridge reset")

    def test_recipe_filters_apply_query_and_meal_type(self):
        response = self.client.get(
            "/recipes/",
            {"q": "tomato", "meal_type": "dinner"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Roasted tomato pantry pasta")

    def test_tag_page_handles_empty_tag_collection(self):
        response = self.client.get("/tags/", {"tag": "seasonal"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "#seasonal")
