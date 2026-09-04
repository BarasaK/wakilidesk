# wakiliDesk

wakiliDesk is a multi-tenant records and digital file management system for Kenyan law firms.

This repository contains the current wakiliDesk MVP through Milestone 9, plus Docker-based local development and VPS staging deployment automation.

## Milestone 0 contents

- Django project skeleton
- PostgreSQL, Redis, MinIO, web, and Celery worker services
- Custom email-based user model
- Firm tenant model
- Firm membership model
- Base role and permission models
- Tenant middleware foundation
- Health endpoint
- Development seed command
- CI-friendly tests, including a first cross-tenant access test

## Milestone 1 contents

- Account signup
- Firm onboarding
- Firm profile administration
- Firm logo and theme color configuration
- Firm user list
- Firm-scoped user invitations
- Invitation acceptance
- Role listing, creation, and editing
- Permission checks for firm administration
- Audit events for signup, firm creation, invitations, role changes, and firm profile changes

## Milestone 2 contents

- Client records
- Practice areas
- Matter records
- Matter parties
- Firm-scoped client and matter numbering
- Tenant-scoped client and matter views
- Audit events for client and matter activity

## Milestone 3 contents

- Document categories
- Document metadata records
- Immutable document versions
- Private tenant-aware storage keys
- Upload and download flows
- Archive and restore
- Audit events for document activity

## Milestone 4 contents

- Storage locations
- Physical file registry
- Physical file digitisation status
- Check-out and check-in history
- Overdue file tracking
- Tenant-scoped physical file views

## Milestone 5 contents

- Historical digitisation review records
- Tenant-scoped global search
- Dashboard filing metrics
- In-app notifications

## Milestone 6 contents

- Celery OCR/text-extraction task boundary
- Plain-text extraction
- OCR reprocessing action
- Failed processing notification hook
- Deployment and backup notes

## Milestone 7 contents

- Confidentiality-aware matter access policy
- Restricted matter filtering for documents, physical files, digitisation, dashboard metrics, and search
- Document confidentiality inheritance validation
- Regression tests for restricted records and assigned-user access

## Milestone 8 contents

- Court diary events linked to matters
- Diary filters for type, status, assigned user, search text, and date range
- Visual month calendar for booked events
- Dashboard upcoming diary panel and diary metrics
- In-app and email reminder records
- Celery task and management command for due reminders
- Tenant-scoped and confidentiality-aware diary access

## Milestone 9 contents

- Entity reports for clients, matters, documents, physical files, and diary events
- CSV exports for spreadsheet import and quick sharing
- Excel-compatible `.xlsx` exports without an extra reporting dependency
- PDF report exports with firm name and logo where a firm logo is configured
- Permission-aware report navigation and direct export authorization
- Confidentiality-aware report rows for matter-linked entities

## Local setup

Create a local environment file:

```powershell
Copy-Item .env.example .env
```

Build and start the stack:

```powershell
docker compose up --build
```

In a second terminal, run migrations:

```powershell
docker compose exec web python manage.py migrate
```

Seed development firms, users, and dummy content:

```powershell
docker compose exec web python manage.py seed_dev
```

Run tests:

```powershell
docker compose exec web pytest
```

Run the Celery worker:

```powershell
docker compose up worker
```

## Local URLs

- App: http://localhost:8000/
- Sign in: http://localhost:8000/accounts/login/
- Sign up: http://localhost:8000/accounts/signup/
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
- Health: http://localhost:8000/health/
- Django admin: http://localhost:8000/admin/
- MinIO API: http://localhost:9000/
- MinIO console: http://localhost:9001/

## Development accounts

The seed command creates example accounts for Amani Advocates, Baraka Legal, and Kosmas Law.

Password for all seeded users:

```text
ChangeMe123!
```

Firm A:

```text
admin@amaniadvocates.test
partner@amaniadvocates.test
advocate1@amaniadvocates.test
advocate2@amaniadvocates.test
secretary@amaniadvocates.test
clerk@amaniadvocates.test
```

Firm B:

```text
admin@barakalegal.test
partner@barakalegal.test
advocate1@barakalegal.test
advocate2@barakalegal.test
secretary@barakalegal.test
clerk@barakalegal.test
```

Kosmas Law:

```text
admin@kosmaslaw.test
partner@kosmaslaw.test
advocate1@kosmaslaw.test
advocate2@kosmaslaw.test
secretary@kosmaslaw.test
clerk@kosmaslaw.test
```

The seed command also creates default practice areas, document categories, storage locations, clients, matters, matter parties, documents, physical files, diary events, reminders, and notifications for each seeded firm.

## Manuals

- [Technical MVP manual](docs/user-manual.md): setup, seed data, local operations, troubleshooting, and pilot notes.
- [Technical architecture](docs/architecture.md): system flow, framework choices, modules, routes, background jobs, and deployment architecture.
- [End user manual](docs/end-user-manual.md): non-technical guide for firm users and administrators.
- [VPS staging deployment](docs/vps-staging-deployment.md): Docker Compose and GitHub Actions deployment guide.

## Architectural decisions

- Multi-tenancy starts with a shared PostgreSQL database and shared schema.
- Tenant-owned records must carry a direct `firm` foreign key as modules are added.
- Users are not directly tied to one firm; access comes through `FirmMembership`.
- Roles are firm-owned and permissions are globally defined by codename.
- Server-side membership checks are mandatory for tenant data access.
- Docker is the default development and staging execution path.

## Next milestone

Next work should add explicit matter access lists, deepen search with PostgreSQL full-text indexes, add a real PDF/OCR engine, harden document storage against production S3/MinIO, and expand reporting with filters and scheduled delivery.
