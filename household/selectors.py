from collections import defaultdict
from dataclasses import dataclass

from .models import ShoppingItem


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
