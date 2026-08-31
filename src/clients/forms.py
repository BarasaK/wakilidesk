from django import forms

from clients.models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = (
            "client_type",
            "name",
            "company_registration_number",
            "national_id_or_passport",
            "kra_pin",
            "email",
            "phone",
            "address",
            "status",
        )
