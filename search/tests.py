from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse


class SearchViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("bootstrap_demo", verbosity=0)

    def test_search_query_renders_results_page(self):
        response = self.client.get(reverse("search"), {"query": "fridge"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Search DomoNest")

    def test_search_without_query_renders_empty_prompt(self):
        response = self.client.get(reverse("search"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "What would make home easier today?")

    def test_invalid_page_number_falls_back_to_first_page(self):
        response = self.client.get(
            reverse("search"),
            {"query": "home", "page": "not-a-number"},
        )
        self.assertEqual(response.status_code, 200)

    def test_out_of_range_page_uses_last_page(self):
        response = self.client.get(
            reverse("search"),
            {"query": "home", "page": 999},
        )
        self.assertEqual(response.status_code, 200)
