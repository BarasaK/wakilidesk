import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from accounts.models import User
from clients.models import Client
from documents.models import Document, DocumentCategory
from documents.services import create_document_with_version
from firms.models import Firm, FirmMembership
from firms.services import ensure_default_roles_for_firm
from matters.models import Matter, PracticeArea
from physical_files.models import PhysicalFile, StorageLocation
from search.services import global_search


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_restricted_matter_records_are_hidden_from_unassigned_user(client):
    firm, _admin, _assigned, unassigned, matter, document, physical_file = _confidential_setup()

    client.force_login(unassigned)

    assert client.get(reverse("matter_detail", args=[matter.id])).status_code == 404
    assert client.get(reverse("document_detail", args=[document.id])).status_code == 404
    assert client.get(reverse("document_download", args=[document.id])).status_code == 404
    assert client.get(reverse("physical_file_detail", args=[physical_file.id])).status_code == 404

    results = global_search(firm=firm, user=unassigned, query="confidential")

    assert results["matters"] == []
    assert results["documents"] == []
    assert results["physical_files"] == []


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_assigned_user_can_access_restricted_matter_records(client):
    firm, _admin, assigned, _unassigned, matter, document, physical_file = _confidential_setup()

    client.force_login(assigned)

    assert client.get(reverse("matter_detail", args=[matter.id])).status_code == 200
    assert client.get(reverse("document_detail", args=[document.id])).status_code == 200
    assert client.get(reverse("physical_file_detail", args=[physical_file.id])).status_code == 200

    results = global_search(firm=firm, user=assigned, query="confidential")

    assert [matter] == results["matters"]
    assert [document] == results["documents"]
    assert [physical_file] == results["physical_files"]


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_document_confidentiality_cannot_be_lower_than_matter():
    firm, admin, _assigned, _unassigned, matter, _document, _physical_file = _confidential_setup()
    category = firm.document_categories.get(name="Correspondence")

    with pytest.raises(ValueError, match="cannot be lower"):
        create_document_with_version(
            firm=firm,
            user=admin,
            data={
                "matter": matter,
                "title": "Too Open",
                "document_type": category,
                "document_date": "2026-09-01",
                "reference_number": "OPEN-001",
                "description": "Invalid confidentiality",
                "source": Document.Source.INTERNAL_UPLOAD,
                "confidentiality_level": Document.ConfidentialityLevel.STANDARD,
            },
            uploaded_file=SimpleUploadedFile("open.txt", b"too open", content_type="text/plain"),
        )


def _confidential_setup():
    firm = Firm.objects.create(
        name="Milestone 7 LLP",
        display_name="Milestone 7",
        slug="milestone-7",
        email="admin@milestone7.test",
    )
    roles = ensure_default_roles_for_firm(firm)
    admin = User.objects.create_user("admin@milestone7.test", "StrongPass123!")
    assigned = User.objects.create_user("assigned@milestone7.test", "StrongPass123!")
    unassigned = User.objects.create_user("unassigned@milestone7.test", "StrongPass123!")
    FirmMembership.objects.create(user=admin, firm=firm, role=roles["Firm Administrator"])
    FirmMembership.objects.create(user=assigned, firm=firm, role=roles["Auditor / Read-only"])
    FirmMembership.objects.create(user=unassigned, firm=firm, role=roles["Auditor / Read-only"])
    client = Client.objects.create(
        firm=firm,
        client_number="CL-00001",
        client_type=Client.ClientType.INDIVIDUAL,
        name="Confidential Client",
        created_by=admin,
    )
    practice_area = PracticeArea.objects.create(firm=firm, name="Litigation", code="LIT")
    matter = Matter.objects.create(
        firm=firm,
        client=client,
        matter_number="LIT/2026/00001",
        title="Confidential Claim",
        description="confidential matter text",
        practice_area=practice_area,
        responsible_partner=admin,
        responsible_advocate=assigned,
        confidentiality_level=Matter.ConfidentialityLevel.RESTRICTED,
        created_by=admin,
    )
    category = DocumentCategory.objects.create(firm=firm, name="Correspondence")
    document = create_document_with_version(
        firm=firm,
        user=admin,
        data={
            "matter": matter,
            "title": "Confidential Memo",
            "document_type": category,
            "document_date": "2026-09-01",
            "reference_number": "CONF-001",
            "description": "confidential document text",
            "source": Document.Source.INTERNAL_UPLOAD,
            "confidentiality_level": Document.ConfidentialityLevel.RESTRICTED,
        },
        uploaded_file=SimpleUploadedFile("confidential.txt", b"confidential file text", content_type="text/plain"),
    )
    location = StorageLocation.objects.create(firm=firm, name="Restricted Shelf")
    physical_file = PhysicalFile.objects.create(
        firm=firm,
        matter=matter,
        physical_file_number="PF-CONF-001",
        volume_number=1,
        storage_location=location,
        notes="confidential physical file text",
    )
    return firm, admin, assigned, unassigned, matter, document, physical_file
