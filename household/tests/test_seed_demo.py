from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from blog.models import BlogPage
from household.models import Routine, ShoppingItem
from recipes.models import RecipePage


class SeedDemoCommandTests(TestCase):
    def test_seed_is_repeatable_without_duplicate_editorial_content(self):
        output = StringIO()

        call_command(
            "seed_demo",
            reset=True,
            username="demo-test",
            password="demo-password",
            stdout=output,
        )
        call_command(
            "seed_demo",
            reset=True,
            username="demo-test",
            password="demo-password",
            stdout=output,
        )

        user = get_user_model().objects.get(username="demo-test")
        self.assertTrue(user.check_password("demo-password"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.is_active)
        self.assertEqual(RecipePage.objects.filter(slug="tomato-pasta").count(), 1)
        self.assertEqual(BlogPage.objects.filter(slug="fridge-reset").count(), 1)
        self.assertEqual(
            Routine.objects.filter(user=user, title="Take out recycling").count(),
            1,
        )

    def test_seed_demotes_an_existing_privileged_demo_account(self):
        user_model = get_user_model()
        demo = user_model.objects.create_superuser(
            username="demo-privileged",
            password="temporary-admin-password",
        )

        call_command(
            "seed_demo",
            reset=True,
            username=demo.username,
            password="demo-password",
            stdout=StringIO(),
        )

        demo.refresh_from_db()
        self.assertTrue(demo.is_active)
        self.assertFalse(demo.is_staff)
        self.assertFalse(demo.is_superuser)
        self.assertTrue(demo.check_password("demo-password"))

    def test_reset_is_scoped_to_selected_demo_user(self):
        user_model = get_user_model()
        demo = user_model.objects.create_user(
            username="demo-reset",
            password="safe-test-password",
        )
        other = user_model.objects.create_user(
            username="untouched-user",
            password="safe-test-password",
        )
        ShoppingItem.objects.create(user=demo, name="Remove me")
        ShoppingItem.objects.create(user=other, name="Keep me")

        call_command(
            "seed_demo",
            reset=True,
            username="demo-reset",
            password="demo-password",
            stdout=StringIO(),
        )

        self.assertFalse(ShoppingItem.objects.filter(user=demo, name="Remove me").exists())
        self.assertTrue(ShoppingItem.objects.filter(user=other, name="Keep me").exists())
