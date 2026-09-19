import datetime

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("blog", "0002_domonest_content"),
    ]

    operations = [
        migrations.CreateModel(
            name="Chore",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140)),
                ("room", models.CharField(choices=[("kitchen", "Kitchen"), ("bathroom", "Bathroom"), ("bedroom", "Bedroom"), ("living", "Living room"), ("laundry", "Laundry"), ("whole_home", "Whole home")], default="whole_home", max_length=20)),
                ("frequency", models.CharField(choices=[("once", "One-off"), ("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")], default="weekly", max_length=20)),
                ("due_on", models.DateField(default=datetime.date.today)),
                ("is_done", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chores", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["is_done", "due_on", "room", "title"]},
        ),
        migrations.CreateModel(
            name="PantryItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("quantity", models.CharField(default="1", max_length=40)),
                ("category", models.CharField(choices=[("produce", "Produce"), ("dairy", "Dairy"), ("pantry", "Pantry"), ("frozen", "Frozen"), ("household", "Household"), ("other", "Other")], default="pantry", max_length=20)),
                ("expires_on", models.DateField(blank=True, null=True)),
                ("low_stock", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pantry_items", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-low_stock", "expires_on", "name"]},
        ),
        migrations.CreateModel(
            name="ShoppingItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("quantity", models.CharField(default="1", max_length=40)),
                ("category", models.CharField(choices=[("produce", "Produce"), ("dairy", "Dairy"), ("pantry", "Pantry"), ("frozen", "Frozen"), ("household", "Household"), ("other", "Other")], default="other", max_length=20)),
                ("is_done", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shopping_items", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["is_done", "category", "name"]},
        ),
        migrations.CreateModel(
            name="MealPlanEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(default=datetime.date.today)),
                ("meal_type", models.CharField(choices=[("breakfast", "Breakfast"), ("lunch", "Lunch"), ("dinner", "Dinner")], max_length=20)),
                ("custom_meal", models.CharField(blank=True, max_length=140)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("recipe", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="meal_plan_entries", to="blog.recipepage")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="meal_plan_entries", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["date", "meal_type"]},
        ),
        migrations.AddIndex(model_name="shoppingitem", index=models.Index(fields=["user", "is_done"], name="shop_user_done_idx")),
        migrations.AddIndex(model_name="pantryitem", index=models.Index(fields=["user", "expires_on"], name="pantry_user_exp_idx")),
        migrations.AddIndex(model_name="chore", index=models.Index(fields=["user", "is_done", "due_on"], name="chore_user_due_idx")),
        migrations.AddIndex(model_name="mealplanentry", index=models.Index(fields=["user", "date"], name="meal_user_date_idx")),
        migrations.AddConstraint(
            model_name="mealplanentry",
            constraint=models.UniqueConstraint(
                fields=("user", "date", "meal_type"),
                name="unique_meal_slot_per_user",
            ),
        ),
    ]
