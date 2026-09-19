from django.core.exceptions import ValidationError
from wagtail import blocks
from wagtail.images.blocks import ImageBlock


RICH_TEXT_FEATURES = ["bold", "italic", "link", "ul", "ol"]


class TipBlock(blocks.StructBlock):
    title = blocks.CharBlock(
        required=False,
        max_length=80,
        help_text="Optional short label. Leave blank to use “Tip”.",
    )
    body = blocks.RichTextBlock(
        features=RICH_TEXT_FEATURES,
        help_text="Keep the advice concise and directly useful.",
    )

    class Meta:
        label = "Practical tip"
        icon = "help"
        group = "Guidance"
        template = "content/blocks/tip.html"
        description = "Helpful context or a practical shortcut."
        preview_value = {
            "title": "Practical tip",
            "body": "<p>Store similar items together so they are easier to notice and use.</p>",
        }


class WarningBlock(blocks.StructBlock):
    title = blocks.CharBlock(
        required=False,
        max_length=80,
        help_text="Optional short label. Leave blank to use “Take care”.",
    )
    body = blocks.RichTextBlock(
        features=RICH_TEXT_FEATURES,
        help_text="Use warnings only for information that genuinely deserves extra attention.",
    )

    class Meta:
        label = "Important note"
        icon = "warning"
        group = "Guidance"
        template = "content/blocks/warning.html"
        description = "A restrained warning or important safety/context note."
        preview_value = {
            "title": "Take care",
            "body": "<p>Check the product label before combining household cleaning products.</p>",
        }


class ChecklistBlock(blocks.StructBlock):
    title = blocks.CharBlock(
        required=False,
        max_length=100,
        help_text="Optional heading for the checklist.",
    )
    items = blocks.ListBlock(
        blocks.CharBlock(
            max_length=180,
            label="Checklist item",
        ),
        min_num=1,
        label="Items",
    )

    class Meta:
        label = "Checklist"
        icon = "list-ul"
        group = "Actionable content"
        template = "content/blocks/checklist.html"
        description = "A scannable set of things to check or prepare."
        preview_value = {
            "title": "Before you start",
            "items": ["Open a window", "Gather supplies", "Clear the surface"],
        }


class StepsBlock(blocks.StructBlock):
    title = blocks.CharBlock(
        required=False,
        max_length=100,
        help_text="Optional heading. Use the page structure rather than numbering the title.",
    )
    steps = blocks.ListBlock(
        blocks.TextBlock(
            max_length=320,
            label="Step",
        ),
        min_num=1,
        label="Steps",
    )

    class Meta:
        label = "Step-by-step"
        icon = "list-ol"
        group = "Actionable content"
        template = "content/blocks/steps.html"
        description = "An ordered procedure where sequence matters."
        preview_value = {
            "title": "How to do it",
            "steps": ["Prepare the area.", "Do the task.", "Put everything back."],
        }


class ActionBlock(blocks.StructBlock):
    heading = blocks.CharBlock(
        max_length=100,
        help_text="Describe the useful next action, not a marketing slogan.",
    )
    text = blocks.TextBlock(
        required=False,
        max_length=220,
        help_text="Optional context explaining what happens next.",
    )
    label = blocks.CharBlock(
        max_length=60,
        help_text="Short action label, for example “Open Pantry”.",
    )
    page = blocks.PageChooserBlock(
        required=False,
        help_text="Choose an internal destination, or provide an external URL below.",
    )
    url = blocks.URLBlock(
        required=False,
        help_text="External destination. Leave blank when an internal page is selected.",
    )

    def clean(self, value):
        result = super().clean(value)
        if self.is_deferred_validation:
            return result

        has_page = bool(result["page"])
        has_url = bool(result["url"])
        if has_page == has_url:
            raise blocks.StructBlockValidationError(
                non_block_errors=[
                    ValidationError("Choose exactly one destination: an internal page or an external URL.")
                ]
            )
        return result

    class Meta:
        label = "Next action"
        icon = "link"
        group = "Actionable content"
        template = "content/blocks/action.html"
        description = "A single useful next step connected to the guide."
        preview_value = {
            "heading": "Make this actionable",
            "text": "Connect the guide to a useful next step.",
            "label": "Continue",
            "url": "https://example.com/",
        }


class GuideBodyBlock(blocks.StreamBlock):
    heading = blocks.CharBlock(
        form_classname="full title",
        label="Section heading",
        icon="title",
        group="Core content",
        description="A clear section heading that structures the guide.",
        template="blog/streamfield/blocks/heading_block.html",
    )
    paragraph = blocks.RichTextBlock(
        features=["h3", "bold", "italic", "link", "ul", "ol"],
        label="Text",
        icon="pilcrow",
        group="Core content",
        description="Body text with deliberately limited formatting.",
    )
    image = blocks.ImageChooserBlock(
        label="Legacy image",
        icon="image",
        group="Legacy",
        description="Kept for existing content. Prefer Accessible image for new guides.",
        template="blog/streamfield/blocks/image_block.html",
    )
    quote = blocks.BlockQuoteBlock(
        label="Quote",
        icon="openquote",
        group="Core content",
        description="A short quotation. Do not use for decorative pull quotes.",
    )
    embed = blocks.EmbedBlock(
        label="Media embed",
        icon="media",
        group="Media",
        description="Embedded media from a supported provider.",
    )
    illustration = ImageBlock(
        label="Accessible image",
        icon="image",
        group="Media",
        description="Image with context-specific alt text or an explicit decorative choice.",
    )
    tip = TipBlock()
    warning = WarningBlock()
    checklist = ChecklistBlock()
    steps = StepsBlock()
    action = ActionBlock()

    class Meta:
        label = "Guide content"
