import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("firms", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="UserInvitation",
            fields=[
                ("created_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("email", models.EmailField(max_length=254)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("ACCEPTED", "Accepted"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("accepted_at", models.DateTimeField(blank=True, null=True)),
                (
                    "accepted_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="accepted_invitations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "firm",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="invitations",
                        to="firms.firm",
                    ),
                ),
                (
                    "invited_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="sent_invitations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="invitations",
                        to="firms.role",
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="userinvitation",
            index=models.Index(fields=["firm", "status"], name="firms_useri_firm_id_606ccf_idx"),
        ),
        migrations.AddIndex(
            model_name="userinvitation",
            index=models.Index(fields=["email", "status"], name="firms_useri_email_3a33d0_idx"),
        ),
    ]
