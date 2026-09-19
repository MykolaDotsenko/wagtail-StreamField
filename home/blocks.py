from wagtail import blocks
from wagtail.images.blocks import ImageBlock


class FeatureBlock(blocks.StructBlock):
    icon = blocks.ChoiceBlock(
        choices=[
            ("meal", "Meal planning"),
            ("shop", "Shopping"),
            ("pantry", "Pantry"),
            ("clean", "Cleaning"),
            ("guide", "Guides"),
        ],
        default="meal",
    )
    title = blocks.CharBlock(max_length=80)
    text = blocks.TextBlock(max_length=220)
    link_label = blocks.CharBlock(required=False, max_length=40)
    link_url = blocks.CharBlock(required=False, max_length=200)

    class Meta:
        icon = "pick"
        label = "Feature card"


class HeroBlock(blocks.StructBlock):
    eyebrow = blocks.CharBlock(
        required=False,
        max_length=60,
        default="A calmer home, one small plan at a time",
    )
    title = blocks.CharBlock(max_length=120)
    text = blocks.TextBlock(max_length=320)
    primary_label = blocks.CharBlock(max_length=40, default="Open my planner")
    primary_url = blocks.CharBlock(max_length=200, default="/planner/")
    secondary_label = blocks.CharBlock(
        required=False, max_length=40, default="Explore recipes"
    )
    secondary_url = blocks.CharBlock(required=False, max_length=200, default="/recipes/")
    image = ImageBlock(required=False)

    class Meta:
        icon = "home"
        label = "Hero"
        template = "home/blocks/hero.html"


class FeatureGridBlock(blocks.StructBlock):
    eyebrow = blocks.CharBlock(
        required=False, max_length=60, default="Everything in one place"
    )
    title = blocks.CharBlock(max_length=100)
    intro = blocks.TextBlock(required=False, max_length=260)
    items = blocks.ListBlock(FeatureBlock(), min_num=2, max_num=6)

    class Meta:
        icon = "grip"
        label = "Feature grid"
        template = "home/blocks/feature_grid.html"


class SplitFeatureBlock(blocks.StructBlock):
    eyebrow = blocks.CharBlock(required=False, max_length=60)
    title = blocks.CharBlock(max_length=100)
    text = blocks.RichTextBlock(features=["bold", "italic", "link", "ol", "ul"])
    image = ImageBlock(required=False)
    link_label = blocks.CharBlock(required=False, max_length=40)
    link_url = blocks.CharBlock(required=False, max_length=200)
    image_on_left = blocks.BooleanBlock(required=False, default=False)

    class Meta:
        icon = "image"
        label = "Split feature"
        template = "home/blocks/split_feature.html"


class MetricBlock(blocks.StructBlock):
    value = blocks.CharBlock(max_length=20)
    label = blocks.CharBlock(max_length=80)

    class Meta:
        label = "Metric"


class MetricsBlock(blocks.StructBlock):
    items = blocks.ListBlock(MetricBlock(), min_num=2, max_num=4)

    class Meta:
        icon = "site"
        label = "Metrics"
        template = "home/blocks/metrics.html"


class CtaBlock(blocks.StructBlock):
    eyebrow = blocks.CharBlock(required=False, max_length=60)
    title = blocks.CharBlock(max_length=100)
    text = blocks.TextBlock(max_length=260)
    label = blocks.CharBlock(max_length=40, default="Start planning")
    url = blocks.CharBlock(max_length=200, default="/planner/")

    class Meta:
        icon = "plus"
        label = "Call to action"
        template = "home/blocks/cta.html"


class HomeStreamBlock(blocks.StreamBlock):
    hero = HeroBlock(group="Landing")
    feature_grid = FeatureGridBlock(group="Landing")
    split_feature = SplitFeatureBlock(group="Storytelling")
    metrics = MetricsBlock(group="Evidence")
    cta = CtaBlock(group="Landing")

    class Meta:
        block_counts = {"hero": {"max_num": 1}}
