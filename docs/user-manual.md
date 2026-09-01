# wakiliDesk User Manual

This manual covers the current MVP workflow for local development and pilot demos.

## Getting started

Start the application stack, apply migrations, and create demo data:

```powershell
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_dev
```

Open the application at http://localhost:8000/accounts/login/.

All seeded users use this password:

```text
ChangeMe123!
```

## Seeded law firms

The seed command creates three demo law firms:

- Amani Advocates
- Baraka Legal
- Kosmas Law

Kosmas Law accounts:

```text
admin@kosmaslaw.test
partner@kosmaslaw.test
advocate1@kosmaslaw.test
advocate2@kosmaslaw.test
secretary@kosmaslaw.test
clerk@kosmaslaw.test
```

Each firm receives users, roles, practice areas, document categories, storage locations, clients, matters, matter parties, documents, physical files, and an in-app notification.

## Dashboard

After login, the dashboard shows the current firm's working totals, including clients, matters, documents, physical files, overdue checkouts, digitisation review items, and unread notifications. Use the navigation links to move between records.

## Clients

Use **Clients** to view and create client records. Each client belongs to the active firm and receives a firm-scoped client number. Individual and organisation clients can both be recorded.

## Matters

Use **Matters** to create legal files linked to a client and practice area. Matter numbers are generated per firm, year, and practice area. Matter parties can be added from a matter detail page.

Restricted and partner-only matters are visible only to users with confidential-matter permission or users assigned as the responsible partner or advocate.

## Documents

Use **Documents** to upload matter documents, record metadata, and download stored versions. Supported local MVP file types include plain text, PDF, images, Microsoft Word, and DOCX. Documents can be archived and restored without deleting their stored versions.

A document cannot be saved with a confidentiality level lower than its linked matter.

## Text extraction

Plain text uploads are processed by the Celery task boundary added in Milestone 6. Use the document detail page to reprocess text extraction when needed. Failed processing creates an in-app notification for the uploading user.

## Physical files

Use **Physical files** to register paper files, assign storage locations, track digitisation status, and record barcode or QR references. Physical files are linked to matters.

## Checkout and check-in

Open a physical file detail page to check a file out to a user or named recipient. A checked-out file is marked unavailable until it is checked in. Overdue checkouts are shown in the physical files area and dashboard metrics.

## Digitisation

Use **Digitisation** to record scan and quality review status for physical files. Review records capture scanner, reviewer, quality flags, rescan requirements, completion confirmation, and notes.

## Search

Use **Search** to search across clients, matters, documents, and physical files within the active firm. Extracted document text is included when available.

## Notifications

Use **Notifications** to see unread and read in-app messages. Notifications are firm-scoped and user-specific.

## Firm administration

Firm administrators can manage firm profile settings, users, invitations, roles, and permissions. Role changes affect access within that firm only.

## Django admin

The Django admin is available at http://localhost:8000/admin/ for development inspection. Create a superuser with:

```powershell
docker compose exec web python manage.py createsuperuser
```
