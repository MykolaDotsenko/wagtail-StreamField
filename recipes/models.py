import unicodedata

from django.core.exceptions import ValidationError
from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from .blocks import RecipeBodyBlock


@register_snippet
class Ingredient(index.Indexed, models.Model):
    class Category(models.TextChoices):
        PRODUCE = "produce", "Fruit & vegetables"
        DAIRY = "dairy", "Dairy & eggs"
        BAKERY = "bakery", "Bakery"
        MEAT_FISH = "meat_fish", "Meat & fish"
        PANTRY = "pantry", "Pantry"
        FROZEN = "frozen", "Frozen"
        OTHER = "other", "Other"

    name = models.CharField(max_length=120)
    normalized_name = models.CharField(max_length=255, unique=True, editable=False)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("category"),
    ]

    search_fields = [
        index.SearchField("name"),
        index.FilterField("category"),
    ]

    class Meta:
        ordering = ["name", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(normalized_name=""),
                name="ingredient_name_not_empty",
            )
        ]

    @staticmethod
    def normalize_display_name(value: str) -> str:
        normalized = unicodedata.normalize("NFKC", value)
        return " ".join(normalized.split())

    @classmethod
    def normalize_identity(cls, value: str) -> str:
        return cls.normalize_display_name(value).casefold()

    def save(self, *args, **kwargs):
        self.name = self.normalize_display_name(self.name)
        self.normalized_name = self.normalize_identity(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class RecipeIndexPage(Page):
    intro = RichTextField(
        blank=True,
        features=["bold", "italic", "link"],
        help_text="A short introduction to the recipe collection.",
    )

    parent_page_types = ["home.HomePage"]
    subpage_types = ["recipes.RecipePage"]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context["recipes"] = (
            RecipePage.objects.child_of(self)
            .live()
            .order_by("-first_published_at")
            .select_related("hero_image")
            .prefetch_related("ingredient_lines__ingredient")
        )
        return context

    class Meta:
        verbose_name = "Recipe library"


class RecipePageTag(TaggedItemBase):
    content_object = ParentalKey(
        "RecipePage",
        related_name="tagged_items",
        on_delete=models.CASCADE,
    )


class RecipePage(Page):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        ADVANCED = "advanced", "Advanced"

    intro = models.CharField(
        max_length=280,
        help_text="One concise promise: what should the cook expect from this recipe?",
    )
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    hero_alt_text = models.CharField(
        max_length=180,
        blank=True,
        help_text="Context-specific alt text. Leave blank only when the image is decorative.",
    )
    prep_minutes = models.PositiveSmallIntegerField(
        help_text="Active preparation time in minutes.",
    )
    cook_minutes = models.PositiveSmallIntegerField(
        default=0,
        help_text="Cooking/baking time in minutes. Use 0 for no-cook recipes.",
    )
    servings = models.PositiveSmallIntegerField(default=2)
    difficulty = models.CharField(
        max_length=12,
        choices=Difficulty.choices,
        default=Difficulty.EASY,
    )
    tags = ClusterTaggableManager(through=RecipePageTag, blank=True)
    instructions = StreamField(
        RecipeBodyBlock(),
        use_json_field=True,
        blank=True,
        help_text="Keep ingredient quantities in the structured ingredient rows below.",
    )

    parent_page_types = ["recipes.RecipeIndexPage"]
    subpage_types = []

    search_fields = Page.search_fields + [
        index.SearchField("intro", boost=1.5),
        index.SearchField("instructions"),
        index.SearchField("get_ingredient_names"),
        index.FilterField("difficulty"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        MultiFieldPanel(
            [
                FieldPanel("hero_image"),
                FieldPanel("hero_alt_text"),
            ],
            heading="Hero image",
        ),
        MultiFieldPanel(
            [
                FieldPanel("prep_minutes"),
                FieldPanel("cook_minutes"),
                FieldPanel("servings"),
                FieldPanel("difficulty"),
                FieldPanel("tags"),
            ],
            heading="Recipe facts",
        ),
        InlinePanel(
            "ingredient_lines",
            label="Ingredient",
            heading="Ingredients",
            help_text="Use one canonical ingredient per recipe; use the note field for “divided” or preparation detail.",
            min_num=1,
        ),
        FieldPanel("instructions"),
    ]

    @property
    def total_minutes(self) -> int:
        return self.prep_minutes + self.cook_minutes

    def get_ingredient_names(self) -> str:
        return "\n".join(
            self.ingredient_lines.order_by("sort_order", "pk").values_list(
                "ingredient__name",
                flat=True,
            )
        )

    def get_context(self, request):
        context = super().get_context(request)
        if request.user.is_authenticated:
            from household.recipe_reconciliation import recipe_readiness

            context["readiness"] = recipe_readiness(recipe=self, user=request.user)
        else:
            context["readiness"] = None
        return context

    def clean(self):
        super().clean()
        if self.hero_image_id and not self.hero_alt_text.strip():
            raise ValidationError(
                {
                    "hero_alt_text": (
                        "Describe the meaningful hero image. Remove the image if it is purely decorative."
                    )
                }
            )

    class Meta:
        verbose_name = "Recipe"
        verbose_name_plural = "Recipes"


class RecipeIngredient(Orderable):
    class Unit(models.TextChoices):
        ITEM = "item", "item"
        GRAM = "g", "g"
        KILOGRAM = "kg", "kg"
        MILLILITRE = "ml", "ml"
        LITRE = "l", "l"
        TEASPOON = "tsp", "tsp"
        TABLESPOON = "tbsp", "tbsp"
        CUP = "cup", "cup"

    page = ParentalKey(
        RecipePage,
        on_delete=models.CASCADE,
        related_name="ingredient_lines",
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.PROTECT,
        related_name="recipe_lines",
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=True,
        null=True,
    )
    unit = models.CharField(
        max_length=8,
        choices=Unit.choices,
        blank=True,
        default="",
    )
    note = models.CharField(
        max_length=120,
        blank=True,
        help_text="Optional preparation detail, for example “finely chopped” or “divided”.",
    )
    optional = models.BooleanField(default=False)

    panels = [
        FieldPanel("ingredient"),
        FieldPanel("amount"),
        FieldPanel("unit"),
        FieldPanel("note"),
        FieldPanel("optional"),
    ]

    class Meta:
        ordering = ["sort_order", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(amount__isnull=True, unit="")
                    | (models.Q(amount__isnull=False, amount__gt=0) & ~models.Q(unit=""))
                ),
                name="recipe_ingredient_quantity_consistent",
            ),
            models.UniqueConstraint(
                fields=["page", "ingredient"],
                name="unique_ingredient_per_recipe",
            ),
        ]

    @property
    def amount_label(self) -> str:
        if self.amount is None:
            return ""
        amount = f"{self.amount.normalize():f}"
        return f"{amount} {self.get_unit_display()}"

    def __str__(self):
        return f"{self.page}: {self.ingredient}"
