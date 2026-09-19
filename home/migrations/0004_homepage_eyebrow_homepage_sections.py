from django.db import migrations, models
import wagtail.blocks
import wagtail.fields


class Migration(migrations.Migration):
    dependencies = [("home", "0003_homepage_body")]

    operations = [
        migrations.AddField(
            model_name="homepage",
            name="eyebrow",
            field=models.CharField(blank=True, default="A calmer way to run your home", max_length=80),
        ),
        migrations.AddField(
            model_name="homepage",
            name="sections",
            field=wagtail.fields.StreamField(
                [
                    ("hero", wagtail.blocks.StructBlock([
                        ("title", wagtail.blocks.CharBlock(max_length=120)),
                        ("text", wagtail.blocks.TextBlock(max_length=320)),
                        ("primary_label", wagtail.blocks.CharBlock(default="Open dashboard", max_length=40)),
                        ("primary_url", wagtail.blocks.CharBlock(default="/app/", max_length=160)),
                        ("secondary_label", wagtail.blocks.CharBlock(default="Explore features", max_length=40)),
                        ("secondary_url", wagtail.blocks.CharBlock(default="#features", max_length=160)),
                    ])),
                    ("features", wagtail.blocks.StructBlock([
                        ("heading", wagtail.blocks.CharBlock(max_length=100)),
                        ("intro", wagtail.blocks.TextBlock(max_length=260, required=False)),
                        ("items", wagtail.blocks.ListBlock(wagtail.blocks.StructBlock([
                            ("icon", wagtail.blocks.CharBlock(help_text="Emoji or short symbol", max_length=4)),
                            ("title", wagtail.blocks.CharBlock(max_length=80)),
                            ("text", wagtail.blocks.TextBlock(max_length=220)),
                        ]), max_num=6, min_num=2)),
                    ])),
                    ("callout", wagtail.blocks.StructBlock([
                        ("kicker", wagtail.blocks.CharBlock(max_length=60, required=False)),
                        ("heading", wagtail.blocks.CharBlock(max_length=100)),
                        ("text", wagtail.blocks.TextBlock(max_length=260)),
                        ("button_label", wagtail.blocks.CharBlock(max_length=40, required=False)),
                        ("button_url", wagtail.blocks.CharBlock(max_length=160, required=False)),
                    ])),
                    ("rich_text", wagtail.blocks.RichTextBlock(features=["h2", "h3", "bold", "italic", "ol", "ul", "link"])),
                ],
                blank=True,
                use_json_field=True,
            ),
        ),
    ]
