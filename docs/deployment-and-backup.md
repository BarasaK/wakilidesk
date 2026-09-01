# Deployment and Backup Notes

## Runtime Components

- Django web app served by Gunicorn
- PostgreSQL database
- Redis broker/cache
- Celery worker
- Private object storage for legal documents
- Reverse proxy with HTTPS termination

## Required Environment Variables

Use `.env.example` as the source list. Production must provide unique values for:

```text
DJANGO_SECRET_KEY
DJANGO_DEBUG=false
ALLOWED_HOSTS
CSRF_TRUSTED_ORIGINS
POSTGRES_*
REDIS_URL
S3_ENDPOINT
S3_ACCESS_KEY
S3_SECRET_KEY
S3_BUCKET
EMAIL_*
```

## Backup Strategy

PostgreSQL:

- Run automated daily backups at minimum.
- Keep point-in-time recovery where available.
- Test restore into a non-production database before relying on a backup plan.

Object storage:

- Enable bucket versioning where supported.
- Keep backups separate from the primary bucket/account.
- Retain enough history to recover from accidental deletion or ransomware.

Application configuration:

- Keep deployment secrets in a managed secret store.
- Keep `.env` out of source control.
- Document every production variable change.

## Restore Order

1. Restore PostgreSQL.
2. Restore object storage bucket/prefixes.
3. Restore application environment configuration.
4. Run migrations.
5. Start web and worker services.
6. Verify `/health/`, login, document metadata, and document download.

## Current MVP Limitation

The current document storage writer uses `MEDIA_ROOT/private` with tenant-aware keys. It is suitable for local development only. Production pilots should replace it with an S3/MinIO adapter using private buckets and signed URLs.
