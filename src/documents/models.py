from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class DocumentCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="document_categories")
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["firm", "name"], name="unique_document_category_per_firm")
        ]
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name


class Document(models.Model):
    class Source(models.TextChoices):
        SCANNED_PHYSICAL = "SCANNED_PHYSICAL", "Scanned physical"
        EMAIL = "EMAIL", "Email"
        INTERNAL_UPLOAD = "INTERNAL_UPLOAD", "Internal upload"
        CLIENT_UPLOAD = "CLIENT_UPLOAD", "Client upload"
        MIGRATION = "MIGRATION", "Migration"
        SYSTEM_GENERATED = "SYSTEM_GENERATED", "System generated"

    class ConfidentialityLevel(models.TextChoices):
        STANDARD = "STANDARD", "Standard"
        RESTRICTED = "RESTRICTED", "Restricted"
        PARTNER_ONLY = "PARTNER_ONLY", "Partner only"
        CUSTOM = "CUSTOM", "Custom"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firm = models.ForeignKey("firms.Firm", on_delete=models.CASCADE, related_name="documents")
    matter = models.ForeignKey("matters.Matter", on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    document_type = models.ForeignKey(
        DocumentCategory,
        on_delete=models.PROTECT,
        related_name="documents",
    )
    document_date = models.DateField(null=True, blank=True)
    reference_number = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    current_version = models.ForeignKey(
        "documents.DocumentVersion",
        on_delete=models.SET_NULL,
        related_name="+",
        null=True,
        blank=True,
    )
    source = models.CharField(max_length=30, choices=Source.choices, default=Source.INTERNAL_UPLOAD)
    confidentiality_level = models.CharField(
        max_length=20,
        choices=ConfidentialityLevel.choices,
        default=ConfidentialityLevel.STANDARD,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="uploaded_documents",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    archived_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["firm", "title"], name="documents_doc_firm_title_idx"),
            models.Index(fields=["firm", "matter"], name="documents_doc_firm_matter_idx"),
            models.Index(fields=["firm", "archived_at"], name="documents_doc_firm_arch_idx"),
        ]
        ordering = ("-created_at", "title")

    def __str__(self) -> str:
        return self.title


class DocumentVersion(models.Model):
    class OCRStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        PROCESSING = "PROCESSING", "Processing"
        COMPLETED = "COMPLETED", "Completed"
        FAILED = "FAILED", "Failed"
        NOT_REQUIRED = "NOT_REQUIRED", "Not required"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField()
    storage_key = models.CharField(max_length=500, unique=True)
    original_filename = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=120)
    file_size = models.PositiveBigIntegerField()
    checksum = models.CharField(max_length=64)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="uploaded_document_versions",
        null=True,
        blank=True,
    )
    uploaded_at = models.DateTimeField(default=timezone.now)
    extracted_text = models.TextField(blank=True)
    ocr_status = models.CharField(max_length=20, choices=OCRStatus.choices, default=OCRStatus.PENDING)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["document", "version_number"], name="unique_document_version_number")
        ]
        indexes = [
            models.Index(fields=["document", "version_number"], name="documents_ver_doc_num_idx"),
            models.Index(fields=["ocr_status"], name="documents_ver_ocr_status_idx"),
        ]
        ordering = ("-version_number",)

    def __str__(self) -> str:
        return f"{self.document} v{self.version_number}"
