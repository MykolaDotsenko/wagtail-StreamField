import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("household", "0004_canonical_ingredient_links"),
        ("recipes", "0002_recipeingredient_quantity_constraint_null_safe"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="MealPlanEntry",
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
                ("date", models.DateField()),
                (
                    "name",
                    models.CharField(
                        help_text=(
                            "Dinner name snapshot; preserved even if a linked recipe is later removed."
                        ),
                        max_length=160,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "recipe",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="meal_plan_entries",
                        to="recipes.recipepage",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="meal_plan_entries",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["date", "pk"],
                "constraints": [
                    models.CheckConstraint(
                        condition=~models.Q(name=""),
                        name="meal_plan_name_not_empty",
                    ),
                    models.UniqueConstraint(
                        fields=("user", "date"),
                        name="unique_dinner_per_user_date",
                    ),
                ],
            },
        ),
    ]
