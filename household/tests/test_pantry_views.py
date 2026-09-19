from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from household.models import PantryItem, ShoppingItem


class PantryViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="pantry-view-user",
            password="safe-test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="pantry-view-other",
            password="safe-test-password",
        )

    def test_pantry_requires_authentication(self):
        response = self.client.get(reverse("household:pantry"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_name_only_post_creates_approximate_full_item(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("household:pantry"),
            {"name": "Rice"},
        )

        self.assertRedirects(response, reverse("household:pantry"))
        item = PantryItem.objects.get(user=self.user)
        self.assertEqual(item.quantity_mode, PantryItem.QuantityMode.APPROXIMATE)
        self.assertEqual(item.approximate_level, PantryItem.ApproximateLevel.FULL)
        self.assertEqual(item.category, ShoppingItem.Category.OTHER)

    def test_invalid_precise_form_reveals_associated_errors(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("household:pantry"),
            {
                "name": "Flour",
                "quantity_mode": PantryItem.QuantityMode.PRECISE,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Enter the current amount.")
        self.assertContains(response, "Choose a unit for precise tracking.")
        self.assertContains(response, 'class="disclosure pantry-disclosure" open')

    def test_low_stock_item_can_be_added_to_shopping(self):
        self.client.force_login(self.user)
        item = PantryItem.objects.create(
            user=self.user,
            name="Milk",
            category=ShoppingItem.Category.DAIRY,
            approximate_level=PantryItem.ApproximateLevel.LOW,
        )

        response = self.client.post(
            reverse("household:pantry_to_shopping", args=[item.pk]),
        )

        self.assertRedirects(response, reverse("household:pantry"))
        shopping = ShoppingItem.objects.get(user=self.user)
        self.assertEqual(shopping.name, "Milk")
        self.assertEqual(shopping.quantity, 1)

    def test_repeated_add_to_shopping_does_not_inflate_quantity(self):
        self.client.force_login(self.user)
        item = PantryItem.objects.create(
            user=self.user,
            name="Milk",
            approximate_level=PantryItem.ApproximateLevel.LOW,
        )

        url = reverse("household:pantry_to_shopping", args=[item.pk])
        self.client.post(url)
        self.client.post(url)

        self.assertEqual(ShoppingItem.objects.get(user=self.user).quantity, 1)

    def test_user_cannot_edit_another_users_pantry_item(self):
        self.client.force_login(self.user)
        item = PantryItem.objects.create(user=self.other_user, name="Private")

        response = self.client.get(
            reverse("household:edit_pantry_item", args=[item.pk]),
        )

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_add_another_users_pantry_item_to_shopping(self):
        self.client.force_login(self.user)
        item = PantryItem.objects.create(user=self.other_user, name="Private")

        response = self.client.post(
            reverse("household:pantry_to_shopping", args=[item.pk]),
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(ShoppingItem.objects.filter(user=self.user).exists())

    def test_pantry_mutations_are_post_only(self):
        self.client.force_login(self.user)
        item = PantryItem.objects.create(user=self.user, name="Rice")

        self.assertEqual(
            self.client.get(
                reverse("household:remove_pantry_item", args=[item.pk])
            ).status_code,
            405,
        )
        self.assertEqual(
            self.client.get(
                reverse("household:pantry_to_shopping", args=[item.pk])
            ).status_code,
            405,
        )

    def test_csrf_protects_add_to_shopping(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        item = PantryItem.objects.create(user=self.user, name="Rice")

        response = client.post(
            reverse("household:pantry_to_shopping", args=[item.pk]),
        )

        self.assertEqual(response.status_code, 403)
