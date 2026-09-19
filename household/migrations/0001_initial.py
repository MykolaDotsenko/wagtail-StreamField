from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ShoppingItem",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("normalized_name", models.CharField(editable=False, max_length=255)),
                ("quantity", models.PositiveIntegerField(default=1)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("produce", "Fruit & vegetables"),
                            ("dairy", "Dairy & eggs"),
                            ("bakery", "Bakery"),
                            ("meat_fish", "Meat & fish"),
                            ("pantry", "Pantry"),
                            ("frozen", "Frozen"),
                            ("household", "Household"),
                            ("other", "Other"),
                        ],
                        default="other",
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[("open", "Open"), ("completed", "Completed")],
                        default="open",
                        max_length=12,
                    ),
                ),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("deleted_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shopping_items",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["category", "created_at", "pk"],
                "indexes": [
                    models.Index(
                        fields=["user", "status", "deleted_at", "category"],
                        name="shopping_active_lookup",
                    )
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("quantity__gte", 1)),
                        name="shopping_quantity_at_least_one",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(("normalized_name", ""), _negated=True),
                        name="shopping_name_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(
                                ("completed_at__isnull", True),
                                ("status", "open"),
                            ),
                            models.Q(
                                ("completed_at__isnull", False),
                                ("status", "completed"),
                            ),
                            _connector="OR",
                        ),
                        name="shopping_completion_state_consistent",
                    ),
                    models.UniqueConstraint(
                        condition=models.Q(
                            ("deleted_at__isnull", True),
                            ("status", "open"),
                        ),
                        fields=("user", "normalized_name"),
                        name="unique_open_shopping_name_per_user",
                    ),
                ],
            },
        ),
    ]
