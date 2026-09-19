import content.blocks
import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0002_alter_blogpage_body"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="blogindexpage",
            options={"verbose_name": "Guide library"},
        ),
        migrations.AlterModelOptions(
            name="blogpage",
            options={
                "verbose_name": "Home guide",
                "verbose_name_plural": "Home guides",
            },
        ),
        migrations.AlterModelOptions(
            name="blogtagindexpage",
            options={"verbose_name": "Guide topic index"},
        ),
        migrations.AlterField(
            model_name="blogindexpage",
            name="intro",
            field=wagtail.fields.RichTextField(
                blank=True,
                features=["bold", "italic", "link", "ul", "ol"],
                help_text="Briefly explain what readers can learn from this guide library.",
            ),
        ),
        migrations.AddField(
            model_name="blogpage",
            name="guide_type",
            field=models.CharField(
                choices=[
                    ("general", "General"),
                    ("cleaning", "Cleaning"),
                    ("food_storage", "Food storage"),
                    ("organization", "Organization"),
                    ("maintenance", "Home maintenance"),
                    ("seasonal", "Seasonal"),
                ],
                default="general",
                help_text="Used for editorial context and Discover filtering.",
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name="blogpage",
            name="body",
            field=wagtail.fields.StreamField(
                content.blocks.GuideBodyBlock(),
                help_text=(
                    "Build the guide from structured blocks. "
                    "Prefer actionable blocks over free-form layout."
                ),
                use_json_field=True,
            ),
        ),
        migrations.AlterField(
            model_name="blogpage",
            name="date",
            field=models.DateField(
                help_text="Use the editorial date readers should associate with this guide.",
                verbose_name="Published date",
            ),
        ),
        migrations.AlterField(
            model_name="blogpage",
            name="intro",
            field=models.CharField(
                help_text="One concise promise: what useful outcome will the reader get?",
                max_length=250,
            ),
        ),
    ]
