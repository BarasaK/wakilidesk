from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey(
        "firms.Firm",
        on_delete=models.CASCADE,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="audit_events",
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("-timestamp",)
        indexes = [
            models.Index(fields=["firm", "timestamp"], name="audit_audit_firm_id_9c9c24_idx"),
            models.Index(fields=["user", "timestamp"], name="audit_audit_user_id_92cf35_idx"),
            models.Index(fields=["action"], name="audit_audit_action_f0cb12_idx"),
        ]

    def __str__(self) -> str:
        return f"{self.action} at {self.timestamp:%Y-%m-%d %H:%M:%S}"
