# Milestone 4: Physical Files

## Done

- Added `physical_files` Django app
- Added hierarchical `StorageLocation`
- Added tenant-owned `PhysicalFile`
- Added immutable `FileCheckout` history records
- Added physical file list/detail/create/edit views
- Added storage location list/create/edit views
- Added check-out and check-in views
- Added duplicate active check-out prevention
- Added overdue checkout query and dashboard table on physical file list
- Extended seed data with default storage locations and one pilot physical file per firm
- Added tests for physical file tenant isolation, register/check-out/check-in, duplicate checkout prevention, and overdue listing

## Local URLs

```text
http://localhost:8000/physical-files/
http://localhost:8000/physical-files/new/
http://localhost:8000/physical-files/locations/
```

## Notes for Milestone 5

- Add the full digitisation workflow screens using `PhysicalFile.digitisation_status`.
- Add quality review fields and reviewer tracking.
- Add dashboard cards for digitisation progress and files awaiting return.
