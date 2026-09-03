from datetime import timedelta

import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from clients.models import Client
from diary.models import DiaryEvent, DiaryReminder
from diary.services import send_due_diary_reminders
from firms.models import Firm, FirmMembership
from firms.services import ensure_default_roles_for_firm
from matters.models import Matter
from notifications.models import Notification


@pytest.mark.django_db
def test_diary_event_create_adds_reminders(client):
    firm, admin, matter, _assigned, _unassigned = _setup()
    client.force_login(admin)

    start_at = timezone.now() + timedelta(days=5)
    response = client.post(
        reverse("diary_event_create"),
        {
            "matter": matter.id,
            "title": "High Court mention",
            "event_type": DiaryEvent.EventType.MENTION,
            "start_at": start_at.strftime("%Y-%m-%dT%H:%M"),
            "end_at": "",
            "court_name": "Milimani High Court",
            "location": "Court 3",
            "assigned_to": admin.id,
            "status": DiaryEvent.Status.SCHEDULED,
            "notes": "Prepare bundle.",
            "reminder_offsets": ["1", "3"],
            "reminder_channels": [DiaryReminder.Channel.IN_APP, DiaryReminder.Channel.EMAIL],
        },
    )

    assert response.status_code == 302
    event = DiaryEvent.objects.get(firm=firm, title="High Court mention")
    assert event.reminders.count() == 4


@pytest.mark.django_db
def test_diary_list_is_tenant_scoped(client):
    firm, admin, _matter, _assigned, _unassigned = _setup()
    other_firm, other_admin, other_matter, _other_assigned, _other_unassigned = _setup(
        slug="other-firm",
        email_prefix="other",
    )
    DiaryEvent.objects.create(
        firm=other_firm,
        matter=other_matter,
        title="Other firm hearing",
        event_type=DiaryEvent.EventType.HEARING,
        start_at=timezone.now() + timedelta(days=1),
        created_by=other_admin,
    )

    client.force_login(admin)
    response = client.get(reverse("diary_event_list"))

    assert response.status_code == 200
    assert b"Other firm hearing" not in response.content
    assert firm != other_firm


@pytest.mark.django_db
def test_diary_events_for_restricted_matters_are_hidden_from_unassigned_user(client):
    _firm, _admin, matter, assigned, unassigned = _setup(confidential=True)
    event = DiaryEvent.objects.create(
        firm=matter.firm,
        matter=matter,
        title="Restricted hearing",
        event_type=DiaryEvent.EventType.HEARING,
        start_at=timezone.now() + timedelta(days=1),
        assigned_to=assigned,
        created_by=assigned,
    )

    client.force_login(unassigned)
    assert client.get(reverse("diary_event_detail", args=[event.id])).status_code == 404

    response = client.get(reverse("diary_event_list"))
    assert response.status_code == 200
    assert b"Restricted hearing" not in response.content


@pytest.mark.django_db
def test_dashboard_shows_upcoming_diary_events(client):
    _firm, admin, matter, _assigned, _unassigned = _setup()
    DiaryEvent.objects.create(
        firm=matter.firm,
        matter=matter,
        title="Upcoming mention",
        event_type=DiaryEvent.EventType.MENTION,
        start_at=timezone.now() + timedelta(days=1),
        assigned_to=admin,
        created_by=admin,
    )

    client.force_login(admin)
    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert b"Upcoming Diary" in response.content
    assert b"Upcoming mention" in response.content


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_due_diary_reminders_create_notification_and_email_once():
    _firm, admin, matter, _assigned, _unassigned = _setup()
    event = DiaryEvent.objects.create(
        firm=matter.firm,
        matter=matter,
        title="Due hearing",
        event_type=DiaryEvent.EventType.HEARING,
        start_at=timezone.now() + timedelta(hours=1),
        assigned_to=admin,
        created_by=admin,
    )
    DiaryReminder.objects.create(
        event=event,
        remind_at=timezone.now() - timedelta(minutes=1),
        channel=DiaryReminder.Channel.IN_APP,
    )
    DiaryReminder.objects.create(
        event=event,
        remind_at=timezone.now() - timedelta(minutes=1),
        channel=DiaryReminder.Channel.EMAIL,
    )

    result = send_due_diary_reminders()
    second_result = send_due_diary_reminders()

    assert result == {"sent": 2, "failed": 0}
    assert second_result == {"sent": 0, "failed": 0}
    assert Notification.objects.filter(recipient=admin, title__icontains="Due hearing").count() == 1
    assert len(mail.outbox) == 1
    assert "Due hearing" in mail.outbox[0].subject


@pytest.mark.django_db
def test_email_reminder_failure_is_recorded(monkeypatch):
    _firm, admin, matter, _assigned, _unassigned = _setup()
    event = DiaryEvent.objects.create(
        firm=matter.firm,
        matter=matter,
        title="Failing email",
        event_type=DiaryEvent.EventType.HEARING,
        start_at=timezone.now() + timedelta(hours=1),
        assigned_to=admin,
        created_by=admin,
    )
    reminder = DiaryReminder.objects.create(
        event=event,
        remind_at=timezone.now() - timedelta(minutes=1),
        channel=DiaryReminder.Channel.EMAIL,
    )
    monkeypatch.setattr("diary.services.send_mail", _raise_email_error)

    result = send_due_diary_reminders()
    reminder.refresh_from_db()

    assert result == {"sent": 0, "failed": 1}
    assert reminder.status == DiaryReminder.Status.FAILED
    assert "SMTP unavailable" in reminder.failure_reason


def _raise_email_error(*args, **kwargs):
    raise RuntimeError("SMTP unavailable")


def _setup(slug="diary-firm", email_prefix="diary", confidential=False):
    firm = Firm.objects.create(
        name=f"{email_prefix} LLP",
        display_name=f"{email_prefix.title()} Firm",
        slug=slug,
        email=f"admin@{email_prefix}.test",
    )
    roles = ensure_default_roles_for_firm(firm)
    admin = User.objects.create_user(f"admin@{email_prefix}.test", "StrongPass123!")
    assigned = User.objects.create_user(f"assigned@{email_prefix}.test", "StrongPass123!")
    unassigned = User.objects.create_user(f"unassigned@{email_prefix}.test", "StrongPass123!")
    FirmMembership.objects.create(user=admin, firm=firm, role=roles["Firm Administrator"])
    FirmMembership.objects.create(user=assigned, firm=firm, role=roles["Auditor / Read-only"])
    FirmMembership.objects.create(user=unassigned, firm=firm, role=roles["Auditor / Read-only"])
    client = Client.objects.create(
        firm=firm,
        client_number="CL-00001",
        client_type=Client.ClientType.INDIVIDUAL,
        name=f"{email_prefix.title()} Client",
        created_by=admin,
    )
    matter = Matter.objects.create(
        firm=firm,
        client=client,
        matter_number="LIT/2026/00001",
        title=f"{email_prefix.title()} Matter",
        responsible_partner=admin,
        responsible_advocate=assigned,
        confidentiality_level=(
            Matter.ConfidentialityLevel.RESTRICTED
            if confidential
            else Matter.ConfidentialityLevel.STANDARD
        ),
        created_by=admin,
    )
    return firm, admin, matter, assigned, unassigned
