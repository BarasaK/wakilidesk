from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Client(models.Model):
    class ClientType(models.TextChoices):
        INDIVIDUAL = "INDIVIDUAL", "Individual"
        ORGANISATION = "ORGANISATION", "Organisation"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        ARCHIVED = "ARCHIVED", "Archived"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="clients")
    client_number = models.CharField(max_length=50)
    client_type = models.CharField(
        max_length=20, choices=ClientType.choices, default=ClientType.INDIVIDUAL
    )
    name = models.CharField(max_length=255)
    company_registration_number = models.CharField(max_length=100, blank=True)
    national_id_or_passport = models.CharField(max_length=100, blank=True)
    kra_pin = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    address = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_clients",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["firm", "client_number"], name="unique_client_number_per_firm"
            )
        ]
        indexes = [
            models.Index(fields=["firm", "name"], name="clients_client_firm_name_idx"),
            models.Index(fields=["firm", "status"], name="clients_client_firm_status_idx"),
        ]
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name
