from django.test import TestCase
from wagtail import blocks
from wagtail.images.blocks import ImageBlock, ImageChooserBlock

from content.blocks import ActionBlock, GuideBodyBlock, TipBlock


class GuideBlockTests(TestCase):
    def test_action_requires_exactly_one_destination(self):
        block = ActionBlock()
        value = block.to_python(
            {
                "heading": "Do the next thing",
                "text": "",
                "label": "Continue",
                "page": None,
                "url": "",
            }
        )

        with self.assertRaises(blocks.StructBlockValidationError):
            block.clean(value)

    def test_action_accepts_one_external_destination(self):
        block = ActionBlock()
        value = block.to_python(
            {
                "heading": "Read more",
                "text": "Useful next context.",
                "label": "Open resource",
                "page": None,
                "url": "https://example.com/",
            }
        )

        cleaned = block.clean(value)

        self.assertEqual(cleaned["url"], "https://example.com/")
        self.assertIsNone(cleaned["page"])

    def test_guide_body_keeps_legacy_image_but_prefers_accessible_image(self):
        body = GuideBodyBlock()

        self.assertIsInstance(body.child_blocks["image"], ImageChooserBlock)
        self.assertIsInstance(body.child_blocks["illustration"], ImageBlock)
        self.assertEqual(body.child_blocks["image"].meta.group, "Legacy")
        self.assertEqual(body.child_blocks["illustration"].meta.group, "Media")

    def test_guide_body_exposes_product_oriented_action_blocks(self):
        body = GuideBodyBlock()

        self.assertIn("tip", body.child_blocks)
        self.assertIn("warning", body.child_blocks)
        self.assertIn("checklist", body.child_blocks)
        self.assertIn("steps", body.child_blocks)
        self.assertIn("action", body.child_blocks)

    def test_tip_has_editor_preview_and_description(self):
        block = TipBlock()

        self.assertTrue(block.is_previewable)
        self.assertTrue(block.get_description())
