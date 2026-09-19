from django.test import SimpleTestCase

from .models import HomePage


class HomePageTests(SimpleTestCase):
    def test_modern_streamfield_contains_expected_product_blocks(self):
        field = HomePage._meta.get_field("content")
        self.assertEqual(
            set(field.stream_block.child_blocks),
            {"hero", "feature_grid", "split_feature", "metrics", "cta"},
        )
