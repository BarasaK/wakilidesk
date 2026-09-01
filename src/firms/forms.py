from django import forms

from firms.models import Firm, Permission, Role, UserInvitation


DEFAULT_ACCENT_COLOR = "#0f766e"


class FirmThemeFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["accent_color"].required = False
        self.fields["accent_color"].initial = self.fields["accent_color"].initial or DEFAULT_ACCENT_COLOR

    def clean_accent_color(self):
        return self.cleaned_data["accent_color"] or DEFAULT_ACCENT_COLOR


class FirmOnboardingForm(FirmThemeFormMixin, forms.ModelForm):
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
            "accent_color",
        )
        widgets = {"accent_color": forms.TextInput(attrs={"type": "color"})}
        labels = {"accent_color": "Theme color"}


class FirmProfileForm(FirmThemeFormMixin, forms.ModelForm):
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
            "accent_color",
        )
        widgets = {"accent_color": forms.TextInput(attrs={"type": "color"})}
        labels = {"accent_color": "Theme color"}


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
