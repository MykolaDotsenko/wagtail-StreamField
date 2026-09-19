from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from django.utils import timezone

from .models import PantryItem, Routine, ShoppingItem


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


def today_snapshot(*, user, today=None, limit: int = 6) -> TodaySnapshot:
    today = today or timezone.localdate()
    pantry = pantry_snapshot(user=user, today=today)
    routines = routine_snapshot(user=user, today=today)
    shopping = shopping_snapshot(user=user)

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

    if shopping.open_count:
        signals.append(
            TodaySignal(
                kind="shopping",
                priority=5,
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
    )
