from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class ShoppingItem(models.Model):
    class Category(models.TextChoices):
        PRODUCE = "produce", "Fruit & vegetables"
        DAIRY = "dairy", "Dairy"
        PANTRY = "pantry", "Pantry"
        HOUSEHOLD = "household", "Household"
        OTHER = "other", "Other"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shopping_items")
    name = models.CharField(max_length=120)
    quantity = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1)])
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    is_done = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["is_done", "category", "-created_at"]

    def __str__(self):
        return self.name


class PantryItem(models.Model):
    class Unit(models.TextChoices):
        PCS = "pcs", "pcs"
        G = "g", "g"
        KG = "kg", "kg"
        ML = "ml", "ml"
        L = "l", "l"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="pantry_items")
    name = models.CharField(max_length=120)
    quantity = models.DecimalField(max_digits=8, decimal_places=2, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=8, choices=Unit.choices, default=Unit.PCS)
    low_stock_threshold = models.DecimalField(max_digits=8, decimal_places=2, default=1, validators=[MinValueValidator(0)])
    expires_on = models.DateField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["expires_on", "name"]

    @property
    def is_low_stock(self):
        return self.quantity <= self.low_stock_threshold

    @property
    def expires_soon(self):
        if not self.expires_on:
            return False
        return self.expires_on <= timezone.localdate() + timezone.timedelta(days=3)

    def __str__(self):
        return self.name


class Chore(models.Model):
    class Frequency(models.TextChoices):
        ONCE = "once", "One time"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    class Room(models.TextChoices):
        KITCHEN = "kitchen", "Kitchen"
        BATHROOM = "bathroom", "Bathroom"
        BEDROOM = "bedroom", "Bedroom"
        LIVING = "living", "Living room"
        WHOLE_HOME = "whole-home", "Whole home"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chores")
    title = models.CharField(max_length=140)
    room = models.CharField(max_length=20, choices=Room.choices, default=Room.WHOLE_HOME)
    frequency = models.CharField(max_length=12, choices=Frequency.choices, default=Frequency.WEEKLY)
    due_on = models.DateField(default=timezone.localdate)
    is_done = models.BooleanField(default=False)

    class Meta:
        ordering = ["is_done", "due_on", "room", "title"]

    @property
    def is_overdue(self):
        return not self.is_done and self.due_on < timezone.localdate()

    def __str__(self):
        return self.title
