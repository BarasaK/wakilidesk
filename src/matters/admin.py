from django.contrib import admin

from matters.models import Matter, MatterParty, PracticeArea


@admin.register(PracticeArea)
class PracticeAreaAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "firm", "is_active")
    search_fields = ("name", "code", "firm__display_name")
    list_filter = ("is_active",)


@admin.register(Matter)
class MatterAdmin(admin.ModelAdmin):
    list_display = ("matter_number", "title", "client", "firm", "status", "confidentiality_level")
    search_fields = ("matter_number", "title", "client__name", "firm__display_name")
    list_filter = ("status", "confidentiality_level")


@admin.register(MatterParty)
class MatterPartyAdmin(admin.ModelAdmin):
    list_display = ("name", "party_type", "matter", "firm")
    search_fields = ("name", "matter__matter_number", "firm__display_name")
    list_filter = ("party_type",)
