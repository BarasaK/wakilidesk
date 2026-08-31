from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class PracticeArea(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="practice_areas")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["firm", "name"], name="unique_practice_area_name_per_firm"),
            models.UniqueConstraint(fields=["firm", "code"], name="unique_practice_area_code_per_firm"),
        ]
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Matter(models.Model):
    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        ACTIVE = "ACTIVE", "Active"
        ON_HOLD = "ON_HOLD", "On hold"
        CLOSED = "CLOSED", "Closed"
        ARCHIVED = "ARCHIVED", "Archived"

    class ConfidentialityLevel(models.TextChoices):
        STANDARD = "STANDARD", "Standard"
        RESTRICTED = "RESTRICTED", "Restricted"
        PARTNER_ONLY = "PARTNER_ONLY", "Partner only"
        CUSTOM = "CUSTOM", "Custom"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="matters")
    matter_number = models.CharField(max_length=80)
    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="matters")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    practice_area = models.ForeignKey(
        PracticeArea,
        on_delete=models.PROTECT,
        related_name="matters",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    responsible_partner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="partner_matters",
        null=True,
        blank=True,
    )
    responsible_advocate = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="advocate_matters",
        null=True,
        blank=True,
    )
    opened_date = models.DateField(default=timezone.localdate)
    closed_date = models.DateField(null=True, blank=True)
    physical_file_exists = models.BooleanField(default=False)
    confidentiality_level = models.CharField(
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.STANDARD,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_matters",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["firm", "matter_number"], name="unique_matter_number_per_firm")
        ]
        indexes = [
            models.Index(fields=["firm", "matter_number"], name="matters_matter_firm_number_idx"),
            models.Index(fields=["firm", "status"], name="matters_matter_firm_status_idx"),
            models.Index(fields=["firm", "title"], name="matters_matter_firm_title_idx"),
        ]
        ordering = ("-opened_date", "matter_number")

    def __str__(self) -> str:
        return f"{self.matter_number} {self.title}"


class MatterParty(models.Model):
    class PartyType(models.TextChoices):
        CLIENT = "CLIENT", "Client"
        OPPOSING_PARTY = "OPPOSING_PARTY", "Opposing party"
        INTERESTED_PARTY = "INTERESTED_PARTY", "Interested party"
        WITNESS = "WITNESS", "Witness"
        COMPANY_DIRECTOR = "COMPANY_DIRECTOR", "Company director"
        OTHER = "OTHER", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="matter_parties")
    matter = models.ForeignKey(Matter, on_delete=models.CASCADE, related_name="parties")
    party_type = models.CharField(max_length=30, choices=PartyType.choices)
    name = models.CharField(max_length=255)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["firm", "name"], name="matters_party_firm_name_idx"),
            models.Index(fields=["firm", "party_type"], name="matters_party_firm_type_idx"),
        ]
        ordering = ("party_type", "name")

    def __str__(self) -> str:
        return self.name
