from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class DiaryEvent(models.Model):
    class EventType(models.TextChoices):
        MENTION = "MENTION", "Mention"
        HEARING = "HEARING", "Hearing"
        FILING_DEADLINE = "FILING_DEADLINE", "Filing deadline"
        CLIENT_MEETING = "CLIENT_MEETING", "Client meeting"
        INTERNAL_TASK = "INTERNAL_TASK", "Internal task"
        OTHER = "OTHER", "Other"

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        ADJOURNED = "ADJOURNED", "Adjourned"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="diary_events")
    matter = models.ForeignKey(
        "matters.Matter",
        on_delete=models.CASCADE,
        related_name="diary_events",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField(null=True, blank=True)
    court_name = models.CharField(max_length=180, blank=True)
    location = models.CharField(max_length=180, blank=True)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="assigned_diary_events",
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="created_diary_events",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["firm", "start_at"], name="diary_event_firm_start_idx"),
            models.Index(fields=["firm", "status"], name="diary_event_firm_status_idx"),
            models.Index(fields=["firm", "event_type"], name="diary_event_firm_type_idx"),
            models.Index(fields=["assigned_to", "start_at"], name="diary_event_assigned_idx"),
        ]
        ordering = ("start_at", "title")

    def __str__(self) -> str:
        return self.title

    @property
    def is_past_due(self) -> bool:
        return self.status == self.Status.SCHEDULED and self.start_at < timezone.now()


class DiaryReminder(models.Model):
    class Channel(models.TextChoices):
        IN_APP = "IN_APP", "In app"
        EMAIL = "EMAIL", "Email"

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(DiaryEvent, on_delete=models.CASCADE, related_name="reminders")
    remind_at = models.DateTimeField()
    channel = models.CharField(max_length=20, choices=Channel.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    sent_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "remind_at", "channel"],
                name="unique_diary_reminder_schedule",
            )
        ]
        indexes = [
            models.Index(fields=["status", "remind_at"], name="diary_rem_status_due_idx"),
            models.Index(fields=["channel", "status"], name="diary_rem_channel_status_idx"),
        ]
        ordering = ("remind_at", "channel")

    def __str__(self) -> str:
        return f"{self.event} {self.channel} at {self.remind_at}"
