# Milestone 7 - Confidentiality and Access Hardening

Milestone 7 tightens MVP data visibility around restricted legal matters and records linked to those matters.

## Delivered

- Central matter visibility selector for user-aware access filtering.
- Restricted and partner-only matters are hidden from users unless they have `manage_confidential_matter` or are assigned as responsible partner/advocate.
- Matter detail and edit routes use user-aware access checks.
- Document list, detail, edit, version upload, download, archive, restore, and OCR reprocess routes use user-aware access checks.
- Document uploads only allow selecting matters the current user can access.
- Document confidentiality cannot be lower than the linked matter confidentiality.
- Physical file list, detail, edit, checkout, check-in, digitisation list, and review routes use user-aware access checks through their linked matters.
- Overdue checkout and dashboard metrics are filtered to visible physical files.
- Global search filters matters, matter parties, documents, and physical files through the same access policy.
- Regression tests cover restricted record hiding, assigned-user access, and document confidentiality inheritance.

## MVP policy

The current MVP does not yet include explicit matter access lists. Until that is added, access to non-standard matters is allowed for:

- Users with `manage_confidential_matter`.
- The matter's responsible partner.
- The matter's responsible advocate.

Standard matters remain visible to users with the relevant `view_*` permissions.

## Verification

```powershell
docker compose exec web pytest tests/test_milestone_7.py
```

Expected result:

```text
3 passed
```
