from calendar import monthrange
from dataclasses import dataclass
from datetime import date, timedelta

from django.db import models, transaction
from django.utils import timezone

from household.models import PantryItem, Routine, RoutineEvent, ShoppingItem

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


class StaleRoutineAction(Exception):
    pass


def _monthly_date(*, year: int, month: int, anchor_day: int) -> date:
    return date(year, month, min(anchor_day, monthrange(year, month)[1]))


def _next_month(*, current: date, anchor_day: int) -> date:
    year = current.year + (1 if current.month == 12 else 0)
    month = 1 if current.month == 12 else current.month + 1
    return _monthly_date(year=year, month=month, anchor_day=anchor_day)


def next_routine_due_date(
    *,
    frequency: str,
    current_due: date,
    anchor_day: int | None,
    after_date: date,
) -> date | None:
    if frequency == Routine.Frequency.ONE_TIME:
        return None

    if frequency == Routine.Frequency.DAILY:
        candidate = current_due + timedelta(days=1)
        if candidate <= after_date:
            candidate = after_date + timedelta(days=1)
        return candidate

    if frequency == Routine.Frequency.WEEKLY:
        candidate = current_due + timedelta(days=7)
        if candidate <= after_date:
            weeks = ((after_date - candidate).days // 7) + 1
            candidate += timedelta(days=weeks * 7)
        return candidate

    if frequency == Routine.Frequency.MONTHLY:
        if anchor_day is None:
            raise ValueError("Monthly routines require an anchor day.")
        candidate = _next_month(current=current_due, anchor_day=anchor_day)
        while candidate <= after_date:
            candidate = _next_month(current=candidate, anchor_day=anchor_day)
        return candidate

    raise ValueError("Unsupported routine frequency.")


@transaction.atomic
def create_routine(*, user, data) -> Routine:
    frequency = data["frequency"]
    due_on = data["due_on"]
    return Routine.objects.create(
        user=user,
        title=data["title"],
        room=data["room"],
        frequency=frequency,
        due_on=due_on,
        recurrence_anchor_day=(due_on.day if frequency == Routine.Frequency.MONTHLY else None),
        expected_duration_minutes=data["expected_duration_minutes"],
    )


@transaction.atomic
def update_routine(*, user, routine_id: int, data) -> Routine:
    routine = Routine.objects.select_for_update().get(pk=routine_id, user=user)
    frequency = data["frequency"]
    due_on = data["due_on"]
    routine.title = data["title"]
    routine.room = data["room"]
    routine.frequency = frequency
    routine.due_on = due_on
    routine.postponed_until = None
    routine.recurrence_anchor_day = due_on.day if frequency == Routine.Frequency.MONTHLY else None
    routine.expected_duration_minutes = data["expected_duration_minutes"]
    routine.active = True
    routine.save()
    return routine


def _locked_current_routine(*, user, routine_id: int, expected_scheduled_for: date) -> Routine:
    routine = Routine.objects.select_for_update().get(
        pk=routine_id,
        user=user,
        active=True,
    )
    if routine.due_on != expected_scheduled_for:
        raise StaleRoutineAction
    return routine


@transaction.atomic
def _terminal_routine_action(
    *,
    user,
    routine_id: int,
    expected_scheduled_for: date,
    outcome: str,
    today: date,
) -> Routine:
    routine = _locked_current_routine(
        user=user,
        routine_id=routine_id,
        expected_scheduled_for=expected_scheduled_for,
    )

    RoutineEvent.objects.create(
        routine=routine,
        scheduled_for=routine.due_on,
        outcome=outcome,
    )

    next_due = next_routine_due_date(
        frequency=routine.frequency,
        current_due=routine.due_on,
        anchor_day=routine.recurrence_anchor_day,
        after_date=today,
    )

    routine.postponed_until = None
    if next_due is None:
        routine.active = False
    else:
        routine.due_on = next_due

    routine.save(
        update_fields=[
            "active",
            "due_on",
            "postponed_until",
            "updated_at",
        ]
    )
    return routine


def complete_routine(
    *,
    user,
    routine_id: int,
    expected_scheduled_for: date,
    today: date,
) -> Routine:
    return _terminal_routine_action(
        user=user,
        routine_id=routine_id,
        expected_scheduled_for=expected_scheduled_for,
        outcome=RoutineEvent.Outcome.COMPLETED,
        today=today,
    )


def skip_routine(
    *,
    user,
    routine_id: int,
    expected_scheduled_for: date,
    today: date,
) -> Routine:
    return _terminal_routine_action(
        user=user,
        routine_id=routine_id,
        expected_scheduled_for=expected_scheduled_for,
        outcome=RoutineEvent.Outcome.SKIPPED,
        today=today,
    )


@transaction.atomic
def postpone_routine(
    *,
    user,
    routine_id: int,
    expected_scheduled_for: date,
    expected_effective_due_on: date,
    postponed_to: date,
) -> Routine:
    routine = _locked_current_routine(
        user=user,
        routine_id=routine_id,
        expected_scheduled_for=expected_scheduled_for,
    )
    if routine.effective_due_on != expected_effective_due_on:
        raise StaleRoutineAction
    if postponed_to <= routine.effective_due_on:
        raise ValueError("Postponed date must be after the current due date.")

    RoutineEvent.objects.create(
        routine=routine,
        scheduled_for=routine.due_on,
        outcome=RoutineEvent.Outcome.POSTPONED,
        postponed_to=postponed_to,
    )
    routine.postponed_until = postponed_to
    routine.save(update_fields=["postponed_until", "updated_at"])
    return routine


@transaction.atomic
def archive_routine(*, user, routine_id: int) -> Routine:
    routine = Routine.objects.select_for_update().get(pk=routine_id, user=user)
    routine.active = False
    routine.postponed_until = None
    routine.save(update_fields=["active", "postponed_until", "updated_at"])
    return routine
