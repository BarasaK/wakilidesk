from django.contrib import admin

from diary.models import DiaryEvent, DiaryReminder


@admin.register(DiaryEvent)
class DiaryEventAdmin(admin.ModelAdmin):
    list_display = ("title", "firm", "event_type", "start_at", "status", "assigned_to")
    list_filter = ("event_type", "status", "firm")
    search_fields = ("title", "court_name", "location", "matter__matter_number")


@admin.register(DiaryReminder)
class DiaryReminderAdmin(admin.ModelAdmin):
    list_display = ("event", "channel", "remind_at", "status", "sent_at")
    list_filter = ("channel", "status")
