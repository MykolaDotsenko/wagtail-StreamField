from django.contrib.auth import get_user_model
from django.test import TestCase

from household.forms import PantryItemForm
from household.models import PantryItem


class PantryItemFormTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="pantry-form-user",
            password="safe-test-password",
        )

    def test_name_only_submission_gets_low_maintenance_defaults(self):
        form = PantryItemForm(
            {"name": "Rice"},
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["quantity_mode"],
            PantryItem.QuantityMode.APPROXIMATE,
        )
        self.assertEqual(
            form.cleaned_data["approximate_level"],
            PantryItem.ApproximateLevel.FULL,
        )
        self.assertIsNone(form.cleaned_data["amount"])
        self.assertEqual(form.cleaned_data["unit"], "")

    def test_precise_mode_requires_amount_and_unit(self):
        form = PantryItemForm(
            {
                "name": "Flour",
                "quantity_mode": PantryItem.QuantityMode.PRECISE,
            },
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)
        self.assertIn("unit", form.errors)

    def test_precise_mode_clears_approximate_state(self):
        form = PantryItemForm(
            {
                "name": "Flour",
                "quantity_mode": PantryItem.QuantityMode.PRECISE,
                "approximate_level": PantryItem.ApproximateLevel.LOW,
                "amount": "1.5",
                "unit": PantryItem.Unit.KILOGRAM,
                "low_stock_threshold": "0.25",
            },
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["approximate_level"], "")

    def test_approximate_mode_discards_irrelevant_precise_values(self):
        form = PantryItemForm(
            {
                "name": "Flour",
                "quantity_mode": PantryItem.QuantityMode.APPROXIMATE,
                "approximate_level": PantryItem.ApproximateLevel.HALF,
                "amount": "1.5",
                "unit": PantryItem.Unit.KILOGRAM,
                "low_stock_threshold": "0.25",
            },
            user=self.user,
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertIsNone(form.cleaned_data["amount"])
        self.assertEqual(form.cleaned_data["unit"], "")
        self.assertIsNone(form.cleaned_data["low_stock_threshold"])

    def test_duplicate_identity_is_rejected_for_same_user(self):
        PantryItem.objects.create(user=self.user, name="Milk")

        form = PantryItemForm(
            {"name": " milk "},
            user=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("already in your pantry", form.errors["name"][0])

    def test_edit_can_keep_its_existing_identity(self):
        item = PantryItem.objects.create(user=self.user, name="Milk")

        form = PantryItemForm(
            {"name": "Milk"},
            user=self.user,
            instance=item,
        )

        self.assertTrue(form.is_valid(), form.errors)
