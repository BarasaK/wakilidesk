from django.contrib import admin

from audit.models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("action", "firm", "user", "object_type", "object_id", "timestamp")
    search_fields = ("action", "firm__display_name", "user__email", "object_type", "object_id")
    list_filter = ("action", "object_type", "timestamp")
    readonly_fields = (
        "firm",
        "user",
        "action",
        "object_type",
        "object_id",
        "timestamp",
        "ip_address",
        "user_agent",
        "metadata",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
