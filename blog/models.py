from django import forms
from django.db import models
from django.db.models import Q
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from .blocks import (
    GuideBodyBlock,
    RecipeBodyBlock,
    RecipeIngredientsBlock,
    RecipeStepsBlock,
)


@register_snippet
class HouseholdTopic(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=8, default="✨")
    description = models.CharField(max_length=180, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class BlogIndexPage(Page):
    intro = RichTextField(blank=True)
    max_count_per_parent = 1
    subpage_types = ["blog.BlogPage"]

    content_panels = Page.content_panels + [FieldPanel("intro")]

    def get_context(self, request):
        context = super().get_context(request)
        guides = (
            BlogPage.objects.live()
            .child_of(self)
            .select_related("topic")
            .order_by("-date")
        )
        topic = request.GET.get("topic", "").strip()
        query = request.GET.get("q", "").strip()
        if topic:
            guides = guides.filter(topic__slug=topic)
        if query:
            guides = guides.filter(
                Q(title__icontains=query) | Q(intro__icontains=query)
            )
        context.update(
            {
                "blogpages": guides,
                "topics": HouseholdTopic.objects.all(),
                "active_topic": topic,
                "query": query,
            }
        )
        return context


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "BlogPage", related_name="tagged_items", on_delete=models.CASCADE
    )


class BlogPage(Page):
    date = models.DateField("Published date")
    intro = models.CharField(max_length=250)
    authors = ParentalManyToManyField("blog.Author", blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    topic = models.ForeignKey(
        "blog.HouseholdTopic",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="guides",
    )
    featured = models.BooleanField(default=False)
    reading_minutes = models.PositiveSmallIntegerField(default=5)
    body = StreamField(GuideBodyBlock(), blank=True, use_json_field=True)

    parent_page_types = ["blog.BlogIndexPage"]
    subpage_types = []

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
        index.FilterField("featured"),
        index.RelatedFields("topic", [index.SearchField("name")]),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("date"),
                FieldPanel("authors", widget=forms.CheckboxSelectMultiple),
                FieldPanel("tags"),
                FieldPanel("topic"),
                FieldPanel("reading_minutes"),
                FieldPanel("featured"),
            ],
            heading="Guide information",
        ),
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

    def main_image(self):
        gallery_item = self.gallery_images.first()
        return gallery_item.image if gallery_item else None


class BlogPageGalleryImage(Orderable):
    page = ParentalKey(
        BlogPage, on_delete=models.CASCADE, related_name="gallery_images"
    )
    image = models.ForeignKey(
        "wagtailimages.Image", on_delete=models.CASCADE, related_name="+"
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [FieldPanel("image"), FieldPanel("caption")]


@register_snippet
class Author(models.Model):
    name = models.CharField(max_length=255)
    author_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    panels = [FieldPanel("name"), FieldPanel("author_image")]

    class Meta:
        verbose_name_plural = "Authors"

    def __str__(self):
        return self.name


class BlogTagIndexPage(Page):
    def get_context(self, request):
        tag = request.GET.get("tag")
        context = super().get_context(request)
        context["blogpages"] = (
            BlogPage.objects.live().filter(tags__name=tag)
            if tag
            else BlogPage.objects.none()
        )
        return context


class RecipeIndexPage(Page):
    intro = RichTextField(blank=True)
    max_count_per_parent = 1
    subpage_types = ["blog.RecipePage"]

    content_panels = Page.content_panels + [FieldPanel("intro")]

    def get_context(self, request):
        context = super().get_context(request)
        recipes = (
            RecipePage.objects.live()
            .child_of(self)
            .select_related("hero_image")
            .order_by("-featured", "title")
        )
        query = request.GET.get("q", "").strip()
        meal_type = request.GET.get("meal_type", "").strip()
        if query:
            recipes = recipes.filter(
                Q(title__icontains=query) | Q(summary__icontains=query)
            )
        if meal_type:
            recipes = recipes.filter(meal_type=meal_type)
        context.update(
            {
                "recipes": recipes,
                "query": query,
                "active_meal_type": meal_type,
                "meal_types": RecipePage.MealType.choices,
            }
        )
        return context


class RecipePage(Page):
    class Difficulty(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        WEEKEND = "weekend", "Weekend project"

    class MealType(models.TextChoices):
        BREAKFAST = "breakfast", "Breakfast"
        LUNCH = "lunch", "Lunch"
        DINNER = "dinner", "Dinner"
        SNACK = "snack", "Snack"
        BAKING = "baking", "Baking"

    summary = models.CharField(max_length=260)
    hero_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    prep_minutes = models.PositiveSmallIntegerField(default=10)
    cook_minutes = models.PositiveSmallIntegerField(default=20)
    servings = models.PositiveSmallIntegerField(default=4)
    difficulty = models.CharField(
        max_length=20, choices=Difficulty.choices, default=Difficulty.EASY
    )
    meal_type = models.CharField(
        max_length=20, choices=MealType.choices, default=MealType.DINNER
    )
    featured = models.BooleanField(default=False)
    ingredients = StreamField(
        RecipeIngredientsBlock(), blank=True, use_json_field=True
    )
    steps = StreamField(RecipeStepsBlock(), blank=True, use_json_field=True)
    body = StreamField(RecipeBodyBlock(), blank=True, use_json_field=True)

    parent_page_types = ["blog.RecipeIndexPage"]
    subpage_types = []

    search_fields = Page.search_fields + [
        index.SearchField("summary"),
        index.SearchField("ingredients"),
        index.SearchField("body"),
        index.FilterField("meal_type"),
        index.FilterField("featured"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("summary"),
        FieldPanel("hero_image"),
        MultiFieldPanel(
            [
                FieldPanel("prep_minutes"),
                FieldPanel("cook_minutes"),
                FieldPanel("servings"),
                FieldPanel("difficulty"),
                FieldPanel("meal_type"),
                FieldPanel("featured"),
            ],
            heading="Recipe facts",
        ),
        FieldPanel("ingredients"),
        FieldPanel("steps"),
        FieldPanel("body"),
    ]

    @property
    def total_minutes(self):
        return self.prep_minutes + self.cook_minutes
