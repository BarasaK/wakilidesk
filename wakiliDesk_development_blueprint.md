# wakiliDesk — Development Blueprint & VS Code Build Prompt

## 1. Product Vision

Build **wakiliDesk**, a secure, responsive, multi-tenant web application for law firms in Kenya.

The first production module is **Digital File & Document Management**, designed to digitize both:

1. **Existing physical legal files** through structured scanning, indexing and migration.
2. **New files and documents going forward**, so firms progressively move away from paper-first operations.

The architecture must support future modules without major rewrites, including:

- Matter / case management
- Court diary and deadlines
- Tasks and workflow
- Billing and fee notes
- Client / trust accounting
- M-Pesa integration
- Client portal
- Notifications
- Email integration
- Reporting and dashboards
- Document templates
- Legal research and AI-assisted document capabilities

The first release should remain focused and production-quality rather than attempting to build all future modules at once.

---

# 2. Recommended Technical Architecture

## 2.1 Development approach

Use a **Docker-based development and deployment environment**.

Docker is preferred over native-only development because wakiliDesk will have multiple infrastructure components and is intended to become a multi-tenant SaaS product.

Docker should provide consistent environments across:

- Developer laptops
- Test/UAT servers
- Production
- CI/CD

Use `docker compose` during development.

## 2.2 Core stack

Preferred stack:

### Backend
- Python
- Django
- Django REST Framework where APIs are needed
- Django ORM
- PostgreSQL

### Frontend
For the initial product, prefer a Django-centered frontend rather than immediately creating a separate SPA.

Use:

- Django templates
- HTMX for interactive components
- Alpine.js only where lightweight client-side state is useful
- Tailwind CSS for responsive styling

Reasoning:

- Python remains the primary development language.
- Authentication, forms and permissions remain simpler.
- Faster delivery than maintaining separate React and Django applications.
- Lower deployment complexity.
- HTMX supports modern app-like interactions without creating an unnecessary frontend API layer.
- REST APIs can still be exposed later for mobile apps, integrations and client portals.

Do **not** tightly couple domain logic to HTML views. Business logic should remain in services/domain modules so that the same logic can later support APIs.

### Supporting infrastructure
- PostgreSQL — relational application database
- Redis — caching and task queue broker
- Celery — background processing
- S3-compatible object storage for documents
  - Local development: MinIO
  - Production: AWS S3, Azure Blob, Cloudflare R2 or another suitable object store
- Nginx or equivalent reverse proxy in production
- Gunicorn for Django serving
- Optional ClamAV or equivalent malware scanning for uploaded files

### OCR
OCR should be an asynchronous background capability.

The initial architecture must permit:

- PDF text extraction
- OCR of scanned PDFs/images
- Searchable OCR text
- Reprocessing failed OCR jobs

Do not make OCR a blocking step during file upload.

---

# 3. Architecture Style

Build wakiliDesk as a **modular monolith** initially.

Do not use microservices for the MVP.

Create clear Django apps/modules such as:

```text
wakiliDesk/
├── accounts/
├── tenants/
├── firms/
├── clients/
├── matters/
├── documents/
├── physical_files/
├── audit/
├── notifications/
├── dashboard/
└── common/
```

Future modules can be added as:

```text
billing/
client_accounts/
court_diary/
tasks/
integrations/
client_portal/
ai/
reports/
```

Each module should have:

- models
- services
- permissions
- selectors/query logic where useful
- views
- forms
- templates
- tests

Avoid putting complex business logic directly inside views.

---

# 4. Multi-Tenancy

wakiliDesk must be designed as a **multi-tenant SaaS application from the beginning**.

A tenant represents a law firm.

For the initial implementation, use:

> **Shared PostgreSQL database + shared schema + explicit `firm_id` / tenant foreign key on tenant-owned data.**

Do not start with one database or one PostgreSQL schema per firm unless a later enterprise requirement requires stronger physical isolation.

Reasons:

- Easier migrations
- Simpler backup and operations
- Easier reporting
- Lower infrastructure cost
- Better fit for early SaaS growth

## 4.1 Tenant isolation requirement

Tenant isolation is a critical security requirement.

A user belonging to Firm A must never be able to access:

- Firm B clients
- Firm B matters
- Firm B documents
- Firm B audit records
- Firm B configuration

Every tenant-owned table must include a firm/tenant reference.

Examples:

```text
Client -> Firm
Matter -> Firm
Document -> Firm
PhysicalFile -> Firm
UserMembership -> Firm
Role -> Firm
AuditEvent -> Firm
```

Do not rely only on frontend filtering.

Tenant filtering must be enforced server-side.

Use a central tenant-aware query/service pattern to minimize accidental cross-firm access.

Add automated tests specifically attempting cross-tenant access.

---

# 5. Authentication and Firm Onboarding

## 5.1 First-time SaaS onboarding

The initial signup flow should create both:

1. User account
2. Law firm / tenant

Suggested flow:

```text
Create Account
      ↓
Verify Email
      ↓
Create Law Firm
      ↓
Firm Profile Setup
      ↓
Create Initial Administrator
      ↓
Initial Configuration
      ↓
Dashboard
```

## 5.2 Firm setup fields

Capture at minimum:

- Firm legal name
- Display name
- Firm logo
- Primary email
- Primary phone
- Physical/postal address
- Town/city
- Country
- Website, optional
- LSK-related identifier(s), optional/configurable
- Default timezone
- Default date format
- Default currency
- Firm file-number format
- Primary contact person
- Data retention preferences where applicable

Defaults for Kenyan firms:

```text
Country: Kenya
Timezone: Africa/Nairobi
Currency: KES
```

## 5.3 Firm branding

Allow each firm to configure:

- Logo
- Display name
- Optional letterhead details
- Optional accent/brand color later

The firm logo should appear appropriately in the authenticated application and future generated reports.

---

# 6. User, Role and Permission Model

Do not hard-code access rules only by role name.

Implement:

```text
User
  ↓
Firm Membership
  ↓
Role
  ↓
Permissions
```

A user can belong to a firm through a `FirmMembership`.

Roles should provide default permission bundles, while the firm administrator can configure granular permissions.

## 6.1 Initial roles

### Platform Super Administrator

wakiliDesk operator role.

Can:

- Manage tenants
- Suspend/reactivate firms
- View system health
- Manage platform configuration
- Assist with support

Platform administrators should **not automatically browse confidential client documents** merely because they are system admins. Any exceptional support access must be deliberate and audited.

### Firm Administrator

Usually managing partner, administrator or designated IT/admin person.

Can:

- Configure firm
- Invite users
- Activate/deactivate users
- Configure roles
- Assign permissions
- Configure document categories
- Configure practice areas
- Configure file numbering
- View firm audit logs
- Configure retention/settings

### Managing Partner / Partner

Useful initial senior role.

Typical rights:

- View all or permitted firm matters
- Create/edit matters
- View matter documents
- Approve restricted actions
- Access management views
- Mark matters confidential
- Control matter-level access where enabled

### Advocate

Can typically:

- Access assigned/permitted matters
- Upload documents
- Create new document versions
- View/download documents
- Add notes
- Search permitted matters and clients
- Request/create file check-out
- Create matters if permission granted

### Secretary

Typical responsibilities:

- Client data entry
- Matter opening support
- Document upload
- Scan/index correspondence
- Update metadata
- Generate file labels/reference numbers
- Search/retrieve files
- Limited editing based on firm configuration

### Clerk / Records Officer

Important for the initial digitisation module.

Can typically:

- Scan/upload documents
- Index documents
- Manage physical file location
- Check files in/out
- Record archive location
- Bulk import historical documents
- Correct indexing metadata
- View records necessary for filing

Should normally have restricted access to confidential matter content unless explicitly granted.

### Auditor / Read-only

Optional but useful.

Can:

- Read selected records
- Review audit activity
- Cannot modify/delete documents

### Finance

Create the role placeholder now, but financial permissions can be activated when billing/accounting modules are introduced.

---

# 7. Permission Configuration

Build a permission management interface under firm administration.

Permissions should be grouped by module.

Example:

```text
Clients
- view_client
- create_client
- edit_client
- archive_client

Matters
- view_matter
- create_matter
- edit_matter
- close_matter
- view_all_matters
- manage_confidential_matter

Documents
- view_document
- upload_document
- download_document
- edit_document_metadata
- create_document_version
- archive_document
- delete_document
- restore_document
- bulk_upload_documents

Physical Files
- view_physical_file
- create_physical_file
- checkout_physical_file
- checkin_physical_file
- change_storage_location

Administration
- manage_users
- manage_roles
- manage_firm_settings
- view_audit_logs
```

Permissions must be configurable by the Firm Administrator.

Use least privilege by default.

---

# 8. Core Domain Model

## 8.1 Firm

Represents the tenant.

Important fields:

```text
id
name
display_name
slug
logo
email
phone
address
city
country
timezone
currency
file_number_pattern
is_active
created_at
updated_at
```

## 8.2 User

Use a custom Django user model from the beginning.

Prefer email-based login.

## 8.3 FirmMembership

```text
user
firm
role
status
joined_at
last_active_at
```

Avoid placing a single `firm_id` directly on the User if there is any future possibility that one person may work across multiple branches/firms.

## 8.4 Client

Support both:

- Individual
- Organisation/company

Fields should include only necessary information initially.

Examples:

```text
firm
client_number
client_type
name
company_registration_number
national_id_or_passport
kra_pin
email
phone
address
status
created_by
created_at
updated_at
```

Design sensitive identifiers carefully.

## 8.5 Matter

The Matter is the main digital file container.

```text
firm
matter_number
client
title
description
practice_area
status
responsible_partner
responsible_advocate
opened_date
closed_date
physical_file_exists
confidentiality_level
created_by
created_at
updated_at
```

Potential statuses:

```text
OPEN
ACTIVE
ON_HOLD
CLOSED
ARCHIVED
```

## 8.6 Matter Party

Allow additional parties:

- Client
- Opposing party
- Interested party
- Witness
- Company director
- Other related party

This will later support conflict checking.

## 8.7 Practice Area

Firm configurable.

Examples:

```text
Litigation
Conveyancing
Corporate & Commercial
Employment
Family
Probate & Succession
Debt Recovery
Intellectual Property
Tax
Arbitration
```

---

# 9. Digital Document Management Module

This is the first major product module.

## 9.1 Document record

A document is not merely a file attachment.

Store document metadata separately from binary storage.

Example:

```text
Document
- id
- firm
- matter
- title
- document_type
- document_date
- reference_number
- description
- current_version
- source
- confidentiality_level
- uploaded_by
- created_at
- updated_at
- archived_at
```

## 9.2 Document version

Every uploaded revision should create a version.

```text
DocumentVersion
- document
- version_number
- storage_key
- original_filename
- mime_type
- file_size
- checksum
- uploaded_by
- uploaded_at
- extracted_text
- ocr_status
```

Never overwrite the previous binary when a new version is uploaded.

## 9.3 Document categories

Firm-configurable categories.

Suggested defaults:

```text
Client Instructions
Pleadings
Court Documents
Correspondence
Evidence
Agreements
Research
Billing
Internal Notes
Other
```

Support subcategories later.

## 9.4 Document source

Useful values:

```text
SCANNED_PHYSICAL
EMAIL
INTERNAL_UPLOAD
CLIENT_UPLOAD
MIGRATION
SYSTEM_GENERATED
```

---

# 10. Physical File Management

The system must support coexistence of physical and digital filing during transition.

## 10.1 Physical file record

Example fields:

```text
firm
matter
physical_file_number
volume_number
storage_location
status
barcode_or_qr_code
notes
created_at
updated_at
```

Suggested physical file statuses:

```text
IN_STORAGE
CHECKED_OUT
ARCHIVED
MISSING
DESTROYED
```

## 10.2 Storage locations

Allow administrators to define hierarchical storage locations.

Example:

```text
Nairobi Office
  └── Records Room
      └── Cabinet B
          └── Shelf 03
```

## 10.3 File check-in / check-out

Record:

- Physical file
- Checked out by
- Checked out to
- Date/time
- Expected return
- Purpose
- Return date/time
- Notes

Maintain immutable history.

Optional future feature:

- QR/barcode scanning with mobile camera.

---

# 11. Existing Physical File Digitisation Workflow

Historical conversion is a separate operational workflow within the system.

Suggested process:

```text
Select/Create Matter
       ↓
Register Physical File
       ↓
Prepare Documents for Scanning
       ↓
Scan
       ↓
Upload Batch
       ↓
Split/Identify Documents
       ↓
Assign Document Category
       ↓
Capture Metadata
       ↓
OCR Processing
       ↓
Quality Review
       ↓
Approve
       ↓
Searchable Digital Matter File
```

## 11.1 Migration status

Track digitisation progress per physical file.

Suggested statuses:

```text
NOT_STARTED
PREPARING
SCANNING
INDEXING
QUALITY_REVIEW
COMPLETED
ON_HOLD
```

Dashboard should show:

- Total physical files
- Not started
- In progress
- Awaiting quality review
- Completed
- Digitisation percentage

## 11.2 Quality control

For historical digitisation, support:

- Scanner/operator
- Scan date
- Reviewer
- Review date
- Missing-page flag
- Poor-quality flag
- Re-scan required
- Completion confirmation

Do not mark a physical file digitised merely because one PDF was uploaded.

---

# 12. New Document Filing Workflow

New documents should support a simpler workflow.

```text
Upload / Scan
    ↓
Select Matter
    ↓
Choose Category
    ↓
Enter Metadata
    ↓
Save
    ↓
OCR / text extraction runs asynchronously
    ↓
Document becomes searchable
```

Minimise required fields so clerks and secretaries can file documents quickly.

---

# 13. Search

Search is a key feature, not an afterthought.

Users should be able to search by:

- Client name
- Matter number
- Matter title
- Court/case reference number later
- Opposing party
- Document title
- Document category
- Document reference
- Document date
- Responsible advocate
- Practice area
- Physical file number
- OCR/extracted document text

Initial search can use PostgreSQL full-text search.

Design the search service so it can later move to:

- OpenSearch
- Elasticsearch
- Meilisearch

without rewriting domain models.

Search results must respect tenant and role permissions.

---

# 14. Confidentiality

Provide matter/document confidentiality levels.

Initial values:

```text
STANDARD
RESTRICTED
PARTNER_ONLY
CUSTOM
```

A matter marked restricted should permit explicit user/role access.

Document permissions inherit from the matter by default, but a document may be more restricted than its parent matter.

Never allow a document to be less restricted than its containing matter without an explicit rule.

---

# 15. Audit Trail

Audit logging is mandatory.

Record significant events such as:

- Login
- Logout
- Failed login where appropriate
- Client created/updated
- Matter created/updated/closed
- Document uploaded
- Document viewed
- Document downloaded
- Version created
- Document archived/deleted/restored
- Permission changed
- User invited/deactivated
- Physical file checked out/in
- Firm configuration changed

Audit fields:

```text
firm
user
action
object_type
object_id
timestamp
ip_address
user_agent
metadata
```

Audit records should not be editable through normal application interfaces.

---

# 16. Deletion and Archiving

Avoid destructive deletion.

Use:

- Active
- Archived
- Soft deleted

for business records.

Permanent deletion must require an elevated permission and should be rare.

Documents should generally be archived rather than deleted.

Maintain restore capability for soft-deleted documents.

---

# 17. File Storage and Security

Never store uploaded legal documents directly inside the public web directory.

Use object storage and private buckets.

Store only storage keys/metadata in PostgreSQL.

Requirements:

- Private objects
- Signed temporary download URLs
- Tenant-separated storage prefixes
- File size limits configurable
- MIME validation
- Malware scanning hook
- Checksums
- Encryption at rest
- HTTPS/TLS in transit

Suggested storage structure:

```text
firms/{firm_uuid}/matters/{matter_uuid}/documents/{document_uuid}/versions/{version_uuid}
```

Do not expose predictable storage paths publicly.

---

# 18. Responsive UI

The web app must work well on:

- Desktop
- Laptop
- Tablet
- Modern mobile browser

Use a responsive sidebar/navigation pattern.

Primary navigation for V1:

```text
Dashboard
Clients
Matters
Documents
Physical Files
Digitisation
Search
Administration
```

Mobile users should at minimum be able to:

- Search matters
- Open a matter
- View documents
- Upload documents/photos/PDFs
- Check physical file status

---

# 19. Dashboard V1

Firm dashboard should show useful filing information.

Suggested cards:

```text
Active Matters
Documents Uploaded This Month
Physical Files Checked Out
Files Awaiting Return
Digitisation Progress
Files Awaiting Quality Review
Recently Accessed Matters
Recent Uploads
```

The dashboard must never expose confidential matter names to users without permission.

---

# 20. Administration

Firm administrators need configuration screens for:

## Firm
- Firm profile
- Logo
- Contact details

## Users
- Invite user
- Suspend user
- Reactivate user

## Roles
- Create role
- Clone role
- Assign permissions

## Practice Areas
- Add/edit/archive

## Document Categories
- Add/edit/archive

## Storage Locations
- Define offices, rooms, cabinets and shelves

## Numbering
Configure numbering patterns.

Example:

```text
{PRACTICE_AREA}/{YEAR}/{SEQUENCE}
```

Result:

```text
LIT/2026/00124
```

Ensure generated references are unique within the firm.

---

# 21. Notifications

Initial notifications:

- User invited
- Physical file overdue
- File assigned/check-out event
- Digitisation item awaiting review
- Failed document processing/OCR

Start with in-app and email notification architecture.

SMS/WhatsApp can be added later.

---

# 22. Data Protection and Privacy

Design with Kenya's Data Protection Act obligations in mind.

Key principles:

- Data minimisation
- Purpose limitation
- Access control
- Auditability
- Secure retention
- Secure deletion
- Tenant isolation

Keep the application capable of supporting:

- Data export
- Account deactivation
- Retention configuration
- Audit review
- Backup and restore

Do not log sensitive document content unnecessarily.

---

# 23. Backup and Recovery

Production must have:

- Automated PostgreSQL backups
- Object storage versioning or backup strategy
- Backup retention policy
- Restore testing
- Separation between primary and backup copies

Document how to restore:

1. Database
2. Object storage
3. Application configuration

---

# 24. Initial Docker Layout

Use a structure similar to:

```text
docker-compose.yml
.env.example

services:
  web:
    Django application

  db:
    PostgreSQL

  redis:
    Redis

  worker:
    Celery worker

  beat:
    Celery beat, only when scheduled jobs are introduced

  minio:
    Local S3-compatible storage

  nginx:
    Optional locally; required/recommended in production
```

Do not embed secrets in Dockerfiles or source control.

---

# 25. Environment Configuration

Use environment variables for:

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG
DATABASE_URL
REDIS_URL
S3_ENDPOINT
S3_ACCESS_KEY
S3_SECRET_KEY
S3_BUCKET
EMAIL_HOST
EMAIL_PORT
EMAIL_USER
EMAIL_PASSWORD
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS
```

Commit `.env.example`, not `.env`.

---

# 26. Testing Expectations

Use pytest / pytest-django or Django's test framework consistently.

Minimum important test categories:

## Tenant isolation
Attempt cross-firm access for:

- clients
- matters
- documents
- physical files
- search
- audit logs

These tests are mandatory.

## Permission tests
For each role, verify:

- permitted actions succeed
- forbidden actions return 403

## Document tests
- upload
- version creation
- download permission
- archive
- restore
- metadata update

## Physical file tests
- checkout
- duplicate checkout prevention
- return
- overdue calculations

## Search tests
Ensure restricted records do not appear.

---

# 27. Seed Data

Create development seed data for:

### Firm A
- 1 Firm Admin
- 1 Partner
- 2 Advocates
- 1 Secretary
- 1 Clerk

### Firm B
- Similar structure

Create clients, matters and documents for both firms.

This data must make tenant-isolation testing easy.

---

# 28. Initial MVP Boundaries

Build now:

- Multi-tenant foundation
- Authentication
- Firm onboarding
- Firm profile and branding
- User invitations
- Roles and configurable permissions
- Client records
- Matter records
- Matter parties
- Practice areas
- Document categories
- Digital document upload/storage
- Document versioning
- Metadata
- OCR/text-extraction architecture
- Search
- Physical file registry
- Physical file location
- Check-in/check-out
- Historical digitisation workflow
- Quality review
- Audit logs
- Basic notifications
- Responsive dashboard
- Administration
- Docker development environment
- Automated tests

Do not build yet:

- Billing
- Trust/client accounting
- Payroll
- HR
- Full court diary
- M-Pesa
- KRA/eTIMS
- Judiciary integration
- Client portal
- AI drafting
- Advanced legal research

However, avoid architectural decisions that make these future modules difficult.

---

# 29. Future Module Architecture

Plan future expansion roughly as:

## Phase 1
Digital Filing & Records

## Phase 2
Matter Operations
- Tasks
- Court diary
- Calendar
- Reminders
- Workflow templates

## Phase 3
Finance
- Time entries
- Fee notes
- Invoicing
- Expenses
- Client/trust account
- Receipts
- M-Pesa

## Phase 4
Client Experience & Integrations
- Client portal
- Outlook/Gmail
- SMS/WhatsApp
- eTIMS
- External legal/court integrations

## Phase 5
Intelligence
- OCR enrichment
- Semantic search
- Matter chronology
- Document summarisation
- Precedent retrieval
- AI-assisted drafting

---

# 30. Suggested Repository Structure

```text
wakiliDesk/
├── docker/
├── docs/
├── src/
│   ├── config/
│   ├── accounts/
│   ├── tenants/
│   ├── firms/
│   ├── clients/
│   ├── matters/
│   ├── documents/
│   ├── physical_files/
│   ├── audit/
│   ├── notifications/
│   ├── dashboard/
│   ├── common/
│   ├── templates/
│   └── static/
├── tests/
├── scripts/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

Prefer `pyproject.toml` for Python dependency/project configuration.

---

# 31. Development Principles

Follow these rules throughout implementation:

1. **Security before convenience.**
2. Every tenant-owned query must be tenant-scoped.
3. Permissions are enforced server-side.
4. Never trust a tenant/firm ID supplied by the browser.
5. Use UUIDs for externally exposed object identifiers.
6. Keep business logic out of templates and thin views.
7. Use database transactions for multi-step operations.
8. Keep migrations small and reviewable.
9. Add indexes for frequently filtered fields.
10. Do not prematurely create microservices.
11. Prefer well-tested standard Django patterns.
12. Do not overengineer the UI.
13. Make common clerk/secretary workflows fast.
14. Audit sensitive actions.
15. Never overwrite historical document versions.
16. Treat uploaded files as untrusted input.
17. Validate permissions again on downloads.
18. Avoid exposing direct object-storage URLs.
19. Write tests with every security-sensitive feature.
20. Keep codebase modular enough for future legal modules.

---

# 32. UX Principles for a Law Firm

The interface should prioritize:

- Fast search
- Low click count
- Clear matter identity
- Clear document hierarchy
- Readable tables
- Keyboard-friendly data entry
- Bulk operations for records staff
- Obvious confidentiality markers
- Simple status indicators
- Consistent layout

Do not design it like a consumer social application.

Aim for a professional records-management interface.

---

# 33. Key User Journeys to Implement First

## Journey 1 — Create a firm

```text
Register
→ Verify account
→ Enter firm details
→ Upload logo
→ Create first admin
→ Configure defaults
→ Dashboard
```

## Journey 2 — Invite a user

```text
Admin
→ Users
→ Invite
→ Enter email
→ Select role
→ User accepts invite
→ Sets password
→ Accesses permitted modules
```

## Journey 3 — Create client and matter

```text
Create Client
→ Create Matter
→ Assign practice area
→ Assign advocate
→ Generate matter number
→ Digital file created
```

## Journey 4 — Upload a new document

```text
Open Matter
→ Documents
→ Upload
→ Select category
→ Enter metadata
→ Save
→ Background extraction/OCR
→ Searchable
```

## Journey 5 — Digitise existing physical file

```text
Register Physical File
→ Associate Matter
→ Mark digitisation started
→ Bulk upload scans
→ Index documents
→ Review quality
→ Approve
→ Mark digitisation complete
```

## Journey 6 — Check out a physical file

```text
Open Physical File
→ Check Out
→ Select person
→ Expected return
→ Save
→ Audit event created
```

## Journey 7 — Search

```text
Global Search
→ Client / matter / document / full-text results
→ Filter
→ Open permitted result
```

---

# 34. Definition of Done for Core MVP

The initial core module is ready for controlled pilot when:

- Two separate firms can coexist in the same deployment.
- Cross-tenant access tests pass.
- A firm can self-onboard.
- Firm Administrator can invite and manage users.
- Firm Administrator can configure role permissions.
- Clients and matters can be created.
- Matter numbers can be generated.
- Documents can be securely uploaded.
- Documents have metadata and categories.
- New versions preserve previous versions.
- Documents can be previewed/downloaded by authorised users.
- Physical files can be registered and located.
- Check-in/check-out history works.
- Existing files can move through a digitisation workflow.
- OCR/text-extraction jobs can run asynchronously.
- Search respects tenant and confidentiality permissions.
- Major actions are audited.
- Application is usable on desktop and mobile.
- Database and files have a documented backup approach.
- Development and staging run using Docker.
- Automated core permission and tenant-isolation tests pass.

---

# 35. Instructions to the Coding Assistant

When using this document as context in VS Code, follow this build approach:

1. Do not attempt to generate the entire system in one response/change.
2. First create the architecture and project skeleton.
3. Establish Docker, Django, PostgreSQL, Redis and object storage.
4. Create the custom User model before first production migration.
5. Implement Firm and FirmMembership before business modules.
6. Implement tenant middleware/context and tenant-safe access patterns.
7. Add automated tenant isolation tests.
8. Implement authentication and onboarding.
9. Implement roles and permissions.
10. Implement clients.
11. Implement matters.
12. Implement document storage/versioning.
13. Implement physical file registry.
14. Implement digitisation workflow.
15. Implement search.
16. Implement audit logs.
17. Build dashboard/admin configuration.
18. Add OCR/background jobs.
19. Harden security.
20. Produce deployment documentation.

For every feature:

- Explain the proposed change briefly.
- Identify affected files.
- Implement it incrementally.
- Add migrations where necessary.
- Add tests.
- Avoid unrelated refactors.
- Do not weaken tenant isolation.
- Do not bypass permissions for convenience.
- Keep setup instructions current in `README.md`.

---

# 36. First Development Task

Start by creating **Milestone 0 — Project Foundation**.

Deliver:

1. Django project skeleton.
2. Dockerfile.
3. `docker-compose.yml`.
4. PostgreSQL service.
5. Redis service.
6. MinIO service for development document storage.
7. Custom User model.
8. Firm model.
9. FirmMembership model.
10. Base Role and Permission design.
11. Tenant context/middleware foundation.
12. Health endpoint.
13. Environment configuration.
14. Basic CI-friendly tests.
15. README with local setup commands.
16. Seed command creating two example law firms and users.
17. Automated test proving a user from Firm A cannot retrieve Firm B data.

Do not implement documents or matters until this foundation is working and tested.

At the end of Milestone 0, provide:

- Directory structure
- Commands to start the application
- Local URLs
- Default development accounts generated by the seed command
- Tests executed and results
- Any architectural decisions that require review before Milestone 1

---

# 37. Product Name

Working product name:

**wakiliDesk**

Use `wakiliDesk` for user-facing branding and `wakiliDesk` for package/repository identifiers unless otherwise required.
