import datetime

from django.conf import settings
from django.db import models


class HouseholdCategory(models.TextChoices):
    PRODUCE = "produce", "Produce"
    DAIRY = "dairy", "Dairy"
    PANTRY = "pantry", "Pantry"
    FROZEN = "frozen", "Frozen"
    HOUSEHOLD = "household", "Household"
    OTHER = "other", "Other"


class ShoppingItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shopping_items"
    )
    name = models.CharField(max_length=120)
    quantity = models.CharField(max_length=40, default="1")
    category = models.CharField(
        max_length=20, choices=HouseholdCategory.choices, default=HouseholdCategory.OTHER
    )
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_done", "category", "name"]
        indexes = [models.Index(fields=["user", "is_done"], name="shop_user_done_idx")]

    def __str__(self):
        return self.name


class PantryItem(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pantry_items"
    )
    name = models.CharField(max_length=120)
    quantity = models.CharField(max_length=40, default="1")
    category = models.CharField(
        max_length=20, choices=HouseholdCategory.choices, default=HouseholdCategory.PANTRY
    )
    expires_on = models.DateField(null=True, blank=True)
    low_stock = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-low_stock", "expires_on", "name"]
        indexes = [models.Index(fields=["user", "expires_on"], name="pantry_user_exp_idx")]

    @property
    def needs_attention(self):
        if self.low_stock:
            return True
        if self.expires_on:
            return self.expires_on <= datetime.date.today() + datetime.timedelta(days=3)
        return False

    def __str__(self):
        return self.name


class Chore(models.Model):
    class Room(models.TextChoices):
        KITCHEN = "kitchen", "Kitchen"
        BATHROOM = "bathroom", "Bathroom"
        BEDROOM = "bedroom", "Bedroom"
        LIVING = "living", "Living room"
        LAUNDRY = "laundry", "Laundry"
        WHOLE_HOME = "whole_home", "Whole home"

    class Frequency(models.TextChoices):
        ONCE = "once", "One-off"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chores")
    title = models.CharField(max_length=140)
    room = models.CharField(max_length=20, choices=Room.choices, default=Room.WHOLE_HOME)
    frequency = models.CharField(
        max_length=20, choices=Frequency.choices, default=Frequency.WEEKLY
    )
    due_on = models.DateField(default=datetime.date.today)
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_done", "due_on", "room", "title"]
        indexes = [
            models.Index(fields=["user", "is_done", "due_on"], name="chore_user_due_idx")
        ]

    def __str__(self):
        return self.title


class MealPlanEntry(models.Model):
    class MealType(models.TextChoices):
        BREAKFAST = "breakfast", "Breakfast"
        LUNCH = "lunch", "Lunch"
        DINNER = "dinner", "Dinner"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="meal_plan_entries"
    )
    date = models.DateField(default=datetime.date.today)
    meal_type = models.CharField(max_length=20, choices=MealType.choices)
    recipe = models.ForeignKey(
        "blog.RecipePage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="meal_plan_entries",
    )
    custom_meal = models.CharField(max_length=140, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "meal_type"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "date", "meal_type"], name="unique_meal_slot_per_user"
            )
        ]
        indexes = [models.Index(fields=["user", "date"], name="meal_user_date_idx")]

    @property
    def label(self):
        return self.recipe.title if self.recipe_id else self.custom_meal

    def __str__(self):
        return f"{self.date} · {self.get_meal_type_display()}: {self.label or 'Unplanned'}"
