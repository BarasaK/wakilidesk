import pytest
from django.urls import reverse

from accounts.models import User
from audit.models import AuditEvent
from firms.models import Firm, FirmMembership, Role, UserInvitation
from firms.services import ensure_default_roles_for_firm


@pytest.mark.django_db
def test_signup_then_firm_onboarding_creates_admin_membership(client):
    signup_response = client.post(
        reverse("signup"),
        {
            "email": "newadmin@example.test",
            "first_name": "New",
            "last_name": "Admin",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        },
    )

    assert signup_response.status_code == 302
    assert signup_response["Location"] == reverse("firm_onboarding")

    onboarding_response = client.post(
        reverse("firm_onboarding"),
        {
            "name": "New Firm LLP",
            "display_name": "New Firm",
            "email": "hello@newfirm.test",
            "phone": "+254700000000",
            "address": "Nairobi",
            "city": "Nairobi",
            "country": "Kenya",
            "timezone": "Africa/Nairobi",
            "currency": "KES",
            "file_number_pattern": "{PRACTICE_AREA}/{YEAR}/{SEQUENCE}",
            "accent_color": "#1d4ed8",
        },
    )

    assert onboarding_response.status_code == 302
    assert onboarding_response["Location"] == reverse("dashboard")
    firm = Firm.objects.get(slug="new-firm")
    assert firm.accent_color == "#1d4ed8"
    membership = FirmMembership.objects.get(user__email="newadmin@example.test", firm=firm)
    assert membership.role.name == "Firm Administrator"
    assert AuditEvent.objects.filter(action="firm_created", firm=firm).exists()


@pytest.mark.django_db
def test_firm_admin_can_update_theme_color(client):
    firm, admin = _firm_with_user("admin@amani.test", "Firm Administrator")

    client.force_login(admin)
    response = client.post(
        reverse("firm_profile"),
        {
            "display_name": firm.display_name,
            "email": firm.email,
            "phone": firm.phone,
            "address": firm.address,
            "city": firm.city,
            "country": firm.country,
            "timezone": firm.timezone,
            "currency": firm.currency,
            "file_number_pattern": firm.file_number_pattern,
            "accent_color": "#7c2d12",
        },
    )
    firm.refresh_from_db()

    assert response.status_code == 302
    assert firm.accent_color == "#7c2d12"


@pytest.mark.django_db
def test_dashboard_uses_firm_theme_color(client):
    firm, admin = _firm_with_user("admin@theme.test", "Firm Administrator")
    firm.accent_color = "#1d4ed8"
    firm.save(update_fields=["accent_color"])

    client.force_login(admin)
    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert b"--accent: #1d4ed8" in response.content


@pytest.mark.django_db
def test_firm_admin_can_create_invitation(client):
    firm, admin = _firm_with_user("admin@amani.test", "Firm Administrator")
    role = firm.roles.get(name="Advocate")

    client.force_login(admin)
    response = client.post(
        reverse("invite_user"),
        {"email": "advocate@amani.test", "role": role.id},
    )

    assert response.status_code == 302
    invitation = UserInvitation.objects.get(email="advocate@amani.test")
    assert invitation.firm == firm
    assert invitation.role == role
    assert AuditEvent.objects.filter(action="user_invited", firm=firm).exists()


@pytest.mark.django_db
def test_user_without_manage_users_cannot_invite(client):
    _firm, advocate = _firm_with_user("advocate@amani.test", "Advocate")

    client.force_login(advocate)
    response = client.get(reverse("invite_user"))

    assert response.status_code == 403


@pytest.mark.django_db
def test_navigation_hides_inaccessible_admin_links(client):
    _firm, auditor = _firm_with_user("auditor@amani.test", "Auditor / Read-only")

    client.force_login(auditor)
    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert b">Clients<" in response.content
    assert b">Users<" not in response.content
    assert b">Roles<" not in response.content
    assert b">Firm Profile<" not in response.content
    assert b"New client" not in response.content
    assert b"Upload document" not in response.content
    assert b"New diary event" not in response.content
    assert client.get(reverse("admin_users")).status_code == 403


@pytest.mark.django_db
def test_module_actions_hide_inaccessible_links(client):
    firm, clerk = _firm_with_user("clerk@amani.test", "Clerk / Records Officer")

    client.force_login(clerk)
    documents_response = client.get(reverse("document_list"))
    physical_files_response = client.get(reverse("physical_file_list"))
    matters_response = client.get(reverse("matter_list"))

    assert documents_response.status_code == 200
    assert b"Upload document" in documents_response.content
    assert b"Categories" not in documents_response.content
    assert physical_files_response.status_code == 200
    assert b"Register file" in physical_files_response.content
    assert b"Locations" in physical_files_response.content
    assert matters_response.status_code == 200
    assert b"Create matter" not in matters_response.content
    assert b"Practice areas" not in matters_response.content
    assert firm.roles.filter(name="Clerk / Records Officer").exists()


@pytest.mark.django_db
def test_invited_user_can_accept_invitation(client):
    firm, admin = _firm_with_user("admin@amani.test", "Firm Administrator")
    role = firm.roles.get(name="Secretary")
    invitation = UserInvitation.objects.create(
        firm=firm,
        email="secretary@amani.test",
        role=role,
        invited_by=admin,
    )

    response = client.post(
        reverse("accept_invitation", args=[invitation.token]),
        {
            "first_name": "Secretary",
            "last_name": "Amani",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        },
    )

    assert response.status_code == 302
    user = User.objects.get(email="secretary@amani.test")
    assert FirmMembership.objects.filter(user=user, firm=firm, role=role).exists()
    invitation.refresh_from_db()
    assert invitation.status == UserInvitation.Status.ACCEPTED
    assert AuditEvent.objects.filter(action="user_invitation_accepted", firm=firm).exists()


def _firm_with_user(email: str, role_name: str):
    firm = Firm.objects.create(
        name="Amani & Co Advocates LLP",
        display_name=f"Amani {email}",
        slug=email.split("@")[0].replace(".", "-"),
        email="hello@amani.test",
    )
    roles = ensure_default_roles_for_firm(firm)
    user = User.objects.create_user(email, "StrongPass123!")
    FirmMembership.objects.create(user=user, firm=firm, role=roles[role_name])
    return firm, user
