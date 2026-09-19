from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import ChoreForm, PantryItemForm, ShoppingItemForm
from .models import Chore, PantryItem, ShoppingItem


@login_required
def dashboard(request):
    shopping_form = ShoppingItemForm(prefix="shopping")
    pantry_form = PantryItemForm(prefix="pantry")
    chore_form = ChoreForm(prefix="chore")

    if request.method == "POST":
        form_type = request.POST.get("form_type")
        if form_type == "shopping":
            shopping_form = ShoppingItemForm(request.POST, prefix="shopping")
            form = shopping_form
        elif form_type == "pantry":
            pantry_form = PantryItemForm(request.POST, prefix="pantry")
            form = pantry_form
        elif form_type == "chore":
            chore_form = ChoreForm(request.POST, prefix="chore")
            form = chore_form
        else:
            raise Http404

        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, "Added to your home plan.")
            return redirect("household:dashboard")

    shopping = request.user.shopping_items.all()
    pantry = request.user.pantry_items.all()
    chores = request.user.chores.all()
    today = timezone.localdate()

    context = {
        "shopping_items": shopping,
        "shopping_open": shopping.filter(is_done=False).count(),
        "pantry_items": pantry,
        "low_stock_count": sum(item.is_low_stock for item in pantry),
        "expiring_count": sum(item.expires_soon for item in pantry),
        "chores": chores,
        "chores_due": chores.filter(is_done=False, due_on__lte=today).count(),
        "shopping_form": shopping_form,
        "pantry_form": pantry_form,
        "chore_form": chore_form,
        "today": today,
    }
    return render(request, "household/dashboard.html", context)


@login_required
@require_POST
def toggle_shopping(request, pk):
    item = request.user.shopping_items.filter(pk=pk).first()
    if not item:
        raise Http404
    item.is_done = not item.is_done
    item.save(update_fields=["is_done"])
    return redirect("household:dashboard")


@login_required
@require_POST
def toggle_chore(request, pk):
    chore = request.user.chores.filter(pk=pk).first()
    if not chore:
        raise Http404
    chore.is_done = not chore.is_done
    chore.save(update_fields=["is_done"])
    return redirect("household:dashboard")


@login_required
@require_POST
def delete_item(request, kind, pk):
    model_map = {
        "shopping": ShoppingItem,
        "pantry": PantryItem,
        "chore": Chore,
    }
    model = model_map.get(kind)
    if model is None:
        raise Http404
    obj = model.objects.filter(pk=pk, user=request.user).first()
    if not obj:
        raise Http404
    obj.delete()
    messages.success(request, "Removed.")
    return redirect("household:dashboard")
