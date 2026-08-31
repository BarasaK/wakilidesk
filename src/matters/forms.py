from django import forms

from clients.models import Client
from firms.models import FirmMembership
from matters.models import Matter, MatterParty, PracticeArea


class PracticeAreaForm(forms.ModelForm):
    class Meta:
        model = PracticeArea
        fields = ("name", "code", "is_active")


class MatterForm(forms.ModelForm):
    class Meta:
        model = Matter
        fields = (
            "client",
            "title",
            "description",
            "practice_area",
            "status",
            "responsible_partner",
            "responsible_advocate",
            "opened_date",
            "closed_date",
            "physical_file_exists",
            "confidentiality_level",
        )

    def __init__(self, *args, firm, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["client"].queryset = Client.objects.filter(firm=firm).order_by("name")
        self.fields["practice_area"].queryset = PracticeArea.objects.filter(
            firm=firm, is_active=True
        ).order_by("name")
        users = [membership.user_id for membership in FirmMembership.objects.filter(firm=firm)]
        self.fields["responsible_partner"].queryset = self.fields[
            "responsible_partner"
        ].queryset.filter(id__in=users)
        self.fields["responsible_advocate"].queryset = self.fields[
            "responsible_advocate"
        ].queryset.filter(id__in=users)


class MatterPartyForm(forms.ModelForm):
    class Meta:
        model = MatterParty
        fields = ("party_type", "name", "email", "phone", "notes")
