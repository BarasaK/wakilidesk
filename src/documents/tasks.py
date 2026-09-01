from __future__ import annotations

from celery import shared_task
from django.db import transaction

from documents.models import DocumentVersion
from documents.storage import private_storage_path
from notifications.services import notify_user


@shared_task
def extract_text_for_version(version_id: str) -> str:
    version = (
        DocumentVersion.objects.select_related("document", "document__firm", "uploaded_by")
        .filter(id=version_id)
        .first()
    )
    if version is None:
        return "missing"

    with transaction.atomic():
        version.ocr_status = DocumentVersion.OCRStatus.PROCESSING
        version.save(update_fields=["ocr_status"])

    try:
        extracted_text = _extract_text(version)
    except Exception as exc:
        version.ocr_status = DocumentVersion.OCRStatus.FAILED
        version.save(update_fields=["ocr_status"])
        if version.uploaded_by_id:
            notify_user(
                firm=version.document.firm,
                recipient=version.uploaded_by,
                title="Document processing failed",
                message=f"Text extraction failed for {version.document.title}.",
                object_type="DocumentVersion",
                object_id=version.id,
            )
        return f"failed: {exc}"

    version.extracted_text = extracted_text
    version.ocr_status = (
        DocumentVersion.OCRStatus.COMPLETED
        if extracted_text
        else DocumentVersion.OCRStatus.NOT_REQUIRED
    )
    version.save(update_fields=["extracted_text", "ocr_status"])
    return version.ocr_status


def _extract_text(version: DocumentVersion) -> str:
    path = private_storage_path(version.storage_key)
    if version.mime_type == "text/plain":
        return path.read_text(encoding="utf-8", errors="ignore")
    if version.mime_type == "application/pdf":
        # PDF/OCR engine integration belongs behind this boundary.
        return ""
    if version.mime_type.startswith("image/"):
        return ""
    return ""
