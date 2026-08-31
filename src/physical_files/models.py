from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class StorageLocation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="storage_locations")
    name = models.CharField(max_length=120)
    parent = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        related_name="children",
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["firm", "parent", "name"], name="unique_storage_location_sibling")
        ]
        indexes = [
            models.Index(fields=["firm", "name"], name="phys_loc_firm_name_idx"),
            models.Index(fields=["firm", "parent"], name="phys_loc_firm_parent_idx"),
        ]
        ordering = ("name",)

    def __str__(self) -> str:
        names = [self.name]
        parent = self.parent
        while parent is not None:
            names.append(parent.name)
            parent = parent.parent
        return " / ".join(reversed(names))


class PhysicalFile(models.Model):
    class Status(models.TextChoices):
        IN_STORAGE = "IN_STORAGE", "In storage"
        CHECKED_OUT = "CHECKED_OUT", "Checked out"
        ARCHIVED = "ARCHIVED", "Archived"
        MISSING = "MISSING", "Missing"
        DESTROYED = "DESTROYED", "Destroyed"

    class DigitisationStatus(models.TextChoices):
        NOT_STARTED = "NOT_STARTED", "Not started"
        PREPARING = "PREPARING", "Preparing"
        SCANNING = "SCANNING", "Scanning"
        INDEXING = "INDEXING", "Indexing"
        QUALITY_REVIEW = "QUALITY_REVIEW", "Quality review"
        COMPLETED = "COMPLETED", "Completed"
        ON_HOLD = "ON_HOLD", "On hold"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="physical_files")
    matter = models.ForeignKey("matters.Matter", on_delete=models.PROTECT, related_name="physical_files")
    physical_file_number = models.CharField(max_length=80)
    volume_number = models.PositiveIntegerField(default=1)
    storage_location = models.ForeignKey(
        StorageLocation,
        on_delete=models.PROTECT,
        related_name="physical_files",
        null=True,
        blank=True,
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.IN_STORAGE)
    digitisation_status = models.CharField(
        max_length=20,
        choices=DigitisationStatus.choices,
        default=DigitisationStatus.NOT_STARTED,
    )
    barcode_or_qr_code = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["firm", "physical_file_number", "volume_number"], name="unique_physical_file_volume_per_firm")
        ]
        indexes = [
            models.Index(fields=["firm", "physical_file_number"], name="phys_file_firm_number_idx"),
            models.Index(fields=["firm", "status"], name="phys_file_firm_status_idx"),
            models.Index(fields=["firm", "digitisation_status"], name="phys_file_firm_digit_idx"),
        ]
        ordering = ("physical_file_number", "volume_number")

    def __str__(self) -> str:
        return f"{self.physical_file_number} Vol {self.volume_number}"


class FileCheckout(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="file_checkouts")
    physical_file = models.ForeignKey(PhysicalFile, on_delete=models.CASCADE, related_name="checkouts")
    checked_out_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="file_checkouts_created",
        null=True,
        blank=True,
    )
    checked_out_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="file_checkouts_received",
        null=True,
        blank=True,
    )
    checked_out_to_name = models.CharField(max_length=255, blank=True)
    checked_out_at = models.DateTimeField(default=timezone.now)
    expected_return_at = models.DateTimeField(null=True, blank=True)
    purpose = models.CharField(max_length=255, blank=True)
    returned_at = models.DateTimeField(null=True, blank=True)
    returned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="file_returns_created",
        null=True,
        blank=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["firm", "returned_at"], name="phys_checkout_firm_return_idx"),
            models.Index(fields=["physical_file", "returned_at"], name="phys_checkout_file_return_idx"),
            models.Index(fields=["expected_return_at"], name="phys_checkout_expected_idx"),
        ]
        ordering = ("-checked_out_at",)

    @property
    def is_overdue(self) -> bool:
        return (
            self.returned_at is None
            and self.expected_return_at is not None
            and self.expected_return_at < timezone.now()
        )

    def __str__(self) -> str:
        return f"{self.physical_file} checkout"


class DigitisationReview(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="digitisation_reviews")
    physical_file = models.ForeignKey(PhysicalFile, on_delete=models.CASCADE, related_name="digitisation_reviews")
    scanner_operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="digitisation_scans",
        null=True,
        blank=True,
    )
    scan_date = models.DateField(null=True, blank=True)
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="digitisation_reviews",
        null=True,
        blank=True,
    )
    review_date = models.DateField(null=True, blank=True)
    missing_page_flag = models.BooleanField(default=False)
    poor_quality_flag = models.BooleanField(default=False)
    rescan_required = models.BooleanField(default=False)
    completion_confirmed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["firm", "completion_confirmed"], name="digit_review_firm_done_idx"),
            models.Index(fields=["physical_file", "created_at"], name="digit_review_file_created_idx"),
        ]
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"Digitisation review for {self.physical_file}"
