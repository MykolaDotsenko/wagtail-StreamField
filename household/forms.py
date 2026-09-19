from django import forms

from .models import ShoppingItem


AUTO_CATEGORY = "auto"


class ShoppingItemCreateForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        strip=True,
        label="Item",
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
        return name

    def clean_quantity(self):
        return self.cleaned_data.get("quantity") or 1

    def clean_category(self):
        return self.cleaned_data.get("category") or AUTO_CATEGORY
