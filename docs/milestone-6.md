# Milestone 6: OCR and Operational Hardening

## Done

- Added Celery settings from `REDIS_URL`
- Added `CELERY_TASK_ALWAYS_EAGER` configuration for tests/local overrides
- Added document text extraction task boundary
- Added plain-text extraction implementation
- Added PDF/image OCR placeholders behind the same task boundary
- Added failed-processing notification hook
- Added document reprocess action
- Added tests for text extraction and authorized reprocessing
- Added deployment and backup notes

## Local URLs

```text
http://localhost:8000/documents/
```

Open a document detail page and use `Reprocess text` to queue/re-run extraction for the current version.

## Notes for Future Work

- Integrate a real PDF parser such as `pypdf`.
- Integrate OCR for scanned PDFs/images, likely Tesseract or a cloud OCR provider.
- Store production documents in S3-compatible object storage with signed download URLs.
- Add malware scanning before files become available for download.
