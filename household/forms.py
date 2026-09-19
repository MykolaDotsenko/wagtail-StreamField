from django import forms

from .models import Chore, PantryItem, ShoppingItem


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "field-control")


class ShoppingItemForm(StyledModelForm):
    class Meta:
        model = ShoppingItem
        fields = ["name", "quantity", "category"]
        widgets = {"name": forms.TextInput(attrs={"placeholder": "Milk, tomatoes, detergent…"})}


class PantryItemForm(StyledModelForm):
    class Meta:
        model = PantryItem
        fields = ["name", "quantity", "unit", "low_stock_threshold", "expires_on"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Rice, oats, olive oil…"}),
            "expires_on": forms.DateInput(attrs={"type": "date"}),
        }


class ChoreForm(StyledModelForm):
    class Meta:
        model = Chore
        fields = ["title", "room", "frequency", "due_on"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Reset kitchen surfaces"}),
            "due_on": forms.DateInput(attrs={"type": "date"}),
        }
