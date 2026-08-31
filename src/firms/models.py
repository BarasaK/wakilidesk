from __future__ import annotations

import uuid

from django.conf import settings
from django.core.signing import TimestampSigner
from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Firm(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    logo = models.ImageField(upload_to="firm-logos/", blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, default="Nairobi")
    country = models.CharField(max_length=100, default="Kenya")
    timezone = models.CharField(max_length=64, default="Africa/Nairobi")
    currency = models.CharField(max_length=3, default="KES")
    file_number_pattern = models.CharField(
        max_length=100, default="{PRACTICE_AREA}/{YEAR}/{SEQUENCE}"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=["slug"], name="firms_firm_slug_456c64_idx"),
            models.Index(fields=["is_active"], name="firms_firm_is_acti_1ab640_idx"),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.display_name or self.name)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.display_name


class Permission(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    codename = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=150)
    module = models.CharField(max_length=80)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ("module", "codename")

    def __str__(self) -> str:
        return self.codename


class Role(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="roles")
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_system_default = models.BooleanField(default=False)
    permissions = models.ManyToManyField(Permission, blank=True, related_name="roles")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["firm", "name"], name="unique_role_per_firm")
        ]
        indexes = [
            models.Index(fields=["firm", "name"], name="firms_role_firm_id_53be3d_idx")
        ]

    def __str__(self) -> str:
        return f"{self.firm}: {self.name}"


class FirmMembership(TimeStampedModel):
    class Status(models.TextChoices):
        INVITED = "INVITED", "Invited"
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="memberships")
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="memberships")
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    joined_at = models.DateTimeField(default=timezone.now)
    last_active_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "firm"], name="unique_membership_per_user_firm"
            )
        ]
        indexes = [
            models.Index(fields=["firm", "status"], name="firms_firmm_firm_id_c31c37_idx"),
            models.Index(fields=["user", "status"], name="firms_firmm_user_id_b876ee_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.user} in {self.firm}"


class UserInvitation(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        ACCEPTED = "ACCEPTED", "Accepted"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey(Firm, on_delete=models.CASCADE, related_name="invitations")
    email = models.EmailField()
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="invitations")
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="sent_invitations",
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="accepted_invitations",
        null=True,
        blank=True,
    )
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["firm", "status"], name="firms_useri_firm_id_606ccf_idx"),
            models.Index(fields=["email", "status"], name="firms_useri_email_3a33d0_idx"),
        ]

    @property
    def token(self) -> str:
        signer = TimestampSigner()
        return signer.sign(str(self.id))

    def __str__(self) -> str:
        return f"{self.email} invited to {self.firm}"
