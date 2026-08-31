from __future__ import annotations

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone

from audit.services import record_audit_event
from physical_files.models import DigitisationReview, FileCheckout, PhysicalFile, StorageLocation


def physical_files_for_firm(firm):
    return PhysicalFile.objects.filter(firm=firm).select_related("matter", "storage_location")


def get_physical_file_for_firm_or_404(firm, physical_file_id):
    return get_object_or_404(PhysicalFile, id=physical_file_id, firm=firm)


@transaction.atomic
def create_physical_file(*, firm, data, request=None) -> PhysicalFile:
    matter = data["matter"]
    location = data.get("storage_location")
    if matter.firm_id != firm.id:
        raise ValueError("Matter does not belong to the current firm.")
    if location is not None and location.firm_id != firm.id:
        raise ValueError("Storage location does not belong to the current firm.")
    physical_file = PhysicalFile.objects.create(firm=firm, **data)
    record_audit_event(
        request=request,
        firm=firm,
        action="physical_file_created",
        object_type="PhysicalFile",
        object_id=physical_file.id,
    )
    return physical_file


@transaction.atomic
def update_physical_file(*, physical_file, firm, data, request=None) -> PhysicalFile:
    matter = data["matter"]
    location = data.get("storage_location")
    if matter.firm_id != firm.id:
        raise ValueError("Matter does not belong to the current firm.")
    if location is not None and location.firm_id != firm.id:
        raise ValueError("Storage location does not belong to the current firm.")
    for field, value in data.items():
        setattr(physical_file, field, value)
    physical_file.save()
    record_audit_event(
        request=request,
        firm=firm,
        action="physical_file_updated",
        object_type="PhysicalFile",
        object_id=physical_file.id,
    )
    return physical_file


@transaction.atomic
def checkout_physical_file(*, physical_file, firm, user, data, request=None) -> FileCheckout:
    if active_checkout_for_file(physical_file).exists():
        raise ValueError("This physical file is already checked out.")
    checkout = FileCheckout.objects.create(
        firm=firm,
        physical_file=physical_file,
        checked_out_by=user,
        **data,
    )
    physical_file.status = PhysicalFile.Status.CHECKED_OUT
    physical_file.save(update_fields=["status", "updated_at"])
    record_audit_event(
        request=request,
        firm=firm,
        user=user,
        action="physical_file_checked_out",
        object_type="FileCheckout",
        object_id=checkout.id,
    )
    return checkout


@transaction.atomic
def checkin_physical_file(*, physical_file, firm, user, notes="", request=None) -> FileCheckout:
    checkout = active_checkout_for_file(physical_file).select_for_update().first()
    if checkout is None:
        raise ValueError("This physical file is not checked out.")
    checkout.returned_at = timezone.now()
    checkout.returned_by = user
    if notes:
        checkout.notes = f"{checkout.notes}\nReturn notes: {notes}".strip()
    checkout.save(update_fields=["returned_at", "returned_by", "notes"])
    physical_file.status = PhysicalFile.Status.IN_STORAGE
    physical_file.save(update_fields=["status", "updated_at"])
    record_audit_event(
        request=request,
        firm=firm,
        user=user,
        action="physical_file_checked_in",
        object_type="FileCheckout",
        object_id=checkout.id,
    )
    return checkout


def active_checkout_for_file(physical_file):
    return physical_file.checkouts.filter(returned_at__isnull=True)


def overdue_checkouts_for_firm(firm):
    return FileCheckout.objects.filter(
        firm=firm,
        returned_at__isnull=True,
        expected_return_at__lt=timezone.now(),
    ).select_related("physical_file", "checked_out_to")


def ensure_default_storage_locations(firm) -> list[StorageLocation]:
    office, _ = StorageLocation.objects.get_or_create(firm=firm, parent=None, name="Nairobi Office")
    room, _ = StorageLocation.objects.get_or_create(firm=firm, parent=office, name="Records Room")
    cabinet, _ = StorageLocation.objects.get_or_create(firm=firm, parent=room, name="Cabinet A")
    shelf, _ = StorageLocation.objects.get_or_create(firm=firm, parent=cabinet, name="Shelf 01")
    return [office, room, cabinet, shelf]


def digitisation_files_for_firm(firm):
    return PhysicalFile.objects.filter(firm=firm).select_related("matter", "storage_location")


@transaction.atomic
def save_digitisation_review(*, physical_file, firm, data, request=None) -> DigitisationReview:
    review = DigitisationReview.objects.create(
        firm=firm,
        physical_file=physical_file,
        **data,
    )
    if review.completion_confirmed:
        physical_file.digitisation_status = PhysicalFile.DigitisationStatus.COMPLETED
    elif review.rescan_required or review.missing_page_flag or review.poor_quality_flag:
        physical_file.digitisation_status = PhysicalFile.DigitisationStatus.QUALITY_REVIEW
    else:
        physical_file.digitisation_status = PhysicalFile.DigitisationStatus.QUALITY_REVIEW
    physical_file.save(update_fields=["digitisation_status", "updated_at"])
    record_audit_event(
        request=request,
        firm=firm,
        action="digitisation_review_created",
        object_type="DigitisationReview",
        object_id=review.id,
    )
    return review
