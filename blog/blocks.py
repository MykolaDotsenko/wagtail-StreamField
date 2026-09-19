from wagtail import blocks
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageBlock, ImageChooserBlock


class ChecklistItemBlock(blocks.StructBlock):
    text = blocks.CharBlock(max_length=160)
    note = blocks.CharBlock(required=False, max_length=160)


class ChecklistBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=100)
    intro = blocks.CharBlock(required=False, max_length=220)
    items = blocks.ListBlock(ChecklistItemBlock(), min_num=1, max_num=12)

    class Meta:
        icon = "list-ul"
        label = "Checklist"
        template = "blog/streamfield/blocks/checklist_block.html"


class TipBlock(blocks.StructBlock):
    eyebrow = blocks.CharBlock(
        required=False, max_length=60, default="DomoNest tip"
    )
    title = blocks.CharBlock(max_length=100)
    text = blocks.TextBlock(max_length=320)
    tone = blocks.ChoiceBlock(
        choices=[
            ("sage", "Calm sage"),
            ("peach", "Warm peach"),
            ("sky", "Fresh sky"),
        ],
        default="sage",
    )

    class Meta:
        icon = "help"
        label = "Practical tip"
        template = "blog/streamfield/blocks/tip_block.html"


class StepsBlock(blocks.StructBlock):
    title = blocks.CharBlock(
        required=False, max_length=100, default="Do this next"
    )
    items = blocks.ListBlock(blocks.CharBlock(max_length=220), min_num=2, max_num=10)

    class Meta:
        icon = "list-ol"
        label = "Steps"
        template = "blog/streamfield/blocks/steps_block.html"


class GuideBodyBlock(blocks.StreamBlock):
    heading = blocks.CharBlock(
        form_classname="title",
        template="blog/streamfield/blocks/heading_block.html",
    )
    paragraph = blocks.RichTextBlock(
        features=["h3", "h4", "bold", "italic", "link", "ol", "ul"]
    )
    image = ImageChooserBlock(template="blog/streamfield/blocks/image_block.html")
    accessible_image = ImageBlock()
    quote = blocks.BlockQuoteBlock()
    embed = EmbedBlock()
    checklist = ChecklistBlock()
    tip = TipBlock()
    steps = StepsBlock()


class IngredientBlock(blocks.StructBlock):
    amount = blocks.CharBlock(required=False, max_length=40)
    name = blocks.CharBlock(max_length=100)
    note = blocks.CharBlock(required=False, max_length=100)

    class Meta:
        icon = "plus"
        label_format = "{amount} {name}"


class RecipeIngredientsBlock(blocks.StreamBlock):
    ingredient = IngredientBlock()

    class Meta:
        min_num = 1


class RecipeStepBlock(blocks.StructBlock):
    title = blocks.CharBlock(required=False, max_length=80)
    instruction = blocks.TextBlock(max_length=420)

    class Meta:
        icon = "list-ol"
        label_format = "{title}"


class RecipeStepsBlock(blocks.StreamBlock):
    step = RecipeStepBlock()

    class Meta:
        min_num = 1


class RecipeBodyBlock(blocks.StreamBlock):
    paragraph = blocks.RichTextBlock(
        features=["h3", "h4", "bold", "italic", "link", "ol", "ul"]
    )
    image = ImageBlock()
    tip = TipBlock()
    quote = blocks.BlockQuoteBlock()
