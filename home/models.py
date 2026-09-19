from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.search import index

from .blocks import HomeStreamBlock


class HomePage(Page):
    body = RichTextField(
        blank=True, help_text="Legacy content kept for backwards compatibility."
    )
    content = StreamField(HomeStreamBlock(), blank=True, use_json_field=True)

    max_count = 1
    subpage_types = [
        "blog.BlogIndexPage",
        "blog.RecipeIndexPage",
        "blog.BlogTagIndexPage",
    ]

    search_fields = Page.search_fields + [index.SearchField("content")]

    content_panels = Page.content_panels + [FieldPanel("content")]

    def get_context(self, request):
        context = super().get_context(request)
        from blog.models import BlogPage, RecipePage

        context["featured_recipes"] = (
            RecipePage.objects.live().filter(featured=True).select_related("hero_image")[:3]
        )
        context["featured_guides"] = (
            BlogPage.objects.live().filter(featured=True).select_related("topic")[:3]
        )
        return context
