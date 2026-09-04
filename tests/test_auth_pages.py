import pytest
from django.urls import reverse

from accounts.models import User
from firms.models import Firm, FirmMembership
from firms.services import ensure_default_roles_for_firm


@pytest.mark.django_db
def test_login_page_loads(client):
    response = client.get(reverse("login"))

    assert response.status_code == 200
    assert b"wakiliDesk" in response.content
    assert b"Sign in" in response.content
    assert b"Open user documentation" in response.content
    assert reverse("documentation").encode() in response.content
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
