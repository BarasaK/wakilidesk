import pytest
from django.urls import reverse

from accounts.models import User
from firms.models import Firm, FirmMembership
from firms.services import ensure_default_roles_for_firm


@pytest.mark.django_db
def test_user_from_firm_a_cannot_retrieve_firm_b_data(client):
    firm_a = Firm.objects.create(
        name="Firm A LLP",
        display_name="Firm A",
        slug="firm-a",
        email="admin@firma.test",
    )
    firm_b = Firm.objects.create(
        name="Firm B LLP",
        display_name="Firm B",
        slug="firm-b",
        email="admin@firmb.test",
    )
    role_a = ensure_default_roles_for_firm(firm_a)["Firm Administrator"]
    ensure_default_roles_for_firm(firm_b)
    user_a = User.objects.create_user("admin@firma.test", "password123")
    FirmMembership.objects.create(user=user_a, firm=firm_a, role=role_a)

    client.force_login(user_a)
    response = client.get(reverse("firm_detail", args=[firm_b.id]))

    assert response.status_code == 403
