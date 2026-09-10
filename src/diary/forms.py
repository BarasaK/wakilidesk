from __future__ import annotations

from datetime import timedelta

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils import timezone

from diary.models import DiaryEvent, DiaryReminder
from firms.models import FirmMembership
from matters.services import matters_visible_to_user


REMINDER_OFFSETS = {
    "0": ("Same day", timedelta(hours=0)),
    "1": ("1 day before", timedelta(days=1)),
    "3": ("3 days before", timedelta(days=3)),
    "7": ("7 days before", timedelta(days=7)),
}


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"

    def __init__(self, attrs=None):
        super().__init__(attrs=attrs, format="%Y-%m-%dT%H:%M")


class DiaryEventForm(forms.ModelForm):
    reminder_offsets = forms.MultipleChoiceField(
        choices=[(value, label_offset[0]) for value, label_offset in REMINDER_OFFSETS.items()],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Reminder schedule",
    )
    reminder_channels = forms.MultipleChoiceField(
        choices=DiaryReminder.Channel.choices,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        initial=[DiaryReminder.Channel.IN_APP],
        label="Reminder channels",
    )

    class Meta:
        model = DiaryEvent
        fields = (
            "matter",
            "title",
            "event_type",
            "start_at",
            "end_at",
            "court_name",
            "location",
            "assigned_to",
            "additional_reminder_emails",
            "status",
            "notes",
        )
        widgets = {
            "start_at": DateTimeLocalInput(),
            "end_at": DateTimeLocalInput(),
            "additional_reminder_emails": forms.Textarea(attrs={"rows": 3}),
        }
        labels = {
            "additional_reminder_emails": "Additional reminder emails",
        }
        help_texts = {
            "additional_reminder_emails": "Optional. Add comma-separated or line-separated email addresses to copy on email reminders.",
        }

    def __init__(self, *args, firm, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["matter"].queryset = matters_visible_to_user(firm=firm, user=user).order_by(
            "matter_number"
        )
        user_ids = FirmMembership.objects.filter(
            firm=firm,
            status=FirmMembership.Status.ACTIVE,
        ).values_list("user_id", flat=True)
        self.fields["assigned_to"].queryset = self.fields["assigned_to"].queryset.filter(
            id__in=user_ids,
            is_active=True,
        ).order_by("email")

        for name in ("start_at", "end_at"):
            value = self.initial.get(name) or getattr(self.instance, name, None)
            if value:
                self.initial[name] = timezone.localtime(value).strftime("%Y-%m-%dT%H:%M")

        if self.instance.pk:
            pending_reminders = self.instance.reminders.filter(
                status=DiaryReminder.Status.PENDING
            )
            self.initial["reminder_channels"] = sorted(
                set(pending_reminders.values_list("channel", flat=True))
            )

    def clean(self):
        cleaned_data = super().clean()
        start_at = cleaned_data.get("start_at")
        end_at = cleaned_data.get("end_at")
        if start_at and end_at and end_at <= start_at:
            self.add_error("end_at", "End time must be after start time.")
        if cleaned_data.get("reminder_offsets") and not cleaned_data.get("reminder_channels"):
            self.add_error("reminder_channels", "Select at least one reminder channel.")
        return cleaned_data

    def clean_additional_reminder_emails(self):
        value = self.cleaned_data.get("additional_reminder_emails", "")
        emails = []
        seen = set()
        for raw_email in value.replace(",", "\n").splitlines():
            email = raw_email.strip().lower()
            if not email or email in seen:
                continue
            try:
                validate_email(email)
            except ValidationError:
                raise forms.ValidationError(f"Enter a valid email address: {raw_email.strip()}")
            seen.add(email)
            emails.append(email)
        return "\n".join(emails)


class DiaryEventFilterForm(forms.Form):
    q = forms.CharField(required=False, label="Search")
    event_type = forms.ChoiceField(
        choices=[("", "All types"), *DiaryEvent.EventType.choices],
        required=False,
    )
    status = forms.ChoiceField(
        choices=[("", "All statuses"), *DiaryEvent.Status.choices],
        required=False,
    )
    assigned_to = forms.ModelChoiceField(
        queryset=FirmMembership.objects.none(),
        required=False,
        label="Assigned user",
    )
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))

    def __init__(self, *args, firm, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assigned_to"].queryset = FirmMembership.objects.filter(
            firm=firm,
            status=FirmMembership.Status.ACTIVE,
            user__is_active=True,
        ).select_related("user").order_by("user__email")
        self.fields["assigned_to"].label_from_instance = lambda membership: membership.user.email
