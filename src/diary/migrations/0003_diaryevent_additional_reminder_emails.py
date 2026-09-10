from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("diary", "0002_default_diary_permissions"),
    ]

    operations = [
        migrations.AddField(
            model_name="diaryevent",
            name="additional_reminder_emails",
            field=models.TextField(blank=True),
        ),
    ]
