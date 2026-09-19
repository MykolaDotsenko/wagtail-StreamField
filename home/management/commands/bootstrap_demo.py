import datetime

from django.core.management.base import BaseCommand
from wagtail.models import Page, Site

from blog.models import (
    BlogIndexPage,
    BlogPage,
    BlogTagIndexPage,
    HouseholdTopic,
    RecipeIndexPage,
    RecipePage,
)
from home.models import HomePage


class Command(BaseCommand):
    help = "Create or refresh a small, editorially useful DomoNest demo content tree."

    def handle(self, *args, **options):
        root = Page.get_first_root_node()
        home = HomePage.objects.child_of(root).first()
        if home is None:
            home = HomePage(title="DomoNest", slug="home")
            root.add_child(instance=home)

        home.title = "DomoNest"
        home.seo_title = "DomoNest — calm household planning"
        home.search_description = (
            "Plan meals, shopping, pantry stock and simple home routines in one calm place."
        )
        if not home.content:
            home.content = [
                (
                    "hero",
                    {
                        "eyebrow": "A calmer home, one small plan at a time",
                        "title": "Keep meals, shopping and home routines in one gentle rhythm.",
                        "text": (
                            "DomoNest combines a practical household planner with trustworthy, "
                            "editor-curated recipes and home guides."
                        ),
                        "primary_label": "Open my planner",
                        "primary_url": "/planner/",
                        "secondary_label": "Explore recipes",
                        "secondary_url": "/recipes/",
                    },
                ),
                (
                    "feature_grid",
                    {
                        "eyebrow": "Everything in one place",
                        "title": "Useful enough to open every day.",
                        "intro": (
                            "Each module solves one household job with the fewest possible steps."
                        ),
                        "items": [
                            {
                                "icon": "meal",
                                "title": "Meal planning",
                                "text": (
                                    "Give the week a simple food rhythm without over-planning."
                                ),
                            },
                            {
                                "icon": "shop",
                                "title": "Smart shopping",
                                "text": (
                                    "Keep quantities, categories and checked items in one tactile list."
                                ),
                            },
                            {
                                "icon": "pantry",
                                "title": "Pantry signals",
                                "text": (
                                    "Spot low stock and food that deserves to be used soon."
                                ),
                            },
                            {
                                "icon": "clean",
                                "title": "Home routines",
                                "text": (
                                    "Small recurring chores, organised by room and due date."
                                ),
                            },
                        ],
                    },
                ),
                (
                    "cta",
                    {
                        "eyebrow": "Start small",
                        "title": "One clear household view beats five forgotten notes.",
                        "text": (
                            "Create a private space and plan only what helps this week."
                        ),
                        "label": "Create my space",
                        "url": "/accounts/signup/",
                    },
                ),
            ]
        home.save_revision().publish()

        site = Site.objects.filter(is_default_site=True).first()
        if site:
            site.root_page = home
            site.site_name = "DomoNest"
            site.save(update_fields=["root_page", "site_name"])

        guides = BlogIndexPage.objects.child_of(home).first()
        if guides is None:
            guides = BlogIndexPage(
                title="Home guides",
                slug="guides",
                intro=(
                    "Practical, calm guidance for cleaning, organising, food care "
                    "and everyday home systems."
                ),
            )
            home.add_child(instance=guides)
            guides.save_revision().publish()

        recipes = RecipeIndexPage.objects.child_of(home).first()
        if recipes is None:
            recipes = RecipeIndexPage(
                title="Recipes",
                slug="recipes",
                intro=(
                    "Straightforward recipes chosen for real weekdays, small kitchens "
                    "and repeatability."
                ),
            )
            home.add_child(instance=recipes)
            recipes.save_revision().publish()

        if not BlogTagIndexPage.objects.child_of(home).filter(slug="tags").exists():
            tag_index = BlogTagIndexPage(title="Guide tags", slug="tags")
            home.add_child(instance=tag_index)
            tag_index.save_revision().publish()

        topic, _ = HouseholdTopic.objects.get_or_create(
            slug="kitchen",
            defaults={
                "name": "Kitchen",
                "icon": "🍋",
                "description": "Food care, prep and kitchen routines.",
            },
        )

        if not BlogPage.objects.child_of(guides).filter(slug="fridge-reset").exists():
            guide = BlogPage(
                title="The 15-minute fridge reset",
                slug="fridge-reset",
                date=datetime.date.today(),
                intro=(
                    "A small weekly reset that keeps food visible, reduces waste "
                    "and makes shopping easier."
                ),
                topic=topic,
                featured=True,
                reading_minutes=4,
                body=[
                    (
                        "paragraph",
                        (
                            "<p>Do not deep-clean the whole fridge. The useful goal is "
                            "to make the next few meals obvious and remove anything that "
                            "can no longer be used.</p>"
                        ),
                    ),
                    (
                        "checklist",
                        {
                            "title": "Your quick reset",
                            "intro": "Stop when these five things are done.",
                            "items": [
                                {
                                    "text": (
                                        "Move open and soon-to-expire food to one visible shelf."
                                    )
                                },
                                {"text": "Discard anything unsafe or clearly past use."},
                                {
                                    "text": (
                                        "Wipe one sticky shelf or drawer — not the entire fridge."
                                    )
                                },
                                {
                                    "text": (
                                        "Add low-stock staples to your DomoNest shopping list."
                                    )
                                },
                                {
                                    "text": (
                                        "Choose one meal that uses the food that needs attention first."
                                    )
                                },
                            ],
                        },
                    ),
                    (
                        "tip",
                        {
                            "eyebrow": "Reduce friction",
                            "title": "Make the “use first” shelf permanent.",
                            "text": (
                                "A fixed place for open yoghurt, herbs, leftovers and soft "
                                "vegetables removes a surprising amount of meal-planning guesswork."
                            ),
                            "tone": "sage",
                        },
                    ),
                ],
            )
            guides.add_child(instance=guide)
            guide.save_revision().publish()

        if not RecipePage.objects.child_of(recipes).filter(
            slug="roasted-tomato-pasta"
        ).exists():
            recipe = RecipePage(
                title="Roasted tomato pantry pasta",
                slug="roasted-tomato-pasta",
                summary=(
                    "A forgiving weeknight pasta built around tomatoes, garlic "
                    "and whatever greens need using."
                ),
                prep_minutes=10,
                cook_minutes=25,
                servings=4,
                difficulty=RecipePage.Difficulty.EASY,
                meal_type=RecipePage.MealType.DINNER,
                featured=True,
                ingredients=[
                    ("ingredient", {"amount": "350 g", "name": "pasta"}),
                    ("ingredient", {"amount": "500 g", "name": "cherry tomatoes"}),
                    ("ingredient", {"amount": "3 cloves", "name": "garlic"}),
                    ("ingredient", {"amount": "2 tbsp", "name": "olive oil"}),
                    (
                        "ingredient",
                        {
                            "amount": "2 handfuls",
                            "name": "spinach or other greens",
                            "note": "great for using food soon",
                        },
                    ),
                ],
                steps=[
                    (
                        "step",
                        {
                            "title": "Roast",
                            "instruction": (
                                "Roast tomatoes and garlic with olive oil at 220°C until "
                                "collapsed and lightly caramelised."
                            ),
                        },
                    ),
                    (
                        "step",
                        {
                            "title": "Cook",
                            "instruction": (
                                "Boil the pasta until just tender. Reserve a mug of pasta "
                                "water before draining."
                            ),
                        },
                    ),
                    (
                        "step",
                        {
                            "title": "Finish",
                            "instruction": (
                                "Crush the roasted tomatoes, toss with pasta and enough "
                                "pasta water to make a glossy sauce. Fold in greens at the end."
                            ),
                        },
                    ),
                ],
                body=[
                    (
                        "tip",
                        {
                            "eyebrow": "Pantry logic",
                            "title": "Treat the recipe as a pattern.",
                            "text": (
                                "Use the vegetables that need attention first. The structure "
                                "matters more than matching every ingredient exactly."
                            ),
                            "tone": "peach",
                        },
                    )
                ],
            )
            recipes.add_child(instance=recipe)
            recipe.save_revision().publish()

        self.stdout.write(self.style.SUCCESS("DomoNest demo content is ready."))
