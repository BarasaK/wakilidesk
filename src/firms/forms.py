from django import forms
from django.utils.html import format_html

from firms.models import Firm, Permission, Role, UserInvitation


DEFAULT_ACCENT_COLOR = "#0f766e"
DEFAULT_APP_FONT_FAMILY = Firm.AppFontFamily.SYSTEM
DEFAULT_APP_FONT_SIZE = 16
MIN_APP_FONT_SIZE = 14
MAX_APP_FONT_SIZE = 18


class LogoPreviewWidget(forms.ClearableFileInput):
    def render(self, name, value, attrs=None, renderer=None):
        field_html = super().render(name, value, attrs, renderer)
        if not value:
            return field_html
        try:
            url = value.url
        except ValueError:
            return field_html
        return format_html(
            '<div class="logo-preview"><img src="{}" alt="Current firm logo"></div>{}',
            url,
            field_html,
        )


class FirmThemeFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["accent_color"].required = False
        self.fields["accent_color"].initial = self.fields["accent_color"].initial or DEFAULT_ACCENT_COLOR
        self.fields["app_font_family"].required = False
        self.fields["app_font_family"].initial = (
            self.fields["app_font_family"].initial or DEFAULT_APP_FONT_FAMILY
        )
        self.fields["app_font_size"].required = False
        self.fields["app_font_size"].initial = (
            self.fields["app_font_size"].initial or DEFAULT_APP_FONT_SIZE
        )

    def clean_accent_color(self):
        return self.cleaned_data["accent_color"] or DEFAULT_ACCENT_COLOR

    def clean_app_font_family(self):
        return self.cleaned_data["app_font_family"] or DEFAULT_APP_FONT_FAMILY

    def clean_app_font_size(self):
        value = self.cleaned_data["app_font_size"] or DEFAULT_APP_FONT_SIZE
        return min(max(value, MIN_APP_FONT_SIZE), MAX_APP_FONT_SIZE)


class FirmOnboardingForm(FirmThemeFormMixin, forms.ModelForm):
    class Meta:
        model = Firm
        fields = (
            "name",
            "display_name",
            "email",
            "phone",
            "address",
            "logo",
            "city",
            "country",
            "timezone",
            "currency",
            "file_number_pattern",
            "accent_color",
            "app_font_family",
            "app_font_size",
        )
        widgets = {
            "accent_color": forms.TextInput(attrs={"type": "color"}),
            "app_font_family": forms.Select(attrs={"data-theme-font": "family"}),
            "app_font_size": forms.NumberInput(
                attrs={
                    "min": MIN_APP_FONT_SIZE,
                    "max": MAX_APP_FONT_SIZE,
                    "data-theme-font": "size",
                }
            ),
            "logo": LogoPreviewWidget,
        }
        labels = {
            "accent_color": "Theme color",
            "app_font_family": "Application font",
            "app_font_size": "Base font size",
        }


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
            "app_font_family",
            "app_font_size",
        )
        widgets = {
            "accent_color": forms.TextInput(attrs={"type": "color"}),
            "app_font_family": forms.Select(attrs={"data-theme-font": "family"}),
            "app_font_size": forms.NumberInput(
                attrs={
                    "min": MIN_APP_FONT_SIZE,
                    "max": MAX_APP_FONT_SIZE,
                    "data-theme-font": "size",
                }
            ),
            "logo": LogoPreviewWidget,
        }
        labels = {
            "accent_color": "Theme color",
            "app_font_family": "Application font",
            "app_font_size": "Base font size",
        }


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
