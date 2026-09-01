from __future__ import annotations

from django.db import transaction
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone

from audit.services import record_audit_event
from documents.models import Document, DocumentCategory, DocumentVersion
from documents.storage import private_storage_path, save_uploaded_document_file
from matters.services import matters_visible_to_user, require_matter_access


def documents_for_firm(firm):
    return Document.objects.filter(firm=firm, deleted_at__isnull=True).select_related(
        "matter", "document_type", "current_version"
    )


def documents_visible_to_user(*, firm, user):
    return documents_for_firm(firm).filter(matter__in=matters_visible_to_user(firm=firm, user=user))


def get_document_for_firm_or_404(firm, document_id):
    return get_object_or_404(Document, id=document_id, firm=firm, deleted_at__isnull=True)


def get_document_for_user_or_404(*, firm, user, document_id):
    return get_object_or_404(documents_visible_to_user(firm=firm, user=user), id=document_id)


@transaction.atomic
def create_document_with_version(*, firm, user, data, uploaded_file, request=None) -> Document:
    data = dict(data)
    data.pop("file", None)
    matter = data["matter"]
    category = data["document_type"]
    if matter.firm_id != firm.id:
        raise ValueError("Matter does not belong to the current firm.")
    if category.firm_id != firm.id:
        raise ValueError("Document category does not belong to the current firm.")
    require_matter_access(matter=matter, firm=firm, user=user)
    validate_document_confidentiality(matter=matter, document_level=data["confidentiality_level"])

    document = Document.objects.create(firm=firm, uploaded_by=user, **data)
    version = create_document_version(
        document=document,
        firm=firm,
        user=user,
        uploaded_file=uploaded_file,
        request=request,
        audit=False,
    )
    document.current_version = version
    document.save(update_fields=["current_version", "updated_at"])
    record_audit_event(
        request=request,
        firm=firm,
        user=user,
        action="document_uploaded",
        object_type="Document",
        object_id=document.id,
    )
    schedule_text_extraction(version)
    return document


@transaction.atomic
def create_document_version(*, document, firm, user, uploaded_file, request=None, audit=True) -> DocumentVersion:
    if document.firm_id != firm.id:
        raise ValueError("Document does not belong to the current firm.")
    require_matter_access(matter=document.matter, firm=firm, user=user)
    next_number = document.versions.count() + 1
    version_id = DocumentVersion._meta.get_field("id").get_default()
    storage = save_uploaded_document_file(
        firm=firm,
        matter=document.matter,
        document=document,
        version_id=version_id,
        uploaded_file=uploaded_file,
    )
    version = DocumentVersion.objects.create(
        id=version_id,
        document=document,
        version_number=next_number,
        original_filename=uploaded_file.name,
        uploaded_by=user,
        **storage,
    )
    document.current_version = version
    document.save(update_fields=["current_version", "updated_at"])
    if audit:
        record_audit_event(
            request=request,
            firm=firm,
            user=user,
            action="document_version_created",
            object_type="DocumentVersion",
            object_id=version.id,
        )
    schedule_text_extraction(version)
    return version


@transaction.atomic
def update_document_metadata(*, document, firm, data, request=None) -> Document:
    category = data["document_type"]
    if category.firm_id != firm.id:
        raise ValueError("Document category does not belong to the current firm.")
    validate_document_confidentiality(matter=document.matter, document_level=data["confidentiality_level"])
    for field, value in data.items():
        setattr(document, field, value)
    document.save()
    record_audit_event(
        request=request,
        firm=firm,
        action="document_metadata_updated",
        object_type="Document",
        object_id=document.id,
    )
    return document


def archive_document(*, document, firm, request=None):
    document.archived_at = timezone.now()
    document.save(update_fields=["archived_at", "updated_at"])
    record_audit_event(
        request=request,
        firm=firm,
        action="document_archived",
        object_type="Document",
        object_id=document.id,
    )


def restore_document(*, document, firm, request=None):
    document.archived_at = None
    document.save(update_fields=["archived_at", "updated_at"])
    record_audit_event(
        request=request,
        firm=firm,
        action="document_restored",
        object_type="Document",
        object_id=document.id,
    )


def document_file_response(*, document, firm, request=None):
    version = document.current_version
    if version is None:
        raise ValueError("Document has no current version.")
    path = private_storage_path(version.storage_key)
    record_audit_event(
        request=request,
        firm=firm,
        action="document_downloaded",
        object_type="Document",
        object_id=document.id,
    )
    return FileResponse(path.open("rb"), as_attachment=True, filename=version.original_filename)


def validate_document_confidentiality(*, matter, document_level: str) -> None:
    matter_rank = _CONFIDENTIALITY_RANK[matter.confidentiality_level]
    document_rank = _CONFIDENTIALITY_RANK[document_level]
    if document_rank < matter_rank:
        raise ValueError("Document confidentiality cannot be lower than the matter confidentiality.")


def ensure_default_document_categories(firm) -> list[DocumentCategory]:
    names = [
        "Client Instructions",
        "Pleadings",
        "Court Documents",
        "Correspondence",
        "Evidence",
        "Agreements",
        "Research",
        "Billing",
        "Internal Notes",
        "Other",
    ]
    categories = []
    for name in names:
        category, _ = DocumentCategory.objects.get_or_create(
            firm=firm,
            name=name,
            defaults={"is_active": True},
        )
        categories.append(category)
    return categories


def schedule_text_extraction(version: DocumentVersion) -> None:
    from documents.tasks import extract_text_for_version

    extract_text_for_version.delay(str(version.id))


_CONFIDENTIALITY_RANK = {
    Document.ConfidentialityLevel.STANDARD: 0,
    Document.ConfidentialityLevel.RESTRICTED: 1,
    Document.ConfidentialityLevel.PARTNER_ONLY: 2,
    Document.ConfidentialityLevel.CUSTOM: 3,
}
