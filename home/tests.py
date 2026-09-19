from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from blog.models import BlogPage, RecipePage

from .models import HomePage


class HomePageSchemaTests(SimpleTestCase):
    def test_modern_streamfield_contains_expected_product_blocks(self):
        field = HomePage._meta.get_field("content")
        self.assertEqual(
            set(field.stream_block.child_blocks),
            {"hero", "feature_grid", "split_feature", "metrics", "cta"},
        )


class DomoNestDemoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("bootstrap_demo", verbosity=0)

    def test_bootstrap_is_idempotent(self):
        call_command("bootstrap_demo", verbosity=0)

        self.assertEqual(RecipePage.objects.filter(slug="roasted-tomato-pasta").count(), 1)
        self.assertEqual(BlogPage.objects.filter(slug="fridge-reset").count(), 1)

    def test_public_product_surfaces_render(self):
        for path, expected in [
            ("/", "DomoNest"),
            ("/guides/", "Home guides"),
            ("/recipes/", "Recipes"),
        ]:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, expected)
