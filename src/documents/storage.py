from __future__ import annotations

import hashlib
import mimetypes
import uuid
from pathlib import Path

from django.conf import settings


ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/tiff",
    "text/plain",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def save_uploaded_document_file(*, firm, matter, document, version_id, uploaded_file):
    mime_type = (
        getattr(uploaded_file, "content_type", None)
        or mimetypes.guess_type(uploaded_file.name)[0]
        or "application/octet-stream"
    )
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported file type: {mime_type}")

    suffix = Path(uploaded_file.name).suffix.lower()
    storage_key = (
        f"firms/{firm.id}/matters/{matter.id}/documents/{document.id}/"
        f"versions/{version_id}/{uuid.uuid4().hex}{suffix}"
    )
    target_path = Path(settings.MEDIA_ROOT) / "private" / storage_key
    target_path.parent.mkdir(parents=True, exist_ok=True)

    checksum = hashlib.sha256()
    size = 0
    with target_path.open("wb") as destination:
        for chunk in uploaded_file.chunks():
            size += len(chunk)
            checksum.update(chunk)
            destination.write(chunk)

    return {
        "storage_key": storage_key,
        "mime_type": mime_type,
        "file_size": size,
        "checksum": checksum.hexdigest(),
    }


def private_storage_path(storage_key: str) -> Path:
    root = (Path(settings.MEDIA_ROOT) / "private").resolve()
    path = (root / storage_key).resolve()
    if root not in path.parents and path != root:
        raise ValueError("Invalid storage key")
    return path
