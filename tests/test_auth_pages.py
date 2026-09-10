import pytest
from django.core import mail
from django.test import override_settings
from django.urls import reverse

from accounts.models import User
from firms.models import Firm, FirmMembership
from firms.services import ensure_default_roles_for_firm


@pytest.mark.django_db
def test_login_page_loads(client):
    response = client.get(reverse("login"))

    assert response.status_code == 200
    assert b"wakiliDesk" in response.content
    assert b"common/wakilidesk-logo.png" in response.content
    assert b"Sign in" in response.content
    assert b"Open user documentation" in response.content
    assert b"Forgot password?" in response.content
    assert reverse("documentation").encode() in response.content
    assert reverse("password_reset").encode() in response.content
    assert b"development accounts from the README" not in response.content


@pytest.mark.django_db
def test_seeded_style_user_can_login(client):
    firm = Firm.objects.create(
        name="Amani & Co Advocates LLP",
        display_name="Amani Advocates",
        slug="amani-advocates-test",
        email="admin@amani.test",
    )
    role = ensure_default_roles_for_firm(firm)["Firm Administrator"]
    user = User.objects.create_user("admin@amaniadvocates.test", "ChangeMe123!")
    FirmMembership.objects.create(user=user, firm=firm, role=role)

    response = client.post(
        reverse("login"),
        {"username": "admin@amaniadvocates.test", "password": "ChangeMe123!"},
    )

    assert response.status_code == 302
    assert response["Location"] == reverse("dashboard")


@pytest.mark.django_db
@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
    DEFAULT_FROM_EMAIL="noreply@wakilidesk.com",
    PUBLIC_BASE_URL="https://staging.wakilidesk.com",
)
def test_password_reset_sends_email_to_active_user(client):
    User.objects.create_user("admin@wakilidesk.com", "ChangeMe123!")

    response = client.post(reverse("password_reset"), {"email": "admin@wakilidesk.com"})

    assert response.status_code == 302
    assert response["Location"] == reverse("password_reset_done")
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["admin@wakilidesk.com"]
    assert "Reset your wakiliDesk password" in mail.outbox[0].subject
    assert "https://staging.wakilidesk.com/accounts/reset/" in mail.outbox[0].body
    assert "127.0.0.1" not in mail.outbox[0].body
