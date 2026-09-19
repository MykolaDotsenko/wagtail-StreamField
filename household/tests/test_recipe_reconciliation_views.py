from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from home.models import HomePage
from household.models import PantryItem, ShoppingItem
from recipes.models import Ingredient, RecipeIndexPage, RecipeIngredient, RecipePage


class RecipeShoppingViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="recipe-action-user",
            password="safe-test-password",
        )
        home = HomePage.objects.first()
        index = RecipeIndexPage(title="Recipes", slug="recipes-action", intro="")
        home.add_child(instance=index)
        self.recipe = RecipePage(
            title="Action dinner",
            slug="action-dinner",
            intro="A recipe for action testing.",
            prep_minutes=5,
            cook_minutes=10,
            servings=2,
            instructions=[],
        )
        index.add_child(instance=self.recipe)
        self.tomato = Ingredient.objects.create(
            name="Tomato",
            category=Ingredient.Category.PRODUCE,
        )
        RecipeIngredient.objects.create(
            page=self.recipe,
            ingredient=self.tomato,
            amount=Decimal("2"),
            unit=RecipeIngredient.Unit.ITEM,
        )
        self.url = reverse(
            "household:add_recipe_to_shopping",
            args=[self.recipe.pk],
        )

    def test_recipe_page_keeps_private_readiness_behind_authentication(self):
        anonymous = self.client.get(self.recipe.url)

        self.assertContains(anonymous, "Compare with Pantry")
        self.assertNotContains(anonymous, "Missing")

        self.client.force_login(self.user)
        authenticated = self.client.get(self.recipe.url)

        self.assertContains(authenticated, "Missing")
        self.assertContains(authenticated, "Add 1 needed item to Shopping")
        self.assertNotContains(authenticated, "Compare with Pantry")

    def test_action_requires_authentication(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)
        self.assertFalse(ShoppingItem.objects.exists())

    def test_action_is_post_only(self):
        self.client.force_login(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)

    def test_action_is_csrf_protected(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)

        response = client.post(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertFalse(ShoppingItem.objects.exists())

    def test_action_redirects_back_to_recipe_and_is_idempotent(self):
        self.client.force_login(self.user)

        first = self.client.post(self.url)
        second = self.client.post(self.url)

        self.assertRedirects(first, self.recipe.url)
        self.assertRedirects(second, self.recipe.url)
        item = ShoppingItem.objects.get(user=self.user)
        self.assertEqual(item.ingredient_id, self.tomato.pk)
        self.assertEqual(item.quantity, 1)

    def test_other_users_pantry_never_changes_current_users_readiness(self):
        other = get_user_model().objects.create_user(
            username="recipe-action-other",
            password="safe-test-password",
        )
        PantryItem.objects.create(
            user=other,
            ingredient=self.tomato,
            name="Tomato",
            approximate_level=PantryItem.ApproximateLevel.FULL,
        )
        self.client.force_login(self.user)

        response = self.client.get(self.recipe.url)

        self.assertContains(response, "Missing")

    def test_non_live_recipe_cannot_be_mutated_through_public_action(self):
        self.client.force_login(self.user)
        self.recipe.live = False
        self.recipe.save()

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 404)
        self.assertFalse(ShoppingItem.objects.exists())
