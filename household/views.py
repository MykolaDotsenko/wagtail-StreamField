from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    PantryItemForm,
    RoutineActionForm,
    RoutineForm,
    RoutinePostponeForm,
    ShoppingItemCreateForm,
)
from .models import PantryItem, Routine, ShoppingItem
from .selectors import (
    deleted_shopping_item_for_undo,
    pantry_snapshot,
    routine_snapshot,
    shopping_snapshot,
)
from .services import (
    StaleRoutineAction,
    add_pantry_item_to_shopping,
    add_shopping_item,
    archive_routine,
    complete_routine,
    create_pantry_item,
    create_routine,
    delete_pantry_item,
    delete_shopping_item,
    postpone_routine,
    restore_shopping_item,
    skip_routine,
    toggle_shopping_item,
    update_pantry_item,
    update_routine,
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


@login_required
def pantry(request):
    form = PantryItemForm(request.POST or None, user=request.user)

    if request.method == "POST" and form.is_valid():
        try:
            item = create_pantry_item(user=request.user, data=form.cleaned_data)
        except IntegrityError:
            form.add_error("name", "This item is already in your pantry.")
        else:
            messages.success(request, f"{item.name} added to pantry.")
            return redirect("household:pantry")

    return render(
        request,
        "household/pantry.html",
        {
            "form": form,
            "snapshot": pantry_snapshot(user=request.user),
        },
    )


def _pantry_initial(item):
    return {
        "name": item.name,
        "category": item.category,
        "quantity_mode": item.quantity_mode,
        "approximate_level": item.approximate_level,
        "amount": item.amount,
        "unit": item.unit,
        "low_stock_threshold": item.low_stock_threshold,
        "expires_on": item.expires_on,
    }


@login_required
def edit_pantry_item(request, item_id):
    try:
        item = PantryItem.objects.get(pk=item_id, user=request.user)
    except PantryItem.DoesNotExist as exc:
        raise Http404 from exc

    form = PantryItemForm(
        request.POST or None,
        user=request.user,
        instance=item,
        initial=_pantry_initial(item),
    )

    if request.method == "POST" and form.is_valid():
        try:
            item = update_pantry_item(
                user=request.user,
                item_id=item.pk,
                data=form.cleaned_data,
            )
        except IntegrityError:
            form.add_error("name", "This item is already in your pantry.")
        else:
            messages.success(request, f"{item.name} updated.")
            return redirect("household:pantry")

    return render(
        request,
        "household/pantry_edit.html",
        {
            "form": form,
            "item": item,
        },
    )


@login_required
@require_POST
def remove_pantry_item(request, item_id):
    try:
        item = delete_pantry_item(user=request.user, item_id=item_id)
    except PantryItem.DoesNotExist as exc:
        raise Http404 from exc

    messages.success(request, f"{item.name} removed from pantry.")
    return redirect("household:pantry")


@login_required
@require_POST
def pantry_to_shopping(request, item_id):
    try:
        result = add_pantry_item_to_shopping(user=request.user, item_id=item_id)
    except PantryItem.DoesNotExist as exc:
        raise Http404 from exc

    if result.created:
        messages.success(request, f"{result.item.name} added to Shopping.")
    else:
        messages.success(
            request,
            f"{result.item.name} was already on Shopping — quantity updated.",
        )
    return redirect("household:pantry")


@login_required
def routines(request):
    form = RoutineForm(request.POST or None, initial={"due_on": timezone.localdate()})

    if request.method == "POST" and form.is_valid():
        routine = create_routine(user=request.user, data=form.cleaned_data)
        messages.success(request, f"{routine.title} added to your home rhythm.")
        return redirect("household:routines")

    return render(
        request,
        "household/routines.html",
        {
            "form": form,
            "snapshot": routine_snapshot(user=request.user),
            "today": timezone.localdate(),
        },
    )


@login_required
def edit_routine(request, routine_id):
    try:
        routine = Routine.objects.get(pk=routine_id, user=request.user)
    except Routine.DoesNotExist as exc:
        raise Http404 from exc

    form = RoutineForm(
        request.POST or None,
        initial={
            "title": routine.title,
            "room": routine.room,
            "frequency": routine.frequency,
            "due_on": routine.due_on,
            "expected_duration_minutes": routine.expected_duration_minutes,
        },
    )

    if request.method == "POST" and form.is_valid():
        routine = update_routine(
            user=request.user,
            routine_id=routine.pk,
            data=form.cleaned_data,
        )
        messages.success(request, f"{routine.title} updated.")
        return redirect("household:routines")

    return render(
        request,
        "household/routine_edit.html",
        {
            "form": form,
            "routine": routine,
        },
    )


def _routine_action_result(request, routine_id, *, outcome):
    form = RoutineActionForm(request.POST)
    if not form.is_valid():
        raise Http404

    try:
        if outcome == "complete":
            routine = complete_routine(
                user=request.user,
                routine_id=routine_id,
                expected_scheduled_for=form.cleaned_data["scheduled_for"],
                today=timezone.localdate(),
            )
            message = (
                f"{routine.title} completed."
                if not routine.active
                else f"{routine.title} completed. Next due {routine.due_on:%b %d}."
            )
        else:
            routine = skip_routine(
                user=request.user,
                routine_id=routine_id,
                expected_scheduled_for=form.cleaned_data["scheduled_for"],
                today=timezone.localdate(),
            )
            message = (
                f"{routine.title} skipped."
                if not routine.active
                else f"{routine.title} skipped. Next due {routine.due_on:%b %d}."
            )
    except Routine.DoesNotExist as exc:
        raise Http404 from exc
    except StaleRoutineAction:
        messages.info(request, "Routine was already updated. Showing the latest schedule.")
    else:
        messages.success(request, message)

    return redirect("household:routines")


@login_required
@require_POST
def complete_routine_view(request, routine_id):
    return _routine_action_result(request, routine_id, outcome="complete")


@login_required
@require_POST
def skip_routine_view(request, routine_id):
    return _routine_action_result(request, routine_id, outcome="skip")


@login_required
@require_POST
def postpone_routine_view(request, routine_id):
    try:
        routine = Routine.objects.get(pk=routine_id, user=request.user, active=True)
    except Routine.DoesNotExist as exc:
        raise Http404 from exc

    form = RoutinePostponeForm(request.POST, routine=routine)
    if not form.is_valid():
        messages.error(request, "Choose a valid later date to postpone this routine.")
        return redirect("household:routines")

    try:
        routine = postpone_routine(
            user=request.user,
            routine_id=routine.pk,
            expected_scheduled_for=form.cleaned_data["scheduled_for"],
            expected_effective_due_on=form.cleaned_data["expected_effective_due_on"],
            postponed_to=form.cleaned_data["postponed_to"],
        )
    except StaleRoutineAction:
        messages.info(request, "Routine was already updated. Showing the latest schedule.")
    except ValueError:
        messages.error(request, "Choose a date after the current due date.")
    else:
        messages.success(
            request,
            f"{routine.title} postponed to {routine.postponed_until:%b %d}.",
        )

    return redirect("household:routines")


@login_required
@require_POST
def archive_routine_view(request, routine_id):
    try:
        routine = archive_routine(user=request.user, routine_id=routine_id)
    except Routine.DoesNotExist as exc:
        raise Http404 from exc

    messages.success(request, f"{routine.title} archived.")
    return redirect("household:routines")
