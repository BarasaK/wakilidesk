from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from clients.models import Client
from documents.models import DocumentCategory
from documents.services import create_document_with_version
from django.core.files.uploadedfile import SimpleUploadedFile
from firms.models import Firm, FirmMembership
from firms.services import ensure_default_roles_for_firm
from matters.models import Matter
from notifications.models import Notification
from notifications.services import notify_user
from physical_files.models import FileCheckout, PhysicalFile, StorageLocation
from search.services import global_search


@pytest.mark.django_db
def test_global_search_is_tenant_scoped(client):
    firm_a, user_a, matter_a, _file_a, category_a = _setup("admin@firma.test")
    firm_b, user_b, matter_b, file_b, category_b = _setup("admin@firmb.test")
    create_document_with_version(
        firm=firm_b,
        user=user_b,
        data={
            "matter": matter_b,
            "title": "Hidden Contract",
            "document_type": category_b,
            "document_date": "2026-09-01",
            "reference_number": "SECRET-REF",
            "description": "Cross tenant hidden",
            "source": "INTERNAL_UPLOAD",
            "confidentiality_level": "STANDARD",
        },
        uploaded_file=SimpleUploadedFile("hidden.txt", b"hidden searchable text", content_type="text/plain"),
    )

    results = global_search(firm=firm_a, user=user_a, query="Hidden")

    assert results["documents"] == []
    assert results["physical_files"] == []
    assert file_b.firm == firm_b
    assert matter_a.firm == firm_a


@pytest.mark.django_db
def test_search_page_returns_current_firm_results(client):
    firm, user, matter, physical_file, category = _setup("admin@firm.test")
    create_document_with_version(
        firm=firm,
        user=user,
        data={
            "matter": matter,
            "title": "Client Instructions",
            "document_type": category,
            "document_date": "2026-09-01",
            "reference_number": "REF-SEARCH",
            "description": "Searchable document",
            "source": "INTERNAL_UPLOAD",
            "confidentiality_level": "STANDARD",
        },
        uploaded_file=SimpleUploadedFile("search.txt", b"searchable text", content_type="text/plain"),
    )

    client.force_login(user)
    response = client.get(reverse("global_search"), {"q": "Client"})

    assert response.status_code == 200
    assert b"Client Instructions" in response.content
    assert physical_file.physical_file_number.encode() in response.content


@pytest.mark.django_db
def test_digitisation_review_updates_status_and_audit(client):
    firm, user, _matter, physical_file, _category = _setup("admin@firm.test")

    client.force_login(user)
    response = client.post(
        reverse("digitisation_review_create", args=[physical_file.id]),
        {
            "scanner_operator": user.id,
            "scan_date": "2026-09-01",
            "reviewer": user.id,
            "review_date": "2026-09-01",
            "missing_page_flag": "",
            "poor_quality_flag": "",
            "rescan_required": "",
            "completion_confirmed": "on",
            "notes": "Complete",
        },
    )

    assert response.status_code == 302
    physical_file.refresh_from_db()
    assert physical_file.digitisation_status == PhysicalFile.DigitisationStatus.COMPLETED
    assert firm.digitisation_reviews.count() == 1


@pytest.mark.django_db
def test_notification_list_and_mark_read(client):
    firm, user, _matter, _physical_file, _category = _setup("admin@firm.test")
    notification = notify_user(
        firm=firm,
        recipient=user,
        title="File overdue",
        message="PF-001 is overdue.",
    )

    client.force_login(user)
    response = client.get(reverse("notification_list"))

    assert response.status_code == 200
    assert b"File overdue" in response.content

    read_response = client.post(reverse("notification_mark_read", args=[notification.id]))
    notification.refresh_from_db()

    assert read_response.status_code == 302
    assert notification.status == Notification.Status.READ


@pytest.mark.django_db
def test_dashboard_metrics_render(client):
    firm, user, _matter, physical_file, _category = _setup("admin@firm.test")
    FileCheckout.objects.create(
        firm=firm,
        physical_file=physical_file,
        checked_out_by=user,
        checked_out_to=user,
        expected_return_at=timezone.now() - timedelta(days=1),
    )
    physical_file.status = PhysicalFile.Status.CHECKED_OUT
    physical_file.save()

    client.force_login(user)
    response = client.get(reverse("dashboard"))

    assert response.status_code == 200
    assert b"Filing Metrics" in response.content
    assert b"Clients" in response.content
    assert b">1</strong>" in response.content
    assert b"Files awaiting return" in response.content


def _setup(email: str):
    slug = email.replace("@", "-").replace(".", "-")
    firm = Firm.objects.create(
        name=f"{email} LLP",
        display_name=f"{email} Firm",
        slug=slug,
        email=email,
    )
    roles = ensure_default_roles_for_firm(firm)
    user = User.objects.create_user(email, "StrongPass123!")
    FirmMembership.objects.create(user=user, firm=firm, role=roles["Firm Administrator"])
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
    location = StorageLocation.objects.create(firm=firm, name="Shelf 01")
    physical_file = PhysicalFile.objects.create(
        firm=firm,
        matter=matter,
        physical_file_number=f"PF-{slug}",
        volume_number=1,
        storage_location=location,
        notes="Client storage file",
    )
    category = DocumentCategory.objects.create(firm=firm, name="Correspondence")
    return firm, user, matter, physical_file, category
