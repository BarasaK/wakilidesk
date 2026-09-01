import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from accounts.models import User
from clients.models import Client
from documents.models import DocumentCategory, DocumentVersion
from documents.services import create_document_with_version
from documents.tasks import extract_text_for_version
from firms.models import Firm, FirmMembership
from firms.services import ensure_default_roles_for_firm
from matters.models import Matter


@pytest.mark.django_db
def test_text_extraction_task_extracts_plain_text():
    firm, user, matter, category = _setup("admin@firm.test")
    document = create_document_with_version(
        firm=firm,
        user=user,
        data={
            "matter": matter,
            "title": "Plain Text Filing",
            "document_type": category,
            "document_date": "2026-09-01",
            "reference_number": "TXT-001",
            "description": "Text extraction test",
            "source": "INTERNAL_UPLOAD",
            "confidentiality_level": "STANDARD",
        },
        uploaded_file=SimpleUploadedFile("filing.txt", b"searchable legal text", content_type="text/plain"),
    )
    version = document.current_version
    version.extracted_text = ""
    version.ocr_status = DocumentVersion.OCRStatus.PENDING
    version.save()

    result = extract_text_for_version(str(version.id))
    version.refresh_from_db()

    assert result == DocumentVersion.OCRStatus.COMPLETED
    assert version.extracted_text == "searchable legal text"


@pytest.mark.django_db
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
def test_reprocess_action_runs_task_for_authorized_user(client):
    firm, user, matter, category = _setup("admin@firm.test")
    document = create_document_with_version(
        firm=firm,
        user=user,
        data={
            "matter": matter,
            "title": "Reprocess Filing",
            "document_type": category,
            "document_date": "2026-09-01",
            "reference_number": "TXT-002",
            "description": "Text extraction test",
            "source": "INTERNAL_UPLOAD",
            "confidentiality_level": "STANDARD",
        },
        uploaded_file=SimpleUploadedFile("reprocess.txt", b"reprocessed legal text", content_type="text/plain"),
    )

    client.force_login(user)
    response = client.post(reverse("document_reprocess_ocr", args=[document.id]))
    document.current_version.refresh_from_db()

    assert response.status_code == 302
    assert document.current_version.ocr_status == DocumentVersion.OCRStatus.COMPLETED
    assert "reprocessed legal text" in document.current_version.extracted_text


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
    category = DocumentCategory.objects.create(firm=firm, name="Correspondence")
    return firm, user, matter, category
