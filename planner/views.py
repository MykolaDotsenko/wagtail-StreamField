import datetime

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ChoreForm, MealPlanEntryForm, PantryItemForm, ShoppingItemForm
from .models import Chore, MealPlanEntry, PantryItem, ShoppingItem

FORM_ACTIONS = {
    "shopping": (ShoppingItemForm, "Shopping item added."),
    "pantry": (PantryItemForm, "Pantry item added."),
    "chore": (ChoreForm, "Chore added."),
    "meal": (MealPlanEntryForm, "Meal plan updated."),
}


@login_required
def dashboard(request):
    forms = {name: form_class(prefix=name) for name, (form_class, _) in FORM_ACTIONS.items()}

    if request.method == "POST":
        action = request.POST.get("action")
        config = FORM_ACTIONS.get(action)
        if config:
            form_class, success_message = config
            form = form_class(request.POST, prefix=action)
            forms[action] = form
            if form.is_valid():
                instance = form.save(commit=False)
                instance.user = request.user
                if isinstance(instance, MealPlanEntry):
                    MealPlanEntry.objects.update_or_create(
                        user=request.user,
                        date=instance.date,
                        meal_type=instance.meal_type,
                        defaults={
                            "recipe": instance.recipe,
                            "custom_meal": instance.custom_meal.strip(),
                        },
                    )
                else:
                    instance.save()
                messages.success(request, success_message)
                return redirect("planner:dashboard")

    today = datetime.date.today()
    week_days = [today + datetime.timedelta(days=offset) for offset in range(7)]
    meals = list(
        MealPlanEntry.objects.filter(
            user=request.user, date__range=(week_days[0], week_days[-1])
        )
        .select_related("recipe")
        .order_by("date", "meal_type")
    )
    week = [
        {"date": day, "entries": [entry for entry in meals if entry.date == day]}
        for day in week_days
    ]

    shopping = ShoppingItem.objects.filter(user=request.user)
    pantry = PantryItem.objects.filter(user=request.user)
    chores = Chore.objects.filter(user=request.user)
    attention_cutoff = today + datetime.timedelta(days=3)

    return render(
        request,
        "planner/dashboard.html",
        {
            "forms": forms,
            "shopping_items": shopping,
            "pantry_items": pantry,
            "chores": chores,
            "week": week,
            "stats": {
                "shopping_open": shopping.filter(is_done=False).count(),
                "chores_open": chores.filter(is_done=False).count(),
                "pantry_attention": pantry.filter(
                    Q(low_stock=True) | Q(expires_on__lte=attention_cutoff)
                )
                .distinct()
                .count(),
                "meals_planned": len(meals),
            },
        },
    )


@require_POST
@login_required
def toggle_item(request, kind, pk):
    model = {"shopping": ShoppingItem, "chore": Chore}.get(kind)
    if model is None:
        messages.error(request, "Unsupported item type.")
        return redirect("planner:dashboard")
    item = get_object_or_404(model, pk=pk, user=request.user)
    if isinstance(item, Chore):
        if item.is_done:
            item.is_done = False
            item.save(update_fields=["is_done"])
        else:
            item.complete()
            item.save(update_fields=["is_done", "due_on"])
    else:
        item.is_done = not item.is_done
        item.save(update_fields=["is_done"])
    return redirect("planner:dashboard")


@require_POST
@login_required
def delete_item(request, kind, pk):
    model = {
        "shopping": ShoppingItem,
        "pantry": PantryItem,
        "chore": Chore,
        "meal": MealPlanEntry,
    }.get(kind)
    if model is None:
        messages.error(request, "Unsupported item type.")
        return redirect("planner:dashboard")
    item = get_object_or_404(model, pk=pk, user=request.user)
    item.delete()
    messages.success(request, "Item removed.")
    return redirect("planner:dashboard")


def signup(request):
    if request.user.is_authenticated:
        return redirect("planner:dashboard")
    form = UserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your household space is ready.")
        return redirect("planner:dashboard")
    return render(request, "registration/signup.html", {"form": form})
