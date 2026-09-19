from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from django.utils import timezone

from recipes.models import RecipePage

from .models import MealPlanEntry, PantryItem, Routine, ShoppingItem
from .recipe_reconciliation import recipe_readiness


@dataclass(frozen=True)
class ShoppingGroup:
    key: str
    label: str
    items: tuple[ShoppingItem, ...]


@dataclass(frozen=True)
class ShoppingSnapshot:
    open_groups: tuple[ShoppingGroup, ...]
    completed_items: tuple[ShoppingItem, ...]
    open_count: int
    completed_count: int


def shopping_snapshot(*, user) -> ShoppingSnapshot:
    active_items = list(
        ShoppingItem.objects.filter(
            user=user,
            deleted_at__isnull=True,
        ).order_by("category", "created_at", "pk")
    )

    grouped = defaultdict(list)
    completed = []

    for item in active_items:
        if item.status == ShoppingItem.Status.COMPLETED:
            completed.append(item)
        else:
            grouped[item.category].append(item)

    open_groups = tuple(
        ShoppingGroup(
            key=category,
            label=label,
            items=tuple(grouped[category]),
        )
        for category, label in ShoppingItem.Category.choices
        if grouped[category]
    )

    completed.sort(
        key=lambda item: item.completed_at or item.updated_at,
        reverse=True,
    )

    return ShoppingSnapshot(
        open_groups=open_groups,
        completed_items=tuple(completed),
        open_count=sum(len(group.items) for group in open_groups),
        completed_count=len(completed),
    )


def deleted_shopping_item_for_undo(*, user, item_id: str | None):
    if not item_id or not item_id.isdigit():
        return None

    return ShoppingItem.objects.filter(
        pk=int(item_id),
        user=user,
        deleted_at__isnull=False,
    ).first()


@dataclass(frozen=True)
class PantryEntry:
    item: PantryItem
    is_expired: bool
    expires_soon: bool
    is_low_stock: bool
    expiry_unknown: bool

    @property
    def needs_attention(self) -> bool:
        return self.is_expired or self.expires_soon or self.is_low_stock


@dataclass(frozen=True)
class PantrySnapshot:
    attention_items: tuple[PantryEntry, ...]
    other_items: tuple[PantryEntry, ...]
    total_count: int


def pantry_snapshot(*, user, today=None) -> PantrySnapshot:
    today = today or timezone.localdate()
    entries = []

    for item in PantryItem.objects.filter(user=user).order_by("name", "pk"):
        entries.append(
            PantryEntry(
                item=item,
                is_expired=item.is_expired(today=today),
                expires_soon=item.expires_soon(today=today),
                is_low_stock=item.is_low_stock,
                expiry_unknown=item.has_unknown_expiry,
            )
        )

    def attention_key(entry):
        if entry.is_expired:
            priority = 0
        elif entry.expires_soon:
            priority = 1
        else:
            priority = 2
        return (priority, entry.item.name.casefold(), entry.item.pk)

    attention = sorted(
        (entry for entry in entries if entry.needs_attention),
        key=attention_key,
    )
    other = [entry for entry in entries if not entry.needs_attention]

    return PantrySnapshot(
        attention_items=tuple(attention),
        other_items=tuple(other),
        total_count=len(entries),
    )


@dataclass(frozen=True)
class RoutineEntry:
    routine: Routine
    effective_due_on: date
    is_overdue: bool
    is_due_today: bool
    is_postponed: bool


@dataclass(frozen=True)
class RoutineSnapshot:
    due_items: tuple[RoutineEntry, ...]
    upcoming_items: tuple[RoutineEntry, ...]
    total_active: int


def routine_snapshot(*, user, today=None) -> RoutineSnapshot:
    today = today or timezone.localdate()
    entries = []

    for routine in Routine.objects.filter(user=user, active=True).order_by(
        "due_on",
        "title",
        "pk",
    ):
        effective_due_on = routine.effective_due_on
        entries.append(
            RoutineEntry(
                routine=routine,
                effective_due_on=effective_due_on,
                is_overdue=effective_due_on < today,
                is_due_today=effective_due_on == today,
                is_postponed=routine.postponed_until is not None,
            )
        )

    due_items = tuple(
        sorted(
            (entry for entry in entries if entry.effective_due_on <= today),
            key=lambda entry: (
                entry.effective_due_on,
                entry.routine.title.casefold(),
                entry.routine.pk,
            ),
        )
    )
    upcoming_items = tuple(
        sorted(
            (entry for entry in entries if entry.effective_due_on > today),
            key=lambda entry: (
                entry.effective_due_on,
                entry.routine.title.casefold(),
                entry.routine.pk,
            ),
        )
    )

    return RoutineSnapshot(
        due_items=due_items,
        upcoming_items=upcoming_items,
        total_active=len(entries),
    )


@dataclass(frozen=True)
class MealRecipeOption:
    recipe: RecipePage
    readiness: object

    @property
    def selection_label(self) -> str:
        parts = [f"{self.recipe.title} — {self.recipe.total_minutes} min"]
        if not self.readiness.items:
            parts.append("ingredient data incomplete")
        else:
            if self.readiness.needed_count:
                count = self.readiness.needed_count
                parts.append(
                    f"{count} item{'s' if count != 1 else ''} need{'s' if count == 1 else ''} Shopping"
                )
            if self.readiness.unknown_count:
                count = self.readiness.unknown_count
                parts.append(f"{count} check stock")
            if not self.readiness.needed_count and not self.readiness.unknown_count:
                parts.append("Pantry ready")
        return " · ".join(parts)


def meal_recipe_options(*, user, today=None) -> tuple[MealRecipeOption, ...]:
    today = today or timezone.localdate()
    options = []

    for recipe in RecipePage.objects.live().order_by("title", "pk"):
        readiness = recipe_readiness(recipe=recipe, user=user, today=today)
        options.append(MealRecipeOption(recipe=recipe, readiness=readiness))

    def rank(option):
        readiness = option.readiness
        if not readiness.items:
            bucket = 3
        elif not readiness.needed_count and not readiness.unknown_count:
            bucket = 0
        elif not readiness.unknown_count:
            bucket = 1
        else:
            bucket = 2
        return (
            bucket,
            readiness.needed_count,
            readiness.unknown_count,
            option.recipe.total_minutes,
            option.recipe.title.casefold(),
            option.recipe.pk,
        )

    return tuple(sorted(options, key=rank))


@dataclass(frozen=True)
class MealPlanDay:
    date: date
    entry: MealPlanEntry | None
    readiness: object | None
    recipe_available: bool
    is_today: bool


@dataclass(frozen=True)
class MealPlanWeek:
    start: date
    end: date
    days: tuple[MealPlanDay, ...]


def week_start(anchor: date) -> date:
    return anchor - timedelta(days=anchor.weekday())


def meal_plan_for_date(*, user, meal_date: date) -> MealPlanEntry | None:
    return (
        MealPlanEntry.objects.filter(user=user, date=meal_date)
        .select_related("recipe")
        .first()
    )


def meal_plan_week(*, user, anchor=None, today=None) -> MealPlanWeek:
    today = today or timezone.localdate()
    anchor = anchor or today
    start = week_start(anchor)
    end = start + timedelta(days=6)

    entries = {
        entry.date: entry
        for entry in MealPlanEntry.objects.filter(
            user=user,
            date__range=(start, end),
        ).select_related("recipe")
    }

    days = []
    for offset in range(7):
        meal_date = start + timedelta(days=offset)
        entry = entries.get(meal_date)
        recipe_available = bool(entry and entry.recipe_id and entry.recipe and entry.recipe.live)
        readiness = (
            recipe_readiness(recipe=entry.recipe, user=user, today=meal_date)
            if recipe_available
            else None
        )
        days.append(
            MealPlanDay(
                date=meal_date,
                entry=entry,
                readiness=readiness,
                recipe_available=recipe_available,
                is_today=meal_date == today,
            )
        )

    return MealPlanWeek(
        start=start,
        end=end,
        days=tuple(days),
    )


@dataclass(frozen=True)
class TodaySignal:
    kind: str
    priority: int
    title: str
    detail: str
    destination: str


@dataclass(frozen=True)
class TodaySnapshot:
    signals: tuple[TodaySignal, ...]
    total_action_count: int
    has_more: bool
    shopping_count: int
    dinner_name: str | None
    dinner_needed_count: int
    dinner_unknown_count: int


def today_snapshot(*, user, today=None, limit: int = 6) -> TodaySnapshot:
    today = today or timezone.localdate()
    pantry = pantry_snapshot(user=user, today=today)
    routines = routine_snapshot(user=user, today=today)
    shopping = shopping_snapshot(user=user)
    dinner = meal_plan_for_date(user=user, meal_date=today)
    dinner_readiness = (
        recipe_readiness(recipe=dinner.recipe, user=user, today=today)
        if dinner and dinner.recipe_id and dinner.recipe and dinner.recipe.live
        else None
    )

    signals = []

    for entry in routines.due_items:
        if entry.is_overdue:
            signals.append(
                TodaySignal(
                    kind="routine_overdue",
                    priority=0,
                    title=f"{entry.routine.title} is overdue",
                    detail=f"{entry.routine.get_room_display()} · due {entry.effective_due_on:%b %d}",
                    destination="routines",
                )
            )
        else:
            signals.append(
                TodaySignal(
                    kind="routine_today",
                    priority=2,
                    title=f"Due today: {entry.routine.title}",
                    detail=f"{entry.routine.get_room_display()} · {entry.routine.get_frequency_display()}",
                    destination="routines",
                )
            )

    for entry in pantry.attention_items:
        if entry.is_expired:
            signals.append(
                TodaySignal(
                    kind="pantry_expired",
                    priority=1,
                    title=f"{entry.item.name} has expired",
                    detail=f"{entry.item.quantity_label} · check before use",
                    destination="pantry",
                )
            )
        elif entry.expires_soon:
            signals.append(
                TodaySignal(
                    kind="pantry_use_soon",
                    priority=3,
                    title=f"Use {entry.item.name} soon",
                    detail=f"Best before / expiry {entry.item.expires_on:%b %d}",
                    destination="pantry",
                )
            )
        elif entry.is_low_stock:
            signals.append(
                TodaySignal(
                    kind="pantry_low",
                    priority=4,
                    title=f"{entry.item.name} is running low",
                    detail=f"{entry.item.quantity_label} · consider Shopping",
                    destination="pantry",
                )
            )

    if dinner is None:
        signals.append(
            TodaySignal(
                kind="dinner_unplanned",
                priority=5,
                title="Dinner is not planned yet",
                detail="Choose a recipe or add a simple custom dinner.",
                destination="plan",
            )
        )
    elif dinner_readiness and dinner_readiness.needed_count:
        count = dinner_readiness.needed_count
        signals.append(
            TodaySignal(
                kind="dinner_needs",
                priority=5,
                title=f"{dinner.name} needs {count} Shopping item{'s' if count != 1 else ''}",
                detail="Open Plan to review dinner readiness.",
                destination="plan",
            )
        )
    elif dinner_readiness and dinner_readiness.unknown_count:
        count = dinner_readiness.unknown_count
        signals.append(
            TodaySignal(
                kind="dinner_unknown",
                priority=5,
                title=f"Check stock for {dinner.name}",
                detail=f"{count} ingredient{'s' if count != 1 else ''} cannot be confirmed safely.",
                destination="plan",
            )
        )

    if shopping.open_count:
        signals.append(
            TodaySignal(
                kind="shopping",
                priority=6,
                title=f"{shopping.open_count} item{'s' if shopping.open_count != 1 else ''} to buy",
                detail="Your active shopping list is ready when you are.",
                destination="shopping",
            )
        )

    signals.sort(key=lambda signal: (signal.priority, signal.title.casefold()))
    total_action_count = len(signals)

    return TodaySnapshot(
        signals=tuple(signals[:limit]),
        total_action_count=total_action_count,
        has_more=total_action_count > limit,
        shopping_count=shopping.open_count,
        dinner_name=dinner.name if dinner else None,
        dinner_needed_count=(dinner_readiness.needed_count if dinner_readiness else 0),
        dinner_unknown_count=(dinner_readiness.unknown_count if dinner_readiness else 0),
    )
