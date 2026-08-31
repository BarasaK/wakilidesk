# wakiliDesk

wakiliDesk is a multi-tenant records and digital file management system for Kenyan law firms.

This repository currently contains Milestone 0: the project foundation.

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

Seed development firms and users:

```powershell
docker compose exec web python manage.py seed_dev
```

Run tests:

```powershell
docker compose exec web pytest
```

## Local URLs

- App: http://localhost:8000/
- Health: http://localhost:8000/health/
- Django admin: http://localhost:8000/admin/
- MinIO API: http://localhost:9000/
- MinIO console: http://localhost:9001/

## Development accounts

The seed command creates these example accounts for Firm A and Firm B.

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

## Architectural decisions

- Multi-tenancy starts with a shared PostgreSQL database and shared schema.
- Tenant-owned records must carry a direct `firm` foreign key as modules are added.
- Users are not directly tied to one firm; access comes through `FirmMembership`.
- Roles are firm-owned and permissions are globally defined by codename.
- Server-side membership checks are mandatory for tenant data access.
- Docker is the default development and staging execution path.

## Next milestone

Milestone 1 should add authentication screens, firm onboarding, user invitations, role management views, and audit events around account and firm administration.
