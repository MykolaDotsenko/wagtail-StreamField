from django.contrib import admin

from .models import Chore, MealPlanEntry, PantryItem, ShoppingItem

admin.site.register([ShoppingItem, PantryItem, Chore, MealPlanEntry])
