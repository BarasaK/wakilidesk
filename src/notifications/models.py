from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Notification(models.Model):
    class Channel(models.TextChoices):
        IN_APP = "IN_APP", "In app"
        EMAIL = "EMAIL", "Email"

    class Status(models.TextChoices):
        UNREAD = "UNREAD", "Unread"
        READ = "READ", "Read"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="notifications")
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=180)
    message = models.TextField()
    channel = models.CharField(max_length=20, choices=Channel.choices, default=Channel.IN_APP)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.UNREAD)
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["firm", "recipient", "status"], name="notif_firm_rec_stat_idx"),
            models.Index(fields=["firm", "created_at"], name="notif_firm_created_idx"),
        ]
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return self.title
