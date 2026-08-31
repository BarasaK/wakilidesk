# Milestone 3: Documents and Versioning

## Done

- Added `documents` Django app
- Added firm-owned `DocumentCategory`
- Added `Document` metadata records linked to firm and matter
- Added immutable `DocumentVersion` records
- Added upload flow for first version
- Added upload flow for later versions
- Added private tenant-aware storage keys under `MEDIA_ROOT/private`
- Added checksum, MIME type, file size, original filename, and OCR status metadata
- Added download flow with permission check and audit event
- Added archive/restore flow
- Added category list/create/edit views
- Extended seed data with default document categories and pilot document
- Added tests for upload, versioning, download permissions, archive/restore, and cross-tenant document access

## Local URLs

```text
http://localhost:8000/documents/
http://localhost:8000/documents/upload/
http://localhost:8000/documents/categories/
```

## Notes for Later Hardening

- Replace the local private media writer with an S3/MinIO storage adapter before production document pilots.
- Add malware scanning hook before a file is marked available.
- Add OCR/text extraction Celery tasks after Milestone 4.
