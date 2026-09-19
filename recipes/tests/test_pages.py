from decimal import Decimal

from django.test import TestCase
from wagtail.models import Page

from home.models import HomePage
from recipes.models import Ingredient, RecipeIndexPage, RecipeIngredient, RecipePage


class RecipePageTests(TestCase):
    def setUp(self):
        self.home = HomePage.objects.first()
        self.assertIsNotNone(self.home)
        self.index = RecipeIndexPage(
            title="Recipes",
            slug="recipes",
            intro="<p>Weeknight recipes that reduce planning work.</p>",
        )
        self.home.add_child(instance=self.index)

    def test_page_tree_is_deliberately_constrained(self):
        self.assertTrue(RecipeIndexPage.can_create_at(self.home))
        self.assertTrue(RecipePage.can_create_at(self.index))
        self.assertFalse(RecipePage.can_create_at(self.home))
        self.assertEqual(RecipePage.allowed_subpage_models(), [])

    def test_recipe_detail_renders_structured_ingredients_and_method(self):
        recipe = RecipePage(
            title="Tomato pasta",
            slug="tomato-pasta",
            intro="Fast, calm and pantry friendly.",
            prep_minutes=10,
            cook_minutes=15,
            servings=2,
            difficulty=RecipePage.Difficulty.EASY,
            instructions=[
                (
                    "steps",
                    {
                        "title": "Cook",
                        "steps": [
                            "Boil the pasta.",
                            "Fold through the tomato sauce.",
                        ],
                    },
                ),
                (
                    "tip",
                    {
                        "title": "Practical tip",
                        "body": "<p>Reserve a little pasta water.</p>",
                    },
                ),
            ],
        )
        self.index.add_child(instance=recipe)

        tomato = Ingredient.objects.create(
            name="Tomato",
            category=Ingredient.Category.PRODUCE,
        )
        RecipeIngredient.objects.create(
            page=recipe,
            ingredient=tomato,
            amount=Decimal("2"),
            unit=RecipeIngredient.Unit.ITEM,
            note="roughly chopped",
        )

        response = self.client.get(recipe.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Tomato pasta")
        self.assertContains(response, "25 min")
        self.assertContains(response, "2 item")
        self.assertContains(response, "roughly chopped")
        self.assertContains(response, "Boil the pasta.")
        self.assertContains(response, "Reserve a little pasta water.")

    def test_recipe_library_renders_only_its_live_children(self):
        first = RecipePage(
            title="First recipe",
            slug="first-recipe",
            intro="First",
            prep_minutes=5,
            cook_minutes=0,
            servings=1,
            instructions=[],
        )
        self.index.add_child(instance=first)

        other_index = RecipeIndexPage(
            title="Other recipes",
            slug="other-recipes",
            intro="",
        )
        self.home.add_child(instance=other_index)
        other = RecipePage(
            title="Other recipe",
            slug="other-recipe",
            intro="Other",
            prep_minutes=5,
            cook_minutes=0,
            servings=1,
            instructions=[],
        )
        other_index.add_child(instance=other)

        response = self.client.get(self.index.url)

        self.assertContains(response, "First recipe")
        self.assertNotContains(response, "Other recipe")

    def test_generic_page_cannot_be_created_under_recipe(self):
        recipe = RecipePage(
            title="Leaf recipe",
            slug="leaf-recipe",
            intro="Leaf",
            prep_minutes=5,
            cook_minutes=0,
            servings=1,
            instructions=[],
        )
        self.index.add_child(instance=recipe)

        self.assertFalse(Page.can_create_at(recipe))
