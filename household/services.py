from dataclasses import dataclass

from django.db import models, transaction
from django.utils import timezone

from household.models import PantryItem, ShoppingItem

AUTO_CATEGORY = "auto"


_CATEGORY_KEYWORDS = {
    ShoppingItem.Category.PRODUCE: {
        "apple",
        "apples",
        "banana",
        "bananas",
        "broccoli",
        "carrot",
        "carrots",
        "cucumber",
        "lettuce",
        "onion",
        "onions",
        "pepper",
        "peppers",
        "potato",
        "potatoes",
        "tomato",
        "tomatoes",
    },
    ShoppingItem.Category.DAIRY: {
        "butter",
        "cheese",
        "cream",
        "egg",
        "eggs",
        "milk",
        "yoghurt",
        "yogurt",
    },
    ShoppingItem.Category.BAKERY: {
        "bagel",
        "bagels",
        "bread",
        "bun",
        "buns",
        "croissant",
        "roll",
        "rolls",
    },
    ShoppingItem.Category.MEAT_FISH: {
        "beef",
        "chicken",
        "fish",
        "pork",
        "salmon",
        "turkey",
    },
    ShoppingItem.Category.FROZEN: {
        "frozen berries",
        "frozen vegetables",
        "ice cream",
    },
    ShoppingItem.Category.HOUSEHOLD: {
        "cleaner",
        "detergent",
        "dishwasher tablets",
        "paper towels",
        "soap",
        "toilet paper",
        "trash bags",
        "washing liquid",
    },
}


@dataclass(frozen=True)
class AddShoppingResult:
    item: ShoppingItem
    created: bool


@dataclass(frozen=True)
class MutationResult:
    item: ShoppingItem
    merged: bool = False


def infer_category(name: str) -> str:
    normalized_name = ShoppingItem.normalize_identity(name)
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if normalized_name in keywords:
            return category
    return ShoppingItem.Category.OTHER


def resolve_category(name: str, requested_category: str) -> str:
    if requested_category == AUTO_CATEGORY:
        return infer_category(name)
    if requested_category not in ShoppingItem.Category.values:
        raise ValueError("Unsupported shopping category.")
    return requested_category


@transaction.atomic
def add_shopping_item(*, user, name: str, quantity: int = 1, category: str = AUTO_CATEGORY):
    display_name = ShoppingItem.normalize_display_name(name)
    normalized_name = ShoppingItem.normalize_identity(display_name)
    resolved_category = resolve_category(display_name, category)

    item, created = ShoppingItem.objects.get_or_create(
        user=user,
        normalized_name=normalized_name,
        status=ShoppingItem.Status.OPEN,
        deleted_at=None,
        defaults={
            "name": display_name,
            "quantity": quantity,
            "category": resolved_category,
        },
    )

    if created:
        return AddShoppingResult(item=item, created=True)

    ShoppingItem.objects.filter(pk=item.pk).update(quantity=models.F("quantity") + quantity)
    item.refresh_from_db()

    should_update_category = (category != AUTO_CATEGORY and item.category != resolved_category) or (
        item.category == ShoppingItem.Category.OTHER
        and resolved_category != ShoppingItem.Category.OTHER
    )
    if should_update_category:
        item.category = resolved_category
        item.save(update_fields=["category", "name", "normalized_name", "updated_at"])

    return AddShoppingResult(item=item, created=False)


@transaction.atomic
def ensure_shopping_item(
    *,
    user,
    name: str,
    category: str = AUTO_CATEGORY,
) -> AddShoppingResult:
    display_name = ShoppingItem.normalize_display_name(name)
    normalized_name = ShoppingItem.normalize_identity(display_name)
    resolved_category = resolve_category(display_name, category)

    item, created = ShoppingItem.objects.get_or_create(
        user=user,
        normalized_name=normalized_name,
        status=ShoppingItem.Status.OPEN,
        deleted_at=None,
        defaults={
            "name": display_name,
            "quantity": 1,
            "category": resolved_category,
        },
    )

    if (
        not created
        and item.category == ShoppingItem.Category.OTHER
        and resolved_category != ShoppingItem.Category.OTHER
    ):
        item.category = resolved_category
        item.save(update_fields=["category", "name", "normalized_name", "updated_at"])

    return AddShoppingResult(item=item, created=created)


@transaction.atomic
def toggle_shopping_item(*, user, item_id: int) -> MutationResult:
    item = ShoppingItem.objects.select_for_update().get(
        pk=item_id,
        user=user,
        deleted_at__isnull=True,
    )

    if item.status == ShoppingItem.Status.OPEN:
        item.complete()
        item.save(
            update_fields=[
                "status",
                "completed_at",
                "name",
                "normalized_name",
                "updated_at",
            ]
        )
        return MutationResult(item=item)

    existing_open = (
        ShoppingItem.objects.select_for_update()
        .filter(
            user=user,
            normalized_name=item.normalized_name,
            status=ShoppingItem.Status.OPEN,
            deleted_at__isnull=True,
        )
        .exclude(pk=item.pk)
        .first()
    )

    if existing_open:
        ShoppingItem.objects.filter(pk=existing_open.pk).update(
            quantity=models.F("quantity") + item.quantity
        )
        existing_open.refresh_from_db()
        item.deleted_at = timezone.now()
        item.save(
            update_fields=[
                "deleted_at",
                "name",
                "normalized_name",
                "updated_at",
            ]
        )
        return MutationResult(item=existing_open, merged=True)

    item.reopen()
    item.save(
        update_fields=[
            "status",
            "completed_at",
            "name",
            "normalized_name",
            "updated_at",
        ]
    )
    return MutationResult(item=item)


@transaction.atomic
def delete_shopping_item(*, user, item_id: int) -> ShoppingItem:
    item = ShoppingItem.objects.select_for_update().get(
        pk=item_id,
        user=user,
        deleted_at__isnull=True,
    )
    item.deleted_at = timezone.now()
    item.save(
        update_fields=[
            "deleted_at",
            "name",
            "normalized_name",
            "updated_at",
        ]
    )
    return item


@transaction.atomic
def restore_shopping_item(*, user, item_id: int) -> MutationResult:
    item = ShoppingItem.objects.select_for_update().get(
        pk=item_id,
        user=user,
        deleted_at__isnull=False,
    )

    if item.status == ShoppingItem.Status.OPEN:
        existing_open = (
            ShoppingItem.objects.select_for_update()
            .filter(
                user=user,
                normalized_name=item.normalized_name,
                status=ShoppingItem.Status.OPEN,
                deleted_at__isnull=True,
            )
            .exclude(pk=item.pk)
            .first()
        )
        if existing_open:
            ShoppingItem.objects.filter(pk=existing_open.pk).update(
                quantity=models.F("quantity") + item.quantity
            )
            existing_open.refresh_from_db()
            item.delete()
            return MutationResult(item=existing_open, merged=True)

    item.deleted_at = None
    item.save(
        update_fields=[
            "deleted_at",
            "name",
            "normalized_name",
            "updated_at",
        ]
    )
    return MutationResult(item=item)


@transaction.atomic
def create_pantry_item(*, user, data) -> PantryItem:
    return PantryItem.objects.create(
        user=user,
        name=data["name"],
        category=data["category"],
        quantity_mode=data["quantity_mode"],
        approximate_level=data["approximate_level"],
        amount=data["amount"],
        unit=data["unit"],
        low_stock_threshold=data["low_stock_threshold"],
        expires_on=data["expires_on"],
    )


@transaction.atomic
def update_pantry_item(*, user, item_id: int, data) -> PantryItem:
    item = PantryItem.objects.select_for_update().get(pk=item_id, user=user)
    item.name = data["name"]
    item.category = data["category"]
    item.quantity_mode = data["quantity_mode"]
    item.approximate_level = data["approximate_level"]
    item.amount = data["amount"]
    item.unit = data["unit"]
    item.low_stock_threshold = data["low_stock_threshold"]
    item.expires_on = data["expires_on"]
    item.save()
    return item


@transaction.atomic
def delete_pantry_item(*, user, item_id: int) -> PantryItem:
    item = PantryItem.objects.select_for_update().get(pk=item_id, user=user)
    item.delete()
    return item


@transaction.atomic
def add_pantry_item_to_shopping(*, user, item_id: int) -> AddShoppingResult:
    item = PantryItem.objects.select_for_update().get(pk=item_id, user=user)
    return ensure_shopping_item(
        user=user,
        name=item.name,
        category=item.category,
    )
