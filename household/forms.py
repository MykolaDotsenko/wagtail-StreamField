from django import forms
from django.utils import timezone

from recipes.models import RecipePage

from .models import PantryItem, Routine, ShoppingItem
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


class RoutineForm(forms.Form):
    title = forms.CharField(
        max_length=120,
        strip=True,
        label="Routine",
        error_messages={"required": "Enter a routine."},
    )
    room = forms.ChoiceField(
        choices=Routine.Room.choices,
        initial=Routine.Room.WHOLE_HOME,
        required=False,
        label="Area",
    )
    frequency = forms.ChoiceField(
        choices=Routine.Frequency.choices,
        initial=Routine.Frequency.WEEKLY,
        required=False,
        label="Repeat",
    )
    due_on = forms.DateField(
        label="Next due",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    expected_duration_minutes = forms.IntegerField(
        min_value=1,
        max_value=480,
        required=False,
        label="Expected minutes",
    )

    def clean_title(self):
        return ShoppingItem.normalize_display_name(self.cleaned_data["title"])

    def clean_room(self):
        return self.cleaned_data.get("room") or Routine.Room.WHOLE_HOME

    def clean_frequency(self):
        return self.cleaned_data.get("frequency") or Routine.Frequency.WEEKLY


class RoutineActionForm(forms.Form):
    scheduled_for = forms.DateField(widget=forms.HiddenInput)


class RoutinePostponeForm(RoutineActionForm):
    expected_effective_due_on = forms.DateField(widget=forms.HiddenInput)
    postponed_to = forms.DateField(
        label="Postpone to",
        widget=forms.DateInput(attrs={"type": "date"}),
    )

    def __init__(self, *args, routine, **kwargs):
        super().__init__(*args, **kwargs)
        self.routine = routine

    def clean_postponed_to(self):
        postponed_to = self.cleaned_data["postponed_to"]
        if postponed_to <= self.routine.effective_due_on:
            raise forms.ValidationError("Choose a date after the current due date.")
        return postponed_to


class MealPlanForm(forms.Form):
    date = forms.DateField(
        label="Dinner date",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    recipe = forms.ChoiceField(
        required=False,
        label="Recipe",
    )
    custom_name = forms.CharField(
        max_length=160,
        required=False,
        strip=True,
        label="Or custom dinner",
        help_text="Use this when dinner is not a DomoNest recipe.",
    )

    def __init__(self, *args, recipe_options=(), today=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.today = today or timezone.localdate()
        self.fields["recipe"].choices = [
            ("", "Choose a recipe"),
            *[
                (str(option.recipe.pk), option.selection_label)
                for option in recipe_options
            ],
        ]

    def clean_date(self):
        value = self.cleaned_data["date"]
        if value < self.today:
            raise forms.ValidationError("Choose today or a future date.")
        return value

    def clean_custom_name(self):
        value = self.cleaned_data.get("custom_name") or ""
        return ShoppingItem.normalize_display_name(value)

    def clean(self):
        cleaned = super().clean()
        recipe_id = cleaned.get("recipe")
        custom_name = cleaned.get("custom_name", "")

        if recipe_id and custom_name:
            raise forms.ValidationError("Choose a recipe or enter a custom dinner, not both.")
        if not recipe_id and not custom_name:
            raise forms.ValidationError("Choose a recipe or enter a custom dinner.")

        if recipe_id:
            try:
                recipe = RecipePage.objects.live().get(pk=int(recipe_id))
            except (RecipePage.DoesNotExist, TypeError, ValueError):
                self.add_error("recipe", "Choose an available recipe.")
            else:
                cleaned["recipe_obj"] = recipe
                cleaned["meal_name"] = recipe.title
        else:
            cleaned["recipe_obj"] = None
            cleaned["meal_name"] = custom_name

        return cleaned
