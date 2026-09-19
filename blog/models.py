from django import forms
from django.db import models
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Orderable, Page
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from content.blocks import GuideBodyBlock


class BlogIndexPage(Page):
    intro = RichTextField(
        blank=True,
        features=["bold", "italic", "link", "ul", "ol"],
        help_text="Briefly explain what readers can learn from this guide library.",
    )

    parent_page_types = ["home.HomePage"]
    subpage_types = ["blog.BlogPage", "blog.BlogTagIndexPage"]

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context["blogpages"] = (
            BlogPage.objects.child_of(self)
            .live()
            .order_by("-first_published_at")
            .prefetch_related("authors", "gallery_images")
        )
        return context

    class Meta:
        verbose_name = "Guide library"


class BlogPageTag(TaggedItemBase):
    content_object = ParentalKey(
        "BlogPage",
        related_name="tagged_items",
        on_delete=models.CASCADE,
    )


class BlogPage(Page):
    class GuideType(models.TextChoices):
        GENERAL = "general", "General"
        CLEANING = "cleaning", "Cleaning"
        FOOD_STORAGE = "food_storage", "Food storage"
        ORGANIZATION = "organization", "Organization"
        MAINTENANCE = "maintenance", "Home maintenance"
        SEASONAL = "seasonal", "Seasonal"

    date = models.DateField(
        "Published date",
        help_text="Use the editorial date readers should associate with this guide.",
    )
    guide_type = models.CharField(
        max_length=20,
        choices=GuideType.choices,
        default=GuideType.GENERAL,
        help_text="Used for editorial context and Discover filtering.",
    )
    intro = models.CharField(
        max_length=250,
        help_text="One concise promise: what useful outcome will the reader get?",
    )
    authors = ParentalManyToManyField("blog.Author", blank=True)
    tags = ClusterTaggableManager(through=BlogPageTag, blank=True)
    body = StreamField(
        GuideBodyBlock(),
        use_json_field=True,
        help_text="Build the guide from structured blocks. Prefer actionable blocks over free-form layout.",
    )

    parent_page_types = ["blog.BlogIndexPage"]
    subpage_types = []

    search_fields = Page.search_fields + [
        index.SearchField("intro", boost=1.5),
        index.SearchField("body"),
        index.FilterField("guide_type"),
    ]

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [
                FieldPanel("date"),
                FieldPanel("guide_type"),
                FieldPanel("authors", widget=forms.CheckboxSelectMultiple),
                FieldPanel("tags"),
            ],
            heading="Guide information",
        ),
        FieldPanel("intro"),
        FieldPanel("body"),
        InlinePanel("gallery_images", label="Legacy gallery images"),
    ]

    def main_image(self):
        gallery_item = self.gallery_images.first()
        return gallery_item.image if gallery_item else None

    class Meta:
        verbose_name = "Home guide"
        verbose_name_plural = "Home guides"


class BlogPageGalleryImage(Orderable):
    page = ParentalKey(
        BlogPage,
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.CASCADE,
        related_name="+",
    )
    caption = models.CharField(blank=True, max_length=250)

    panels = [
        FieldPanel("image"),
        FieldPanel("caption"),
    ]


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

    panels = [
        FieldPanel("name"),
        FieldPanel("author_image"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Authors"


class BlogTagIndexPage(Page):
    parent_page_types = ["blog.BlogIndexPage"]
    subpage_types = []

    def get_context(self, request):
        tag = request.GET.get("tag")
        context = super().get_context(request)
        context["blogpages"] = (
            BlogPage.objects.live()
            .filter(tags__name=tag)
            .distinct()
            .order_by("-first_published_at")
        )
        return context

    class Meta:
        verbose_name = "Guide topic index"
