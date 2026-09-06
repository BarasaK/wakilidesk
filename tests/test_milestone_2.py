import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from audit.models import AuditEvent
from clients.models import Client
from firms.models import Firm, FirmMembership, Role
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


@pytest.mark.django_db
def test_admin_can_move_client_to_trash_and_restore_it(client):
    firm, user = _firm_with_user("admin@client-trash.test", "Firm Administrator")
    client_record = Client.objects.create(
        firm=firm,
        client_number="CL-00001",
        client_type="INDIVIDUAL",
        name="Trash Client",
        created_by=user,
    )

    client.force_login(user)
    trash_response = client.post(reverse("client_trash_move", args=[client_record.id]))
    client_record.refresh_from_db()

    assert trash_response.status_code == 302
    assert client_record.deleted_at is not None
    assert b"Trash Client" not in client.get(reverse("client_list")).content
    assert b"Trash Client" in client.get(reverse("client_trash")).content
    assert AuditEvent.objects.filter(action="client_moved_to_trash", firm=firm).exists()

    restore_response = client.post(reverse("client_trash_restore", args=[client_record.id]))
    client_record.refresh_from_db()

    assert restore_response.status_code == 302
    assert client_record.deleted_at is None
    assert b"Trash Client" in client.get(reverse("client_list")).content
    assert AuditEvent.objects.filter(action="client_restored_from_trash", firm=firm).exists()


@pytest.mark.django_db
def test_admin_can_move_matter_to_trash_and_restore_it(client):
    firm, user, matter = _matter_for_trash("admin@matter-trash.test")

    client.force_login(user)
    trash_response = client.post(reverse("matter_trash_move", args=[matter.id]))
    matter.refresh_from_db()

    assert trash_response.status_code == 302
    assert matter.deleted_at is not None
    assert matter.title.encode() not in client.get(reverse("matter_list")).content
    assert matter.title.encode() in client.get(reverse("matter_trash")).content
    assert AuditEvent.objects.filter(action="matter_moved_to_trash", firm=firm).exists()

    restore_response = client.post(reverse("matter_trash_restore", args=[matter.id]))
    matter.refresh_from_db()

    assert restore_response.status_code == 302
    assert matter.deleted_at is None
    assert matter.title.encode() in client.get(reverse("matter_list")).content
    assert AuditEvent.objects.filter(action="matter_restored_from_trash", firm=firm).exists()


@pytest.mark.django_db
def test_client_trash_hides_linked_matters_from_active_workflows(client):
    _firm, user, matter = _matter_for_trash("admin@linked-trash.test")
    client_record = matter.client

    client.force_login(user)
    client.post(reverse("client_trash_move", args=[client_record.id]))

    assert client_record.name.encode() not in client.get(reverse("client_list")).content
    assert matter.title.encode() not in client.get(reverse("matter_list")).content


@pytest.mark.django_db
def test_only_admin_can_permanently_delete_trashed_client_or_matter(client):
    firm, admin, matter = _matter_for_trash("admin@permanent-trash.test")
    client_record = Client.objects.create(
        firm=firm,
        client_number="CL-00002",
        client_type="INDIVIDUAL",
        name="Unlinked Trash Client",
        created_by=admin,
    )
    limited = User.objects.create_user("limited@permanent-trash.test", "StrongPass123!")
    limited_role = Role.objects.create(firm=firm, name="Delete without settings")
    limited_role.permissions.set(
        [
            firm.roles.get(name="Firm Administrator").permissions.get(codename="delete_client"),
            firm.roles.get(name="Firm Administrator").permissions.get(codename="delete_matter"),
        ]
    )
    FirmMembership.objects.create(user=limited, firm=firm, role=limited_role)
    client_record.deleted_at = matter.deleted_at = timezone.now()
    client_record.save(update_fields=["deleted_at", "updated_at"])
    matter.save(update_fields=["deleted_at", "updated_at"])

    client.force_login(limited)
    assert client.post(reverse("client_permanent_delete", args=[client_record.id])).status_code == 302
    assert client.post(reverse("matter_permanent_delete", args=[matter.id])).status_code == 302
    assert Client.objects.filter(id=client_record.id).exists()
    assert Matter.objects.filter(id=matter.id).exists()

    client.force_login(admin)
    assert client.post(reverse("client_permanent_delete", args=[client_record.id])).status_code == 302
    assert client.post(reverse("matter_permanent_delete", args=[matter.id])).status_code == 302
    assert not Client.objects.filter(id=client_record.id).exists()
    assert not Matter.objects.filter(id=matter.id).exists()
    assert AuditEvent.objects.filter(action="client_permanently_deleted", firm=firm).exists()
    assert AuditEvent.objects.filter(action="matter_permanently_deleted", firm=firm).exists()


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


def _matter_for_trash(email: str):
    firm, user = _firm_with_user(email, "Firm Administrator")
    client_record = Client.objects.create(
        firm=firm,
        client_number="CL-00001",
        client_type="INDIVIDUAL",
        name=f"{email} Client",
        created_by=user,
    )
    matter = Matter.objects.create(
        firm=firm,
        client=client_record,
        matter_number="GEN/2026/00001",
        title=f"{email} Matter",
        created_by=user,
    )
    return firm, user, matter
