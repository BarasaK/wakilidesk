import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("firms", "0004_client_matter_trash_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="firm",
            name="app_font_family",
            field=models.CharField(
                choices=[
                    ("SYSTEM", "System default"),
                    ("ARIAL", "Arial"),
                    ("GEORGIA", "Georgia"),
                    ("VERDANA", "Verdana"),
                    ("TAHOMA", "Tahoma"),
                ],
                default="SYSTEM",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="firm",
            name="app_font_size",
            field=models.PositiveSmallIntegerField(
                default=16,
                validators=[
                    django.core.validators.MinValueValidator(14),
                    django.core.validators.MaxValueValidator(18),
                ],
            ),
        ),
    ]
