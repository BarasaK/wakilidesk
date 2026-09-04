from django import forms


class ReportRequestForm(forms.Form):
    ENTITY_CHOICES = (
        ("clients", "Clients"),
        ("matters", "Matters"),
        ("documents", "Documents"),
        ("physical_files", "Physical files"),
        ("diary_events", "Diary events"),
    )
    FORMAT_CHOICES = (
        ("csv", "CSV"),
        ("xlsx", "Excel"),
        ("pdf", "PDF"),
    )

    entity = forms.ChoiceField(choices=ENTITY_CHOICES)
    export_format = forms.ChoiceField(choices=FORMAT_CHOICES, label="Format")
