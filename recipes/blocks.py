from wagtail import blocks
from wagtail.images.blocks import ImageBlock

from content.blocks import RICH_TEXT_FEATURES, StepsBlock, TipBlock, WarningBlock


class RecipeBodyBlock(blocks.StreamBlock):
    heading = blocks.CharBlock(
        max_length=100,
        label="Section heading",
        icon="title",
        group="Cooking",
        description="Use a short heading only when the recipe needs multiple instruction sections.",
    )
    paragraph = blocks.RichTextBlock(
        features=RICH_TEXT_FEATURES,
        label="Cooking note",
        icon="pilcrow",
        group="Cooking",
        description="Short supporting text that is not an ingredient or numbered cooking step.",
    )
    steps = StepsBlock(
        label="Cooking steps",
        group="Cooking",
        description="Ordered cooking instructions where sequence matters.",
    )
    tip = TipBlock()
    warning = WarningBlock()
    illustration = ImageBlock(
        required=False,
        label="Instruction image",
        icon="image",
        group="Media",
        description="Optional contextual image with editor-controlled alt/decorative semantics.",
    )
    substitutions = blocks.RichTextBlock(
        required=False,
        features=RICH_TEXT_FEATURES,
        label="Substitutions",
        icon="repeat",
        group="Useful extras",
        description="Practical ingredient substitutions. Keep claims concrete and tested.",
    )
    storage = blocks.RichTextBlock(
        required=False,
        features=RICH_TEXT_FEATURES,
        label="Storage advice",
        icon="date",
        group="Useful extras",
        description="How to store leftovers or prepared food safely and usefully.",
    )

    class Meta:
        label = "Recipe instructions"
