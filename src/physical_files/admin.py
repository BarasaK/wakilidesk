from django.contrib import admin

from physical_files.models import DigitisationReview, FileCheckout, PhysicalFile, StorageLocation


@admin.register(StorageLocation)
class StorageLocationAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "firm", "is_active")
    search_fields = ("name", "firm__display_name")
    list_filter = ("is_active",)


@admin.register(PhysicalFile)
class PhysicalFileAdmin(admin.ModelAdmin):
    list_display = ("physical_file_number", "volume_number", "matter", "firm", "status", "digitisation_status")
    search_fields = ("physical_file_number", "matter__matter_number", "firm__display_name")
    list_filter = ("status", "digitisation_status")


@admin.register(FileCheckout)
class FileCheckoutAdmin(admin.ModelAdmin):
    list_display = ("physical_file", "checked_out_to", "checked_out_to_name", "checked_out_at", "expected_return_at", "returned_at")
    search_fields = ("physical_file__physical_file_number", "checked_out_to__email", "checked_out_to_name")
    list_filter = ("returned_at",)


@admin.register(DigitisationReview)
class DigitisationReviewAdmin(admin.ModelAdmin):
    list_display = ("physical_file", "firm", "scan_date", "review_date", "completion_confirmed", "rescan_required")
    search_fields = ("physical_file__physical_file_number", "firm__display_name", "notes")
    list_filter = ("completion_confirmed", "rescan_required", "missing_page_flag", "poor_quality_flag")
