import home.blocks
import wagtail.fields
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("home", "0003_homepage_body")]

    operations = [
        migrations.AddField(
            model_name="homepage",
            name="content",
            field=wagtail.fields.StreamField(
                home.blocks.HomeStreamBlock(), blank=True, use_json_field=True
            ),
        ),
    ]
