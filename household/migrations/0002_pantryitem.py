from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("household", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PantryItem",
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
                    "quantity_mode",
                    models.CharField(
                        choices=[
                            ("approximate", "Approximate"),
                            ("precise", "Precise"),
                        ],
                        default="approximate",
                        max_length=12,
                    ),
                ),
                (
                    "approximate_level",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("full", "Full"),
                            ("half", "Half"),
                            ("low", "Low"),
                        ],
                        default="full",
                        max_length=8,
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=9,
                        null=True,
                    ),
                ),
                (
                    "unit",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("item", "item"),
                            ("g", "g"),
                            ("kg", "kg"),
                            ("ml", "ml"),
                            ("l", "l"),
                        ],
                        default="",
                        max_length=8,
                    ),
                ),
                (
                    "low_stock_threshold",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=9,
                        null=True,
                    ),
                ),
                ("expires_on", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="pantry_items",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["name", "pk"],
                "indexes": [
                    models.Index(
                        fields=["user", "expires_on"],
                        name="pantry_expiry_lookup",
                    )
                ],
                "constraints": [
                    models.CheckConstraint(
                        condition=models.Q(("normalized_name", ""), _negated=True),
                        name="pantry_name_not_empty",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("amount__isnull", True),
                            ("amount__gte", 0),
                            _connector="OR",
                        ),
                        name="pantry_amount_non_negative",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            ("low_stock_threshold__isnull", True),
                            ("low_stock_threshold__gte", 0),
                            _connector="OR",
                        ),
                        name="pantry_threshold_non_negative",
                    ),
                    models.CheckConstraint(
                        condition=models.Q(
                            models.Q(
                                ("amount__isnull", True),
                                ("approximate_level__in", ["full", "half", "low"]),
                                ("low_stock_threshold__isnull", True),
                                ("quantity_mode", "approximate"),
                                ("unit", ""),
                            ),
                            models.Q(
                                models.Q(
                                    ("amount__isnull", False),
                                    ("approximate_level", ""),
                                    ("quantity_mode", "precise"),
                                ),
                                models.Q(("unit", ""), _negated=True),
                            ),
                            _connector="OR",
                        ),
                        name="pantry_quantity_mode_consistent",
                    ),
                    models.UniqueConstraint(
                        fields=("user", "normalized_name"),
                        name="unique_pantry_name_per_user",
                    ),
                ],
            },
        ),
    ]
