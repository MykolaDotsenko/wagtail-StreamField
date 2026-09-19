from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from household.models import ShoppingItem
from household.services import add_shopping_item


class ShoppingViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="shopping-user",
            password="safe-test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other-user",
            password="safe-test-password",
        )

    def test_shopping_requires_authentication(self):
        response = self.client.get(reverse("household:shopping"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_shopping_page_renders_quick_add_after_login(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("household:shopping"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "What do you need?")
        self.assertContains(response, 'id="shopping-name"')
        self.assertContains(response, "Quantity and category")

    def test_name_only_post_creates_categorized_item(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("household:shopping"),
            {"name": "Milk"},
        )

        self.assertRedirects(response, reverse("household:shopping"))
        item = ShoppingItem.objects.get(user=self.user)
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.category, ShoppingItem.Category.DAIRY)

    def test_duplicate_post_updates_quantity_instead_of_creating_duplicate(self):
        self.client.force_login(self.user)
        add_shopping_item(user=self.user, name="Milk")

        self.client.post(
            reverse("household:shopping"),
            {"name": " milk ", "quantity": 2},
        )

        self.assertEqual(ShoppingItem.objects.filter(user=self.user).count(), 1)
        self.assertEqual(ShoppingItem.objects.get(user=self.user).quantity, 3)

    def test_invalid_form_preserves_page_and_does_not_create_item(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("household:shopping"),
            {"name": "   ", "quantity": 1},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter an item to add.")
        self.assertFalse(ShoppingItem.objects.filter(user=self.user).exists())

    def test_toggle_is_post_only(self):
        self.client.force_login(self.user)
        item = add_shopping_item(user=self.user, name="Bread").item

        response = self.client.get(
            reverse("household:toggle_item", args=[item.pk]),
        )

        self.assertEqual(response.status_code, 405)

    def test_user_cannot_toggle_another_users_item(self):
        self.client.force_login(self.user)
        item = add_shopping_item(user=self.other_user, name="Bread").item

        response = self.client.post(
            reverse("household:toggle_item", args=[item.pk]),
        )

        self.assertEqual(response.status_code, 404)
        item.refresh_from_db()
        self.assertEqual(item.status, ShoppingItem.Status.OPEN)

    def test_delete_is_soft_and_redirect_exposes_owner_scoped_undo(self):
        self.client.force_login(self.user)
        item = add_shopping_item(user=self.user, name="Eggs").item

        response = self.client.post(
            reverse("household:delete_item", args=[item.pk]),
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn(f"undo={item.pk}", response.url)

        item.refresh_from_db()
        self.assertIsNotNone(item.deleted_at)

        undo_page = self.client.get(response.url)
        self.assertContains(undo_page, "Eggs removed")
        self.assertContains(
            undo_page,
            reverse("household:restore_item", args=[item.pk]),
        )

    def test_undo_query_cannot_expose_another_users_deleted_item(self):
        self.client.force_login(self.user)
        item = add_shopping_item(user=self.other_user, name="Private item").item
        item.deleted_at = item.updated_at
        item.save(
            update_fields=[
                "deleted_at",
                "name",
                "normalized_name",
                "updated_at",
            ]
        )

        response = self.client.get(
            f"{reverse('household:shopping')}?undo={item.pk}",
        )

        self.assertNotContains(response, "Private item removed")

    def test_shopping_mode_hides_quick_add_and_completed_section(self):
        self.client.force_login(self.user)
        completed = add_shopping_item(user=self.user, name="Milk").item
        self.client.post(
            reverse("household:toggle_item", args=[completed.pk]),
        )
        add_shopping_item(user=self.user, name="Bread")

        response = self.client.get(
            f"{reverse('household:shopping')}?mode=shop",
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "What do you need?")
        self.assertNotContains(response, 'id="completed-title"')
        self.assertContains(response, "Bread")
        self.assertContains(response, "Exit shopping mode")

    def test_csrf_protects_toggle_mutation(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        item = add_shopping_item(user=self.user, name="Bread").item

        response = client.post(
            reverse("household:toggle_item", args=[item.pk]),
        )

        self.assertEqual(response.status_code, 403)
