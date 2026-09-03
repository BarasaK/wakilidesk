from __future__ import annotations

from datetime import datetime, time

from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from audit.services import record_audit_event
from diary.forms import REMINDER_OFFSETS
from diary.models import DiaryEvent, DiaryReminder
from matters.services import matters_visible_to_user, require_matter_access
from notifications.services import notify_user


def diary_events_for_firm(firm):
    return DiaryEvent.objects.filter(firm=firm).select_related(
        "matter",
        "matter__client",
        "assigned_to",
        "created_by",
    )


def diary_events_visible_to_user(*, firm, user):
    events = diary_events_for_firm(firm)
    accessible_matter_ids = matters_visible_to_user(firm=firm, user=user).values_list("id", flat=True)
    return events.filter(Q(matter__isnull=True) | Q(matter_id__in=accessible_matter_ids))


def filter_diary_events(queryset, *, data):
    q = data.get("q")
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q)
            | Q(court_name__icontains=q)
            | Q(location__icontains=q)
            | Q(matter__matter_number__icontains=q)
            | Q(matter__title__icontains=q)
        )
    if data.get("event_type"):
        queryset = queryset.filter(event_type=data["event_type"])
    if data.get("status"):
        queryset = queryset.filter(status=data["status"])
    if data.get("assigned_to"):
        queryset = queryset.filter(assigned_to=data["assigned_to"].user)
    if data.get("date_from"):
        queryset = queryset.filter(start_at__date__gte=data["date_from"])
    if data.get("date_to"):
        queryset = queryset.filter(start_at__date__lte=data["date_to"])
    return queryset


@transaction.atomic
def create_diary_event(*, firm, user, data, reminder_offsets, reminder_channels, request=None):
    matter = data.get("matter")
    if matter is not None:
        require_matter_access(matter=matter, firm=firm, user=user)
    assigned_to = data.get("assigned_to")
    if assigned_to is not None and not assigned_to.memberships.filter(firm=firm).exists():
        raise ValueError("Assigned user does not belong to the current firm.")

    event = DiaryEvent.objects.create(firm=firm, created_by=user, **data)
    sync_reminders(
        event=event,
        reminder_offsets=reminder_offsets,
        reminder_channels=reminder_channels,
    )
    record_audit_event(
        request=request,
        firm=firm,
        user=user,
        action="diary_event_created",
        object_type="DiaryEvent",
        object_id=event.id,
    )
    return event


@transaction.atomic
def update_diary_event(*, event, user, data, reminder_offsets, reminder_channels, request=None):
    matter = data.get("matter")
    if matter is not None:
        require_matter_access(matter=matter, firm=event.firm, user=user)
    assigned_to = data.get("assigned_to")
    if assigned_to is not None and not assigned_to.memberships.filter(firm=event.firm).exists():
        raise ValueError("Assigned user does not belong to the current firm.")

    for field, value in data.items():
        setattr(event, field, value)
    event.save()
    sync_reminders(
        event=event,
        reminder_offsets=reminder_offsets,
        reminder_channels=reminder_channels,
    )
    record_audit_event(
        request=request,
        firm=event.firm,
        user=user,
        action="diary_event_updated",
        object_type="DiaryEvent",
        object_id=event.id,
    )
    return event


def sync_reminders(*, event, reminder_offsets, reminder_channels):
    event.reminders.filter(status=DiaryReminder.Status.PENDING).delete()
    for offset_key in reminder_offsets:
        offset = REMINDER_OFFSETS[offset_key][1]
        remind_at = event.start_at - offset
        if offset_key == "0":
            remind_at = timezone.make_aware(
                datetime.combine(timezone.localtime(event.start_at).date(), time(hour=8))
            )
            if remind_at > event.start_at:
                remind_at = event.start_at
        for channel in reminder_channels:
            DiaryReminder.objects.get_or_create(
                event=event,
                remind_at=remind_at,
                channel=channel,
            )


def pending_reminders_due(now=None):
    now = now or timezone.now()
    return DiaryReminder.objects.select_related(
        "event",
        "event__firm",
        "event__matter",
        "event__assigned_to",
        "event__created_by",
    ).filter(
        status=DiaryReminder.Status.PENDING,
        remind_at__lte=now,
        event__status=DiaryEvent.Status.SCHEDULED,
    )


def send_due_diary_reminders(now=None) -> dict[str, int]:
    sent = 0
    failed = 0
    for reminder in pending_reminders_due(now=now):
        try:
            send_diary_reminder(reminder)
        except Exception as exc:
            failed += 1
            reminder.status = DiaryReminder.Status.FAILED
            reminder.failure_reason = str(exc)
            reminder.save(update_fields=["status", "failure_reason"])
        else:
            sent += 1
    return {"sent": sent, "failed": failed}


@transaction.atomic
def send_diary_reminder(reminder):
    reminder = DiaryReminder.objects.select_for_update().get(id=reminder.id)
    if reminder.status != DiaryReminder.Status.PENDING:
        return reminder

    event = DiaryEvent.objects.select_related(
        "firm",
        "matter",
        "assigned_to",
        "created_by",
    ).get(id=reminder.event_id)
    recipient = event.assigned_to or event.created_by
    if recipient is None:
        reminder.status = DiaryReminder.Status.FAILED
        reminder.failure_reason = "No reminder recipient is available."
        reminder.save(update_fields=["status", "failure_reason"])
        return reminder

    title = f"Diary reminder: {event.title}"
    message = diary_reminder_message(event)
    if reminder.channel == DiaryReminder.Channel.IN_APP:
        notify_user(
            firm=event.firm,
            recipient=recipient,
            title=title,
            message=message,
            object_type="DiaryEvent",
            object_id=event.id,
        )
    elif reminder.channel == DiaryReminder.Channel.EMAIL:
        if not recipient.email:
            raise ValueError("Reminder recipient has no email address.")
        send_mail(
            subject=title,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient.email],
            fail_silently=False,
        )

    reminder.status = DiaryReminder.Status.SENT
    reminder.sent_at = timezone.now()
    reminder.failure_reason = ""
    reminder.save(update_fields=["status", "sent_at", "failure_reason"])
    return reminder


def diary_reminder_message(event):
    start_at = timezone.localtime(event.start_at).strftime("%d %b %Y, %H:%M")
    matter = f"\nMatter: {event.matter.matter_number} {event.matter.title}" if event.matter else ""
    court = f"\nCourt: {event.court_name}" if event.court_name else ""
    location = f"\nLocation: {event.location}" if event.location else ""
    return f"{event.get_event_type_display()} scheduled for {start_at}.{matter}{court}{location}"
