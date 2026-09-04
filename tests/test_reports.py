import io
import zipfile
from datetime import datetime, timedelta

import pytest
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from clients.models import Client
from diary.models import DiaryEvent
from documents.models import Document, DocumentCategory
from documents.services import create_document_with_version
from firms.models import Firm, FirmMembership
from firms.services import ensure_default_roles_for_firm
from matters.models import Matter, PracticeArea
from physical_files.models import PhysicalFile, StorageLocation


@pytest.mark.django_db
def test_reports_index_and_csv_export_include_accessible_clients(client):
    _firm, admin, client_record, _matter, _restricted_matter, _finance, _auditor = _setup()
    client.force_login(admin)

    index_response = client.get(reverse("report_index"))
    export_response = client.get(
        reverse("report_export"),
        {"entity": "clients", "export_format": "csv"},
    )

    assert index_response.status_code == 200
    assert b"Reports" in index_response.content
    assert export_response.status_code == 200
    assert export_response["Content-Type"] == "text/csv"
    assert 'filename="clients-report.csv"' in export_response["Content-Disposition"]
    assert client_record.name.encode() in export_response.content


@pytest.mark.django_db
def test_xlsx_export_is_valid_spreadsheet_archive(client):
    _firm, admin, _client_record, matter, _restricted_matter, _finance, _auditor = _setup()
    client.force_login(admin)

    response = client.get(
        reverse("report_export"),
        {"entity": "matters", "export_format": "xlsx"},
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        sheet_xml = archive.read("xl/worksheets/sheet1.xml")
    assert matter.title.encode() in sheet_xml


@pytest.mark.django_db
def test_pdf_export_includes_firm_logo_when_available(client, tmp_path, settings):
    settings.MEDIA_ROOT = tmp_path
    firm, admin, _client_record, _matter, _restricted_matter, _finance, _auditor = _setup()
    firm.logo.save("logo.png", ContentFile(_one_pixel_png()), save=True)
    DiaryEvent.objects.create(
        firm=firm,
        title="PDF hearing",
        event_type=DiaryEvent.EventType.HEARING,
        start_at=timezone.make_aware(datetime(2026, 9, 12, 9, 0)),
        assigned_to=admin,
        created_by=admin,
    )
    client.force_login(admin)

    response = client.get(
        reverse("report_export"),
        {"entity": "diary_events", "export_format": "pdf"},
    )

    assert response.status_code == 200
    assert response["Content-Type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert b"/Subtype /Image" in response.content
    assert b"Diary Events Report" in response.content


@pytest.mark.django_db
def test_report_nav_and_export_are_hidden_for_roles_without_view_permissions(client):
    _firm, _admin, _client_record, _matter, _restricted_matter, finance, _auditor = _setup(include_finance=True)
    client.force_login(finance)

    index_response = client.get(reverse("report_index"))
    export_response = client.get(
        reverse("report_export"),
        {"entity": "clients", "export_format": "csv"},
    )

    assert index_response.status_code == 200
    assert b"No reports are available for your current role." in index_response.content
    assert b'href="/reports/"' not in index_response.content
    assert export_response.status_code == 403


@pytest.mark.django_db
def test_matter_report_hides_restricted_matters_from_unassigned_user(client):
    _firm, _admin, _client_record, visible_matter, restricted_matter, _finance, auditor = _setup(
        include_finance=True,
        include_auditor=True,
    )
    client.force_login(auditor)

    response = client.get(
        reverse("report_export"),
        {"entity": "matters", "export_format": "csv"},
    )

    assert response.status_code == 200
    assert visible_matter.title.encode() in response.content
    assert restricted_matter.title.encode() not in response.content


def _setup(include_finance=False, include_auditor=False):
    firm = Firm.objects.create(
        name="Reports LLP",
        display_name="Reports Firm",
        slug=f"reports-firm-{User.objects.count()}",
        email="admin@reports.test",
    )
    roles = ensure_default_roles_for_firm(firm)
    admin = User.objects.create_user(f"admin{User.objects.count()}@reports.test", "StrongPass123!")
    assigned = User.objects.create_user(f"assigned{User.objects.count()}@reports.test", "StrongPass123!")
    FirmMembership.objects.create(user=admin, firm=firm, role=roles["Firm Administrator"])
    FirmMembership.objects.create(user=assigned, firm=firm, role=roles["Auditor / Read-only"])
    client_record = Client.objects.create(
        firm=firm,
        client_number="CL-00001",
        client_type=Client.ClientType.INDIVIDUAL,
        name="Reports Client",
        email="client@reports.test",
        phone="+254700000000",
        created_by=admin,
    )
    practice_area = PracticeArea.objects.create(firm=firm, name="Litigation", code="LIT")
    matter = Matter.objects.create(
        firm=firm,
        client=client_record,
        matter_number="LIT/2026/00001",
        title="Open Reports Matter",
        practice_area=practice_area,
        responsible_partner=admin,
        responsible_advocate=assigned,
        created_by=admin,
    )
    restricted_matter = Matter.objects.create(
        firm=firm,
        client=client_record,
        matter_number="LIT/2026/00002",
        title="Restricted Reports Matter",
        practice_area=practice_area,
        responsible_partner=admin,
        responsible_advocate=assigned,
        confidentiality_level=Matter.ConfidentialityLevel.RESTRICTED,
        created_by=admin,
    )
    category = DocumentCategory.objects.create(firm=firm, name="Pleadings")
    create_document_with_version(
        firm=firm,
        user=admin,
        data={
            "matter": matter,
            "title": "Reports Filing",
            "document_type": category,
            "document_date": timezone.localdate(),
            "reference_number": "RPT-001",
            "description": "Reports document",
            "source": Document.Source.INTERNAL_UPLOAD,
            "confidentiality_level": Document.ConfidentialityLevel.STANDARD,
        },
        uploaded_file=SimpleUploadedFile("report.txt", b"report document", content_type="text/plain"),
    )
    location = StorageLocation.objects.create(firm=firm, name="Main Registry")
    PhysicalFile.objects.create(
        firm=firm,
        matter=matter,
        physical_file_number="PF-00001",
        volume_number=1,
        storage_location=location,
    )
    DiaryEvent.objects.create(
        firm=firm,
        matter=matter,
        title="Reports Mention",
        event_type=DiaryEvent.EventType.MENTION,
        start_at=timezone.now() + timedelta(days=3),
        assigned_to=admin,
        created_by=admin,
    )
    finance = None
    if include_finance:
        finance = User.objects.create_user(f"finance{User.objects.count()}@reports.test", "StrongPass123!")
        FirmMembership.objects.create(user=finance, firm=firm, role=roles["Finance"])
    auditor = None
    if include_auditor:
        auditor = User.objects.create_user(f"auditor{User.objects.count()}@reports.test", "StrongPass123!")
        FirmMembership.objects.create(user=auditor, firm=firm, role=roles["Auditor / Read-only"])
    return firm, admin, client_record, matter, restricted_matter, finance, auditor


def _one_pixel_png():
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), color=(15, 118, 110)).save(buffer, format="PNG")
    return buffer.getvalue()
