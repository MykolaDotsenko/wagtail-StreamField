import unicodedata

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
    normalized_name = models.CharField(max_length=120, editable=False)
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
