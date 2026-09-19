from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from blog.models import BlogIndexPage, BlogPage
from home.models import HomePage
from household.models import MealPlanEntry, PantryItem, Routine, ShoppingItem
from recipes.models import Ingredient, RecipeIndexPage, RecipeIngredient, RecipePage


class Command(BaseCommand):
    help = "Create deterministic local demo content and a non-privileged demo household account."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo")
        parser.add_argument("--password", default="domonest-demo")
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Reset private household state for the selected demo user before seeding.",
        )

    def handle(self, *args, **options):
        username = options["username"].strip()
        password = options["password"]
        if not username:
            raise CommandError("Demo username cannot be empty.")
        if len(password) < 8:
            raise CommandError("Demo password must contain at least 8 characters.")

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(username=username)
        user.is_active = True
        user.is_staff = False
        user.is_superuser = False
        user.set_password(password)
        user.save(update_fields=["is_active", "is_staff", "is_superuser", "password"])

        if options["reset"]:
            MealPlanEntry.objects.filter(user=user).delete()
            Routine.objects.filter(user=user).delete()
            PantryItem.objects.filter(user=user).delete()
            ShoppingItem.objects.filter(user=user).delete()

        home = HomePage.objects.first()
        if home is None:
            raise CommandError("No HomePage exists. Apply project migrations before seeding.")

        recipe_index = RecipeIndexPage.objects.child_of(home).filter(slug="recipes").first()
        if recipe_index is None:
            recipe_index = RecipeIndexPage(
                title="Recipes",
                slug="recipes",
                intro="<p>Practical dinners that connect Pantry, Plan and Shopping.</p>",
            )
            home.add_child(instance=recipe_index)
            recipe_index.save_revision().publish()

        tomato = self._ingredient(
            "Tomato",
            Ingredient.Category.PRODUCE,
        )
        pasta = self._ingredient(
            "Pasta",
            Ingredient.Category.PANTRY,
        )

        recipe = RecipePage.objects.child_of(recipe_index).filter(slug="tomato-pasta").first()
        if recipe is None:
            recipe = RecipePage(
                title="Tomato pasta",
                slug="tomato-pasta",
                intro="A simple weeknight dinner that demonstrates structured recipe readiness.",
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
                                "Cook the pasta until just tender.",
                                "Warm the tomatoes and fold through the pasta.",
                            ],
                        },
                    ),
                    (
                        "tip",
                        {
                            "title": "Keep it calm",
                            "body": "<p>Reserve a little pasta water before draining.</p>",
                        },
                    ),
                ],
            )
            recipe_index.add_child(instance=recipe)
        else:
            recipe.title = "Tomato pasta"
            recipe.intro = (
                "A simple weeknight dinner that demonstrates structured recipe readiness."
            )
            recipe.prep_minutes = 10
            recipe.cook_minutes = 15
            recipe.servings = 2
            recipe.difficulty = RecipePage.Difficulty.EASY
            recipe.save()

        RecipeIngredient.objects.update_or_create(
            page=recipe,
            ingredient=tomato,
            defaults={
                "amount": Decimal("2"),
                "unit": RecipeIngredient.Unit.ITEM,
                "note": "roughly chopped",
                "optional": False,
                "sort_order": 0,
            },
        )
        RecipeIngredient.objects.update_or_create(
            page=recipe,
            ingredient=pasta,
            defaults={
                "amount": Decimal("200"),
                "unit": RecipeIngredient.Unit.GRAM,
                "note": "",
                "optional": False,
                "sort_order": 1,
            },
        )
        recipe.save_revision().publish()

        guide_index = BlogIndexPage.objects.child_of(home).filter(slug="guides").first()
        if guide_index is None:
            guide_index = BlogIndexPage(
                title="Home guides",
                slug="guides",
                intro="<p>Small practical systems for a calmer home.</p>",
            )
            home.add_child(instance=guide_index)
            guide_index.save_revision().publish()

        guide = BlogPage.objects.child_of(guide_index).filter(slug="fridge-reset").first()
        if guide is None:
            guide = BlogPage(
                title="A calm fridge reset",
                slug="fridge-reset",
                date=timezone.localdate(),
                guide_type=BlogPage.GuideType.ORGANIZATION,
                intro="A short weekly reset that keeps use-soon food visible.",
                body=[
                    (
                        "checklist",
                        {
                            "title": "Five-minute reset",
                            "items": [
                                "Check dates.",
                                "Move older food forward.",
                                "Wipe one shelf that needs it.",
                            ],
                        },
                    )
                ],
            )
            guide_index.add_child(instance=guide)
            guide.save_revision().publish()

        Routine.objects.get_or_create(
            user=user,
            title="Take out recycling",
            defaults={
                "room": Routine.Room.WHOLE_HOME,
                "frequency": Routine.Frequency.WEEKLY,
                "due_on": timezone.localdate(),
                "expected_duration_minutes": 5,
            },
        )

        state = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo {state}: username={username!r}; recipe={recipe.url}; "
                f"guide={guide.url}. Password was set from --password."
            )
        )

    @staticmethod
    def _ingredient(name, category):
        normalized_name = Ingredient.normalize_identity(name)
        ingredient = Ingredient.objects.filter(normalized_name=normalized_name).first()
        if ingredient is None:
            return Ingredient.objects.create(name=name, category=category)

        changed = False
        if ingredient.name != name:
            ingredient.name = name
            changed = True
        if ingredient.category != category:
            ingredient.category = category
            changed = True
        if changed:
            ingredient.save()
        return ingredient
