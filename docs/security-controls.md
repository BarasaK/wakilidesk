# wakiliDesk Security Controls

This note summarises current MVP controls and the next hardening measures planned for production use.

## What We Can Say

No online system can honestly promise that hacking is impossible. wakiliDesk should be positioned as security-conscious software that reduces risk through access control, encryption in transit, auditability, monitoring, backups, and tested recovery.

Suggested client-facing wording:

```text
wakiliDesk is built with security-by-design principles. The system separates firm data, restricts user actions through role-based permissions, protects document access behind permission checks, records important activity in audit logs, and supports HTTPS deployment. For production rollout, we will add stronger monitoring, encrypted backups, MFA, rate limiting, and periodic security reviews.
```

## Current MVP Controls

- Firm-level tenant separation for client, matter, document, diary, file, report, and notification records.
- Role-based permissions for module access and sensitive actions.
- Confidential matter filtering for restricted and partner-only files.
- Permission-checked document downloads.
- Document trash with admin-only permanent deletion.
- Audit logging for important changes such as invitations, role edits, matter changes, document actions, and diary updates.
- Public password reset and invitation links use the configured public domain.
- Login throttling limits repeated failed sign-in attempts.
- Production-configurable secure cookies, HTTPS redirect, HSTS, X-Frame-Options, and content type sniffing protection.
- Secrets and production environment values remain outside source control.

## Production Settings To Enable

For HTTPS domain deployment:

```text
DJANGO_DEBUG=false
DJANGO_SECURE_PROXY_SSL_HEADER=true
DJANGO_SECURE_SSL_REDIRECT=true
DJANGO_SECURE_HSTS_SECONDS=31536000
DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS=true
DJANGO_SECURE_HSTS_PRELOAD=false
DJANGO_SESSION_COOKIE_SECURE=true
DJANGO_CSRF_COOKIE_SECURE=true
LOGIN_ATTEMPT_LIMIT=5
LOGIN_LOCKOUT_SECONDS=900
```

Only enable HSTS preload after confirming all production subdomains are permanently HTTPS-capable.

## Next Security Roadmap

- MFA for firm administrators and optional MFA for all users.
- Admin audit-log review UI for logins, downloads, deletes, permission changes, and invitations.
- Automated encrypted database and media backups with periodic restore tests.
- Private S3-compatible document storage with signed downloads.
- Dependency vulnerability scanning in CI.
- Login and password-reset rate limiting by IP and account.
- Security monitoring and alerting for unusual download volume, repeated failed login attempts, and admin role changes.
- Formal incident response playbook.
- Data retention policy for archive, trash, permanent delete, and backup retention.
- Penetration test before handling sensitive live client data at scale.
- Kenya Data Protection Act alignment checklist and operating policy.
