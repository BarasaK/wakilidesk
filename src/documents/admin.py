from django.contrib import admin

from documents.models import Document, DocumentCategory, DocumentVersion


@admin.register(DocumentCategory)
class DocumentCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "firm", "is_active")
    search_fields = ("name", "firm__display_name")
    list_filter = ("is_active",)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "matter", "firm", "document_type", "source", "archived_at")
    search_fields = ("title", "matter__matter_number", "firm__display_name")
    list_filter = ("source", "confidentiality_level", "archived_at")


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ("document", "version_number", "original_filename", "mime_type", "file_size", "ocr_status")
    search_fields = ("document__title", "original_filename", "checksum")
    list_filter = ("ocr_status", "mime_type")
