# Milestone 5: Workflow Foundations, Search, Dashboard, Notifications

## Done

- Added `notifications` Django app
- Added in-app `Notification` model and service
- Added notification list and mark-read views
- Added `search` Django app
- Added tenant-scoped search service across clients, matters, matter parties, documents, and physical files
- Added search page
- Added `DigitisationReview` records for historical file quality control
- Added digitisation list and review form
- Added dashboard metrics from real client/matter/document/physical file data
- Added tests for tenant-scoped search, dashboard metrics, notifications, and digitisation review status changes

## Local URLs

```text
http://localhost:8000/search/
http://localhost:8000/notifications/
http://localhost:8000/physical-files/digitisation/
```

## Notes for Next Work

- Upgrade search to PostgreSQL full-text indexes.
- Add Celery jobs for OCR/text extraction and failed-job reprocessing.
- Add in-app notification creation for overdue file and failed processing events.
- Add richer dashboard cards and recent activity lists.
