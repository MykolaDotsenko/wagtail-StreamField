import django.db.models.deletion
import modelcluster.contrib.taggit
import modelcluster.fields
import recipes.blocks
import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("taggit", "0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx"),
        ("wagtailcore", "0094_alter_page_locale"),
        ("wagtailimages", "0027_image_description"),
    ]

    operations = [
        migrations.CreateModel(
            name="Ingredient",
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
                (
                    "normalized_name",
                    models.CharField(editable=False, max_length=255, unique=True),
                ),
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
                            ("other", "Other"),
                        ],
                        default="other",
                        max_length=20,
                    ),
                ),
            ],
            options={
                "ordering": ["name", "pk"],
                "constraints": [
                    models.CheckConstraint(
                        condition=~models.Q(normalized_name=""),
                        name="ingredient_name_not_empty",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="RecipeIndexPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.page",
                    ),
                ),
                (
                    "intro",
                    wagtail.fields.RichTextField(
                        blank=True,
                        features=["bold", "italic", "link"],
                        help_text="A short introduction to the recipe collection.",
                    ),
                ),
            ],
            options={
                "verbose_name": "Recipe library",
            },
            bases=("wagtailcore.page",),
        ),
        migrations.CreateModel(
            name="RecipePage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.page",
                    ),
                ),
                (
                    "intro",
                    models.CharField(
                        help_text="One concise promise: what should the cook expect from this recipe?",
                        max_length=280,
                    ),
                ),
                (
                    "hero_alt_text",
                    models.CharField(
                        blank=True,
                        help_text="Context-specific alt text. Leave blank only when the image is decorative.",
                        max_length=180,
                    ),
                ),
                (
                    "prep_minutes",
                    models.PositiveSmallIntegerField(
                        help_text="Active preparation time in minutes.",
                    ),
                ),
                (
                    "cook_minutes",
                    models.PositiveSmallIntegerField(
                        default=0,
                        help_text="Cooking/baking time in minutes. Use 0 for no-cook recipes.",
                    ),
                ),
                ("servings", models.PositiveSmallIntegerField(default=2)),
                (
                    "difficulty",
                    models.CharField(
                        choices=[
                            ("easy", "Easy"),
                            ("medium", "Medium"),
                            ("advanced", "Advanced"),
                        ],
                        default="easy",
                        max_length=12,
                    ),
                ),
                (
                    "instructions",
                    wagtail.fields.StreamField(
                        recipes.blocks.RecipeBodyBlock(),
                        blank=True,
                        help_text="Keep ingredient quantities in the structured ingredient rows below.",
                        use_json_field=True,
                    ),
                ),
                (
                    "hero_image",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="+",
                        to="wagtailimages.image",
                    ),
                ),
            ],
            options={
                "verbose_name": "Recipe",
                "verbose_name_plural": "Recipes",
            },
            bases=("wagtailcore.page",),
        ),
        migrations.CreateModel(
            name="RecipeIngredient",
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
                (
                    "sort_order",
                    models.IntegerField(blank=True, editable=False, null=True),
                ),
                (
                    "amount",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        max_digits=8,
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
                            ("tsp", "tsp"),
                            ("tbsp", "tbsp"),
                            ("cup", "cup"),
                        ],
                        default="",
                        max_length=8,
                    ),
                ),
                (
                    "note",
                    models.CharField(
                        blank=True,
                        help_text="Optional preparation detail, for example “finely chopped” or “divided”.",
                        max_length=120,
                    ),
                ),
                ("optional", models.BooleanField(default=False)),
                (
                    "ingredient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="recipe_lines",
                        to="recipes.ingredient",
                    ),
                ),
                (
                    "page",
                    modelcluster.fields.ParentalKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ingredient_lines",
                        to="recipes.recipepage",
                    ),
                ),
            ],
            options={
                "ordering": ["sort_order", "pk"],
                "constraints": [
                    models.CheckConstraint(
                        condition=(
                            models.Q(amount__isnull=True, unit="")
                            | (
                                models.Q(amount__isnull=False, amount__gt=0)
                                & ~models.Q(unit="")
                            )
                        ),
                        name="recipe_ingredient_quantity_consistent",
                    ),
                    models.UniqueConstraint(
                        fields=("page", "ingredient"),
                        name="unique_ingredient_per_recipe",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="RecipePageTag",
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
                (
                    "content_object",
                    modelcluster.fields.ParentalKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tagged_items",
                        to="recipes.recipepage",
                    ),
                ),
                (
                    "tag",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="%(app_label)s_%(class)s_items",
                        to="taggit.tag",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="recipepage",
            name="tags",
            field=modelcluster.contrib.taggit.ClusterTaggableManager(
                blank=True,
                help_text="A comma-separated list of tags.",
                through="recipes.RecipePageTag",
                to="taggit.Tag",
                verbose_name="Tags",
            ),
        ),
    ]
