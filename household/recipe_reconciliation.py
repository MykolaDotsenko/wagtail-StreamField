from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from django.db import transaction
from django.utils import timezone

from household.models import PantryItem, ShoppingItem
from household.services import ensure_shopping_item


class RecipeReadinessState(StrEnum):
    AVAILABLE = "available"
    LOW = "low"
    MISSING = "missing"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RecipeIngredientReadiness:
    line: object
    pantry_item: PantryItem | None
    state: RecipeReadinessState
    detail: str

    @property
    def label(self) -> str:
        return {
            RecipeReadinessState.AVAILABLE: "At home",
            RecipeReadinessState.LOW: "Running low",
            RecipeReadinessState.MISSING: "Missing",
            RecipeReadinessState.UNKNOWN: "Check stock",
        }[self.state]

    @property
    def needs_shopping(self) -> bool:
        return (
            not self.line.optional
            and self.state in {RecipeReadinessState.LOW, RecipeReadinessState.MISSING}
        )


@dataclass(frozen=True)
class RecipeReadinessSnapshot:
    items: tuple[RecipeIngredientReadiness, ...]
    needed_items: tuple[RecipeIngredientReadiness, ...]
    available_count: int
    low_count: int
    missing_count: int
    unknown_count: int

    @property
    def needed_count(self) -> int:
        return len(self.needed_items)


@dataclass(frozen=True)
class AddRecipeShoppingResult:
    added_count: int
    existing_count: int
    considered_count: int


_BASE_UNITS = {
    "item": ("item", Decimal("1")),
    "g": ("mass", Decimal("1")),
    "kg": ("mass", Decimal("1000")),
    "ml": ("volume", Decimal("1")),
    "l": ("volume", Decimal("1000")),
}


def _precise_readiness(*, line, pantry_item: PantryItem) -> tuple[RecipeReadinessState, str]:
    if line.amount is None:
        if pantry_item.amount is None:
            return RecipeReadinessState.UNKNOWN, "Precise Pantry quantity is incomplete."
        if pantry_item.amount <= 0 or pantry_item.is_low_stock:
            return RecipeReadinessState.LOW, f"Pantry has {pantry_item.quantity_label}."
        return RecipeReadinessState.AVAILABLE, f"Pantry has {pantry_item.quantity_label}."

    recipe_unit = _BASE_UNITS.get(line.unit)
    pantry_unit = _BASE_UNITS.get(pantry_item.unit)
    if recipe_unit is None or pantry_unit is None or recipe_unit[0] != pantry_unit[0]:
        return (
            RecipeReadinessState.UNKNOWN,
            "Units cannot be compared safely. Check the Pantry amount.",
        )

    required = line.amount * recipe_unit[1]
    available = pantry_item.amount * pantry_unit[1]
    if available < required or pantry_item.is_low_stock:
        return RecipeReadinessState.LOW, f"Pantry has {pantry_item.quantity_label}."

    return RecipeReadinessState.AVAILABLE, f"Pantry has {pantry_item.quantity_label}."


def _line_readiness(*, line, pantry_item: PantryItem | None, today) -> RecipeIngredientReadiness:
    if pantry_item is None:
        return RecipeIngredientReadiness(
            line=line,
            pantry_item=None,
            state=RecipeReadinessState.MISSING,
            detail="Not found in Pantry.",
        )

    if pantry_item.is_expired(today=today):
        return RecipeIngredientReadiness(
            line=line,
            pantry_item=pantry_item,
            state=RecipeReadinessState.UNKNOWN,
            detail="Pantry entry is expired. Check it before use.",
        )

    if pantry_item.quantity_mode == PantryItem.QuantityMode.APPROXIMATE:
        if pantry_item.approximate_level == PantryItem.ApproximateLevel.LOW:
            state = RecipeReadinessState.LOW
            detail = "Pantry marks this as low."
        elif line.amount is None:
            state = RecipeReadinessState.AVAILABLE
            detail = f"Pantry level: {pantry_item.quantity_label}."
        else:
            state = RecipeReadinessState.UNKNOWN
            detail = "Pantry quantity is approximate. Check whether there is enough."
        return RecipeIngredientReadiness(
            line=line,
            pantry_item=pantry_item,
            state=state,
            detail=detail,
        )

    state, detail = _precise_readiness(line=line, pantry_item=pantry_item)
    return RecipeIngredientReadiness(
        line=line,
        pantry_item=pantry_item,
        state=state,
        detail=detail,
    )


def recipe_readiness(*, recipe, user, today=None) -> RecipeReadinessSnapshot:
    today = today or timezone.localdate()
    pantry_items = list(
        PantryItem.objects.filter(user=user)
        .select_related("ingredient")
        .order_by("pk")
    )
    by_ingredient = {
        item.ingredient_id: item
        for item in pantry_items
        if item.ingredient_id is not None
    }
    by_name = {
        item.normalized_name: item
        for item in pantry_items
        if item.ingredient_id is None
    }

    entries = []
    for line in recipe.ingredient_lines.select_related("ingredient").order_by("sort_order", "pk"):
        pantry_item = by_ingredient.get(line.ingredient_id)
        if pantry_item is None:
            pantry_item = by_name.get(line.ingredient.normalized_name)
        entries.append(_line_readiness(line=line, pantry_item=pantry_item, today=today))

    items = tuple(entries)
    needed_items = tuple(entry for entry in items if entry.needs_shopping)

    return RecipeReadinessSnapshot(
        items=items,
        needed_items=needed_items,
        available_count=sum(
            entry.state == RecipeReadinessState.AVAILABLE for entry in items
        ),
        low_count=sum(entry.state == RecipeReadinessState.LOW for entry in items),
        missing_count=sum(entry.state == RecipeReadinessState.MISSING for entry in items),
        unknown_count=sum(entry.state == RecipeReadinessState.UNKNOWN for entry in items),
    )


@transaction.atomic
def add_needed_recipe_ingredients(*, recipe, user) -> AddRecipeShoppingResult:
    snapshot = recipe_readiness(recipe=recipe, user=user)
    added_count = 0
    existing_count = 0

    for entry in snapshot.needed_items:
        ingredient = entry.line.ingredient
        category = (
            ingredient.category
            if ingredient.category in ShoppingItem.Category.values
            else ShoppingItem.Category.OTHER
        )
        result = ensure_shopping_item(
            user=user,
            name=ingredient.name,
            category=category,
            ingredient=ingredient,
        )
        if result.created:
            added_count += 1
        else:
            existing_count += 1

    return AddRecipeShoppingResult(
        added_count=added_count,
        existing_count=existing_count,
        considered_count=snapshot.needed_count,
    )
