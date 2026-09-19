from datetime import date

from django.test import TestCase
from wagtail.models import Page

from blog.models import BlogIndexPage, BlogPage
from home.models import HomePage


class GuidePageArchitectureTests(TestCase):
    def setUp(self):
        self.home = HomePage.objects.first()
        self.assertIsNotNone(self.home)

        self.index = BlogIndexPage(
            title="Home guides",
            slug="guides",
            intro="<p>Useful household knowledge.</p>",
        )
        self.home.add_child(instance=self.index)

    def test_page_tree_allows_guides_only_under_guide_library(self):
        self.assertTrue(BlogIndexPage.can_create_at(self.home))
        self.assertTrue(BlogPage.can_create_at(self.index))
        self.assertFalse(BlogPage.can_create_at(self.home))
        self.assertEqual(BlogPage.allowed_subpage_models(), [])

    def test_guide_renders_structured_actionable_content(self):
        guide = BlogPage(
            title="Keep the fridge calm",
            slug="keep-fridge-calm",
            date=date(2026, 9, 19),
            guide_type=BlogPage.GuideType.ORGANIZATION,
            intro="A short guide for a fridge that is easier to use.",
            body=[
                (
                    "tip",
                    {
                        "title": "Practical tip",
                        "body": "<p>Put use-soon food where you can see it.</p>",
                    },
                ),
                (
                    "checklist",
                    {
                        "title": "Weekly reset",
                        "items": ["Check dates", "Move older food forward"],
                    },
                ),
            ],
        )
        self.index.add_child(instance=guide)

        response = self.client.get(guide.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Organization")
        self.assertContains(response, "Practical tip")
        self.assertContains(response, "Put use-soon food where you can see it.")
        self.assertContains(response, "Weekly reset")
        self.assertContains(response, "Move older food forward")

    def test_guide_library_returns_only_its_live_child_guides(self):
        first = BlogPage(
            title="First guide",
            slug="first-guide",
            date=date(2026, 9, 19),
            intro="First",
            body=[],
        )
        self.index.add_child(instance=first)

        sibling_index = BlogIndexPage(
            title="Other guides",
            slug="other-guides",
            intro="",
        )
        self.home.add_child(instance=sibling_index)
        sibling = BlogPage(
            title="Private to other index",
            slug="other-guide",
            date=date(2026, 9, 19),
            intro="Other",
            body=[],
        )
        sibling_index.add_child(instance=sibling)

        response = self.client.get(self.index.url)

        self.assertContains(response, "First guide")
        self.assertNotContains(response, "Private to other index")

    def test_guide_type_is_filterable_search_metadata(self):
        filter_names = {
            field.field_name
            for field in BlogPage.search_fields
            if hasattr(field, "field_name")
        }

        self.assertIn("guide_type", filter_names)

    def test_generic_page_cannot_be_created_under_guide(self):
        guide = BlogPage(
            title="Leaf guide",
            slug="leaf-guide",
            date=date(2026, 9, 19),
            intro="Leaf",
            body=[],
        )
        self.index.add_child(instance=guide)

        self.assertFalse(Page.can_create_at(guide))
