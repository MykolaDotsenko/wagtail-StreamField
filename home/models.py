from django.db import models
from wagtail import blocks
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page


class FeatureBlock(blocks.StructBlock):
    icon = blocks.CharBlock(max_length=4, help_text="Emoji or short symbol")
    title = blocks.CharBlock(max_length=80)
    text = blocks.TextBlock(max_length=220)

    class Meta:
        icon = "placeholder"
        label = "Feature"


class HomePage(Page):
    body = RichTextField(blank=True, help_text="Legacy content; used only when no sections are configured.")
    eyebrow = models.CharField(max_length=80, blank=True, default="A calmer way to run your home")
    sections = StreamField(
        [
            ("hero", blocks.StructBlock([
                ("title", blocks.CharBlock(max_length=120)),
                ("text", blocks.TextBlock(max_length=320)),
                ("primary_label", blocks.CharBlock(max_length=40, default="Open dashboard")),
                ("primary_url", blocks.CharBlock(max_length=160, default="/app/")),
                ("secondary_label", blocks.CharBlock(max_length=40, default="Explore features")),
                ("secondary_url", blocks.CharBlock(max_length=160, default="#features")),
            ], icon="home", label="Hero")),
            ("features", blocks.StructBlock([
                ("heading", blocks.CharBlock(max_length=100)),
                ("intro", blocks.TextBlock(max_length=260, required=False)),
                ("items", blocks.ListBlock(FeatureBlock(), min_num=2, max_num=6)),
            ], icon="list-ul", label="Feature grid")),
            ("callout", blocks.StructBlock([
                ("kicker", blocks.CharBlock(max_length=60, required=False)),
                ("heading", blocks.CharBlock(max_length=100)),
                ("text", blocks.TextBlock(max_length=260)),
                ("button_label", blocks.CharBlock(max_length=40, required=False)),
                ("button_url", blocks.CharBlock(max_length=160, required=False)),
            ], icon="pick", label="Callout")),
            ("rich_text", blocks.RichTextBlock(features=["h2", "h3", "bold", "italic", "ol", "ul", "link"])),
        ],
        blank=True,
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("eyebrow"),
        FieldPanel("sections"),
        FieldPanel("body"),
    ]
