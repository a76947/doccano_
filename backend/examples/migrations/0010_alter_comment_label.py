

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("examples", "0009_comment_label"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="label",
            field=models.IntegerField(blank=True, db_column="label_id", null=True),
        ),
    ]
