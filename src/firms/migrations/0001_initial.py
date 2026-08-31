import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Firm",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
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
                ("name", models.CharField(max_length=255)),
                ("display_name", models.CharField(max_length=255)),
                ("slug", models.SlugField(max_length=255, unique=True)),
                (
                    "logo",
                    models.ImageField(blank=True, upload_to="firm-logos/"),
                ),
                ("email", models.EmailField(max_length=254)),
                ("phone", models.CharField(blank=True, max_length=50)),
                ("address", models.TextField(blank=True)),
                ("city", models.CharField(default="Nairobi", max_length=100)),
                ("country", models.CharField(default="Kenya", max_length=100)),
                (
                    "timezone",
                    models.CharField(default="Africa/Nairobi", max_length=64),
                ),
                ("currency", models.CharField(default="KES", max_length=3)),
                (
                    "file_number_pattern",
                    models.CharField(
                        default="{PRACTICE_AREA}/{YEAR}/{SEQUENCE}",
                        max_length=100,
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name="Permission",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
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
                ("codename", models.CharField(max_length=100, unique=True)),
                ("name", models.CharField(max_length=150)),
                ("module", models.CharField(max_length=80)),
                ("description", models.TextField(blank=True)),
            ],
            options={
                "ordering": ("module", "codename"),
            },
        ),
        migrations.CreateModel(
            name="Role",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
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
                ("name", models.CharField(max_length=100)),
                ("description", models.TextField(blank=True)),
                ("is_system_default", models.BooleanField(default=False)),
                (
                    "firm",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="roles",
                        to="firms.firm",
                    ),
                ),
                (
                    "permissions",
                    models.ManyToManyField(
                        blank=True, related_name="roles", to="firms.permission"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="FirmMembership",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
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
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("INVITED", "Invited"),
                            ("ACTIVE", "Active"),
                            ("SUSPENDED", "Suspended"),
                        ],
                        default="ACTIVE",
                        max_length=20,
                    ),
                ),
                (
                    "joined_at",
                    models.DateTimeField(default=django.utils.timezone.now),
                ),
                ("last_active_at", models.DateTimeField(blank=True, null=True)),
                (
                    "firm",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to="firms.firm",
                    ),
                ),
                (
                    "role",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="memberships",
                        to="firms.role",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddIndex(
            model_name="firm",
            index=models.Index(fields=["slug"], name="firms_firm_slug_456c64_idx"),
        ),
        migrations.AddIndex(
            model_name="firm",
            index=models.Index(
                fields=["is_active"], name="firms_firm_is_acti_1ab640_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="role",
            index=models.Index(fields=["firm", "name"], name="firms_role_firm_id_53be3d_idx"),
        ),
        migrations.AddConstraint(
            model_name="role",
            constraint=models.UniqueConstraint(
                fields=("firm", "name"), name="unique_role_per_firm"
            ),
        ),
        migrations.AddIndex(
            model_name="firmmembership",
            index=models.Index(
                fields=["firm", "status"], name="firms_firmm_firm_id_c31c37_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="firmmembership",
            index=models.Index(
                fields=["user", "status"], name="firms_firmm_user_id_b876ee_idx"
            ),
        ),
        migrations.AddConstraint(
            model_name="firmmembership",
            constraint=models.UniqueConstraint(
                fields=("user", "firm"), name="unique_membership_per_user_firm"
            ),
        ),
    ]
