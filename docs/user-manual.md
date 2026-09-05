# wakiliDesk MVP User Manual

This manual explains how to run, seed, navigate, administer, and test the current wakiliDesk MVP.

wakiliDesk is a multi-tenant records and digital file management system for Kenyan law firms. The current MVP focuses on firm onboarding, users and roles, clients, matters, document management, physical file tracking, digitisation review, search, notifications, audit logging, and confidentiality-aware access controls.

For system flow, framework choices, module boundaries, API routes, background jobs, and deployment architecture, see `docs/architecture.md`.

## 1. MVP Scope

The MVP supports:

- Email-based sign in and signup.
- Law firm workspace creation.
- Firm profile administration.
- Firm branding with logo and theme color.
- Firm logo upload during setup/profile, with image preview where a logo is configured.
- Firm users, invitations, roles, and configurable permissions.
- Client records.
- Matter records and matter parties.
- Practice areas and matter numbering.
- Document upload, metadata, versioning, archive, restore, and download.
- Private local document storage under tenant-aware paths.
- Background text extraction task boundary.
- OCR reprocessing action for document versions.
- Physical file registry.
- Storage locations.
- File checkout and check-in history.
- Digitisation quality review records.
- Court diary events, visual calendar, and reminder schedules.
- Tenant-scoped global search.
- Entity reports for clients, matters, documents, physical files, and diary events.
- CSV, Excel-compatible `.xlsx`, and PDF report exports.
- In-app notifications.
- Optional email reminders through configured SMTP.
- Dashboard metrics.
- Confidentiality filtering for restricted records.
- Docker-based local development.

The MVP does not yet include billing, client/trust accounting, M-Pesa, eTIMS, Judiciary integrations, client portal, AI drafting, full OCR for scanned PDFs/images, or production object-storage signing.

## 2. Local Setup

Run the application with Docker Compose from the repository root.

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Build and start the services:

```powershell
docker compose up --build
```

In a second terminal, apply migrations:

```powershell
docker compose exec web python manage.py migrate
```

Create development data:

```powershell
docker compose exec web python manage.py seed_dev
```

Run tests:

```powershell
docker compose exec web pytest
```

Run only Django checks:

```powershell
docker compose exec web python manage.py check
```

Run the Celery worker:

```powershell
docker compose up worker
```

## 3. Local URLs

- App dashboard: http://localhost:8000/
- Sign in: http://localhost:8000/accounts/login/
- Sign up: http://localhost:8000/accounts/signup/
- End-user documentation: http://localhost:8000/documentation/
- Clients: http://localhost:8000/clients/
- Matters: http://localhost:8000/matters/
- Documents: http://localhost:8000/documents/
- Physical files: http://localhost:8000/physical-files/
- Digitisation: http://localhost:8000/physical-files/digitisation/
- Diary: http://localhost:8000/diary/
- Diary calendar: http://localhost:8000/diary/calendar/
- Search: http://localhost:8000/search/
- Reports: http://localhost:8000/reports/
- Notifications: http://localhost:8000/notifications/
- Firm users: http://localhost:8000/app/administration/users/
- Roles: http://localhost:8000/app/administration/roles/
- Firm profile: http://localhost:8000/app/firm/profile/
- Health check: http://localhost:8000/health/
- Django admin: http://localhost:8000/admin/
- MinIO API: http://localhost:9000/
- MinIO console: http://localhost:9001/

## 4. VPS Staging Deployment

The MVP includes a production-style Docker Compose file and GitHub Actions workflow for staging deployments to the VPS.

Current staging target:

```text
http://184.174.32.103:8085/
```

Primary files:

- `.github/workflows/deploy.yml`
- `docker-compose.prod.yml`
- `.env.prod.example`
- `scripts/deploy.sh`
- `docs/vps-staging-deployment.md`

The GitHub Actions workflow deploys automatically when `master` is pushed. It SSHs into the VPS, resets `/opt/wakilidesk` to `origin/master`, builds images, starts Postgres and Redis, waits for Postgres readiness, runs migrations, collects static files, restarts the web and worker containers, and runs Django checks.

Server-only configuration lives in `/opt/wakilidesk/.env.prod` and must not be committed.

Important staging environment values:

```text
DJANGO_DEBUG=false
ALLOWED_HOSTS=184.174.32.103,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://184.174.32.103:8085
WAKILIDESK_HOST_PORT=8085
WAKILIDESK_HOST_BIND=0.0.0.0
```

Use `WAKILIDESK_HOST_BIND=0.0.0.0` only for temporary direct-IP staging access. For Nginx reverse proxy access through a domain, change it back to `127.0.0.1` and proxy traffic to `http://127.0.0.1:8085`.

Manual redeploy from the VPS:

```bash
cd /opt/wakilidesk
APP_DIR=/opt/wakilidesk scripts/deploy.sh
```

Confirm the staging app is healthy:

```bash
curl -f http://127.0.0.1:8085/health/
curl -f http://184.174.32.103:8085/health/
```

Seed staging demo data:

```bash
cd /opt/wakilidesk
docker compose --env-file .env.prod -f docker-compose.prod.yml exec web python manage.py seed_dev
```

If `docker compose ps` shows `127.0.0.1:8085->8000/tcp` after setting `WAKILIDESK_HOST_BIND=0.0.0.0`, recreate the web container:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml stop web
docker compose --env-file .env.prod -f docker-compose.prod.yml rm -f web
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d web
```

For the full VPS setup and rollback procedure, use `docs/vps-staging-deployment.md`.

## 5. Seeded Demo Data

The `seed_dev` command creates three demo law firms:

- Amani Advocates
- Baraka Legal
- Kosmas Law

The command is intended to be idempotent. You can run it again after migrations or local data changes without creating duplicate demo clients, matters, documents, physical files, or notifications.

All seeded users use this password:

```text
ChangeMe123!
```

### Amani Advocates

```text
admin@amaniadvocates.test
partner@amaniadvocates.test
advocate1@amaniadvocates.test
advocate2@amaniadvocates.test
secretary@amaniadvocates.test
clerk@amaniadvocates.test
```

### Baraka Legal

```text
admin@barakalegal.test
partner@barakalegal.test
advocate1@barakalegal.test
advocate2@barakalegal.test
secretary@barakalegal.test
clerk@barakalegal.test
```

### Kosmas Law

```text
admin@kosmaslaw.test
partner@kosmaslaw.test
advocate1@kosmaslaw.test
advocate2@kosmaslaw.test
secretary@kosmaslaw.test
clerk@kosmaslaw.test
```

Each firm receives:

- Default roles and permissions.
- Default practice areas.
- Default document categories.
- Default storage locations.
- Three clients.
- Three matters.
- Matter parties.
- Six text documents.
- Three physical files.
- Three diary events with in-app and email reminders.
- One in-app notification.

## 6. User Roles

wakiliDesk uses firm-scoped roles. A user receives access through a firm membership, not through a single firm field on the user account.

### Firm Administrator

Typical user: managing partner, practice manager, IT/admin lead.

Can manage users, invitations, roles, firm settings, clients, matters, documents, physical files, diary events, reminders, and confidential matters.

### Partner

Typical user: partner or supervising advocate.

Can view clients, matters, documents, physical files, and diary events; create and edit matters; upload documents; download documents; create document versions; manage diary reminders; and manage confidential matters.

### Advocate

Typical user: associate advocate or fee earner.

Can view clients, matters, documents, and diary events; create and edit matters and diary events; upload documents; download documents; and create document versions. Does not manage confidential matters by default.

### Secretary

Typical user: legal secretary or administrative assistant.

Can view, create, and edit clients; view and create matters; view and upload documents; edit document metadata; view physical files; and create or edit diary events.

### Clerk / Records Officer

Typical user: registry clerk or digitisation operator.

Can view clients, matters, documents, physical files, and diary events; upload and index documents; create physical files; check files out and in; and change storage locations.

### Auditor / Read-only

Typical user: internal reviewer, external auditor, or compliance reviewer.

Can view clients, matters, documents, physical files, diary events, and audit logs. Can download documents but cannot change normal records.

### Finance

Placeholder role for future billing and accounts modules. It currently has no default permissions.

## 7. Signing In

Open http://localhost:8000/accounts/login/.

Enter a seeded email and password, for example:

```text
admin@kosmaslaw.test
ChangeMe123!
```

After login, wakiliDesk opens the current firm dashboard. If a user belongs to more than one firm, firm switching links appear on the dashboard.

## 8. Creating a New Firm

Use signup when testing a fresh firm onboarding journey.

1. Open http://localhost:8000/accounts/signup/.
2. Create the user account.
3. Complete firm onboarding.
4. The new user becomes the Firm Administrator for that firm.
5. The application creates default roles for the firm.
6. The user lands on the dashboard.

Default firm values are optimized for Kenyan firms:

- Country: Kenya
- Timezone: Africa/Nairobi
- Currency: KES
- Matter number pattern: `{PRACTICE_AREA}/{YEAR}/{SEQUENCE}`

The setup form can capture a firm logo. Existing logos are rendered as an image preview in the firm profile form instead of only showing the uploaded file path.

## 9. Dashboard

The dashboard gives an operational summary for the active firm. Metrics are filtered to records the current user can access.

Dashboard cards show:

- Active matters.
- Documents.
- Physical files checked out.
- Files awaiting return.
- Files awaiting quality review.
- Upcoming diary events.
- Past scheduled diary events.
- Unread notifications.

The digitisation progress panel shows completed physical files against total physical files available to the current user.

Common actions provide shortcuts to:

- New client.
- New matter.
- Upload document.
- Register file.
- New diary event.

## 10. Clients

Use **Clients** to maintain client records for the active firm.

Client types:

- Individual.
- Organisation.

Common fields:

- Client type.
- Name.
- Company registration number, where applicable.
- National ID or passport, where applicable.
- KRA PIN, where applicable.
- Email.
- Phone.
- Address.
- Status.

### Create a client

1. Open **Clients**.
2. Select **Create client**.
3. Complete the form.
4. Save.

wakiliDesk assigns a firm-scoped client number, for example `CL-00001`.

### Edit a client

1. Open the client detail page.
2. Select **Edit client**.
3. Update the form.
4. Save.

Client records are tenant-scoped. A user from another firm cannot retrieve another firm's client.

## 11. Matters

Matters are the main digital file containers.

Common fields:

- Client.
- Title.
- Description.
- Practice area.
- Status.
- Responsible partner.
- Responsible advocate.
- Opened date.
- Closed date.
- Whether a physical file exists.
- Confidentiality level.

Matter statuses:

- Open.
- Active.
- On hold.
- Closed.
- Archived.

### Create a matter

1. Open **Matters**.
2. Select **Create matter**.
3. Choose the client.
4. Choose the practice area.
5. Assign responsible users if needed.
6. Set status and confidentiality.
7. Save.

wakiliDesk generates the matter number from the firm's numbering pattern. The default format is:

```text
{PRACTICE_AREA}/{YEAR}/{SEQUENCE}
```

Example:

```text
LIT/2026/00001
```

### Add a matter party

1. Open a matter.
2. Select **Add party**.
3. Choose the party type.
4. Enter name and contact details.
5. Save.

Matter party types include opposing party, interested party, witness, company director, and other.

### View matter documents

Open a matter to see documents linked to that file. The matter detail screen shows document title, category, reference, date, current version, and archive status for users with document view permission.

Users with upload permission can select **Upload document** from the matter page. The upload form opens with that matter preselected.

## 12. Confidentiality

Confidentiality levels are:

- Standard.
- Restricted.
- Partner only.
- Custom.

Standard matters are visible to users with the relevant view permission.

Restricted, partner-only, and custom matters are visible only to:

- Users with `manage_confidential_matter`.
- The matter's responsible partner.
- The matter's responsible advocate.

Documents and physical files inherit access from their linked matter. If a user cannot access the matter, they cannot access linked documents, physical files, digitisation records, or search results for that matter.

A document cannot be saved with a confidentiality level lower than its linked matter. For example, a restricted matter cannot contain a standard document unless a future explicit override rule is added.

## 13. Practice Areas

Practice areas are firm-configurable.

Default practice areas include:

- Litigation.
- Conveyancing.
- Corporate & Commercial.
- Employment.
- Family.
- Probate & Succession.
- Debt Recovery.
- Intellectual Property.
- Tax.
- Arbitration.

Firm administrators can create and edit practice areas from the practice area screen. Practice area codes are used in generated matter numbers.

## 14. Documents

Documents are matter-linked records with metadata and immutable file versions.

Common document fields:

- Matter.
- Title.
- Document type.
- Document date.
- Reference number.
- Description.
- Source.
- Confidentiality level.
- File.

Document sources:

- Scanned physical.
- Email.
- Internal upload.
- Client upload.
- Migration.
- System generated.

Supported MVP file types:

- Plain text.
- PDF.
- JPEG.
- PNG.
- TIFF.
- DOC.
- DOCX.

### Upload a document

1. Open **Documents**.
2. Select **Upload document**.
3. Choose an accessible matter. If you started from a matter page, the matter is preselected.
4. Enter document metadata.
5. Select the file.
6. Save.

The upload creates:

- A document metadata record.
- Version 1 of the document file.
- A private tenant-aware storage key.
- A checksum.
- An audit event.
- A queued text-extraction task.

### Add a new version

1. Open the document detail page.
2. Select **Upload new version**.
3. Choose the replacement or revised file.
4. Save.

New versions do not overwrite older versions. The document points to the latest version as its current version.

### Download a document

1. Open the document detail page.
2. Select **Download current version**.

Downloads require `download_document` permission and access to the linked matter.

### Archive and restore

Use archive when a document should no longer appear as active. Archive does not permanently delete the stored file or version history.

Users with restore permission can restore archived documents.

## 15. Text Extraction and OCR Boundary

The MVP includes the asynchronous processing boundary needed for OCR/text extraction.

Current behavior:

- Plain text files are extracted into searchable text.
- Other file types are marked through the OCR/task boundary but do not yet receive full scanned-image OCR.
- Failed processing creates an in-app notification for the uploading user.
- A document detail page can trigger reprocessing.

For local testing, run the worker:

```powershell
docker compose up worker
```

If Celery is not running, uploads still complete, but queued background extraction may not execute until a worker is available.

## 16. Physical Files

Physical files represent paper files that coexist with digital records.

Common fields:

- Matter.
- Physical file number.
- Volume number.
- Storage location.
- Status.
- Digitisation status.
- Barcode or QR reference.
- Notes.

Physical file statuses:

- In storage.
- Checked out.
- Archived.
- Missing.
- Destroyed.

Digitisation statuses:

- Not started.
- Preparing.
- Scanning.
- Indexing.
- Quality review.
- Completed.
- On hold.

### Register a physical file

1. Open **Physical files**.
2. Select **Register file**.
3. Choose an accessible matter.
4. Enter physical file number and volume.
5. Select storage location.
6. Set file and digitisation status.
7. Save.

### Edit a physical file

Use edit to change file metadata, storage location, barcode/QR reference, notes, or digitisation state.

## 17. Storage Locations

Storage locations are hierarchical and firm-scoped.

Example:

```text
Nairobi Office
Records Room
Cabinet A
Shelf 01
```

Firm administrators or records users with the relevant permission can create and edit locations from the storage location screen.

## 18. Checkout and Check-in

Checkout records who has a physical file and when it should be returned.

Checkout fields:

- Checked out to.
- Checked out to name.
- Expected return date and time.
- Purpose.
- Notes.

### Check out a file

1. Open the physical file detail page.
2. Select **Check out**.
3. Choose a user or enter a named recipient.
4. Enter expected return date and purpose.
5. Save.

Once checked out, the physical file status changes to checked out.

### Check in a file

1. Open the physical file detail page.
2. Select **Check in**.
3. Add return notes if needed.
4. Save.

Once checked in, the physical file status returns to in storage.

wakiliDesk prevents duplicate active checkouts for the same physical file.

## 19. Digitisation Review

Digitisation review is used for historical paper-file conversion.

Review fields:

- Scanner/operator.
- Scan date.
- Reviewer.
- Review date.
- Missing-page flag.
- Poor-quality flag.
- Rescan required.
- Completion confirmed.
- Notes.

### Record a review

1. Open **Digitisation**.
2. Open the review action for a physical file.
3. Enter scanner and reviewer details.
4. Set quality flags.
5. Confirm completion only when the digital record is acceptable.
6. Save.

If completion is confirmed, the linked physical file is marked completed. If there are quality issues, the file remains in quality review.

## 20. Court Diary, Calendar, and Reminders

The court diary tracks dated work such as mentions, hearings, filing deadlines, client meetings, internal tasks, and other firm events.

Diary events are firm-scoped. If a diary event is linked to a confidential matter, the event is hidden from users who cannot access that matter.

The diary has two views:

- **List view**: best for filtering, operational follow-up, and reviewing all matching events.
- **Calendar view**: best for seeing booked dates across a month.

Common diary fields:

- Matter, optional.
- Title.
- Event type.
- Start date and time.
- End date and time, optional.
- Court name.
- Location.
- Assigned user.
- Status.
- Notes.
- Reminder schedule.
- Reminder channels.

Diary event statuses:

- Scheduled.
- Completed.
- Adjourned.
- Cancelled.

### Create a diary event

1. Open **Diary**.
2. Select **Create diary event**.
3. Choose the linked matter if the event belongs to a matter.
4. Enter the event title, type, start date and time, court, location, and assigned user.
5. Choose reminder timing such as same day, 1 day before, 3 days before, or 7 days before.
6. Choose reminder channels: in-app, email, or both.
7. Save.

### Use the calendar view

1. Open **Diary**.
2. Select **Calendar view**.
3. Use **Previous**, **Today**, and **Next** to move between months.
4. Select a diary event inside the calendar to open its detail page.
5. Select **Add** on a date cell to create a diary event prefilled for that date.

### Reminder processing

Due reminders are sent by the `send_diary_reminders` Celery task or by the management command:

```powershell
docker compose exec web python manage.py send_diary_reminders
```

For staging:

```bash
cd /opt/wakilidesk
docker compose --env-file .env.prod -f docker-compose.prod.yml exec web python manage.py send_diary_reminders
```

In-app reminders create unread notifications for the assigned user. If no assigned user exists, the reminder goes to the event creator.

Email reminders use Django's configured email backend. Offline and early staging environments can keep:

```text
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
DEFAULT_FROM_EMAIL=wakilidesk@gmail.com
```

For Gmail SMTP testing, use a Gmail app password and set:

```text
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=wakilidesk@gmail.com
EMAIL_PASSWORD=<gmail-app-password>
EMAIL_USE_TLS=true
DEFAULT_FROM_EMAIL=wakilidesk@gmail.com
```

Failed email reminders are marked failed with a failure reason. A failed email does not prevent other due reminders from being processed.

## 21. Search

Global search is tenant-scoped and confidentiality-aware.

Search can find:

- Client names.
- Client numbers.
- Client email or phone.
- Matter numbers.
- Matter titles.
- Matter descriptions.
- Matter parties.
- Document titles.
- Document reference numbers.
- Document descriptions.
- Extracted document text.
- Physical file numbers.
- Barcode or QR references.
- Physical file notes.

Search results only include records the current user has permission to view.

## 22. Notifications

Notifications are in-app, firm-scoped, and user-specific.

Current MVP notification examples:

- Seed data ready.
- Failed document processing.
- Court diary reminders.

Users can open the notification list and mark notifications as read.

## 23. Reports

Reports export firm records the current user is allowed to view. The report menu is hidden from roles that do not have any supported view permission.

Available report entities:

- Clients.
- Matters.
- Documents.
- Physical files.
- Diary events.

Available formats:

- CSV for simple spreadsheet import.
- Excel-compatible `.xlsx` for spreadsheet users.
- PDF for printable summaries.

PDF exports include the firm display name. If the firm has a logo configured in **Firm Profile**, the logo is placed at the top of the PDF.

Reports use the same access rules as the screens:

- Client reports require `view_client`.
- Matter reports require `view_matter`.
- Document reports require `view_document`.
- Physical file reports require `view_physical_file`.
- Diary event reports require `view_diaryevent`.
- Restricted matter-linked records are hidden unless the user can access the linked matter.

### Export a report

1. Open **Reports**.
2. Select the report entity.
3. Select CSV, Excel, or PDF.
4. Select **Export report**.

The file downloads immediately. If no report options appear, the current role does not have reportable view permissions.

## 24. Firm Administration

Firm administration includes:

- Firm profile.
- Users.
- Invitations.
- Roles.
- Permissions.
- Practice areas.
- Document categories.
- Storage locations.

### Invite a user

1. Open **Users**.
2. Select **Invite user**.
3. Enter the user's email address.
4. Select a role.
5. Save.

The application creates a firm invitation. The invited user can accept the invitation, set a password, and receive membership in the firm.

### Manage roles

1. Open **Roles**.
2. Create or edit a role.
3. Assign permissions.
4. Save.

Permissions are grouped by module, including clients, matters, documents, physical files, and administration.

### Manage firm profile

Use **Firm Profile** to update firm details such as legal name, display name, email, phone, address, city, country, timezone, currency, logo, theme color, and matter numbering pattern. When a logo has been uploaded, the current image is shown in the form before the file input.

## 25. Audit Trail

Audit logging records significant system actions.

Current audited examples include:

- Firm creation.
- Firm profile updates.
- User invitations.
- Role creation and updates.
- Client creation and updates.
- Matter creation and updates.
- Matter party creation.
- Document upload.
- Document version creation.
- Document metadata update.
- Document download.
- Document archive and restore.
- Physical file creation and updates.
- Physical file checkout and check-in.
- Digitisation review creation.
- Diary event creation and updates.

Audit records are tenant-scoped and should not be edited through normal application interfaces.

## 26. Data Protection Operating Notes

For pilot use:

- Use least-privilege roles.
- Do not grant confidential-matter permission broadly.
- Avoid storing unnecessary national ID, passport, or KRA PIN data unless needed.
- Use document categories consistently.
- Keep physical file checkout records current.
- Keep court diary events current after adjournments, mentions, and hearings.
- Export reports only to approved firm storage or recipients.
- Review overdue files regularly.
- Confirm digitisation quality before marking files completed.
- Do not use seeded passwords in production.
- Do not commit `.env` files or secrets.

## 27. Troubleshooting

### Login page does not load

Run:

```powershell
docker compose exec web python manage.py check
```

Confirm the app is running:

```powershell
docker compose ps
```

Open:

```text
http://localhost:8000/accounts/login/
```

### Seed command fails

Run migrations first:

```powershell
docker compose exec web python manage.py migrate
```

Then rerun:

```powershell
docker compose exec web python manage.py seed_dev
```

### Document text is not searchable

Confirm the worker is running:

```powershell
docker compose up worker
```

For plain text documents, open the document detail page and use the reprocess action.

### Diary reminders are not arriving

Run the reminder command manually:

```powershell
docker compose exec web python manage.py send_diary_reminders
```

Confirm the event has pending reminders and the reminder time is due. For email reminders, confirm `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_USER`, `EMAIL_PASSWORD`, and `DEFAULT_FROM_EMAIL` are set correctly.

### A report is missing records

Confirm the user has the relevant view permission. For matter-linked reports, also confirm the user can access restricted or partner-only matters where applicable.

### Test database already exists

If pytest fails during test database creation after an interrupted or parallel run, recreate the test database:

```powershell
docker compose exec web pytest --create-db
```

### Static UI looks plain

The current MVP uses Django templates and inline CSS in `src/templates/base.html`. It does not yet include a Tailwind build pipeline or separate frontend asset bundling.

## 28. Developer and Admin Commands

Apply migrations:

```powershell
docker compose exec web python manage.py migrate
```

Create demo data:

```powershell
docker compose exec web python manage.py seed_dev
```

Create a Django superuser:

```powershell
docker compose exec web python manage.py createsuperuser
```

Run tests:

```powershell
docker compose exec web pytest
```

Run tests with test database recreation:

```powershell
docker compose exec web pytest --create-db
```

Run a targeted test:

```powershell
docker compose exec web pytest tests/test_milestone_7.py
```

Run Django checks:

```powershell
docker compose exec web python manage.py check
```

Send due diary reminders:

```powershell
docker compose exec web python manage.py send_diary_reminders
```

Check for missing migrations:

```powershell
docker compose exec web python manage.py makemigrations --check --dry-run
```

## 29. Pilot Readiness Checklist

Before a controlled pilot:

- Confirm each pilot firm has correct users and roles.
- Replace all demo passwords.
- Confirm firm profile data and numbering pattern.
- Confirm the firm logo and theme color.
- Confirm document categories and practice areas.
- Confirm storage locations.
- Upload sample documents and verify download behavior.
- Start Celery worker and verify text extraction.
- Register several physical files.
- Test checkout and check-in.
- Record at least one digitisation review.
- Create sample court diary events and confirm in-app reminders.
- Export sample CSV, Excel, and PDF reports.
- Confirm the firm logo appears in PDF reports when configured.
- Confirm confidential matters are hidden from unassigned users.
- Run the automated test suite.
- Confirm backup and restore procedures in `docs/deployment-and-backup.md`.

## 30. Known MVP Limitations

- OCR is a task boundary with plain-text extraction; scanned PDF/image OCR is future work.
- Object storage is represented by private local storage in the current implementation.
- Search is simple database filtering, not PostgreSQL full-text ranking yet.
- Explicit matter access lists are not implemented yet.
- Email reminders use Django email settings, but production deliverability, bounce handling, and templates need hardening.
- Reports do not yet include user-selected date filters, saved report templates, or scheduled delivery.
- Client portal and external integrations are outside MVP scope.

## 31. Recommended Next Improvements

For the next post-MVP hardening pass:

- Add explicit matter access lists.
- Add PostgreSQL full-text search indexes and ranking.
- Add real PDF text extraction and scanned image OCR.
- Add S3/MinIO production storage adapter with signed downloads.
- Add audit log review UI.
- Add richer dashboard trends and recent activity.
- Add recurring diary events and richer calendar export.
- Add report filters, report templates, and scheduled report emails.
