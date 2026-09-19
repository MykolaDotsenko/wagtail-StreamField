# Generated for DomoNest.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Chore",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=140)),
                ("room", models.CharField(choices=[("kitchen", "Kitchen"), ("bathroom", "Bathroom"), ("bedroom", "Bedroom"), ("living", "Living room"), ("whole-home", "Whole home")], default="whole-home", max_length=20)),
                ("frequency", models.CharField(choices=[("once", "One time"), ("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")], default="weekly", max_length=12)),
                ("due_on", models.DateField(default=django.utils.timezone.localdate)),
                ("is_done", models.BooleanField(default=False)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chores", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["is_done", "due_on", "room", "title"]},
        ),
        migrations.CreateModel(
            name="PantryItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("quantity", models.DecimalField(decimal_places=2, max_digits=8)),
                ("unit", models.CharField(choices=[("pcs", "pcs"), ("g", "g"), ("kg", "kg"), ("ml", "ml"), ("l", "l")], default="pcs", max_length=8)),
                ("low_stock_threshold", models.DecimalField(decimal_places=2, default=1, max_digits=8)),
                ("expires_on", models.DateField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="pantry_items", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["expires_on", "name"]},
        ),
        migrations.CreateModel(
            name="ShoppingItem",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120)),
                ("quantity", models.PositiveSmallIntegerField(default=1)),
                ("category", models.CharField(choices=[("produce", "Fruit & vegetables"), ("dairy", "Dairy"), ("pantry", "Pantry"), ("household", "Household"), ("other", "Other")], default="other", max_length=20)),
                ("is_done", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="shopping_items", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["is_done", "category", "-created_at"]},
        ),
    ]
