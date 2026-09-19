from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import ShoppingItemCreateForm
from .models import ShoppingItem
from .selectors import deleted_shopping_item_for_undo, shopping_snapshot
from .services import (
    add_shopping_item,
    delete_shopping_item,
    restore_shopping_item,
    toggle_shopping_item,
)


def _shopping_url(*, shopping_mode: bool = False, undo_item_id: int | None = None) -> str:
    params = {}
    if shopping_mode:
        params["mode"] = "shop"
    if undo_item_id is not None:
        params["undo"] = undo_item_id

    url = reverse("household:shopping")
    return f"{url}?{urlencode(params)}" if params else url


def _is_shopping_mode(request) -> bool:
    return request.GET.get("mode") == "shop" or request.POST.get("mode") == "shop"


@login_required
def shopping(request):
    shopping_mode = _is_shopping_mode(request)
    form = ShoppingItemCreateForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            result = add_shopping_item(
                user=request.user,
                name=form.cleaned_data["name"],
                quantity=form.cleaned_data["quantity"],
                category=form.cleaned_data["category"],
            )
            if result.created:
                messages.success(request, f"{result.item.name} added.")
            else:
                messages.success(
                    request,
                    f"{result.item.name} is already on the list — quantity updated.",
                )
            return redirect(_shopping_url(shopping_mode=shopping_mode))

    snapshot = shopping_snapshot(user=request.user)
    undo_candidate = deleted_shopping_item_for_undo(
        user=request.user,
        item_id=request.GET.get("undo"),
    )

    return render(
        request,
        "household/shopping.html",
        {
            "form": form,
            "snapshot": snapshot,
            "shopping_mode": shopping_mode,
            "undo_candidate": undo_candidate,
        },
    )


@login_required
@require_POST
def toggle_item(request, item_id):
    try:
        result = toggle_shopping_item(user=request.user, item_id=item_id)
    except ShoppingItem.DoesNotExist as exc:
        raise Http404 from exc

    if result.merged:
        messages.success(
            request,
            f"{result.item.name} was merged into the open list.",
        )
    elif result.item.is_completed:
        messages.success(request, f"{result.item.name} marked as bought.")
    else:
        messages.success(request, f"{result.item.name} moved back to the list.")

    return redirect(_shopping_url(shopping_mode=_is_shopping_mode(request)))


@login_required
@require_POST
def delete_item(request, item_id):
    try:
        item = delete_shopping_item(user=request.user, item_id=item_id)
    except ShoppingItem.DoesNotExist as exc:
        raise Http404 from exc

    return redirect(_shopping_url(undo_item_id=item.pk))


@login_required
@require_POST
def restore_item(request, item_id):
    try:
        result = restore_shopping_item(user=request.user, item_id=item_id)
    except ShoppingItem.DoesNotExist as exc:
        raise Http404 from exc

    if result.merged:
        messages.success(
            request,
            f"{result.item.name} was restored by merging it into the open item.",
        )
    else:
        messages.success(request, f"{result.item.name} restored.")

    return redirect("household:shopping")
