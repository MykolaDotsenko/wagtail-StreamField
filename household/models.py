import unicodedata
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


class ShoppingItem(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        COMPLETED = "completed", "Completed"

    class Category(models.TextChoices):
        PRODUCE = "produce", "Fruit & vegetables"
        DAIRY = "dairy", "Dairy & eggs"
        BAKERY = "bakery", "Bakery"
        MEAT_FISH = "meat_fish", "Meat & fish"
        PANTRY = "pantry", "Pantry"
        FROZEN = "frozen", "Frozen"
        HOUSEHOLD = "household", "Household"
        OTHER = "other", "Other"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shopping_items",
    )
    name = models.CharField(max_length=120)
    normalized_name = models.CharField(max_length=255, editable=False)
    quantity = models.PositiveIntegerField(default=1)
    category = models.CharField(
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER,
    )
    status = models.CharField(
        max_length=12,
        choices=Status.choices,
        default=Status.OPEN,
    )
    completed_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["category", "created_at", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(quantity__gte=1),
                name="shopping_quantity_at_least_one",
            ),
            models.CheckConstraint(
                condition=~models.Q(normalized_name=""),
                name="shopping_name_not_empty",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(status="open", completed_at__isnull=True)
                    | models.Q(status="completed", completed_at__isnull=False)
                ),
                name="shopping_completion_state_consistent",
            ),
            models.UniqueConstraint(
                fields=["user", "normalized_name"],
                condition=models.Q(status="open", deleted_at__isnull=True),
                name="unique_open_shopping_name_per_user",
            ),
        ]
        indexes = [
            models.Index(
                fields=["user", "status", "deleted_at", "category"],
                name="shopping_active_lookup",
            ),
        ]

    @staticmethod
    def normalize_display_name(value: str) -> str:
        normalized = unicodedata.normalize("NFKC", value)
        return " ".join(normalized.split())

    @classmethod
    def normalize_identity(cls, value: str) -> str:
        return cls.normalize_display_name(value).casefold()

    @property
    def is_completed(self) -> bool:
        return self.status == self.Status.COMPLETED

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    def complete(self) -> None:
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()

    def reopen(self) -> None:
        self.status = self.Status.OPEN
        self.completed_at = None

    def save(self, *args, **kwargs):
        self.name = self.normalize_display_name(self.name)
        self.normalized_name = self.normalize_identity(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PantryItem(models.Model):
    class QuantityMode(models.TextChoices):
        APPROXIMATE = "approximate", "Approximate"
        PRECISE = "precise", "Precise"

    class ApproximateLevel(models.TextChoices):
        FULL = "full", "Full"
        HALF = "half", "Half"
        LOW = "low", "Low"

    class Unit(models.TextChoices):
        ITEM = "item", "item"
        GRAM = "g", "g"
        KILOGRAM = "kg", "kg"
        MILLILITRE = "ml", "ml"
        LITRE = "l", "l"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pantry_items",
    )
    name = models.CharField(max_length=120)
    normalized_name = models.CharField(max_length=255, editable=False)
    category = models.CharField(
        max_length=20,
        choices=ShoppingItem.Category.choices,
        default=ShoppingItem.Category.OTHER,
    )
    quantity_mode = models.CharField(
        max_length=12,
        choices=QuantityMode.choices,
        default=QuantityMode.APPROXIMATE,
    )
    approximate_level = models.CharField(
        max_length=8,
        choices=ApproximateLevel.choices,
        blank=True,
        default=ApproximateLevel.FULL,
    )
    amount = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        blank=True,
        null=True,
    )
    unit = models.CharField(
        max_length=8,
        choices=Unit.choices,
        blank=True,
        default="",
    )
    low_stock_threshold = models.DecimalField(
        max_digits=9,
        decimal_places=2,
        blank=True,
        null=True,
    )
    expires_on = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name", "pk"]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(normalized_name=""),
                name="pantry_name_not_empty",
            ),
            models.CheckConstraint(
                condition=models.Q(amount__isnull=True) | models.Q(amount__gte=0),
                name="pantry_amount_non_negative",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(low_stock_threshold__isnull=True)
                    | models.Q(low_stock_threshold__gte=0)
                ),
                name="pantry_threshold_non_negative",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        quantity_mode="approximate",
                        amount__isnull=True,
                        unit="",
                        low_stock_threshold__isnull=True,
                        approximate_level__in=["full", "half", "low"],
                    )
                    | (
                        models.Q(
                            quantity_mode="precise",
                            amount__isnull=False,
                            approximate_level="",
                        )
                        & ~models.Q(unit="")
                    )
                ),
                name="pantry_quantity_mode_consistent",
            ),
            models.UniqueConstraint(
                fields=["user", "normalized_name"],
                name="unique_pantry_name_per_user",
            ),
        ]
        indexes = [
            models.Index(
                fields=["user", "expires_on"],
                name="pantry_expiry_lookup",
            ),
        ]

    @property
    def is_low_stock(self) -> bool:
        if self.quantity_mode == self.QuantityMode.APPROXIMATE:
            return self.approximate_level == self.ApproximateLevel.LOW
        return (
            self.low_stock_threshold is not None
            and self.amount is not None
            and self.amount <= self.low_stock_threshold
        )

    def is_expired(self, *, today) -> bool:
        return self.expires_on is not None and self.expires_on < today

    def expires_soon(self, *, today, days: int = 3) -> bool:
        if self.expires_on is None or self.expires_on < today:
            return False
        return self.expires_on <= today + timedelta(days=days)

    @property
    def has_unknown_expiry(self) -> bool:
        return self.expires_on is None

    @property
    def quantity_label(self) -> str:
        if self.quantity_mode == self.QuantityMode.APPROXIMATE:
            return self.get_approximate_level_display()
        amount = f"{self.amount.normalize():f}" if self.amount is not None else "0"
        return f"{amount} {self.get_unit_display()}"

    def save(self, *args, **kwargs):
        self.name = ShoppingItem.normalize_display_name(self.name)
        self.normalized_name = ShoppingItem.normalize_identity(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Routine(models.Model):
    class Frequency(models.TextChoices):
        ONE_TIME = "one_time", "One-time"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"

    class Room(models.TextChoices):
        WHOLE_HOME = "whole_home", "Whole home"
        KITCHEN = "kitchen", "Kitchen"
        BATHROOM = "bathroom", "Bathroom"
        BEDROOM = "bedroom", "Bedroom"
        LIVING_ROOM = "living_room", "Living room"
        OUTDOOR = "outdoor", "Outdoor"
        OTHER = "other", "Other"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="routines",
    )
    title = models.CharField(max_length=120)
    room = models.CharField(
        max_length=20,
        choices=Room.choices,
        default=Room.WHOLE_HOME,
    )
    frequency = models.CharField(
        max_length=12,
        choices=Frequency.choices,
        default=Frequency.WEEKLY,
    )
    due_on = models.DateField()
    postponed_until = models.DateField(blank=True, null=True)
    recurrence_anchor_day = models.PositiveSmallIntegerField(blank=True, null=True)
    expected_duration_minutes = models.PositiveSmallIntegerField(blank=True, null=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["due_on", "title", "pk"]
        indexes = [
            models.Index(
                fields=["user", "active", "due_on"],
                name="routine_due_lookup",
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(expected_duration_minutes__isnull=True)
                    | models.Q(expected_duration_minutes__gte=1)
                ),
                name="routine_duration_positive",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(postponed_until__isnull=True)
                    | models.Q(postponed_until__gt=models.F("due_on"))
                ),
                name="routine_postpone_after_due",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(
                        frequency="monthly",
                        recurrence_anchor_day__gte=1,
                        recurrence_anchor_day__lte=31,
                    )
                    | (
                        ~models.Q(frequency="monthly")
                        & models.Q(recurrence_anchor_day__isnull=True)
                    )
                ),
                name="routine_monthly_anchor_consistent",
            ),
        ]

    @property
    def effective_due_on(self):
        return self.postponed_until or self.due_on

    def __str__(self):
        return self.title


class RoutineEvent(models.Model):
    class Outcome(models.TextChoices):
        COMPLETED = "completed", "Completed"
        SKIPPED = "skipped", "Skipped"
        POSTPONED = "postponed", "Postponed"

    routine = models.ForeignKey(
        Routine,
        on_delete=models.CASCADE,
        related_name="events",
    )
    scheduled_for = models.DateField()
    outcome = models.CharField(max_length=12, choices=Outcome.choices)
    postponed_to = models.DateField(blank=True, null=True)
    acted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-acted_at", "-pk"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(
                        outcome="postponed",
                        postponed_to__isnull=False,
                        postponed_to__gt=models.F("scheduled_for"),
                    )
                    | (
                        models.Q(outcome__in=["completed", "skipped"])
                        & models.Q(postponed_to__isnull=True)
                    )
                ),
                name="routine_event_outcome_consistent",
            ),
            models.UniqueConstraint(
                fields=["routine", "scheduled_for"],
                condition=models.Q(outcome__in=["completed", "skipped"]),
                name="unique_terminal_routine_occurrence",
            ),
        ]

    def __str__(self):
        return f"{self.routine}: {self.get_outcome_display()}"
