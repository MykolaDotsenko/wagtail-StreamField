from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from blog.models import BlogIndexPage, BlogPage
from home.models import HomePage
from household.models import MealPlanEntry, PantryItem, Routine, ShoppingItem
from recipes.models import RecipeIndexPage, RecipePage


class DiscoverTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="discover-user",
            password="safe-test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="discover-other",
            password="safe-test-password",
        )
        self.today = timezone.localdate()
        home = HomePage.objects.first()

        recipe_index = RecipeIndexPage(
            title="Discover recipes",
            slug="discover-recipes",
            intro="",
        )
        home.add_child(instance=recipe_index)
        self.recipe = RecipePage(
            title="Tomato pasta",
            slug="discover-tomato-pasta",
            intro="Fast tomato dinner.",
            prep_minutes=10,
            cook_minutes=15,
            servings=2,
            instructions=[],
        )
        recipe_index.add_child(instance=self.recipe)

        guide_index = BlogIndexPage(
            title="Discover guides",
            slug="discover-guides",
            intro="",
        )
        home.add_child(instance=guide_index)
        self.guide = BlogPage(
            title="Fridge reset",
            slug="discover-fridge-reset",
            date=self.today,
            guide_type=BlogPage.GuideType.ORGANIZATION,
            intro="A calm fridge organization guide.",
            body=[],
        )
        guide_index.add_child(instance=self.guide)

    def test_discover_landing_surfaces_latest_public_content(self):
        response = self.client.get(reverse("search"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Latest recipes")
        self.assertContains(response, "Tomato pasta")
        self.assertContains(response, "Latest guides")
        self.assertContains(response, "Fridge reset")

    def test_anonymous_search_finds_public_content(self):
        recipe_response = self.client.get(
            reverse("search"),
            {"query": "tomato"},
        )
        guide_response = self.client.get(
            reverse("search"),
            {"query": "fridge"},
        )

        self.assertContains(recipe_response, "Tomato pasta")
        self.assertContains(guide_response, "Fridge reset")
        self.assertNotContains(recipe_response, "Your home")
        self.assertNotContains(guide_response, "Your home")

    def test_private_results_are_owner_scoped(self):
        ShoppingItem.objects.create(user=self.user, name="Private milk")
        ShoppingItem.objects.create(user=self.other_user, name="Private secret milk")
        PantryItem.objects.create(user=self.user, name="Private rice")
        PantryItem.objects.create(user=self.other_user, name="Private secret rice")
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("search"),
            {"query": "Private", "kind": "home"},
        )

        self.assertContains(response, "Your home")
        self.assertContains(response, "Private milk")
        self.assertContains(response, "Private rice")
        self.assertNotContains(response, "Private secret milk")
        self.assertNotContains(response, "Private secret rice")

    def test_anonymous_home_filter_never_queries_private_state_into_response(self):
        ShoppingItem.objects.create(user=self.user, name="Secret detergent")

        response = self.client.get(
            reverse("search"),
            {"query": "Secret", "kind": "home"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Secret detergent")
        self.assertContains(response, "Sign in before searching private household state")
        self.assertNotContains(response, ">Your home</a>")

    def test_search_filters_public_groups(self):
        self.client.force_login(self.user)

        recipes = self.client.get(
            reverse("search"),
            {"query": "tomato", "kind": "recipes"},
        )
        guides = self.client.get(
            reverse("search"),
            {"query": "fridge", "kind": "guides"},
        )

        self.assertContains(recipes, "Tomato pasta")
        self.assertNotContains(recipes, "Home guides")
        self.assertContains(guides, "Fridge reset")

    def test_private_search_ignores_completed_deleted_and_inactive_state(self):
        completed = ShoppingItem.objects.create(user=self.user, name="Archived milk")
        completed.complete()
        completed.save()
        deleted = ShoppingItem.objects.create(user=self.user, name="Archived bread")
        deleted.deleted_at = timezone.now()
        deleted.save()
        Routine.objects.create(
            user=self.user,
            title="Archived kitchen reset",
            due_on=self.today,
            active=False,
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("search"),
            {"query": "Archived", "kind": "home"},
        )

        self.assertNotContains(response, "Archived milk")
        self.assertNotContains(response, "Archived bread")
        self.assertNotContains(response, "Archived kitchen reset")

    def test_private_search_includes_active_home_domains(self):
        ShoppingItem.objects.create(user=self.user, name="Findable milk")
        PantryItem.objects.create(user=self.user, name="Findable flour")
        Routine.objects.create(
            user=self.user,
            title="Findable kitchen reset",
            due_on=self.today + timedelta(days=1),
        )
        MealPlanEntry.objects.create(
            user=self.user,
            date=self.today + timedelta(days=2),
            name="Findable pasta",
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("search"),
            {"query": "Findable", "kind": "home"},
        )

        self.assertContains(response, "Findable milk")
        self.assertContains(response, "Findable flour")
        self.assertContains(response, "Findable kitchen reset")
        self.assertContains(response, "Findable pasta")

    def test_past_meal_plan_does_not_pollute_private_search(self):
        MealPlanEntry.objects.create(
            user=self.user,
            date=self.today - timedelta(days=1),
            name="Old dinner",
        )
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("search"),
            {"query": "Old", "kind": "home"},
        )

        self.assertNotContains(response, "Old dinner")

    def test_query_is_normalized_and_bounded(self):
        response = self.client.get(
            reverse("search"),
            {"query": "   tomato     pasta   "},
        )

        self.assertContains(response, "Tomato pasta")
        self.assertEqual(response.context["search_query"], "tomato pasta")

    def test_invalid_kind_falls_back_to_all(self):
        response = self.client.get(
            reverse("search"),
            {"query": "tomato", "kind": "not-real"},
        )

        self.assertEqual(response.context["search_kind"], "all")
        self.assertContains(response, "Tomato pasta")
