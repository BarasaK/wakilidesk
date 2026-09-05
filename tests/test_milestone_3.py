import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from accounts.models import User
from audit.models import AuditEvent
from clients.models import Client
from documents.models import Document, DocumentCategory
from firms.models import Firm, FirmMembership, Permission, Role
from firms.services import ensure_default_roles_for_firm
from matters.models import Matter, PracticeArea


@pytest.mark.django_db
def test_firm_admin_can_upload_document_and_new_version(client):
    firm, user, matter, category = _matter_setup("admin@firm.test", "Firm Administrator")

    client.force_login(user)
    response = client.post(
        reverse("document_upload"),
        {
            "matter": matter.id,
            "title": "Client Instructions",
            "document_type": category.id,
            "document_date": "2026-08-31",
            "reference_number": "REF-001",
            "description": "Initial instructions",
            "source": "INTERNAL_UPLOAD",
            "confidentiality_level": "STANDARD",
            "file": SimpleUploadedFile("instructions.txt", b"first version", content_type="text/plain"),
        },
    )

    assert response.status_code == 302
    document = Document.objects.get(title="Client Instructions")
    assert document.firm == firm
    assert document.current_version.version_number == 1
    assert document.current_version.checksum
    assert f"firms/{firm.id}/matters/{matter.id}/documents/{document.id}/versions/" in document.current_version.storage_key

    version_response = client.post(
        reverse("document_version_upload", args=[document.id]),
        {"file": SimpleUploadedFile("instructions-v2.txt", b"second version", content_type="text/plain")},
    )

    assert version_response.status_code == 302
    document.refresh_from_db()
    assert document.versions.count() == 2
    assert document.current_version.version_number == 2
    assert AuditEvent.objects.filter(action="document_uploaded", firm=firm).exists()
    assert AuditEvent.objects.filter(action="document_version_created", firm=firm).exists()


@pytest.mark.django_db
def test_user_cannot_view_or_download_other_firm_document(client):
    firm_a, user_a, _matter_a, _category_a = _matter_setup("admin@firma.test", "Firm Administrator")
    firm_b, user_b, matter_b, category_b = _matter_setup("admin@firmb.test", "Firm Administrator")
    document = _create_document(firm_b, user_b, matter_b, category_b)

    client.force_login(user_a)

    assert client.get(reverse("document_detail", args=[document.id])).status_code == 404
    assert client.get(reverse("document_download", args=[document.id])).status_code == 404
    assert firm_a.documents.count() == 0


@pytest.mark.django_db
def test_user_without_download_permission_cannot_download(client):
    firm, admin, matter, category = _matter_setup("admin@firm.test", "Firm Administrator")
    document = _create_document(firm, admin, matter, category)
    secretary = User.objects.create_user("secretary@firm.test", "StrongPass123!")
    secretary_role = firm.roles.get(name="Secretary")
    FirmMembership.objects.create(user=secretary, firm=firm, role=secretary_role)

    client.force_login(secretary)
    response = client.get(reverse("document_download", args=[document.id]))

    assert response.status_code == 403


@pytest.mark.django_db
def test_archive_and_restore_document(client):
    firm, admin, matter, category = _matter_setup("admin@firm.test", "Firm Administrator")
    document = _create_document(firm, admin, matter, category)

    client.force_login(admin)
    archive_response = client.post(reverse("document_archive", args=[document.id]))
    document.refresh_from_db()

    assert archive_response.status_code == 302
    assert document.archived_at is not None

    restore_response = client.post(reverse("document_restore", args=[document.id]))
    document.refresh_from_db()

    assert restore_response.status_code == 302
    assert document.archived_at is None


@pytest.mark.django_db
def test_matter_detail_lists_linked_documents(client):
    firm, admin, matter, category = _matter_setup("admin@matterdocs.test", "Firm Administrator")
    document = _create_document(firm, admin, matter, category)

    client.force_login(admin)
    response = client.get(reverse("matter_detail", args=[matter.id]))

    assert response.status_code == 200
    assert b"<h3>Documents</h3>" in response.content
    assert document.title.encode() in response.content
    assert reverse("document_detail", args=[document.id]).encode() in response.content
    assert f'{reverse("document_upload")}?matter={matter.id}'.encode() in response.content


@pytest.mark.django_db
def test_document_upload_from_matter_prefills_matter(client):
    _firm, admin, matter, _category = _matter_setup("admin@prefill.test", "Firm Administrator")

    client.force_login(admin)
    response = client.get(reverse("document_upload"), {"matter": matter.id})

    assert response.status_code == 200
    assert f'<option value="{matter.id}" selected>'.encode() in response.content


@pytest.mark.django_db
def test_matter_detail_hides_documents_for_role_without_document_permission(client):
    firm, admin, matter, category = _matter_setup("admin@matteronly.test", "Firm Administrator")
    document = _create_document(firm, admin, matter, category)
    role = Role.objects.create(firm=firm, name="Matter only")
    role.permissions.set([Permission.objects.get(codename="view_matter")])
    matter_only_user = User.objects.create_user("matteronly@matteronly.test", "StrongPass123!")
    FirmMembership.objects.create(user=matter_only_user, firm=firm, role=role)

    client.force_login(matter_only_user)
    response = client.get(reverse("matter_detail", args=[matter.id]))

    assert response.status_code == 200
    assert document.title.encode() not in response.content
    assert b"<h3>Documents</h3>" not in response.content


def _matter_setup(email: str, role_name: str):
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
    area = PracticeArea.objects.create(firm=firm, name="Litigation", code="LIT")
    matter = Matter.objects.create(
        firm=firm,
        client=client,
        matter_number="LIT/2026/00001",
        title=f"{email} Matter",
        practice_area=area,
        created_by=user,
    )
    category = DocumentCategory.objects.create(firm=firm, name="Pleadings")
    return firm, user, matter, category


def _create_document(firm, user, matter, category):
    from documents.services import create_document_with_version

    return create_document_with_version(
        firm=firm,
        user=user,
        data={
            "matter": matter,
            "title": f"{firm.slug} Document",
            "document_type": category,
            "document_date": "2026-08-31",
            "reference_number": "REF-001",
            "description": "Test document",
            "source": "INTERNAL_UPLOAD",
            "confidentiality_level": "STANDARD",
        },
        uploaded_file=SimpleUploadedFile("document.txt", b"content", content_type="text/plain"),
    )
