from django import forms

from firms.models import FirmMembership
from matters.models import Matter
from physical_files.models import FileCheckout, PhysicalFile, StorageLocation


class StorageLocationForm(forms.ModelForm):
    class Meta:
        model = StorageLocation
        fields = ("name", "parent", "is_active")

    def __init__(self, *args, firm, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent"].queryset = StorageLocation.objects.filter(firm=firm).order_by("name")


class PhysicalFileForm(forms.ModelForm):
    class Meta:
        model = PhysicalFile
        fields = (
            "matter",
            "physical_file_number",
            "volume_number",
            "storage_location",
            "status",
            "digitisation_status",
            "barcode_or_qr_code",
            "notes",
        )

    def __init__(self, *args, firm, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["matter"].queryset = Matter.objects.filter(firm=firm).order_by("matter_number")
        self.fields["storage_location"].queryset = StorageLocation.objects.filter(
            firm=firm, is_active=True
        ).order_by("name")


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = FileCheckout
        fields = ("checked_out_to", "checked_out_to_name", "expected_return_at", "purpose", "notes")
        widgets = {
            "expected_return_at": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, firm, **kwargs):
        super().__init__(*args, **kwargs)
        users = [membership.user_id for membership in FirmMembership.objects.filter(firm=firm)]
        self.fields["checked_out_to"].queryset = self.fields["checked_out_to"].queryset.filter(id__in=users)


class CheckinForm(forms.Form):
    notes = forms.CharField(widget=forms.Textarea, required=False)
