from collections import defaultdict
from dataclasses import dataclass

from django.utils import timezone

from .models import PantryItem, ShoppingItem


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
    other = [
        entry
        for entry in entries
        if not entry.needs_attention
    ]

    return PantrySnapshot(
        attention_items=tuple(attention),
        other_items=tuple(other),
        total_count=len(entries),
    )
