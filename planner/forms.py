from django import forms

from blog.models import RecipePage

from .models import Chore, MealPlanEntry, PantryItem, ShoppingItem


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")


class ShoppingItemForm(StyledModelForm):
    class Meta:
        model = ShoppingItem
        fields = ["name", "quantity", "category"]
        widgets = {
            "name": forms.TextInput(
                attrs={"placeholder": "Milk, apples, dishwasher tablets…"}
            )
        }


class PantryItemForm(StyledModelForm):
    class Meta:
        model = PantryItem
        fields = ["name", "quantity", "category", "expires_on", "low_stock"]
        widgets = {"expires_on": forms.DateInput(attrs={"type": "date"})}


class ChoreForm(StyledModelForm):
    class Meta:
        model = Chore
        fields = ["title", "room", "frequency", "due_on"]
        widgets = {
            "due_on": forms.DateInput(attrs={"type": "date"}),
            "title": forms.TextInput(attrs={"placeholder": "Clean fridge shelves"}),
        }


class MealPlanEntryForm(StyledModelForm):
    class Meta:
        model = MealPlanEntry
        fields = ["date", "meal_type", "recipe", "custom_meal"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "custom_meal": forms.TextInput(attrs={"placeholder": "Or type a simple meal"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["recipe"].queryset = RecipePage.objects.live().order_by("title")
        self.fields["recipe"].required = False
        self.fields["custom_meal"].required = False

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("recipe") and not cleaned.get("custom_meal", "").strip():
            raise forms.ValidationError("Choose a recipe or enter a custom meal.")
        return cleaned
