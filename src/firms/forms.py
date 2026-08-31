from django import forms

from firms.models import Firm, Permission, Role, UserInvitation


class FirmOnboardingForm(forms.ModelForm):
    class Meta:
        model = Firm
        fields = (
            "name",
            "display_name",
            "email",
            "phone",
            "address",
            "city",
            "country",
            "timezone",
            "currency",
            "file_number_pattern",
        )


class FirmProfileForm(forms.ModelForm):
    class Meta:
        model = Firm
        fields = (
            "display_name",
            "logo",
            "email",
            "phone",
            "address",
            "city",
            "country",
            "timezone",
            "currency",
            "file_number_pattern",
        )


class UserInvitationForm(forms.ModelForm):
    class Meta:
        model = UserInvitation
        fields = ("email", "role")

    def __init__(self, *args, firm, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].queryset = firm.roles.order_by("name")


class RoleForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.order_by("module", "codename"),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Role
        fields = ("name", "description", "permissions")

    def __init__(self, *args, firm, **kwargs):
        self.firm = firm
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        role = super().save(commit=False)
        role.firm = self.firm
        if commit:
            role.save()
            self.save_m2m()
        return role
