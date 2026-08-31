from django.contrib import admin

from notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "firm", "recipient", "channel", "status", "created_at")
    search_fields = ("title", "message", "recipient__email", "firm__display_name")
    list_filter = ("channel", "status")
