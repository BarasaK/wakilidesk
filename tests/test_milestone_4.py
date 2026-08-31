from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from audit.models import AuditEvent
from clients.models import Client
from firms.models import Firm, FirmMembership
from firms.services import ensure_default_roles_for_firm
from matters.models import Matter
from physical_files.models import FileCheckout, PhysicalFile, StorageLocation
from physical_files.services import checkout_physical_file


@pytest.mark.django_db
def test_firm_admin_can_register_checkout_and_checkin_file(client):
    firm, user, matter, location = _setup("admin@firm.test", "Firm Administrator")

    client.force_login(user)
    create_response = client.post(
        reverse("physical_file_create"),
        {
            "matter": matter.id,
            "physical_file_number": "PF-001",
            "volume_number": 1,
            "storage_location": location.id,
            "status": "IN_STORAGE",
            "digitisation_status": "NOT_STARTED",
            "barcode_or_qr_code": "",
            "notes": "",
        },
    )

    assert create_response.status_code == 302
    physical_file = PhysicalFile.objects.get(physical_file_number="PF-001")
    assert physical_file.firm == firm

    checkout_response = client.post(
        reverse("physical_file_checkout", args=[physical_file.id]),
        {
            "checked_out_to": user.id,
            "checked_out_to_name": "",
            "expected_return_at": "2026-09-02T10:00",
            "purpose": "Court attendance",
            "notes": "",
        },
    )

    assert checkout_response.status_code == 302
    physical_file.refresh_from_db()
    assert physical_file.status == PhysicalFile.Status.CHECKED_OUT
    assert physical_file.checkouts.filter(returned_at__isnull=True).count() == 1

    checkin_response = client.post(
        reverse("physical_file_checkin", args=[physical_file.id]),
        {"notes": "Returned by clerk"},
    )

    assert checkin_response.status_code == 302
    physical_file.refresh_from_db()
    assert physical_file.status == PhysicalFile.Status.IN_STORAGE
    assert physical_file.checkouts.filter(returned_at__isnull=False).count() == 1
    assert AuditEvent.objects.filter(action="physical_file_checked_out", firm=firm).exists()
    assert AuditEvent.objects.filter(action="physical_file_checked_in", firm=firm).exists()


@pytest.mark.django_db
def test_duplicate_checkout_is_prevented():
    firm, user, matter, location = _setup("admin@firm.test", "Firm Administrator")
    physical_file = PhysicalFile.objects.create(
        firm=firm,
        matter=matter,
        physical_file_number="PF-001",
        volume_number=1,
        storage_location=location,
    )
    checkout_physical_file(
        physical_file=physical_file,
        firm=firm,
        user=user,
        data={
            "checked_out_to": user,
            "checked_out_to_name": "",
            "expected_return_at": timezone.now() + timedelta(days=1),
            "purpose": "Review",
            "notes": "",
        },
    )

    with pytest.raises(ValueError):
        checkout_physical_file(
            physical_file=physical_file,
            firm=firm,
            user=user,
            data={
                "checked_out_to": user,
                "checked_out_to_name": "",
                "expected_return_at": timezone.now() + timedelta(days=1),
                "purpose": "Second review",
                "notes": "",
            },
        )


@pytest.mark.django_db
def test_user_cannot_view_other_firm_physical_file(client):
    _firm_a, user_a, _matter_a, _location_a = _setup("admin@firma.test", "Firm Administrator")
    firm_b, _user_b, matter_b, location_b = _setup("admin@firmb.test", "Firm Administrator")
    physical_file_b = PhysicalFile.objects.create(
        firm=firm_b,
        matter=matter_b,
        physical_file_number="PF-B-001",
        volume_number=1,
        storage_location=location_b,
    )

    client.force_login(user_a)
    response = client.get(reverse("physical_file_detail", args=[physical_file_b.id]))

    assert response.status_code == 404


@pytest.mark.django_db
def test_overdue_checkout_is_listed(client):
    firm, user, matter, location = _setup("admin@firm.test", "Firm Administrator")
    physical_file = PhysicalFile.objects.create(
        firm=firm,
        matter=matter,
        physical_file_number="PF-001",
        volume_number=1,
        storage_location=location,
        status=PhysicalFile.Status.CHECKED_OUT,
    )
    FileCheckout.objects.create(
        firm=firm,
        physical_file=physical_file,
        checked_out_by=user,
        checked_out_to=user,
        expected_return_at=timezone.now() - timedelta(days=1),
    )

    client.force_login(user)
    response = client.get(reverse("physical_file_list"))

    assert response.status_code == 200
    assert b"PF-001" in response.content


def _setup(email: str, role_name: str):
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
    client = Client.objects.create(
        firm=firm,
        client_number="CL-00001",
        client_type="INDIVIDUAL",
        name=f"{email} Client",
        created_by=user,
    )
    matter = Matter.objects.create(
        firm=firm,
        client=client,
        matter_number="GEN/2026/00001",
        title=f"{email} Matter",
        created_by=user,
    )
    office = StorageLocation.objects.create(firm=firm, name="Nairobi Office")
    location = StorageLocation.objects.create(firm=firm, parent=office, name="Shelf 01")
    return firm, user, matter, location
