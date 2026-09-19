import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("household", "0003_routine_routineevent"),
        ("recipes", "0002_recipeingredient_quantity_constraint_null_safe"),
    ]

    operations = [
        migrations.AddField(
            model_name="shoppingitem",
            name="ingredient",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="shopping_demands",
                to="recipes.ingredient",
            ),
        ),
        migrations.AddField(
            model_name="pantryitem",
            name="ingredient",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="pantry_entries",
                to="recipes.ingredient",
            ),
        ),
        migrations.AddConstraint(
            model_name="shoppingitem",
            constraint=models.UniqueConstraint(
                condition=models.Q(
                    ingredient__isnull=False,
                    status="open",
                    deleted_at__isnull=True,
                ),
                fields=("user", "ingredient"),
                name="unique_open_shopping_ingredient_per_user",
            ),
        ),
        migrations.AddConstraint(
            model_name="pantryitem",
            constraint=models.UniqueConstraint(
                condition=models.Q(ingredient__isnull=False),
                fields=("user", "ingredient"),
                name="unique_pantry_ingredient_per_user",
            ),
        ),
        migrations.AddIndex(
            model_name="shoppingitem",
            index=models.Index(
                fields=["user", "ingredient"],
                name="shopping_ingredient_lookup",
            ),
        ),
        migrations.AddIndex(
            model_name="pantryitem",
            index=models.Index(
                fields=["user", "ingredient"],
                name="pantry_ingredient_lookup",
            ),
        ),
    ]
