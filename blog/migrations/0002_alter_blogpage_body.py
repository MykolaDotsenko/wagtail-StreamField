import wagtail.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("blog", "0001_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name="blogpage",
                    name="body",
                    field=wagtail.fields.StreamField(
                        [
                            ("heading", 0),
                            ("paragraph", 1),
                            ("image", 2),
                            ("quote", 3),
                            ("embed", 4),
                        ],
                        block_lookup={
                            0: (
                                "wagtail.blocks.CharBlock",
                                (),
                                {
                                    "form_classname": "full title",
                                    "template": "blog/streamfield/blocks/heading_block.html",
                                },
                            ),
                            1: ("wagtail.blocks.RichTextBlock", (), {}),
                            2: (
                                "wagtail.images.blocks.ImageChooserBlock",
                                (),
                                {"template": "blog/streamfield/blocks/image_block.html"},
                            ),
                            3: ("wagtail.blocks.BlockQuoteBlock", (), {}),
                            4: ("wagtail.embeds.blocks.EmbedBlock", (), {}),
                        },
                    ),
                )
            ],
        ),
    ]
