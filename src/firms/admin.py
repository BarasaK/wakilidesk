from django.contrib import admin

from firms.models import Firm, FirmMembership, Permission, Role


@admin.register(Firm)
class FirmAdmin(admin.ModelAdmin):
    list_display = ("display_name", "email", "city", "country", "is_active")
    search_fields = ("name", "display_name", "email")
    prepopulated_fields = {"slug": ("display_name",)}


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ("codename", "module", "name")
    search_fields = ("codename", "name", "module")
    list_filter = ("module",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("name", "firm", "is_system_default")
    search_fields = ("name", "firm__display_name")
    list_filter = ("is_system_default",)
    filter_horizontal = ("permissions",)


@admin.register(FirmMembership)
class FirmMembershipAdmin(admin.ModelAdmin):
    list_display = ("user", "firm", "role", "status", "joined_at")
    search_fields = ("user__email", "firm__display_name", "role__name")
    list_filter = ("status", "role__name")
