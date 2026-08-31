# Milestone 1: Authentication and Firm Administration

## Done

- Signup flow for the first administrator account
- Firm onboarding flow
- Current-firm dashboard shell
- Firm profile edit view
- Firm user administration view
- Firm-scoped invitation creation
- Invitation acceptance for new and existing users
- Role list, create, and edit views
- Permission enforcement for administration views
- Audit event model and service
- Tests for onboarding, invites, invite permissions, and invitation acceptance

## Local URLs

```text
http://localhost:8000/accounts/login/
http://localhost:8000/accounts/signup/
http://localhost:8000/onboarding/firm/
http://localhost:8000/app/administration/users/
http://localhost:8000/app/administration/roles/
http://localhost:8000/app/firm/profile/
```

## Notes for Milestone 2

- Add `PracticeArea` before `Matter` so matter numbering can use practice-area codes.
- Add tenant-owned `Client` and `Matter` models with direct `firm` foreign keys.
- Keep every user-facing query scoped through the current firm.
