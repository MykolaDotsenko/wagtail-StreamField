import blog.blocks
import django.db.models.deletion
import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0001_initial"),
        ("wagtailimages", "0027_image_description"),
    ]

    operations = [
        migrations.CreateModel(
            name="HouseholdTopic",
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
                ("name", models.CharField(max_length=80, unique=True)),
                ("slug", models.SlugField(unique=True)),
                ("icon", models.CharField(default="✨", max_length=8)),
                ("description", models.CharField(blank=True, max_length=180)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.AddField(
            model_name="blogpage",
            name="featured",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="blogpage",
            name="reading_minutes",
            field=models.PositiveSmallIntegerField(default=5),
        ),
        migrations.AddField(
            model_name="blogpage",
            name="topic",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="guides",
                to="blog.householdtopic",
            ),
        ),
        migrations.AlterField(
            model_name="blogpage",
            name="body",
            field=wagtail.fields.StreamField(
                blog.blocks.GuideBodyBlock(), blank=True, use_json_field=True
            ),
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
                ("intro", wagtail.fields.RichTextField(blank=True)),
            ],
            options={"abstract": False},
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
                ("summary", models.CharField(max_length=260)),
                ("prep_minutes", models.PositiveSmallIntegerField(default=10)),
                ("cook_minutes", models.PositiveSmallIntegerField(default=20)),
                ("servings", models.PositiveSmallIntegerField(default=4)),
                (
                    "difficulty",
                    models.CharField(
                        choices=[
                            ("easy", "Easy"),
                            ("medium", "Medium"),
                            ("weekend", "Weekend project"),
                        ],
                        default="easy",
                        max_length=20,
                    ),
                ),
                (
                    "meal_type",
                    models.CharField(
                        choices=[
                            ("breakfast", "Breakfast"),
                            ("lunch", "Lunch"),
                            ("dinner", "Dinner"),
                            ("snack", "Snack"),
                            ("baking", "Baking"),
                        ],
                        default="dinner",
                        max_length=20,
                    ),
                ),
                ("featured", models.BooleanField(default=False)),
                (
                    "ingredients",
                    wagtail.fields.StreamField(
                        blog.blocks.RecipeIngredientsBlock(),
                        blank=True,
                        use_json_field=True,
                    ),
                ),
                (
                    "steps",
                    wagtail.fields.StreamField(
                        blog.blocks.RecipeStepsBlock(),
                        blank=True,
                        use_json_field=True,
                    ),
                ),
                (
                    "body",
                    wagtail.fields.StreamField(
                        blog.blocks.RecipeBodyBlock(),
                        blank=True,
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
            options={"abstract": False},
            bases=("wagtailcore.page",),
        ),
    ]
