from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("recipes", "0001_initial"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="recipeingredient",
            name="recipe_ingredient_quantity_consistent",
        ),
        migrations.AddConstraint(
            model_name="recipeingredient",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(amount__isnull=True, unit="")
                    | (
                        models.Q(amount__isnull=False, amount__gt=0)
                        & ~models.Q(unit="")
                    )
                ),
                name="recipe_ingredient_quantity_consistent",
            ),
        ),
    ]
