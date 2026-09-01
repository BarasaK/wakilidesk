from django import forms

from firms.models import FirmMembership
from matters.models import Matter
from matters.services import matters_visible_to_user
from physical_files.models import DigitisationReview, FileCheckout, PhysicalFile, StorageLocation


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

    def __init__(self, *args, firm, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        matters = (
            matters_visible_to_user(firm=firm, user=user)
            if user is not None
            else Matter.objects.filter(firm=firm)
        )
        self.fields["matter"].queryset = matters.order_by("matter_number")
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


class DigitisationReviewForm(forms.ModelForm):
    class Meta:
        model = DigitisationReview
        fields = (
            "scanner_operator",
            "scan_date",
            "reviewer",
            "review_date",
            "missing_page_flag",
            "poor_quality_flag",
            "rescan_required",
            "completion_confirmed",
            "notes",
        )
        widgets = {
            "scan_date": forms.DateInput(attrs={"type": "date"}),
            "review_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, firm, **kwargs):
        super().__init__(*args, **kwargs)
        users = [membership.user_id for membership in FirmMembership.objects.filter(firm=firm)]
        self.fields["scanner_operator"].queryset = self.fields["scanner_operator"].queryset.filter(id__in=users)
        self.fields["reviewer"].queryset = self.fields["reviewer"].queryset.filter(id__in=users)
