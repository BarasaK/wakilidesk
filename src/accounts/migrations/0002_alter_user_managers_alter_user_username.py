import accounts.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelManagers(
            name="user",
            managers=[
                ("objects", accounts.models.UserManager()),
            ],
        ),
        migrations.AlterField(
            model_name="user",
            name="username",
            field=models.CharField(max_length=254, unique=True),
        ),
    ]
