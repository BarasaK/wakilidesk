import pytest
from django.urls import reverse

from accounts.models import User
from audit.models import AuditEvent
from clients.models import Client
from firms.models import Firm, FirmMembership
from firms.services import ensure_default_roles_for_firm
from matters.models import Matter, MatterParty, PracticeArea


@pytest.mark.django_db
def test_firm_admin_can_create_client_and_matter(client):
    firm, user = _firm_with_user("admin@firm.test", "Firm Administrator")
    area = PracticeArea.objects.create(firm=firm, name="Litigation", code="LIT")

    client.force_login(user)
    client_response = client.post(
        reverse("client_create"),
        {
            "client_type": "INDIVIDUAL",
            "name": "Jane Wanjiku",
            "email": "jane@example.test",
            "phone": "+254700000001",
            "address": "Nairobi",
            "status": "ACTIVE",
        },
    )

    assert client_response.status_code == 302
    created_client = Client.objects.get(name="Jane Wanjiku")
    assert created_client.firm == firm
    assert created_client.client_number == "CL-00001"

    matter_response = client.post(
        reverse("matter_create"),
        {
            "client": created_client.id,
            "title": "Employment Claim",
            "description": "Claim file",
            "practice_area": area.id,
            "status": "OPEN",
            "responsible_partner": user.id,
            "responsible_advocate": user.id,
            "opened_date": "2026-08-31",
            "closed_date": "",
            "physical_file_exists": "on",
            "confidentiality_level": "STANDARD",
        },
    )

    assert matter_response.status_code == 302
    matter = Matter.objects.get(title="Employment Claim")
    assert matter.firm == firm
    assert matter.matter_number == "LIT/2026/00001"
    assert AuditEvent.objects.filter(action="client_created", firm=firm).exists()
    assert AuditEvent.objects.filter(action="matter_created", firm=firm).exists()


@pytest.mark.django_db
def test_user_cannot_view_other_firm_client_or_matter(client):
    firm_a, user_a = _firm_with_user("admin@firma.test", "Firm Administrator")
    firm_b, user_b = _firm_with_user("admin@firmb.test", "Firm Administrator")
    client_b = Client.objects.create(
        firm=firm_b,
        client_number="CL-00001",
        client_type="INDIVIDUAL",
        name="Firm B Client",
        created_by=user_b,
    )
    area_b = PracticeArea.objects.create(firm=firm_b, name="Litigation", code="LIT")
    matter_b = Matter.objects.create(
        firm=firm_b,
        client=client_b,
        matter_number="LIT/2026/00001",
        title="Firm B Matter",
        practice_area=area_b,
        created_by=user_b,
    )

    client.force_login(user_a)

    assert client.get(reverse("client_detail", args=[client_b.id])).status_code == 404
    assert client.get(reverse("matter_detail", args=[matter_b.id])).status_code == 404
    assert firm_a.clients.count() == 0


@pytest.mark.django_db
def test_advocate_can_create_matter_but_not_client_by_default(client):
    _firm, user = _firm_with_user("advocate@firm.test", "Advocate")

    client.force_login(user)

    assert client.get(reverse("client_create")).status_code == 403
    assert client.get(reverse("matter_create")).status_code == 200


@pytest.mark.django_db
def test_matter_party_is_created_with_current_firm(client):
    firm, user = _firm_with_user("admin@firm.test", "Firm Administrator")
    client_record = Client.objects.create(
        firm=firm,
        client_number="CL-00001",
        client_type="INDIVIDUAL",
        name="Jane Wanjiku",
        created_by=user,
    )
    matter = Matter.objects.create(
        firm=firm,
        client=client_record,
        matter_number="GEN/2026/00001",
        title="General Matter",
        created_by=user,
    )

    client.force_login(user)
    response = client.post(
        reverse("matter_party_create", args=[matter.id]),
        {
            "party_type": "OPPOSING_PARTY",
            "name": "Respondent Ltd",
            "email": "legal@respondent.test",
            "phone": "",
            "notes": "Opposing party",
        },
    )

    assert response.status_code == 302
    party = MatterParty.objects.get(name="Respondent Ltd")
    assert party.firm == firm
    assert party.matter == matter


def _firm_with_user(email: str, role_name: str):
    slug = email.replace("@", "-").replace(".", "-")
    firm = Firm.objects.create(
        name=f"{email} LLP",
        display_name=f"{email} Firm",
        slug=slug,
        email=email,
    )
    roles = ensure_default_roles_for_firm(firm)
    user = User.objects.create_user(email, "StrongPass123!")
    FirmMembership.objects.create(user=user, firm=firm, role=roles[role_name])
    return firm, user
