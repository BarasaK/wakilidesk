# Milestone 2: Clients and Matters

## Done

- Added `clients` Django app
- Added `matters` Django app
- Added tenant-owned `Client`, `PracticeArea`, `Matter`, and `MatterParty` models
- Added client list/detail/create/edit views
- Added matter list/detail/create/edit views
- Added matter party creation
- Added practice area list/create/edit views
- Added matter numbering from firm pattern, practice-area code, year, and sequence
- Extended seed data with default practice areas, pilot client, and pilot matter per seeded firm
- Added audit events for client, matter, and matter party creation/updates
- Added tenant isolation and permission tests for clients and matters

## Local URLs

```text
http://localhost:8000/clients/
http://localhost:8000/clients/new/
http://localhost:8000/matters/
http://localhost:8000/matters/new/
http://localhost:8000/matters/practice-areas/
```

## Notes for Milestone 3

- Documents should link directly to `firm` and `matter`.
- Document category must be firm-owned and configurable.
- Every uploaded revision should create a separate `DocumentVersion`.
- Storage should use private tenant-aware keys even while the initial local backend is minimal.
