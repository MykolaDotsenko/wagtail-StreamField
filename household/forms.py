from django import forms

from .models import PantryItem, ShoppingItem
from .services import AUTO_CATEGORY


class ShoppingItemCreateForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        strip=True,
        label="Item",
        error_messages={"required": "Enter an item to add."},
    )
    quantity = forms.IntegerField(
        min_value=1,
        max_value=99,
        initial=1,
        required=False,
        label="Quantity",
    )
    category = forms.ChoiceField(
        choices=[(AUTO_CATEGORY, "Choose automatically"), *ShoppingItem.Category.choices],
        initial=AUTO_CATEGORY,
        required=False,
        label="Category",
    )

    def clean_name(self):
        name = ShoppingItem.normalize_display_name(self.cleaned_data["name"])
        if not name:
            raise forms.ValidationError("Enter an item to add.")
        if len(name) > 120:
            raise forms.ValidationError("Keep the item name to 120 characters or fewer.")
        return name

    def clean_quantity(self):
        return self.cleaned_data.get("quantity") or 1

    def clean_category(self):
        return self.cleaned_data.get("category") or AUTO_CATEGORY


class PantryItemForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        strip=True,
        label="Item",
        error_messages={"required": "Enter a pantry item."},
    )
    category = forms.ChoiceField(
        choices=ShoppingItem.Category.choices,
        initial=ShoppingItem.Category.OTHER,
        required=False,
        label="Category",
    )
    quantity_mode = forms.ChoiceField(
        choices=PantryItem.QuantityMode.choices,
        initial=PantryItem.QuantityMode.APPROXIMATE,
        required=False,
        label="Tracking style",
    )
    approximate_level = forms.ChoiceField(
        choices=PantryItem.ApproximateLevel.choices,
        initial=PantryItem.ApproximateLevel.FULL,
        required=False,
        label="Approximate level",
    )
    amount = forms.DecimalField(
        min_value=0,
        max_digits=9,
        decimal_places=2,
        required=False,
        label="Amount",
    )
    unit = forms.ChoiceField(
        choices=[("", "Choose unit"), *PantryItem.Unit.choices],
        required=False,
        label="Unit",
    )
    low_stock_threshold = forms.DecimalField(
        min_value=0,
        max_digits=9,
        decimal_places=2,
        required=False,
        label="Low-stock threshold",
    )
    expires_on = forms.DateField(
        required=False,
        label="Best before / expiry",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, user, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.instance = instance

    def clean_name(self):
        name = ShoppingItem.normalize_display_name(self.cleaned_data["name"])
        normalized_name = ShoppingItem.normalize_identity(name)
        duplicates = PantryItem.objects.filter(
            user=self.user,
            normalized_name=normalized_name,
        )
        if self.instance is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("This item is already in your pantry.")
        return name

    def clean_category(self):
        return self.cleaned_data.get("category") or ShoppingItem.Category.OTHER

    def clean_quantity_mode(self):
        return self.cleaned_data.get("quantity_mode") or PantryItem.QuantityMode.APPROXIMATE

    def clean(self):
        cleaned = super().clean()
        mode = cleaned.get("quantity_mode") or PantryItem.QuantityMode.APPROXIMATE
        cleaned["quantity_mode"] = mode

        if mode == PantryItem.QuantityMode.APPROXIMATE:
            cleaned["approximate_level"] = (
                cleaned.get("approximate_level") or PantryItem.ApproximateLevel.FULL
            )
            cleaned["amount"] = None
            cleaned["unit"] = ""
            cleaned["low_stock_threshold"] = None
        elif mode == PantryItem.QuantityMode.PRECISE:
            if cleaned.get("amount") is None:
                self.add_error("amount", "Enter the current amount.")
            if not cleaned.get("unit"):
                self.add_error("unit", "Choose a unit for precise tracking.")
            cleaned["approximate_level"] = ""

        return cleaned
